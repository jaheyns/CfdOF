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
import FreeCADGui
from CfdMesh import _CfdMesh
from PySide import QtCore
import os
import CfdTools
from CfdTools import addObjectProperty
from pivy import coin
import Part
from core.mesh.dynamic import _TaskPanelCfdDynamicMeshRefinement

def makeCfdDynamicMeshRefinement(base_mesh, name="DynamicMeshRefinement"):
    """ makeCfdDynamicMeshRefinement([name]):
        Creates an object to define dynamic mesh refinement properties and existing mesh if the solver supports it
    """
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", name)
    _CfdDynamicMeshRefinement(obj)
    if FreeCAD.GuiUp:
        _ViewProviderCfdDynamicMeshRefinement(obj.ViewObject)
    base_mesh.addObject(obj)
    return obj


class _CommandDynamicMesh:

    def __init__(self):
        pass

    def GetResources(self):
        icon_path = os.path.join(CfdTools.get_module_path(), "Gui", "Resources", "icons", "meshdynamic.png")
        return {'Pixmap': icon_path,
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Cfd_DynamicMesh", "Dynamic mesh refinement"),
                'Accel': "M, R",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Cfd_DynamicMesh", "Creates a dynamic mesh refinement rule")}

    def IsActive(self):
        sel = FreeCADGui.Selection.getSelection()
        return sel and len(sel) == 1 and hasattr(sel[0], "Proxy") and isinstance(sel[0].Proxy, _CfdMesh)

    def Activated(self):
        sel = FreeCADGui.Selection.getSelection()
        if len(sel) == 1:
            sobj = sel[0]
            if len(sel) == 1 and hasattr(sobj, "Proxy") and isinstance(sobj.Proxy, _CfdMesh):
                FreeCAD.ActiveDocument.openTransaction("Create DynamicMesh")
                FreeCADGui.doCommand("")
                FreeCADGui.addModule("core.mesh.dynamic.CfdDynamicMeshRefinement as CfdDynamicMeshRefinement")
                FreeCADGui.doCommand(
                    "CfdDynamicMeshRefinement.makeCfdDynamicMeshRefinement(App.ActiveDocument.{})".format(sobj.Name))
                FreeCADGui.ActiveDocument.setEdit(FreeCAD.ActiveDocument.ActiveObject.Name)

        FreeCADGui.Selection.clearSelection()







class _CfdDynamicMeshRefinement:

    def __init__(self, obj):
        obj.Proxy = self
        self.Type = "_CfdDynamicMeshRefinement"
        self.initProperties(obj)

    def initProperties(self, obj):
        # Common to all
        if addObjectProperty(obj, 'ShapeRefs', [], "App::PropertyLinkSubList",
                             "", "List of mesh refinement objects"):
            # Backward compat
            if 'References' in obj.PropertiesList:
                doc = FreeCAD.getDocument(obj.Document.Name)
                for r in obj.References:
                    if not r[1]:
                        obj.ShapeRefs += [doc.getObject(r[0])]
                    else:
                        obj.ShapeRefs += [(doc.getObject(r[0]), r[1])]
                obj.removeProperty('References')
                obj.removeProperty('LinkedObjects')

