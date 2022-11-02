# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2022 Jonathan Bergh <bergh.jonathan@gmail.com>          *
# *   Copyright (c) 2022 Oliver Oxtoby <oliveroxtoby@gmail.com>             *
# *                                                                         *
# *   This program is free software: you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License as        *
# *   published by the Free Software Foundation, either version 3 of the    *
# *   License, or (at your option) any later version.                       *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Lesser General Public License for more details.                   *
# *                                                                         *
# *   You should have received a copy of the GNU Lesser General Public      *
# *   License along with this program.  If not,                             *
# *   see <https://www.gnu.org/licenses/>.                                  *
# *                                                                         *
# ***************************************************************************

import FreeCAD
import FreeCADGui
from CfdOF.Mesh.CfdMesh import CfdMesh
from PySide import QtCore
import os
from CfdOF import CfdTools
from CfdOF.CfdTools import addObjectProperty
from pivy import coin
from CfdOF.Mesh import TaskPanelCfdDynamicMeshRefinement


class CommandGroupDynamicMeshRefinement:
    def GetCommands(self):
        return ('Cfd_DynamicMeshRefinement',)

    def GetResources(self):
        icon_path = os.path.join(CfdTools.getModulePath(), "Gui", "Icons", "mesh_dynamic.svg")
        return {'Pixmap': icon_path,
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Cfd_DynamicMesh", "Dynamic mesh refinement"),
                'Accel': "M, D",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Cfd_DynamicMesh", "Allows adaptive refinement of the mesh")}

    def IsActive(self):
        sel = FreeCADGui.Selection.getSelection()
        mesh_selected = (sel and len(sel) == 1 and hasattr(sel[0], "Proxy") and isinstance(sel[0].Proxy, CfdMesh))

        transient = False
        if mesh_selected:
            analysis = CfdTools.getParentAnalysisObject(sel[0])
            physics = None
            if analysis:
                physics = CfdTools.getPhysicsModel(analysis)
                if physics:
                    transient = (physics.Time == 'Transient')
        
        return mesh_selected and transient


def makeCfdDynamicMeshRefinement(base_mesh, name="DynamicMeshInterfaceRefinement"):
    """
    makeCfdDynamicMeshRefinement([name]):
    Creates an object to define dynamic mesh properties if the solver supports it
    """
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", name)
    CfdDynamicMeshRefinement(obj)
    if FreeCAD.GuiUp:
        ViewProviderCfdDynamicMeshRefinement(obj.ViewObject)
    base_mesh.addObject(obj)
    return obj


class CommandDynamicMeshRefinement:

    def __init__(self):
        pass

    def GetResources(self):
        icon_path = os.path.join(CfdTools.getModulePath(), "Gui", "Icons", "mesh_dynamic.svg")
        return {'Pixmap': icon_path,
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Cfd_DynamicMesh", "Interface dynamic refinement"),
                'Accel': "M, D",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Cfd_DynamicMesh", 
                "Activates adaptive mesh refinement at free-surface interfaces")}

    def IsActive(self):
        sel = FreeCADGui.Selection.getSelection()
        mesh_selected = (sel and len(sel) == 1 and hasattr(sel[0], "Proxy") and isinstance(sel[0].Proxy, CfdMesh))

        transient = False
        if mesh_selected:
            analysis = CfdTools.getParentAnalysisObject(sel[0])
            physics = None
            if analysis:
                physics = CfdTools.getPhysicsModel(analysis)
                if physics:
                    transient = (physics.Time == 'Transient')
        
        return mesh_selected and transient

    def Activated(self):
        is_present = False
        members = CfdTools.getMesh(CfdTools.getActiveAnalysis()).Group
        for i in members:
            if hasattr(i, 'Proxy') and isinstance(i.Proxy, CfdDynamicMeshRefinement):
                FreeCADGui.activeDocument().setEdit(i.Name)
                is_present = True

        # Allow to re-create if deleted
        if not is_present:
            sel = FreeCADGui.Selection.getSelection()
            if len(sel) == 1:
                sobj = sel[0]
                if len(sel) == 1 and hasattr(sobj, "Proxy") and isinstance(sobj.Proxy, CfdMesh):
                    FreeCAD.ActiveDocument.openTransaction("Create DynamicMesh")
                    FreeCADGui.doCommand("")
                    FreeCADGui.doCommand("from CfdOF.Mesh import CfdDynamicMeshRefinement")
                    FreeCADGui.doCommand("from CfdOF import CfdTools")
                    FreeCADGui.doCommand(
                        "CfdDynamicMeshRefinement.makeCfdDynamicMeshRefinement(App.ActiveDocument.{})".format(sobj.Name))
                    FreeCADGui.ActiveDocument.setEdit(FreeCAD.ActiveDocument.ActiveObject.Name)

        FreeCADGui.Selection.clearSelection()


class CfdDynamicMeshRefinement:

    def __init__(self, obj):
        obj.Proxy = self
        self.Type = "DynamicMeshInterfaceRefinement"
        self.initProperties(obj)

    def initProperties(self, obj):
        addObjectProperty(obj, "Phase", "", "App::PropertyString", "DynamicMesh",
                          "Set the target refinement interface phase")

        addObjectProperty(obj, "RefinementInterval", 1, "App::PropertyInteger", "DynamicMesh",
                          "Set the interval at which to run the dynamic mesh refinement")

        addObjectProperty(obj, "MaxRefinementLevel", 1, "App::PropertyInteger", "DynamicMesh",
                          "Set the maximum dynamic mesh refinement level")

        addObjectProperty(obj, "BufferLayers", 1, "App::PropertyInteger", "DynamicMesh",
                          "Set the number of buffer layers between refined and existing cells")

        addObjectProperty(obj, "WriteFields", False, "App::PropertyBool", "DynamicMesh",
                          "Whether to write the dynamic mesh refinement fields after refinement")

    def onDocumentRestored(self, obj):
        self.initProperties(obj)


class _CfdDynamicMeshRefinement:
    """ Backward compatibility for old class name when loading from file """
    def onDocumentRestored(self, obj):
        CfdDynamicMeshRefinement(obj)


class ViewProviderCfdDynamicMeshRefinement:
    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        icon_path = os.path.join(CfdTools.getModulePath(), "Gui", "Icons", "mesh_dynamic.svg")
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
        analysis_object = CfdTools.getParentAnalysisObject(self.Object)
        if analysis_object is None:
            CfdTools.cfdErrorBox("No parent analysis object found")
            return False
        physics_model = CfdTools.getPhysicsModel(analysis_object)
        if not physics_model:
            CfdTools.cfdErrorBox("Analysis object must have a physics object")
            return False
        material_models = CfdTools.getMaterials(analysis_object)

        import importlib
        importlib.reload(TaskPanelCfdDynamicMeshRefinement)
        taskd = TaskPanelCfdDynamicMeshRefinement.TaskPanelCfdDynamicMeshRefinement(
            self.Object, physics_model, material_models)
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
            FreeCADGui.Control.showTaskView()
        return True

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None


class _ViewProviderCfdDynamicMeshRefinement:
    """ Backward compatibility for old class name when loading from file """
    def attach(self, vobj):
        new_proxy = ViewProviderCfdDynamicMeshRefinement(vobj)
        new_proxy.attach(vobj)

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None
