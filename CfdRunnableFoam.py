# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2015 - Qingfeng Xia <qingfeng.xia()eng.ox.ac.uk>        *
# *   Copyright (c) 2017 - Alfred Bogaers (CSIR) <abogaers@csir.co.za>      *
# *   Copyright (c) 2017 - Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>        *
# *   Copyright (c) 2017 - Johan Heyns (CSIR) <jheyns@csir.co.za>           *
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
import Gnuplot
from numpy import *

import FreeCAD

import CfdCaseWriterFoam
import CfdTools
import platform
import subprocess


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

        self.edit_process = None

    def check_prerequisites(self):
        return "" #CfdTools.check_prerequisites()

    def edit_case(self):
        """ Open case folder externally in file browser. """
        case_path = self.solver.WorkingDir + os.path.sep + self.solver.InputCaseName
        FreeCAD.Console.PrintMessage("Please edit the case input files externally at: {}\n".format(case_path))
        if platform.system() == 'MacOS':
            self.edit_process = subprocess.Popen(['open', '--', case_path])
        elif platform.system() == 'Linux':
            self.edit_process = subprocess.Popen(['xdg-open', case_path])
        elif platform.system() == 'Windows':
            self.edit_process = subprocess.Popen(['explorer', case_path])


#  Concrete Class for CfdRunnable for OpenFOAM
#  implemented write_case() and solver_case(), not yet for load_result()
class CfdRunnableFoam(CfdRunnable):
    def __init__(self, analysis=None, solver=None):
        super(CfdRunnableFoam, self).__init__(analysis, solver)
        self.writer = CfdCaseWriterFoam.CfdCaseWriterFoam(self.analysis)

        # Set default windows executable to gnuplot instead of older pgnuplot
        import platform
        if platform.system() == 'Windows':
            Gnuplot.GnuplotOpts.gnuplot_command = 'gnuplot.exe'
        gnuplot_cmd = Gnuplot.GnuplotOpts.gnuplot_command
        # For blueCFD, use the supplied Gnuplot
        if CfdTools.getFoamRuntime() == 'BlueCFD':
            gnuplot_cmd = CfdTools.getFoamDir()
            gnuplot_cmd = '{}\\..\\AddOns\\gnuplot\\bin\\gnuplot.exe'.format(gnuplot_cmd)
            Gnuplot.GnuplotOpts.gnuplot_command = '"{}"'.format(gnuplot_cmd)
        # Otherwise, the command 'gnuplot' must be in the path. Possibly make path user-settable.
        # Test to see if it exists, as the exception thrown is cryptic on Windows if it doesn't
        import distutils.spawn
        if distutils.spawn.find_executable(gnuplot_cmd) is None:
            raise IOError("Gnuplot executable " + gnuplot_cmd + " not found in path.")
        self.g = Gnuplot.Gnuplot()

        self.UxResiduals = [1]
        self.UyResiduals = [1]
        self.UzResiduals = [1]
        self.pResiduals = [1]
        self.niter = 0

        self.print_next_error_lines = 0
        self.print_next_error_file = False

    def check_prerequisites(self):
        return ""

    def get_solver_cmd(self, case_dir):
        self.UxResiduals = [1]
        self.UyResiduals = [1]
        self.UzResiduals = [1]
        self.pResiduals = [1]
        self.niter = 0
        self.print_next_error_lines = 0
        self.print_next_error_file = False

        self.g('set style data lines')
        self.g.title("Simulation residuals")
        self.g.xlabel("Iteration")
        self.g.ylabel("Residual")

        self.g("set grid")
        self.g("set logscale y")
        self.g("set yrange [0.95:1.05]")
        self.g("set xrange [0:1]")

        # Environment is sourced in run script, so no need to include in run command
        cmd = CfdTools.makeRunCommand('./Allrun', case_dir, source_env=False)
        FreeCAD.Console.PrintMessage("Solver run command: " + ' '.join(cmd) + "\n")
        return cmd

    def getRunEnvironment(self):
        return CfdTools.getRunEnvironment()

    def getParaviewScript(self):
        # Already created when case created - just return script name
        return os.path.join(self.writer.case_folder, "pvScript.py")

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

        # Workaround for 'Interrupted System Call' error - see PEP 475 (not necessary in Python >= 3.5)
        while True:
            try:
                self.g.plot(Gnuplot.Data(self.UxResiduals, with_='line', title="Ux", inline=1),
                            Gnuplot.Data(self.UyResiduals, with_='line', title="Uy", inline=1),
                            Gnuplot.Data(self.UzResiduals, with_='line', title="Uz", inline=1),
                            Gnuplot.Data(self.pResiduals, with_='line', title="p", inline=1))
                break
            except IOError as ioe:
                import errno
                if ioe.errno == errno.EINTR:
                    pass
                else:
                    raise

        if self.niter >= 2:
            self.g("set autoscale")  # NOTE: this is just to suppress the empty yrange error when Gnuplot autoscales

    def processErrorOutput(self, err):
        """
        Process standard error text output from solver
        :param err: Standard error output, single or multiple lines
        :return: A message to be printed on console, or None
        """
        ret = ""
        errlines = err.split('\n')
        for errline in errlines:
            if len(errline) > 0:  # Ignore blanks
                if self.print_next_error_lines > 0:
                    ret += errline + "\n"
                    self.print_next_error_lines -= 1
                if self.print_next_error_file and errline.contains("file:"):
                    ret += errline + "\n"
                    self.print_next_error_file = False
                if errline.contains("--> FOAM FATAL ERROR:"):
                    self.print_next_error_lines = 1
                    ret += "OpenFOAM fatal error:\n"
                elif errline.contains("--> FOAM FATAL IO ERROR:"):
                    self.print_next_error_lines = 1
                    self.print_next_error_file = True
                    ret += "OpenFOAM IO error:\n"
        if len(ret) > 0:
            return ret
        else:
            return None
