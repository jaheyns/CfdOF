# **************************************************************************
# *  (c) bernd hahnebach (bernd@bimstatik.org) 2014                        *
# *  (c) qingfeng xia @ iesensor.com 2016                                  *
# *  Copyright (c) 2017 - Andrew Gill (CSIR) <agill@csir.co.za>            *
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


__title__ = "cfd analysis workbench"
__author__ = "qingfeng xia"
__url__ = "http://www.freecadweb.org"


class CfdFoamWorkbench(Workbench):
    """ cfdfoam workbench object """
    def __init__(self):
        import os
        import CfdTools
        icon_path = os.path.join(CfdTools.get_module_path(), "Gui", "Resources", "icons", "cfd.png")
        self.__class__.Icon = icon_path
        self.__class__.MenuText = "CFDFoam"
        self.__class__.ToolTip = "CFD workbench"

        from PySide import QtCore
        from CfdPreferencePage import CfdPreferencePage
        ICONS_PATH = os.path.join(CfdTools.get_module_path(), "Gui", "Resources", "icons")
        QtCore.QDir.addSearchPath("icons", ICONS_PATH)
        FreeCADGui.addPreferencePage(CfdPreferencePage, "CFD")

    def Initialize(self):
        # must import QtCore in this function,
        # not at the beginning of this file for translation support
        from PySide import QtCore
        import Fem
        import FemGui

        import _CommandCfdAnalysis
        import _CommandCfdSolverFoam
        import _CommandCfdSolverControl
        import _CommandCfdPhysicsSelection
        import _CommandCfdInitialiseInternalFlowField
        import _CommandCfdFluidBoundary
        import _CommandCfdPorousZone
        import _CommandCfdInitialisationZone
        import _CommandCfdFluidMaterial

        import _CommandCfdMeshGmshFromShape
        import _CommandCfdMeshRegion
        # import _CommandPrintMeshInfo  # Create a fluid specific check as the current does not contain any
        #                               # useful info for flow (see checkMesh)
        import _CommandCfdMeshCartFromShape


        cmdlst = ['Cfd_Analysis','Cfd_PhysicsModel', 'Cfd_FluidMaterial',
                  'Cfd_InitialiseInternal', 'Cfd_MeshGmshFromShape',
                  'Cfd_MeshCartFromShape', 'Fem_MeshRegion',
                  'Cfd_FluidBoundary', 'Cfd_InitialisationZone', 'Cfd_PorousZone',
                  'Cfd_SolverControl']

        self.appendToolbar(str(QtCore.QT_TRANSLATE_NOOP("Cfd", "CFDFoam")), cmdlst)
        self.appendMenu(str(QtCore.QT_TRANSLATE_NOOP("Cfd", "&CFDFoam")), cmdlst)

        # enable QtCore translation here, todo

    def GetClassName(self):
        return "Gui::PythonWorkbench"

FreeCADGui.addWorkbench(CfdFoamWorkbench())
