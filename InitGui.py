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


class CfdOFWorkbench(Workbench):
    """ CfdOF workbench object """
    def __init__(self):
        import os
        from CfdOF import CfdTools
        from PySide import QtCore
        from CfdOF.CfdPreferencePage import CfdPreferencePage
        from CfdOF.CfdRemotePreferencePage import CfdRemotePreferencePage

        icon_path = os.path.join(CfdTools.getModulePath(), "Gui", "Icons", "cfd.svg")
        self.__class__.Icon = icon_path
        self.__class__.MenuText = "CfdOF"
        self.__class__.ToolTip = "CfdOF workbench"

        icons_path = os.path.join(CfdTools.getModulePath(), "Gui", "Icons")
        QtCore.QDir.addSearchPath("icons", icons_path)
        FreeCADGui.addPreferencePage(CfdPreferencePage, "CfdOF")
        FreeCADGui.addPreferencePage(CfdRemotePreferencePage, "CfdOF")

    def Initialize(self):
        # Must import QtCore in this function, not at the beginning of this file for translation support
        from PySide import QtCore

        from CfdOF.CfdAnalysis import CommandCfdAnalysis
        from CfdOF.Mesh.CfdMesh import CommandCfdMeshFromShape
        from CfdOF.Mesh.CfdMeshRefinement import CommandMeshRegion
        from CfdOF.Solve.CfdPhysicsSelection import CommandCfdPhysicsSelection
        from CfdOF.Solve.CfdFluidMaterial import CommandCfdFluidMaterial
        from CfdOF.Solve.CfdSolverFoam import CommandCfdSolverFoam
        from CfdOF.Solve.CfdInitialiseFlowField import CommandCfdInitialiseInternalFlowField
        from CfdOF.Solve.CfdFluidBoundary import CommandCfdFluidBoundary
        from CfdOF.Solve.CfdZone import CommandCfdPorousZone
        from CfdOF.Solve.CfdZone import CommandCfdInitialisationZone
        from CfdOF.Mesh.CfdDynamicMeshRefinement import CommandGroupDynamicMeshRefinement, \
            CommandDynamicMeshInterfaceRefinement, CommandDynamicMeshShockRefinement
        from CfdOF.PostProcess.CfdReportingFunction import CommandCfdReportingFunction
        from CfdOF.Solve.CfdScalarTransportFunction import CommandCfdScalarTransportFunction

        FreeCADGui.addCommand('Cfd_Analysis', CommandCfdAnalysis())
        FreeCADGui.addCommand('Cfd_MeshFromShape', CommandCfdMeshFromShape())
        FreeCADGui.addCommand('Cfd_MeshRegion', CommandMeshRegion())
        FreeCADGui.addCommand('Cfd_DynamicMeshInterfaceRefinement', CommandDynamicMeshInterfaceRefinement())
        FreeCADGui.addCommand('Cfd_DynamicMeshShockRefinement', CommandDynamicMeshShockRefinement())
        FreeCADGui.addCommand('Cfd_GroupDynamicMeshRefinement', CommandGroupDynamicMeshRefinement())
        FreeCADGui.addCommand('Cfd_PhysicsModel', CommandCfdPhysicsSelection())
        FreeCADGui.addCommand('Cfd_FluidMaterial', CommandCfdFluidMaterial())
        FreeCADGui.addCommand('Cfd_FluidBoundary', CommandCfdFluidBoundary())
        FreeCADGui.addCommand('Cfd_InitialiseInternal', CommandCfdInitialiseInternalFlowField())
        FreeCADGui.addCommand('Cfd_PorousZone', CommandCfdPorousZone())
        FreeCADGui.addCommand('Cfd_InitialisationZone', CommandCfdInitialisationZone())
        FreeCADGui.addCommand('Cfd_SolverControl', CommandCfdSolverFoam())
        FreeCADGui.addCommand('Cfd_ReportingFunctions', CommandCfdReportingFunction())
        FreeCADGui.addCommand('Cfd_ScalarTransportFunctions', CommandCfdScalarTransportFunction())

        cmdlst = ['Cfd_Analysis',
                  'Cfd_MeshFromShape', 'Cfd_MeshRegion', 
                  ("Dynamic mesh refinement", ['Cfd_DynamicMeshInterfaceRefinement','Cfd_DynamicMeshShockRefinement',]),
                  ('Cfd_GroupDynamicMeshRefinement',),
                  'Cfd_PhysicsModel', 'Cfd_FluidMaterial',
                  'Cfd_FluidBoundary', 'Cfd_InitialiseInternal',
                  'Cfd_InitialisationZone', 'Cfd_PorousZone',
                  'Cfd_ReportingFunctions', 'Cfd_ScalarTransportFunctions',
                  'Cfd_SolverControl']

        for cmd in cmdlst:
            if isinstance(cmd, tuple):
                if len(cmd) == 1:
                    self.appendToolbar(str(QtCore.QT_TRANSLATE_NOOP("Cfd", "CfdOF")), [cmd[0]])
                else:
                    self.appendMenu([str(QtCore.QT_TRANSLATE_NOOP("Cfd", "&CfdOF")), cmd[0]], cmd[1])
            else:
                self.appendMenu(str(QtCore.QT_TRANSLATE_NOOP("Cfd", "&CfdOF")), [cmd])
                self.appendToolbar(str(QtCore.QT_TRANSLATE_NOOP("Cfd", "CfdOF")), [cmd])

        from CfdOF import CfdTools
        prefs = CfdTools.getPreferencesLocation()
        CfdTools.DockerContainer.usedocker = FreeCAD.ParamGet(prefs).GetBool("UseDocker", 0)    

        # TODO enable QtCore translation here

    def GetClassName(self):
        return "Gui::PythonWorkbench"

    def __del__(sef):
        from CfdOF import CfdTools
        if CfdTools.DockerContainer.container_id != None:
            CfdTools.docker_container.stop_container()

import CfdOF
FreeCADGui.addWorkbench(CfdOFWorkbench())
FreeCAD.__unit_test__ += ["TestCfdOF"]

# Create backward compatible aliases for loading from file when modules have moved
from CfdOF import CfdAnalysis
sys.modules['CfdAnalysis'] = CfdAnalysis
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
from CfdOF.PostProcess import CfdReportingFunction
sys.modules['core.functionobjects.reporting.CfdReportingFunctions'] = CfdReportingFunction
sys.modules['CfdOF.PostProcess.CfdReportingFunctions'] = CfdReportingFunction
from CfdOF.Solve import CfdScalarTransportFunction
sys.modules['core.functionobjects.scalartransport.CfdScalarTransportFunction'] = CfdScalarTransportFunction
from CfdOF.Mesh import CfdDynamicMeshRefinement
sys.modules['core.mesh.dynamic.CfdDynamicMeshRefinement'] = CfdDynamicMeshRefinement
sys.modules['core'] = CfdOF
