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

__title__ = "Command cut-cell Cartesian Mesh From Shape"
__author__ = "Bernd Hahnebach"
__url__ = "http://www.freecadweb.org"

import FreeCAD
import platform
from PyGui.FemCommands import FemCommands
import FreeCADGui
import FemGui
from PySide import QtCore
import CfdTools
import os

class _CommandCfdMeshCartFromShape(FemCommands):
    # the Cfd_MeshCartFromShape command definition
    def __init__(self):
        super(_CommandCfdMeshCartFromShape, self).__init__()
        icon_path = os.path.join(CfdTools.get_module_path(),"Gui","Resources","icons","mesh_c.png")
        self.resources = {'Pixmap': icon_path,
                          'MenuText': QtCore.QT_TRANSLATE_NOOP("Cfd_MeshCartFromShape", "Cut-cell Cartesian mesh from shape"),
                          'ToolTip': QtCore.QT_TRANSLATE_NOOP("Cfd_MeshCartFromShape", "Create a Cut-cell Cartesian mesh from a shape")}
        self.is_active = 'with_part_feature'

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Create cut-cell Cartesian mesh")
        FreeCADGui.addModule("FemGui")
        analysis_obj = FemGui.getActiveAnalysis()
        meshObj= CfdTools.getMesh(analysis_obj)
        if not meshObj:
            sel = FreeCADGui.Selection.getSelection()
            if (len(sel) == 1):
                if(sel[0].isDerivedFrom("Part::Feature")):
                    mesh_obj_name = sel[0].Name + "_CartesianMesh"
                    FreeCADGui.addModule("CfdMeshCart")
                    FreeCADGui.doCommand("CfdMeshCart.makeCfdMeshCart('" + mesh_obj_name + "')")
                    FreeCADGui.doCommand("App.ActiveDocument.ActiveObject.Part = App.ActiveDocument." + sel[0].Name)
                    if FemGui.getActiveAnalysis():
                        FreeCADGui.addModule("FemGui")
                        FreeCADGui.doCommand("FemGui.getActiveAnalysis().Member = FemGui.getActiveAnalysis().Member + [App.ActiveDocument.ActiveObject]")
                    FreeCADGui.doCommand("Gui.ActiveDocument.setEdit(App.ActiveDocument.ActiveObject.Name)")
        else:
            print "ERROR: You cannot have more than one mesh object"
        FreeCADGui.Selection.clearSelection()


FreeCADGui.addCommand('Cfd_MeshCartFromShape', _CommandCfdMeshCartFromShape())
