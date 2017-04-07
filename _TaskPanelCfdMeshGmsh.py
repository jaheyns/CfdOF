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

__title__ = "_TaskPanelCfdMeshGmsh"
__author__ = "Bernd Hahnebach"
__url__ = "http://www.freecadweb.org"

import FreeCAD
import os
import sys
import os.path
import platform
from PyObjects import _FemMeshGmsh
import time

if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore
    from PySide import QtCore
    from PySide import QtGui
    from PySide.QtCore import Qt
    from PySide.QtGui import QApplication
    import FemGui


class _TaskPanelCfdMeshGmsh:
    '''The TaskPanel for editing References property of FemMeshGmsh objects and creation of new CFD mesh'''
    def __init__(self, obj):
        self.mesh_obj = obj
        self.form = FreeCADGui.PySideUic.loadUi(os.path.join(os.path.dirname(__file__), "TaskPanelCfdMeshGmsh.ui"))

        self.mesh_process = QtCore.QProcess()
        self.Timer = QtCore.QTimer()
        self.Start = time.time()
        self.console_message_gmsh = ''
        self.error_message = ''
        self.gmsh_mesh = []

        QtCore.QObject.connect(self.mesh_process, QtCore.SIGNAL("readyReadStandardOutput()"), self.readOutput)
        QtCore.QObject.connect(self.mesh_process, QtCore.SIGNAL("readyReadStandardError()"), self.readOutput)
        QtCore.QObject.connect(self.mesh_process, QtCore.SIGNAL("finished(int)"), self.meshFinished)

        QtCore.QObject.connect(self.form.if_max, QtCore.SIGNAL("valueChanged(Base::Quantity)"), self.max_changed)
        QtCore.QObject.connect(self.form.if_min, QtCore.SIGNAL("valueChanged(Base::Quantity)"), self.min_changed)
        QtCore.QObject.connect(self.form.cb_dimension, QtCore.SIGNAL("activated(int)"), self.choose_dimension)
        QtCore.QObject.connect(self.Timer, QtCore.SIGNAL("timeout()"), self.update_timer_text)

        QtCore.QObject.connect(self.form.pb_run_mesh, QtCore.SIGNAL("clicked()"), self.runMeshProcess)
        QtCore.QObject.connect(self.form.pb_stop_mesh, QtCore.SIGNAL("clicked()"), self.killMeshProcess)
        self.form.pb_stop_mesh.setEnabled(False)

        self.form.cb_dimension.addItems(_FemMeshGmsh._FemMeshGmsh.known_element_dimensions)

        self.get_mesh_params()
        self.order = '1st'  # Force first order for CFD mesh
        self.get_active_analysis()
        self.update()

    def getStandardButtons(self):
        return int(QtGui.QDialogButtonBox.Close)
        # def reject() is called on close button
        # def accept() in no longer needed, since there is no OK button

    def reject(self):
        # To be safe, cancel timer in case of unexpected error in meshing
        self.Timer.stop()

        FreeCADGui.ActiveDocument.resetEdit()
        FreeCAD.ActiveDocument.recompute()

        return True

    def get_mesh_params(self):
        self.clmax = self.mesh_obj.CharacteristicLengthMax
        self.clmin = self.mesh_obj.CharacteristicLengthMin
        self.order = self.mesh_obj.ElementOrder
        self.dimension = self.mesh_obj.ElementDimension

    def set_mesh_params(self):
        self.mesh_obj.CharacteristicLengthMax = self.clmax
        self.mesh_obj.CharacteristicLengthMin = self.clmin
        self.mesh_obj.ElementOrder = self.order
        self.mesh_obj.ElementDimension = self.dimension

    def update(self):
        """ Fills the widgets """
        self.form.if_max.setText(self.clmax.UserString)
        self.form.if_max.setToolTip("Select 0 to use default value")
        self.form.if_min.setText(self.clmin.UserString)
        self.form.if_min.setToolTip("Select 0 to use default value")
        index_dimension = self.form.cb_dimension.findText(self.dimension)
        self.form.cb_dimension.setCurrentIndex(index_dimension)

    def console_log(self, message="", color="#000000"):
        self.console_message_gmsh = self.console_message_gmsh \
                                    + '<font color="#0000FF">{0:4.1f}:</font> <font color="{1}">{2}</font><br>'.\
                                    format(time.time()
                                    - self.Start, color, message.encode('utf-8', 'replace'))
        self.form.te_output.setText(self.console_message_gmsh)
        self.form.te_output.moveCursor(QtGui.QTextCursor.End)

    def update_timer_text(self):
        self.form.l_time.setText('Time: {0:4.1f}'.format(time.time() - self.Start))

    def max_changed(self, base_quantity_value):
        self.clmax = base_quantity_value

    def min_changed(self, base_quantity_value):
        self.clmin = base_quantity_value

    def choose_dimension(self, index):
        if index < 0:
            return
        self.form.cb_dimension.setCurrentIndex(index)
        self.dimension = str(self.form.cb_dimension.itemText(index))  # form returns unicode

    def runMeshProcess(self):
        self.console_message_gmsh = ''
        self.get_active_analysis()
        self.set_mesh_params()
        import FemGmshTools  # Fresh init before remeshing
        self.gmsh_mesh = FemGmshTools.FemGmshTools(self.obj)
        gmsh_mesh = self.gmsh_mesh
        self.Start = time.time()
        self.Timer.start(100)  # 100 milliseconds
        self.console_log("Starting GMSH ...")
        print("\nStarted GMSH meshing ...\n")
        print('  Part to mesh: Name --> '
              + gmsh_mesh.part_obj.Name + ',  Label --> '
              + gmsh_mesh.part_obj.Label + ', ShapeType --> '
              + gmsh_mesh.part_obj.Shape.ShapeType)
        print('  CharacteristicLengthMax: ' + str(gmsh_mesh.clmax))
        print('  CharacteristicLengthMin: ' + str(gmsh_mesh.clmin))
        print('  ElementOrder: ' + gmsh_mesh.order)
        gmsh_mesh.get_dimension()
        gmsh_mesh.get_tmp_file_paths()
        gmsh_mesh.get_gmsh_command()
        gmsh_mesh.get_group_data()
        gmsh_mesh.write_part_file()
        gmsh_mesh.write_geo()
        self.runGmsh(gmsh_mesh)

    def runGmsh(self, gmsh_mesh):
        gmsh_mesh.error = False
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.console_log("Executing: {} {}".format(gmsh_mesh.gmsh_bin, gmsh_mesh.temp_file_geo))
        self.mesh_process.start(gmsh_mesh.gmsh_bin, ['-', gmsh_mesh.temp_file_geo])
        if self.mesh_process.waitForStarted():
            self.form.pb_run_mesh.setEnabled(False)  # Prevent user running a second instance
            self.form.pb_stop_mesh.setEnabled(True)
        else:
            self.console_log("Error starting meshing process", "#FF0000")
            gmsh_mesh.error = True
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
        #self.readOutput()
        self.console_log("Reading mesh")
        gmsh_mesh = self.gmsh_mesh
        try:
            gmsh_mesh.read_and_set_new_mesh()  # Only read once meshing has finished
            self.console_log('Meshing completed')
        except RuntimeError as e:
            self.console_log('Could not read mesh: ' + e.message())
        self.Timer.stop()
        self.update()
        self.form.pb_run_mesh.setEnabled(True)
        self.form.pb_stop_mesh.setEnabled(False)
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
