# **************************************************************************
# *  (c) bernd hahnebach (bernd@bimstatik.org) 2014                        *
# *  (c) qingfeng xia @ iesensor.com 2016                                  *
# *  Copyright (c) 2017 Andrew Gill (CSIR) <agill@csir.co.za>              *
# *  Copyright (c) 2019 Oliver Oxtoby <oliveroxtoby@gmail.com>             *
# *                                                                        *
# *  this file is part of the freecad cax development system.              *
# *                                                                        *
# *  this program is free software; you can redistribute it and/or modify  *
# *  it under the terms of the gnu lesser general public license (lgpl)    *
# *  as published by the free software foundation; either version 2 of     *
# *  the license, or (at your option) any later version.                   *
# *  for detail see the licence text file.                                 *
# *                                                                        *
# *  freecad is distributed in the hope that it will be useful,            *
# *  but without any warranty; without even the implied warranty of        *
# *  merchantability or fitness for a particular purpose.  see the         *
# *  gnu lesser general public license for more details.                   *
# *                                                                        *
# *  you should have received a copy of the gnu library general public     *
# *  license along with freecad; if not, write to the free software        *
# *  foundation, inc., 59 temple place, suite 330, boston, ma  02111-1307  *
# *  usa                                                                   *
# *                                                                        *
# **************************************************************************/


class CfdOFWorkbench(Workbench):
    """ CfdOF workbench object """
    def __init__(self):
        import os
        import CfdTools
        icon_path = os.path.join(CfdTools.get_module_path(), "Gui", "Resources", "icons", "cfd.svg")
        self.__class__.Icon = icon_path
        self.__class__.MenuText = "CfdOF"
        self.__class__.ToolTip = "CfdOF workbench"

        from PySide import QtCore
        from CfdPreferencePage import CfdPreferencePage
        ICONS_PATH = os.path.join(CfdTools.get_module_path(), "Gui", "Resources", "icons")
        QtCore.QDir.addSearchPath("icons", ICONS_PATH)
        FreeCADGui.addPreferencePage(CfdPreferencePage, "CfdOF")

    def Initialize(self):
        # must import QtCore in this function,
        # not at the beginning of this file for translation support
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

        FreeCADGui.addCommand('Cfd_Analysis', _CommandCfdAnalysis())
        FreeCADGui.addCommand('Cfd_MeshFromShape', _CommandCfdMeshFromShape())
        FreeCADGui.addCommand('Cfd_MeshRegion', _CommandMeshRegion())

        cmdlst = ['Cfd_Analysis',
                  'Cfd_MeshFromShape', 'Cfd_MeshRegion',
                  'Cfd_PhysicsModel', 'Cfd_FluidMaterial',
                  'Cfd_InitialiseInternal',
                  'Cfd_FluidBoundary', 'Cfd_InitialisationZone', 'Cfd_PorousZone',
                  'Cfd_SolverControl']

        self.appendToolbar(str(QtCore.QT_TRANSLATE_NOOP("Cfd", "CfdOF")), cmdlst)
        self.appendMenu(str(QtCore.QT_TRANSLATE_NOOP("Cfd", "&CfdOF")), cmdlst)

        # enable QtCore translation here, todo

    def GetClassName(self):
        return "Gui::PythonWorkbench"

FreeCADGui.addWorkbench(CfdOFWorkbench())
