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
from core.mesh.dynamic import _TaskPanelCfdDynamicMeshRefinement


def makeCfdDynamicMeshRefinement(base_mesh, name="DynamicMeshAdaptationModel"):
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
        # FreeCAD.ActiveDocument.openTransaction("Set up a dynamic mesh refinement")
        is_present = False
        members = CfdTools.getActiveAnalysis().Group
        for i in members:
            if isinstance(i.Proxy, _CfdDynamicMeshRefinement):
                FreeCADGui.activeDocument().setEdit(i.Name)
                is_present = True

        # Allow to re-create if deleted
        if not is_present:
            sel = FreeCADGui.Selection.getSelection()
            if len(sel) == 1:
                sobj = sel[0]
                if len(sel) == 1 and hasattr(sobj, "Proxy") and isinstance(sobj.Proxy, _CfdMesh):
                    FreeCAD.ActiveDocument.openTransaction("Create DynamicMesh")
                    FreeCADGui.doCommand("")
                    FreeCADGui.addModule("core.mesh.dynamic.CfdDynamicMeshRefinement as CfdDynamicMeshRefinement")
                    FreeCADGui.addModule("CfdTools")
                    FreeCADGui.doCommand(
                        "CfdTools.getActiveAnalysis().addObject(CfdDynamicMeshRefinement.makeCfdDynamicMeshRefinement(App.ActiveDocument.{}))".format(sobj.Name))
                    FreeCADGui.ActiveDocument.setEdit(FreeCAD.ActiveDocument.ActiveObject.Name)

            FreeCADGui.Selection.clearSelection()


class _CfdDynamicMeshRefinement:

    def __init__(self, obj):
        obj.Proxy = self
        self.Type = "DynamicMeshAdaptationModel"
        self.initProperties(obj)

    def initProperties(self, obj):
        addObjectProperty(obj, "RefinementInterval", 1, "App::PropertyInteger", "DynamicMeshRefinement",
                          "Set the interval at which to run the dynamic mesh refinement")

        addObjectProperty(obj, "MaxRefinementLevel", 1, "App::PropertyInteger", "DynamicMeshRefinement",
                          "Set the maximum dynamic mesh refinement level")

        addObjectProperty(obj, "BufferLayers", 1, "App::PropertyInteger", "DynamicMeshRefinement",
                          "Set the number of buffer layers between refined and existing cells")

        addObjectProperty(obj, "MaxRefinementCells", 20000, "App::PropertyInteger", "DynamicMeshRefinement",
                          "Set the maximum number of cells added during dynamic mesh refinement")

        addObjectProperty(obj, "RefinementField", "", "App::PropertyString", "DynamicMeshRefinement",
                          "Set the target refinement field")

        addObjectProperty(obj, "LowerRefinementLevel", 0.001, "App::PropertyFloat", "DynamicMeshRefinement",
                          "Set the lower mesh refinement")

        addObjectProperty(obj, "UpperRefinementLevel", 0.999, "App::PropertyFloat", "DynamicMeshRefinement",
                          "Set the upper mesh refinement")

        addObjectProperty(obj, "UnRefinementLevel", 10, "App::PropertyInteger", "DynamicMeshRefinement",
                          "Set the unrefinement level below which the mesh will be unrefined")

        addObjectProperty(obj, "WriteFields", False, "App::PropertyBool", "DynamicMeshRefinement",
                          "Whether to write the dynamic mesh refinement fields after refinement")

    def onDocumentRestored(self, obj):
        self.initProperties(obj)




class _ViewProviderCfdDynamicMeshRefinement:
    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        icon_path = os.path.join(CfdTools.get_module_path(), "Gui", "Resources", "icons", "meshdynamic.png")
        return icon_path

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object
        self.standard = coin.SoGroup()
        vobj.addDisplayMode(self.standard, "Standard")

    def getDisplayModes(self, obj):
        modes = []
        return modes

    def getDefaultDisplayMode(self):
        return "Shaded"

    def setDisplayMode(self, mode):
        return mode

    def updateData(self, obj, prop):
        return

    def onChanged(self, vobj, prop):
        return

    def setEdit(self, vobj, mode=0):
        import importlib
        importlib.reload(_TaskPanelCfdDynamicMeshRefinement)
        taskd = _TaskPanelCfdDynamicMeshRefinement._TaskPanelCfdDynamicMeshRefinement(self.Object)
        taskd.obj = vobj.Object
        FreeCADGui.Control.showDialog(taskd)
        return True

    def unsetEdit(self, vobj, mode=0):
        FreeCADGui.Control.closeDialog()
        return

    def doubleClicked(self, vobj):
        doc = FreeCADGui.getDocument(vobj.Object.Document)
        if not doc.getInEdit():
            doc.setEdit(vobj.Object.Name)
        else:
            FreeCAD.Console.PrintError('Task dialog already open\n')
        return True

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None
