# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2022 - Jonathan Bergh <bergh.jonathan@gmail.com>        *
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
import FreeCADGui
import os
from PySide import QtCore


class CfdMeshImporter:
    """
    A Utility class to allow importing of CFD meshes from other packages / formats, for
    example e.g. CGNS, Ansys Fluent (.msh)
    """

    def __init__(self, input_mesh_filename):
        self._mesh_type = self.getMeshType(input_mesh_filename)
        self._input_mesh_filename = input_mesh_filename
        self._output_mesh = None
        self._foam_convert_command = None

    def doImport(self):
        self.consoleMessage(f"Running {self._mesh_type} import ...")
        if self._mesh_type == '.cgns':  # CGNS
            self._foam_convert_command = 'cgnsToFoam'
        elif self._mesh_type == '.msh': # Fluent
            self._foam_convert_command = 'fluentMeshToFoam'
        else:
            raise RuntimeError(f'Import of mesh type {self._mesh_type} not supported or check your file extension')

        self._output_mesh = self._output_mesh = self.convert()

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

    @staticmethod
    def getMeshType(input_filename):
        filename, file_extension = os.path.splitext(input_filename)
        return file_extension
