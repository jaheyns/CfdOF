# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileNotice: Part of the CfdOF addon.

import os

import FreeCAD
import FreeCADGui
from pivy import coin

from CfdOF import CfdTools
from CfdOF.CfdTools import addObjectProperty

QT_TRANSLATE_NOOP = FreeCAD.Qt.QT_TRANSLATE_NOOP


def makeCfdMeanVelocityForce(name="MeanVelocityForce"):
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", name)
    CfdMeanVelocityForce(obj)
    if FreeCAD.GuiUp:
        ViewProviderCfdMeanVelocityForce(obj.ViewObject)
    return obj


class CommandCfdMeanVelocityForce:
    def __init__(self):
        pass

    def GetResources(self):
        icon_path = os.path.join(CfdTools.getModulePath(), "Gui", "Icons", "meanvelocityforce.svg")
        return {
            'Pixmap': icon_path,
            'MenuText': QT_TRANSLATE_NOOP("CfdOF_MeanVelocityForce", "Mean velocity force"),
            'ToolTip': QT_TRANSLATE_NOOP("CfdOF_MeanVelocityForce", "Create a mean velocity force fvOption"),
        }

    def IsActive(self):
        return CfdTools.getActiveAnalysis() is not None

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Create MeanVelocityForce object")
        FreeCADGui.doCommand("")
        FreeCADGui.doCommand("from CfdOF.Solve import CfdMeanVelocityForce")
        FreeCADGui.doCommand("from CfdOF import CfdTools")
        FreeCADGui.doCommand(
            "CfdTools.getActiveAnalysis().addObject(CfdMeanVelocityForce.makeCfdMeanVelocityForce())")
        FreeCADGui.ActiveDocument.setEdit(FreeCAD.ActiveDocument.ActiveObject.Name)


class CfdMeanVelocityForce:
    def __init__(self, obj):
        self.Object = obj
        self.initProperties(obj)

    def initProperties(self, obj):
        obj.Proxy = self
        self.Type = 'CfdMeanVelocityForce'

        addObjectProperty(
            obj,
            "Direction",
            FreeCAD.Vector(0, 0, 0),
            "App::PropertyVector",
            "Mean velocity force",
            QT_TRANSLATE_NOOP("App::Property", "Direction vector for the mean velocity force"),
        )
        addObjectProperty(
            obj,
            "Ubar",
            FreeCAD.Vector(0, 0, 0),
            "App::PropertyVector",
            "Mean velocity force",
            QT_TRANSLATE_NOOP("App::Property", "Target mean velocity vector"),
        )
        addObjectProperty(
            obj,
            "Relaxation",
            0.2,
            "App::PropertyFloat",
            "Mean velocity force",
            QT_TRANSLATE_NOOP("App::Property", "Relaxation factor for mean velocity force"),
        )

    def onDocumentRestored(self, obj):
        self.initProperties(obj)

    def execute(self, obj):
        pass

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None

    def dumps(self):
        return None

    def loads(self, state):
        return None


class ViewProviderCfdMeanVelocityForce:
    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        icon_path = os.path.join(CfdTools.getModulePath(), "Gui", "Icons", "meanvelocityforce.svg")
        return icon_path

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object
        self.standard = coin.SoGroup()
        vobj.addDisplayMode(self.standard, "Standard")
        return

    def updateData(self, obj, prop):
        analysis_obj = CfdTools.getParentAnalysisObject(obj)
        if analysis_obj and not analysis_obj.Proxy.loading:
            analysis_obj.NeedsCaseRewrite = True

    def onChanged(self, vobj, prop):
        return

    def doubleClicked(self, vobj):
        doc = FreeCADGui.getDocument(vobj.Object.Document)
        if not doc.getInEdit():
            doc.setEdit(vobj.Object.Name)
        else:
            FreeCAD.Console.PrintError('Task dialog already active\\n')
            FreeCADGui.Control.showTaskView()
        return True

    def setEdit(self, vobj, mode):
        analysis_object = CfdTools.getParentAnalysisObject(self.Object)
        if analysis_object is None:
            CfdTools.cfdErrorBox("Mean velocity force object must have a parent analysis object")
            return False

        from CfdOF.Solve import TaskPanelCfdMeanVelocityForce
        import importlib
        importlib.reload(TaskPanelCfdMeanVelocityForce)
        taskd = TaskPanelCfdMeanVelocityForce.TaskPanelCfdMeanVelocityForce(self.Object)
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

    def dumps(self):
        return None

    def loads(self, state):
        return None


class _ViewProviderCfdMeanVelocityForce:
    def attach(self, vobj):
        new_proxy = ViewProviderCfdMeanVelocityForce(vobj)
        new_proxy.attach(vobj)

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None

    def dumps(self):
        return None

    def loads(self, state):
        return None
