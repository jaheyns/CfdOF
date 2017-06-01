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
        icon_path = os.path.join(CfdTools.get_module_path(), "Gui", "Resources",
            "icons", "cfd.png")
        self.__class__.Icon = icon_path
        self.__class__.MenuText = "CFDFoam"
        self.__class__.ToolTip = "CFD workbench"

    def Initialize(self):
        import CfdTools
        err_message = self.checkCfdDependencies()
        if err_message:
            CfdTools.cfdError(err_message)

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
        #import _CommandCfdResult  # error in import vtk6 in python, this function is implemented in File->Open Instead
        import _CommandCfdFluidMaterial

        # classes developed in FemWorkbench
        import _CommandCfdMeshGmshFromShape
        # import _CommandMeshNetgenFromShape  # CFD WB will only support GMSH
        import _CommandCfdMeshRegion
        # import _CommandPrintMeshInfo  # Create a fluid specific check as the current does not contain any
        #                               # useful info for flow (see checkMesh)
        # import _CommandClearMesh  # Not currently in-use
        import _CommandCfdMeshCartFromShape


        # Post Processing commands are located in FemWorkbench, implemented and imported in C++
        cmdlst = ['Cfd_Analysis','Cfd_PhysicsModel', 'Cfd_FluidMaterial',
                  'Cfd_InitialiseInternal', 'Cfd_MeshGmshFromShape',
                  'Cfd_MeshCartFromShape', 'Fem_MeshRegion',
                  'Cfd_FluidBoundary', 'Cfd_PorousZone','Cfd_SolverControl']

        self.appendToolbar(str(QtCore.QT_TRANSLATE_NOOP("Cfd", "CFDFoam")), cmdlst)
        self.appendMenu(str(QtCore.QT_TRANSLATE_NOOP("Cfd", "&CFDFoam")), cmdlst)

        # enable QtCore translation here, todo

    def GetClassName(self):
        return "Gui::PythonWorkbench"

    def checkCfdDependencies(self, term_print=True):
        import os
        import subprocess  # should this move?
        import platform

        message = ""
        if (term_print):
            print("checking cfd workbench dependencies:")

        # check for gnplot python module
        if (term_print):
            print(" checking for gnuplot:")
        try:
            import Gnuplot
        except:
            message += "gnuplot python module not installed\n"
            if (term_print):
                print("gnuplot python module not installed")

        # check openfoam
        if (term_print):
            print("checking for openfoam:")
        if platform.system() == 'Windows':
            foam_dir = None
            foam_ver = None
        else:
            cmdline = ['bash', '-l', '-c', 'echo $WM_PROJECT_DIR']
            # foam_dir = subprocess.check_output(cmdline, stderr=subprocess.pipe)
            foam_dir = subprocess.check_output(cmdline)
            cmdline = ['bash', '-l', '-c', 'echo $WM_PROJECT_VERSION']
            # foam_ver = subprocess.check_output(cmdline, stderr=subprocess.pipe)
            foam_ver = subprocess.check_output(cmdline)
        # python 3 compatible, check_output() return type byte
        foam_dir = str(foam_dir)
        if len(foam_dir) < 3:
            # if env var is not defined, python 3 returns `b'\n'` and python 2`\n`
            if (term_print):
                print("openfoam environment not pre-loaded before running freecad.\n\
                        Defaulting to openfoam path in workbench preferences...\n")

            # check that path to openfoam is set
            ofpath = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Cfd/OpenFOAM").GetString(
                "InstallationPath", "")
            if not ofpath:
                message += \
                    "openfoam installation path not set and openfoam environment not pre-loaded before running freecad.\n"
                if (term_print):
                    print("openfoam installation path not set")
                    # TODO: Check version of OpenFOAM at inst path
        else:
            foam_ver = str(foam_ver)
            if len(foam_ver) > 1:
                if foam_ver[:2] == "b'":
                    foam_ver = foam_ver[2:-3]  # python3: strip 'b' from front and eol char
                else:
                    foam_ver = foam_ver.strip()  # python2: strip eol char
            if (foam_ver.split('.')[0] < 4):
                message += "openfoam version " + foam_ver + " pre-loaded is outdated: " \
                           + "the cfd workbench requires at least openfoam 4.0\n"

                if (term_print):
                    print("openfoam version " + foam_ver
                          + "pre-loaded is outdated: the cfd workbench requires at least openfoam 4.0'")

        if (term_print):
            print(" checking for gmsh:")

        # check that gmsh version 2.13 or greater is installed
        gmshversion = ""
        try:
            gmshversion = subprocess.check_output(["gmsh", "-version"], stderr=subprocess.STDOUT)
        except:
            message += "gmsh is not installed\n"
            if (term_print):
                print(" gmsh is not installed")
        if (len(gmshversion) > 1):
            versionlist = gmshversion.split(".")
            if ((int(versionlist[0]) < 2) or ((int(versionlist[0]==2) and (int(versionlist[1])<13)):
                message += "gmesh version is older than minimum required (2.13)\n"
                if (term_print):
                    print("gmsh version is older than minimum required (2.13)")

        if (term_print):
            print(" completed cfd dependency check")
        return message


FreeCADGui.addWorkbench(CfdFoamWorkbench())
