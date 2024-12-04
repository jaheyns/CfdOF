# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2013-2015 - Juergen Riegel <FreeCAD@juergen-riegel.net> *
# *   Copyright (c) 2017-2018 Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>     *
# *   Copyright (c) 2017-2018 Alfred Bogaers (CSIR) <abogaers@csir.co.za>   *
# *   Copyright (c) 2017-2018 Johan Heyns (CSIR) <jheyns@csir.co.za>        *
# *   Copyright (c) 2019-2022 Oliver Oxtoby <oliveroxtoby@gmail.com>        *
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

if FreeCAD.GuiUp:
    import FreeCADGui
from CfdOF import CfdTools
from CfdOF.CfdTools import addObjectProperty
from CfdOF.Solve import TaskPanelCfdFluidProperties

translate = FreeCAD.Qt.translate
QT_TRANSLATE_NOOP = FreeCAD.Qt.QT_TRANSLATE_NOOP


def makeCfdFluidMaterial(name):
    obj = FreeCAD.ActiveDocument.addObject("App::MaterialObjectPython", name)
    CfdMaterial(obj)  # Include default fluid properties
    if FreeCAD.GuiUp:
        ViewProviderCfdFluidMaterial(obj.ViewObject)
    return obj


class CommandCfdFluidMaterial:

    def GetResources(self):
        icon_path = os.path.join(CfdTools.getModulePath(), "Gui", "Icons", "material.svg")
        return {
            'Pixmap': icon_path,
            'MenuText': QT_TRANSLATE_NOOP("CfdOF_FluidMaterial", "Add fluid properties"),
            'ToolTip': QT_TRANSLATE_NOOP("CfdOF_FluidMaterial", "Add fluid properties")}

    def IsActive(self):
        return CfdTools.getActiveAnalysis() is not None

    def Activated(self):
        FreeCAD.Console.PrintMessage(translate("Console", "Set fluid properties \n"))
        FreeCAD.ActiveDocument.openTransaction("Set CfdFluidMaterialProperty")
        FreeCADGui.doCommand("from CfdOF import CfdTools")
        FreeCADGui.doCommand("from CfdOF.Solve import CfdFluidMaterial")
        editing_existing = False
        analysis_object = CfdTools.getActiveAnalysis()
        if analysis_object is None:
            CfdTools.cfdErrorBox("No active analysis object found")
            return False
        physics_model = CfdTools.getPhysicsModel(analysis_object)
        if not physics_model or physics_model.Phase == 'Single':
            members = analysis_object.Group
            for i in members:
                if isinstance(i.Proxy, CfdMaterial):
                    FreeCADGui.activeDocument().setEdit(i.Name)
                    editing_existing = True
        if not editing_existing:
            FreeCADGui.doCommand(
                "CfdTools.getActiveAnalysis().addObject(CfdFluidMaterial.makeCfdFluidMaterial('FluidProperties'))")
            FreeCADGui.ActiveDocument.setEdit(FreeCAD.ActiveDocument.ActiveObject.Name)


class CfdMaterial:
    """ CFD material properties object. Compatible with FreeCAD material object. """
    def __init__(self, obj):
        obj.Proxy = self
        self.Type = "CfdMaterial"
        self.initProperties(obj)

    def initProperties(self, obj):
        # Not currently used, but required for parent class
        addObjectProperty(
            obj,
            "References",
            [],
            "App::PropertyLinkSubListGlobal",
            "Material",
            QT_TRANSLATE_NOOP("App::Property", "List of material shapes"),
        )

        # Compatibility with FEM material object
        if addObjectProperty(
            obj,
            "Category",
            ["Solid", "Fluid"],
            "App::PropertyEnumeration",
            "Material",
            QT_TRANSLATE_NOOP("App::Property", "Type of material"),
        ):
            obj.Category = "Fluid"

        # 'Material' PropertyMap already present in MaterialObjectPython
        if not obj.Material:
            mats, name_path_list = CfdTools.importMaterials()
            # Load a default to initialise the values for each type
            obj.Material = mats[name_path_list[[np[0] for np in name_path_list].index('AirIsothermal')][1]]
        elif not obj.Material.get('Type'):
            mat = obj.Material
            mat['Type'] = 'Isothermal'
            obj.Material = mat

    def onDocumentRestored(self, obj):
        self.initProperties(obj)

    def execute(self, obj):
        return


class _CfdMaterial:
    """ Backward compatibility for old class name when loading from file """
    def onDocumentRestored(self, obj):
        CfdMaterial(obj)


class ViewProviderCfdFluidMaterial:
    def __init__(self, vobj):
        vobj.Proxy = self
        self.taskd = None

    def getIcon(self):
        icon_path = os.path.join(CfdTools.getModulePath(), "Gui", "Icons", "material.svg")
        return icon_path

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object

    def updateData(self, obj, prop):
        analysis_obj = CfdTools.getParentAnalysisObject(obj)
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
        import importlib
        importlib.reload(TaskPanelCfdFluidProperties)
        self.taskd = TaskPanelCfdFluidProperties.TaskPanelCfdFluidProperties(self.Object, physics_model)
        self.taskd.obj = vobj.Object
        FreeCADGui.Control.showDialog(self.taskd)
        return True

    def doubleClicked(self, vobj):
        doc = FreeCADGui.getDocument(vobj.Object.Document)
        if not doc.getInEdit():
            doc.setEdit(vobj.Object.Name)
        else:
            FreeCAD.Console.PrintError('Task dialog already open\n')
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


class _ViewProviderCfdFluidMaterial:
    """ Backward compatibility for old class name when loading from file """
    def attach(self, vobj):
        new_proxy = ViewProviderCfdFluidMaterial(vobj)
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
