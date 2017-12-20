# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2017 - Alfred Bogaers (CSIR) <abogaers@csir.co.za>      *
# *   Copyright (c) 2017 - Johan Heyns (CSIR) <jheyns@csir.co.za>           *
# *   Copyright (c) 2017 - Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>        *
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

__title__ = "Command to generate an initialisation zone"
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


class _CommandCfdInitialisationZone(CommandManager):
    """ The Cfd initialisation zone command definition """
    def __init__(self):
        super(_CommandCfdInitialisationZone, self).__init__()
        icon_path = os.path.join(CfdTools.get_module_path(), "Gui", "Resources", "icons", "alpha.png")
        self.resources = {'Pixmap': icon_path,
                          'MenuText': QtCore.QT_TRANSLATE_NOOP("Cfd_InitialisationZone", "Initialisation zone"),
                          'Accel': "",
                          'ToolTip': QtCore.QT_TRANSLATE_NOOP("Cfd_InitialisationZone",
                                                              "Select and create an initialisation zone")}
        self.is_active = 'with_analysis'

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Select and create an initialisation zone")

        FreeCADGui.addModule("FemGui")
        FreeCADGui.addModule("CfdZone")
        FreeCADGui.doCommand(
            "FemGui.getActiveAnalysis().addObject(CfdZone.makeCfdInitialisationZone())")
        FreeCADGui.ActiveDocument.setEdit(FreeCAD.ActiveDocument.ActiveObject.Name)


FreeCADGui.addCommand('Cfd_InitialisationZone', _CommandCfdInitialisationZone())
