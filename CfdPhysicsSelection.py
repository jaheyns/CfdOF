# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2017-2018                                               *
# *   Alfred Bogaers (CSIR) <abogaers@csir.co.za>                           *
# *   Johan Heyns (CSIR) <jheyns@csir.co.za>                                *
# *   Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>                             *
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
from femcommands.manager import CommandManager
import FemGui


def makeCfdPhysicsSelection(name="PhysicsModel"):
    obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython", name)
    _CfdPhysicsModel(obj)

    if FreeCAD.GuiUp:
        _ViewProviderPhysicsSelection(obj.ViewObject)
    return obj


class _CommandCfdPhysicsSelection(CommandManager):
    """ CFD physics selection command definition """
    def __init__(self):
        super(_CommandCfdPhysicsSelection, self).__init__()
        icon_path = os.path.join(CfdTools.get_module_path(), "Gui", "Resources", "icons", "physics.png")
        self.resources = {'Pixmap': icon_path,
                          'MenuText': QtCore.QT_TRANSLATE_NOOP("Cfd_PhysicsModel", "Select models"),
                          'Accel': "",
                          'ToolTip': QtCore.QT_TRANSLATE_NOOP("Cfd_PhysicsModel", "Select the physics model")}
        self.is_active = 'with_analysis'

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Choose appropriate physics model")
        isPresent = False
        members = FemGui.getActiveAnalysis().Group
        for i in members:
            if "PhysicsModel" in i.Name:
                FreeCADGui.doCommand("Gui.activeDocument().setEdit('"+i.Name+"')")
                isPresent = True

        # Allow to re-create if deleted
        if not isPresent:
            FreeCADGui.addModule("CfdPhysicsSelection")
            FreeCADGui.addModule("FemGui")
            FreeCADGui.doCommand("FemGui.getActiveAnalysis().addObject(CfdPhysicsSelection.makeCfdPhysicsSelection())")
            FreeCADGui.ActiveDocument.setEdit(FreeCAD.ActiveDocument.ActiveObject.Name)


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Cfd_PhysicsModel', _CommandCfdPhysicsSelection())


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

        if 'Time' not in obj.PropertiesList:
            obj.addProperty("App::PropertyEnumeration", "Time", "Physics modelling",
                            "Resolve time dependence")
            obj.Time = ['Steady', 'Transient']
            obj.Time = 'Steady'

        if 'Flow' not in obj.PropertiesList:
            obj.addProperty("App::PropertyEnumeration", "Flow", "Physics modelling",
                            "Flow algorithm")
            obj.Flow = ['Incompressible', 'Compressible', 'HighMachCompressible']
            obj.Flow = 'Incompressible'

        if 'Thermal' not in obj.PropertiesList:
            obj.addProperty("App::PropertyEnumeration", "Thermal", "Physics modelling",
                            "Thermal modelling")
            obj.Thermal = ['None', 'Buoyancy', 'Energy']
            obj.Thermal = 'None'

        if 'Phase' not in obj.PropertiesList:
            obj.addProperty("App::PropertyEnumeration", "Phase", "Physics modelling",
                            "Type of phases present")
            obj.Phase = ['Single', 'FreeSurface']
            obj.Phase = 'Single'

        if 'Turbulence' not in obj.PropertiesList:
            obj.addProperty("App::PropertyEnumeration", "Turbulence", "Physics modelling",
                        "Type of turbulence modelling")
            obj.Turbulence = ['Inviscid', 'Laminar', 'RANS']
            obj.Turbulence = 'Laminar'

        if 'TurbulenceModel' not in obj.PropertiesList:
            obj.addProperty("App::PropertyEnumeration", "TurbulenceModel", "Physics modelling",
                            "Turbulence model")
            obj.TurbulenceModel = ['kOmegaSST']

        if 'gx' not in obj.PropertiesList:
            obj.addProperty("App::PropertyAcceleration", "gx", "Physics modelling",
                            "Gravitational acceleration vector (x component)")
            obj.gx = '0 m/s^2'
        if 'gy' not in obj.PropertiesList:
            obj.addProperty("App::PropertyAcceleration", "gy", "Physics modelling",
                            "Gravitational acceleration vector (y component)")
            obj.gy = '-9.81 m/s^2'
        if 'gz' not in obj.PropertiesList:
            obj.addProperty("App::PropertyAcceleration", "gz", "Physics modelling",
                            "Gravitational acceleration vector (z component)")
            obj.gz = '0 m/s^2'

    def execute(self, obj):
        return


class _ViewProviderPhysicsSelection:
    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        icon_path = os.path.join(CfdTools.get_module_path(), "Gui", "Resources", "icons", "physics.png")
        return icon_path

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object

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
