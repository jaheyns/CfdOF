# ***************************************************************************
# *                                                                         *
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
from FemCommands import FemCommands
import CfdTools
import os

if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore
    import FemGui

class setCfdFluidPropertyCommand(FemCommands):
    def __init__(self):
        self.is_active = 'with_analysis'    # Only activate when analysis is active

    def Activated(self):
        #selection = FreeCADGui.Selection.getSelectionEx()
        #selectedObj = FreeCADGui.Selection.getSelection()[0]

        FreeCAD.Console.PrintMessage("Set fluid properties \n")


        FreeCAD.ActiveDocument.openTransaction("Set CfdFluidMaterialProperty")
        FreeCADGui.addModule("CfdFluidMaterial")

        isPresent = False
        members = FemGui.getActiveAnalysis().Member
        for i in members:
            ''' Check for existing fluid material entity as the solver currently only support single region analysis.
            '''
            if "CfdFluidProperties" in i.Name:
                FreeCADGui.doCommand("Gui.activeDocument().setEdit('"+i.Name+"')")
                isPresent = True

        ''' NOTE: Since it is possible to delete the FluidProperties, allowing here for re-creation if it is not
                  present.
        '''
        if not(isPresent):
            FreeCADGui.doCommand("CfdFluidMaterial.makeCfdFluidMaterial('CfdFluidProperties')")

            # CFD WB is still a member of FemGui
            FreeCADGui.doCommand("App.activeDocument()." + FemGui.getActiveAnalysis().Name +
                                 ".Member = App.activeDocument()." + FemGui.getActiveAnalysis().Name +
                                 ".Member + [App.ActiveDocument.ActiveObject]")
            FreeCADGui.doCommand("Gui.activeDocument().setEdit(App.ActiveDocument.ActiveObject.Name)")



    def GetResources(self):
        icon_path = os.path.join(CfdTools.get_module_path(),"Gui","Resources","icons","material.png")
        return {
            'Pixmap' : icon_path ,
            'MenuText': 'Add fluid properties', 
            'ToolTip': 'Add fluid properties'
            } 

if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Cfd_FluidMaterial', setCfdFluidPropertyCommand())