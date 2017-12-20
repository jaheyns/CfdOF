# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2013-2015 - Juergen Riegel <FreeCAD@juergen-riegel.net> *
# *   Copyright (c) 2017 - Alfred Bogaers <abogaers@csir.co.za>             *
# *   Copyright (c) 2017 - Johan Heyns <jheyns@csir.co.za>                  *
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

__title__ = "Command for internal field initialisation"
__author__ = ""
__url__ = "http://www.freecadweb.org"

import FreeCAD
import platform
try:
    from femcommands.manager import CommandManager
except ImportError:  # Backward compatibility
    from PyGui.FemCommands import FemCommands as CommandManager
import FemGui
import CfdTools
import os

if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore


class _CommandCfdInitialiseInternalFlowField(CommandManager):
    """ Field initialisation command """
    def __init__(self):
        super(_CommandCfdInitialiseInternalFlowField, self).__init__()
        icon_path = os.path.join(CfdTools.get_module_path(), "Gui", "Resources", "icons", "initialise.png")
        self.resources = {'Pixmap': icon_path,
                          'MenuText': QtCore.QT_TRANSLATE_NOOP("Cfd_InitialiseInternal", "Initialise"),
                          'Accel': "",
                          'ToolTip': QtCore.QT_TRANSLATE_NOOP(
                                "Cfd_InitialiseInternal",
                                "Initialise internal flow variables based on the selected physics model")}
        self.is_active = 'with_analysis'

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Initialise the internal flow variables")
        isPresent = False
        members = FemGui.getActiveAnalysis().Group
        for i in members:
            if "InitialiseFields" in i.Name:
                FreeCADGui.doCommand("Gui.activeDocument().setEdit('"+i.Name+"')")
                isPresent = True

        # Allow to re-create if deleted
        if not isPresent:
            FreeCADGui.addModule("CfdInitialiseFlowField")
            FreeCADGui.addModule("FemGui")
            FreeCADGui.doCommand(
                "analysis.addObject(CfdInitialiseFlowField.makeCfdInitialFlowField())")
            FreeCADGui.ActiveDocument.setEdit(FreeCAD.ActiveDocument.ActiveObject.Name)

if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Cfd_InitialiseInternal', _CommandCfdInitialiseInternalFlowField())
