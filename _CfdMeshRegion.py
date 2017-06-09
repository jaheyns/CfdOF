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


class _CfdMeshRegion:
    """The CfdMeshRegion object"""
    def __init__(self, obj):
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

        obj.addProperty("App::PropertyLinkSubList", "References", "MeshRegionProperties",
                        "List of mesh region surfaces")

        obj.Proxy = self
        self.Type = "CfdMeshRegion"

    def execute(self, obj):
        return
