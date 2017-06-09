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

__title__ = "Tools for cartesian mesh generation using snappyHexMesh and cfMesh"
__author__ = "AB, JH, OO, Bernd Hahnebach"
__url__ = "http://www.freecadweb.org"

## \addtogroup FEM
#  @{

import FreeCAD
import Fem
import Units
import tempfile
import os
import shutil
import CfdTools
import math
import MeshPart
import TemplateBuilder

class CfdCartTools():
    def __init__(self, cart_mesh_obj, analysis=None):
        self.mesh_obj = cart_mesh_obj
        if analysis:
            self.analysis = analysis
            # group meshing turned on
        else:
            self.analysis = None
            # group meshing turned off

        self.part_obj = self.mesh_obj.Part  # Part to mesh
        self.scale = 0.001  # Scale mm to m

        # Default to 2 % of bounding box characteristic length
        self.clmax = Units.Quantity(self.mesh_obj.CharacteristicLengthMax).Value
        if self.clmax == 0.0:
            shape = self.part_obj.Shape
            cl_bound_box = math.sqrt(shape.BoundBox.XLength**2 + shape.BoundBox.YLength**2 + shape.BoundBox.ZLength**2)
            self.clmax = 0.02*cl_bound_box

        self.dimension = self.mesh_obj.ElementDimension

        # Algorithm2D
        # cfMesh supports 2D cartesian meshing but this is not yet implemented.
        algo2D = self.mesh_obj.Algorithm2D
        if algo2D == 'Cartesian':
            self.algorithm2D = '2'
        else:
            FreeCAD.Console.PrintError("Currently, only Cartesian is supported.\n")
            self.algorithm2D = '2'

        # Algorithm3D
        # known_mesh_algorithm_3D = ['Cartesian', 'Polymesh', 'Tetrahedral']
        # Snappy and cf support cartesian, while cf also supports tet and poly
        algo3D = self.mesh_obj.Algorithm2D
        if algo3D == 'Cartesian':
            self.algorithm3D = '1'
        else:
            FreeCAD.Console.PrintError("Currently, only Cartesian is supported.\n")
            self.algorithm3D = '1'

        shape_face_names = []
        for (i, f) in enumerate(self.part_obj.Shape.Faces):
            face_name = ("face{}".format(i))
            shape_face_names.append(face_name)
        self.mesh_obj.ShapeFaceNames = shape_face_names

        self.cf_settings = {}
        self.snappy_settings = {}

    def get_dimension(self):
        # Dimension
        # 3D cfMesh and snappyHexMesh, while in future cfMesh may support 2D
        if self.dimension == '3D':
            self.dimension = '3'
        else:
            FreeCAD.Console.PrintError('Could not retrive Dimension from shape type. Please choose dimension.')
            self.dimension = '3'
        print('  ElementDimension: ' + self.dimension)

    def get_clmax(self):
        return self.clmax

    # def get_tmp_file_paths(self, typeCart):
    def get_tmp_file_paths(self):
        tmpdir = tempfile.gettempdir()
        self.case_name = 'meshCase'
        self.meshCaseDir = os.path.join(tmpdir, self.case_name)
        self.constantDir = os.path.join(self.meshCaseDir, 'constant')
        self.polyMeshDir = os.path.join(self.constantDir, 'polyMesh')
        # if typeCart == "cfMesh":
        #     self.polyMeshDir = os.path.join(self.constantDir, 'polyMesh')
        # elif typeCart == "snappyHexMesh":
        #     # surfaceTOPatch does not have an overwrite functionality. It therefore will always create a new time step
        #     # folder. However, if there is no changes to be made to the boundary then this time folder is not created.
        #     polyMeshDir = os.path.join(self.meshCaseDir,'1','polyMesh')
        #     if os.path.isfile(polyMeshDir):
        #         self.polyMeshDir = polyMeshDir
        #     else:
        #         self.polyMeshDir =  os.path.join(self.constantDir, 'polyMesh')
        self.triSurfaceDir = os.path.join(self.constantDir, 'triSurface')
        self.systemDir = os.path.join(self.meshCaseDir, 'system')

        self.temp_file_geo = os.path.join(self.constantDir, 'triSurface', self.part_obj.Name+'_Geometry')

    def setup_mesh_case_dir(self):
        """ Create temporary mesh case directory """
        if os.path.isdir(self.meshCaseDir):
            shutil.rmtree(self.meshCaseDir)
        os.makedirs(self.meshCaseDir)
        os.makedirs(self.constantDir)
        os.makedirs(self.triSurfaceDir)
        os.makedirs(self.systemDir)

        self.temp_file_geo = os.path.join(self.constantDir, 'triSurface', self.part_obj.Name+'_Geometry')

    def get_group_data(self):
        """ Mesh groups and groups of analysis member """
        if not self.mesh_obj.MeshGroupList:
            print ('  No mesh group objects.')

    def get_region_data(self):
        """ Mesh regions """
        cf_settings = self.cf_settings
        cf_settings['MeshRegions'] = {}
        cf_settings = self.cf_settings
        cf_settings['BoundaryLayers'] = {}
        snappy_settings = self.snappy_settings
        snappy_settings['MeshRegions'] = {}

        self.boundary_layer_present = False  # NOTE: check if still needed

        from collections import defaultdict
        self.ele_meshpatch_map = defaultdict(list)
        if not self.mesh_obj.MeshRegionList:
            print ('  No mesh regions.')
        else:
            print ('  Mesh regions, we need to get the elements.')
            if "Boolean" in self.part_obj.Name:
                err = "Cartesian meshes should not be generated for boolean split compounds."
                FreeCAD.Console.PrintError(err + "\n")
            for mr_obj in self.mesh_obj.MeshRegionList:
                if mr_obj.RelativeLength:
                    # Store parameters per region
                    mr_rellen = mr_obj.RelativeLength
                    if mr_rellen > 1.0:
                        mr_rellen = 1.0
                        FreeCAD.Console.PrintError(
                            "The meshregion: {} should not use a relative length greater "
                            "than unity.\n".format(mr_obj.Name))
                    elif mr_rellen < 0.001:
                        mr_rellen = 0.001  # Relative length should not be less than 0.1% of base length
                        FreeCAD.Console.PrintError(
                            "The meshregion: {} should not use a relative length smaller "
                            "than 0.05.\n".format(mr_obj.Name))

                    tri_surface = ""
                    snappy_mesh_region_list = []
                    patch_list = []
                    for (si, sub) in enumerate(mr_obj.References):
                        # print(sub[0])  # Part the elements belongs to
                        for (ei, elems) in enumerate(sub[1]):
                            # print(elems)  # elems --> element
                            elt = sub[0].Shape.getElement(elems)
                            if elt.ShapeType == 'Face':
                                facemesh = MeshPart.meshFromShape(elt,
                                                                  LinearDeflection=self.mesh_obj.STLLinearDeflection)

                                tri_surface += "solid {}{}{}\n".format(mr_obj.Name, sub[0].Name, elems)
                                for face in facemesh.Facets:
                                    tri_surface += " facet normal 0 0 0\n"
                                    tri_surface += "  outer loop\n"
                                    for i in range(3):
                                        p = [i * self.scale for i in face.Points[i]]
                                        tri_surface += "    vertex {} {} {}\n".format(p[0], p[1], p[2])
                                    tri_surface += "  endloop\n"
                                    tri_surface += " endfacet\n"
                                tri_surface += "solid {}{}{}\n".format(mr_obj.Name, sub[0].Name, elems)

                                if self.mesh_obj.MeshUtility == 'snappyHexMesh' and mr_obj.Baffle:
                                    # Save baffle references or faces individually
                                    baffle = "{}{}{}".format(mr_obj.Name, sub[0].Name, elems)
                                    fid = open(os.path.join(self.triSurfaceDir, baffle + ".stl"), 'w')
                                    fid.write(tri_surface)
                                    fid.close()
                                    tri_surface = ""
                                    snappy_mesh_region_list.append(baffle)
                                elif self.mesh_obj.MeshUtility == 'cfMesh' and mr_obj.NumberLayers > 1:
                                    # Similarity search for patch used in boundary layer meshing
                                    meshFaceList = self.mesh_obj.Part.Shape.Faces
                                    for (i, mf) in enumerate(meshFaceList):
                                        import FemMeshTools
                                        isSameGeo = FemMeshTools.is_same_geometry(elt, mf)
                                        if isSameGeo and (mr_obj.NumberLayers > 1):  # Only one matching face
                                            sfN = self.mesh_obj.ShapeFaceNames[i]
                                            self.ele_meshpatch_map[mr_obj.Name].append(sfN)
                                            patch_list.append(self.mesh_obj.ShapeFaceNames[i])

                                            # Limit expansion ratio to greater than 1.0 and less than 1.2
                                            expratio = mr_obj.ExpansionRatio
                                            expratio = min(1.2, max(1.0, expratio))

                                            cf_settings['BoundaryLayers'][self.mesh_obj.ShapeFaceNames[i]] = {
                                                'NumberLayers': mr_obj.NumberLayers,
                                                'ExpansionRatio': expratio,
                                                'FirstLayerHeight': self.scale *
                                                                    Units.Quantity(mr_obj.FirstLayerHeight).Value
                                            }
                            else:
                                FreeCAD.Console.PrintError("Cartesian meshes only support surface refinement.\n")

                    if self.mesh_obj.MeshUtility == 'cfMesh' or not mr_obj.Baffle:
                        fid = open(os.path.join(self.triSurfaceDir, mr_obj.Name + '.stl'), 'w')
                        fid.write(tri_surface)
                        fid.close()

                    if self.mesh_obj.MeshUtility == 'cfMesh':
                        cf_settings['MeshRegions'][mr_obj.Label] = {
                            'RelativeLength': mr_rellen * self.clmax * self.scale,
                            'RefinementThickness': self.scale * Units.Quantity(
                                mr_obj.RefinementThickness).Value,
                        }

                    elif self.mesh_obj.MeshUtility == 'snappyHexMesh':
                        if not mr_obj.Baffle:
                            snappy_mesh_region_list.append(mr_obj.Name)

                        snappy_settings['MeshRegions'][mr_obj.Name] = {
                            'RegionName': snappy_mesh_region_list,
                            'RefinementLevel': mr_obj.RefinementLevel,
                            'EdgeRefinementLevel': mr_obj.RegionEdgeRefinement,
                            'Baffle': mr_obj.Baffle
                        }

                else:
                    FreeCAD.Console.PrintError(
                        "The meshregion: " + mr_obj.Name + " is not used to create the mesh because the "
                        "CharacteristicLength is 0.0 mm or the reference list is empty.\n")

    def automatic_inside_point_detect(self):
        # Snappy requires that the chosen internal point must remain internal during the meshing process and therefore
        # the meshing algorithm might fail if the point accidentally in a sliver fall between the mesh and the geometry.
        # As a safety measure, the check distance is chosen to be approximately the size of the background mesh.
        shape = self.part_obj.Shape
        step_size = self.clmax*2.5

        bound_box = self.part_obj.Shape.BoundBox
        error_safety_factor = 2.0
        if (step_size*error_safety_factor >= bound_box.XLength or
                        step_size*error_safety_factor >= bound_box.YLength or
                        step_size*error_safety_factor >= bound_box.ZLength):
            CfdTools.cfdError("Current choice in characteristic length of {} might be too large for automatic "
                              "internal point detection.".format(self.clmax))
        x1 = bound_box.XMin
        x2 = bound_box.XMax
        y1 = bound_box.YMin
        y2 = bound_box.YMax
        z1 = bound_box.ZMin
        z2 = bound_box.ZMax
        import random
        while 1:
            x = random.uniform(x1,x2)
            y = random.uniform(y1,y2)
            z = random.uniform(z1,z2)
            pointCheck = FreeCAD.Vector(x,y,z)
            result = shape.isInside(pointCheck,step_size,False)
            if result:
                return pointCheck

    def write_part_file(self):
        """ Construct multi-element STL based on mesh part faces. """
        if ("Boolean" in self.part_obj.Name) and self.mesh_obj.MeshUtility:
            FreeCAD.Console.PrintError('cfMesh and snappyHexMesh do not accept boolean segments.')

        fullMeshFile = open(self.temp_file_geo+'.stl', 'w')
        for (i, objFaces) in enumerate(self.part_obj.Shape.Faces):
            faceName = ("face{}".format(i))
            mesh_stl = MeshPart.meshFromShape(objFaces, LinearDeflection = self.mesh_obj.STLLinearDeflection)
            fullMeshFile.write("solid {}\n".format(faceName))
            for face in mesh_stl.Facets:
                n = face.Normal
                fullMeshFile.write(" facet normal {} {} {}\n".format(n[0], n[1], n[2]))
                fullMeshFile.write("  outer loop\n")
                for j in range(3):
                    p = face.Points[j]
                    fullMeshFile.write("    vertex {} {} {}".format(self.scale*p[0],
                                                                    self.scale*p[1],
                                                                    self.scale*p[2]))
                    fullMeshFile.write("\n")
                fullMeshFile.write("  endloop\n")
                fullMeshFile.write(" endfacet\n")
            fullMeshFile.write("endsolid {}\n".format(faceName))
        fullMeshFile.close()

    def read_and_set_new_mesh(self):
        if not self.error:
            # NOTE: FemMesh does not support multi element stl
            # fem_mesh = Fem.read(os.path.join(self.meshCaseDir,'mesh_outside.stl'))
            # This is a temp work around to remove multiple solids, but is not very efficient
            import Mesh
            stl = os.path.join(self.meshCaseDir, 'mesh_outside.stl')
            ast = os.path.join(self.meshCaseDir, 'mesh_outside.ast')
            mesh = Mesh.Mesh(stl)
            mesh.write(ast)
            os.remove(stl)
            os.rename(ast, stl)
            fem_mesh = Fem.read(stl)
            self.mesh_obj.FemMesh = fem_mesh
            print('  The Part should have a new mesh!')
        else:
            print('No mesh was created.')

    def write_mesh_case(self):
        """ Write_case() will collect case setings, and finally build a runnable case. """
        tmpdir = tempfile.gettempdir()
        FreeCAD.Console.PrintMessage("Populating mesh dictionaries in folder {}\n".format(tmpdir))
        _cwd = os.curdir

        # if not os.path.exists(tmpdir = tempfile.gettempdir()):
        #     raise IOError("Path {} does not exist.".format(tmpdir = tempfile.gettempdir()))
        os.chdir(tmpdir)  # pyFoam can not write to cwd if FreeCAD is started NOT from terminal

        if self.mesh_obj.MeshUtility == "cfMesh":
            self.cf_settings['ClMax'] = self.clmax*self.scale

            if len(self.cf_settings['MeshRegions']) > 0:
                self.cf_settings['BoundaryLayerPresent'] = True
            else:
                self.cf_settings['BoundaryLayerPresent'] = False

        elif self.mesh_obj.MeshUtility == "snappyHexMesh":
            bound_box = self.part_obj.Shape.BoundBox
            bC = 5  # Number of background mesh buffer cells
            x_min = (bound_box.XMin - bC*self.clmax)*self.scale
            x_max = (bound_box.XMax + bC*self.clmax)*self.scale
            y_min = (bound_box.YMin - bC*self.clmax)*self.scale
            y_max = (bound_box.YMax + bC*self.clmax)*self.scale
            z_min = (bound_box.ZMin - bC*self.clmax)*self.scale
            z_max = (bound_box.ZMax + bC*self.clmax)*self.scale
            cells_x = int(math.ceil(bound_box.XLength/self.clmax) + 2*bC)
            cells_y = int(math.ceil(bound_box.YLength/self.clmax) + 2*bC)
            cells_z = int(math.ceil(bound_box.ZLength/self.clmax) + 2*bC)

            snappy_settings = self.snappy_settings
            snappy_settings['BlockMesh'] = {
                "xMin": x_min,
                "xMax": x_max,
                "yMin": y_min,
                "yMax": y_max,
                "zMin": z_min,
                "zMax": z_max,
                "cellsX": cells_x,
                "cellsY": cells_y,
                "cellsZ": cells_z
            }

            inside_x = self.mesh_obj.PointInMesh.get('x')*self.scale
            inside_y = self.mesh_obj.PointInMesh.get('y')*self.scale
            inside_z = self.mesh_obj.PointInMesh.get('z')*self.scale

            shape_face_names_list = []
            for i in self.mesh_obj.ShapeFaceNames:
                shape_face_names_list.append(i)
            snappy_settings['ShapeFaceNames'] = shape_face_names_list
            snappy_settings['EdgeRefinementLevel'] = self.mesh_obj.EdgeRefinement
            snappy_settings['PointInMesh'] = {
                "x": inside_x,
                "y": inside_y,
                "z": inside_z
            }
            snappy_settings['CellsBetweenLevels'] = self.mesh_obj.CellsBetweenLevels
            if self.mesh_obj.NumberCores <= 1:
                self.mesh_obj.NumberCores = 1
                snappy_settings['ParallelMesh'] = False
            else:
                snappy_settings['ParallelMesh'] = True
            snappy_settings['NumberCores'] = self.mesh_obj.NumberCores

        try:  # Make sure we restore cwd after exception here
            # Perform initialisation here rather than __init__ in case of path changes
            self.template_path = os.path.join(CfdTools.get_module_path(), "data", "defaultsMesh")

            mesh_region_present = False
            if len(self.cf_settings['MeshRegions']) > 0 or len(self.snappy_settings['MeshRegions']) > 0:
                mesh_region_present = True

            self.settings = {
                'Name': self.part_obj.Name,
                'MeshPath': self.meshCaseDir,
                'TranslatedFoamPath': CfdTools.translatePath(CfdTools.getFoamDir()),
                'MeshUtility': self.mesh_obj.MeshUtility,
                'MeshRegionPresent': mesh_region_present,
                'CfSettings': self.cf_settings,
                'SnappySettings': self.snappy_settings
            }

            TemplateBuilder.TemplateBuilder(self.meshCaseDir, self.template_path, self.settings)

            # Update Allmesh permission - will fail silently on Windows
            fname = os.path.join(self.meshCaseDir, "Allmesh")
            import stat
            s = os.stat(fname)
            os.chmod(fname, s.st_mode | stat.S_IEXEC)

        except:
            raise
        finally:
            os.chdir(_cwd)  # Restore working dir
        FreeCAD.Console.PrintMessage("Successfully wrote meshCase to folder {}\n".format(tmpdir))

##  @}
