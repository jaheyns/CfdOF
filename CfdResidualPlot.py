# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2017 - Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>        *
# *   Copyright (c) 2017 - Johan Heyns (CSIR) <jheyns@csir.co.za>           *
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

from PySide import QtCore
import FreeCAD
import Plot


class ResidualPlot:
    def __init__(self):
        self.fig = Plot.figure(FreeCAD.ActiveDocument.Name + "Residuals")

        self.updated = False
        self.UxResiduals = []
        self.UyResiduals = []
        self.UzResiduals = []
        self.pResiduals = []

        self.Timer = QtCore.QTimer()
        self.Timer.timeout.connect(self.refresh)
        self.Timer.start(2000)

    def updateResiduals(self, UxResiduals, UyResiduals, UzResiduals, pResiduals):
        self.updated = True
        self.UxResiduals = UxResiduals
        self.UyResiduals = UyResiduals
        self.UzResiduals = UzResiduals
        self.pResiduals = pResiduals

    def refresh(self):
        if self.updated:
            self.updated = False
            ax = self.fig.axes
            ax.cla()
            ax.set_title("Simulation residuals")
            ax.set_xlabel("Iteration")
            ax.set_ylabel("Residual")

            ax.plot(self.UxResiduals, label="$U_x$", color='violet', linewidth=1)
            ax.plot(self.UyResiduals, label="$U_y$", color='green', linewidth=1)
            ax.plot(self.UzResiduals, label="$U_z$", color='blue', linewidth=1)
            ax.plot(self.pResiduals, label="$p$", color='orange', linewidth=1)

            ax.grid()
            ax.set_yscale('log')
            ax.legend()

            self.fig.canvas.draw()
