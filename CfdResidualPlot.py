# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2017 Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>          *
# *   Copyright (c) 2017 Johan Heyns (CSIR) <jheyns@csir.co.za>             *
# *   Copyright (c) 2017 Alfred Bogaers (CSIR) <abogaers@csir.co.za>        *
# *   Copyright (c) 2019-2022 Oliver Oxtoby <oliveroxtoby@gmail.com>        *
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

from PySide import QtCore
import math
import FreeCAD

if int(FreeCAD.Version()[0]) == 0 and int(FreeCAD.Version()[1].split('.')[0]) < 20:
    from freecad.plot import Plot  # Plot workbench
else:
    try:
        from FreeCAD.Plot import Plot  # Inbuilt plot module
    except ImportError:
        from freecad.plot import Plot  # Fallback to workbench

from FreeCAD import Units
import CfdTools


class ResidualPlot:
    def __init__(self, title, is_log=True):
        self.fig = None
        self.title = title
        self.is_logarithmic = is_log

        self.updated = False
        self.times = []
        self.residuals = {}
        self.transient = False

        self.Timer = QtCore.QTimer()
        self.Timer.timeout.connect(self.refresh)
        self.Timer.start(2000)

    def __del__(self):
        if FreeCAD.GuiUp:
            self.refresh()

    def figureClosed(self):
        self.fig = None

    def updateResiduals(self, times, residuals):
        self.updated = True
        self.times = times
        self.residuals = residuals

    def reInitialise(self, analysis_obj):
        phys_model = CfdTools.getPhysicsModel(analysis_obj)
        solver_obj = CfdTools.getSolver(analysis_obj)
        self.transient = (phys_model.Time == 'Transient')
        self.residuals = {}
        self.times = [solver_obj.TimeStep.getValueAs(Units.TimeSpan) if self.transient else 1]

    def refresh(self):
        if self.updated:
            self.updated = False
            if self.fig is None:
                self.fig = Plot.figure("Residuals for " + FreeCAD.ActiveDocument.Name)
                self.fig.destroyed.connect(self.figureClosed)
            ax = self.fig.axes
            ax.cla()
            ax.set_title(self.title)
            time_unit = str(Units.Quantity(1, Units.TimeSpan)).split()[-1]
            ax.set_xlabel("Time [{}]".format(time_unit) if self.transient else "Iteration")
            ax.set_ylabel("Residual")

            last_residuals_min = 1e-2
            time_max = max(10*self.times[0] if self.transient else 100, self.times[-1])
            for k in self.residuals:
                if self.residuals[k]:
                    ax.plot(self.times[0:len(self.residuals[k])], self.residuals[k], label=k, linewidth=1)
                    last_residuals_min = min([last_residuals_min]+self.residuals[k][1:-1])

            ax.grid()
            ax.set_yscale('log')
            # Decrease in increments of 10
            ax.set_ylim([10**(math.floor(math.log10(last_residuals_min))), 1])
            # Increase in increments of 100
            time_incr = 10.0*self.times[0] if self.transient else 100
            ax.set_xlim([0, math.ceil(float(time_max)/time_incr)*time_incr])

            if len(self.times):
                ax.legend(loc='lower left')

            self.fig.canvas.draw()
