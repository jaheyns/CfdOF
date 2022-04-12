# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2013-2015 - Juergen Riegel <FreeCAD@juergen-riegel.net> *
# *   Copyright (c) 2017 Alfred Bogaers (CSIR) <abogaers@csir.co.za>        *
# *   Copyright (c) 2017 Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>          *
# *   Copyright (c) 2017 Johan Heyns (CSIR) <jheyns@csir.co.za>             *
# *   Copyright (c) 2019-2022 Oliver Oxtoby <oliveroxtoby@gmail.com>        *
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

import os
import os.path
import FreeCAD
if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore
import CfdTools
from CfdTools import addObjectProperty
import _TaskPanelCfdInitialiseInternalFlowField


def makeCfdInitialFlowField(name="InitialiseFields"):
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", name)
    _CfdInitialVariables(obj)
    if FreeCAD.GuiUp:
        _ViewProviderCfdInitialseInternalFlowField(obj.ViewObject)
    return obj


class _CommandCfdInitialiseInternalFlowField:
    """ Field initialisation command """

    def GetResources(self):
        icon_path = os.path.join(CfdTools.get_module_path(), "Gui", "Resources", "icons", "initialise.png")
        return {'Pixmap': icon_path,
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Cfd_InitialiseInternal", "Initialise"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP(
                    "Cfd_InitialiseInternal",
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
            FreeCADGui.doCommand("")
            FreeCADGui.addModule("CfdTools")
            FreeCADGui.addModule("CfdInitialiseFlowField")
            FreeCADGui.doCommand(
                "CfdTools.getActiveAnalysis().addObject(CfdInitialiseFlowField.makeCfdInitialFlowField())")
            FreeCADGui.ActiveDocument.setEdit(FreeCAD.ActiveDocument.ActiveObject.Name)


class _CfdInitialVariables:
    """ The field initialisation object """
    def __init__(self, obj):
        obj.Proxy = self
        self.Type = "InitialVariables"
        self.initProperties(obj)

    def initProperties(self, obj):
        addObjectProperty(obj, 'PotentialFlow', True, "App::PropertyBool", "Flow",
                          "Initialise velocity with potential flow solution")
        addObjectProperty(obj, 'PotentialFlowP', False, "App::PropertyBool", "Flow",
                          "Initialise pressure with potential flow solution")
        addObjectProperty(obj, 'UseInletUValues', False, "App::PropertyBool", "Flow",
                          "Initialise with flow values from inlet")
        addObjectProperty(obj, 'UseOutletPValue', True, "App::PropertyBool", "Flow",
                          "Initialise with flow values from outlet")
        addObjectProperty(obj, 'Ux', '0 m/s', "App::PropertySpeed", "Flow", "Velocity (x component)")
        addObjectProperty(obj, 'Uy', '0 m/s', "App::PropertySpeed", "Flow", "Velocity (y component)")
        addObjectProperty(obj, 'Uz', '0 m/s', "App::PropertySpeed", "Flow", "Velocity (z component)")
        addObjectProperty(obj, 'Pressure', '0 Pa', "App::PropertyPressure", "Flow", "Static pressure")
        addObjectProperty(obj, 'UseInletTemperatureValue', False, "App::PropertyBool", "Thermal",
                          "Initialise with temperature value from inlet")
        addObjectProperty(obj, 'Temperature', '293 K', "App::PropertyQuantity", "Thermal", "Temperature")
        addObjectProperty(obj, 'UseInletTurbulenceValues', False, "App::PropertyBool", "Turbulence",
                          "Initialise turbulence with values from inlet")
        addObjectProperty(obj, 'k', '0.01 m^2/s^2', "App::PropertyQuantity", "Turbulence", "Turbulent kinetic energy")
        addObjectProperty(obj, 'omega', '1 rad/s', "App::PropertyQuantity", "Turbulence",
                          "Specific turbulent dissipation rate")
        addObjectProperty(obj, 'epsilon', '50 m^2/s^3', "App::PropertyQuantity", "Turbulence",
                          "Turbulent dissipation rate")
        addObjectProperty(obj, 'nuTilda', '55 m^2/s^1', "App::PropertyQuantity", "Turbulence",
                          "Modified turbulent viscosity")
        addObjectProperty(obj, 'gammaInt', '1', "App::PropertyQuantity", "Turbulence",
                          "Turbulent intermittency")
        addObjectProperty(obj, 'ReThetat', '1', "App::PropertyQuantity", "Turbulence",
                          "Transition Momentum Thickness Reynolds Number")
        addObjectProperty(obj, 'nut', '50 m^2/s^1', "App::PropertyQuantity", "Turbulence",
                          "Turbulent viscosity")
        addObjectProperty(obj, 'kEqnk', '0.01 m^2/s^2', "App::PropertyQuantity", "Turbulence",
                          "Turbulent kinetic energy")
        addObjectProperty(obj, 'kEqnNut', '50 m^2/s^1', "App::PropertyQuantity", "Turbulence",
                          "Turbulent viscosity")

        addObjectProperty(obj, 'VolumeFractions', {}, "App::PropertyMap", "Volume Fraction", "Volume fraction values")
        addObjectProperty(obj, 'BoundaryU', None, "App::PropertyLink", "", "U boundary name")
        addObjectProperty(obj, 'BoundaryP', None, "App::PropertyLink", "", "P boundary name")
        addObjectProperty(obj, 'BoundaryT', None, "App::PropertyLink", "", "T boundary name")
        addObjectProperty(obj, 'BoundaryTurb', None, "App::PropertyLink", "", "Turbulence boundary name")

    def onDocumentRestored(self, obj):
        self.initProperties(obj)


class _ViewProviderCfdInitialseInternalFlowField:

    def __init__(self, vobj):
        vobj.Proxy = self
        self.taskd = None

    def getIcon(self):
        icon_path = os.path.join(CfdTools.get_module_path(), "Gui", "Resources", "icons", "initialise.png")
        return icon_path

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object

    def updateData(self, obj, prop):
        analysis_obj = CfdTools.getParentAnalysisObject(obj)
        if 'NeedsCaseRewrite' in analysis_obj.PropertiesList:
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
        importlib.reload(_TaskPanelCfdInitialiseInternalFlowField)
        self.taskd = _TaskPanelCfdInitialiseInternalFlowField._TaskPanelCfdInitialiseInternalFlowField(
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
            FreeCADGui.Control.showDialog(self.taskd)
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


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Cfd_InitialiseInternal', _CommandCfdInitialiseInternalFlowField())