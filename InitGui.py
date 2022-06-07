# ***************************************************************************
# *   (c) bernd hahnebach (bernd@bimstatik.org) 2014                        *
# *   (c) qingfeng xia @ iesensor.com 2016                                  *
# *   Copyright (c) 2017 Andrew Gill (CSIR) <agill@csir.co.za>              *
# *   Copyright (c) 2019-2021 Oliver Oxtoby <oliveroxtoby@gmail.com>        *
# *   Copyright (c) 2022 Jonathan Bergh <bergh.jonathan@gmail.com>          *
# *                                                                         *
# *   This program is free software: you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License as        *
# *   published by the Free Software Foundation, either version 3 of the    *
# *   License, or (at your option) any later version.                       *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Lesser General Public License for more details.                   *
# *                                                                         *
# *   You should have received a copy of the GNU Lesser General Public      *
# *   License along with this program.  If not,                             *
# *   see <https://www.gnu.org/licenses/>.                                  *
# *                                                                         *
# **************************************************************************/

import sys
from PySide import QtCore


class CfdOFWorkbench(Workbench):
    """ CfdOF workbench object """
    def __init__(self):
        import os
        from CfdOF import CfdTools
        from PySide import QtCore
        from CfdOF.CfdPreferencePage import CfdPreferencePage

        icon_path = os.path.join(CfdTools.getModulePath(), "Gui", "Icons", "cfd.svg")
        self.__class__.Icon = icon_path
        self.__class__.MenuText = "CfdOF"
        self.__class__.ToolTip = "CfdOF workbench"

        icons_path = os.path.join(CfdTools.getModulePath(), "Gui", "Icons")
        QtCore.QDir.addSearchPath("icons", icons_path)
        FreeCADGui.addPreferencePage(CfdPreferencePage, "CfdOF")

    def Initialize(self):
        # Must import QtCore in this function, not at the beginning of this file for translation support
        from PySide import QtCore

        from CfdOF.CfdAnalysis import _CommandCfdAnalysis
        from CfdOF.Mesh.CfdMesh import _CommandCfdMeshFromShape
        from CfdOF.Mesh.CfdMeshRefinement import _CommandMeshRegion
        from CfdOF.Solve.CfdPhysicsSelection import _CommandCfdPhysicsSelection
        from CfdOF.Solve.CfdFluidMaterial import _CommandCfdFluidMaterial
        from CfdOF.Solve.CfdSolverFoam import _CommandCfdSolverFoam
        from CfdOF.Solve.CfdInitialiseFlowField import _CommandCfdInitialiseInternalFlowField
        from CfdOF.Solve.CfdFluidBoundary import _CommandCfdFluidBoundary
        from CfdOF.Solve.CfdZone import _CommandCfdPorousZone
        from CfdOF.Solve.CfdZone import _CommandCfdInitialisationZone
        from CfdOF.Mesh.CfdDynamicMeshRefinement import _CommandDynamicMeshRefinement
        from CfdOF.PostProcess.CfdReportingFunctions import _CommandCfdReportingFunctions
        from CfdOF.Solve.CfdScalarTransportFunction import CommandCfdScalarTransportFunction

        FreeCADGui.addCommand('Cfd_Analysis', _CommandCfdAnalysis())
        FreeCADGui.addCommand('Cfd_MeshFromShape', _CommandCfdMeshFromShape())
        FreeCADGui.addCommand('Cfd_MeshRegion', _CommandMeshRegion())
        FreeCADGui.addCommand('Cfd_DynamicMeshRefinement', _CommandDynamicMeshRefinement())
        FreeCADGui.addCommand('Cfd_ReportingFunctions', _CommandCfdReportingFunctions())
        FreeCADGui.addCommand('Cfd_ScalarTransportFunctions', CommandCfdScalarTransportFunction())

        cmdlst = ['Cfd_Analysis',
                  'Cfd_MeshFromShape', 'Cfd_MeshRegion', 'Cfd_DynamicMeshRefinement',
                  'Cfd_PhysicsModel', 'Cfd_FluidMaterial',
                  'Cfd_FluidBoundary', 'Cfd_InitialiseInternal',
                  'Cfd_InitialisationZone', 'Cfd_PorousZone',
                  'Cfd_ReportingFunctions', 'Cfd_ScalarTransportFunctions',
                  'Cfd_SolverControl']

        self.appendMenu(str(QtCore.QT_TRANSLATE_NOOP("Cfd", "&CfdOF")), cmdlst)

        cmdlst.remove('Cfd_DynamicMeshRefinement')
        self.appendToolbar(str(QtCore.QT_TRANSLATE_NOOP("Cfd", "CfdOF")), cmdlst)

        # TODO enable QtCore translation here

    def GetClassName(self):
        return "Gui::PythonWorkbench"

import CfdOF
FreeCADGui.addWorkbench(CfdOFWorkbench())
FreeCAD.__unit_test__ += ["TestCfdOF"]

# Create backward compatible aliases for loading from file when modules have moved
from CfdOF import CfdAnalysis
sys.modules['CfdAnalysis'] = CfdOF.CfdAnalysis
from CfdOF.Solve import CfdPhysicsSelection
sys.modules['CfdPhysicsSelection'] = CfdPhysicsSelection
from CfdOF.Solve import CfdFluidMaterial
sys.modules['CfdFluidMaterial'] = CfdFluidMaterial
from CfdOF.Solve import CfdInitialiseFlowField
sys.modules['CfdInitialiseFlowField'] = CfdInitialiseFlowField
from CfdOF.Mesh import CfdMesh
sys.modules['CfdMesh'] = CfdMesh
from CfdOF.Mesh import CfdMeshRefinement
sys.modules['CfdMeshRefinement'] = CfdMeshRefinement
from CfdOF.Solve import CfdFluidBoundary
sys.modules['CfdFluidBoundary'] = CfdFluidBoundary
from CfdOF.Solve import CfdZone
sys.modules['CfdZone'] = CfdZone
from CfdOF.Solve import CfdSolverFoam
sys.modules['CfdSolverFoam'] = CfdSolverFoam
from CfdOF.PostProcess import CfdReportingFunctions
sys.modules['core.functionobjects.reporting.CfdReportingFunctions'] = CfdReportingFunctions
from CfdOF.Solve import CfdScalarTransportFunction
sys.modules['core.functionobjects.scalartransport.CfdScalarTransportFunction'] = CfdScalarTransportFunction
from CfdOF.Mesh import CfdDynamicMeshRefinement
sys.modules['core.mesh.dynamic.CfdDynamicMeshRefinement'] = CfdDynamicMeshRefinement
sys.modules['core'] = CfdOF
