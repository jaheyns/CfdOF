# ***************************************************************************
# *   (c) bernd hahnebach (bernd@bimstatik.org) 2014                        *
# *   (c) qingfeng xia @ iesensor.com 2016                                  *
# *   Copyright (c) 2017 Andrew Gill (CSIR) <agill@csir.co.za>              *
# *   Copyright (c) 2019-2024 Oliver Oxtoby <oliveroxtoby@gmail.com>        *
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
    """CfdOF workbench object"""

    def __init__(self):
        import os
        from CfdOF import CfdTools
        from PySide import QtCore
        from CfdOF.CfdPreferencePage import CfdPreferencePage

        translate = FreeCAD.Qt.translate
        translations_path = os.path.join(CfdTools.getModulePath(), "Translations")
        FreeCADGui.addLanguagePath(translations_path)
        FreeCADGui.updateLocale()

        icon_path = os.path.join(CfdTools.getModulePath(), "Gui", "Icons", "cfd.svg")
        self.__class__.Icon = icon_path
        self.__class__.MenuText = translate("Workbench", "CfdOF")
        self.__class__.ToolTip = translate("Workbench", "CfdOF workbench")

        icons_path = os.path.join(CfdTools.getModulePath(), "Gui", "Icons")
        QtCore.QDir.addSearchPath("icons", icons_path)
        FreeCADGui.addPreferencePage(CfdPreferencePage, "CfdOF")

    def Initialize(self):
        from PySide.QtCore import QT_TRANSLATE_NOOP

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
        from CfdOF.CfdOpenPreferencesPage import CommandCfdOpenPreferencesPage
        from CfdOF.CfdReloadWorkbench import CommandCfdReloadWorkbench
        from CfdOF.CfdTestCommands import CommandCfdRunTests, CommandCfdUpdateTestData, CommandCfdCleanTests

        FreeCADGui.addCommand('CfdOF_Analysis', CommandCfdAnalysis())
        FreeCADGui.addCommand('CfdOF_MeshFromShape', CommandCfdMeshFromShape())
        FreeCADGui.addCommand('CfdOF_MeshRegion', CommandMeshRegion())
        FreeCADGui.addCommand('CfdOF_DynamicMeshInterfaceRefinement', CommandDynamicMeshInterfaceRefinement())
        FreeCADGui.addCommand('CfdOF_DynamicMeshShockRefinement', CommandDynamicMeshShockRefinement())
        FreeCADGui.addCommand('CfdOF_GroupDynamicMeshRefinement', CommandGroupDynamicMeshRefinement())
        FreeCADGui.addCommand('CfdOF_PhysicsModel', CommandCfdPhysicsSelection())
        FreeCADGui.addCommand('CfdOF_FluidMaterial', CommandCfdFluidMaterial())
        FreeCADGui.addCommand('CfdOF_FluidBoundary', CommandCfdFluidBoundary())
        FreeCADGui.addCommand('CfdOF_InitialiseInternal', CommandCfdInitialiseInternalFlowField())
        FreeCADGui.addCommand('CfdOF_PorousZone', CommandCfdPorousZone())
        FreeCADGui.addCommand('CfdOF_InitialisationZone', CommandCfdInitialisationZone())
        FreeCADGui.addCommand('CfdOF_SolverControl', CommandCfdSolverFoam())
        FreeCADGui.addCommand('CfdOF_ReportingFunctions', CommandCfdReportingFunction())
        FreeCADGui.addCommand('CfdOF_ScalarTransportFunctions', CommandCfdScalarTransportFunction())
        FreeCADGui.addCommand('CfdOF_OpenPreferences', CommandCfdOpenPreferencesPage())
        FreeCADGui.addCommand('CfdOF_ReloadWorkbench', CommandCfdReloadWorkbench())
        FreeCADGui.addCommand('CfdOF_RunTests', CommandCfdRunTests())
        FreeCADGui.addCommand('CfdOF_UpdateTestData', CommandCfdUpdateTestData())
        FreeCADGui.addCommand('CfdOF_CleanTests', CommandCfdCleanTests())

        # Commands for both menu and toolbar, or one or the other if a tuple
        # starting with 'M' or 'T'
        cmdlst = ['CfdOF_Analysis',
                  'CfdOF_MeshFromShape', 'CfdOF_MeshRegion',
                  ('M', QT_TRANSLATE_NOOP("Workbench", "Dynamic mesh refinement"),
                   ['CfdOF_DynamicMeshInterfaceRefinement','CfdOF_DynamicMeshShockRefinement',]),
                  ('T', 'CfdOF_GroupDynamicMeshRefinement',),
                  'CfdOF_PhysicsModel', 'CfdOF_FluidMaterial',
                  'CfdOF_FluidBoundary', 'CfdOF_InitialiseInternal',
                  'CfdOF_InitialisationZone', 'CfdOF_PorousZone',
                  'CfdOF_ReportingFunctions', 'CfdOF_ScalarTransportFunctions',
                  'CfdOF_SolverControl',
                  ('M', 'CfdOF_OpenPreferences',),
                  ('M', QT_TRANSLATE_NOOP("Workbench", "Development"),
                   ['CfdOF_ReloadWorkbench', 'CfdOF_RunTests', 'CfdOF_UpdateTestData', 'CfdOF_CleanTests']),
                  ]

        for cmd in cmdlst:
            if isinstance(cmd, tuple):
                if cmd[0] == 'T':
                    self.appendToolbar(QT_TRANSLATE_NOOP("Workbench", "CfdOF"), [cmd[1]])
                else:
                    if len(cmd) == 2:
                        self.appendMenu(QT_TRANSLATE_NOOP("Workbench", "&CfdOF"), [cmd[1]])
                    else:
                        self.appendMenu([QT_TRANSLATE_NOOP("Workbench", "&CfdOF"), cmd[1]], cmd[2])
            else:
                self.appendMenu(QT_TRANSLATE_NOOP("Workbench", "&CfdOF"), [cmd])
                self.appendToolbar(QT_TRANSLATE_NOOP("Workbench", "CfdOF"), [cmd])

        from CfdOF import CfdTools
        prefs = CfdTools.getPreferencesLocation()
        CfdTools.DockerContainer.usedocker = FreeCAD.ParamGet(prefs).GetBool("UseDocker", 0)

    def GetClassName(self):
        return "Gui::PythonWorkbench"

    def __del__(sef):
        from CfdOF import CfdTools
        if CfdTools.docker_container is not None:
            CfdTools.docker_container.clean_container()
            print("Container stopped.")

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
