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
import tempfile
import os
import shutil
import CfdTools
import math
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

        # Default to 2 % of bounding box characteristic length
        self.clmax = Units.Quantity(self.mesh_obj.CharacteristicLengthMax).Value
        if self.clmax == 0.0:
            shape = self.part_obj.Shape
            clBoundBox = math.sqrt(shape.BoundBox.XLength**2 + shape.BoundBox.YLength**2 + shape.BoundBox.ZLength**2)
            self.clmax = 0.02*clBoundBox

        self.clmax *= 0.001  # Scale characteristic length to meter (saved in mm)

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

        # STL file
        self.temp_file_ast = os.path.join(tmpdir, self.part_obj.Name + '_Geometry.ast')  # Extension for ASCI stl file
        self.temp_file_geo = os.path.join(self.constantDir, 'triSurface', self.part_obj.Name+'_Geometry')  # Rename
        # Mesh dictionary
        self.temp_file_meshDict = os.path.join(self.systemDir, 'meshDict')

    def get_group_data(self):  # Get from GMSH if needed in future
        print ('  Mesh group not active.')

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

            # Scale geometry, in mm, to meters. It is done at this point to ensure correct handeling when running
            # scripts from the terminal
            f.write('runCommand surfaceTransformPoints -scale "(0.001 0.001 0.001)"'
                    + ' "{}.stl" "{}Scaled.stl"\n'.format(self.temp_file_geo, self.temp_file_geo))
            f.write('\n')

            if mesher_name == 'cartesianMesh':
                f.write('# Extract feature edges\n')
                f.write('runCommand surfaceFeatureEdges -angle 60 {}Scaled.stl {}_Geometry.fms\n'.format(self.temp_file_geo, self.part_obj.Name))
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

        import MeshPart
        fullMeshFile = open(self.temp_file_geo+'.stl','w')
        for (i, objFaces) in enumerate(self.part_obj.Shape.Faces):
            faceName = ("face{}".format(i))
            shapeFaceNames.append(faceName)
            meshStl = MeshPart.meshFromShape(objFaces, LinearDeflection = self.mesh_obj.STLLinearDeflection)
            fullMeshFile.write("solid {}\n".format(faceName))
            for face in meshStl.Facets:
                f = face.PointIndices
                n = face.Normal
                fullMeshFile.write(" facet normal {} {} {}\n".format(n[0],n[1],n[2]))
                fullMeshFile.write("  outer loop\n")
                for i in range(3):
                    p = face.Points[i]
                    fullMeshFile.write("    vertex {} {} {}".format(p[0],p[1],p[2]))
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
        fid.close()

    def read_and_set_new_mesh(self):
        if not self.error:
            # NOTE: FemMesh does not support multi element stl
            # fem_mesh = Fem.read(os.path.join(self.meshCaseDir,'mesh_outside.stl'))
            # This is a temp work around to remove multiple solids, but is not very efficient
            import Mesh
            mesh = Mesh.Mesh(os.path.join(self.meshCaseDir,'mesh_outside.stl'))
            mesh.write(os.path.join(self.meshCaseDir,'mesh_outside.ast'))
            os.rename(os.path.join(self.meshCaseDir,'mesh_outside.ast'), os.path.join(self.meshCaseDir,'mesh_outside.stl'))
            fem_mesh = Fem.read(os.path.join(self.meshCaseDir,'mesh_outside.stl'))
            self.mesh_obj.FemMesh = fem_mesh
            print('  The Part should have a new mesh!')
        else:
            print('No mesh was created.')

##  @}
