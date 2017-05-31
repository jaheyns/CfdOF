# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2013-2015 - Juergen Riegel <FreeCAD@juergen-riegel.net> *
# *   Copyright (c) 2017 - Johan Heyns <jheyns@csir.co.za>                  *
# *   Copyright (c) 2017 - Alfred Bogaers <abogaers@csir.co.za>             *
# *   Copyright (c) 2017 - Oliver Oxtoby <ooxtoby@csir.co.za>               *
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
import platform
from PyGui.FemCommands import FemCommands
import CfdTools
import os

if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore
    import FemGui


class setCfdFluidPropertyCommand(FemCommands):
    def __init__(self):
        icon_path = os.path.join(CfdTools.get_module_path(), "Gui", "Resources", "icons", "material.png")
        self.resources = {
            'Pixmap': icon_path,
            'MenuText': 'Add fluid properties',
            'ToolTip': 'Add fluid properties'
            }
        self.is_active = 'with_analysis'  # Only activate when analysis is active

    def Activated(self):
        FreeCAD.Console.PrintMessage("Set fluid properties \n")
        FreeCAD.ActiveDocument.openTransaction("Set CfdFluidMaterialProperty")

        isPresent = False
        members = FemGui.getActiveAnalysis().Member
        for i in members:
            # Check for existing fluid material entity as the solver currently only support single region analysis.
            if "FluidProperties" in i.Name:
                FreeCADGui.doCommand("Gui.activeDocument().setEdit('"+i.Name+"')")
                isPresent = True

        # Allow to re-create if deleted
        if not isPresent:
            FreeCADGui.addModule("CfdFluidMaterial")
            FreeCADGui.doCommand(
                "analysis.Member = analysis.Member + [CfdFluidMaterial.makeCfdFluidMaterial('FluidProperties')]")
            FreeCADGui.doCommand("Gui.activeDocument().setEdit(App.ActiveDocument.ActiveObject.Name)")

if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Cfd_FluidMaterial', setCfdFluidPropertyCommand())