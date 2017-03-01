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

__title__ = "Command to generate a porous zone"
__author__ = ""
__url__ = "http://www.freecadweb.org"

import FreeCAD
import platform
if platform.system() == 'Windows':
    from PyGui.FemCommands import FemCommands
else:
    from FemCommands import FemCommands
import FemGui
import CfdTools
import os

if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore


class _CommandCfdPorousZone(FemCommands):
    """ The Cfd porous zone command definition """
    def __init__(self):
        super(_CommandCfdPorousZone, self).__init__()
        icon_path = os.path.join(CfdTools.get_module_path(),"Gui","Resources","icons","porous.png")
        self.resources = {'Pixmap': icon_path,
                          'MenuText': QtCore.QT_TRANSLATE_NOOP("Cfd_PorousZone", "Porous zone"),
                          'Accel': "",
                          'ToolTip': QtCore.QT_TRANSLATE_NOOP("Cfd_PorousZone", "Select and create a porous zone")}
        self.is_active = 'with_analysis'

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Select and create a porous zone")

        FreeCADGui.addModule("FemGui")
        FreeCADGui.addModule("CfdPorousZone")
        FreeCADGui.doCommand("FemGui.getActiveAnalysis().Member = FemGui.getActiveAnalysis().Member + [CfdPorousZone.makeCfdPorousZone()]")
        FreeCADGui.doCommand("Gui.activeDocument().setEdit(App.ActiveDocument.ActiveObject.Name)")
        
if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Cfd_PorousZone', _CommandCfdPorousZone())
