# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2016 - Bernd Hahnebach <bernd@bimstatik.org>            *
# *   Copyright (c) 2017 - Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>        *
# *   Copyright (c) 2017 - Alfred Bogaers (CSIR) <abogaers@csir.co.za>      *
# *   Copyright (c) 2017 - Johan Heyns (CSIR) <jheyns@csir.co.za>           *
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

__title__ = "Command to add CFD fluid boundary"
__author__ = ""
__url__ = "http://www.freecadweb.org"

## @package CommandCfdFluidBoundary
#  \ingroup CFD

import FreeCAD
from FemCommands import FemCommands
import FreeCADGui
from PySide import QtCore
import os
import FemGui
import CfdTools


class _CommandCfdFluidBoundary(FemCommands):
    """ The Fem_CfdFluidBoundary command definition """
    def __init__(self):
        super(_CommandCfdFluidBoundary, self).__init__()
        self.resources = self.GetResources()
        self.is_active = 'with_analysis'

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Create CfdFluidBoundary")
        FreeCADGui.addModule("FemGui")
        FreeCADGui.addModule("CfdFluidBoundary")
        FreeCADGui.doCommand("FemGui.getActiveAnalysis().Member = FemGui.getActiveAnalysis().Member + [CfdFluidBoundary.makeCfdFluidBoundary()]")

        FreeCADGui.doCommand("Gui.activeDocument().setEdit(App.ActiveDocument.ActiveObject.Name)")

    def GetResources(self):
        icon_path = os.path.join(CfdTools.get_module_path(), "Gui", "Resources", "icons", "boundary.png")
        return {
            'Pixmap': icon_path,
            'MenuText': QtCore.QT_TRANSLATE_NOOP("Cfd_FluidBoundary", "Fluid boundary"),
            'Accel': "C, W",
            'ToolTip': QtCore.QT_TRANSLATE_NOOP("Cfd_FluidBoundary", "Creates a CFD fluid boundary")}


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Cfd_FluidBoundary', _CommandCfdFluidBoundary())
