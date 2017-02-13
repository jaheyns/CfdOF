
__title__ = "_ViewProviderInitialiseInternalFlowField"
__author__ = ""
__url__ = "http://www.freecadweb.org"

import FreeCAD
import FreeCADGui
import FemGui
import CfdTools
import os

class _ViewProviderCfdInitialseInternalFlowField:
    "A View Provider for the InitialVariables object"

    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        icon_path = os.path.join(CfdTools.get_module_path(), "Gui", "Resources", "icons", "initialise.png")
        return icon_path

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object

    def updateData(self, obj, prop):
        return

    def onChanged(self, vobj, prop):
        return

    def setEdit(self, vobj, mode):
        import _TaskPanelCfdInitialiseInternalFlowField
        taskd = _TaskPanelCfdInitialiseInternalFlowField._TaskPanelCfdInitialiseInternalFlowField(self.Object)
        taskd.obj = vobj.Object
        FreeCADGui.Control.showDialog(taskd)
        return True
    

    def unsetEdit(self, vobj, mode):
        FreeCADGui.Control.closeDialog()
        return

    # overwrite the doubleClicked to make sure no other Material taskd (and thus no selection observer) is still active
    def doubleClicked(self, vobj):
        doc = FreeCADGui.getDocument(vobj.Object.Document)
        if not FemGui.getActiveAnalysis():
            analysis_obj = CfdTools.getActiveAnalysis(self.Object)
            if analysis_obj:
                FemGui.setActiveAnalysis(analysis_obj)
            else:
                FreeCAD.Console.PrintError('No Active Analysis is detected from solver object in the active Document!\n')
        if not doc.getInEdit():
            doc.setEdit(vobj.Object.Name)
        else:
            FreeCAD.Console.PrintError('Active Task Dialog found! Please close this one first!\n')
        return True

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None
