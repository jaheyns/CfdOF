# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: © 2024 CfdOF contributors
# SPDX-FileNotice: Part of the CfdOF addon.

import os
import FreeCAD

if FreeCAD.GuiUp:
    import FreeCADGui
from CfdOF import CfdTools
from CfdOF.CfdTools import addObjectProperty

translate = FreeCAD.Qt.translate
QT_TRANSLATE_NOOP = FreeCAD.Qt.QT_TRANSLATE_NOOP


def makeCfdSolidMaterial(name):
    obj = FreeCAD.ActiveDocument.addObject("App::MaterialObjectPython", name)
    CfdSolidMaterial(obj)
    if FreeCAD.GuiUp:
        ViewProviderCfdSolidMaterial(obj.ViewObject)
    return obj


class CommandCfdSolidMaterial:

    def GetResources(self):
        icon_path = os.path.join(CfdTools.getModulePath(), "Gui", "Icons", "solid_material.svg")
        return {
            'Pixmap': icon_path,
            'MenuText': QT_TRANSLATE_NOOP("CfdOF_SolidMaterial", "Add solid properties"),
            'ToolTip': QT_TRANSLATE_NOOP("CfdOF_SolidMaterial", "Add solid material properties for CHT simulation")}

    def IsActive(self):
        return CfdTools.getActiveAnalysis() is not None

    def Activated(self):
        FreeCAD.Console.PrintMessage(translate("Console", "Set solid properties\n"))
        FreeCAD.ActiveDocument.openTransaction("Set CfdSolidMaterial")
        FreeCADGui.doCommand("from CfdOF import CfdTools")
        FreeCADGui.doCommand("from CfdOF.Solve import CfdSolidMaterial")
        FreeCADGui.doCommand(
            "CfdTools.getActiveAnalysis().addObject(CfdSolidMaterial.makeCfdSolidMaterial('SolidProperties'))")
        FreeCADGui.ActiveDocument.setEdit(FreeCAD.ActiveDocument.ActiveObject.Name)


class CfdSolidMaterial:
    """Solid material properties for CHT multi-region simulation."""

    def __init__(self, obj):
        self.initProperties(obj)

    def initProperties(self, obj):
        obj.Proxy = self
        self.Type = 'CfdSolidMaterial'

        addObjectProperty(
            obj,
            "ShapeRefs",
            [],
            "App::PropertyLinkSubListGlobal",
            "Solid region",
            QT_TRANSLATE_NOOP("App::Property", "Solid body defining this region"),
        )

        addObjectProperty(
            obj,
            "RegionName",
            "",
            "App::PropertyString",
            "Solid region",
            QT_TRANSLATE_NOOP("App::Property",
                              "OpenFOAM region name (defaults to object Label if empty)"),
        )

        addObjectProperty(
            obj,
            "HeatGeneration",
            "0 W/m^3",
            "App::PropertyQuantity",
            "Solid region",
            QT_TRANSLATE_NOOP("App::Property", "Volumetric heat generation rate"),
        )

        if not obj.Material:
            mats, name_path_list = CfdTools.importMaterials()
            names = [np[0] for np in name_path_list]
            if 'AluminiumSolid' in names:
                obj.Material = mats[name_path_list[names.index('AluminiumSolid')][1]]
            else:
                obj.Material = {'Name': 'Custom', 'Description': '', 'Type': 'Solid',
                                'ThermalConductivity': '1 W/m/K',
                                'Density': '1000 kg/m^3',
                                'SpecificHeat': '500 J/kg/K'}

    def onDocumentRestored(self, obj):
        self.initProperties(obj)
        if FreeCAD.GuiUp and obj.ViewObject.Proxy == 0:
            ViewProviderCfdSolidMaterial(obj.ViewObject)

    def execute(self, obj):
        return


class ViewProviderCfdSolidMaterial:
    def __init__(self, vobj):
        vobj.Proxy = self
        self.taskd = None

    def getIcon(self):
        return os.path.join(CfdTools.getModulePath(), "Gui", "Icons", "solid_material.svg")

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object
        self.taskd = None

    def updateData(self, obj, prop):
        analysis_obj = CfdTools.getParentAnalysisObject(obj)
        if analysis_obj and not analysis_obj.Proxy.loading:
            analysis_obj.NeedsCaseRewrite = True

    def onChanged(self, vobj, prop):
        return

    def setEdit(self, vobj, mode):
        obj = getattr(self, 'Object', vobj.Object)
        self.Object = obj
        analysis_object = CfdTools.getParentAnalysisObject(obj)
        if analysis_object is None:
            CfdTools.cfdErrorBox("No parent analysis object found")
            return False
        import importlib
        from CfdOF.Solve import TaskPanelCfdSolidProperties
        importlib.reload(TaskPanelCfdSolidProperties)
        self.taskd = TaskPanelCfdSolidProperties.TaskPanelCfdSolidProperties(obj)
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
        if getattr(self, 'taskd', None):
            self.taskd.closing()
            self.taskd = None
        FreeCADGui.Control.closeDialog()

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None

    def dumps(self):
        return None

    def loads(self, state):
        return None


FreeCADGui.addCommand('CfdOF_SolidMaterial', CommandCfdSolidMaterial())
