#***************************************************************************
#*   (c) Bernd Hahnebach (bernd@bimstatik.org) 2014                    *
#*   (c) Qingfeng Xia @ iesensor.com 2016                    *
#*                                                                         *
#*   This file is part of the FreeCAD CAx development system.              *
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   FreeCAD is distributed in the hope that it will be useful,            *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Lesser General Public License for more details.                   *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with FreeCAD; if not, write to the Free Software        *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************/

__title__ = "Cfd Analysis workbench"
__author__ = "Qingfeng Xia"
__url__ = "http://www.freecadweb.org"


class CfdWorkbench(Workbench):
    "CFD workbench object"
    def __init__(self):
        #self.__class__.Icon = FreeCAD.getResourceDir() + "Mod/Cfd/Resources/icons/CfdWorkbench.svg"
        self.__class__.Icon = FreeCAD.getResourceDir() + "Mod/Fem/Resources/icons/FemWorkbench.svg"
        self.__class__.MenuText = "CFD"
        self.__class__.ToolTip = "CFD workbench"

    def Initialize(self):
        from PySide import QtCore  # must import in this function, not at the beginning of this file for translation support
        import Fem
        import FemGui

        import _CommandCfdAnalysis
        import _CommandCfdSolverFoam
        import _CommandCfdSolverControl
        #import _CommandCfdResult  # error in import vtk6 in python, this function is implemented in File->Open Instead

        # classes developed in FemWorkbench
        import _CommandMeshGmshFromShape
        import _CommandMeshNetgenFromShape
        import _CommandMeshRegion
        import _CommandPrintMeshInfo
        import _CommandClearMesh
        import _CommandCfdFluidMaterial

        # Post Processing commands are located in FemWorkbench, implemented and imported in C++
        cmdlst = ['Cfd_Analysis', 'Fem_MeshNetgenFromShape', 'Fem_MeshGmshFromShape',
                        'Fem_MeshRegion', 'Fem_PrintMeshInfo', 'Fem_ClearMesh',
                        'Fem_ConstraintFluidBoundary', 'Cfd_SolverControl', 'Cfd_FluidMaterial', "Separator",
                        "Fem_PostPipelineFromResult", "Fem_PostCreateClipFilter", 
                        "Fem_PostCreateScalarClipFilter", "Fem_PostCreateCutFilter"]
        self.appendToolbar(str(QtCore.QT_TRANSLATE_NOOP("Cfd", "CFD")), cmdlst)
        self.appendMenu(str(QtCore.QT_TRANSLATE_NOOP("Cfd", "CFD")), cmdlst)

        # enable QtCore translation here, todo

    def GetClassName(self):
        return "Gui::PythonWorkbench"

FreeCADGui.addWorkbench(CfdWorkbench())
