# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2015 - Qingfeng Xia <qingfeng.xia()eng.ox.ac.uk>        *
# *   Copyright (c) 2017 Alfred Bogaers (CSIR) <abogaers@csir.co.za>        *
# *   Copyright (c) 2017 Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>          *
# *   Copyright (c) 2017 Johan Heyns (CSIR) <jheyns@csir.co.za>             *
# *   Copyright (c) 2019-2023 Oliver Oxtoby <oliveroxtoby@gmail.com>        *
# *   Copyright (c) 2022 Jonathan Bergh <bergh.jonathan@gmail.com>          *
# *                                                                         *
# *   This program is free software: you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License as        *
# *   published by the Free Software Foundation, either version 3 of the    *
# *   License, or (at your option) any later version.                       *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Lesser General Public License for more details.                   *
# *                                                                         *
# *   You should have received a copy of the GNU Lesser General Public      *
# *   License along with this program.  If not,                             *
# *   see <https://www.gnu.org/licenses/>.                                  *
# *                                                                         *
# ***************************************************************************

from __future__ import print_function

import os
import FreeCAD
from FreeCAD import Units
from CfdOF import CfdTools
from CfdOF import CfdAnalysis
from PySide.QtCore import QObject, Signal
from collections import OrderedDict

from CfdOF.CfdTimePlot import TimePlot


class CfdRunnable(QObject, object):

    def __init__(self, analysis=None, solver=None):
        super(CfdRunnable, self).__init__()

        if analysis and isinstance(analysis.Proxy, CfdAnalysis.CfdAnalysis):
            self.analysis = analysis
        else:
            if FreeCAD.GuiUp:
                self.analysis = CfdTools.getActiveAnalysis()

        self.solver = None
        if solver:
            self.solver = solver
        else:
            if analysis:
                self.solver = CfdTools.getSolver(self.analysis)
            if not self.solver:
                FreeCAD.Console.printMessage("Solver object is missing from Analysis Object")

        if self.analysis:
            self.results_present = False
            self.result_object = None
        else:
            raise Exception('No active analysis found')


class CfdRunnableFoam(CfdRunnable):
    update_residual_signal = Signal(list, list, list, list)

    def __init__(self, analysis=None, solver=None):
        super(CfdRunnableFoam, self).__init__(analysis, solver)

        self.forces = {}
        self.force_coeffs = {}
        self.probes = {}
        self.postproc_readers = []

        self.constructReportingFunctionPlotters()

        self.initResiduals()
        self.initMonitors()

    def constructReportingFunctionPlotters(self):
        reporting_functions = CfdTools.getReportingFunctionsGroup(CfdTools.getActiveAnalysis())
        if reporting_functions is not None:
            for rf in reporting_functions:
                if rf.ReportingFunctionType == "Force":
                    self.forces[rf.Label] = {}
                    if rf.Label not in self.solver.Proxy.forces_plotters:
                        self.solver.Proxy.forces_plotters[rf.Label] = \
                            TimePlot(title=rf.Label, y_label="Force [N]", is_log=False)
                elif rf.ReportingFunctionType == "ForceCoefficients":
                    self.force_coeffs[rf.Label] = {}
                    if rf.Label not in self.solver.Proxy.force_coeffs_plotters:
                        self.solver.Proxy.force_coeffs_plotters[rf.Label] = \
                            TimePlot(title=rf.Label, y_label="Coefficient", is_log=False)
                elif rf.ReportingFunctionType == 'Probes':
                    self.probes[rf.Label] = {
                        'field': rf.SampleFieldName, 
                        'points': [rf.ProbePosition]}
                    if rf.Label not in self.solver.Proxy.probes_plotters:
                        self.solver.Proxy.probes_plotters[rf.Label] = \
                            TimePlot(title=rf.Label, y_label=rf.SampleFieldName, is_log=False)
                    else:
                        self.solver.Proxy.probes_plotters[rf.Label].y_label = rf.SampleFieldName

    def initResiduals(self):
        self.UxResiduals = []
        self.UyResiduals = []
        self.UzResiduals = []
        self.pResiduals = []
        self.rhoResiduals = []
        self.EResiduals = []
        self.kResiduals = []
        self.epsilonResiduals = []
        self.omegaResiduals = []
        self.nuTildaResiduals = []
        self.gammaIntResiduals = []
        self.ReThetatResiduals = []

        self.time = []
        self.niter = 0
        self.latest_time = 0
        self.prev_time = 0
        self.latest_outer_iter = 0
        self.prev_num_outer_iters = 0

        self.solver.Proxy.residual_plotter.reInitialise(self.analysis)

    def initMonitors(self):
        working_dir = CfdTools.getOutputPath(self.analysis)
        case_name = self.solver.InputCaseName
        solver_dir = os.path.abspath(os.path.join(working_dir, case_name))
        self.postproc_readers = []

        for fn in self.forces:
            # OpenCFD
            file_name = os.path.join(solver_dir, 'postProcessing', fn, '0', 'force.dat')
            legends = ["$F_X$ (pressure)", "$F_Y$ (pressure)", "$F_Z$ (pressure)", 
                       "$F_X$ (viscous)", "$F_Y$ (viscous)", "$F_Z$ (viscous)"]
            self.postproc_readers += [PostProcessingReader(
                file_name, [4, 5, 6, 7, 8, 9], legends, self.solver.Proxy.forces_plotters[fn])]
            # Foundation
            file_name = os.path.join(solver_dir, 'postProcessing', fn, '0', 'forces.dat')
            legends = ["$F${} (pressure)", "$F${} (viscous)"]
            self.postproc_readers += [PostProcessingReader(
                file_name, [1, 2], legends, self.solver.Proxy.forces_plotters[fn])]
            self.solver.Proxy.forces_plotters[fn].reInitialise(self.analysis)

        for fcn in self.force_coeffs:
            legends = ["$C_D$", "$C_L$"]
            # OpenCFD
            file_name = os.path.join(solver_dir, 'postProcessing', fcn, '0', 'coefficient.dat')
            self.postproc_readers += [PostProcessingReader(
                file_name, [1, 4], legends, self.solver.Proxy.force_coeffs_plotters[fcn])]
            # Foundation
            file_name = os.path.join(solver_dir, 'postProcessing', fcn, '0', 'forceCoeffs.dat')
            self.postproc_readers += [PostProcessingReader(
                file_name, [2, 3], legends, self.solver.Proxy.force_coeffs_plotters[fcn])]
            self.solver.Proxy.force_coeffs_plotters[fcn].reInitialise(self.analysis)

        for pn in self.probes:
            p = self.probes[pn]
            file_name = os.path.join(solver_dir, 'postProcessing', pn, '0', p['field'])
            legends = []
            for pi in p['points']:
                points_str = '({}, {}, {}) m'.format(
                    *(Units.Quantity(pij, Units.Length).getValueAs('m') for pij in (pi.x, pi.y, pi.z)))
                legends.append('{}{{}} @ '.format(p['field']) + points_str)
            self.postproc_readers += [PostProcessingReader(
                file_name, range(1, len(p['points'])+1), legends, self.solver.Proxy.probes_plotters[pn])]
            self.solver.Proxy.probes_plotters[pn].reInitialise(self.analysis)


    def getSolverCmd(self, case_dir):
        self.initResiduals()
        self.initMonitors()

        if CfdTools.getFoamRuntime() == "PosixDocker":
            CfdTools.startDocker()

        # Environment is sourced in run script, so no need to include in run command
        if CfdTools.getFoamRuntime() == "MinGW":
            cmd = CfdTools.makeRunCommand('Allrun.bat', case_dir, source_env=False)
        else:
            cmd = CfdTools.makeRunCommand('./Allrun', case_dir, source_env=False)

        return cmd

    def getRunEnvironment(self):
        return CfdTools.getRunEnvironment()

    def processOutput(self, text):
        log_lines = text.split('\n')[:-1]
        prev_niter = self.niter
        for line in log_lines:
            line = line.rstrip()
            split = line.split()

            # Only record the first residual per outer iteration
            if line.startswith(u"Time = "):
                try:
                    time_val = float(line.lstrip(u"Time = ").rstrip("s"))
                except ValueError:
                    pass
                else:
                    self.prev_time = self.latest_time
                    self.latest_time = time_val
                    self.prev_num_outer_iters = self.latest_outer_iter
                    if self.latest_time > 0:
                        # Don't keep spurious time zero
                        self.latest_outer_iter = 0
                        self.niter += 1
                    self.in_forces_section = None
                    self.in_forcecoeffs_section = None

            if line.find(u"PIMPLE: iteration ") >= 0 or line.find(u"pseudoTime: iteration ") >= 0:
                self.latest_outer_iter += 1
                # Don't increment counter on first outer iter as this was already done with time
                if self.latest_outer_iter > 1:
                    self.niter += 1

            # Add a point to the time axis for each outer iteration
            if self.niter > len(self.time):
                self.time.append(self.latest_time)
                if self.latest_outer_iter > 0:
                    # Outer-iteration case
                    # Create virtual times to space the residuals of the outer iterations nicely on the time graph
                    self.prev_num_outer_iters = max(self.prev_num_outer_iters, self.latest_outer_iter)
                    for i in range(self.latest_outer_iter):
                        self.time[-(self.latest_outer_iter-i)] = self.prev_time + (
                            self.latest_time-self.prev_time)*((i+1)/self.prev_num_outer_iters)

            if "Ux," in split and self.niter > len(self.UxResiduals):
                self.UxResiduals.append(float(split[7].split(',')[0]))
            if "Uy," in split and self.niter > len(self.UyResiduals):
                self.UyResiduals.append(float(split[7].split(',')[0]))
            if "Uz," in split and self.niter > len(self.UzResiduals):
                self.UzResiduals.append(float(split[7].split(',')[0]))
            if "p," in split and self.niter > len(self.pResiduals):
                self.pResiduals.append(float(split[7].split(',')[0]))
            if "p_rgh," in split and self.niter > len(self.pResiduals):
                self.pResiduals.append(float(split[7].split(',')[0]))
            if "h," in split and self.niter > len(self.EResiduals):
                self.EResiduals.append(float(split[7].split(',')[0]))
            # HiSA coupled residuals
            if "Residual:" in split and self.niter > len(self.rhoResiduals):
                self.rhoResiduals.append(float(split[4]))
                self.UxResiduals.append(float(split[5].lstrip('(')))
                self.UyResiduals.append(float(split[6]))
                self.UzResiduals.append(float(split[7].rstrip(')')))
                self.EResiduals.append(float(split[8]))
            if "k," in split and self.niter > len(self.kResiduals):
                self.kResiduals.append(float(split[7].split(',')[0]))
            if "epsilon," in split and self.niter > len(self.epsilonResiduals):
                self.epsilonResiduals.append(float(split[7].split(',')[0]))
            if "omega," in split and self.niter > len(self.omegaResiduals):
                self.omegaResiduals.append(float(split[7].split(',')[0]))
            if "nuTilda," in split and self.niter > len(self.nuTildaResiduals):
                self.nuTildaResiduals.append(float(split[7].split(',')[0]))
            if "gammaInt," in split and self.niter > len(self.gammaIntResiduals):
                self.gammaIntResiduals.append(float(split[7].split(',')[0]))
            if "ReThetat," in split and self.niter > len(self.ReThetatResiduals):
                self.ReThetatResiduals.append(float(split[7].split(',')[0]))

        # Update plots
        if self.niter > 1 and self.niter > prev_niter:
            self.solver.Proxy.residual_plotter.updateValues(self.time, OrderedDict([
                ('$\\rho$', self.rhoResiduals),
                ('$U_x$', self.UxResiduals),
                ('$U_y$', self.UyResiduals),
                ('$U_z$', self.UzResiduals),
                ('$p$', self.pResiduals),
                ('$E$', self.EResiduals),
                ('$k$', self.kResiduals),
                ('$\\epsilon$', self.epsilonResiduals),
                ('$\\tilde{\\nu}$', self.nuTildaResiduals),
                ('$\\omega$', self.omegaResiduals),
                ('$\\gamma$', self.gammaIntResiduals),
                ('$Re_{\\theta}$', self.ReThetatResiduals)]))

        # postProcessing readers
        for r in self.postproc_readers:
            r.read()

    def solverFinished(self):
        for r in self.postproc_readers:
            r.end()


class PostProcessingReader:
    def __init__(self, file_name, column_numbers, legends, plotter):
        self.file_name = file_name
        self.file = None
        self.time = []
        self.column_numbers = column_numbers
        self.column_legends = legends
        self.legends = []
        self.values = []
        self.plotter = plotter

    def read(self):
        if self.file is None:
            try:
                self.file = open(self.file_name)
            except OSError:
                pass
        if self.file:
            ntimes = len(self.time)
            
            for l in self.file.readlines():
                l = l.strip()
                if len(l) and not l.startswith('#'):
                    s = l.split()
                    self.time.append(float(s[0]))
                    
                    col_num = 1
                    val_num = 0
                    output_num = 0
                    in_vector = False
                    for i in range(1, len(s)):
                        if s[i].startswith('('):
                            in_vector = True
                        v = s[i].lstrip('(').rstrip(')')
                        if v and col_num in self.column_numbers:
                            while len(self.values) < val_num+1:
                                if in_vector:
                                    self.legends.append(self.column_legends[output_num].format('$_x$'))
                                    self.legends.append(self.column_legends[output_num].format('$_y$'))
                                    self.legends.append(self.column_legends[output_num].format('$_z$'))
                                    self.values.append([])
                                    self.values.append([])
                                    self.values.append([])
                                else:
                                    self.legends.append(self.column_legends[output_num].format(''))
                                    self.values.append([])
                            self.values[val_num].append(float(v))
                            val_num += 1
                        if s[i].endswith(')'):
                            in_vector = False
                        if v and not in_vector:
                            if col_num in self.column_numbers:
                                output_num += 1
                            col_num += 1

            if len(self.time) > ntimes:
                self.plotter.updateValues(self.time, OrderedDict(
                    zip(self.legends, self.values)))

    def end(self):
        if self.file:
            self.file.close()
            self.file = None
