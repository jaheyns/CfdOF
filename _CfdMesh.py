# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2019 - Oliver Oxtoby <oliveroxtoby@gmail.com>           *
# *   Copyright (c) 2016 - Bernd Hahnebach <bernd@bimstatik.org>            *
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


class _CfdMesh:
    """ CFD mesh properties
    """

    # they will be used from the task panel too, thus they need to be outside of the __init__
    known_element_dimensions = ['2D', '3D']
    known_mesh_utility = ['cfMesh', 'snappyHexMesh', 'gmsh']

    def __init__(self, obj):
        self.Type = "CfdMesh"
        self.Object = obj  # keep a ref to the DocObj for nonGui usage
        obj.Proxy = self  # link between App::DocumentObject to  this object

        obj.addProperty("App::PropertyString", "CaseName", "Base", "Name of directory in which the mesh is created")
        obj.CaseName = "meshCase"

        obj.addProperty("App::PropertyLinkList", "MeshRegionList", "Base", "Mesh regions of the mesh")
        obj.MeshRegionList = []

        obj.addProperty("App::PropertyStringList", "ShapeFaceNames", "Base", "Mesh face names")
        obj.ShapeFaceNames = []

        obj.addProperty("App::PropertyFloat", "STLLinearDeflection", "Base", "STL linear deflection")
        obj.STLLinearDeflection = 0.05

        obj.addProperty("App::PropertyInteger", "NumberCores", "Base", "Number of parallel cores "
                                                                       "(only applicable when using snappyHexMesh) ")
        obj.NumberCores = 1

        obj.addProperty("App::PropertyLink", "Part", "Mesh Parameters", "Part object to mesh")
        obj.Part = None

        obj.addProperty("App::PropertyEnumeration", "MeshUtility", "Mesh Parameters",
                        "Meshing utilities")
        obj.MeshUtility = _CfdMesh.known_mesh_utility
        obj.MeshUtility = 'cfMesh'

        obj.addProperty("App::PropertyLength", "CharacteristicLengthMax", "Mesh Parameters",
                        "Max mesh element size (0.0 = infinity)")
        obj.CharacteristicLengthMax = 0.0

        obj.addProperty("App::PropertyPythonObject", "PointInMesh", "Mesh Parameters",
                        "Location vector inside the region to be meshed (must not coincide with a cell face)")
        obj.PointInMesh = {"x": 0.0,
                           "y": 0.0,
                           "z": 0.0}

        obj.addProperty("App::PropertyInteger", "CellsBetweenLevels", "Mesh Parameters",
                        "Number of cells between each level of refinement")
        obj.CellsBetweenLevels = 3

        obj.addProperty("App::PropertyInteger", "EdgeRefinement", "Mesh Parameters",
                        "Edge or feature refinement level")
        obj.EdgeRefinement = 0

        obj.addProperty("App::PropertyEnumeration", "ElementDimension", "Mesh Parameters",
                        "Dimension of mesh elements (Default 3D)")
        obj.ElementDimension = _CfdMesh.known_element_dimensions
        obj.ElementDimension = '3D'

    def execute(self, obj):
        return

    def __getstate__(self):
        return self.Type

    def __setstate__(self, state):
        if state:
            self.Type = state
