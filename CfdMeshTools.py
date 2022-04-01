# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2017 Johan Heyns (CSIR) <jheyns@csir.co.za>             *
# *   Copyright (c) 2017-2018 Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>     *
# *   Copyright (c) 2017 Alfred Bogaers (CSIR) <abogaers@csir.co.za>        *
# *   Copyright (c) 2019-2022 Oliver Oxtoby <oliveroxtoby@gmail.com>        *
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

import FreeCAD
from FreeCAD import Units
import os
import shutil
import CfdTools
import math
import MeshPart
import TemplateBuilder
import Part


class CfdMeshTools:
    def __init__(self, cart_mesh_obj):
        self.mesh_obj = cart_mesh_obj
        self.analysis = CfdTools.getParentAnalysisObject(self.mesh_obj)

        self.part_obj = self.mesh_obj.Part  # Part to mesh
        self.scale = 0.001  # Scale mm to m

        # Default to 2 % of bounding box characteristic length
        self.clmax = Units.Quantity(self.mesh_obj.CharacteristicLengthMax).Value
        if self.clmax <= 0.0:
            shape = self.part_obj.Shape
            cl_bound_mag = math.sqrt(shape.BoundBox.XLength**2 + shape.BoundBox.YLength**2 + shape.BoundBox.ZLength**2)
            cl_bound_min = min(min(shape.BoundBox.XLength, shape.BoundBox.YLength), shape.BoundBox.ZLength)
            self.clmax = min(0.02*cl_bound_mag, 0.4*cl_bound_min)  # Always in internal format, i.e. mm

        # Only used by gmsh - what purpose?
        self.clmin = 0.0

        self.dimension = self.mesh_obj.ElementDimension

        self.cf_settings = {}
        self.snappy_settings = {}
        self.gmsh_settings = {}
        self.extrusion_settings = {}

        self.error = False

        output_path = CfdTools.getOutputPath(self.analysis)
        self.getFilePaths(output_path)

        # 2D array of list of faces (index into shape) in each patch, indexed by [bc_id+1][meshregion_id+1]
        self.patch_faces = []
        # 2D array of names of each patch, indexed by [bc_id+1][meshregion_id+1]
        self.patch_names = []

        self.progressCallback = None

    def writeMesh(self):
        self.setupMeshCaseDir()
        CfdTools.cfdMessage("Exporting mesh refinement data ...\n")
        if self.progressCallback:
            self.progressCallback("Exporting mesh refinement data ...")
        self.processRefinements()
        self.processExtrusions()
        CfdTools.cfdMessage("Exporting the part surfaces ...\n")
        if self.progressCallback:
            self.progressCallback("Exporting the part surfaces ...")
        self.writePartFile()
        self.writeMeshCase()
        CfdTools.cfdMessage("Wrote mesh case to {}\n".format(self.meshCaseDir))
        if self.progressCallback:
            self.progressCallback("Mesh case written successfully")

    def processExtrusions(self):
        """ Find and process any extrusion objects """

        twoD_extrusion_objs = []
        other_extrusion_objs = []
        mesh_refinements = CfdTools.getMeshRefinementObjs(self.mesh_obj)
        self.extrusion_settings['ExtrusionsPresent'] = False
        self.extrusion_settings['ExtrudeTo2D'] = False
        self.extrusion_settings['Extrude2DPlanar'] = False
        for mr in mesh_refinements:
            if mr.Extrusion:
                self.extrusion_settings['ExtrusionsPresent'] = True
                if mr.ExtrusionType == '2DPlanar' or mr.ExtrusionType == '2DWedge':
                    twoD_extrusion_objs.append(mr)
                else:
                    other_extrusion_objs.append(mr)
                if mr.ExtrusionType == '2DPlanar':
                    self.extrusion_settings['Extrude2DPlanar'] = True

        if len(twoD_extrusion_objs) > 1:
            raise RuntimeError("For 2D meshing, there must be exactly one 2D mesh extrusion object.")
        elif len(twoD_extrusion_objs) == 1:
            self.extrusion_settings['ExtrudeTo2D'] = True
        all_extrusion_objs = other_extrusion_objs + twoD_extrusion_objs  # Ensure 2D extrusion happens last

        self.extrusion_settings['Extrusions'] = []
        for extrusion_obj in all_extrusion_objs:
            extrusion_shape = extrusion_obj.Shape
            this_extrusion_settings = {}
            if len(extrusion_shape.Faces) == 0:
                raise RuntimeError("Extrusion object '{}' is empty.".format(extrusion_obj.Label))

            this_extrusion_settings['KeepExistingMesh'] = extrusion_obj.KeepExistingMesh
            if extrusion_obj.ExtrusionType == '2DPlanar' or extrusion_obj.ExtrusionType == '2DWedge':
                this_extrusion_settings['KeepExistingMesh'] = False
                all_faces_planar = True
                for faces in extrusion_shape.Faces:
                    if not isinstance(faces.Surface, Part.Plane):
                        all_faces_planar = False
                        break
                if not all_faces_planar:
                    raise RuntimeError("2D mesh extrusion surface must be a flat plane.")

            normal = extrusion_shape.Faces[0].Surface.Axis
            normal.multiply(1.0/normal.Length)
            this_extrusion_settings['Normal'] = (normal.x, normal.y, normal.z)
            this_extrusion_settings['ExtrusionType'] = extrusion_obj.ExtrusionType

            # Get the names of the faces being extruded
            mri = mesh_refinements.index(extrusion_obj)
            efl = []
            for l, ff in enumerate(self.patch_faces):
                f = ff[mri+1]
                if len(f):
                    efl.append(self.patch_names[l][mri+1])

            if not efl:
                raise RuntimeError("Extrusion patch for '{}' could not be found in the shape being meshed.".format(
                    extrusion_obj.Label))
            this_extrusion_settings['FrontFaceList'] = tuple(efl)
            this_extrusion_settings['BackFace'] = efl[0]+'_back'

            this_extrusion_settings['Distance'] = extrusion_obj.ExtrusionThickness.getValueAs('m')
            this_extrusion_settings['Angle'] = extrusion_obj.ExtrusionAngle.getValueAs('deg')
            this_extrusion_settings['NumLayers'] = extrusion_obj.ExtrusionLayers
            this_extrusion_settings['ExpansionRatio'] = extrusion_obj.ExtrusionRatio
            this_extrusion_settings['AxisPoint'] = tuple(p for p in extrusion_obj.ExtrusionAxisPoint)

            axis_direction = extrusion_obj.ExtrusionAxisDirection

            # Flip axis if necessary to go in same direction as patch normal (otherwise negative volume cells result)
            if len(extrusion_shape.Faces) > 0:
                in_plane_vector = extrusion_shape.Faces[0].CenterOfMass-extrusion_obj.ExtrusionAxisPoint
                extrusion_normal = extrusion_obj.ExtrusionAxisDirection.cross(in_plane_vector)
                face_normal = extrusion_shape.Faces[0].normalAt(0.5, 0.5)
                if extrusion_normal.dot(face_normal) < 0:
                    axis_direction = -axis_direction

            this_extrusion_settings['AxisDirection'] = tuple(d for d in axis_direction)

            self.extrusion_settings['Extrusions'].append(this_extrusion_settings)

    def getClmax(self):
        return Units.Quantity(self.clmax, Units.Length)

    def getFilePaths(self, output_dir):
        if not hasattr(self.mesh_obj, 'CaseName'):  # Backward compat
            self.mesh_obj.CaseName = 'meshCase'
        self.case_name = self.mesh_obj.CaseName
        self.meshCaseDir = os.path.join(output_dir, self.case_name)
        self.constantDir = os.path.join(self.meshCaseDir, 'constant')
        self.polyMeshDir = os.path.join(self.constantDir, 'polyMesh')
        self.triSurfaceDir = os.path.join(self.constantDir, 'triSurface')
        self.gmshDir = os.path.join(self.meshCaseDir, 'gmsh')
        self.systemDir = os.path.join(self.meshCaseDir, 'system')

        if self.mesh_obj.MeshUtility == "gmsh":
            self.temp_file_shape = os.path.join(self.gmshDir, self.part_obj.Name +"_Geometry.brep")
            self.temp_file_geo = os.path.join(self.gmshDir, self.part_obj.Name +"_Geometry.geo")
            self.temp_file_mesh = os.path.join(self.gmshDir, self.part_obj.Name + '_Geometry.msh')
        else:
            self.temp_file_geo = os.path.join(self.constantDir, 'triSurface', self.part_obj.Name + '_Geometry.stl')

    def setupMeshCaseDir(self):
        """ Create temporary mesh case directory """
        if os.path.isdir(self.meshCaseDir):
            shutil.rmtree(self.meshCaseDir)
        os.makedirs(self.meshCaseDir)
        os.makedirs(self.constantDir)
        os.makedirs(self.triSurfaceDir)
        os.makedirs(self.gmshDir)
        os.makedirs(self.systemDir)

    def processRefinements(self):
        """ Process mesh refinements """

        mr_objs = CfdTools.getMeshRefinementObjs(self.mesh_obj)

        cf_settings = self.cf_settings
        cf_settings['MeshRegions'] = {}
        cf_settings['BoundaryLayers'] = {}
        cf_settings['InternalRegions'] = {}
        snappy_settings = self.snappy_settings
        snappy_settings['MeshRegions'] = {}
        snappy_settings['InternalRegions'] = {}

        # Make list of all faces in meshed shape with original index
        mesh_face_list = list(zip(self.mesh_obj.Part.Shape.Faces, range(len(self.mesh_obj.Part.Shape.Faces))))

        # Make list of all boundary references
        CfdTools.cfdMessage("Matching boundary patches\n")
        boundary_face_list = []
        bc_group = None
        analysis_obj = CfdTools.getParentAnalysisObject(self.mesh_obj)
        if not analysis_obj:
            analysis_obj = CfdTools.getActiveAnalysis()
        if analysis_obj:
            bc_group = CfdTools.getCfdBoundaryGroup(analysis_obj)
        for bc_id, bc_obj in enumerate(bc_group):
            for ri, ref in enumerate(bc_obj.ShapeRefs):
                try:
                    bf = CfdTools.resolveReference(ref)
                except RuntimeError as re:
                    raise RuntimeError("Error processing boundary condition {}: {}".format(bc_obj.Label, str(re)))
                for si, s in enumerate(bf):
                    boundary_face_list += [(sf, (bc_id, ri, si)) for sf in s[0].Faces]

        # Match them up to faces in the main geometry
        bc_matched_faces = CfdTools.matchFaces(boundary_face_list, mesh_face_list)

        # Check for and filter duplicates
        bc_match_per_shape_face = [-1] * len(mesh_face_list)
        for k in range(len(bc_matched_faces)):
            match = bc_matched_faces[k][1]
            prev_k = bc_match_per_shape_face[match]
            if prev_k >= 0:
                nb, ri, si = bc_matched_faces[k][0]
                nb2, ri2, si2 = bc_matched_faces[prev_k][0]
                bc = bc_group[nb]
                bc2 = bc_group[nb2]
                CfdTools.cfdWarning(
                    "Boundary '{}' reference {}:{} also assigned as "
                    "boundary '{}' reference {}:{} - ignoring duplicate\n".format(
                        bc.Label, bc.ShapeRefs[ri][0].Name, bc.ShapeRefs[ri][1][si],
                        bc2.Label, bc.ShapeRefs[ri][0].Name, bc.ShapeRefs[ri][1][si]))
            else:
                bc_match_per_shape_face[match] = k

        # Match relevant mesh regions to shape faces: boundary layer mesh regions for cfMesh, and extrusion patches
        # Normal surface refinements are written as separate surfaces so need not be matched
        CfdTools.cfdMessage("Matching mesh refinement regions\n")
        mr_face_list = []
        for mr_id, mr_obj in enumerate(mr_objs):
            if mr_obj.Extrusion or (
                    self.mesh_obj.MeshUtility == 'cfMesh' and not mr_obj.Internal and mr_obj.NumberLayers > 1):
                for ri, r in enumerate(mr_obj.ShapeRefs):
                    try:
                        bf = CfdTools.resolveReference(r)
                    except RuntimeError as re:
                        raise RuntimeError("Error processing mesh refinement {}: {}".format(
                            mr_obj.Label, str(re)))
                    for si, s in enumerate(bf):
                        mr_face_list += [(f, (mr_id, ri, si)) for f in s[0].Faces]

        # Match them up
        mr_matched_faces = CfdTools.matchFaces(mr_face_list, mesh_face_list)

        # Check for and filter duplicates
        bl_match_per_shape_face = [-1] * len(mesh_face_list)
        for k in range(len(mr_matched_faces)):
            match = mr_matched_faces[k][1]
            prev_k = bl_match_per_shape_face[match]
            if prev_k >= 0:
                nr, ri, si = mr_matched_faces[k][0]
                nr2, ri2, si2 = mr_matched_faces[prev_k][0]
                CfdTools.cfdWarning(
                    "Mesh refinement '{}' reference {}:{} also assigned as "
                    "mesh refinement '{}' reference {}:{} - ignoring duplicate\n".format(
                        mr_objs[nr].Label, mr_objs[nr].ShapeRefs[ri][0].Name, mr_objs[nr].ShapeRefs[ri][1][si],
                        mr_objs[nr2].Label, mr_objs[nr2].ShapeRefs[ri2][0].Name, mr_objs[nr2].ShapeRefs[ri2][1][si2]))
            else:
                bl_match_per_shape_face[match] = k

        self.patch_faces = []
        self.patch_names = []
        for k in range(len(bc_group)+1):
            self.patch_faces.append([])
            self.patch_names.append([])
            for l in range(len(mr_objs)+1):
                self.patch_faces[k].append([])
                self.patch_names[k].append("patch_"+str(k)+"_"+str(l))
        for i in range(len(mesh_face_list)):
            k = bc_match_per_shape_face[i]
            l = bl_match_per_shape_face[i]
            nb = -1
            nr = -1
            if k >= 0:
                nb, bri, bsi = bc_matched_faces[k][0]
            if l >= 0:
                nr, rri, ssi = mr_matched_faces[l][0]
            self.patch_faces[nb+1][nr+1].append(i)

        # For gmsh, match mesh refinement with vertices in original mesh
        mr_matched_vertices = []
        if self.mesh_obj.MeshUtility == 'gmsh':
            # Make list of all vertices in meshed shape with original index
            mesh_vertices_list = list(
                zip(self.mesh_obj.Part.Shape.Vertexes, range(len(self.mesh_obj.Part.Shape.Vertexes))))

            CfdTools.cfdMessage("Matching mesh refinements\n")
            mr_vertices_list = []
            for mr_id, mr_obj in enumerate(mr_objs):
                if not mr_obj.Internal:
                    for ri, r in enumerate(mr_obj.ShapeRefs):
                        try:
                            bf = CfdTools.resolveReference(r)
                        except RuntimeError as re:
                            raise RuntimeError("Error processing mesh refinement {}: {}".format(
                                mr_obj.Label, str(re)))
                        for si, s in enumerate(bf):
                            mr_vertices_list += [(v, (mr_id, ri, si)) for v in s[0].Vertexes]

            mr_matched_vertices = CfdTools.matchFaces(mr_vertices_list, mesh_vertices_list)
            self.ele_length_map = {}
            self.ele_node_map = {}

        # Additionally for snappy, match baffles to any surface mesh refinements
        # as well as matching each surface mesh refinement region to boundary conditions
        bc_mr_matched_faces = []
        mr_face_list = []
        if self.mesh_obj.MeshUtility == 'snappyHexMesh':
            CfdTools.cfdMessage("Matching surface geometries\n")
            for mr_id, mr_obj in enumerate(mr_objs):
                if not mr_obj.Internal:
                    for ri, r in enumerate(mr_obj.ShapeRefs):
                        try:
                            bf = CfdTools.resolveReference(r)
                        except RuntimeError as re:
                            raise RuntimeError("Error processing mesh refinement {}: {}".format(
                                mr_obj.Label, str(re)))
                        for si, s in enumerate(bf):
                            mr_face_list += [(f, (mr_id, ri, si)) for f in s[0].Faces]

            # Match mesh regions to the boundary conditions, to identify boundary conditions on supplementary
            # geometry (including on baffles)
            bc_mr_matched_faces = CfdTools.matchFaces(boundary_face_list, mr_face_list)

        for bc_id, bc_obj in enumerate(bc_group):
            if bc_obj.BoundaryType == 'baffle':
                baffle_matches = [m for m in bc_mr_matched_faces if m[0][0] == bc_id]
                mr_match_per_baffle_ref = []
                for r in bc_obj.ShapeRefs:
                    mr_match_per_baffle_ref += [[-1]*len(r[1])]
                for m in baffle_matches:
                    mr_match_per_baffle_ref[m[0][1]][m[0][2]] = m[1][0]
                # For each mesh region, the refs that are part of this baffle
                baffle_patch_refs = [[] for ri in range(len(mr_objs)+1)]
                for ri, mr in enumerate(mr_match_per_baffle_ref):
                    for si, mri in enumerate(mr_match_per_baffle_ref[ri]):
                        baffle_patch_refs[mri+1].append((bc_obj.ShapeRefs[ri][0], (bc_obj.ShapeRefs[ri][1][si],)))

                # Write these geometries
                for ri, refs in enumerate(baffle_patch_refs):
                    try:
                        shape = CfdTools.makeShapeFromReferences(refs)
                    except RuntimeError as re:
                        raise RuntimeError("Error processing baffle {}: {}".format(
                            bc_obj.Label, str(re)))
                    solid_name = bc_obj.Name + "_" + str(ri)
                    if shape:
                        CfdTools.cfdMessage("Triangulating baffle {}, section {} ...".format(bc_obj.Label, ri))
                        facemesh = MeshPart.meshFromShape(
                            shape, LinearDeflection=self.mesh_obj.STLLinearDeflection)

                        CfdTools.cfdMessage(" writing to file\n")
                        with open(os.path.join(self.triSurfaceDir, solid_name + '.stl'), 'w') as fid:
                            CfdTools.writePatchToStl(solid_name, facemesh, fid, self.scale)

                        if ri > 0:  # The parts of the baffle corresponding to a surface mesh region obj
                            mr_obj = mr_objs[ri-1]
                            refinement_level = CfdTools.relLenToRefinementLevel(mr_obj.RelativeLength)
                            edge_level = CfdTools.relLenToRefinementLevel(mr_obj.RegionEdgeRefinement)
                        else:  # The parts of the baffle with no refinement obj
                            refinement_level = 0
                            edge_level = 0
                        snappy_settings['MeshRegions'][solid_name] = {
                            'RefinementLevel': refinement_level,
                            'EdgeRefinementLevel': edge_level,
                            'MaxRefinementLevel': max(refinement_level, edge_level),
                            'Baffle': True
                        }

        mr_matched_faces = []
        if self.mesh_obj.MeshUtility == 'snappyHexMesh':
            # Match mesh regions to the primary geometry
            mr_matched_faces = CfdTools.matchFaces(mr_face_list, mesh_face_list)

        for mr_id, mr_obj in enumerate(mr_objs):
            Internal = mr_obj.Internal
            mr_rellen = mr_obj.RelativeLength
            if mr_rellen > 1.0:
                mr_rellen = 1.0
                FreeCAD.Console.PrintError(
                    "The mesh refinement region '{}' should not use a relative length greater "
                    "than unity.\n".format(mr_obj.Name))
            elif mr_rellen < 0.001:
                mr_rellen = 0.001  # Relative length should not be less than 0.1% of base length
                FreeCAD.Console.PrintError(
                    "The mesh refinement region '{}' should not use a relative length smaller "
                    "than 0.001.\n".format(mr_obj.Name))

            if self.mesh_obj.MeshUtility == 'gmsh':
                # Generate element maps for gmsh
                if not Internal:
                    mesh_vertex_idx = [mf[1] for mf in mr_matched_vertices if mf[0][0] == mr_id]
                    self.ele_length_map[mr_obj.Name] = mr_rellen*self.clmax
                    self.ele_node_map[mr_obj.Name] = mesh_vertex_idx
            else:
                # Find any matches with boundary conditions; mark those matching baffles for removal
                bc_matches = [m for m in bc_mr_matched_faces if m[1][0] == mr_id]
                bc_match_per_mr_ref = []
                for ri, r in enumerate(mr_obj.ShapeRefs):
                    bc_match_per_mr_ref.append([-1]*len(r[1]))
                for m in bc_matches:
                    bc_match_per_mr_ref[m[1][1]][m[1][2]] = -2 if bc_group[m[0][0]].BoundaryType == 'baffle' else m[0][0]

                # Unmatch those in primary geometry
                main_geom_matches = [m for m in mr_matched_faces if m[0][0] == mr_id]
                for m in main_geom_matches:
                    bc_match_per_mr_ref[m[0][1]][m[0][2]] = -1

                # For each boundary, the refs that are part of this mesh region
                mr_patch_refs = [[] for ri in range(len(bc_group)+1)]
                for ri, m in enumerate(bc_match_per_mr_ref):
                    for si, bci in enumerate(m):
                        if bci > -2:
                            mr_patch_refs[bci+1].append((mr_obj.ShapeRefs[ri][0], (mr_obj.ShapeRefs[ri][1][si],)))

                # Loop over and write the sub-sections of this mesh object
                for bi in range(len(mr_patch_refs)):
                    if len(mr_patch_refs[bi]) and not mr_obj.Extrusion:
                        if bi == 0:
                            mr_patch_name = mr_obj.Name
                        else:
                            mr_patch_name = self.patch_names[bi][mr_id+1]

                        CfdTools.cfdMessage("Triangulating mesh refinement region {}, section {} ...".format(
                            mr_obj.Label, bi))

                        try:
                            shape = CfdTools.makeShapeFromReferences(mr_patch_refs[bi])
                        except RuntimeError as re:
                            raise RuntimeError("Error processing mesh refinement region {}: {}".format(
                                mr_obj.Label, str(re)))
                        if shape:
                            facemesh = MeshPart.meshFromShape(shape, LinearDeflection=self.mesh_obj.STLLinearDeflection)

                            CfdTools.cfdMessage(" writing to file\n")
                            with open(os.path.join(self.triSurfaceDir, mr_patch_name + '.stl'), 'w') as fid:
                                CfdTools.writePatchToStl(mr_patch_name, facemesh, fid, self.scale)

                        if self.mesh_obj.MeshUtility == 'cfMesh':
                            if not Internal:
                                cf_settings['MeshRegions'][mr_patch_name] = {
                                    'RelativeLength': mr_rellen * self.clmax * self.scale,
                                    'RefinementThickness': self.scale * Units.Quantity(
                                        mr_obj.RefinementThickness).Value,
                                }
                            else:
                                cf_settings['InternalRegions'][mr_obj.Name] = {
                                    'RelativeLength': mr_rellen * self.clmax * self.scale
                                }

                        elif self.mesh_obj.MeshUtility == 'snappyHexMesh':
                            refinement_level = CfdTools.relLenToRefinementLevel(mr_obj.RelativeLength)
                            if not Internal:
                                edge_level = CfdTools.relLenToRefinementLevel(mr_obj.RegionEdgeRefinement)
                                snappy_settings['MeshRegions'][mr_patch_name] = {
                                    'RefinementLevel': refinement_level,
                                    'EdgeRefinementLevel': edge_level,
                                    'MaxRefinementLevel': max(refinement_level, edge_level),
                                    'Baffle': False
                                }
                            else:
                                snappy_settings['InternalRegions'][mr_patch_name] = {
                                    'RefinementLevel': refinement_level
                                }

            # In addition, for cfMesh, record matched boundary layer patches
            if self.mesh_obj.MeshUtility == 'cfMesh' and mr_obj.NumberLayers > 1 and \
                    not Internal and not mr_obj.Extrusion:
                for k in range(len(self.patch_faces)):
                    if len(self.patch_faces[k][mr_id+1]):
                        # Limit expansion ratio to greater than 1.0 and less than 1.2
                        expratio = mr_obj.ExpansionRatio
                        expratio = min(1.2, max(1.0, expratio))

                        cf_settings['BoundaryLayers'][self.patch_names[k][mr_id+1]] = {
                            'NumberLayers': mr_obj.NumberLayers,
                            'ExpansionRatio': expratio,
                            'FirstLayerHeight': self.scale *
                                                Units.Quantity(mr_obj.FirstLayerHeight).Value
                        }

    def automaticInsidePointDetect(self):
        # Snappy requires that the chosen internal point must remain internal during the meshing process and therefore
        # the meshing algorithm might fail if the point accidentally falls in a sliver between the mesh and the geometry
        # As a safety measure, the check distance is chosen to be approximately the size of the background mesh.
        shape = self.part_obj.Shape
        step_size = self.clmax*2.5

        bound_box = self.part_obj.Shape.BoundBox
        error_safety_factor = 2.0
        if (step_size*error_safety_factor >= bound_box.XLength or
                        step_size*error_safety_factor >= bound_box.YLength or
                        step_size*error_safety_factor >= bound_box.ZLength):
            CfdTools.cfdErrorBox("Current choice in characteristic length of {} might be too large for automatic "
                                 "internal point detection.".format(self.clmax))
        x1 = bound_box.XMin
        x2 = bound_box.XMax
        y1 = bound_box.YMin
        y2 = bound_box.YMax
        z1 = bound_box.ZMin
        z2 = bound_box.ZMax
        import random
        if not shape.isClosed():
            CfdTools.cfdErrorBox("Can not find an internal point as shape is not closed - please specify manually.")
            return None
        for i in range(100):
            x = random.uniform(x1,x2)
            y = random.uniform(y1,y2)
            z = random.uniform(z1,z2)
            pointCheck = FreeCAD.Vector(x,y,z)
            result = shape.isInside(pointCheck, step_size, False)
            if result:
                return pointCheck
        CfdTools.cfdErrorBox("Failed to find an internal point - please specify manually.")
        return None

    def writePartFile(self):
        """ Construct multi-element STL based on mesh part faces. """
        if self.mesh_obj.MeshUtility == "gmsh":
            self.part_obj.Shape.exportBrep(self.temp_file_shape)
        else:
            with open(self.temp_file_geo, 'w') as fid:
                for k in range(len(self.patch_faces)):
                    for l in range(len(self.patch_faces[k])):
                        patch_faces = self.patch_faces[k][l]
                        patch_name = self.patch_names[k][l]
                        if len(patch_faces):
                            # Put together the faces making up this patch; mesh them and output to file
                            patch_shape = Part.makeCompound([self.mesh_obj.Part.Shape.Faces[f] for f in patch_faces])
                            CfdTools.cfdMessage(
                                "Triangulating part {}, patch {} ...".format(self.part_obj.Label, patch_name))
                            mesh_stl = MeshPart.meshFromShape(
                                patch_shape, LinearDeflection=self.mesh_obj.STLLinearDeflection)
                            CfdTools.cfdMessage(" writing to file\n")
                            CfdTools.writePatchToStl(patch_name, mesh_stl, fid, self.scale)

    def loadSurfMesh(self):
        if not self.error:
            # NOTE: FemMesh does not support multi element stl
            # fem_mesh = Fem.read(os.path.join(self.meshCaseDir,'mesh_outside.stl'))
            # This is a temp work around to remove multiple solids, but is not very efficient
            import Mesh
            import Fem
            stl = os.path.join(self.meshCaseDir, 'mesh_outside.stl')
            ast = os.path.join(self.meshCaseDir, 'mesh_outside.ast')
            mesh = Mesh.Mesh(stl)
            mesh.write(ast)
            os.remove(stl)
            os.rename(ast, stl)
            fem_mesh = Fem.read(stl)
            fem_mesh_obj = FreeCAD.ActiveDocument.addObject("Fem::FemMeshObject", self.mesh_obj.Name+"_Surf_Vis")
            fem_mesh_obj.FemMesh = fem_mesh
            self.mesh_obj.addObject(fem_mesh_obj)
            print('  Finished loading mesh.')
        else:
            print('No mesh was created.')

    def writeMeshCase(self):
        """ Collect case settings, and finally build a runnable case. """
        CfdTools.cfdMessage("Populating mesh dictionaries in folder {}\n".format(self.meshCaseDir))

        # cfMESH settings
        if self.mesh_obj.MeshUtility == "cfMesh":
            self.cf_settings['ClMax'] = self.clmax*self.scale
            if len(self.cf_settings['BoundaryLayers']) > 0:
                self.cf_settings['BoundaryLayerPresent'] = True
            else:
                self.cf_settings['BoundaryLayerPresent'] = False
            if len(self.cf_settings["InternalRegions"]) > 0:
                self.cf_settings['InternalRefinementRegionsPresent'] = True
            else:
                self.cf_settings['InternalRefinementRegionsPresent'] = False

        # SnappyHexMesh settings
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

            if self.mesh_obj.ImplicitEdgeDetection:
                snappy_settings['ImplicitEdgeDetection'] = True
            else:
                snappy_settings['ImplicitEdgeDetection'] = False

            inside_x = Units.Quantity(self.mesh_obj.PointInMesh.get('x')).Value*self.scale
            inside_y = Units.Quantity(self.mesh_obj.PointInMesh.get('y')).Value*self.scale
            inside_z = Units.Quantity(self.mesh_obj.PointInMesh.get('z')).Value*self.scale

            shape_patch_names_list = []
            for k in range(len(self.patch_faces)):
                for j in range(len(self.patch_faces[k])):
                    if len(self.patch_faces[k][j]):
                        shape_patch_names_list.append(self.patch_names[k][j])
            snappy_settings['ShapePatchNames'] = tuple(shape_patch_names_list)
            snappy_settings['EdgeRefinementLevel'] = CfdTools.relLenToRefinementLevel(self.mesh_obj.EdgeRefinement)
            snappy_settings['PointInMesh'] = {
                "x": inside_x,
                "y": inside_y,
                "z": inside_z
            }
            snappy_settings['CellsBetweenLevels'] = self.mesh_obj.CellsBetweenLevels

            if len(self.snappy_settings["InternalRegions"]) > 0:
                self.snappy_settings['InternalRefinementRegionsPresent'] = True
            else:
                self.snappy_settings['InternalRefinementRegionsPresent'] = False

        # GMSH settings
        elif self.mesh_obj.MeshUtility == "gmsh":
            exe = CfdTools.getGmshExecutable()
            self.gmsh_settings['Executable'] = CfdTools.translatePath(exe)
            self.gmsh_settings['HasLengthMap'] = False
            if self.ele_length_map:
                self.gmsh_settings['HasLengthMap'] = True
                print(self.ele_length_map)
                print(self.ele_node_map)
                self.gmsh_settings['LengthMap'] = self.ele_length_map
                self.gmsh_settings['NodeMap'] = {}
                for e in self.ele_length_map:
                    ele_nodes = (''.join((str(n+1) + ', ') for n in self.ele_node_map[e])).rstrip(', ')
                    self.gmsh_settings['NodeMap'][e] = ele_nodes
            self.gmsh_settings['ClMax'] = self.clmax
            self.gmsh_settings['ClMin'] = self.clmin
            sols = (''.join((str(n+1) + ', ') for n in range(len(self.mesh_obj.Part.Shape.Solids)))).rstrip(', ')
            self.gmsh_settings['Solids'] = sols
            self.gmsh_settings['BoundaryFaceMap'] = {}
            for k in range(len(self.patch_faces)):
                for l in range(len(self.patch_faces[k])):
                    patch_faces = self.patch_faces[k][l]
                    patch_name = self.patch_names[k][l]
                    if len(patch_faces):
                        self.gmsh_settings['BoundaryFaceMap'][patch_name] = ', '.join(str(fi+1) for fi in patch_faces)

        # Perform initialisation here rather than __init__ in case of path changes
        self.template_path = os.path.join(CfdTools.get_module_path(), "data", "defaultsMesh")

        mesh_region_present = False
        if self.mesh_obj.MeshUtility == "cfMesh" and len(self.cf_settings['MeshRegions']) > 0 or \
           self.mesh_obj.MeshUtility == "snappyHexMesh" and len(self.snappy_settings['MeshRegions']) > 0:
            mesh_region_present = True

        self.settings = {
            'Name': self.part_obj.Name,
            'MeshPath': self.meshCaseDir,
            'FoamRuntime': CfdTools.getFoamRuntime(),
            'MeshUtility': self.mesh_obj.MeshUtility,
            'MeshRegionPresent': mesh_region_present,
            'CfSettings': self.cf_settings,
            'SnappySettings': self.snappy_settings,
            'GmshSettings': self.gmsh_settings,
            'ExtrusionSettings': self.extrusion_settings,
            'ConvertToDualMesh': self.mesh_obj.ConvertToDualMesh
        }
        if CfdTools.getFoamRuntime() != 'WindowsDocker':
            self.settings['TranslatedFoamPath'] = CfdTools.translatePath(CfdTools.getFoamDir())

        if self.mesh_obj.NumberOfProcesses <= 1:
            self.mesh_obj.NumberOfProcesses = 1
            self.settings['ParallelMesh'] = False
        else:
            self.settings['ParallelMesh'] = True
        self.settings['NumberOfProcesses'] = self.mesh_obj.NumberOfProcesses
        self.settings['NumberOfThreads'] = self.mesh_obj.NumberOfThreads

        TemplateBuilder.TemplateBuilder(self.meshCaseDir, self.template_path, self.settings)

        # Update Allmesh permission - will fail silently on Windows
        fname = os.path.join(self.meshCaseDir, "Allmesh")
        import stat
        s = os.stat(fname)
        os.chmod(fname, s.st_mode | stat.S_IEXEC)

        CfdTools.cfdMessage("Successfully wrote meshCase to folder {}\n".format(self.meshCaseDir))
