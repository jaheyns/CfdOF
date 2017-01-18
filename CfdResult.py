#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2016 - Qingfeng Xia <qingfeng.xia()eng.ox.ac.uk> *
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   This program is distributed in the hope that it will be useful,       *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Library General Public License for more details.                  *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with this program; if not, write to the Free Software   *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************

__title__ = "DocumentOject Class to hold CFD result"
__author__ = "Qingfeng Xia"
__url__ = "http://www.freecadweb.org"

import FreeCAD
import Fem

def makeCfdResult(result_obj_name):
    obj= FreeCAD.ActiveDocument.addObject('Fem::FemResultObjectPython', result_obj_name)
    _CfdResult(obj)
    if FreeCAD.GuiUp:
        from _ViewProviderCfdResult import _ViewProviderCfdResult
        _ViewProviderCfdResult(obj.ViewObject)
    return obj

class _CfdResult(object):
    def __init__(self, obj):
        self.Type = "CfdResult"
        self.Object = obj  # keep a ref to the DocObj for nonGui usage
        obj.Proxy = self  # link between App::DocumentObject to  this object

        obj.addProperty("App::PropertyVectorList", "Velocity", "CFD",
                                "fluid velocity", True)  # does not show up in propertyEditor of combiView
        obj.addProperty("App::PropertyFloatList", "Pressure", "CFD",
                                "fluid pressure", True)  # readonly in propertyEditor of combiView
        # `Temperature, Time, Stats` should have been defined in base cpp class, creat it in case cpp has refactored
        if "Temperature" not in obj.PropertiesList:
            obj.addProperty("App::PropertyFloatList", "Temperature", "CFD",
                                    "Temperature field", True)
        obj.addProperty("App::PropertyFloatList", "TurbulenceViscosity", "CFD",
                                "turbulence visocisity for any turblulent flow", True)
        obj.addProperty("App::PropertyFloatList", "TurbulenceThermalDiffusivity", "CFD",
                                "turbulence thermal diffusivity (alphat) for any turblulent flow", True)
        obj.addProperty("App::PropertyFloatList", "TurbulenceEnergy", "CFD",
                                "k for k-epsilon or k-omega model for the fluid", True)
        obj.addProperty("App::PropertyFloatList", "TurbulenceDissipationRate", "CFD",
                                "epsilon for k-epsilon model for the fluid", True)
        obj.addProperty("App::PropertyFloatList", "TurbulenceSpecificDissipation", "CFD",
                                "omega for k-omega model for the fluid", True)
        # multiphase flow will not support by GUI
    ############ standard FeutureT methods ##########
    def execute(self, obj):
        """"this method is executed on object creation and whenever the document is recomputed"
        update Part or Mesh should NOT lead to recompution of the analysis automatically, time consuming
        """
        return

    def onChanged(self, obj, prop):
        return

    def __getstate__(self):
        return self.Type

    def __setstate__(self, state):
        if state:
            self.Type = state
