# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2016 - Bernd Hahnebach <bernd@bimstatik.org>            *
# *   Copyright (c) 2017 - Johan Heyns (CSIR) <jheyns@csir.co.za>           *
# *   Copyright (c) 2017 - Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>        *
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

__title__ = "_CfdMeshRegion"
__author__ = "JH, OO, AB"
__url__ = "http://www.freecadweb.org"

# @package CfdMeshRegion
#  \ingroup CFD
from FreeCAD import Base

class PartFeature:
    def __init__(self, obj):
        obj.Proxy = self


class _CfdMeshRegion(PartFeature):
    """The CfdMeshRegion object"""
    def __init__(self, obj):
        PartFeature.__init__(self, obj)

        # GMSH related properties
        obj.addProperty("App::PropertyFloat", "RelativeLength", "GMSH",
                        "Set relative length of the elements for this region")
        obj.RelativeLength = 0.75

        # cfMesh related properties
        obj.addProperty("App::PropertyFloat", "RelativeLength", "cfMesh",
                        "Set relative length of the elements for this region")
        obj.RelativeLength = 0.75

        obj.addProperty("App::PropertyLength", "RefinementThickness", "cfMesh",
                        "Set refinement region thickness")
        obj.RefinementThickness = 0.0

        obj.addProperty("App::PropertyInteger", "NumberLayers", "cfMesh",
                        "Set number of boundary layers")
        obj.NumberLayers = 0

        obj.addProperty("App::PropertyFloat", "ExpansionRatio", "cfMesh",
                        "Set expansion ratio within boundary layers")
        obj.ExpansionRatio = 0.0

        obj.addProperty("App::PropertyLength", "FirstLayerHeight", "cfMesh",
                        "Set the maximum first layer height")
        obj.FirstLayerHeight = 0.0

        # sHMesh related properties
        obj.addProperty("App::PropertyInteger", "RefinementLevel", "snappyHexMesh",
                        "Minimum and maximum refinement levels")
        obj.RefinementLevel = 1

        obj.addProperty("App::PropertyInteger", "RegionEdgeRefinement", "snappyHexMesh",
                        "Region edge or feature refinement level")
        obj.RegionEdgeRefinement = 1

        obj.addProperty("App::PropertyBool", "Baffle", "snappyHexMesh",
                        "Create a zero thickness baffle")
        obj.Baffle = False

        obj.addProperty("App::PropertyPythonObject", "References", "MeshRegionProperties",
                        "List of mesh region surfaces")
        obj.References = []

        #Cartesian mesh internal volume refinement properties
        obj.addProperty("App::PropertyBool","Internal","MeshRegionProperties")
        obj.Internal = False

        obj.addProperty("App::PropertyPythonObject","InternalRegion")
        obj.InternalRegion = {"Type": "Box",
                              "Center": {"x":0,"y":0,"z":0},
                              "BoxLengths": {"x":1e-3,"y":1e-3,"z":1e-3},
                              "SphereRadius": 1e-3}

        obj.Proxy = self
        self.Type = "CfdMeshRegion"

    def execute(self, obj):
        import Part
        #try for problem backward compatibility
        try:
            if obj.Internal:
                if obj.InternalRegion["Type"] == "Box":
                    x = obj.InternalRegion["Center"]["x"]*1000 - obj.InternalRegion["BoxLengths"]["x"]*1000/2.0
                    y = obj.InternalRegion["Center"]["y"]*1000 - obj.InternalRegion["BoxLengths"]["y"]*1000/2.0
                    z = obj.InternalRegion["Center"]["z"]*1000 - obj.InternalRegion["BoxLengths"]["z"]*1000/2.0
                    shape = Part.makeBox(obj.InternalRegion["BoxLengths"]["x"]*1000,
                                         obj.InternalRegion["BoxLengths"]["y"]*1000,
                                         obj.InternalRegion["BoxLengths"]["z"]*1000,
                                         Base.Vector(x,y,z))

                elif obj.InternalRegion["Type"] == "Sphere":
                    shape = Part.makeSphere(obj.InternalRegion["SphereRadius"]*1000,
                                            Base.Vector(obj.InternalRegion["Center"]["x"]*1000,
                                                        obj.InternalRegion["Center"]["y"]*1000,
                                                        obj.InternalRegion["Center"]["z"]*1000))
                obj.Shape = shape
            else:
                obj.Shape = Part.Vertex()
        except AttributeError:
            #print("""In order to view a shape corresponding to the internal region please
                #re-create the refinement object""")
            pass

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None