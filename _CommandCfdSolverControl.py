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

__title__ = "Command Control Solver"
__author__ = "Juergen Riegel"
__url__ = "http://www.freecadweb.org"

import FreeCAD
import platform
try:
    from femcommands.manager import CommandManager
except ImportError:  # Backward compatibility
    from PyGui.FemCommands import FemCommands as CommandManager
import CfdTools
import os

if FreeCAD.GuiUp:
    import FreeCADGui
    import FemGui
    from PySide import QtCore


class _CommandCfdSolverControl(CommandManager):
    "the Cfd_SolverControl command definition"
    def __init__(self):
        super(_CommandCfdSolverControl, self).__init__()
        icon_path = os.path.join(CfdTools.get_module_path(),"Gui","Resources","icons","solver.png")
        self.resources = {'Pixmap': icon_path,
                          'MenuText': QtCore.QT_TRANSLATE_NOOP("Cfd_SolverControl", "Solver job control"),
                          'Accel': "S, C",
                          'ToolTip': QtCore.QT_TRANSLATE_NOOP("Cfd_SolverControl", "Edit properties and run solver")}
        # self.is_active = 'with_solver'
        self.is_active = 'with_analysis'

    def Activated(self):

        CfdTools.hide_parts_show_meshes()

        isPresent = False
        members = FemGui.getActiveAnalysis().Group
        for i in members:
            if "OpenFOAM" in i.Name:
                FreeCADGui.doCommand("Gui.activeDocument().setEdit('"+i.Name+"')")
                isPresent = True

        # Allowing user to re-creation if CFDSolver was deleted.
        if not isPresent:
            FreeCADGui.addModule("FemGui")
            FreeCADGui.addModule("CfdSolverFoam")
            FreeCADGui.doCommand("FemGui.getActiveAnalysis().addObject(CfdSolverFoam.makeCfdSolverFoam())")
            FreeCADGui.doCommand("Gui.activeDocument().setEdit(App.ActiveDocument.ActiveObject.Name)")


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Cfd_SolverControl', _CommandCfdSolverControl())
