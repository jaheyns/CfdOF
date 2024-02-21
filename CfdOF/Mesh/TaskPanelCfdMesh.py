# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2016 - Bernd Hahnebach <bernd@bimstatik.org>            *
# *   Copyright (c) 2017 Alfred Bogaers (CSIR) <abogaers@csir.co.za>        *
# *   Copyright (c) 2017 Johan Heyns (CSIR) <jheyns@csir.co.za>             *
# *   Copyright (c) 2017 Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>          *
# *   Copyright (c) 2019-2023 Oliver Oxtoby <oliveroxtoby@gmail.com>        *
# *                                                                         *
# *   This program is free software: you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License as        *
# *   published by the Free Software Foundation, either version 3 of the    *
# *   License, or (at your option) any later version.                       *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Lesser General Public License for more details.                   *
# *                                                                         *
# *   You should have received a copy of the GNU Lesser General Public      *
# *   License along with this program.  If not,                             *
# *   see <https://www.gnu.org/licenses/>.                                  *
# *                                                                         *
# ***************************************************************************

from __future__ import print_function
import FreeCAD
import os
import os.path
from CfdOF.Mesh import CfdMesh
import time
from datetime import timedelta
from CfdOF import CfdTools
from CfdOF.CfdTools import setQuantity, getQuantity, storeIfChanged
from CfdOF.Mesh import CfdMeshTools
from CfdOF.CfdConsoleProcess import CfdConsoleProcess
if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore
    from PySide import QtCore
    from PySide import QtGui
    from PySide.QtCore import Qt
    from PySide.QtGui import QApplication


class TaskPanelCfdMesh:
    """ The TaskPanel for editing References property of CfdMesh objects and creation of new CFD mesh """
    def __init__(self, obj):
        self.mesh_obj = obj
        self.analysis_obj = CfdTools.getParentAnalysisObject(self.mesh_obj)
        self.form = FreeCADGui.PySideUic.loadUi(os.path.join(CfdTools.getModulePath(), 'Gui', "TaskPanelCfdMesh.ui"))

        self.console_message_cart = ''
        self.error_message = ''
        self.mesh_obj.Proxy.cart_mesh = CfdMeshTools.CfdMeshTools(self.mesh_obj)
        self.paraviewScriptName = ""

        self.mesh_obj.Proxy.mesh_process = CfdConsoleProcess(finished_hook=self.meshFinished,
                                                             stdout_hook=self.gotOutputLines,
                                                             stderr_hook=self.gotErrorLines)

        self.Timer = QtCore.QTimer()
        self.Timer.setInterval(1000)
        self.Timer.timeout.connect(self.update_timer_text)

        self.form.cb_utility.activated.connect(self.choose_utility)
        self.form.pb_write_mesh.clicked.connect(self.writeMesh)
        self.form.pb_edit_mesh.clicked.connect(self.editMesh)
        self.form.pb_run_mesh.clicked.connect(self.runMesh)
        self.form.pb_stop_mesh.clicked.connect(self.killMeshProcess)
        self.form.pb_paraview.clicked.connect(self.openParaview)
        self.form.pb_load_mesh.clicked.connect(self.pbLoadMeshClicked)
        self.form.pb_clear_mesh.clicked.connect(self.pbClearMeshClicked)
        self.form.pb_searchPointInMesh.clicked.connect(self.searchPointInMesh)
        self.form.pb_check_mesh.clicked.connect(self.checkMeshClicked)

        self.radioGroup = QtGui.QButtonGroup()
        self.radioGroup.addButton(self.form.radio_explicit_edge_detection)
        self.radioGroup.addButton(self.form.radio_implicit_edge_detection)

        self.form.snappySpecificProperties.setVisible(False)
        self.form.pb_stop_mesh.setEnabled(False)
        self.form.pb_paraview.setEnabled(False)

        self.form.cb_utility.addItems(CfdMesh.MESHER_DESCRIPTIONS)

        self.form.if_max.setToolTip("Enter 0 to use default value")
        self.form.pb_searchPointInMesh.setToolTip("Specify below a point vector inside of the mesh or press 'Search' "
                                                  "to try to automatically find a point")
        self.form.if_cellsbetweenlevels.setToolTip("Number of cells between each of level of refinement")
        self.form.if_edgerefine.setToolTip("Number of refinement levels for all edges")
        self.form.radio_explicit_edge_detection.setToolTip("Find surface edges using explicit (eMesh) detection")
        self.form.radio_implicit_edge_detection.setToolTip("Find surface edges using implicit detection")

        self.load()
        self.updateUI()

        self.Start = time.time()
        self.Timer.start()

    def getStandardButtons(self):
        return int(QtGui.QDialogButtonBox.Close)
        # def reject() is called on close button

    def reject(self):
        FreeCADGui.ActiveDocument.resetEdit()
        return True

    def closed(self):
        # We call this from unsetEdit to ensure cleanup
        self.store()
        self.mesh_obj.Proxy.mesh_process.terminate()
        self.mesh_obj.Proxy.mesh_process.waitForFinished()
        self.Timer.stop()
        FreeCAD.ActiveDocument.recompute()

    def load(self):
        """ Fills the widgets """
        setQuantity(self.form.if_max, self.mesh_obj.CharacteristicLengthMax)
        point_in_mesh = self.mesh_obj.PointInMesh.copy()
        setQuantity(self.form.if_pointInMeshX, point_in_mesh.get('x'))
        setQuantity(self.form.if_pointInMeshY, point_in_mesh.get('y'))
        setQuantity(self.form.if_pointInMeshZ, point_in_mesh.get('z'))

        self.form.if_cellsbetweenlevels.setValue(self.mesh_obj.CellsBetweenLevels)
        self.form.if_edgerefine.setValue(self.mesh_obj.EdgeRefinement)
        self.form.radio_implicit_edge_detection.setChecked(self.mesh_obj.ImplicitEdgeDetection)
        self.form.radio_explicit_edge_detection.setChecked(not self.mesh_obj.ImplicitEdgeDetection)

        index_utility = CfdTools.indexOrDefault(list(zip(
                CfdMesh.MESHERS, CfdMesh.DIMENSION, CfdMesh.DUAL_CONVERSION)), 
                (self.mesh_obj.MeshUtility, self.mesh_obj.ElementDimension, self.mesh_obj.ConvertToDualMesh), 0)
        self.form.cb_utility.setCurrentIndex(index_utility)

    def updateUI(self):
        case_path = self.mesh_obj.Proxy.cart_mesh.meshCaseDir
        self.form.pb_edit_mesh.setEnabled(os.path.exists(case_path))
        self.form.pb_run_mesh.setEnabled(os.path.exists(os.path.join(case_path, "Allmesh")))
        self.form.pb_paraview.setEnabled(os.path.exists(os.path.join(case_path, "pv.foam")))
        self.form.pb_load_mesh.setEnabled(os.path.exists(os.path.join(case_path, "surfaceMesh.vtk")))
        self.form.pb_check_mesh.setEnabled(os.path.exists(os.path.join(case_path, "surfaceMesh.vtk")))
        
        utility = CfdMesh.MESHERS[self.form.cb_utility.currentIndex()]
        if utility == "snappyHexMesh":
            self.form.snappySpecificProperties.setVisible(True)
        else:
            self.form.snappySpecificProperties.setVisible(False)

    def store(self):
        mesher_idx = self.form.cb_utility.currentIndex()
        storeIfChanged(self.mesh_obj, 'CharacteristicLengthMax', getQuantity(self.form.if_max))
        storeIfChanged(self.mesh_obj, 'MeshUtility', CfdMesh.MESHERS[mesher_idx])
        storeIfChanged(self.mesh_obj, 'ElementDimension', CfdMesh.DIMENSION[mesher_idx])
        storeIfChanged(self.mesh_obj, 'CellsBetweenLevels', self.form.if_cellsbetweenlevels.value())
        storeIfChanged(self.mesh_obj, 'EdgeRefinement', self.form.if_edgerefine.value())
        storeIfChanged(self.mesh_obj, 'ConvertToDualMesh', CfdMesh.DUAL_CONVERSION[mesher_idx])
        storeIfChanged(self.mesh_obj, 'ImplicitEdgeDetection', self.form.radio_implicit_edge_detection.isChecked())

        point_in_mesh = {'x': getQuantity(self.form.if_pointInMeshX),
                         'y': getQuantity(self.form.if_pointInMeshY),
                         'z': getQuantity(self.form.if_pointInMeshZ)}

        if self.mesh_obj.MeshUtility == 'snappyHexMesh':
            storeIfChanged(self.mesh_obj, 'PointInMesh', point_in_mesh)

        self.mesh_obj.Proxy.cart_mesh = CfdMeshTools.CfdMeshTools(self.mesh_obj)

    def consoleMessage(self, message="", colour_type=None, timed=True):
        if timed:
            self.console_message_cart += \
                '<font color="{}">{:4.1f}:</font> '.format(CfdTools.getColour('Logging'), time.time() - self.Start)
        if colour_type:
            self.console_message_cart += \
                '<font color="{}">{}</font><br>'.format(CfdTools.getColour(colour_type), message)
        else:
            self.console_message_cart += message + '<br>'
        self.form.te_output.setText(self.console_message_cart)
        self.form.te_output.moveCursor(QtGui.QTextCursor.End)
        if FreeCAD.GuiUp:
            FreeCAD.Gui.updateGui()

    def update_timer_text(self):
        if self.mesh_obj.Proxy.mesh_process.state() == QtCore.QProcess.ProcessState.Running:
            self.form.l_time.setText('Time: ' + CfdTools.formatTimer(time.time() - self.Start))

    def choose_utility(self, index):
        if index < 0:
            return
        utility = CfdMesh.MESHERS[self.form.cb_utility.currentIndex()]
        if utility == "snappyHexMesh":
            self.form.snappySpecificProperties.setVisible(True)
        else:
            self.form.snappySpecificProperties.setVisible(False)

    def writeMesh(self):
        import importlib
        importlib.reload(CfdMeshTools)
        self.console_message_cart = ''
        self.Start = time.time()
        # Re-initialise CfdMeshTools with new parameters
        self.store()

        FreeCADGui.doCommand("from CfdOF.Mesh import CfdMeshTools")
        FreeCADGui.doCommand("from CfdOF import CfdTools")
        FreeCADGui.doCommand("cart_mesh = "
                             "CfdMeshTools.CfdMeshTools(FreeCAD.ActiveDocument." + self.mesh_obj.Name + ")")
        FreeCADGui.doCommand("FreeCAD.ActiveDocument." + self.mesh_obj.Name + ".Proxy.cart_mesh = cart_mesh")
        cart_mesh = self.mesh_obj.Proxy.cart_mesh
        cart_mesh.progressCallback = self.progressCallback

        # Start writing the mesh files
        self.consoleMessage("Preparing meshing ...")
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            setQuantity(self.form.if_max, str(cart_mesh.getClmax()))
            # Re-update the data in case ClMax was auto-set to avoid spurious update detection on next write
            self.store()
            print('Part to mesh:\n  Name: '
                  + cart_mesh.part_obj.Name + ', Label: '
                  + cart_mesh.part_obj.Label + ', ShapeType: '
                  + cart_mesh.part_obj.Shape.ShapeType)
            print('  CharacteristicLengthMax: ' + str(cart_mesh.clmax))
            FreeCADGui.doCommand("cart_mesh.writeMesh()")
        except Exception as ex:
            self.consoleMessage("Error " + type(ex).__name__ + ": " + str(ex), 'Error')
            raise
        else:
            self.analysis_obj.NeedsMeshRerun = True
        finally:
            QApplication.restoreOverrideCursor()

        # Update the UI
        self.updateUI()

    def progressCallback(self, message):
        self.consoleMessage(message)

    def checkMeshClicked(self):
        if CfdTools.getFoamRuntime() == "PosixDocker":
            CfdTools.startDocker()
        self.Start = time.time()
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            FreeCADGui.doCommand("from CfdOF import CfdTools")
            FreeCADGui.doCommand("from CfdOF.Mesh import CfdMeshTools")
            FreeCADGui.doCommand("from CfdOF.CfdConsoleProcess import CfdConsoleProcess")
            FreeCADGui.doCommand("cart_mesh = "
                                 "    CfdMeshTools.CfdMeshTools(FreeCAD.ActiveDocument." + self.mesh_obj.Name + ")")
            FreeCADGui.doCommand("proxy = FreeCAD.ActiveDocument." + self.mesh_obj.Name + ".Proxy")
            FreeCADGui.doCommand("proxy.cart_mesh = cart_mesh")
            FreeCADGui.doCommand("cart_mesh.error = False")
            FreeCADGui.doCommand("cmd = CfdTools.makeRunCommand('checkMesh -meshQuality', cart_mesh.meshCaseDir)")
            FreeCADGui.doCommand("env_vars = CfdTools.getRunEnvironment()")
            self.check_mesh_error = False
            FreeCADGui.doCommand("proxy.running_from_macro = True")
            self.mesh_obj.Proxy.running_from_macro = False
            self.mesh_obj.Proxy.check_mesh_process = CfdConsoleProcess(
                stdout_hook=self.gotOutputLines, stderr_hook=self.gotErrorLines)
            FreeCADGui.doCommand("if proxy.running_from_macro:\n" +
                                 "  proxy.check_mesh_process = CfdConsoleProcess()\n" +
                                 "  proxy.check_mesh_process.start(cmd, env_vars=env_vars, working_dir=cart_mesh.meshCaseDir)\n" +
                                 "  proxy.check_mesh_process.waitForFinished()\n" +
                                 "else:\n" +
                                 "  proxy.check_mesh_process.start(cmd, env_vars=env_vars, working_dir=cart_mesh.meshCaseDir)")
            if self.mesh_obj.Proxy.check_mesh_process.waitForStarted():
                self.consoleMessage("Mesh check started ...")
            else:
                self.consoleMessage("Error starting mesh check process", 'Error')
            if self.mesh_obj.Proxy.check_mesh_process.waitForFinished():
                if self.check_mesh_error:
                    self.consoleMessage("Detected error(s) in mesh", 'Error')
                else:
                    self.consoleMessage("Mesh check OK")
            else:
                self.consoleMessage("Mesh check process failed")

        except Exception as ex:
            self.consoleMessage("Error " + type(ex).__name__ + ": " + str(ex), 'Error')
        finally:
            QApplication.restoreOverrideCursor()

    def editMesh(self):
        case_path = self.mesh_obj.Proxy.cart_mesh.meshCaseDir
        self.consoleMessage("Please edit the case input files externally at: {}\n".format(case_path))
        CfdTools.openFileManager(case_path)

    def runMesh(self):
        if CfdTools.getFoamRuntime() == "PosixDocker":
            CfdTools.startDocker()

        self.Start = time.time()

        # Check for changes that require mesh re-write
        self.store()
        if self.analysis_obj.NeedsMeshRewrite:
            if FreeCAD.GuiUp:
                if QtGui.QMessageBox.question(
                    None,
                    "CfdOF Workbench",
                    "The case setup for the mesher may need to be re-written based on changes you have made to the "
                    "model.\n\nWrite mesh case first?", defaultButton=QtGui.QMessageBox.Yes
                ) == QtGui.QMessageBox.Yes:
                    self.Start = time.time()
                    self.writeMesh()
                else:
                    self.Start = time.time()

        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.consoleMessage("Initializing {} ...".format(self.mesh_obj.MeshUtility))
            FreeCADGui.doCommand("from CfdOF.Mesh import CfdMeshTools")
            FreeCADGui.doCommand("from CfdOF import CfdTools")
            FreeCADGui.doCommand("from CfdOF import CfdConsoleProcess")
            FreeCADGui.doCommand("cart_mesh = "
                                 "    CfdMeshTools.CfdMeshTools(FreeCAD.ActiveDocument." + self.mesh_obj.Name + ")")
            FreeCADGui.doCommand("proxy = FreeCAD.ActiveDocument." + self.mesh_obj.Name + ".Proxy")
            FreeCADGui.doCommand("proxy.cart_mesh = cart_mesh")
            FreeCADGui.doCommand("cart_mesh.error = False")
            if CfdTools.getFoamRuntime() == "MinGW":
                FreeCADGui.doCommand("cmd = CfdTools.makeRunCommand('Allmesh.bat', source_env=False)")
            else:
                FreeCADGui.doCommand("cmd = CfdTools.makeRunCommand('./Allmesh', cart_mesh.meshCaseDir, source_env=False)")
            FreeCADGui.doCommand("env_vars = CfdTools.getRunEnvironment()")
            FreeCADGui.doCommand("proxy.running_from_macro = True")
            self.mesh_obj.Proxy.running_from_macro = False
            FreeCADGui.doCommand("if proxy.running_from_macro:\n" +
                                 "  mesh_process = CfdConsoleProcess.CfdConsoleProcess()\n" +
                                 "  mesh_process.start(cmd, env_vars=env_vars, working_dir=cart_mesh.meshCaseDir)\n" +
                                 "  mesh_process.waitForFinished()\n" +
                                 "else:\n" +
                                 "  proxy.mesh_process.start(cmd, env_vars=env_vars, working_dir=cart_mesh.meshCaseDir)")
            if self.mesh_obj.Proxy.mesh_process.waitForStarted():
                self.form.pb_run_mesh.setEnabled(False)  # Prevent user running a second instance
                self.form.pb_stop_mesh.setEnabled(True)
                self.form.pb_write_mesh.setEnabled(False)
                self.form.pb_check_mesh.setEnabled(False)
                self.form.pb_paraview.setEnabled(False)
                self.form.pb_load_mesh.setEnabled(False)
                self.consoleMessage("Mesher started ...")
            else:
                self.consoleMessage("Error starting meshing process", 'Error')
                self.mesh_obj.Proxy.cart_mesh.error = True
        except Exception as ex:
            self.consoleMessage("Error " + type(ex).__name__ + ": " + str(ex), 'Error')
            raise
        finally:
            QApplication.restoreOverrideCursor()

    def killMeshProcess(self):
        self.consoleMessage("Meshing manually stopped")
        self.error_message = 'Meshing interrupted'
        self.mesh_obj.Proxy.mesh_process.terminate()
        # Note: meshFinished will still be called

    def gotOutputLines(self, lines):
        for l in lines.split('\n'):
            if l.endswith("faces in error to set meshQualityFaces"):
                self.check_mesh_error = True

    def gotErrorLines(self, lines):
        print_err = self.mesh_obj.Proxy.mesh_process.processErrorOutput(lines)
        if print_err is not None:
            self.consoleMessage(print_err, 'Error')

    def meshFinished(self, exit_code):
        if exit_code == 0:
            self.consoleMessage('Meshing completed')
            self.analysis_obj.NeedsMeshRerun = False
            self.form.pb_run_mesh.setEnabled(True)
            self.form.pb_stop_mesh.setEnabled(False)
            self.form.pb_paraview.setEnabled(True)
            self.form.pb_write_mesh.setEnabled(True)
            self.form.pb_check_mesh.setEnabled(True)
            self.form.pb_load_mesh.setEnabled(True)
        else:
            self.consoleMessage("Meshing exited with error", 'Error')
            self.form.pb_run_mesh.setEnabled(True)
            self.form.pb_stop_mesh.setEnabled(False)
            self.form.pb_write_mesh.setEnabled(True)
            self.form.pb_check_mesh.setEnabled(False)
            self.form.pb_paraview.setEnabled(False)

        self.error_message = ''
        # Get rid of any existing loaded mesh
        self.pbClearMeshClicked()
        self.updateUI()

    def openParaview(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        case_path = os.path.abspath(self.mesh_obj.Proxy.cart_mesh.meshCaseDir)
        script_name = "pvScriptMesh.py"
        try:
            CfdTools.startParaview(case_path, script_name, self.consoleMessage)
        finally:
            QApplication.restoreOverrideCursor()

    def pbLoadMeshClicked(self):
        self.consoleMessage("Reading mesh ...", timed=False)
        prev_write_mesh = self.analysis_obj.NeedsMeshRewrite
        self.mesh_obj.Proxy.cart_mesh.loadSurfMesh()
        self.analysis_obj.NeedsMeshRewrite = prev_write_mesh
        self.consoleMessage('Triangulated representation of the surface mesh is shown - ', timed=False)
        self.consoleMessage("Please use Paraview for full mesh visualisation.\n", timed=False)

    def pbClearMeshClicked(self):
        prev_write_mesh = self.analysis_obj.NeedsMeshRewrite
        for m in self.mesh_obj.Group:
            if m.isDerivedFrom("Fem::FemMeshObject"):
                FreeCAD.ActiveDocument.removeObject(m.Name)
        self.analysis_obj.NeedsMeshRewrite = prev_write_mesh
        FreeCAD.ActiveDocument.recompute()

    def searchPointInMesh(self):
        print ("Searching for an internal vector point ...")
        # Apply latest mesh size
        self.store()
        pointCheck = self.mesh_obj.Proxy.cart_mesh.automaticInsidePointDetect()
        if pointCheck is not None:
            iMPx, iMPy, iMPz = pointCheck
            setQuantity(self.form.if_pointInMeshX, str(iMPx) + "mm")
            setQuantity(self.form.if_pointInMeshY, str(iMPy) + "mm")
            setQuantity(self.form.if_pointInMeshZ, str(iMPz) + "mm")
