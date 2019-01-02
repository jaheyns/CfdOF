# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2016 - Bernd Hahnebach <bernd@bimstatik.org>            *
# *   Copyright (c) 2017 - Alfred Bogaers (CSIR) <abogaers@csir.co.za>      *
# *   Copyright (c) 2017 - Johan Heyns (CSIR) <jheyns@csir.co.za>           *
# *   Copyright (c) 2017 - Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>        *
# *   Copyright (c) 2019 - Oliver Oxtoby <oliveroxtoby@gmail.com>           *
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
import sys
import os.path
import platform
import _CfdMesh
import time
import tempfile
import CfdTools
from CfdTools import inputCheckAndStore, setInputFieldQuantity
import CfdMeshTools
import Fem
from CfdConsoleProcess import CfdConsoleProcess

if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore
    from PySide import QtCore
    from PySide import QtGui
    from PySide.QtCore import Qt
    from PySide.QtGui import QApplication
    import FemGui


class _TaskPanelCfdMesh:
    """ The TaskPanel for editing References property of CfdMesh objects and creation of new CFD mesh """
    def __init__(self, obj):
        self.mesh_obj = obj
        self.form = FreeCADGui.PySideUic.loadUi(os.path.join(os.path.dirname(__file__), "TaskPanelCfdMesh.ui"))

        self.Timer = QtCore.QTimer()
        self.console_message_cart = ''
        self.error_message = ''
        self.cart_mesh = CfdMeshTools.CfdMeshTools(self.mesh_obj)
        self.paraviewScriptName = ""

        self.mesh_process = CfdConsoleProcess(finishedHook=self.meshFinished,
                                              stdoutHook=self.gotOutputLines,
                                              stderrHook=self.gotErrorLines)

        QtCore.QObject.connect(self.form.if_max, QtCore.SIGNAL("valueChanged(Base::Quantity)"), self.max_changed)
        QtCore.QObject.connect(self.form.if_pointInMeshX, QtCore.SIGNAL("valueChanged(Base::Quantity)"),
                               self.pointInMeshX_changed)
        QtCore.QObject.connect(self.form.if_pointInMeshY, QtCore.SIGNAL("valueChanged(Base::Quantity)"),
                               self.pointInMeshY_changed)
        QtCore.QObject.connect(self.form.if_pointInMeshZ, QtCore.SIGNAL("valueChanged(Base::Quantity)"),
                               self.pointInMeshZ_changed)
        QtCore.QObject.connect(self.form.if_cellsbetweenlevels, QtCore.SIGNAL("valueChanged(int)"),
                               self.cellsbetweenlevels_changed)
        QtCore.QObject.connect(self.form.if_edgerefine, QtCore.SIGNAL("valueChanged(int)"), self.edgerefine_changed)
        QtCore.QObject.connect(self.form.cb_dimension, QtCore.SIGNAL("activated(int)"), self.choose_dimension)
        QtCore.QObject.connect(self.form.cb_utility, QtCore.SIGNAL("activated(int)"), self.choose_utility)
        QtCore.QObject.connect(self.Timer, QtCore.SIGNAL("timeout()"), self.update_timer_text)

        self.open_paraview = QtCore.QProcess()

        QtCore.QObject.connect(self.form.pb_run_mesh, QtCore.SIGNAL("clicked()"), self.runMeshProcess)
        QtCore.QObject.connect(self.form.pb_stop_mesh, QtCore.SIGNAL("clicked()"), self.killMeshProcess)
        QtCore.QObject.connect(self.form.pb_paraview, QtCore.SIGNAL("clicked()"), self.openParaview)
        self.form.pb_load_mesh.clicked.connect(self.pbLoadMeshClicked)
        self.form.pb_clear_mesh.clicked.connect(self.pbClearMeshClicked)
        QtCore.QObject.connect(self.form.pb_searchPointInMesh, QtCore.SIGNAL("clicked()"), self.searchPointInMesh)
        self.form.pb_stop_mesh.setEnabled(False)
        self.form.pb_paraview.setEnabled(False)
        self.form.snappySpecificProperties.setVisible(False)

        self.form.cb_dimension.addItems(_CfdMesh._CfdMesh.known_element_dimensions)
        self.form.cb_utility.addItems(_CfdMesh._CfdMesh.known_mesh_utility)

        self.form.if_max.setToolTip("Select 0 to use default value")
        self.form.pb_searchPointInMesh.setToolTip("Specify below a point vector inside of the mesh or press 'Search' "
                                                  "to try and automatically find a point")
        self.form.if_cellsbetweenlevels.setToolTip("Number of cells between each of level of refinement.")
        self.form.if_edgerefine.setToolTip("Number of refinement levels for all edges.")

        self.get_mesh_params()
        self.order = '1st'  # Default to first order for CFD mesh
        self.get_active_analysis()
        self.update()
        self.form.pb_paraview.setEnabled(os.path.exists(os.path.join(self.cart_mesh.meshCaseDir, "pv.foam")))
        self.form.pb_load_mesh.setEnabled(os.path.exists(os.path.join(self.cart_mesh.meshCaseDir, "mesh_outside.stl")))

    def getStandardButtons(self):
        return int(QtGui.QDialogButtonBox.Close)
        # def reject() is called on close button
        # def accept() in no longer needed, since there is no OK button

    def reject(self):
        # There is no reject - only close
        self.set_mesh_params()

        FreeCADGui.ActiveDocument.resetEdit()
        FreeCAD.ActiveDocument.recompute()
        return True

    def get_mesh_params(self):
        self.clmax = self.mesh_obj.CharacteristicLengthMax
        self.PointInMesh = self.mesh_obj.PointInMesh.copy()
        self.cellsbetweenlevels = self.mesh_obj.CellsBetweenLevels
        self.edgerefine = self.mesh_obj.EdgeRefinement
        self.dimension = self.mesh_obj.ElementDimension
        self.utility = self.mesh_obj.MeshUtility
        if self.utility == "snappyHexMesh":
            self.form.snappySpecificProperties.setVisible(True)
        elif self.utility == "cfMesh":
            self.form.snappySpecificProperties.setVisible(False)

    def set_mesh_params(self):
        FreeCADGui.doCommand("\nFreeCAD.ActiveDocument.{}.CharacteristicLengthMax "
                             "= '{}'".format(self.mesh_obj.Name, self.clmax))
        FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.MeshUtility "
                             "= '{}'".format(self.mesh_obj.Name, self.utility))
        FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.ElementDimension "
                             "= '{}'".format(self.mesh_obj.Name, self.dimension))
        FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.CellsBetweenLevels "
                             "= {}".format(self.mesh_obj.Name, self.cellsbetweenlevels))
        FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.EdgeRefinement "
                             "= {}".format(self.mesh_obj.Name, self.edgerefine))
        FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.PointInMesh "
                             "= {}".format(self.mesh_obj.Name, self.PointInMesh))

    def update(self):
        """ Fills the widgets """
        setInputFieldQuantity(self.form.if_max, self.clmax)
        setInputFieldQuantity(self.form.if_pointInMeshX, str(self.PointInMesh.get('x')) + "mm")
        setInputFieldQuantity(self.form.if_pointInMeshY, str(self.PointInMesh.get('y')) + "mm")
        setInputFieldQuantity(self.form.if_pointInMeshZ, str(self.PointInMesh.get('z')) + "mm")
        self.form.if_cellsbetweenlevels.setValue(self.cellsbetweenlevels)
        self.form.if_edgerefine.setValue(self.edgerefine)

        index_dimension = self.form.cb_dimension.findText(self.dimension)
        self.form.cb_dimension.setCurrentIndex(index_dimension)
        index_utility = self.form.cb_utility.findText(self.utility)
        self.form.cb_utility.setCurrentIndex(index_utility)

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
        self.form.l_time.setText('Time: {0:4.1f}'.format(time.time() - self.Start))

    def max_changed(self, base_quantity_value):
        self.clmax = base_quantity_value

    def pointInMeshX_changed(self, base_quantity_value):
        inputCheckAndStore(base_quantity_value, "mm", self.PointInMesh, 'x')

    def pointInMeshY_changed(self, base_quantity_value):
        inputCheckAndStore(base_quantity_value, "mm", self.PointInMesh, 'y')

    def pointInMeshZ_changed(self, base_quantity_value):
        inputCheckAndStore(base_quantity_value, "mm", self.PointInMesh, 'z')

    def cellsbetweenlevels_changed(self, base_quantity_value):
        self.cellsbetweenlevels = base_quantity_value

    def edgerefine_changed(self, base_quantity_value):
        self.edgerefine = base_quantity_value

    def choose_dimension(self, index):
        if index < 0:
            return
        self.form.cb_dimension.setCurrentIndex(index)
        self.dimension = str(self.form.cb_dimension.itemText(index))  # form returns unicode

    def choose_utility(self, index):
        if index < 0:
            return
        self.utility = self.form.cb_utility.currentText()
        if self.utility == "snappyHexMesh":
            self.form.snappySpecificProperties.setVisible(True)
        else:
            self.form.snappySpecificProperties.setVisible(False)

    def runMeshProcess(self):
        self.console_message_cart = ''
        self.Start = time.time()
        self.Timer.start()
        # Re-initialise CfdMeshTools with new parameters
        self.set_mesh_params()
        self.cart_mesh = CfdMeshTools.CfdMeshTools(self.mesh_obj)
        self.consoleMessage("Starting meshing ...")
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.get_active_analysis()
            self.set_mesh_params()
            cart_mesh = self.cart_mesh
            setInputFieldQuantity(self.form.if_max, str(cart_mesh.get_clmax()))
            print("\nStarting meshing ...\n")
            print('  Part to mesh: Name --> '
                  + cart_mesh.part_obj.Name + ',  Label --> '
                  + cart_mesh.part_obj.Label + ', ShapeType --> '
                  + cart_mesh.part_obj.Shape.ShapeType)
            print('  CharacteristicLengthMax: ' + str(cart_mesh.clmax))
            cart_mesh.get_dimension()
            cart_mesh.get_file_paths(CfdTools.getOutputPath(self.analysis))
            cart_mesh.setup_mesh_case_dir()
            self.consoleMessage("Exporting mesh region data ...")
            cart_mesh.get_region_data()  # Writes region stls so need file structure
            cart_mesh.write_mesh_case()
            self.consoleMessage("Exporting the part surfaces ...")
            cart_mesh.write_part_file()
            self.consoleMessage("Running {} ...".format(self.utility))
            self.runCart(cart_mesh)
        except Exception as ex:
            self.consoleMessage("Error: " + str(ex), '#FF0000')
            self.Timer.stop()
            raise
        finally:
            QApplication.restoreOverrideCursor()

    def runCart(self, cart_mesh):
        cart_mesh.error = False
        cmd = CfdTools.makeRunCommand('./Allmesh', cart_mesh.meshCaseDir, source_env=False)
        FreeCAD.Console.PrintMessage("Executing: " + ' '.join(cmd) + "\n")
        env_vars = CfdTools.getRunEnvironment()
        QApplication.setOverrideCursor(Qt.WaitCursor)
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
        QApplication.restoreOverrideCursor()

    def killMeshProcess(self):
        self.consoleMessage("Meshing manually stopped")
        self.error_message = 'Meshing interrupted'
        self.mesh_process.terminate()
        # Note: solverFinished will still be called

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
        self.update()
        self.error_message = ''
        # Get rid of any existing loaded mesh
        self.pbClearMeshClicked()

    def get_active_analysis(self):
        import FemGui
        self.analysis = FemGui.getActiveAnalysis()
        if self.analysis:
            for m in FemGui.getActiveAnalysis().Group:
                if m.Name == self.mesh_obj.Name:
                    return
            else:
                # print('Mesh is not member of active analysis, means no group meshing')
                self.analysis = None  # no group meshing
        else:
            # print('No active analyis, means no group meshing')
            self.analysis = None  # no group meshing

    def openParaview(self):
        self.Start = time.time()
        QApplication.setOverrideCursor(Qt.WaitCursor)

        paraview_cmd = "paraview"
        # If using blueCFD, use paraview supplied
        if CfdTools.getFoamRuntime() == 'BlueCFD':
            paraview_cmd = '{}\\..\\AddOns\\ParaView\\bin\\paraview.exe'.format(CfdTools.getFoamDir())
        # Otherwise, the command 'paraview' must be in the path. Possibly make path user-settable.
        # Test to see if it exists, as the exception thrown is cryptic on Windows if it doesn't
        import distutils.spawn
        if distutils.spawn.find_executable(paraview_cmd) is None:
            raise IOError("Paraview executable " + paraview_cmd + " not found in path.")

        self.paraviewScriptName = os.path.join(self.cart_mesh.meshCaseDir, 'pvScriptMesh.py')
        arg = '--script={}'.format(self.paraviewScriptName)

        self.consoleMessage("Running " + paraview_cmd + " " +arg)
        self.open_paraview.start(paraview_cmd, [arg])
        QApplication.restoreOverrideCursor()

    def pbLoadMeshClicked(self):
        self.consoleMessage("Reading mesh ...", timed=False)
        self.cart_mesh.read_and_set_new_mesh()
        self.consoleMessage('Triangulated representation of the surface mesh is shown - ', timed=False)
        self.consoleMessage("Please view in Paraview for accurate display.\n", timed=False)

    def pbClearMeshClicked(self):
        self.mesh_obj.FemMesh = Fem.FemMesh()
        FreeCAD.ActiveDocument.recompute()

    def searchPointInMesh(self):
        print ("Searching for an internal vector point ...")
        # Apply latest mesh size
        self.set_mesh_params()
        pointCheck = self.cart_mesh.automatic_inside_point_detect()
        iMPx, iMPy, iMPz = pointCheck
        setInputFieldQuantity(self.form.if_pointInMeshX, str(iMPx) + "mm")
        setInputFieldQuantity(self.form.if_pointInMeshY, str(iMPy) + "mm")
        setInputFieldQuantity(self.form.if_pointInMeshZ, str(iMPz) + "mm")
