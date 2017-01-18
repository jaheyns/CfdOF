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
import Gnuplot
from numpy import *

import FreeCAD

import CfdCaseWriterFoam
import CfdTools



class CfdRunnable(object):
    ##  run the solver and read the result, corresponding to FemTools class
    #  @param analysis - analysis object to be used as the core object.
    #  "__init__" tries to use current active analysis in analysis is left empty.
    #  Rises exception if analysis is not set and there is no active analysis
    #  The constructur of FemTools is for use of analysis without solver object
    def __init__(self, analysis=None, solver=None):
        if analysis and analysis.isDerivedFrom("Fem::FemAnalysisPython"):
            ## @var analysis
            #  FEM analysis - the core object. Has to be present.
            #  It's set to analysis passed in "__init__" or set to current active analysis by default if nothing has been passed to "__init__"
            self.analysis = analysis
        else:
            if FreeCAD.GuiUp:
                import FemGui
                self.analysis = FemGui.getActiveAnalysis()

        self.solver = None
        if solver and solver.isDerivedFrom("Fem::FemSolverObjectPython"):
            ## @var solver
            #  solver of the analysis. Used to store the active solver and analysis parameters
            self.solver = solver
        else:
            if analysis:
                self.solver = CfdTools.getSolver(self.analysis)
            if self.solver == None:
                FreeCAD.Console.printMessage("FemSolver object is missing from Analysis Object")

        if self.analysis:
            self.results_present = False
            self.result_object = None
        else:
            raise Exception('FEM: No active analysis found!')

    def check_prerequisites(self):
        return ""

    def edit_case(self):
        case_path = self.solver.WorkingDir + os.path.sep + self.solver.InputCaseName
        FreeCAD.Console.PrintMessage("Please edit the case input files externally at: {}".format(case_path))
        self.writer.builder.editCase()


#  Concrete Class for CfdRunnable for OpenFOAM
#  implemented write_case() and solver_case(), not yet for load_result()
class CfdRunnableFoam(CfdRunnable):
    def __init__(self, analysis=None, solver=None):
        super(CfdRunnableFoam, self).__init__(analysis, solver)
        self.writer = CfdCaseWriterFoam.CfdCaseWriterFoam(self.analysis)

        self.g = Gnuplot.Gnuplot()
        self.g('set style data lines')
        self.g.title("Simulation residuals")
        self.g.xlabel("Iteration")
        self.g.ylabel("Residual")

        self.g("set grid")
        self.g("set logscale y")
        self.g("set yrange [0.95:1.05]")
        self.g("set xrange [0:1]")

        self.UxResiduals = [1]
        self.UyResiduals = [1]
        self.UzResiduals = [1]
        self.pResiduals = [1]
        self.niter = 0

    def check_prerequisites(self):
        return ""

    def write_case(self):
        return self.writer.write_case()

    def get_solver_cmd(self):
        import FoamCaseBuilder.utility
        cmd = "bash -c \"source {}/etc/bashrc && ./Allrun\"".format(FoamCaseBuilder.utility.getFoamDir())
        FreeCAD.Console.PrintMessage("Solver run command: " + cmd + "\n")
        return cmd

    def view_result_externally(self):
        self.writer.builder.viewResult()  # paraview

    def view_result(self):
        #  foamToVTK will write result into VTK data files
        result = self.writer.builder.exportResult()
        #result = "/home/qingfeng/Documents/TestCase/VTK/TestCase_345.vtk"  # test passed
        from CfdResultFoamVTK import importCfdResult
        importCfdResult(result, self.analysis)

    def process_output(self, text):
        loglines = text.split('\n')
        printlines = []
        for line in loglines:
            # print line,
            split = line.split()

            # Only store the first residual per timestep
            if line.startswith(u"Time = "):
                self.niter += 1

            # print split
            if "Ux," in split and self.niter > len(self.UxResiduals):
                self.UxResiduals.append(float(split[7].split(',')[0]))
            if "Uy," in split and self.niter > len(self.UyResiduals):
                self.UyResiduals.append(float(split[7].split(',')[0]))
            if "Uz," in split and self.niter > len(self.UzResiduals):
                self.UzResiduals.append(float(split[7].split(',')[0]))
            if "p," in split and self.niter > len(self.pResiduals):
                self.pResiduals.append(float(split[7].split(',')[0]))

        # NOTE: the mod checker is in place for the possibility plotting takes longer
        # NOTE: than a small test case to solve
        if mod(self.niter, 1) == 0:
            self.g.plot(Gnuplot.Data(self.UxResiduals, with_='line', title="Ux", inline=1),
                        Gnuplot.Data(self.UyResiduals, with_='line', title="Uy", inline=1),
                        Gnuplot.Data(self.UzResiduals, with_='line', title="Uz", inline=1),
                        Gnuplot.Data(self.pResiduals, with_='line', title="p"))

        if self.niter >= 2:
            self.g("set autoscale")  # NOTE: this is just to supress the empty yrange error when GNUplot autscales
