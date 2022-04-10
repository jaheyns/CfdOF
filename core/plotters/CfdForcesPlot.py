# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2017 Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>          *
# *   Copyright (c) 2017 Johan Heyns (CSIR) <jheyns@csir.co.za>             *
# *   Copyright (c) 2017 Alfred Bogaers (CSIR) <abogaers@csir.co.za>        *
# *   Copyright (c) 2019 Oliver Oxtoby <oliveroxtoby@gmail.com>             *
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

import FreeCAD
from PySide import QtCore
import math

if int(FreeCAD.Version()[0]) == 0 and int(FreeCAD.Version()[1].split('.')[0]) < 20:
    from freecad.plot import Plot  # Plot workbench
else:
    try:
        from FreeCAD.Plot import Plot  # Builtin plot module
    except ImportError:
        from freecad.plot import Plot  # Fallback to workbench


class ForcesPlot:
    def __init__(self):
        self.fig = Plot.figure(FreeCAD.ActiveDocument.Name + "Forces")

        self.updated = False
        self.residuals_forces = {}
        self.residuals_coeffs = {}

        self.Timer = QtCore.QTimer()
        self.Timer.timeout.connect(self.refresh)
        self.Timer.start(2000)

    def __del__(self):
        if FreeCAD.GuiUp:
            self.refresh()

    def updateResiduals(self, residuals_forces):
        self.updated = True
        self.residuals_forces = residuals_forces

    def refresh(self):
        if self.updated:
            self.updated = False

            # Forces
            ax1 = self.fig.axes
            ax1.cla()
            ax1.set_title("Force Monitors")
            ax1.set_xlabel("Iteration")
            ax1.set_ylabel("Monitor")

            last_residuals_min = 1e-2
            iter_max = 100
            for k in self.residuals_forces:
                if self.residuals_forces[k]:
                    ax1.plot(self.residuals_forces[k], label=k, linewidth=1)
                    last_residuals_min = min([last_residuals_min] + self.residuals_forces[k][1:-1])
                    iter_max = max(iter_max, len(self.residuals_forces[k]))

            ax1.grid()
            # Increase in increments of 100
            ax1.set_xlim([0, math.ceil(float(iter_max)/100)*100])
            ax1.legend(loc='lower left')
