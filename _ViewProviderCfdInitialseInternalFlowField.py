
__title__ = "_ViewProviderInitialiseInternalFlowField"
__author__ = ""
__url__ = "http://www.freecadweb.org"

import FreeCAD
import FreeCADGui


class _ViewProviderCfdInitialseInternalFlowField:
    "A View Provider for the InitialVariables object"

    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        return ""

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
        if not doc.getInEdit():
            doc.setEdit(vobj.Object.Name)
        else:
            FreeCAD.Console.PrintError('Active Task Dialog found! Please close this one first!\n')
        return True

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None
