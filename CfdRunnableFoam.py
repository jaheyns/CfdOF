# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2015 - Qingfeng Xia <qingfeng.xia()eng.ox.ac.uk>        *
# *   Copyright (c) 2017 Alfred Bogaers (CSIR) <abogaers@csir.co.za>        *
# *   Copyright (c) 2017 Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>          *
# *   Copyright (c) 2017 Johan Heyns (CSIR) <jheyns@csir.co.za>             *
# *   Copyright (c) 2019-2022 Oliver Oxtoby <oliveroxtoby@gmail.com>        *
# *   Copyright (c) 2022 Jonathan Bergh <bergh.jonathan@gmail.com>          *
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

import os
import FreeCAD
from FreeCAD import Units
import CfdTools
import CfdAnalysis
from PySide.QtCore import QObject, Signal
from collections import OrderedDict

from CfdTimePlot import TimePlot


class CfdRunnable(QObject, object):

    def __init__(self, analysis=None, solver=None):
        super(CfdRunnable, self).__init__()

        if analysis and isinstance(analysis.Proxy, CfdAnalysis._CfdAnalysis):
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

    def check_prerequisites(self):
        return ""


class CfdRunnableFoam(CfdRunnable):
    update_residual_signal = Signal(list, list, list, list)

    def __init__(self, analysis=None, solver=None):
        super(CfdRunnableFoam, self).__init__(analysis, solver)

        self.plot_forces = False
        self.plot_force_coefficients = False
        self.probes = {}

        self.constructAncillaryPlotters()

        self.initResiduals()
        self.initMonitors()

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

        self.in_forces_output = False
        self.in_forcecoeffs_output = False

        if self.plot_forces:
            self.pressureXForces = []
            self.pressureYForces = []
            self.pressureZForces = []

            self.viscousXForces = []
            self.viscousYForces = []
            self.viscousZForces = []

            self.solver.Proxy.forces_plotter.reInitialise(self.analysis)

        if self.plot_force_coefficients:
            self.cdCoeffs = []
            self.clCoeffs = []

            self.solver.Proxy.force_coeffs_plotter.reInitialise(self.analysis)

        if self.plot_probes:
            for pn in self.probes:
                p = self.probes[pn]
                p['file'] = None
                p['time'] = []
                p['values'] = [[]]
            for pn in self.solver.Proxy.probes_plotters:
                self.solver.Proxy.probes_plotters[pn].reInitialise(self.analysis)


    def get_solver_cmd(self, case_dir):
        self.initResiduals()
        self.initMonitors()

        # Environment is sourced in run script, so no need to include in run command
        cmd = CfdTools.makeRunCommand('./Allrun', case_dir, source_env=False)
        FreeCAD.Console.PrintMessage("Solver run command: " + ' '.join(cmd) + "\n")
        return cmd

    def getRunEnvironment(self):
        return CfdTools.getRunEnvironment()

    def constructAncillaryPlotters(self):
        reporting_functions = CfdTools.getReportingFunctionsGroup(CfdTools.getActiveAnalysis())
        if reporting_functions is not None:
            for rf in reporting_functions:
                if rf.ReportingFunctionType == "Force":
                    self.plot_forces = True
                    if self.solver.Proxy.forces_plotter is None:
                        self.solver.Proxy.forces_plotter = TimePlot(title="Forces", y_label="Force [N]", is_log=False)
                elif rf.ReportingFunctionType == "ForceCoefficients":
                    self.plot_force_coefficients = True
                    if self.solver.Proxy.force_coeffs_plotter is None:
                        self.solver.Proxy.force_coeffs_plotter = \
                            TimePlot(title="Force Coefficients", y_label="Coefficient", is_log=False)
                elif rf.ReportingFunctionType == 'Probes':
                    self.plot_probes = True
                    self.probes[rf.Label] = {
                        'file': None, 
                        'time': [], 
                        'values': [[]], 
                        'field': rf.SampleFieldName, 
                        'points': [rf.ProbePosition]}
                    if rf.Label not in self.solver.Proxy.probes_plotters:
                        self.solver.Proxy.probes_plotters[rf.Label] = \
                            TimePlot(title=rf.Label, y_label=rf.SampleFieldName, is_log=False)

    def process_output(self, text):
        log_lines = text.split('\n')
        prev_niter = self.niter
        for line in log_lines:
            split = line.split()

            # Only record the first residual per outer iteration
            if line.startswith(u"Time = "):
                self.prev_time = self.latest_time
                self.latest_time = float(line.lstrip(u"Time = "))
                self.prev_num_outer_iters = self.latest_outer_iter
                if self.latest_time > 0:
                    # Don't keep spurious time zero
                    self.latest_outer_iter = 0
                    self.niter += 1
                self.in_forces_output = False
                self.in_forcecoeffs_output = False

            if line.find(u"PIMPLE: iteration ") >= 0 or line.find(u"pseudoTime: iteration ") >= 0:
                self.latest_outer_iter += 1
                # Don't increment counter on first outer iter as this was already done with time
                if self.latest_outer_iter > 1:
                    self.niter += 1

            if line.startswith(u"forces"):
                self.in_forces_output = True
            if line.startswith(u"forceCoeffs"):
                self.in_forcecoeffs_output = True

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

            # Force monitors
            if self.in_forces_output:
                if "Pressure" in split and self.niter-1 > len(self.pressureXForces):
                    self.pressureXForces.append(float(split[2].replace("(", "")))
                    self.pressureYForces.append(float(split[3]))
                    self.pressureZForces.append(float(split[4].replace(")", "")))

                if "Viscous" in split and self.niter-1 > len(self.viscousXForces):
                    self.viscousXForces.append(float(split[2].replace("(", "")))
                    self.viscousYForces.append(float(split[3]))
                    self.viscousZForces.append(float(split[4].replace(")", "")))

            if self.in_forcecoeffs_output:
                # Force coefficient monitors
                if "Cd" in split and self.niter-1 > len(self.cdCoeffs):
                    self.cdCoeffs.append(float(split[2]))
                if "Cl" in split and self.niter-1 > len(self.clCoeffs):
                    self.clCoeffs.append(float(split[2]))

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

            if self.plot_forces:
                self.solver.Proxy.forces_plotter.updateValues(self.time, OrderedDict([
                    ('$Pressure_x$', self.pressureXForces),
                    ('$Pressure_y$', self.pressureYForces),
                    ('$Pressure_z$', self.pressureZForces),
                    ('$Viscous_x$', self.viscousXForces),
                    ('$Viscous_y$', self.viscousYForces),
                    ('$Viscous_z$', self.viscousZForces)]))

            if self.plot_force_coefficients:
                self.solver.Proxy.force_coeffs_plotter.updateValues(self.time, OrderedDict([
                    ('$C_D$', self.cdCoeffs),
                    ('$C_L$', self.clCoeffs)
                ]))

        # Probes
        for pn in self.probes:
            p = self.probes[pn]
            if p['file'] is None:
                working_dir = CfdTools.getOutputPath(self.analysis)
                case_name = self.solver.InputCaseName
                solver_dir = os.path.abspath(os.path.join(working_dir, case_name))
                try:
                    f = open(os.path.join(solver_dir, 'postProcessing', pn, '0', p['field']))
                    p['file'] = f
                except OSError:
                    pass
            if p['file']:
                ntimes = len(p['time'])
                is_vector = False
                
                for l in p['file'].readlines():
                    l = l.strip()
                    if len(l) and not l.startswith('#'):
                        s = l.split()
                        p['time'].append(float(s[0]))
                        
                        if s[1].startswith('('):
                            is_vector = True
                        while len(p['values']) < len(s)-1:
                            p['values'].append([])
                        for i in range(1, len(s)):
                            s[i] = s[i].lstrip('(').rstrip(')')
                            p['values'][i-1].append(float(s[i]))

                if len(p['time']) > ntimes:
                    legends = []
                    for pi in p['points']:
                        points_str = '({}, {}, {}) m'.format(
                            *(Units.Quantity(pij, Units.Length).getValueAs('m') for pij in (pi.x, pi.y, pi.z)))
                        if is_vector:
                            legends.append('{}$_x$ @ '.format(p['field']) + points_str)
                            legends.append('{}$_y$ @ '.format(p['field']) + points_str)
                            legends.append('{}$_z$ @ '.format(p['field']) + points_str)
                        else:
                            legends.append('${}$ @ '.format(p['field']) + points_str)
                    self.solver.Proxy.probes_plotters[pn].updateValues(p['time'], OrderedDict(
                        zip(legends, p['values'])))

    def solverFinished(self):
        for pn in self.probes:
            p = self.probes[pn]
            if p['file']:
                p['file'].close()
                p['file'] = None
