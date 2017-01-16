#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2015 - Qingfeng Xia <qingfeng.xia()eng.ox.ac.uk> *
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   This program is distributed in the hope that it will be useful,       *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Library General Public License for more details.                  *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with this program; if not, write to the Free Software   *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************

__title__ = "Classes for New CFD solver"
__author__ = "Qingfeng Xia"
__url__ = "http://www.freecadweb.org"

import os.path

import FreeCAD
if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore, QtGui

import CfdSolver

def makeCfdSolverFoam(name="OpenFOAM"):
    obj = FreeCAD.ActiveDocument.addObject("Fem::FemSolverObjectPython", name)
    CfdSolverFoam(obj)
    if FreeCAD.GuiUp:
        from _ViewProviderCfdSolverFoam import _ViewProviderCfdSolverFoam
        _ViewProviderCfdSolverFoam(obj.ViewObject)
    return obj


class CfdSolverFoam(CfdSolver.CfdSolver):
    def __init__(self, obj):
        super(CfdSolverFoam, self).__init__(obj)
        self.Type = "CfdSolverFoam"
        if "PotentialInit" not in obj.PropertiesList:
            obj.addProperty("App::PropertyBool", "PotentialInit", "Solver",
                    "Initialise fields using potential flow solution", True)
