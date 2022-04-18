# ***************************************************************************
# *                                                                         *
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
import FreeCADGui
from CfdTools import addObjectProperty


class CfdScalarTransportFunction:

    def __init__(self, obj):
        self.Type = "CfdScalarTransportFunction"
        self.Object = obj
        obj.Proxy = self
        self.initProperties(obj)

    def initProperties(self, obj):
        addObjectProperty(obj, 'FieldName', "S", "App::PropertyString", "Scalar transport",
                          "Name of the scalar transport field")

        addObjectProperty(obj, 'FluxFieldName', "phi", "App::PropertyString", "Scalar transport",
                          "Name of the scalar transport flux field")

        addObjectProperty(obj, 'DensityFieldName', "rho", "App::PropertyString", "Scalar transport",
                          "Name of the density field")

        addObjectProperty(obj, 'PhaseFieldName', "none", "App::PropertyString", "Scalar transport",
                          "Name of the scalar transport phase field")

        addObjectProperty(obj, 'ResetOnStartup', False, "App::PropertyBool", "Scalar transport",
                          "Reset the scalar field on startup")

        addObjectProperty(obj, 'SchemeFieldName', "U", "App::PropertyString", "Scalar transport",
                          "Name of the scheme field name from fvScheme")

        addObjectProperty(obj, 'DiffusivityFixedValue', "0.001", "App::PropertyQuantity", "Scalar transport",
                          "Diffusion coefficient for fixed value diffusivity")

        addObjectProperty(obj, 'DiffusivityFieldName', "none", "App::PropertyString", "Scalar transport",
                          "Name of the dynamic diffusivity field")

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