# ***************************************************************************
# *                                                                         *
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

__title__ = "_CfdMeshCart"
__author__ = "Bernd Hahnebach"
__url__ = "http://www.freecadweb.org"


class _CfdMeshCart():
    """ Add cut-cell Cartesian specific properties
    """

    # they will be used from the task panel too, thus they need to be outside of the __init__
    known_element_dimensions = ['2D', '3D']
    known_mesh_algorithm_2D = ['Cartesian']
    known_mesh_algorithm_3D = ['Cartesian']
    known_mesh_utility = ['cfMesh', 'snappyHexMesh']

    def __init__(self, obj):
        self.Type = "CfdMeshCart"
        self.Object = obj  # keep a ref to the DocObj for nonGui usage
        obj.Proxy = self  # link between App::DocumentObject to  this object

        obj.addProperty("App::PropertyLinkList", "MeshRegionList", "Base", "Mesh regions of the mesh")
        obj.MeshRegionList = []

        obj.addProperty("App::PropertyLinkList", "MeshGroupList", "Base", "Mesh groups of the mesh")
        obj.MeshGroupList = []

        obj.addProperty("App::PropertyStringList", "ShapeFaceNames", "Base", "Mesh face names")
        obj.ShapeFaceNames = []

        obj.addProperty("App::PropertyFloat", "STLLinearDeflection", "Base", "STL linear deflection")
        obj.STLLinearDeflection = 0.1

        obj.addProperty("App::PropertyInteger", "NumberCores", "Base", "Number of parallel cores "
                                                                       "(only applicable when using sHM) ")
        obj.NumberCores = 1

        obj.addProperty("App::PropertyLink", "Part", "Mesh Parameters", "Part object to mesh")
        obj.Part = None

        obj.addProperty("App::PropertyEnumeration", "MeshUtility", "Mesh Parameters",
                        "Cut-cell Cartesian meshing utilities")
        obj.MeshUtility = _CfdMeshCart.known_mesh_utility
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
        obj.ElementDimension = _CfdMeshCart.known_element_dimensions
        obj.ElementDimension = '3D'

        obj.addProperty("App::PropertyEnumeration", "Algorithm2D", "Mesh Parameters", "2D mesh algorithm")
        obj.Algorithm2D = _CfdMeshCart.known_mesh_algorithm_2D
        obj.Algorithm2D = 'Cartesian'

        obj.addProperty("App::PropertyEnumeration", "Algorithm3D", "Mesh Parameters", "3D mesh algorithm")
        obj.Algorithm3D = _CfdMeshCart.known_mesh_algorithm_3D
        obj.Algorithm3D = 'Cartesian'

    def execute(self, obj):
        return

    def __getstate__(self):
        return self.Type

    def __setstate__(self, state):
        if state:
            self.Type = state
