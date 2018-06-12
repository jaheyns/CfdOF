# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2017-2018                                               *
# *   Johan Heyns (CSIR) <jheyns@csir.co.za>                                *
# *   Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>                             *
# *   Alfred Bogaers (CSIR) <abogaers@csir.co.za>                           *
# *   Copyright (c) 2013-2015 - Juergen Riegel <FreeCAD@juergen-riegel.net> *
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
import platform
try:
    from femcommands.manager import CommandManager
except ImportError:  # Backward compatibility
    from PyGui.FemCommands import FemCommands as CommandManager
import CfdTools
import os

if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore
    import FemGui


def makeCfdFluidMaterial(name):
    obj = FreeCAD.ActiveDocument.addObject("App::MaterialObjectPython", name)

    _CfdMaterial(obj)  # Include default fluid properties
    if FreeCAD.GuiUp:
        _ViewProviderCfdFluidMaterial(obj.ViewObject)
    return obj


class setCfdFluidPropertyCommand(CommandManager):
    def __init__(self):
        icon_path = os.path.join(CfdTools.get_module_path(), "Gui", "Resources", "icons", "material.png")
        self.resources = {
            'Pixmap': icon_path,
            'MenuText': 'Add fluid properties',
            'ToolTip': 'Add fluid properties'
            }
        self.is_active = 'with_analysis'  # Only activate when analysis is active

    def Activated(self):
        FreeCAD.Console.PrintMessage("Set fluid properties \n")
        FreeCAD.ActiveDocument.openTransaction("Set CfdFluidMaterialProperty")

        FreeCADGui.addModule("FemGui")
        FreeCADGui.addModule("CfdFluidMaterial")
        editing_existing = False
        analysis_object = FemGui.getActiveAnalysis()
        if analysis_object is None:
            CfdTools.cfdError("No analysis object found")
            return False
        physics_model, phys_model_present = CfdTools.getPhysicsModel(analysis_object)
        if not phys_model_present or physics_model.Phase == 'Single':
            members = analysis_object.Group
            for i in members:
                if i.Name.startswith('FluidProperties'):
                    FreeCADGui.doCommand("Gui.activeDocument().setEdit('"+i.Name+"')")
                    editing_existing = True
        if not editing_existing:
            FreeCADGui.doCommand(
                "FemGui.getActiveAnalysis().addObject(CfdFluidMaterial.makeCfdFluidMaterial('FluidProperties'))")
            FreeCADGui.ActiveDocument.setEdit(FreeCAD.ActiveDocument.ActiveObject.Name)


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Cfd_FluidMaterial', setCfdFluidPropertyCommand())


class _CfdMaterial:
    """ CFD material properties object """
    def __init__(self, obj):
        obj.Proxy = self
        self.Type = "CfdMaterial"
        # Currently unused but necessary for compatibility with MaterialObjectPython
        self.Material = {}
        self.initProperties(obj)

    def initProperties(self, obj):
        if "References" not in obj.PropertiesList:
            obj.addProperty("App::PropertyLinkSubList", "References", "Material", "List of material shapes")

        #if "Material" not in obj.PropertiesList:
        #    obj.addProperty("App::PropertyMap", "Material", "Material", "Material Properties")

        if 'Density' not in obj.PropertiesList:
            # We cannot presently use PropertyQuantity because units cannot be
            # set from Python. Use string instead for now.
            obj.addProperty("App::PropertyString", "Density", "Properties", "Density")
            obj.Density = '1.2 kg/m^3'

        if 'DynamicViscosity' not in obj.PropertiesList:
            obj.addProperty("App::PropertyString", "DynamicViscosity", "Properties", "Dynamic Viscosity")
            obj.DynamicViscosity = '1.8e-5 kg/m/s'

        if 'MolarMass' not in obj.PropertiesList:
            obj.addProperty("App::PropertyString", "MolarMass", "Properties", "Molar mass")
            obj.MolarMass = '0.02896438 kg/mol'

        if 'Cp' not in obj.PropertiesList:
            obj.addProperty("App::PropertyString", "Cp", "Properties", "Specific heat (Cp)")
            obj.Cp = '1004.703 J/kg/K'

        if 'SutherlandConstant' not in obj.PropertiesList:
            obj.addProperty("App::PropertyString", "SutherlandConstant", "Properties", "Sutherland constant")
            obj.SutherlandConstant = '1.4579327e-6 kg/m/s/K^0.5'

        if 'SutherlandTemperature' not in obj.PropertiesList:
            obj.addProperty("App::PropertyString", "SutherlandTemperature", "Properties", "Sutherland temperature")
            obj.SutherlandTemperature = '110.4 K'

    def execute(self, obj):
        return


class _ViewProviderCfdFluidMaterial:
    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        # """after load from FCStd file, self.icon does not exist, return constant path instead"""
        # return ":/icons/fem-material.svg"
        icon_path = os.path.join(CfdTools.get_module_path(), "Gui", "Resources", "icons", "material.png")
        return icon_path

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object

    def updateData(self, obj, prop):
        return

    def onChanged(self, vobj, prop):
        return

    def doubleClicked(self, vobj):
        doc = FreeCADGui.getDocument(vobj.Object.Document)
        if not doc.getInEdit():
            doc.setEdit(vobj.Object.Name)
        else:
            FreeCAD.Console.PrintError('Active Task Dialog found! Please close this one first!\n')
        return True

    def setEdit(self, vobj, mode):
        analysis_object = CfdTools.getParentAnalysisObject(self.Object)
        if analysis_object is None:
            CfdTools.cfdError("No parent analysis object found")
            return False
        physics_model, is_present = CfdTools.getPhysicsModel(analysis_object)
        if not is_present:
            CfdTools.cfdError("Analysis object must have a physics object")
            return False
        import _TaskPanelCfdFluidProperties
        taskd = _TaskPanelCfdFluidProperties.TaskPanelCfdFluidProperties(self.Object, physics_model)
        taskd.obj = vobj.Object
        FreeCADGui.Control.showDialog(taskd)
        return True

    def unsetEdit(self, vobj, mode):
        FreeCADGui.Control.closeDialog()
        return

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None