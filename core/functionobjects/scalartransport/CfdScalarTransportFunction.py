# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2022 Jonathan Bergh <bergh.jonathan@gmail.com>          *
# *   Copyright (c) 2022 Oliver Oxtoby <oliveroxtoby@gmail.com>             *
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
from CfdTools import addObjectProperty


class CfdScalarTransportFunction:

    def __init__(self, obj):
        self.Type = "ScalarTransportFunction"
        self.Object = obj
        obj.Proxy = self
        self.initProperties(obj)

    def initProperties(self, obj):
        addObjectProperty(obj, 'FieldName', "S", "App::PropertyString", "Scalar transport",
                          "Name of the scalar transport field")

        addObjectProperty(obj, 'DiffusivityFixed', False, "App::PropertyBool", "Scalar transport",
                          "Use fixed value for diffusivity rather than viscosity")

        # This is actually rho*diffusivity, but this is what OpenFOAM uses
        addObjectProperty(obj, 'DiffusivityFixedValue', "0.001 kg/m/s", "App::PropertyQuantity", "Scalar transport",
                          "Diffusion coefficient for fixed diffusivity")

        addObjectProperty(obj, 'RestrictToPhase', False, "App::PropertyBool", "Scalar transport",
                          "Restrict transport within phase")
        
        addObjectProperty(obj, 'PhaseName', "water", "App::PropertyString", "Scalar transport",
                          "Transport within phase")

        addObjectProperty(obj, 'InjectionRate', '1 kg/s', "App::PropertyQuantity", "Scalar transport",
                          "Injection rate")

        addObjectProperty(obj, 'InjectionPoint', FreeCAD.Vector(0, 0, 0), "App::PropertyPosition", "Scalar transport",
                          "Location of the injection point")

    def onDocumentRestored(self, obj):
        self.initProperties(obj)

    def execute(self, obj):
        pass

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None