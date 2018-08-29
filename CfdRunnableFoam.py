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

from __future__ import print_function

__title__ = "Classes for New CFD solver"
__author__ = "Qingfeng Xia"
__url__ = "http://www.freecadweb.org"

import os
import os.path

from numpy import *

import FreeCAD

import CfdCaseWriterFoam
import CfdTools
import platform
import subprocess
from PySide.QtCore import QObject, Signal, QThread
from CfdResidualPlot import ResidualPlot
from collections import OrderedDict


class CfdRunnable(QObject, object):
    def __init__(self, analysis=None, solver=None):
        super(CfdRunnable, self).__init__()
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
        case_path = os.path.abspath(os.path.join(CfdTools.getOutputPath(self.analysis), self.solver.InputCaseName))
        FreeCAD.Console.PrintMessage("Please edit the case input files externally at: {}\n".format(case_path))
        if platform.system() == 'MacOS':
            self.edit_process = subprocess.Popen(['open', '--', case_path])
        elif platform.system() == 'Linux':
            self.edit_process = subprocess.Popen(['xdg-open', case_path])
        elif platform.system() == 'Windows':
            self.edit_process = subprocess.Popen(['explorer', case_path])


class CfdRunnableFoam(CfdRunnable):
    update_residual_signal = Signal(list, list, list, list)

    def __init__(self, analysis=None, solver=None):
        super(CfdRunnableFoam, self).__init__(analysis, solver)

        self.writer = CfdCaseWriterFoam.CfdCaseWriterFoam(self.analysis)

        self.initResiduals()

        self.residualPlot = None

        self.print_next_error_lines = 0
        self.print_next_error_file = False

    def check_prerequisites(self):
        return ""

    def initResiduals(self):
        self.UxResiduals = []
        self.UyResiduals = []
        self.UzResiduals = []
        self.pResiduals = []
        self.rhoResiduals = []
        self.EResiduals = []
        self.kResiduals = []
        self.omegaResiduals = []
        self.niter = 0

    def get_solver_cmd(self, case_dir):
        self.initResiduals()

        self.print_next_error_lines = 0
        self.print_next_error_file = False

        self.residualPlot = ResidualPlot()

        # Environment is sourced in run script, so no need to include in run command
        cmd = CfdTools.makeRunCommand('./Allrun', case_dir, source_env=False)
        FreeCAD.Console.PrintMessage("Solver run command: " + ' '.join(cmd) + "\n")
        return cmd

    def getRunEnvironment(self):
        return CfdTools.getRunEnvironment()

    def process_output(self, text):
        loglines = text.split('\n')
        for line in loglines:
            # print line,
            split = line.split()

            # Only store the first residual per timestep
            if line.startswith(u"Time = "):
                self.niter += 1

            # print split
            if "Ux," in split and self.niter-1 > len(self.UxResiduals):
                self.UxResiduals.append(float(split[7].split(',')[0]))
            if "Uy," in split and self.niter-1 > len(self.UyResiduals):
                self.UyResiduals.append(float(split[7].split(',')[0]))
            if "Uz," in split and self.niter-1 > len(self.UzResiduals):
                self.UzResiduals.append(float(split[7].split(',')[0]))
            if "p," in split and self.niter-1 > len(self.pResiduals):
                self.pResiduals.append(float(split[7].split(',')[0]))
            # HiSA coupled residuals
            if "Residual:" in split and self.niter-1 > len(self.rhoResiduals):
                self.rhoResiduals.append(float(split[4]))
                self.UxResiduals.append(float(split[5].lstrip('(')))
                self.UyResiduals.append(float(split[6]))
                self.UzResiduals.append(float(split[7].rstrip(')')))
                self.EResiduals.append(float(split[8]))
            if "k," in split and self.niter-1 > len(self.kResiduals):
                self.kResiduals.append(float(split[7].split(',')[0]))
            if "omega," in split and self.niter-1 > len(self.omegaResiduals):
                self.omegaResiduals.append(float(split[7].split(',')[0]))

        if self.niter > 1:
            self.residualPlot.updateResiduals(OrderedDict([
                ('$\\rho$', self.rhoResiduals),
                ('$U_x$', self.UxResiduals),
                ('$U_y$', self.UyResiduals),
                ('$U_z$', self.UzResiduals),
                ('$p$', self.pResiduals),
                ('$E$', self.EResiduals),
                ('$k$', self.kResiduals),
                ('$\\omega$', self.omegaResiduals)]))

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
                if self.print_next_error_file and "file:" in errline:
                    ret += errline + "\n"
                    self.print_next_error_file = False
                words = errline.split(' ', 1)  # Split off first field for parallel
                FATAL = "--> FOAM FATAL ERROR"
                FATALIO = "--> FOAM FATAL IO ERROR"
                if errline.startswith(FATAL) or (len(words) > 1 and words[1].startswith(FATAL)):
                    self.print_next_error_lines = 1
                    ret += "OpenFOAM fatal error:\n"
                elif errline.startswith(FATALIO) or (len(words) > 1 and words[1].startswith(FATALIO)):
                    self.print_next_error_lines = 1
                    self.print_next_error_file = True
                    ret += "OpenFOAM IO error:\n"
        if len(ret) > 0:
            return ret
        else:
            return None
