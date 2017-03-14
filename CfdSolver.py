# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2015 - Qingfeng Xia <qingfeng.xia()eng.ox.ac.uk>        *
# *   Copyright (c) 2017 - Johan Heyns (CSIR) <jheyns@csir.co.za>           *
# *   Copyright (c) 2017 - Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>        *
# *   Copyright (c) 2017 - Alfred Bogaers (CSIR) <abogaers@csir.co.za>      *
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

__title__ = "Classes for New CFD solver"
__author__ = "Qingfeng Xia"
__url__ = "http://www.freecadweb.org"

import os.path

class CfdSolver(object):
    """ Solver specific properties. """
    def __init__(self, obj):
        self.Type = "CfdSolver"
        self.Object = obj  # keep a ref to the DocObj for nonGui usage
        obj.Proxy = self  # link between App::DocumentObject to  this object

        if "SolverName" not in obj.PropertiesList:
            obj.addProperty("App::PropertyString", "SolverName", "Solver",
                            "Name to identify the solver.", True)  # Currently not active
            obj.SolverName = "OpenFOAM"
            obj.addProperty("App::PropertyPath", "WorkingDir", "Solver",
                            "Directory where the case is saved.")
            obj.addProperty("App::PropertyString", "InputCaseName", "Solver",
                            "Name of case containing the input files and from where the solver is executed.")
            obj.addProperty("App::PropertyBool", "Parallel", "Solver",
                            "Parallel analysis on on multiple CPU cores")
            obj.addProperty("App::PropertyInteger", "ParallelCores", "Solver",
                            "Number of cores on which to run parallel analysis")

            import tempfile
            if tempfile.tempdir:
                obj.WorkingDir = tempfile.tempdir
            elif os.path.exists('/tmp/'):   # must exist for POSIX system
                obj.WorkingDir = os.path.abspath('/tmp/')  # On Windows, os.path.exists tests the abs path, i.e. c:\tmp
            else:
                obj.WorkingDir = '.'
            obj.InputCaseName = 'case'

            obj.addProperty("App::PropertyFloat", "EndTime", "TimeStepControl",
                            "Duration limit if the solver did not reach convergence.")
            obj.addProperty("App::PropertyFloat", "TimeStep", "TimeStepControl",
                            "Time step increment.")
            obj.addProperty("App::PropertyFloat", "WriteInterval", "TimeStepControl",
                            "Output interval.")
            obj.addProperty("App::PropertyFloat", "ConvergenceCriteria", "TimeStepControl",
                            "Global solution convergence criterion.")

            # Default time step values
            # Temporarily use steady state (simpleFoam) compliant values
            obj.EndTime = 1000
            obj.TimeStep = 1
            obj.WriteInterval = 100
            obj.ConvergenceCriteria = 1e-4

    def execute(self, obj):
        return

    def onChanged(self, obj, prop):
        return

    def __getstate__(self):
        return self.Type

    def __setstate__(self, state):
        if state:
            self.Type = state
