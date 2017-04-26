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

__title__ = "Tools for the work with GMSH mesher"
__author__ = "Bernd Hahnebach"
__url__ = "http://www.freecadweb.org"

## \addtogroup FEM
#  @{

import FreeCAD
import Fem
import FemMeshTools
import Units
import subprocess
import tempfile
import os
import shutil
import CfdTools
import math
from platform import system
import FoamCaseBuilder.utility
from FoamCaseBuilder.utility import readTemplate

class CfdCartTools():
    def __init__(self, gmsh_mesh_obj, analysis=None):
        self.mesh_obj = gmsh_mesh_obj
        if analysis:
            self.analysis = analysis
            # group meshing turned on
        else:
            self.analysis = None
            # group meshing turned off

        # part to mesh
        self.part_obj = self.mesh_obj.Part

        # Default to 2 % of bounding box characteristic length
        self.clmax = Units.Quantity(self.mesh_obj.CharacteristicLengthMax).Value
        if self.clmax == 0.0:
            shape = self.part_obj.Shape
            clBoundBox = math.sqrt(shape.BoundBox.XLength**2 + shape.BoundBox.YLength**2 + shape.BoundBox.ZLength**2)
            self.clmax = 0.02*clBoundBox

        # clmin, CharacteristicLengthMin: float
        # ADAM NOTE: Remove no longer used, maybe replace by max number of cells?
        self.clmin = Units.Quantity(self.mesh_obj.CharacteristicLengthMin).Value

        # Scale characteristic length to meter (saved in mm)
        self.clmax = 0.001*self.clmax
        self.clmin = 0.001*self.clmin

        # Finite volume uses 1st order elements
        # self.order = self.mesh_obj.ElementOrder
        # if self.order == '1st':
        #     self.order = '1'
        # elif self.order == '2nd':
        #     self.order = '1'
        #     print ('Finite volume only supports 1st order elements')
        # else:
        #     print('Error in element order')

        # dimension
        self.dimension = self.mesh_obj.ElementDimension

        # Algorithm2D
        # known_mesh_algorithm_2D = ['Automatic', 'MeshAdapt', 'Delaunay', 'Frontal', 'BAMG', 'DelQuad']
        # ADAM NOTE: cfMesh does support 2D cartesian meshing but not snappy ... not to be supported at this point
        # keep open the possibility to implement at a later stage
        algo2D = self.mesh_obj.Algorithm2D
        if algo2D == 'Automatic':
            self.algorithm2D = '2'
        elif algo2D == 'MeshAdapt':
            self.algorithm2D = '1'
        elif algo2D == 'Delaunay':
            self.algorithm2D = '5'
        elif algo2D == 'Frontal':
            self.algorithm2D = '6'
        elif algo2D == 'BAMG':
            self.algorithm2D = '7'
        elif algo2D == 'DelQuad':
            self.algorithm2D = '8'
        else:
            self.algorithm2D = '2'

        # Algorithm3D
        # known_mesh_algorithm_3D = ['Automatic', 'Delaunay', 'New Delaunay', 'Frontal', 'Frontal Delaunay', 'Frontal Hex', 'MMG3D', 'R-tree']
        # ADAM NOTE: snappy and cf cartesian, while cf supports tet and poly
        algo3D = self.mesh_obj.Algorithm2D
        if algo3D == 'Automatic':
            self.algorithm3D = '1'
        elif algo3D == 'Delaunay':
            self.algorithm3D = '1'
        elif algo3D == 'New Delaunay':
            self.algorithm3D = '2'
        elif algo3D == 'Frontal':
            self.algorithm3D = '4'
        elif algo3D == 'Frontal Delaunay':
            self.algorithm3D = '5'
        elif algo3D == 'Frontal Hex':
            self.algorithm3D = '6'
        elif algo3D == 'MMG3D':
            self.algorithm3D = '7'
        elif algo3D == 'R-tree':
            self.algorithm3D = '9'
        else:
            self.algorithm3D = '1'

    def get_dimension(self):
        # Dimension
        # known_element_dimensions = ['From Shape', '1D', '2D', '3D']
        # if not given, GMSH uses the hightest available.
        # A use case for not "From Shape" would be a surface (2D) mesh of a solid
        # NOTE ADAM: Remove from shape and only allow user to specify 2D (cfMesh) or 3D. Keep checks so that the user is
        # only allowed to select solids (even for 2D mesh)
        # allow the user to select solid if the
        if self.dimension == 'From Shape':
            shty = self.part_obj.Shape.ShapeType
            if shty == 'Solid' or shty == 'CompSolid':
                # print('Found: ' + shty)
                self.dimension = '3'
            elif shty == 'Face' or shty == 'Shell':
                FreeCAD.Console.PrintError("Currently, only supporting 3D solids.\n")
                # self.dimension = '2'
            elif shty == 'Edge' or shty == 'Wire':
                FreeCAD.Console.PrintError("Currently, only supporting 3D solids.\n")
                # self.dimension = '1'
            elif shty == 'Vertex':
                # print('Found: ' + shty)
                FreeCAD.Console.PrintError("You can not mesh a Vertex.\n")
                self.dimension = '0'
            elif shty == 'Compound':
                print('  Found a ' + shty)
                if ("Boolean" in self.part_obj.Name):
                    err = "Boolean compounds may not return the expected mesh."
                    FreeCAD.Console.PrintError(err + "\n")
                self.dimension = '3'  # dimension 3 works for 2D and 1d shapes as well
            else:
                self.dimension = '0'
                FreeCAD.Console.PrintError('Could not retrive Dimension from shape type. Please choose dimension.')
        elif self.dimension == '3D':
            self.dimension = '3'
        elif self.dimension == '2D':
            self.dimension = '2'
        elif self.dimension == '1D':
            self.dimension = '1'
        else:
            print('Error in dimension')
        print('  ElementDimension: ' + self.dimension)

    def get_tmp_file_paths(self):
        tmpdir = tempfile.gettempdir()
        self.meshCaseDir = os.path.join(tmpdir, 'meshCase')
        self.constantDir = os.path.join(self.meshCaseDir, 'constant')
        self.triSurfaceDir = os.path.join(self.constantDir, 'triSurface')
        self.systemDir = os.path.join(self.meshCaseDir, 'system')
        print('  ' + self.meshCaseDir)

        self.templatePath = os.path.join(CfdTools.get_module_path(), "data", "defaults")

        # STL file
        self.temp_file_ast = os.path.join(tmpdir, self.part_obj.Name + '_Geometry.ast')  # Extension for ASCI stl file
        self.temp_file_geo = os.path.join(self.constantDir, 'triSurface', self.part_obj.Name+'_Geometry')  # Rename
        print('  ' + self.temp_file_geo)
        # Mesh dictionary
        self.temp_file_meshDict = os.path.join(self.systemDir, 'meshDict')
        print('  ' + self.temp_file_meshDict)

    def get_group_data(self):
        self.group_elements = {}
        # TODO solid, face, edge seam not work together, some print or make it work together
        # TODO handle groups for Edges and Vertexes

        # mesh groups and groups of analysis member
        if not self.mesh_obj.MeshGroupList:
            print ('  No mesh group objects.')
        else:
            print ('  Mesh group objects, we need to get the elements.')
            for mg in self.mesh_obj.MeshGroupList:
                new_group_elements = FemMeshTools.get_mesh_group_elements(mg, self.part_obj)
                for ge in new_group_elements:
                    if ge not in self.group_elements:
                        self.group_elements[ge] = new_group_elements[ge]
                    else:
                        FreeCAD.Console.PrintError("  A group with this name exists already.\n")
        if self.analysis:
            print('  Group meshing.')
            new_group_elements = FemMeshTools.get_analysis_group_elements(self.analysis, self.part_obj)
            for ge in new_group_elements:
                if ge not in self.group_elements:
                    self.group_elements[ge] = new_group_elements[ge]
                else:
                    FreeCAD.Console.PrintError("  A group with this name exists already.\n")
        else:
            print('  No anlysis members for group meshing.')
        print('  {}'.format(self.group_elements))

        # mesh regions
        self.ele_length_map = {}  # { 'ElementString' : element length }
        self.ele_node_map = {}  # { 'ElementString' : [element nodes] }
        if not self.mesh_obj.MeshRegionList:
            print ('  No mesh regions.')
        else:
            print ('  Mesh regions, we need to get the elements.')
            if self.part_obj.Shape.ShapeType == 'Compound':
                # see http://forum.freecadweb.org/viewtopic.php?f=18&t=18780&start=40#p149467 and http://forum.freecadweb.org/viewtopic.php?f=18&t=18780&p=149520#p149520
                err = "GMSH could return unexpected meshes for a boolean split tools Compound. It is strongly recommended to extract the shape to mesh from the Compound and use this one."
                FreeCAD.Console.PrintError(err + "\n")
            for mr_obj in self.mesh_obj.MeshRegionList:
                # print(mr_obj.Name)
                # print(mr_obj.CharacteristicLength)
                # print(Units.Quantity(mr_obj.CharacteristicLength).Value)
                if mr_obj.CharacteristicLength:
                    if mr_obj.References:
                        for sub in mr_obj.References:
                            # print(sub[0])  # Part the elements belongs to
                            # check if the shape of the mesh region is an element of the Part to mesh, if not try to find the element in the shape to mesh
                            search_ele_in_shape_to_mesh = False
                            if not self.part_obj.Shape.isSame(sub[0].Shape):
                                # print("  One element of the meshregion " + mr_obj.Name + " is not an element of the Part to mesh.")
                                # print("  But we gone try to find it in the Shape to mesh :-)")
                                search_ele_in_shape_to_mesh = True
                            for elems in sub[1]:
                                # print(elems)  # elems --> element
                                if search_ele_in_shape_to_mesh:
                                    # we gone try to find the element it in the Shape to mesh and use the found element as elems
                                    ele_shape = FemMeshTools.get_element(sub[0], elems)  # the method getElement(element) does not return Solid elements
                                    found_element = FemMeshTools.find_element_in_shape(self.part_obj.Shape, ele_shape)
                                    if found_element:
                                        elems = found_element
                                    else:
                                        FreeCAD.Console.PrintError("One element of the meshregion " + mr_obj.Name + " could not be found in the Part to mesh. It will be ignored.\n")
                                # print(elems)  # element
                                if elems not in self.ele_length_map:
                                    self.ele_length_map[elems] = Units.Quantity(mr_obj.CharacteristicLength).Value
                                else:
                                    FreeCAD.Console.PrintError("The element " + elems + " of the meshregion " + mr_obj.Name + " has been added to another mesh region.\n")
                    else:
                        FreeCAD.Console.PrintError("The meshregion: " + mr_obj.Name + " is not used to create the mesh because the reference list is empty.\n")
                else:
                    FreeCAD.Console.PrintError("The meshregion: " + mr_obj.Name + " is not used to create the mesh because the CharacteristicLength is 0.0 mm.\n")
            for eleml in self.ele_length_map:
                ele_shape = FemMeshTools.get_element(self.part_obj, eleml)  # the method getElement(element) does not return Solid elements
                ele_vertexes = FemMeshTools.get_vertexes_by_element(self.part_obj.Shape, ele_shape)
                self.ele_node_map[eleml] = ele_vertexes
        print('  {}'.format(self.ele_length_map))
        print('  {}'.format(self.ele_node_map))

    def setupMeshCaseDir(self):
        ''' Temporary mesh case directory '''
        if os.path.isdir(self.meshCaseDir):
            shutil.rmtree(self.meshCaseDir)
        os.makedirs(self.meshCaseDir)
        os.makedirs(self.constantDir)
        os.makedirs(self.triSurfaceDir)

        shutil.copytree(os.path.join(self.templatePath, 'cfMesh','system'), self.systemDir)


    def createMeshScript(self, run_parallel, mesher_name, num_proc):
        print("Create Allmesh script ")

        fname = self.meshCaseDir + os.path.sep + "Allmesh"  # Replace

        if os.path.exists(fname):
            print("Warning: Overwrite existing Allmesh script and log files.")
            os.remove(os.path.join(self.meshCaseDir, "log.surfaceFeatureEdges"))
            os.remove(os.path.join(self.meshCaseDir, "log.cartesianMesh"))

        with open(fname, 'w+') as f:
            source = ""
            if FoamCaseBuilder.utility.getFoamRuntime() != "BlueCFD":  # Runs inside own environment - no need to source
                source = readTemplate(os.path.join(self.templatePath, "helperFiles", "AllrunSource"),
                                      {"FOAMDIR": FoamCaseBuilder.utility.translatePath(FoamCaseBuilder.utility.getFoamDir())})

            head = readTemplate(os.path.join(self.templatePath, "helperFiles", "AllmeshPreamble"),
                                {"SOURCE": source})
            f.write(head)

            # Scale geometry, in mm, to meters
            f.write('runCommand surfaceTransformPoints -scale "(0.001 0.001 0.001)"'
                    + ' "{}.stl" "{}Scaled.stl"\n'.format(self.temp_file_geo, self.temp_file_geo))
            f.write('\n')

            if mesher_name == 'cartesianMesh':
                f.write('# Extract feature edges\n')
                f.write('runCommand surfaceFeatureEdges -angle 60 {}Scaled.stl {}_Geometry.fms\n'.format(self.temp_file_geo, self.part_obj.Name))
                f.write('\n')
                f.write('runCommand cartesianMesh\n')  # May in future extend to poly and tet mesh
                f.write('\n')

            # Create stl of FOAM mesh outside to view the object. Scaled from meter to mm to match the geometry.
            f.write('runCommand surfaceMeshTriangulate mesh_outside.stl\n')
            f.write('runCommand surfaceTransformPoints -scale "(1000 1000 1000)"'
                    + ' mesh_outside.stl mesh_outside.stl\n')
            f.write('\n')


        import stat
        s = os.stat(fname)
        os.chmod(fname, s.st_mode | stat.S_IEXEC)  # Update Allmesh permission - will fail silently on windows

    def write_part_file(self):
        # Using Mesh.export as exportStl does not support compound solids
        import Mesh
        objs = []
        print self.part_obj.Name
        objs.append(self.part_obj)
        Mesh.export(objs, self.temp_file_ast)  # Export ASCI stl file
        os.rename(self.temp_file_ast, self.temp_file_geo+'.stl')

    def setupMeshDict(self):
        fname = self.temp_file_meshDict
        fid = open(fname, 'w')

        fid.write(readTemplate(os.path.join(self.templatePath, "helperFiles", "meshDict"),
                               {"HEADER": readTemplate(os.path.join(self.templatePath, "helperFiles", "header"),
                                                       {"LOCATION": "system",
                                                        "FILENAME": "meshDict"}),
                                "FMSNAME":  self.part_obj.Name + '_Geometry.fms',
                                "CELLSIZE": self.clmax}))
        fid.close()

    def read_and_set_new_mesh(self):
        if not self.error:
            fem_mesh = Fem.read(os.path.join(self.meshCaseDir,'mesh_outside.stl'))
            self.mesh_obj.FemMesh = fem_mesh
            print('  The Part should have a pretty new FEM mesh!')
        else:
            print('No mesh was created.')

##  @}
