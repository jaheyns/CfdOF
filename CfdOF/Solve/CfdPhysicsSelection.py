# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2017-2018 Alfred Bogaers (CSIR) <abogaers@csir.co.za>   *
# *   Copyright (c) 2017-2018 Johan Heyns (CSIR) <jheyns@csir.co.za>        *
# *   Copyright (c) 2017-2018 Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>     *
# *   Copyright (c) 2019-2022 Oliver Oxtoby <oliveroxtoby@gmail.com>        *
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
    from PySide import QtCore
from CfdOF import CfdTools
from CfdOF.CfdTools import addObjectProperty

from PySide.QtCore import QT_TRANSLATE_NOOP

def makeCfdPhysicsSelection(name="PhysicsModel"):
    # DocumentObjectGroupPython, FeaturePython, GeometryPython
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", name)
    CfdPhysicsModel(obj)
    if FreeCAD.GuiUp:
        ViewProviderCfdPhysicsSelection(obj.ViewObject)
    return obj


class CommandCfdPhysicsSelection:
    """ CFD physics selection command definition """

    def GetResources(self):
        icon_path = os.path.join(CfdTools.getModulePath(), "Gui", "Icons", "physics.svg")
        return {'Pixmap': icon_path,
                'MenuText': QT_TRANSLATE_NOOP("CfdOF_PhysicsModel", "Select models"),
                'Accel': "",
                'ToolTip': QT_TRANSLATE_NOOP("CfdOF_PhysicsModel", "Select the physics model")}

    def IsActive(self):
        return CfdTools.getActiveAnalysis() is not None

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Choose appropriate physics model")
        is_present = False
        members = CfdTools.getActiveAnalysis().Group
        for i in members:
            if isinstance(i.Proxy, CfdPhysicsModel):
                FreeCADGui.activeDocument().setEdit(i.Name)
                is_present = True

        # Allow to re-create if deleted
        if not is_present:
            FreeCADGui.doCommand("")
            FreeCADGui.doCommand("from CfdOF.Solve import CfdPhysicsSelection")
            FreeCADGui.doCommand("from CfdOF import CfdTools")
            FreeCADGui.doCommand(
                "CfdTools.getActiveAnalysis().addObject(CfdPhysicsSelection.makeCfdPhysicsSelection())")
            FreeCADGui.ActiveDocument.setEdit(FreeCAD.ActiveDocument.ActiveObject.Name)


class CfdPhysicsModel:
    """ The CFD Physics Model """
    def __init__(self, obj):
        obj.Proxy = self
        self.Type = "PhysicsModel"
        self.initProperties(obj)

    def initProperties(self, obj):
        # obj.supportedProperties()
        # ['App::PropertyBool', 'App::PropertyBoolList', 'App::PropertyFloat', 'App::PropertyFloatList',
        #  'App::PropertyFloatConstraint', 'App::PropertyPrecision', 'App::PropertyQuantity',
        #  'App::PropertyQuantityConstraint', 'App::PropertyAngle', 'App::PropertyDistance', 'App::PropertyLength',
        #  'App::PropertyArea', 'App::PropertyVolume', 'App::PropertySpeed', 'App::PropertyAcceleration',
        #  'App::PropertyForce', 'App::PropertyPressure', 'App::PropertyInteger', 'App::PropertyIntegerConstraint',
        #  'App::PropertyPercent', 'App::PropertyEnumeration', 'App::PropertyIntegerList', 'App::PropertyIntegerSet',
        #  'App::PropertyMap', 'App::PropertyString', 'App::PropertyUUID', 'App::PropertyFont',
        #  'App::PropertyStringList', 'App::PropertyLink', 'App::PropertyLinkChild', 'App::PropertyLinkGlobal',
        #  'App::PropertyLinkSub', 'App::PropertyLinkSubChild', 'App::PropertyLinkSubGlobal', 'App::PropertyLinkList',
        #  'App::PropertyLinkListChild', 'App::PropertyLinkListGlobal', 'App::PropertyLinkSubList',
        #  'App::PropertyLinkSubListChild', 'App::PropertyLinkSubListGlobal', 'App::PropertyMatrix',
        #  'App::PropertyVector', 'App::PropertyVectorDistance', 'App::PropertyPosition', 'App::PropertyDirection',
        #  'App::PropertyVectorList', 'App::PropertyPlacement', 'App::PropertyPlacementList',
        #  'App::PropertyPlacementLink', 'App::PropertyColor', 'App::PropertyColorList', 'App::PropertyMaterial',
        #  'App::PropertyMaterialList', 'App::PropertyPath', 'App::PropertyFile', 'App::PropertyFileIncluded',
        #  'App::PropertyPythonObject', 'App::PropertyExpressionEngine', 'Part::PropertyPartShape',
        #  'Part::PropertyGeometryList', 'Part::PropertyShapeHistory', 'Part::PropertyFilletEdges',
        #  'Fem::PropertyFemMesh', 'Fem::PropertyPostDataObject']

        if addObjectProperty(obj, "Time", ['Steady', 'Transient'], "App::PropertyEnumeration", "Physics modelling",
                             "Resolve time dependence"):
            obj.Time = 'Steady'

        # Backward compat - convert old, imprecise 'Incompressible' and 'Compressible' to Isothermal/NonIsothermal
        prev_flow = None
        if 'Flow' in obj.PropertiesList:
            prev_flow = obj.Flow
            obj.removeProperty('Flow')

        if addObjectProperty(obj, "Flow", ['Isothermal', 'NonIsothermal', 'HighMachCompressible'],
                             "App::PropertyEnumeration", "Physics modelling", "Flow algorithm"):
            obj.Flow = 'Isothermal'

        if prev_flow:
            if prev_flow == 'Incompressible':
                obj.Flow = 'Isothermal'
            elif prev_flow == 'Compressible':
                obj.Flow = 'NonIsothermal'
            else:
                obj.Flow = prev_flow

        if addObjectProperty(obj, "Phase", ['Single', 'FreeSurface'], "App::PropertyEnumeration", "Physics modelling",
                             "Type of phases present"):
            obj.Phase = 'Single'

        if addObjectProperty(obj, "Turbulence", ['Inviscid', 'Laminar', 'DES', 'RANS', 'LES'],
                             "App::PropertyEnumeration", "Physics modelling", "Type of turbulence modelling"):
            obj.Turbulence = 'Laminar'

        if addObjectProperty(obj, "TurbulenceModel", ['kOmegaSST', 'kEpsilon', 'SpalartAllmaras', 'kOmegaSSTLM',
                                                      'kOmegaSSTDES', 'kOmegaSSTDDES', 'kOmegaSSTIDDES',
                                                      'SpalartAllmarasDES', 'SpalartAllmarasDDES',
                                                      'SpalartAllmarasIDDES',
                                                      'kEqn', 'Smagorinsky', 'WALE'],
                             "App::PropertyEnumeration", "Physics modelling", "Turbulence model"):
            obj.TurbulenceModel = 'kOmegaSST'

        # Gravity
        addObjectProperty(obj, "gx", '0 m/s^2', "App::PropertyAcceleration", "Physics modelling",
                          "Gravitational acceleration vector (x component)")
        addObjectProperty(obj, "gy", '-9.81 m/s^2', "App::PropertyAcceleration", "Physics modelling",
                          "Gravitational acceleration vector (y component)")
        addObjectProperty(obj, "gz", '0 m/s^2', "App::PropertyAcceleration", "Physics modelling",
                          "Gravitational acceleration vector (z component)")

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


class _CfdPhysicsModel:
    """ Backward compatibility for old class name when loading from file """
    def onDocumentRestored(self, obj):
        CfdPhysicsModel(obj)

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None

    # dumps and loads replace __getstate__ and __setstate__ post v. 0.21.2
    def dumps(self):
        return None

    def loads(self, state):
        return None


class ViewProviderCfdPhysicsSelection:
    def __init__(self, vobj):
        vobj.Proxy = self
        self.taskd = None

    def getIcon(self):
        icon_path = os.path.join(CfdTools.getModulePath(), "Gui", "Icons", "physics.svg")
        return icon_path

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object
        self.bubbles = None

    def updateData(self, obj, prop):
        analysis_obj = CfdTools.getParentAnalysisObject(obj)
        # Ignore Shape updates as these relate to linked patches
        if prop != 'Shape':
            if analysis_obj and not analysis_obj.Proxy.loading:
                analysis_obj.NeedsCaseRewrite = True

    def onChanged(self, vobj, prop):
        return

    def setEdit(self, vobj, mode):
        from CfdOF.Solve import TaskPanelCfdPhysicsSelection
        import importlib
        importlib.reload(TaskPanelCfdPhysicsSelection)
        self.taskd = TaskPanelCfdPhysicsSelection.TaskPanelCfdPhysicsSelection(self.Object)
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


class _ViewProviderPhysicsSelection:
    """ Backward compatibility for old class name when loading from file """
    def attach(self, vobj):
        new_proxy = ViewProviderCfdPhysicsSelection(vobj)
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
