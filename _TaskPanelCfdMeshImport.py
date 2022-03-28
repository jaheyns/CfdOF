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

        self.form = FreeCADGui.PySideUic.loadUi(os.path.join(os.path.dirname(__file__), "TaskPanelCfdMeshImport.ui"))

        self.console_message_cart = ''
        self.error_message = ''

        self.Timer = QtCore.QTimer()
        self.Timer.setInterval(1000)
        self.Timer.timeout.connect(self.update_timer_text)

        self.mesh_input_filename = None

        self.form.pb_select_mesh.clicked.connect(self.openSelectMeshDialog)
        self.form.pb_clear_selection.clicked.connect(self.clearSelectedMeshFilename)
        self.form.pb_do_import.clicked.connect(self.doImport)

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
        FreeCADGui.addModule("CfdMeshImporterTools")
        FreeCADGui.doCommand("importer = CfdMeshImporterTools.CfdMeshImporter('" + self.mesh_input_filename + "')")
        FreeCADGui.doCommand("importer.doImport()")

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