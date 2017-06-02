# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2016 - Bernd Hahnebach <bernd@bimstatik.org>            *
# *   Copyright (c) 2017 - Alfred Bogaers (CSIR) <abogaers@csir.co.za>      *
# *   Copyright (c) 2017 - Johan Heyns (CSIR) <jheyns@csir.co.za>           *
# *   Copyright (c) 2017 - Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>        *
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

"""
Gmsh meshing UI for CFD analysis object. Adapted from equivalent classes
in FEM module but removes the option to generate second-order
mesh cells.
"""

__title__ = "_TaskPanelCfdMeshCart"
__author__ = "Bernd Hahnebach"
__url__ = "http://www.freecadweb.org"

import FreeCAD
import os
import sys
import os.path
import platform
# from PyObjects import _FemMeshGmsh
import _CfdMeshCart
import time
import tempfile
import CfdTools

if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore
    from PySide import QtCore
    from PySide import QtGui
    from PySide.QtCore import Qt
    from PySide.QtGui import QApplication
    import FemGui


class _TaskPanelCfdMeshCart:
    """ The TaskPanel for editing References property of CfdMeshCart objects and creation of new CFD mesh """
    def __init__(self, obj):
        self.mesh_obj = obj
        self.form = FreeCADGui.PySideUic.loadUi(os.path.join(os.path.dirname(__file__), "TaskPanelCfdMeshCart.ui"))

        self.mesh_process = QtCore.QProcess()
        self.Timer = QtCore.QTimer()
        self.Start = time.time()
        self.Timer.start(100)  # 100 milliseconds
        self.cart_runs = False
        self.console_message_cart = ''
        self.error_message = ''
        self.cart_mesh = []
        self.paraviewScriptName = ""

        QtCore.QObject.connect(self.mesh_process, QtCore.SIGNAL("readyReadStandardOutput()"), self.readOutput)
        QtCore.QObject.connect(self.mesh_process, QtCore.SIGNAL("readyReadStandardError()"), self.readOutput)
        QtCore.QObject.connect(self.mesh_process, QtCore.SIGNAL("finished(int)"), self.meshFinished)

        QtCore.QObject.connect(self.form.if_max, QtCore.SIGNAL("valueChanged(Base::Quantity)"), self.max_changed)
        # QtCore.QObject.connect(self.form.if_min, QtCore.SIGNAL("valueChanged(Base::Quantity)"), self.min_changed)
        QtCore.QObject.connect(self.form.cb_dimension, QtCore.SIGNAL("activated(int)"), self.choose_dimension)
        QtCore.QObject.connect(self.form.cb_utility, QtCore.SIGNAL("activated(int)"), self.choose_utility)
        QtCore.QObject.connect(self.Timer, QtCore.SIGNAL("timeout()"), self.update_timer_text)

        self.open_paraview = QtCore.QProcess()

        QtCore.QObject.connect(self.form.pb_run_mesh, QtCore.SIGNAL("clicked()"), self.runMeshProcess)
        QtCore.QObject.connect(self.form.pb_stop_mesh, QtCore.SIGNAL("clicked()"), self.killMeshProcess)
        QtCore.QObject.connect(self.form.pb_paraview, QtCore.SIGNAL("clicked()"), self.openParaview)
        self.form.pb_stop_mesh.setEnabled(False)
        self.form.pb_paraview.setEnabled(False)
        self.form.snappySpecificProperties.setVisible(False)

        # Limit mesh dimensions to 3D solids
        self.form.cb_dimension.addItems(_CfdMeshCart._CfdMeshCart.known_element_dimensions)
        self.form.cb_utility.addItems(_CfdMeshCart._CfdMeshCart.known_mesh_utility)

        self.get_mesh_params()
        self.order = '1st'  # Force first order for CFD mesh
        self.get_active_analysis()
        self.update()


    def getStandardButtons(self):
        return int(QtGui.QDialogButtonBox.Close)
        # def reject() is called on close button
        # def accept() in no longer needed, since there is no OK button

    def reject(self):
        self.mesh_obj.CharacteristicLengthMax = self.clmax
        self.set_mesh_params()

        FreeCADGui.ActiveDocument.resetEdit()
        FreeCAD.ActiveDocument.recompute()
        return True

    def get_mesh_params(self):
        self.clmax = self.mesh_obj.CharacteristicLengthMax
        self.dimension = self.mesh_obj.ElementDimension
        self.utility = self.mesh_obj.MeshUtility
        if self.utility == "snappyHexMesh":
            self.form.snappySpecificProperties.setVisible(True)
        elif self.utility == "cfMesh":
            self.form.snappySpecificProperties.setVisible(False)
        #self.nCellsBetweenLevels = self.mesh_obj.nCellsBetweenLevels
        #self.edgeRefineLevels = self.mesh_obj.edgeRefineLevels

    def set_mesh_params(self):
        self.mesh_obj.CharacteristicLengthMax = self.clmax
        self.mesh_obj.ElementDimension = self.dimension
        #self.mesh_obj.MeshUtility = self.utility
        self.mesh_obj.MeshUtility = self.form.cb_utility.currentText()
        print self.mesh_obj.MeshUtility
        self.mesh_obj.nCellsBetweenLevels = self.form.nCellsBetweenLevels.value()
        self.mesh_obj.edgeRefineLevels = self.form.edgeRefineLevels.value()

    def update(self):
        """ Fills the widgets """
        self.form.if_max.setText(self.clmax.UserString)
        self.form.if_max.setToolTip("Select 0 to use default value")
        index_dimension = self.form.cb_dimension.findText(self.dimension)
        self.form.cb_dimension.setCurrentIndex(index_dimension)
        index_utility = self.form.cb_utility.findText(self.utility)
        self.form.cb_utility.setCurrentIndex(index_utility)

        self.form.nCellsBetweenLevels.setValue(self.mesh_obj.nCellsBetweenLevels)
        self.form.edgeRefineLevels.setValue(self.mesh_obj.edgeRefineLevels)
        self.form.nCellsBetweenLevels.setToolTip("The number of cells between each of level of refinement.")
        self.form.edgeRefineLevels.setToolTip("Specify the number of refinement levels for all edges.")

    def console_log(self, message="", color="#000000"):
        self.console_message_cart = self.console_message_cart \
                                    + '<font color="#0000FF">{0:4.1f}:</font> <font color="{1}">{2}</font><br>'.\
                                    format(time.time()
                                    - self.Start, color, message.encode('utf-8', 'replace'))
        self.form.te_output.setText(self.console_message_cart)
        self.form.te_output.moveCursor(QtGui.QTextCursor.End)

    def update_timer_text(self):
        if self.cart_runs:
            self.form.l_time.setText('Time: {0:4.1f}'.format(time.time() - self.Start))

    def max_changed(self, base_quantity_value):
        self.clmax = base_quantity_value

    def choose_dimension(self, index):
        if index < 0:
            return
        self.form.cb_dimension.setCurrentIndex(index)
        self.dimension = str(self.form.cb_dimension.itemText(index))  # form returns unicode

    def choose_utility(self, index):
        if index < 0:
            return
        #self.form.cb_utility.setCurrentIndex(index)
        #self.utility = str(self.form.cb_utility.itemText(index))  # form returns unicode
        self.utility = self.form.cb_utility.currentText()
        if self.utility == "snappyHexMesh":
            self.form.snappySpecificProperties.setVisible(True)
        elif self.utility == "cfMesh":
            self.form.snappySpecificProperties.setVisible(False)

    def runMeshProcess(self):
        FreeCADGui.doCommand("\nFreeCAD.ActiveDocument.{}.CharacteristicLengthMax "
                             "= '{}'".format(self.mesh_obj.Name, self.clmax))
        FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.MeshUtility "
                             "= '{}'".format(self.mesh_obj.Name, self.utility))

        self.console_message_cart = ''
        self.cart_runs = True
        self.get_active_analysis()
        self.set_mesh_params()
        import CfdCartTools  # Fresh init before remeshing
        self.cart_mesh = CfdCartTools.CfdCartTools(self.obj)
        cart_mesh = self.cart_mesh
        self.form.if_max.setText(str(cart_mesh.get_clmax()))
        self.Start = time.time()
        self.console_log("Starting cut-cell Cartesian meshing ...")
        print("\nStarting cut-cell Cartesian meshing ...\n")
        print('  Part to mesh: Name --> '
              + cart_mesh.part_obj.Name + ',  Label --> '
              + cart_mesh.part_obj.Label + ', ShapeType --> '
              + cart_mesh.part_obj.Shape.ShapeType)
        print('  CharacteristicLengthMax: ' + str(cart_mesh.clmax))
        # print('  CharacteristicLengthMin: ' + str(cart_mesh.clmin))
        # print('  ElementOrder: ' + cart_mesh.order)
        cart_mesh.get_dimension()
        cart_mesh.get_tmp_file_paths(self.utility)
        cart_mesh.setupMeshCaseDir()
        cart_mesh.get_group_data()
        cart_mesh.get_region_data()
        cart_mesh.write_part_file()
        cart_mesh.setupMeshDict(self.utility)
        cart_mesh.createMeshScript(run_parallel = 'false',
                                   mesher_name = 'cartesianMesh',
                                   num_proc = 1,
                                   cartMethod = self.utility)  # Extend in time
        self.paraviewScriptName = self.cart_mesh.createParaviewScript()
        self.runCart(cart_mesh)

    def runCart(self, cart_mesh):
        cart_mesh.error = False
        QApplication.setOverrideCursor(Qt.WaitCursor)

        tmpdir = tempfile.gettempdir()
        meshCaseDir = os.path.join(tmpdir, 'meshCase')
        cmd = CfdTools.makeRunCommand('./Allmesh', meshCaseDir, source_env=False)
        FreeCAD.Console.PrintMessage("Executing: " + ' '.join(cmd) + "\n")
        self.mesh_process.start(cmd[0], cmd[1:])
        if self.mesh_process.waitForStarted():
            self.form.pb_run_mesh.setEnabled(False)  # Prevent user running a second instance
            self.form.pb_stop_mesh.setEnabled(True)
            self.form.pb_paraview.setEnabled(False)
        else:
            self.console_log("Error starting meshing process", "#FF0000")
            cart_mesh.error = True
        QApplication.restoreOverrideCursor()

    def killMeshProcess(self):
        self.console_log("Meshing manually stopped")
        self.error_message = 'Meshing interrupted'
        if platform.system() == 'Windows':
            self.mesh_process.kill()
        else:
            self.mesh_process.terminate()
        self.mesh_process.waitForFinished()
        self.form.pb_run_mesh.setEnabled(True)
        self.form.pb_stop_mesh.setEnabled(False)
        self.form.pb_paraview.setEnabled(False)
        self.Timer.stop()

    def readOutput(self):
        while self.mesh_process.canReadLine():
            print str(self.mesh_process.readLine()),  # Avoid displaying on FreeCAD status bar

        # Print any error output to console
        self.mesh_process.setReadChannel(QtCore.QProcess.StandardError)
        while self.mesh_process.canReadLine():
            err = str(self.mesh_process.readLine())
            self.console_log(err, "#FF0000")
            FreeCAD.Console.PrintError(err)
        self.mesh_process.setReadChannel(QtCore.QProcess.StandardOutput)

    def meshFinished(self):
        self.readOutput()
        self.console_log("Reading mesh")
        cart_mesh = self.cart_mesh
        cart_mesh.read_and_set_new_mesh()  # Only read once meshing has finished
        self.console_log('Meshing completed')
        self.console_log('Tetrahedral representation of the Cartesian mesh is shown')
        self.console_log("Warning: FEM Mesh may not display mesh accurately, please view in Paraview.\n")
        self.Timer.stop()
        self.update()
        self.form.pb_run_mesh.setEnabled(True)
        self.form.pb_stop_mesh.setEnabled(False)
        self.form.pb_paraview.setEnabled(True)
        self.error_message = ''

    def get_active_analysis(self):
        import FemGui
        self.analysis = FemGui.getActiveAnalysis()
        if self.analysis:
            for m in FemGui.getActiveAnalysis().Member:
                if m.Name == self.mesh_obj.Name:
                    print(self.analysis.Name)
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

        arg = '--script={}'.format(self.paraviewScriptName)

        self.console_log("Running " + paraview_cmd + " " +arg)
        self.open_paraview.start(paraview_cmd, [arg])
        QApplication.restoreOverrideCursor()