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

from PySide import QtCore


class CfdOFWorkbench(Workbench):
    """ CfdOF workbench object """
    def __init__(self):
        import os
        import CfdTools
        from PySide import QtCore
        from CfdPreferencePage import CfdPreferencePage

        icon_path = os.path.join(CfdTools.get_module_path(), "Gui", "Resources", "icons", "cfd.svg")
        self.__class__.Icon = icon_path
        self.__class__.MenuText = "CfdOF"
        self.__class__.ToolTip = "CfdOF workbench"

        icons_path = os.path.join(CfdTools.get_module_path(), "Gui", "Resources", "icons")
        QtCore.QDir.addSearchPath("icons", icons_path)
        FreeCADGui.addPreferencePage(CfdPreferencePage, "CfdOF")

    def Initialize(self):
        # Must import QtCore in this function, not at the beginning of this file for translation support
        from PySide import QtCore

        from CfdAnalysis import _CommandCfdAnalysis
        from CfdMesh import _CommandCfdMeshFromShape
        from CfdMeshRefinement import _CommandMeshRegion
        from CfdPhysicsSelection import _CommandCfdPhysicsSelection
        from CfdFluidMaterial import _CommandCfdFluidMaterial
        from CfdSolverFoam import _CommandCfdSolverFoam
        from CfdInitialiseFlowField import _CommandCfdInitialiseInternalFlowField
        from CfdFluidBoundary import _CommandCfdFluidBoundary
        from CfdZone import _CommandCfdPorousZone
        from CfdZone import _CommandCfdInitialisationZone
        from core.mesh.dynamic.CfdDynamicMeshRefinement import _CommandDynamicMeshRefinement
        from core.functionobjects.reporting.CfdReportingFunctions import _CommandCfdReportingFunctions
        from core.functionobjects.scalartransport.CommandCfdScalarTransportFunctions \
            import CommandCfdScalarTransportFunction

        FreeCADGui.addCommand('Cfd_Analysis', _CommandCfdAnalysis())
        FreeCADGui.addCommand('Cfd_MeshFromShape', _CommandCfdMeshFromShape())
        FreeCADGui.addCommand('Cfd_MeshRegion', _CommandMeshRegion())
        FreeCADGui.addCommand('Cfd_DynamicMeshRefinement', _CommandDynamicMeshRefinement())
        FreeCADGui.addCommand('Cfd_ReportingFunctions', _CommandCfdReportingFunctions())
        FreeCADGui.addCommand('Cfd_ScalarTransportFunctions', CommandCfdScalarTransportFunction())

        cmdlst = ['Cfd_Analysis',
                  'Cfd_MeshFromShape', 'Cfd_MeshRegion', 'Cfd_DynamicMeshRefinement',
                  'Cfd_PhysicsModel', 'Cfd_FluidMaterial',
                  'Cfd_InitialiseInternal',
                  'Cfd_FluidBoundary', 'Cfd_InitialisationZone', 'Cfd_PorousZone',
                  'Cfd_ReportingFunctions', 'Cfd_ScalarTransportFunctions',
                  'Cfd_SolverControl']

        self.appendMenu(str(QtCore.QT_TRANSLATE_NOOP("Cfd", "&CfdOF")), cmdlst)

        cmdlst.remove('Cfd_DynamicMeshRefinement')
        self.appendToolbar(str(QtCore.QT_TRANSLATE_NOOP("Cfd", "CfdOF")), cmdlst)

        # TODO enable QtCore translation here

    def GetClassName(self):
        return "Gui::PythonWorkbench"

FreeCADGui.addWorkbench(CfdOFWorkbench())
FreeCAD.__unit_test__ += ["TestCfdOF"]
