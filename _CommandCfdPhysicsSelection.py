
__title__ = "Command Physics Model Selection"
__author__ = ""
__url__ = "http://www.freecadweb.org"

import FreeCAD
import platform
from PyGui.FemCommands import FemCommands
import FemGui
import CfdTools
import os

if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore


class _CommandCfdPhysicsSelection(FemCommands):
    " CFD physics selection command definition"
    def __init__(self):
        super(_CommandCfdPhysicsSelection, self).__init__()
        icon_path = os.path.join(CfdTools.get_module_path(),"Gui","Resources","icons","physics.png")
        self.resources = {'Pixmap': icon_path,
                          'MenuText': QtCore.QT_TRANSLATE_NOOP("Cfd_PhysicsModel", "Select models"),
                          'Accel': "",
                          'ToolTip': QtCore.QT_TRANSLATE_NOOP("Cfd_PhysicsModel", "Select the physics model")}
        self.is_active = 'with_analysis'

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Choose appropriate physics model")
        isPresent = False
        members = FemGui.getActiveAnalysis().Member
        for i in members:
            if "PhysicsModel" in i.Name:
                FreeCADGui.doCommand("Gui.activeDocument().setEdit('"+i.Name+"')")
                isPresent = True

        # Allow to re-create if deleted
        if not(isPresent):
            FreeCADGui.addModule("CfdPhysicsSelection")
            FreeCADGui.doCommand(
                "analysis.Member = analysis.Member + [CfdPhysicsSelection.makeCfdPhysicsSelection()]")
            FreeCADGui.doCommand("Gui.activeDocument().setEdit(App.ActiveDocument.ActiveObject.Name)")

if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Cfd_PhysicsModel', _CommandCfdPhysicsSelection())
