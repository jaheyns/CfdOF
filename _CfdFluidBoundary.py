# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2015 - Bernd Hahnebach <bernd@bimstatik.org>            *
# *   Copyright (c) 2017 - CSIR, South Africa                               *
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

__title__ = "Fluid boundary object"
__author__ = ""
__url__ = "http://www.freecadweb.org"

## @package CfdFluidBoundary
#  \ingroup CFD

import FreeCAD

class _CfdFluidBoundary:
    "The CfdFluidBoundary object"
    def __init__(self, obj):
        obj.Proxy = self
        self.Type = "CfdFluidBoundary"
        obj.addProperty("App::PropertyPythonObject", "BoundarySettings")
        # Default settings
        obj.BoundarySettings = {"BoundaryType": "wall",
                                "BoundarySubtype": "fixed",
                                "VelocityIsCartesian": True,
                                "Ux": "0 m/s",    # Units.Quantity not JSON serialisable, so use string
                                "Uy": "0 m/s",
                                "Uz": "0 m/s",
                                "VelocityMag": "0 m/s",
                                "DirectionFace": "",
                                "ReverseNormal": False,
                                "Pressure": "0 kg*m/s^2",
                                "SlipRatio": "0",
                                "VolFlowRate": "0.0 m^3/s",
                                "MassFlowRate": "0.0 kg/s",
                                "TurbulenceSpecification": "intensity&DissipationRate",
                                "ThermalBoundaryType": "fixedValue"}

    def execute(self, obj):
        return
