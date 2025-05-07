# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2017 Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>          *
# *   Copyright (c) 2017 Johan Heyns (CSIR) <jheyns@csir.co.za>             *
# *   Copyright (c) 2017 Alfred Bogaers (CSIR) <abogaers@csir.co.za>        *
# *   Copyright (c) 2019-2022 Oliver Oxtoby <oliveroxtoby@gmail.com>        *
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

import sys
import math
from PySide import QtCore
import FreeCAD

from PySide.QtCore import QT_TRANSLATE_NOOP

# If for any reason PyQt5 has been imported, we need to unload it temporarily
# to prevent matplotlib using the PyQt backend instead of PySide
if 'PyQt5.QtCore' in sys.modules:
    del sys.modules['PyQt5.QtCore']
    reload_PyQt5 = True
else:
    reload_PyQt5 = False

from FreeCAD.Plot import Plot  # Inbuilt plot module

if reload_PyQt5:
    import PyQt5.QtCore

from FreeCAD import Units
from CfdOF import CfdTools

class TimePlot:
    def __init__(self, title, y_label, is_log):
        self.fig = None
        self.title = title
        self.is_logarithmic = is_log
        self.y_label = y_label

        self.updated = False
        self.just_initialised = False
        self.times = []
        self.values = {}
        self.transient = False
        self.ax_lim = 0

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.refresh)
        self.timer.start(2000)

    def __del__(self):
        if FreeCAD.GuiUp:
            self.refresh()

    def figureClosed(self):
        self.fig = None

    def updateValues(self, times, values):
        self.updated = True
        self.times = times
        self.values = values

    def reInitialise(self, analysis_obj):
        phys_model = CfdTools.getPhysicsModel(analysis_obj)
        solver_obj = CfdTools.getSolver(analysis_obj)
        self.transient = (phys_model.Time == 'Transient')
        self.values = {}
        self.ax_lim = 100*solver_obj.TimeStep.getValueAs(Units.TimeSpan).Value if self.transient else 100

    def refresh(self):
        if self.updated:
            self.updated = False
            if self.fig is None:
                self.fig = Plot.figure(FreeCAD.ActiveDocument.Name + ' : ' + self.title)
                self.fig.destroyed.connect(self.figureClosed)
            ax = self.fig.axes
            ax.cla()
            ax.set_title(self.title)
            time_unit = str(Units.Quantity(1, Units.TimeSpan)).split()[-1]
            ax.set_xlabel("Time [{}]".format(time_unit) if self.transient else "Iteration")
            ax.set_ylabel(self.y_label)

            last_values_min = 1e-2
            for k in self.values:
                if self.values[k]:
                    ax.plot(self.times[0:len(self.values[k])], self.values[k], label=k, linewidth=1)
                    last_values_min = min([last_values_min]+self.values[k][1:-1])

            ax.grid()
            if self.is_logarithmic:
                ax.set_yscale('log')
                # Decrease in increments of 10
                ax.set_ylim([10**(math.floor(math.log10(last_values_min))), 1])

            if self.just_initialised and len(self.times):
                # Re-initialise based on the actual first time step taken, which may differ from the time step
                # specified by the user
                self.ax_lim = 100*self.times[0] if self.transient else 100
                self.just_initialised = False

            while float(self.times[-1]) > self.ax_lim:
                # Increase scale by 10%
                self.ax_lim *= 1.1
            ax.set_xlim([0, self.ax_lim])

            if len(self.times):
                ax.legend(loc='lower left')
                self.fig.canvas.draw()
