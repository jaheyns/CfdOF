# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2017 - Alfred Bogaers (CSIR) <abogaers@csir.co.za>      *
# *   Copyright (c) 2017 - Johan Heyns (CSIR) <jheyns@csir.co.za>           *
# *   Copyright (c) 2017 - Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>        *
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

__title__ = "CFDPorousZone"
__author__ = "AB, OO, JH"
__url__ = "http://www.freecadweb.org"

import FreeCAD, Part, math
from FreeCAD import Base
from pivy import coin
import FreeCADGui


class PartFeature:
    def __init__(self, obj):
        obj.Proxy = self


class _CfdPorousZone(PartFeature):
    """ The CFD Porous Zone Model """

    def __init__(self, obj):
        PartFeature.__init__(self, obj)

        # obj.addProperty("App::PropertyPythonObject","Properties")
        # obj.addProperty("Part::PropertyPartShape","Shape")

        # obj.addProperty("App::PropertyStringList","partNameList")
        obj.addProperty("App::PropertyPythonObject", "partNameList").partNameList = []
        obj.addProperty("App::PropertyLinkList", "shapeList")
        obj.addProperty("App::PropertyPythonObject", "porousZoneProperties")
        obj.porousZoneProperties = {
            'PorousCorrelation': 'DarcyForchheimer',
            'D': [0, 0, 0],
            'F': [0, 0, 0],
            'e1': [1, 0, 0],
            'e2': [0, 1, 0],
            'e3': [0, 0, 1],
            'OuterDiameter': 0.0,
            'TubeAxis': [0, 0, 1],
            'TubeSpacing': 0.0,
            'SpacingDirection': [1, 0, 0],
            'AspectRatio': 1.73,
            'VelocityEstimate': 0.0
        }

        obj.Proxy = self
        self.Type = "PorousZone"

    def execute(self, fp):
        listOfShapes = []
        for i in range(len(fp.shapeList)):
            listOfShapes.append(fp.shapeList[i].Shape)
        if len(listOfShapes) > 0:
            fp.Shape = Part.makeCompound(listOfShapes)
        else:
            fp.Shape = Part.Shape()

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None
