# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2024 Jonathan Bergh <bergh.jonathan@gmail.com>          *
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
import os.path
import FreeCAD
if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore
from CfdOF import CfdTools
from CfdOF.CfdTools import addObjectProperty


def makeCfdPhasePhysicsSelection(name="PhasePhysicsModel"):
    # DocumentObjectGroupPython, FeaturePython, GeometryPython
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", name)
    CfdPhasePhysicsModel(obj)
    if FreeCAD.GuiUp:
        ViewProviderCfdPhasePhysicsSelection(obj.ViewObject)
    return obj


class CommandCfdPhasePhysicsSelection:
    """ CFD physics selection command definition """

    def GetResources(self):
        icon_path = os.path.join(CfdTools.getModulePath(), "Gui", "Icons", "phasephysics.svg")
        return {'Pixmap': icon_path,
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Cfd_PhasePhysicsModel", "Select Eulerian phase models"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Cfd_PhysicsModel", "Select the Eulerian multiphase physics models")}

    def IsActive(self):
        return CfdTools.getActiveAnalysis() is not None

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Choose appropriate phase physics model")
        is_present = False
        members = CfdTools.getActiveAnalysis().Group
        for i in members:
            if isinstance(i.Proxy, CfdPhasePhysicsModel):
                FreeCADGui.activeDocument().setEdit(i.Name)
                is_present = True

        # Allow to re-create if deleted
        if not is_present:
            FreeCADGui.doCommand("")
            FreeCADGui.doCommand("from CfdOF.Solve import CfdPhasePhysicsSelection")
            FreeCADGui.doCommand("from CfdOF import CfdTools")
            FreeCADGui.doCommand(
                "CfdTools.getActiveAnalysis().addObject(CfdPhasePhysicsSelection.makeCfdPhasePhysicsSelection())")
            FreeCADGui.ActiveDocument.setEdit(FreeCAD.ActiveDocument.ActiveObject.Name)


class CfdPhasePhysicsModel:
    """ The Eulerian multiphase specific physics models """
    def __init__(self, obj):
        obj.Proxy = self
        self.Type = "PhasePhysicsModel"
        self.initProperties(obj)

    def initProperties(self, obj):

        if addObjectProperty(obj, "Drag", ['SchillerNeuman'], "App::PropertyEnumeration", "Phase Physics modelling",
                             "Drag force model"):
            obj.Drag = 'SchillerNeuman'

        if addObjectProperty(obj, "Lift", [''],
                             "App::PropertyEnumeration", "Phase Physics modelling", "Lift force model"):
            obj.Lift = ''

        if addObjectProperty(obj, "SurfaceTension", ['Constant'], "App::PropertyEnumeration", "Phase Physics modelling",
                             "Surface tension force model"):
            obj.SurfaceTension = 'Constant'

        if addObjectProperty(obj, "VirtualMass", ['ConstantCoefficient'],
                             "App::PropertyEnumeration", "Phase Physics modelling", "Virtual mass force model"):
            obj.VirtualMass = 'ConstantCoefficient'

        if addObjectProperty(obj, "HeatTransfer", ['RanzMarshall'],
                             "App::PropertyEnumeration", "Phase Physics modelling", "Interphase heat transfer model"):
            obj.HeatTransfer = 'RanzMarshall'

        if addObjectProperty(obj, "PhaseTransfer", [''],
                             "App::PropertyEnumeration", "Phase Physics modelling", "Interphase mass transfer model"):
            obj.PhaseTransfer = ''

        if addObjectProperty(obj, "WallLubrication", [''],
                             "App::PropertyEnumeration", "Phase Physics modelling", "Wall lubrication model"):
            obj.WallLubrication = ''

        if addObjectProperty(obj, "TurbulentDispersion", [''],
                             "App::PropertyEnumeration", "Phase Physics modelling", "Turbulent dispersion model"):
            obj.TurbulentDispersion = ''

        if addObjectProperty(obj, "InterfaceCompression", [''],
                             "App::PropertyEnumeration", "Phase Physics modelling", "Interface compression model"):
            obj.InterfaceCompression = ''

        # SRF model
        addObjectProperty(obj, 'SRFModelEnabled', False, "App::PropertyBool", "Reference frame",
                          "Single Rotating Frame model enabled")

        addObjectProperty(obj, 'SRFModelRPM', '0', "App::PropertyQuantity", "Reference frame", "Rotational speed")

        addObjectProperty(obj, 'SRFModelCoR', FreeCAD.Vector(0, 0, 0), "App::PropertyPosition", "Reference frame",
                          "Centre of rotation (SRF)")

        addObjectProperty(obj, 'SRFModelAxis', FreeCAD.Vector(0, 0, 0), "App::PropertyPosition", "Reference frame",
                          "Axis of rotation (SRF)")

    def onDocumentRestored(self, obj):
        self.initProperties(obj)


class _CfdPhasePhysicsModel:
    """ Backward compatibility for old class name when loading from file """
    def onDocumentRestored(self, obj):
        CfdPhasePhysicsModel(obj)

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None

    # dumps and loads replace __getstate__ and __setstate__ post v. 0.21.2
    def dumps(self):
        return None

    def loads(self, state):
        return None


class ViewProviderCfdPhasePhysicsSelection:
    def __init__(self, vobj):
        vobj.Proxy = self
        self.taskd = None

    def getIcon(self):
        icon_path = os.path.join(CfdTools.getModulePath(), "Gui", "Icons", "phasephysics.svg")
        return icon_path

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object
        self.bubbles = None

    def updateData(self, obj, prop):
        analysis_obj = CfdTools.getParentAnalysisObject(obj)
        if analysis_obj and not analysis_obj.Proxy.loading:
            analysis_obj.NeedsCaseRewrite = True

    def onChanged(self, vobj, prop):
        return

    def setEdit(self, vobj, mode):
        from CfdOF.Solve import TaskPanelCfdPhasePhysicsSelection
        import importlib
        importlib.reload(TaskPanelCfdPhasePhysicsSelection)
        self.taskd = TaskPanelCfdPhasePhysicsSelection.TaskPanelCfdPhasePhysicsSelection(self.Object)
        self.taskd.obj = vobj.Object
        FreeCADGui.Control.showDialog(self.taskd)
        return True

    def doubleClicked(self, vobj):
        # Make sure no other task dialog still active
        doc = FreeCADGui.getDocument(vobj.Object.Document)
        if not doc.getInEdit():
            doc.setEdit(vobj.Object.Name)
        else:
            FreeCAD.Console.PrintError('Task dialog already active\n')
            FreeCADGui.Control.showTaskView()
        return True

    def unsetEdit(self, vobj, mode):
        if self.taskd:
            self.taskd.closing()
            self.taskd = None
        FreeCADGui.Control.closeDialog()

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None

    # dumps and loads replace __getstate__ and __setstate__ post v. 0.21.2
    def dumps(self):
        return None

    def loads(self, state):
        return None


class _ViewProviderPhasePhysicsSelection:
    """ Backward compatibility for old class name when loading from file """
    def attach(self, vobj):
        new_proxy = ViewProviderCfdPhasePhysicsSelection(vobj)
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
