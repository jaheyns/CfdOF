
__title__ = "Command Physics Model Selection"
__author__ = ""
__url__ = "http://www.freecadweb.org"

import FreeCAD
from FemCommands import FemCommands
import FemGui

if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore


class _CommandCfdPhysicsSelection(FemCommands):
    "the CFD physics selection command definition"
    def __init__(self):
        super(_CommandCfdPhysicsSelection, self).__init__()
        self.resources = {'Pixmap': '',
                          'MenuText': QtCore.QT_TRANSLATE_NOOP("Cfd_PhysicsModel", "Select models"),
                          'Accel': "",
                          'ToolTip': QtCore.QT_TRANSLATE_NOOP("Cfd_PhysicsModel", "Select the physics model")}
        #self.is_active = 'with_solver'
        self.is_active = 'with_analysis'

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Choose appropriate physics model")
        FreeCADGui.addModule("CfdPhysicsSelection")
        
        isPresent = False
        members = FemGui.getActiveAnalysis().Member
        for i in members:
            #Physics model is currently created upon creation of CfdAnylis. Therefore rather than creating a new physicsmodel
            #when command is activated, the one that is already present is selected. The name is searched for because
            #there can still be multiple entities when multiple analyses are created. Member.Name is not changed when the label
            #in the GUI is changed. Changing the name in the Gui affects the Member.Label
            if "PhysicsModel" in i.Name:
                FreeCADGui.doCommand("Gui.activeDocument().setEdit('"+i.Name+"')")
                isPresent = True
        #NOTE: since it is possible to delete the PhysicsModel, allowing here for re-creation if a physics model is not present.
        if not(isPresent):
            FreeCADGui.addModule("FemGui")
            FreeCADGui.doCommand("FemGui.getActiveAnalysis().Member = FemGui.getActiveAnalysis().Member + [CfdPhysicsSelection.makeCfdPhysicsSelection()]")
            FreeCADGui.doCommand("Gui.activeDocument().setEdit(App.ActiveDocument.ActiveObject.Name)")

if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Cfd_PhysicsModel', _CommandCfdPhysicsSelection())
