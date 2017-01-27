
__title__ = "Command to generate a porous zone"
__author__ = ""
__url__ = "http://www.freecadweb.org"

import FreeCAD
from FemCommands import FemCommands
import FemGui
import CfdTools
import os

if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore




class _CommandCfdPorousZone(FemCommands):
    "the Cfd_SolverControl command definition"
    def __init__(self):
        super(_CommandCfdPorousZone, self).__init__()
        icon_path = os.path.join(CfdTools.get_module_path(),"Gui","Resources","icons","")
        self.resources = {'Pixmap': icon_path,
                          'MenuText': QtCore.QT_TRANSLATE_NOOP("Cfd_PorousZone", "Porous zone"),
                          'Accel': "",
                          'ToolTip': QtCore.QT_TRANSLATE_NOOP("Cfd_PorousZone", "Select and create a porous zone")}
        #self.is_active = 'with_solver'
        self.is_active = 'with_analysis'

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Select and create a porous zone")
        
        
        isPresent = False
        members = FemGui.getActiveAnalysis().Member
        FreeCADGui.addModule("FemGui")
        FreeCADGui.addModule("CfdPorousZone")
        FreeCADGui.doCommand("FemGui.getActiveAnalysis().Member = FemGui.getActiveAnalysis().Member + [CfdPorousZone.makeCfdPorousZone()]")
        FreeCADGui.doCommand("Gui.activeDocument().setEdit(App.ActiveDocument.ActiveObject.Name)")
        
if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Cfd_PorousZone', _CommandCfdPorousZone())
