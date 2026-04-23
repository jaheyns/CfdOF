# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: © 2014 Bernd Hahnebach <bernd@bimstatik.org>
# SPDX-FileCopyrightText: © 2016 Qingfeng Xia <iesensor.com>
# SPDX-FileCopyrightText: © 2017 Andrew Gill (CSIR) <agill@csir.co.za>
# SPDX-FileCopyrightText: © 2019 Oliver Oxtoby <oliveroxtoby@gmail.com>
# SPDX-FileCopyrightText: © 2022 Jonathan Bergh <bergh.jonathan@gmail.com>
# SPDX-FileNotice: Part of the CfdOF addon.

################################################################################
#                                                                              #
#   This program is free software; you can redistribute it and/or              #
#   modify it under the terms of the GNU Lesser General Public                 #
#   License as published by the Free Software Foundation; either               #
#   version 3 of the License, or (at your option) any later version.           #
#                                                                              #
#   This program is distributed in the hope that it will be useful,            #
#   but WITHOUT ANY WARRANTY; without even the implied warranty of             #
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.                       #
#                                                                              #
#   See the GNU Lesser General Public License for more details.                #
#                                                                              #
#   You should have received a copy of the GNU Lesser General Public License   #
#   along with this program; if not, write to the Free Software Foundation,    #
#   Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.        #
#                                                                              #
################################################################################

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

        # Register the commands
        import CfdOF.CfdAnalysis
        import CfdOF.Mesh.CfdMesh
        import CfdOF.Mesh.CfdMeshRefinement
        import CfdOF.Solve.CfdPhysicsSelection
        import CfdOF.Solve.CfdFluidMaterial
        import CfdOF.Solve.CfdSolverFoam
        import CfdOF.Solve.CfdInitialiseFlowField
        import CfdOF.Solve.CfdFluidBoundary
        import CfdOF.Solve.CfdZone
        import CfdOF.Mesh.CfdDynamicMeshRefinement
        import CfdOF.PostProcess.CfdReportingFunction
        import CfdOF.Solve.CfdScalarTransportFunction
        import CfdOF.Solve.CfdMeanVelocityForce
        import CfdOF.CfdOpenPreferencesPage
        import CfdOF.CfdReloadWorkbench
        import CfdOF.CfdTestCommands

        # Commands for both menu and toolbar, or one or the other if a tuple
        # starting with 'M' or 'T'
        cmdlst = ['CfdOF_Analysis',
                  'CfdOF_MeshFromShape', 'CfdOF_MeshRegion',
                  ('M', QT_TRANSLATE_NOOP("Workbench", "Dynamic mesh refinement"),
                   ['CfdOF_DynamicMeshInterfaceRefinement','CfdOF_DynamicMeshShockRefinement',]),
                  ('T', 'CfdOF_GroupDynamicMeshRefinement',),
                  'CfdOF_PhysicsModel', 'CfdOF_FluidMaterial',
                  'CfdOF_FluidBoundary', 'CfdOF_InitialiseInternal',
                  'CfdOF_InitialisationZone', 'CfdOF_PorousZone', 'CfdOF_MeanVelocityForce',
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
