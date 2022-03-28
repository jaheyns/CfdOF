# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2022 Jonathan Bergh <bergh.jonathan@gmail.com>          *
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

import FreeCAD
import os
import os.path
import time
import CfdTools
from CfdTools import setQuantity, getQuantity
if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtGui, QtCore


class _TaskPanelCfdMeshImport:
    """ Task Panel for CFD mesh importing tasks """
    def __init__(self, obj):
        self.obj = obj

        self.form = FreeCADGui.PySideUic.loadUi(os.path.join(os.path.dirname(__file__),
                                                             "core/gui/TaskPanelCfdMeshImport.ui"))

        self.console_message_cart = ''
        self.error_message = ''

        self.Timer = QtCore.QTimer()
        self.Timer.setInterval(1000)
        self.Timer.timeout.connect(self.update_timer_text)

        self.mesh_input_filename = None
        self.mesh_type = None

        self.form.pb_select_mesh.clicked.connect(self.openSelectMeshDialog)
        self.form.pb_clear_selection.clicked.connect(self.clearSelectedMeshFilename)
        self.form.pb_do_import.clicked.connect(self.doImport)

        self._output_mesh = None
        self._foam_convert_command = None

        self.Start = time.time()
        self.Timer.start()

    def closed(self):
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()
        # return True  # TODO Jonathan - check this is correct

    def reject(self):
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()
        # return True  # TODO Jonathan - check this is correct

    def openSelectMeshDialog(self):
        path = FreeCAD.ConfigGet("UserHomePath")
        self.mesh_input_filename, Filter = QtGui.QFileDialog.getOpenFileName(None, "Read a mesh file", path, "")
        if self.mesh_input_filename is not None:
            self.form.labelInputMeshFilename.setText(self.mesh_input_filename)

    def clearSelectedMeshFilename(self):
        self.form.labelInputMeshFilename.setText("")
        self.mesh_input_filename = None

    def doImport(self):
        self.mesh_type = self.getMeshType(self.mesh_input_filename)
        self.consoleMessage(f"Running {self.mesh_type} import ...")
        if self.mesh_type == '.cgns':  # CGNS
            self._foam_convert_command = 'cgnsToFoam'
        elif self.mesh_type == '.msh': # Fluent
            self._foam_convert_command = 'fluentMeshToFoam'
        else:
            raise RuntimeError(f'Import of mesh type {self.mesh_type} not supported or check your file extension')

        self._output_mesh = self.convert()

        return self._output_mesh

    def convert(self):
        self.Start = time.time()
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            FreeCADGui.addModule("CfdMeshTools")
            FreeCADGui.addModule("CfdTools")
            FreeCADGui.addModule("CfdConsoleProcess")
            FreeCADGui.doCommand("cart_mesh = "
                                 "CfdMeshTools.CfdMeshTools(FreeCAD.ActiveDocument." + self.mesh_obj.Name + ")")
            FreeCADGui.doCommand("proxy = FreeCAD.ActiveDocument." + self.mesh_obj.Name + ".Proxy")
            FreeCADGui.doCommand("proxy.cart_mesh = cart_mesh")
            FreeCADGui.doCommand("cart_mesh.error = False")
            FreeCADGui.doCommand("cmd = CfdTools.makeRunCommand(f'{" + self._foam_convert_command + "} ' "
                                    "{" + self._input_mesh_filename + "}, cart_mesh.meshCaseDir, source_env=False)")
            FreeCADGui.doCommand("FreeCAD.Console.PrintMessage('Executing: ' + ' '.join(cmd) + '\\n')")
            FreeCADGui.doCommand("env_vars = CfdTools.getRunEnvironment()")
            FreeCADGui.doCommand("proxy.running_from_macro = True")
            self.mesh_obj.Proxy.running_from_macro = False
            FreeCADGui.doCommand("if proxy.running_from_macro:\n" +
                                 "  mesh_process = CfdConsoleProcess.CfdConsoleProcess()\n" +
                                 "  mesh_process.start(cmd, env_vars=env_vars)\n" +
                                 "  mesh_process.waitForFinished()\n" +
                                 "else:\n" +
                                 "  proxy.mesh_process.start(cmd, env_vars=env_vars)")
            if self.mesh_obj.Proxy.mesh_process.waitForStarted():
                self.consoleMessage("Mesh import started")
            else:
                self.consoleMessage("Error importing mesh", "#FF0000")
                self.mesh_obj.Proxy.cart_mesh.error = True
        except Exception as ex:
            self.consoleMessage("Error " + type(ex).__name__ + ": " + str(ex), '#FF0000')
            raise
        finally:
            QApplication.restoreOverrideCursor()

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
        # if self.mesh_obj.Proxy.mesh_process.state() == QtCore.QProcess.ProcessState.Running: # todo Jonathan - fix this once we have a import_obj
        #     self.form.l_time.setText('Time: ' + CfdTools.formatTimer(time.time() - self.Start))
        pass

    @staticmethod
    def getMeshType(input_filename):
        filename, file_extension = os.path.splitext(input_filename)
        return file_extension
