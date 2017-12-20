# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2013-2015 - Juergen Riegel <FreeCAD@juergen-riegel.net> *
# *   Copyright (c) 2017 - Johan Heyns <jheyns@csir.co.za>                  *
# *   Copyright (c) 2017 - Oliver Oxtoby <ooxtoby@csir.co.za>               *
# *   Copyright (c) 2017 - Alfred Bogaers <abogaers@csir.co.za>             *
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

__title__ = "Command New Analysis"
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
    from PySide import QtCore


class _CommandCfdAnalysis(CommandManager):
    """ The Cfd_Analysis command definition """
    def __init__(self):
        super(_CommandCfdAnalysis, self).__init__()
        icon_path = os.path.join(CfdTools.get_module_path(), "Gui", "Resources", "icons", "cfd_analysis.png")
        self.resources = \
            {'Pixmap': icon_path,
             'MenuText': QtCore.QT_TRANSLATE_NOOP("Cfd_Analysis", "Analysis container"),
             'Accel': "N, C",
             'ToolTip': QtCore.QT_TRANSLATE_NOOP("Cfd_Analysis", "Creates an analysis container with a CFD solver")}
        self.is_active = 'with_document'

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Create CFD Analysis")
        FreeCADGui.addModule("FemGui")
        FreeCADGui.addModule("CfdAnalysis")
        FreeCADGui.doCommand("analysis = CfdAnalysis.makeCfdAnalysis('CfdAnalysis')")
        FreeCADGui.doCommand("FemGui.setActiveAnalysis(analysis)")

        ''' Objects ordered according to expected workflow '''

        # Add physics object when CfdAnalysis container is created
        FreeCADGui.addModule("CfdPhysicsSelection")
        FreeCADGui.doCommand("analysis.addObject(CfdPhysicsSelection.makeCfdPhysicsSelection())")

        # Add fluid properties object when CfdAnalysis container is created
        FreeCADGui.addModule("CfdFluidMaterial")
        FreeCADGui.doCommand("analysis.addObject(CfdFluidMaterial.makeCfdFluidMaterial('FluidProperties'))")

        # Add initialisation object when CfdAnalysis container is created
        FreeCADGui.addModule("CfdInitialiseFlowField")
        FreeCADGui.doCommand("analysis.addObject(CfdInitialiseFlowField.makeCfdInitialFlowField())")

        # Add solver object when CfdAnalysis container is created
        FreeCADGui.addModule("CfdSolverFoam")
        FreeCADGui.doCommand("analysis.addObject(CfdSolverFoam.makeCfdSolverFoam())")

        sel = FreeCADGui.Selection.getSelection()
        if len(sel) == 1:
            if sel[0].isDerivedFrom("Fem::FemMeshObject"):
                FreeCADGui.doCommand("analysis.addObject(App.activeDocument()." + sel[0].Name + ")")
        FreeCADGui.Selection.clearSelection()

if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Cfd_Analysis', _CommandCfdAnalysis())
