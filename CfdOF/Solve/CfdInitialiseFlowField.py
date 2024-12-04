# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2013-2015 - Juergen Riegel <FreeCAD@juergen-riegel.net> *
# *   Copyright (c) 2017 Alfred Bogaers (CSIR) <abogaers@csir.co.za>        *
# *   Copyright (c) 2017 Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>          *
# *   Copyright (c) 2017 Johan Heyns (CSIR) <jheyns@csir.co.za>             *
# *   Copyright (c) 2019-2023 Oliver Oxtoby <oliveroxtoby@gmail.com>        *
# *   Copyright (c) 2022 Jonathan Bergh <bergh.jonathan@gmail.com>          *
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
from CfdOF import CfdTools
from CfdOF.CfdTools import addObjectProperty
from CfdOF.Solve import TaskPanelCfdInitialiseInternalFlowField

QT_TRANSLATE_NOOP = FreeCAD.Qt.QT_TRANSLATE_NOOP


def makeCfdInitialFlowField(name="InitialiseFields"):
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", name)
    CfdInitialVariables(obj)
    if FreeCAD.GuiUp:
        ViewProviderCfdInitialiseInternalFlowField(obj.ViewObject)
    return obj


class CommandCfdInitialiseInternalFlowField:
    """ Field initialisation command """

    def GetResources(self):
        icon_path = os.path.join(CfdTools.getModulePath(), "Gui", "Icons", "initialise.svg")
        return {'Pixmap': icon_path,
                'MenuText': QT_TRANSLATE_NOOP("CfdOF_InitialiseInternal", "Initialise"),
                'Accel': "",
                'ToolTip': QT_TRANSLATE_NOOP(
                    "CfdOF_InitialiseInternal",
                    "Initialise internal flow variables based on the selected physics model")}

    def IsActive(self):
        return CfdTools.getActiveAnalysis() is not None

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Initialise the internal flow variables")
        isPresent = False
        members = CfdTools.getActiveAnalysis().Group
        for i in members:
            if "InitialiseFields" in i.Name:
                FreeCADGui.activeDocument().setEdit(i.Name)
                isPresent = True

        # Allow to re-create if deleted
        if not isPresent:
            FreeCADGui.doCommand("from CfdOF import CfdTools")
            FreeCADGui.doCommand("from CfdOF.Solve import CfdInitialiseFlowField")
            FreeCADGui.doCommand(
                "CfdTools.getActiveAnalysis().addObject(CfdInitialiseFlowField.makeCfdInitialFlowField())")
            FreeCADGui.ActiveDocument.setEdit(FreeCAD.ActiveDocument.ActiveObject.Name)


class CfdInitialVariables:
    """ The field initialisation object """
    def __init__(self, obj):
        obj.Proxy = self
        self.Type = "InitialVariables"
        self.initProperties(obj)

    def initProperties(self, obj):
        addObjectProperty(
            obj,
            "PotentialFlow",
            True,
            "App::PropertyBool",
            "Flow",
            QT_TRANSLATE_NOOP("App::Property", "Initialise velocity with potential flow solution"),
        )
        addObjectProperty(
            obj,
            "PotentialFlowP",
            False,
            "App::PropertyBool",
            "Flow",
            QT_TRANSLATE_NOOP("App::Property", "Initialise pressure with potential flow solution"),
        )
        addObjectProperty(
            obj,
            "UseInletUValues",
            False,
            "App::PropertyBool",
            "Flow",
            QT_TRANSLATE_NOOP("App::Property", "Initialise with flow values from inlet"),
        )
        addObjectProperty(
            obj,
            "UseOutletPValue",
            True,
            "App::PropertyBool",
            "Flow",
            QT_TRANSLATE_NOOP("App::Property", "Initialise with flow values from outlet"),
        )
        addObjectProperty(
            obj,
            "Ux",
            "0 m/s",
            "App::PropertySpeed",
            "Flow",
            QT_TRANSLATE_NOOP("App::Property", "Velocity (x component)"),
        )
        addObjectProperty(
            obj,
            "Uy",
            "0 m/s",
            "App::PropertySpeed",
            "Flow",
            QT_TRANSLATE_NOOP("App::Property", "Velocity (y component)"),
        )
        addObjectProperty(
            obj,
            "Uz",
            "0 m/s",
            "App::PropertySpeed",
            "Flow",
            QT_TRANSLATE_NOOP("App::Property", "Velocity (z component)"),
        )
        addObjectProperty(
            obj,
            "Pressure",
            "100 kPa",
            "App::PropertyPressure",
            "Flow",
            QT_TRANSLATE_NOOP("App::Property", "Static pressure"),
        )
        addObjectProperty(
            obj,
            "UseInletTemperatureValue",
            False,
            "App::PropertyBool",
            "Thermal",
            QT_TRANSLATE_NOOP("App::Property", "Initialise with temperature value from inlet"),
        )
        addObjectProperty(
            obj,
            "Temperature",
            "293 K",
            "App::PropertyQuantity",
            "Thermal",
            QT_TRANSLATE_NOOP("App::Property", "Temperature"),
        )
        addObjectProperty(
            obj,
            "UseInletTurbulenceValues",
            False,
            "App::PropertyBool",
            "Turbulence",
            QT_TRANSLATE_NOOP("App::Property", "Initialise turbulence with values from inlet"),
        )
        addObjectProperty(
            obj,
            "k",
            "0.01 m^2/s^2",
            "App::PropertyQuantity",
            "Turbulence",
            QT_TRANSLATE_NOOP("App::Property", "Turbulent kinetic energy"),
        )
        addObjectProperty(
            obj,
            "omega",
            "1 1/s",
            "App::PropertyQuantity",
            "Turbulance",
            QT_TRANSLATE_NOOP("App::Property", "Specific turbulent dissipation rate"),
        )
        addObjectProperty(
            obj,
            "epsilon",
            "50 m^2/s^3",
            "App::PropertyQuantity",
            "Turbulence",
            QT_TRANSLATE_NOOP("App::Property", "Turbulent dissipation rate"),
        )
        addObjectProperty(
            obj,
            "nuTilda",
            "55 m^2/s^1",
            "App::PropertyQuantity",
            "Turbulence",
            QT_TRANSLATE_NOOP("App::Property", "Modified turbulent viscosity"),
        )
        addObjectProperty(
            obj,
            "gammaInt",
            "1",
            "App::PropertyQuantity",
            "Turbulence",
            QT_TRANSLATE_NOOP("App::Property", "Turbulent intermittency"),
        )
        addObjectProperty(
            obj,
            "ReThetat",
            "1",
            "App::PropertyQuantity",
            "Turbulence",
            QT_TRANSLATE_NOOP("App::Property", "Transition Momentum Thickness Reynolds Number"),
        )
        addObjectProperty(
            obj,
            "nut",
            "50 m^2/s^1",
            "App::PropertyQuantity",
            "Turbulence",
            QT_TRANSLATE_NOOP("App::Property", "Turbulent viscosity"),
        )

        addObjectProperty(
            obj,
            "VolumeFractions",
            {},
            "App::PropertyMap",
            "Volume Fraction",
            QT_TRANSLATE_NOOP("App::Property", "Volume fraction values"),
        )
        addObjectProperty(
            obj,
            "BoundaryU",
            None,
            "App::PropertyLinkGlobal",
            "",
            QT_TRANSLATE_NOOP("App::Property", "U boundary"),
        )
        addObjectProperty(
            obj,
            "BoundaryP",
            None,
            "App::PropertyLinkGlobal",
            "",
            QT_TRANSLATE_NOOP("App::Property", "P boundary"),
        )
        addObjectProperty(
            obj,
            "BoundaryT",
            None,
            "App::PropertyLinkGlobal",
            "",
            QT_TRANSLATE_NOOP("App::Property", "T boundary"),
        )
        addObjectProperty(
            obj,
            "BoundaryTurb",
            None,
            "App::PropertyLinkGlobal",
            "",
            QT_TRANSLATE_NOOP("App::Property", "Turbulence boundary"),
        )

    def onDocumentRestored(self, obj):
        self.initProperties(obj)


class _CfdInitialVariables:
    """ Backward compatibility for old class name when loading from file """
    def onDocumentRestored(self, obj):
        CfdInitialVariables(obj)


class ViewProviderCfdInitialiseInternalFlowField:

    def __init__(self, vobj):
        vobj.Proxy = self
        self.taskd = None

    def getIcon(self):
        icon_path = os.path.join(CfdTools.getModulePath(), "Gui", "Icons", "initialise.svg")
        return icon_path

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object

    def updateData(self, obj, prop):
        analysis_obj = CfdTools.getParentAnalysisObject(obj)
        # Ignore Shape updates as these relate to linked patches
        if prop != 'Shape':
            if analysis_obj and not analysis_obj.Proxy.loading:
                analysis_obj.NeedsCaseRewrite = True

    def onChanged(self, vobj, prop):
        return

    def setEdit(self, vobj, mode):
        analysis_object = CfdTools.getParentAnalysisObject(self.Object)
        if analysis_object is None:
            CfdTools.cfdErrorBox("No parent analysis object found")
            return False
        physics_model = CfdTools.getPhysicsModel(analysis_object)
        if not physics_model:
            CfdTools.cfdErrorBox("Analysis object must have a physics object")
            return False
        boundaries = CfdTools.getCfdBoundaryGroup(analysis_object)
        material_objs = CfdTools.getMaterials(analysis_object)

        import importlib
        importlib.reload(TaskPanelCfdInitialiseInternalFlowField)
        self.taskd = TaskPanelCfdInitialiseInternalFlowField.TaskPanelCfdInitialiseInternalFlowField(
            self.Object, physics_model, boundaries, material_objs)
        self.taskd.obj = vobj.Object
        FreeCADGui.Control.showDialog(self.taskd)
        return True

    def doubleClicked(self, vobj):
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


class _ViewProviderCfdInitialseInternalFlowField:
    """ Backward compatibility for old class name when loading from file """
    def attach(self, vobj):
        new_proxy = ViewProviderCfdInitialiseInternalFlowField(vobj)
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
