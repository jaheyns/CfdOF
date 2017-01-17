
__title__ = "Command for internal field initialisation"
__author__ = ""
__url__ = "http://www.freecadweb.org"

import FreeCAD
from FemCommands import FemCommands
import FemGui

if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore


class _CommandCfdInitialiseInternalFlowField(FemCommands):
    "the Cfd_SolverControl command definition"
    def __init__(self):
        super(_CommandCfdInitialiseInternalFlowField, self).__init__()
        self.resources = {'Pixmap': '',
                          'MenuText': QtCore.QT_TRANSLATE_NOOP("Cfd_InitialiseInternal", "Initialise"),
                          'Accel': "",
                          'ToolTip': QtCore.QT_TRANSLATE_NOOP("Cfd_InitialiseInternal", "Initialise internal flow variables based on the selected physics model")}
        #self.is_active = 'with_solver'
        self.is_active = 'with_analysis'

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Initialise the internal flow variables")
        
        
        isPresent = False
        members = FemGui.getActiveAnalysis().Member
        for i in members:
            if "InitializeInternalVariables" in i.Name:
                FreeCADGui.doCommand("Gui.activeDocument().setEdit('"+i.Name+"')")
                isPresent = True
        ##NOTE: since it is possible to delete the initialVariables object, allowing here for re-creation not present.
        if not(isPresent):
            FreeCADGui.addModule("CfdInitialiseFlowField")
            FreeCADGui.addModule("FemGui")
            FreeCADGui.doCommand("FemGui.getActiveAnalysis().Member = FemGui.getActiveAnalysis().Member + [CfdInitialiseFlowField.makeCfdInitialFlowField()]")
            FreeCADGui.doCommand("Gui.activeDocument().setEdit(App.ActiveDocument.ActiveObject.Name)")

if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Cfd_InitialiseInternal', _CommandCfdInitialiseInternalFlowField())
