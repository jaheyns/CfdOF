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

__title__ = "Command New Analysis"
__author__ = "Juergen Riegel"
__url__ = "http://www.freecadweb.org"

import FreeCAD
from FemCommands import FemCommands
import CfdTools
import os

if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore


class _CommandCfdAnalysis(FemCommands):
    "the Cfd_Analysis command definition"
    def __init__(self):
        super(_CommandCfdAnalysis, self).__init__()
        icon_path = os.path.join(CfdTools.get_module_path(),"Gui","Resources","icons","cfd_analysis.png")
        self.resources = {'Pixmap': icon_path,
                          'MenuText': QtCore.QT_TRANSLATE_NOOP("Cfd_Analysis", "Analysis container"),
                          'Accel': "N, C",
                          'ToolTip': QtCore.QT_TRANSLATE_NOOP("Cfd_Analysis", "Creates a analysis container with a Cfd solver")}
        self.is_active = 'with_document'

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Create CFD Analysis")
        FreeCADGui.addModule("FemGui")
        FreeCADGui.addModule("CfdAnalysis")
        FreeCADGui.doCommand("CfdAnalysis.makeCfdAnalysis('CfdAnalysis')")
        FreeCADGui.doCommand("FemGui.setActiveAnalysis(App.activeDocument().ActiveObject)")

        ''' Objects ordered according to expected workflow '''

        # Add physics object when CfdAnalysis container is created
        FreeCADGui.addModule("CfdPhysicsSelection")
        FreeCADGui.doCommand("FemGui.getActiveAnalysis().Member = FemGui.getActiveAnalysis().Member + [CfdPhysicsSelection.makeCfdPhysicsSelection()]")

        # Add fluid properties object when CfdAnalysis container is created
        FreeCADGui.addModule("CfdFluidMaterial")
        FreeCADGui.doCommand("FemGui.getActiveAnalysis().Member = FemGui.getActiveAnalysis().Member + [CfdFluidMaterial.makeCfdFluidMaterial('FluidProperties')]")

        # Add initialisation object when CfdAnalysis container is created
        FreeCADGui.addModule("CfdInitialiseFlowField")
        FreeCADGui.doCommand("FemGui.getActiveAnalysis().Member = FemGui.getActiveAnalysis().Member + [CfdInitialiseFlowField.makeCfdInitialFlowField()]")

        # Add solver object when CfdAnalysis container is created
        FreeCADGui.addModule("CfdSolverFoam")
        FreeCADGui.doCommand("FemGui.getActiveAnalysis().Member = FemGui.getActiveAnalysis().Member + [CfdSolverFoam.makeCfdSolverFoam()]")

        sel = FreeCADGui.Selection.getSelection()
        if (len(sel) == 1):
            if(sel[0].isDerivedFrom("Fem::FemMeshObject")):
                FreeCADGui.doCommand("FemGui.getActiveAnalysis().Member = FemGui.getActiveAnalysis().Member + [App.activeDocument()." + sel[0].Name + "]")
        FreeCADGui.Selection.clearSelection()

if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Cfd_Analysis', _CommandCfdAnalysis())
