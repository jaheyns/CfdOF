# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2016 - Qingfeng Xia <qingfeng.xia iesensor.com>         *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************

"""
python-vtk6, which is built with Qt5, does not work with FreeCAD with Qt4

Adapted from ccxFrdReader.py (Calculix result file *.frd reader)
However, readResult() return: list of {'Time': time_step, "Mesh": mesh_data, "Result": result_set}
Python object  Fem::FemResultObjectPython consists of property to hold result data 
like Temperature, NodeNumbers, Time, Mesh, also CFD specific fields:
Pressure (StressValues), Velocity(DisplacementVectors), etc

    /// Von Mises Stress values of analysis
    App::PropertyFloatList StressValues;
    
    FemPipelineObject,  load() all XML vtk files are supported,
"""

__title__ = "FreeCAD Cfd OpenFOAM library"
__author__ = "Juergen Riegel, Michael Hindley, Bernd Hahnebach, Qingfeng Xia"
__url__ = "http://www.freecadweb.org"


import os
from math import pow, sqrt
import numpy as np

import FreeCAD

if open.__module__ == '__builtin__':
    pyopen = open  # because we'll redefine open below

def insert(filename, docname):
    "called when freecad wants to import a file"
    try:
        doc = FreeCAD.getDocument(docname)
    except NameError:
        doc = FreeCAD.newDocument(docname)
    FreeCAD.ActiveDocument = doc

    importCfdResult(filename)


def open(filename):
    "called when freecad opens a file"
    docname = os.path.splitext(os.path.basename(filename))[0]
    insert(filename, docname)


def importCfdResult(filename, analysis=None, result_name_prefix=None):
    from CfdResult import makeCfdResult
    if not result_name_prefix: result_name_prefix = "CfdResult"
    result_obj = makeCfdResult(result_name_prefix)
    import Fem
    Fem.readCfdResult(filename, result_obj.Name) #always create a new femmesh

    ts = filename.split('_')[-1]
    try:
        time_step = float(ts[:-4])
    except:
        time_step = 0.0
    #Stats has been setup in C++ function Fem.readCfdResult

    if(FreeCAD.GuiUp) and analysis:
        import FemGui
        FemGui.setActiveAnalysis(analysis)
        
