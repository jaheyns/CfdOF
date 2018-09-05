# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2016 - Bernd Hahnebach <bernd@bimstatik.org>            *
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

__title__ = "Command Mesh From Shape"
__author__ = "Bernd Hahnebach"
__url__ = "http://www.freecadweb.org"

import FreeCAD
import platform
try:
    from femcommands.manager import CommandManager
except ImportError:  # Backward compatibility
    from PyGui.FemCommands import FemCommands as CommandManager
import FreeCADGui
import FemGui
from PySide import QtCore
import CfdTools
import os


class _CommandCfdMeshFromShape(CommandManager):
    # the Cfd_MeshFromShape command definition
    def __init__(self):
        super(_CommandCfdMeshFromShape, self).__init__()
        icon_path = os.path.join(CfdTools.get_module_path(), "Gui", "Resources", "icons", "mesh.png")
        self.resources = {'Pixmap': icon_path,
                          'MenuText': QtCore.QT_TRANSLATE_NOOP("Cfd_MeshFromShape",
                                                               "CFD mesh"),
                          'ToolTip': QtCore.QT_TRANSLATE_NOOP("Cfd_MeshFromShape",
                                                              "Create a mesh using cfMesh, snappyHexMesh or gmsh")}
        self.is_active = 'with_part_feature'

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Create CFD mesh")
        FreeCADGui.addModule("FemGui")
        analysis_obj = FemGui.getActiveAnalysis()
        if analysis_obj:
            meshObj = CfdTools.getMesh(analysis_obj)
        else:
            meshObj = None
        if not meshObj:
            sel = FreeCADGui.Selection.getSelection()
            if len(sel) == 1:
                if sel[0].isDerivedFrom("Part::Feature"):
                    mesh_obj_name = sel[0].Name + "_Mesh"
                    FreeCADGui.addModule("CfdMesh")
                    FreeCADGui.doCommand("CfdMesh.makeCfdMesh('" + mesh_obj_name + "')")
                    FreeCADGui.doCommand("App.ActiveDocument.ActiveObject.Part = App.ActiveDocument." + sel[0].Name)
                    if FemGui.getActiveAnalysis():
                        FreeCADGui.addModule("FemGui")
                        FreeCADGui.doCommand("FemGui.getActiveAnalysis().addObject(App.ActiveDocument.ActiveObject)")
                    FreeCADGui.ActiveDocument.setEdit(FreeCAD.ActiveDocument.ActiveObject.Name)
        else:
            print("ERROR: You cannot have more than one mesh object")
        FreeCADGui.Selection.clearSelection()

FreeCADGui.addCommand('Cfd_MeshFromShape', _CommandCfdMeshFromShape())
