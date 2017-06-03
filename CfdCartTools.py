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
import FemMeshTools
import Units
import tempfile
import os
import shutil
import CfdTools
import math
import MeshPart

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

    def get_clmax(self):
        return self.clmax

    def get_tmp_file_paths(self,typeCart):
        tmpdir = tempfile.gettempdir()
        self.meshCaseDir = os.path.join(tmpdir, 'meshCase')
        self.constantDir = os.path.join(self.meshCaseDir, 'constant')
        if typeCart == "cfMesh":
            self.polyMeshDir = os.path.join(self.constantDir, 'polyMesh')
        elif typeCart == "snappyHexMesh":
            #surfaceTOPatch does not have an overwrite functionality therefore create a new folder at timestep.
            #However, if there is no changes to be made to the boundary then this time folder is not created.
            #Therefore doing a present check prior to sending off where the mesh directory is located.
            polyMeshDir = os.path.join(self.meshCaseDir,'1','polyMesh')
            if os.path.isfile(polyMeshDir):
                self.polyMeshDir = polyMeshDir
            else:
                self.polyMeshDir =  os.path.join(self.constantDir, 'polyMesh')
        self.triSurfaceDir = os.path.join(self.constantDir, 'triSurface')
        self.systemDir = os.path.join(self.meshCaseDir, 'system')

        self.templatePath = os.path.join(CfdTools.get_module_path(), "data", "defaults")

        self.temp_file_geo = os.path.join(self.constantDir, 'triSurface', self.part_obj.Name+'_Geometry')  # Rename
        self.temp_file_meshDict = os.path.join(self.systemDir, 'meshDict')
        self.temp_file_blockMeshDict = os.path.join(self.systemDir, 'blockMeshDict')
        self.temp_file_snappyMeshDict = os.path.join(self.systemDir, 'snappyHexMeshDict')
        self.temp_file_surfaceFeatureExtractDict = os.path.join(self.systemDir, 'surfaceFeatureExtractDict')


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
        #self.snappyRegionSTLNames = []
        #self.snappyRegionSubLink = {}
        #self.snappyRegionElemLin = {}
        self.snappyMeshRegions = {}
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

                        self.ele_length_map[mr_obj.Name] = mr_rellen * self.clmax * self.scale
                        self.ele_refinethick_map[mr_obj.Name] = self.scale*Units.Quantity(mr_obj.RefinementThickness).Value
                        self.ele_numlayer_map[mr_obj.Name] = mr_obj.NumberLayers
                        self.ele_expratio_map[mr_obj.Name] = mr_obj.ExpansionRatio
                        self.ele_firstlayerheight_map[mr_obj.Name] = self.scale*Units.Quantity(mr_obj.FirstLayerHeight).Value

                        # STL containing the faces in the reference list
                        # For long and many reasons related to snappy and baffles we cannot
                        # use multi-region .stl for creating baffles. Therefore exporting each
                        # mesh region face as an independent .stl surface. To not confuse cfMesh behaviour
                        # leaving cfMesh as is.
                        if self.mesh_obj.MeshUtility == "cfMesh":
                            f = open(os.path.join(self.triSurfaceDir, mr_obj.Name + '.stl'), 'w')
                            #f.write("solid {}\n".format(mr_obj.Name))

                        mr_obj.Name
                        snappyTemp = []
                        subTemp = []
                        print mr_obj.References
                        subC = -1
                        for sub in mr_obj.References:
                            subC+=1
                            # print(sub[0])  # Part the elements belongs to
                            elems_list = []
                            print sub[0].Name
                            elemC = -1
                            for elems in sub[1]:
                                elemC += 1
                                print elems
                                # print(elems)  # elems --> element
                                if not elems in elems_list:
                                    elt = sub[0].Shape.getElement(elems)
                                    if elt.ShapeType == 'Face':
                                        facemesh = MeshPart.meshFromShape(elt,
                                                                          LinearDeflection=self.mesh_obj.STLLinearDeflection)
                                        if self.mesh_obj.MeshUtility == "snappyHexMesh":
                                            #f = open(os.path.join(self.triSurfaceDir, mr_obj.Name+"Sub"+str(subC)+"Elem"+str(elemC) + '.stl'), 'w')
                                            f = open(os.path.join(self.triSurfaceDir, mr_obj.Name+sub[0].Name+elems+ '.stl'), 'w')
                                            #snappyTemp.append(mr_obj.Name+"Sub"+str(subC)+"Elem"+str(elemC))
                                            snappyTemp.append(mr_obj.Name+sub[0].Name+elems)
                                        f.write("solid {}\n".format(mr_obj.Name+"Sub"+str(subC)+"Elem"+str(elemC)))
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
                                        f.write("solid {}\n".format(mr_obj.Name+"Sub"+str(subC)+"Elem"+str(elemC)))

                                        # Similarity search for patch used in boundary layer meshing
                                        meshFaceList = self.mesh_obj.Part.Shape.Faces
                                        for (i, mf) in enumerate(meshFaceList):
                                            import FemMeshTools
                                            isSameGeo = FemMeshTools.is_same_geometry(elt, mf)
                                            if isSameGeo:  # Only one matching face
                                                sfN = self.mesh_obj.ShapeFaceNames[i]
                                                self.ele_meshpatch_map[mr_obj.Name].append(sfN)
                                        if self.mesh_obj.MeshUtility == "snappyHexMesh":
                                            f.close()
                                    else:
                                        FreeCAD.Console.PrintError(
                                            "Cartesian meshes only support surface refinement.\n")
                                else:
                                    FreeCAD.Console.PrintError(
                                        "The element {} has already been added.\n")
                        #f.write("endsolid {}\n".format(mr_obj.Name))
                        if self.mesh_obj.MeshUtility == "cfMesh":
                            f.close()
                        if self.mesh_obj.MeshUtility == "snappyHexMesh":
                            self.snappyMeshRegions[mr_obj.Name] = snappyTemp
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
        print('  {}'.format(self.ele_meshpatch_map))
        if self.mesh_obj.MeshUtility == "snappyHexMesh":
            #self.mesh_obj.snappyRegionInfo["snappyRegionSTLNames"] = self.snappyRegionSTLNames
            #self.mesh_obj.snappyRegionInfo["snappyRegionSubLink"] = self.snappyRegionSubLink
            #self.mesh_obj.snappyRegionInfo["snappyRegionElemLin"] = self.snappyRegionElemLin
            self.mesh_obj.snappyRegionInfo = self.snappyMeshRegions

        print self.mesh_obj.snappyRegionInfo
        #broken12

    def setupMeshCaseDir(self):
        """ Temporary mesh case directory """
        if os.path.isdir(self.meshCaseDir):
            shutil.rmtree(self.meshCaseDir)
        os.makedirs(self.meshCaseDir)
        os.makedirs(self.constantDir)
        os.makedirs(self.triSurfaceDir)

        shutil.copytree(os.path.join(self.templatePath, '_cfMesh', 'system'), self.systemDir)

    def automaticInsidePointDetect(self):
        #consider updating to something more elegant

        #Temporary note of importance:
        #The problem with snappy appears to be that the chosen internal point must remain internal
        #after the refinement regions as well. To be safe, the distance to check is chosen
        #to be approximately the size of the background mesh. 

        shape = self.part_obj.Shape
        vertices = self.part_obj.Shape.Vertexes
        stepSize = self.clmax*3.0

        #stepSize = self.clmax/self.scale*1.1

        #change = [FreeCAD.Vector(stepSize,stepSize,stepSize),
                  #FreeCAD.Vector(stepSize,-stepSize,stepSize),
                  #FreeCAD.Vector(-stepSize,stepSize,stepSize),
                  #FreeCAD.Vector(-stepSize,-stepSize,stepSize),
                  #FreeCAD.Vector(stepSize,stepSize,-stepSize),
                  #FreeCAD.Vector(stepSize,-stepSize,-stepSize),
                  #FreeCAD.Vector(-stepSize,stepSize,-stepSize),
                  #FreeCAD.Vector(-stepSize,-stepSize,-stepSize)]
        #for ii in range(len(vertices)):
            ##print "vertex",ii,vertices[ii], vertices[ii].Point
            #point = vertices[ii].Point
            #for jj in range(8):
                #pointCheck = point + change[jj]
                #result = shape.isInside(pointCheck,stepSize/1.1,False)
                #print pointCheck,result
                #if result:
                    #return pointCheck

        boundBox = self.part_obj.Shape.BoundBox
        errorSafetyFactor = 2.0
        if stepSize*errorSafetyFactor >= boundBox.XLength or stepSize*errorSafetyFactor >= boundBox.YLength or stepSize*errorSafetyFactor >= boundBox.ZLength:
            print stepSize
            #NOTE: need to put a proper error checker in place here
            someErrorNeededHereToSayCurrentChoiceInCharacteristicLengthIsTooLarge
        #extraX = boundBox.XLength*0.1
        #extraY = boundBox.YLength*0.1
        #extraZ = boundBox.ZLength*0.1
        x1 = boundBox.XMin
        x2 = boundBox.XMax
        y1 = boundBox.YMin
        y2 = boundBox.YMax
        z1 = boundBox.ZMin
        z2 = boundBox.ZMax
        import random
        while 1:
            x = random.uniform(x1,x2)
            y = random.uniform(y1,y2)
            z = random.uniform(z1,z2)
            pointCheck = FreeCAD.Vector(x,y,z)
            result = shape.isInside(pointCheck,stepSize,False)
            print pointCheck,result
            if result:
                #broek
                return pointCheck

    def createMeshScript(self, run_parallel, mesher_name, num_proc,cartMethod):
        print("Create Allmesh script ")

        fname = self.meshCaseDir + os.path.sep + "Allmesh"  # Replace

        if os.path.exists(fname):
            print("Warning: Overwrite existing Allmesh script and log files.")
            os.remove(os.path.join(self.meshCaseDir, "log.surfaceFeatureEdges"))
            os.remove(os.path.join(self.meshCaseDir, "log.cartesianMesh"))

        with open(fname, 'w+') as f:
            source = ""
            triSurfaceDir = os.path.join('constant', 'triSurface')
            if not CfdTools.getFoamRuntime() == "BlueCFD":  # Runs inside own environment - no need to source
                source = CfdTools.readTemplate(os.path.join(self.templatePath, "_helperFiles", "AllrunSource"),
                                      {"FOAMDIR": CfdTools.translatePath(CfdTools.getFoamDir())})

            head = CfdTools.readTemplate(os.path.join(self.templatePath, "_helperFiles", "AllmeshPreamble"),
                                {"SOURCE": source})
            f.write(head)

            if cartMethod == 'cfMesh' and mesher_name == 'cartesianMesh':
                f.write('# Extract feature edges\n')
                f.write('runCommand surfaceFeatureEdges -angle 60 {}_Geometry.stl {}_Geometry.fms'
                        '\n'.format(os.path.join(triSurfaceDir, self.part_obj.Name),
                                    self.part_obj.Name))
                f.write('\n')
                f.write('runCommand cartesianMesh\n')  # May in future extend to poly and tet mesh
                f.write('\n')


            elif cartMethod == 'snappyHexMesh':
                f.write('runCommand blockMesh \n')
                f.write('runCommand surfaceFeatureExtract \n')
                f.write('runCommand snappyHexMesh -overwrite\n')
                #f.write('runCommand surfaceToPatch -tol 1e-2 constant/triSurface/' + self.part_obj.Name + '_Geometry.stl \n')
                f.write('runCommand surfaceToPatch constant/triSurface/' + self.part_obj.Name + '_Geometry.stl \n')

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

    def setupMeshDict(self, utility):
        if utility == "cfMesh":
            fname = self.temp_file_meshDict
            fid = open(fname, 'w')

            fid.write(CfdTools.readTemplate(os.path.join(self.templatePath, "_helperFiles", "meshDict"),
                                   {"HEADER": CfdTools.readTemplate(os.path.join(self.templatePath, "_helperFiles", "header"),
                                                           {"LOCATION": "system",
                                                            "FILENAME": "meshDict"}),
                                    "FMSNAME":  self.part_obj.Name + '_Geometry.fms',
                                    "CELLSIZE": self.clmax*self.scale}))

            # Refinement surface
            if self.mesh_obj.MeshRegionList:
                surf = ""
                patch = ""
                for eleml in self.ele_length_map:
                    surf += CfdTools.readTemplate(
                        os.path.join(self.templatePath, "_helperFiles", "meshDictSurfRefineSurf"),
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

                    for face in self.ele_meshpatch_map[eleml]:
                        patch += CfdTools.readTemplate(
                            os.path.join(self.templatePath, "_helperFiles", "meshDictPatchBoundaryLayer"),
                            {"REGION": '\"' + face + '\"',
                             "NLAYER": numlayer,
                             "RATIO": expratio,
                             "FLHEIGHT": self.ele_firstlayerheight_map[eleml]})

                fid.write(CfdTools.readTemplate(os.path.join(self.templatePath, "_helperFiles", "meshDictSurfRefine"),
                                       {"SURFACE": surf}))
                fid.write(CfdTools.readTemplate(os.path.join(self.templatePath, "_helperFiles", "meshDictBoundaryLayer"),
                                       {"BLPATCHES": patch}))

            fid.close()

        if utility == "snappyHexMesh":
            boundBox = self.part_obj.Shape.BoundBox
            extraX = boundBox.XLength*0.1
            extraY = boundBox.YLength*0.1
            extraZ = boundBox.ZLength*0.1
            x1 = (boundBox.XMin - extraX)*self.scale
            x2 = (boundBox.XMax + extraX)*self.scale
            y1 = (boundBox.YMin - extraY)*self.scale
            y2 = (boundBox.YMax + extraY)*self.scale
            z1 = (boundBox.ZMin - extraZ)*self.scale
            z2 = (boundBox.ZMax + extraZ)*self.scale
            nX = math.ceil(boundBox.XLength/self.clmax)
            nY = math.ceil(boundBox.YLength/self.clmax)
            nZ = math.ceil(boundBox.ZLength/self.clmax)
            fname = self.temp_file_blockMeshDict
            fid = open(fname, 'w')

            fid.write(CfdTools.readTemplate(os.path.join(self.templatePath, "helperFiles", "snappyBlockMeshDict"),
                                   {"HEADER": CfdTools.readTemplate(os.path.join(self.templatePath, "_helperFiles", "header"),
                                                           {"LOCATION": "system",
                                                            "FILENAME": "blockMeshDict"}),
                                    "x1":   str(x1),
                                    "x2":   str(x2),
                                    "y1":   str(y1),
                                    "y2":   str(y2),
                                    "z1":   str(z1),
                                    "z2":   str(z2),
                                    "nX":   str(int(nX)),
                                    "nY":   str(int(nY)),
                                    "nZ":   str(int(nZ))}))
            fid.close()

            fname = self.temp_file_snappyMeshDict
            fid = open(fname, 'w')


            pointCheck = self.automaticInsidePointDetect()
            insideX = pointCheck[0]/1000.0
            insideY = pointCheck[1]/1000.0
            insideZ = pointCheck[2]/1000.0


            regionList = ""
            for i in self.mesh_obj.ShapeFaceNames:
                regionList += CfdTools.readTemplate(os.path.join(self.templatePath, "helperFiles", "snappySTLRegions"),
                                     {"REGIONNAME": i})

            STLGeometries = ""
            STLRefinementSurfaces = ""
            STLRefinementRegions = ""
            featureEdge = ""
            FeatureExtract = ""
            STLGeometries += CfdTools.readTemplate(os.path.join(self.templatePath, "helperFiles", "snappySTLSurfaceNameWithRegions"),
                                     {"STLNAME": self.part_obj.Name + '_Geometry.stl',
                                      "SURFACENAME": "MainSTL",
                                      "REGIONS": regionList})
            STLRefinementSurfaces += CfdTools.readTemplate(os.path.join(self.templatePath, "helperFiles", "snappySurfaceRefinementLevels"),
                                     {"SURFACENAME": "MainSTL",
                                      "LEVEL": str(0),
                                      "BAFFLEINFO": "",
                                      "FACEZONEINFO": ""})
            #REFINEMENTSURFACES#
            if self.mesh_obj.MeshRegionList:
                #print self.snappyRegionSTLNames
                #print self.snappyRegionSubLink
                #print self.snappyRegionElemLin
                for regionObj in self.mesh_obj.MeshRegionList:
                    for stlSurface in self.snappyMeshRegions[regionObj.Name]:
                        STLGeometries += CfdTools.readTemplate(os.path.join(self.templatePath, "helperFiles", "snappySTLSurfaceName"),
                                         {"STLNAME": stlSurface+ '.stl',
                                          "SURFACENAME": stlSurface})

                        if regionObj.snappedRefine:
                            facezoneInfo = "faceZone "+stlSurface+";"
                            if regionObj.internalBaffle:
                                baffleInfo = "faceType baffle;"
                                #baffleInfo += "\npatchInfo\n{\ntype patch;\n}"
                            else:
                                baffleInfo = "";
                            STLRefinementSurfaces += CfdTools.readTemplate(os.path.join(self.templatePath, "helperFiles", "snappySurfaceRefinementLevels"),
                                             {"SURFACENAME": stlSurface,
                                              "LEVEL": str(regionObj.snappyRefineLevel),
                                              "BAFFLEINFO": baffleInfo,
                                              "FACEZONEINFO": facezoneInfo})
                        else:
                            STLRefinementRegions += CfdTools.readTemplate(os.path.join(self.templatePath, "helperFiles", "snappyRefinementRegions"),
                                             {"NAME": stlSurface,
                                              "LEVEL": str(regionObj.snappyRefineLevel),
                                              "BAFFLEINFO": ""})
                    featureEdge += CfdTools.readTemplate(os.path.join(self.templatePath, "helperFiles", "edgeRefinementSnappyInner"),
                                     {"PartName":  stlSurface,
                                      "edgeRefineLevels": regionObj.localEdgeRefine})

                    FeatureExtract += CfdTools.readTemplate(os.path.join(self.templatePath, "helperFiles", "surfaceFeatureExtractInner"),
                                     {"STLName": stlSurface+ '.stl',
                                      "FeatureAngle":str(150)})

            ##FEATUREEDGEEXTRACTION
            featureEdge += CfdTools.readTemplate(os.path.join(self.templatePath, "helperFiles", "edgeRefinementSnappyInner"),
                                     {"PartName":  self.part_obj.Name + '_Geometry',
                                      "edgeRefineLevels":self.mesh_obj.edgeRefineLevels})

            fid.write(CfdTools.readTemplate(os.path.join(self.templatePath, "helperFiles", "snappyHexMeshDict"),
                                   {"HEADER": CfdTools.readTemplate(os.path.join(self.templatePath, "_helperFiles", "header"),
                                                           {"LOCATION": "system",
                                                            "FILENAME": "snappyHexMeshDict"}),
                                    #"STLNAME":  self.part_obj.Name + '_GeometryScaled.stl',
                                    "GEOMETRY":  STLGeometries,
                                    "REFINEMENTSURFACES": STLRefinementSurfaces,
                                    "REFINEMENTREGION": STLRefinementRegions, 
                                    "nCellsBetweenLevels": self.mesh_obj.nCellsBetweenLevels,
                                    "featureEdgeMesh": featureEdge,
                                    "PartName": self.part_obj.Name + '_Geometry',
                                    "insideX": str(insideX),
                                    "insideY": str(insideY),
                                    "insideZ": str(insideZ)}))
            fid.close()

            FeatureExtract += CfdTools.readTemplate(os.path.join(self.templatePath, "helperFiles", "surfaceFeatureExtractInner"),
                                     {"STLName":  self.part_obj.Name + '_Geometry.stl',
                                      "FeatureAngle":str(150)})

            fname = self.temp_file_surfaceFeatureExtractDict
            fid = open(fname,'w')
            fid.write(CfdTools.readTemplate(os.path.join(self.templatePath, "helperFiles", "surfaceFeatureExtractDict"),
                                   {"HEADER": CfdTools.readTemplate(os.path.join(self.templatePath, "_helperFiles", "header"),
                                                           {"LOCATION": "system",
                                                            "FILENAME": "surfaceFeatureExtractDict"}),
                                   "SURFACEFEATURE": FeatureExtract}))
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
        fid.write(CfdTools.readTemplate(os.path.join(self.templatePath, "_paraview", "pvScriptMesh"),
                               {"PATHPF": os.path.join(self.meshCaseDir, "p.foam"),
                                "CTYPE": case_type}))

        fid.close()

        return fname

##  @}
