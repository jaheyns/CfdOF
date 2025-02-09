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

import os

import FreeCAD
import FreeCADGui
from pivy import coin

from CfdOF import CfdTools
from CfdOF.CfdTools import addObjectProperty
from CfdOF.Mesh import (
    TaskPanelCfdDynamicMeshInterfaceRefinement,
    TaskPanelCfdDynamicMeshShockRefinement,
)
from CfdOF.Mesh.CfdMesh import CfdMesh

QT_TRANSLATE_NOOP = FreeCAD.Qt.QT_TRANSLATE_NOOP


class CommandGroupDynamicMeshRefinement:
    def GetCommands(self):
        return ('CfdOF_DynamicMeshInterfaceRefinement','CfdOF_DynamicMeshShockRefinement',)

    def GetResources(self):
        icon_path = os.path.join(CfdTools.getModulePath(), "Gui", "Icons", "mesh_dynamic.svg")
        return {#'Pixmap': icon_path,
                'MenuText': QT_TRANSLATE_NOOP("CfdOF_GroupDynamicMeshRefinement", "Dynamic mesh refinement"),
                'Accel': "M, D",
                'ToolTip': QT_TRANSLATE_NOOP("CfdOF_GroupDynamicMeshRefinement", "Allows adaptive refinement of the mesh")}

    def IsActive(self):
        sel = FreeCADGui.Selection.getSelection()
        mesh_selected = (sel and len(sel) == 1 and hasattr(sel[0], "Proxy") and isinstance(sel[0].Proxy, CfdMesh))
        return mesh_selected


def makeCfdDynamicMeshInterfaceRefinement(base_mesh, name="DynamicMeshInterfaceRefinement"):
    """
    makeCfdDynamicMeshInterfaceRefinement([name]):
    Creates an object to define dynamic mesh properties if the solver supports it
    """
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", name)
    CfdDynamicMeshInterfaceRefinement(obj)
    if FreeCAD.GuiUp:
        ViewProviderCfdDynamicMeshInterfaceRefinement(obj.ViewObject)
    base_mesh.addObject(obj)
    return obj


def makeCfdDynamicMeshShockRefinement(base_mesh, name="DynamicMeshShockRefinement"):
    """
    makeCfdDynamicMeshShockRefinement([name]):
    Creates an object to define dynamic mesh properties if the solver supports it
    """
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", name)
    CfdDynamicMeshShockRefinement(obj)
    if FreeCAD.GuiUp:
        ViewProviderCfdDynamicMeshShockRefinement(obj.ViewObject)
    base_mesh.addObject(obj)
    return obj


class CommandDynamicMeshInterfaceRefinement:

    def __init__(self):
        pass

    def GetResources(self):
        icon_path = os.path.join(CfdTools.getModulePath(), "Gui", "Icons", "mesh_dynamic.svg")
        return {'Pixmap': icon_path,
                'MenuText': QT_TRANSLATE_NOOP("CfdOF_DynamicMeshInterfaceRefinement", "Interface dynamic refinement"),
                'Accel': "M, D",
                'ToolTip': QT_TRANSLATE_NOOP("CfdOF_DynamicMeshInterfaceRefinement",
                "Activates adaptive mesh refinement at free-surface interfaces")}

    def IsActive(self):
        sel = FreeCADGui.Selection.getSelection()
        mesh_selected = (sel and len(sel) == 1 and hasattr(sel[0], "Proxy") and isinstance(sel[0].Proxy, CfdMesh))

        free_surf = False
        if mesh_selected:
            analysis = CfdTools.getParentAnalysisObject(sel[0])
            physics = None
            if analysis:
                physics = CfdTools.getPhysicsModel(analysis)
                if physics:
                    free_surf = (physics.Phase == 'FreeSurface')

        return mesh_selected and free_surf

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
                        "CfdDynamicMeshRefinement.makeCfdDynamicMeshInterfaceRefinement(App.ActiveDocument.{})".format(sobj.Name))
                    FreeCADGui.ActiveDocument.setEdit(FreeCAD.ActiveDocument.ActiveObject.Name)

        FreeCADGui.Selection.clearSelection()


class CommandDynamicMeshShockRefinement:

    def __init__(self):
        pass

    def GetResources(self):
        icon_path = os.path.join(CfdTools.getModulePath(), "Gui", "Icons", "mesh_dynamic.svg")
        return {'Pixmap': icon_path,
                'MenuText': QT_TRANSLATE_NOOP("CfdOF_DynamicMeshShockRefinement", "Shockwave dynamic refinement"),
                'Accel': "M, S",
                'ToolTip': QT_TRANSLATE_NOOP("CfdOF_DynamicMeshShockRefinement",
                "Activates adaptive mesh refinement for shocks")}

    def IsActive(self):
        sel = FreeCADGui.Selection.getSelection()
        mesh_selected = (sel and len(sel) == 1 and hasattr(sel[0], "Proxy") and isinstance(sel[0].Proxy, CfdMesh))

        high_mach = False
        if mesh_selected:
            analysis = CfdTools.getParentAnalysisObject(sel[0])
            physics = None
            if analysis:
                physics = CfdTools.getPhysicsModel(analysis)
                if physics:
                    high_mach = (physics.Flow == 'HighMachCompressible')
        
        return mesh_selected and high_mach

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
                        "CfdDynamicMeshRefinement.makeCfdDynamicMeshShockRefinement(App.ActiveDocument.{})".format(sobj.Name))
                    FreeCADGui.ActiveDocument.setEdit(FreeCAD.ActiveDocument.ActiveObject.Name)

        FreeCADGui.Selection.clearSelection()


class CfdDynamicMeshInterfaceRefinement:

    def __init__(self, obj):
        obj.Proxy = self
        self.Type = "DynamicMeshInterfaceRefinement"
        self.initProperties(obj)

    def initProperties(self, obj):
        addObjectProperty(
            obj,
            "Phase",
            "",
            "App::PropertyString",
            "DynamicMesh",
            QT_TRANSLATE_NOOP("App::Property", "Set the target refinement interface phase"),
        )

        addObjectProperty(
            obj,
            "RefinementInterval",
            1,
            "App::PropertyInteger",
            "DynamicMesh",
            QT_TRANSLATE_NOOP(
                "App::Property",
                "Set the interval at which to run the dynamic mesh refinement",
            ),
        )

        addObjectProperty(
            obj,
            "MaxRefinementLevel",
            1,
            "App::PropertyInteger",
            "DynamicMesh",
            QT_TRANSLATE_NOOP("App::Property", "Set the maximum dynamic mesh refinement level"),
        )

        addObjectProperty(
            obj,
            "BufferLayers",
            1,
            "App::PropertyInteger",
            "DynamicMesh",
            QT_TRANSLATE_NOOP(
                "App::Property",
                "Set the number of buffer layers between refined and existing cells",
            ),
        )

        addObjectProperty(
            obj,
            "WriteFields",
            False,
            "App::PropertyBool",
            "DynamicMesh",
            QT_TRANSLATE_NOOP(
                "App::Property",
                "Whether to write the dynamic mesh refinement fields after refinement",
            ),
        )

    def onDocumentRestored(self, obj):
        self.initProperties(obj)


class CfdDynamicMeshRefinement:
    """ Backward compatibility for old class name when loading from file """
    def onDocumentRestored(self, obj):
        CfdDynamicMeshInterfaceRefinement(obj)


class _CfdDynamicMeshRefinement:
    """ Backward compatibility for old class name when loading from file """
    def onDocumentRestored(self, obj):
        CfdDynamicMeshInterfaceRefinement(obj)


class CfdDynamicMeshShockRefinement:

    def __init__(self, obj):
        obj.Proxy = self
        self.Type = "DynamicMeshShockRefinement"
        self.initProperties(obj)

    def initProperties(self, obj):
        addObjectProperty(
            obj,
            "ReferenceVelocityDirection",
            FreeCAD.Vector(1, 0, 0),
            "App::PropertyVector",
            "DynamicMesh",
            QT_TRANSLATE_NOOP(
                "App::Property",
                "Reference velocity direction (typically free-stream/input value)",
            ),
        )

        addObjectProperty(
            obj,
            "RelativeElementSize",
            1,
            "App::PropertyFloat",
            "DynamicMesh",
            QT_TRANSLATE_NOOP("App::Property", "Refinement relative to the base mesh"),
        )

        addObjectProperty(
            obj,
            "RefinementIntervalSteady",
            50,
            "App::PropertyInteger",
            "DynamicMesh",
            QT_TRANSLATE_NOOP(
                "App::Property",
                "Interval at which to run the dynamic mesh refinement in steady analyses",
            ),
        )

        addObjectProperty(
            obj,
            "RefinementIntervalTransient",
            5,
            "App::PropertyInteger",
            "DynamicMesh",
            QT_TRANSLATE_NOOP(
                "App::Property",
                "Interval at which to run the dynamic mesh refinement in transient analyses",
            ),
        )

        addObjectProperty(
            obj,
            "BufferLayers",
            1,
            "App::PropertyInteger",
            "DynamicMesh",
            QT_TRANSLATE_NOOP(
                "App::Property",
                "Number of buffer layers between refined and existing cells",
            ),
        )

        addObjectProperty(
            obj,
            "WriteFields",
            False,
            "App::PropertyBool",
            "DynamicMesh",
            QT_TRANSLATE_NOOP(
                "App::Property",
                "Whether to write the indicator fields for shock wave detection",
            ),
        )

    def onDocumentRestored(self, obj):
        self.initProperties(obj)


class ViewProviderCfdDynamicMeshInterfaceRefinement:
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
        analysis_obj = CfdTools.getParentAnalysisObject(obj)
        if analysis_obj and not analysis_obj.Proxy.loading:
            analysis_obj.NeedsCaseRewrite = True

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
        importlib.reload(TaskPanelCfdDynamicMeshInterfaceRefinement)
        taskd = TaskPanelCfdDynamicMeshInterfaceRefinement.TaskPanelCfdDynamicMeshInterfaceRefinement(
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

    # dumps and loads replace __getstate__ and __setstate__ post v. 0.21.2
    def dumps(self):
        return None

    def loads(self, state):
        return None


class ViewProviderCfdDynamicMeshRefinement:
    """ Backward compatibility for old class name when loading from file """
    def attach(self, vobj):
        new_proxy = ViewProviderCfdDynamicMeshInterfaceRefinement(vobj)
        new_proxy.attach(vobj)

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None

    # dumps and loads replace __getstate__ and __setstate__ post v. 0.21.2
    def dumps(self):
        return None

    def loads(self, state):
        return None


class _ViewProviderCfdDynamicMeshRefinement:
    """ Backward compatibility for old class name when loading from file """
    def attach(self, vobj):
        new_proxy = ViewProviderCfdDynamicMeshInterfaceRefinement(vobj)
        new_proxy.attach(vobj)

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None

    # dumps and loads replace __getstate__ and __setstate__ post v. 0.21.2
    def dumps(self):
        return None

    def loads(self, state):
        return None


class ViewProviderCfdDynamicMeshShockRefinement:
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
        analysis_obj = CfdTools.getParentAnalysisObject(obj)
        if analysis_obj and not analysis_obj.Proxy.loading:
            analysis_obj.NeedsCaseRewrite = True

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
        importlib.reload(TaskPanelCfdDynamicMeshShockRefinement)
        taskd = TaskPanelCfdDynamicMeshShockRefinement.TaskPanelCfdDynamicMeshShockRefinement(
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

    # dumps and loads replace __getstate__ and __setstate__ post v. 0.21.2
    def dumps(self):
        return None

    def loads(self, state):
        return None
