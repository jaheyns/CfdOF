# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2017-2018 Alfred Bogaers (CSIR) <abogaers@csir.co.za>   *
# *   Copyright (c) 2017-2018 Johan Heyns (CSIR) <jheyns@csir.co.za>        *
# *   Copyright (c) 2017-2018 Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>     *
# *   Copyright (c) 2019 Oliver Oxtoby <oliveroxtoby@gmail.com>             *
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
import CfdTools
from CfdTools import addObjectProperty
import os
import os.path
if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore


def makeCfdPhysicsSelection(name="PhysicsModel"):
    # DocumentObjectGroupPython, FeaturePython, GeometryPython
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", name)
    _CfdPhysicsModel(obj)
    if FreeCAD.GuiUp:
        _ViewProviderPhysicsSelection(obj.ViewObject)
    return obj


class _CommandCfdPhysicsSelection:
    """ CFD physics selection command definition """

    def GetResources(self):
        icon_path = os.path.join(CfdTools.get_module_path(), "Gui", "Resources", "icons", "physics.svg")
        return {'Pixmap': icon_path,
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Cfd_PhysicsModel", "Select models"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Cfd_PhysicsModel", "Select the physics model")}

    def IsActive(self):
        return CfdTools.getActiveAnalysis() is not None

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Choose appropriate physics model")
        is_present = False
        members = CfdTools.getActiveAnalysis().Group
        for i in members:
            if isinstance(i.Proxy, _CfdPhysicsModel):
                FreeCADGui.activeDocument().setEdit(i.Name)
                is_present = True

        # Allow to re-create if deleted
        if not is_present:
            FreeCADGui.doCommand("")
            FreeCADGui.addModule("CfdPhysicsSelection")
            FreeCADGui.addModule("CfdTools")
            FreeCADGui.doCommand(
                "CfdTools.getActiveAnalysis().addObject(CfdPhysicsSelection.makeCfdPhysicsSelection())")
            FreeCADGui.ActiveDocument.setEdit(FreeCAD.ActiveDocument.ActiveObject.Name)


class _CfdPhysicsModel:
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

        if addObjectProperty(obj, "Flow", ['Incompressible', 'Compressible', 'HighMachCompressible'],
                             "App::PropertyEnumeration", "Physics modelling", "Flow algorithm"):
            obj.Flow = 'Incompressible'

        if addObjectProperty(obj, "Thermal", ['None', 'Energy'], "App::PropertyEnumeration", "Physics modelling",
                             "Thermal modelling"):
            obj.Thermal = 'None'

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
        addObjectProperty(obj, 'SRFModelRPM', "0", "App::PropertyString", "SRF model", "Rotational speed")

        addObjectProperty(obj, 'SRFModelCoR', FreeCAD.Vector(0, 0, 0), "App::PropertyPosition", "SRF model",
                          "SRF centre of rotation")

        addObjectProperty(obj, 'SRFModelAxis', FreeCAD.Vector(0, 0, 0), "App::PropertyPosition", "SRF model",
                          "SRF rotational axis")

    def onDocumentRestored(self, obj):
        self.initProperties(obj)


class _ViewProviderPhysicsSelection:
    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        icon_path = os.path.join(CfdTools.get_module_path(), "Gui", "Resources", "icons", "physics.svg")
        return icon_path

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object
        self.bubbles = None

    def updateData(self, obj, prop):
        return

    def onChanged(self, vobj, prop):
        return

    def setEdit(self, vobj, mode):
        import _TaskPanelCfdPhysicsSelection
        taskd = _TaskPanelCfdPhysicsSelection._TaskPanelCfdPhysicsSelection(self.Object)
        taskd.obj = vobj.Object
        FreeCADGui.Control.showDialog(taskd)
        return True

    def unsetEdit(self, vobj, mode):
        FreeCADGui.Control.closeDialog()
        return

    def doubleClicked(self, vobj):
        # Make sure no other task dialog still active
        doc = FreeCADGui.getDocument(vobj.Object.Document)
        if not doc.getInEdit():
            doc.setEdit(vobj.Object.Name)
        else:
            FreeCAD.Console.PrintError('Existing task dialog already open\n')
        return True

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Cfd_PhysicsModel', _CommandCfdPhysicsSelection())