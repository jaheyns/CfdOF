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

__title__ = "Tools for the work with GMSH mesher"
__author__ = "Bernd Hahnebach"
__url__ = "http://www.freecadweb.org"

## \addtogroup FEM
#  @{

import FreeCAD
import Fem
import FemMeshTools
import Units
import tempfile
import os
import shutil
import CfdTools
import math
import MeshPart
import FoamCaseBuilder.utility
from FoamCaseBuilder.utility import readTemplate

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
            clBoundBox = math.sqrt(shape.BoundBox.XLength**2 + shape.BoundBox.YLength**2 + shape.BoundBox.ZLength**2)
            self.clmax = 0.02*clBoundBox

        self.clmax *= self.scale  # Scale characteristic length to meter (saved in mm)

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

    def get_dimension(self):
        # Dimension
        # 3D cfMesh and snappyHexMesh, while in future cfMesh may support 2D
        if self.dimension == '3D':
            self.dimension = '3'
        else:
            FreeCAD.Console.PrintError('Could not retrive Dimension from shape type. Please choose dimension.')
            self.dimension = '3'
        print('  ElementDimension: ' + self.dimension)

    def get_tmp_file_paths(self):
        tmpdir = tempfile.gettempdir()
        self.meshCaseDir = os.path.join(tmpdir, 'meshCase')
        self.constantDir = os.path.join(self.meshCaseDir, 'constant')
        self.polyMeshDir = os.path.join(self.constantDir, 'polyMesh')
        self.triSurfaceDir = os.path.join(self.constantDir, 'triSurface')
        self.systemDir = os.path.join(self.meshCaseDir, 'system')

        self.templatePath = os.path.join(CfdTools.get_module_path(), "data", "defaults")

        self.temp_file_geo = os.path.join(self.constantDir, 'triSurface', self.part_obj.Name+'_Geometry')  # Rename
        self.temp_file_meshDict = os.path.join(self.systemDir, 'meshDict')

    def get_group_data(self):
        """ Mesh groups and groups of analysis member """
        if not self.mesh_obj.MeshGroupList:
            print ('  No mesh group objects.')

    def get_region_data(self):
        """ Mesh regions """
        self.ele_length_map = {}  # { 'mrNameString' : element length }
        self.ele_refinethick_map = {}  # { 'mrNameString' : refinement thickness }
        self.ele_firstlayerheight_map = {}  # { 'mrNameString' : first layer height }
        self.ele_numlayer_map = {}  # { 'mrNameString' : number of layers }
        self.ele_expratio_map = {}  # { 'mrNameString' : expansion ratio }
        self.ele_meshpatch_map = {}  # { 'mrNameString' : mesh patch }
        if not self.mesh_obj.MeshRegionList:
            print ('  No mesh regions.')
        else:
            print ('  Mesh regions, we need to get the elements.')
            if "Boolean" in self.part_obj.Name:
                err = "Cartesian meshes should not be generated for boolean split compounds."
                FreeCAD.Console.PrintError(err + "\n")
            for mr_obj in self.mesh_obj.MeshRegionList:
                if mr_obj.RelativeLength:
                    if mr_obj.References:

                        # Store parameters per region
                        mr_rellen = mr_obj.RelativeLength
                        if mr_rellen > 1.0:
                            mr_rellen = 1.0
                            FreeCAD.Console.PrintError(
                                "The meshregion: " + mr_obj.Name +
                                " should not use a relative length greater than unity.\n")
                        elif mr_rellen < 0.01:
                            mr_rellen = 0.01  # Relative length should not be less than 1/100 of base length
                            FreeCAD.Console.PrintError(
                                "The meshregion: " + mr_obj.Name +
                                " should not use a relative length smaller than 0.01.\n")

                        self.ele_length_map[mr_obj.Name] = mr_rellen * self.clmax
                        self.ele_refinethick_map[mr_obj.Name] = self.scale*Units.Quantity(mr_obj.RefinementThickness).Value
                        self.ele_numlayer_map[mr_obj.Name] = mr_obj.NumberLayers
                        self.ele_expratio_map[mr_obj.Name] = mr_obj.ExpansionRatio
                        self.ele_firstlayerheight_map[mr_obj.Name] = self.scale*Units.Quantity(mr_obj.FirstLayerHeight).Value

                        # STL containing the faces in the reference list
                        f = open(os.path.join(self.triSurfaceDir, mr_obj.Name + '.stl'), 'w')
                        f.write("solid {}\n".format(mr_obj.Name))

                        for sub in mr_obj.References:
                            # print(sub[0])  # Part the elements belongs to
                            elems_list = []
                            for elems in sub[1]:
                                # print(elems)  # elems --> element
                                if not elems in elems_list:
                                    elt = sub[0].Shape.getElement(elems)
                                    if elt.ShapeType == 'Face':
                                        facemesh = MeshPart.meshFromShape(elt,
                                                                          LinearDeflection=self.mesh_obj.STLLinearDeflection)
                                        for face in facemesh.Facets:
                                            f.write(" facet normal 0 0 0\n")
                                            f.write("  outer loop\n")
                                            for i in range(3):
                                                p = face.Points[i]
                                                f.write("    vertex {} {} {}".format(self.scale*p[0],
                                                                                     self.scale*p[1],
                                                                                     self.scale*p[2]))
                                                f.write("\n")
                                            f.write("  endloop\n")
                                            f.write(" endfacet\n")

                                        # Similarity search for patch used in boundary layer meshing
                                        meshFaceList = self.mesh_obj.Part.Shape.Faces
                                        self.ele_meshpatch_map[mr_obj.Name] = mr_obj.Name  # Temporary place holder
                                        for (i, mf) in enumerate(meshFaceList):
                                            import FemMeshTools
                                            isSameGeo = FemMeshTools.is_same_geometry(elt, mf)
                                            if isSameGeo:  # Only one matching face
                                                self.ele_meshpatch_map[mr_obj.Name] = self.mesh_obj.ShapeFaceNames[i]

                                    else:
                                        FreeCAD.Console.PrintError(
                                            "Cartesian meshes only support surface refinement.\n")
                                else:
                                    FreeCAD.Console.PrintError(
                                        "The element {} has already been added.\n")
                        f.write("endsolid {}\n".format(mr_obj.Name))
                        f.close()
                    else:
                        FreeCAD.Console.PrintError(
                            "The meshregion: " + mr_obj.Name + " is not used to create the mesh because "
                            "the reference list is empty.\n")
                else:
                    FreeCAD.Console.PrintError(
                        "The meshregion: " + mr_obj.Name + " is not used to create the mesh because the "
                        "CharacteristicLength is 0.0 mm.\n")
        print('  {}'.format(self.ele_length_map))
        # print('  {}'.format(self.ele_refinethick_map))
        # print('  {}'.format(self.ele_numlayer_map))
        # print('  {}'.format(self.ele_expratio_map))
        # print('  {}'.format(self.ele_meshpatch_map))

    def setupMeshCaseDir(self):
        """ Temporary mesh case directory """
        if os.path.isdir(self.meshCaseDir):
            shutil.rmtree(self.meshCaseDir)
        os.makedirs(self.meshCaseDir)
        os.makedirs(self.constantDir)
        os.makedirs(self.triSurfaceDir)

        shutil.copytree(os.path.join(self.templatePath, 'cfMesh', 'system'), self.systemDir)

    def createMeshScript(self, run_parallel, mesher_name, num_proc):
        print("Create Allmesh script ")

        fname = self.meshCaseDir + os.path.sep + "Allmesh"  # Replace

        if os.path.exists(fname):
            print("Warning: Overwrite existing Allmesh script and log files.")
            os.remove(os.path.join(self.meshCaseDir, "log.surfaceFeatureEdges"))
            os.remove(os.path.join(self.meshCaseDir, "log.cartesianMesh"))

        with open(fname, 'w+') as f:
            source = ""
            triSurfaceDir = os.path.join('constant', 'triSurface')
            if FoamCaseBuilder.utility.getFoamRuntime() != "BlueCFD":  # Runs inside own environment - no need to source
                source = readTemplate(os.path.join(self.templatePath, "helperFiles", "AllrunSource"),
                                      {"FOAMDIR": FoamCaseBuilder.utility.translatePath(FoamCaseBuilder.utility.getFoamDir())})

            head = readTemplate(os.path.join(self.templatePath, "helperFiles", "AllmeshPreamble"),
                                {"SOURCE": source})
            f.write(head)

            if mesher_name == 'cartesianMesh':
                f.write('# Extract feature edges\n')
                f.write('runCommand surfaceFeatureEdges -angle 60 {}_Geometry.stl {}_Geometry.fms'
                        '\n'.format(os.path.join(triSurfaceDir, self.part_obj.Name),
                                    self.part_obj.Name))
                f.write('\n')
                f.write('runCommand cartesianMesh\n')  # May in future extend to poly and tet mesh
                f.write('\n')

            # Create stl of FOAM mesh outside (in mm) to view the object in FreeCAD.
            f.write('runCommand surfaceMeshTriangulate mesh_outside.stl\n')
            f.write('runCommand surfaceTransformPoints -scale "(1000 1000 1000)"'
                    + ' mesh_outside.stl mesh_outside.stl\n')
            f.write('\n')

        import stat
        s = os.stat(fname)
        os.chmod(fname, s.st_mode | stat.S_IEXEC)  # Update Allmesh permission - will fail silently on windows

    def write_part_file(self):
        """ Construct multi-element STL based on mesh part faces. """
        # Check if part is a boolean segment
        if ("Boolean" in self.part_obj.Name) and self.mesh_obj.MeshUtility:
            FreeCAD.Console.PrintError('cfMesh and snappyHexMesh does not accept boolean segments.')

        shapeFaceNames = self.mesh_obj.ShapeFaceNames
        fullMeshFile = open(self.temp_file_geo+'.stl', 'w')
        for (i, objFaces) in enumerate(self.part_obj.Shape.Faces):
            faceName = ("face{}".format(i))
            shapeFaceNames.append(faceName)
            meshStl = MeshPart.meshFromShape(objFaces, LinearDeflection = self.mesh_obj.STLLinearDeflection)
            fullMeshFile.write("solid {}\n".format(faceName))
            for face in meshStl.Facets:
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

        self.mesh_obj.ShapeFaceNames = shapeFaceNames

    def setupMeshDict(self):
        fname = self.temp_file_meshDict
        fid = open(fname, 'w')

        fid.write(readTemplate(os.path.join(self.templatePath, "helperFiles", "meshDict"),
                               {"HEADER": readTemplate(os.path.join(self.templatePath, "helperFiles", "header"),
                                                       {"LOCATION": "system",
                                                        "FILENAME": "meshDict"}),
                                "FMSNAME":  self.part_obj.Name + '_Geometry.fms',
                                "CELLSIZE": self.clmax}))

        # Refinement surface
        if self.mesh_obj.MeshRegionList:
            surf = ""
            patch = ""
            for eleml in self.ele_length_map:
                surf += readTemplate(
                    os.path.join(self.templatePath, "helperFiles", "meshDictSurfRefineSurf"),
                    {"REGION": eleml,
                     "SIZE": self.ele_length_map[eleml],
                     "FILE": '\"'+os.path.join('constant', 'triSurface', eleml + '.stl\"'),
                     "THICK": self.ele_refinethick_map[eleml]})

                numlayer = int(1)  # Default to 1 layer
                if self.ele_numlayer_map[eleml] > 0:
                    numlayer = int(self.ele_numlayer_map[eleml])
                expratio = self.ele_expratio_map[eleml]
                # Limit expansion ratio to greater than 1.0 and less than 1.2
                expratio = min(1.2, max(1.0, expratio))

                patch += readTemplate(
                    os.path.join(self.templatePath, "helperFiles", "meshDictPatchBoundaryLayer"),
                    {"REGION": '\"' + self.ele_meshpatch_map[eleml] + '\"',
                     "NLAYER": numlayer,
                     "RATIO": expratio,
                     "FLHEIGHT": self.ele_firstlayerheight_map[eleml]})

            fid.write(readTemplate(os.path.join(self.templatePath, "helperFiles", "meshDictSurfRefine"),
                                   {"SURFACE": surf}))
            fid.write(readTemplate(os.path.join(self.templatePath, "helperFiles", "meshDictBoundaryLayer"),
                                   {"BLPATCHES": patch}))

        fid.close()

    def read_and_set_new_mesh(self):
        if not self.error:
            # NOTE: FemMesh does not support multi element stl
            # fem_mesh = Fem.read(os.path.join(self.meshCaseDir,'mesh_outside.stl'))
            # This is a temp work around to remove multiple solids, but is not very efficient
            import Mesh
            mesh = Mesh.Mesh(os.path.join(self.meshCaseDir, 'mesh_outside.stl'))
            mesh.write(os.path.join(self.meshCaseDir, 'mesh_outside.ast'))
            os.rename(os.path.join(self.meshCaseDir, 'mesh_outside.ast'),
                      os.path.join(self.meshCaseDir, 'mesh_outside.stl'))
            fem_mesh = Fem.read(os.path.join(self.meshCaseDir, 'mesh_outside.stl'))
            self.mesh_obj.FemMesh = fem_mesh
            print('  The Part should have a new mesh!')
        else:
            print('No mesh was created.')

    def createParaviewScript(self):
        """ Create python script for Paraview to view mesh. """
        fname = os.path.join(self.meshCaseDir, "pvScript.py")
        if os.path.exists(fname):
            print("Warning: Overwrite existing pvScript.py script")

        # Only supporting reconstructed meshes
        case_type = "Reconstructed Case"

        fid = open(fname, 'w')
        fid.write(readTemplate(os.path.join(self.templatePath, "paraview", "pvScriptMesh"),
                               {"PATHPF": os.path.join(self.meshCaseDir, "p.foam"),
                                "CTYPE": case_type}))

        fid.close()

        return fname

##  @}
