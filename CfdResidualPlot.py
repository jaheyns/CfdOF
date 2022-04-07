# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2017 Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>          *
# *   Copyright (c) 2017 Johan Heyns (CSIR) <jheyns@csir.co.za>             *
# *   Copyright (c) 2017 Alfred Bogaers (CSIR) <abogaers@csir.co.za>        *
# *   Copyright (c) 2019 Oliver Oxtoby <oliveroxtoby@gmail.com>             *
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

if int(FreeCAD.Version()[0]) == 0 and int(FreeCAD.Version()[1].split('.')[0]) < 20:
    from freecad.plot import Plot  # Plot workbench
else:
    try:
        from FreeCAD.Plot import Plot  # Inbuilt plot module
    except ImportError:
        from freecad.plot import Plot  # Fallback to workbench
import math


class ResidualPlot:
    def __init__(self):
        self.fig = None

        self.updated = False
        self.residuals = {}

        self.Timer = QtCore.QTimer()
        self.Timer.timeout.connect(self.refresh)
        self.Timer.start(2000)

    def __del__(self):
        if FreeCAD.GuiUp:
            self.refresh()

    def figureClosed(self):
        self.fig = None

    def updateResiduals(self, residuals):
        self.updated = True
        self.residuals = residuals

    def reInitialise(self, analysis_obj):
        # TODO: Set behaviour based on steady/transient settings
        self.residuals = {}

    def refresh(self):
        if self.updated:
            self.updated = False
            if self.fig is None:
                self.fig = Plot.figure("Residuals for " + FreeCAD.ActiveDocument.Name)
                self.fig.destroyed.connect(self.figureClosed)
            ax = self.fig.axes
            ax.cla()
            ax.set_title("Simulation residuals")
            ax.set_xlabel("Iteration")
            ax.set_ylabel("Residual")

            last_residuals_min = 1e-2
            iter_max = 100
            for k in self.residuals:
                if self.residuals[k]:
                    ax.plot(self.residuals[k], label=k, linewidth=1)
                    last_residuals_min = min([last_residuals_min]+self.residuals[k][1:-1])
                    iter_max = max(iter_max, len(self.residuals[k]))

            ax.grid()
            ax.set_yscale('log')
            # Decrease in increments of 10
            ax.set_ylim([10**(math.floor(math.log10(last_residuals_min))), 1])
            # Increase in increments of 100
            ax.set_xlim([0, math.ceil(float(iter_max)/100)*100])

            if len(self.residuals):
                ax.legend(loc='lower left')

            self.fig.canvas.draw()
