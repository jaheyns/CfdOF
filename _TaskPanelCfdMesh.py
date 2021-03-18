# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2016 - Bernd Hahnebach <bernd@bimstatik.org>            *
# *   Copyright (c) 2017 Alfred Bogaers (CSIR) <abogaers@csir.co.za>        *
# *   Copyright (c) 2017 Johan Heyns (CSIR) <jheyns@csir.co.za>             *
# *   Copyright (c) 2017 Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>          *
# *   Copyright (c) 2019-2020 Oliver Oxtoby <oliveroxtoby@gmail.com>        *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************

from __future__ import print_function
import FreeCAD
import os
import os.path
from CfdMesh import _CfdMesh
import time
from datetime import timedelta
import CfdTools
from CfdTools import setQuantity, getQuantity
import CfdMeshTools
from CfdConsoleProcess import CfdConsoleProcess
if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore
    from PySide import QtCore
    from PySide import QtGui
    from PySide.QtCore import Qt
    from PySide.QtGui import QApplication


class _TaskPanelCfdMesh:
    """ The TaskPanel for editing References property of CfdMesh objects and creation of new CFD mesh """
    def __init__(self, obj):
        self.mesh_obj = obj
        self.form = FreeCADGui.PySideUic.loadUi(os.path.join(os.path.dirname(__file__), "TaskPanelCfdMesh.ui"))

        self.Timer = QtCore.QTimer()
        self.Start = time.time()
        self.console_message_cart = ''
        self.error_message = ''
        self.cart_mesh = CfdMeshTools.CfdMeshTools(self.mesh_obj)
        self.paraviewScriptName = ""

        self.mesh_process = CfdConsoleProcess(finishedHook=self.meshFinished,
                                              stdoutHook=self.gotOutputLines,
                                              stderrHook=self.gotErrorLines)
        self.edit_prcess = None

        self.form.cb_utility.activated.connect(self.choose_utility)
        self.Timer.timeout.connect(self.update_timer_text)

        self.open_paraview = QtCore.QProcess()

        self.form.pb_write_mesh.clicked.connect(self.writeMesh)
        self.form.pb_edit_mesh.clicked.connect(self.editMesh)
        self.form.pb_run_mesh.clicked.connect(self.runMesh)
        self.form.pb_stop_mesh.clicked.connect(self.killMeshProcess)
        self.form.pb_paraview.clicked.connect(self.openParaview)
        self.form.pb_load_mesh.clicked.connect(self.pbLoadMeshClicked)
        self.form.pb_clear_mesh.clicked.connect(self.pbClearMeshClicked)
        self.form.pb_searchPointInMesh.clicked.connect(self.searchPointInMesh)
        self.form.pb_stop_mesh.setEnabled(False)
        self.form.pb_paraview.setEnabled(False)
        self.form.snappySpecificProperties.setVisible(False)

        self.form.cb_dimension.addItems(_CfdMesh.known_element_dimensions)
        self.form.cb_utility.addItems(_CfdMesh.known_mesh_utility)

        self.form.if_max.setToolTip("Enter 0 to use default value")
        self.form.pb_searchPointInMesh.setToolTip("Specify below a point vector inside of the mesh or press 'Search' "
                                                  "to try to automatically find a point")
        self.form.if_cellsbetweenlevels.setToolTip("Number of cells between each of level of refinement")
        self.form.if_edgerefine.setToolTip("Number of refinement levels for all edges")

        self.load()
        self.updateUI()

    def getStandardButtons(self):
        return int(QtGui.QDialogButtonBox.Close)
        # def reject() is called on close button
        # def accept() in no longer needed, since there is no OK button

    def reject(self):
        # There is no reject - only close
        self.store()
        self.mesh_process.terminate()
        self.mesh_process.waitForFinished()
        self.open_paraview.terminate()
        FreeCADGui.ActiveDocument.resetEdit()
        FreeCAD.ActiveDocument.recompute()
        return True

    def load(self):
        """ Fills the widgets """
        setQuantity(self.form.if_max, self.mesh_obj.CharacteristicLengthMax)
        point_in_mesh = self.mesh_obj.PointInMesh.copy()
        setQuantity(self.form.if_pointInMeshX, point_in_mesh.get('x'))
        setQuantity(self.form.if_pointInMeshY, point_in_mesh.get('y'))
        setQuantity(self.form.if_pointInMeshZ, point_in_mesh.get('z'))
        self.form.if_cellsbetweenlevels.setValue(self.mesh_obj.CellsBetweenLevels)
        self.form.if_edgerefine.setValue(self.mesh_obj.EdgeRefinement)

        index_dimension = self.form.cb_dimension.findText(self.mesh_obj.ElementDimension)
        self.form.cb_dimension.setCurrentIndex(index_dimension)
        index_utility = self.form.cb_utility.findText(self.mesh_obj.MeshUtility)
        self.form.cb_utility.setCurrentIndex(index_utility)

    def updateUI(self):
        case_path = self.cart_mesh.meshCaseDir
        self.form.pb_edit_mesh.setEnabled(os.path.exists(case_path))
        self.form.pb_run_mesh.setEnabled(os.path.exists(os.path.join(case_path, "Allmesh")))
        self.form.pb_paraview.setEnabled(os.path.exists(os.path.join(case_path, "pv.foam")))
        self.form.pb_load_mesh.setEnabled(os.path.exists(os.path.join(case_path, "mesh_outside.stl")))
        utility = self.form.cb_utility.currentText()
        if utility == "snappyHexMesh":
            self.form.snappySpecificProperties.setVisible(True)
        elif utility == "cfMesh":
            self.form.snappySpecificProperties.setVisible(False)

    def store(self):
        FreeCADGui.doCommand("\nFreeCAD.ActiveDocument.{}.CharacteristicLengthMax "
                             "= '{}'".format(self.mesh_obj.Name, getQuantity(self.form.if_max)))
        FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.MeshUtility "
                             "= '{}'".format(self.mesh_obj.Name, self.form.cb_utility.currentText()))
        FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.ElementDimension "
                             "= '{}'".format(self.mesh_obj.Name, self.form.cb_dimension.currentText()))
        FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.CellsBetweenLevels "
                             "= {}".format(self.mesh_obj.Name, self.form.if_cellsbetweenlevels.value()))
        FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.EdgeRefinement "
                             "= {}".format(self.mesh_obj.Name, self.form.if_edgerefine.value()))
        point_in_mesh = {'x': getQuantity(self.form.if_pointInMeshX),
                         'y': getQuantity(self.form.if_pointInMeshY),
                         'z': getQuantity(self.form.if_pointInMeshZ)}
        FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.PointInMesh "
                             "= {}".format(self.mesh_obj.Name, point_in_mesh))
        self.cart_mesh = CfdMeshTools.CfdMeshTools(self.mesh_obj)

    def consoleMessage(self, message="", color="#000000", timed=True):
        if timed:
            self.console_message_cart = self.console_message_cart \
                                        + '<font color="#0000FF">{0:4.1f}:</font> <font color="{1}">{2}</font><br>'.\
                                        format(time.time() - self.Start, color, message)
        else:
            self.console_message_cart = self.console_message_cart \
                                        + '<font color="{0}">{1}</font><br>'.\
                                        format(color, message)
        self.form.te_output.setText(self.console_message_cart)
        self.form.te_output.moveCursor(QtGui.QTextCursor.End)
        if FreeCAD.GuiUp:
            FreeCAD.Gui.updateGui()

    def update_timer_text(self):
        delta = str(timedelta(seconds=time.time() - self.Start))[:-5]
        self.form.l_time.setText('Time: {}'.format(delta))

    def choose_utility(self, index):
        if index < 0:
            return
        utility = self.form.cb_utility.currentText()
        if utility == "snappyHexMesh":
            self.form.snappySpecificProperties.setVisible(True)
        else:
            self.form.snappySpecificProperties.setVisible(False)

    def writeMesh(self):
        import importlib
        importlib.reload(CfdMeshTools)
        self.console_message_cart = ''
        self.Start = time.time()
        self.Timer.start(100)
        # Re-initialise CfdMeshTools with new parameters
        self.store()
        FreeCADGui.addModule("CfdMeshTools")
        FreeCADGui.addModule("CfdTools")
        FreeCADGui.doCommand("FreeCAD.ActiveDocument." + self.mesh_obj.Name + ".Proxy.cart_mesh = "
                             "CfdMeshTools.CfdMeshTools(FreeCAD.ActiveDocument." + self.mesh_obj.Name + ")")
        FreeCADGui.doCommand("cart_mesh = FreeCAD.ActiveDocument." + self.mesh_obj.Name + ".Proxy.cart_mesh")
        cart_mesh = self.mesh_obj.Proxy.cart_mesh
        self.consoleMessage("Preparing meshing ...")
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            setQuantity(self.form.if_max, str(cart_mesh.getClmax()))
            print('Part to mesh:\n  Name: '
                  + cart_mesh.part_obj.Name + ', Label: '
                  + cart_mesh.part_obj.Label + ', ShapeType: '
                  + cart_mesh.part_obj.Shape.ShapeType)
            print('  CharacteristicLengthMax: ' + str(cart_mesh.clmax))
            analysis = CfdTools.getParentAnalysisObject(self.mesh_obj)
            FreeCADGui.doCommand("cart_mesh.getFilePaths(CfdTools.getOutputPath(FreeCAD.ActiveDocument." + analysis.Name + "))")
            FreeCADGui.doCommand("cart_mesh.setupMeshCaseDir()")
            self.consoleMessage("Exporting mesh refinement data ...")
            FreeCADGui.doCommand("cart_mesh.processRefinements()")  # Writes stls so need file structure
            FreeCADGui.doCommand("cart_mesh.processDimension()")
            FreeCADGui.doCommand("cart_mesh.writeMeshCase()")
            self.consoleMessage("Exporting the part surfaces ...")
            FreeCADGui.doCommand("cart_mesh.writePartFile()")
            self.consoleMessage("Mesh case written to {}".format(self.cart_mesh.meshCaseDir))
        except Exception as ex:
            self.consoleMessage("Error " + type(ex).__name__ + ": " + str(ex), '#FF0000')
            raise
        finally:
            self.Timer.stop()
            QApplication.restoreOverrideCursor()
        self.updateUI()

    def editMesh(self):
        case_path = self.cart_mesh.meshCaseDir
        self.consoleMessage("Please edit the case input files externally at: {}\n".format(case_path))
        CfdTools.openFileManager(case_path)

    def runMesh(self):
        self.Start = time.time()
        self.Timer.start(100)
        cart_mesh = self.cart_mesh
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.consoleMessage("Running {} ...".format(self.mesh_obj.MeshUtility))
            cart_mesh.error = False
            cmd = CfdTools.makeRunCommand('./Allmesh', cart_mesh.meshCaseDir, source_env=False)
            FreeCAD.Console.PrintMessage("Executing: " + ' '.join(cmd) + "\n")
            env_vars = CfdTools.getRunEnvironment()
            self.mesh_process.start(cmd, env_vars=env_vars)
            if self.mesh_process.waitForStarted():
                self.form.pb_run_mesh.setEnabled(False)  # Prevent user running a second instance
                self.form.pb_stop_mesh.setEnabled(True)
                self.form.pb_paraview.setEnabled(False)
                self.form.pb_load_mesh.setEnabled(False)
                self.consoleMessage("Mesher started")
            else:
                self.consoleMessage("Error starting meshing process", "#FF0000")
                cart_mesh.error = True
        except Exception as ex:
            self.consoleMessage("Error " + type(e).__name__ + ": " + str(ex), '#FF0000')
            raise
        finally:
            QApplication.restoreOverrideCursor()

    def killMeshProcess(self):
        self.consoleMessage("Meshing manually stopped")
        self.error_message = 'Meshing interrupted'
        self.mesh_process.terminate()
        # Note: meshFinished will still be called

    def gotOutputLines(self, lines):
        pass

    def gotErrorLines(self, lines):
        print_err = self.mesh_process.processErrorOutput(lines)
        if print_err is not None:
            self.consoleMessage(print_err, "#FF0000")

    def meshFinished(self, exit_code):
        if exit_code == 0:
            self.consoleMessage('Meshing completed')
            self.form.pb_run_mesh.setEnabled(True)
            self.form.pb_stop_mesh.setEnabled(False)
            self.form.pb_paraview.setEnabled(True)
            self.form.pb_load_mesh.setEnabled(True)
        else:
            self.consoleMessage("Meshing exited with error", "#FF0000")
            self.form.pb_run_mesh.setEnabled(True)
            self.form.pb_stop_mesh.setEnabled(False)
            self.form.pb_paraview.setEnabled(False)

        self.Timer.stop()
        self.error_message = ''
        # Get rid of any existing loaded mesh
        self.pbClearMeshClicked()
        self.updateUI()

    def openParaview(self):
        self.Start = time.time()
        QApplication.setOverrideCursor(Qt.WaitCursor)
        case_path = os.path.abspath(self.cart_mesh.meshCaseDir)
        script_name = "pvScriptMesh.py"
        try:
            self.open_paraview = CfdTools.startParaview(case_path, script_name, self.consoleMessage)
        finally:
            QApplication.restoreOverrideCursor()

    def pbLoadMeshClicked(self):
        self.consoleMessage("Reading mesh ...", timed=False)
        self.cart_mesh.loadSurfMesh()
        self.consoleMessage('Triangulated representation of the surface mesh is shown - ', timed=False)
        self.consoleMessage("Please view in Paraview for accurate display.\n", timed=False)

    def pbClearMeshClicked(self):
        for m in self.mesh_obj.Group:
            if m.isDerivedFrom("Fem::FemMeshObject"):
                FreeCAD.ActiveDocument.removeObject(m.Name)
        FreeCAD.ActiveDocument.recompute()

    def searchPointInMesh(self):
        print ("Searching for an internal vector point ...")
        # Apply latest mesh size
        self.store()
        pointCheck = self.cart_mesh.automaticInsidePointDetect()
        if pointCheck is not None:
            iMPx, iMPy, iMPz = pointCheck
            setQuantity(self.form.if_pointInMeshX, str(iMPx) + "mm")
            setQuantity(self.form.if_pointInMeshY, str(iMPy) + "mm")
            setQuantity(self.form.if_pointInMeshZ, str(iMPz) + "mm")
