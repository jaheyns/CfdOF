# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: © 2017 Alfred Bogaers (CSIR) <abogaers@csir.co.za>
# SPDX-FileCopyrightText: © 2017 Johan Heyns (CSIR) <jheyns@csir.co.za>
# SPDX-FileCopyrightText: © 2017 Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>
# SPDX-FileCopyrightText: © 2019 Oliver Oxtoby <oliveroxtoby@gmail.com>
# SPDX-FileCopyrightText: © 2022 Jonathan Bergh <bergh.jonathan@gmail.com>
# SPDX-FileNotice: Part of the CfdOF addon.

################################################################################
#                                                                              #
#   This program is free software; you can redistribute it and/or              #
#   modify it under the terms of the GNU Lesser General Public                 #
#   License as published by the Free Software Foundation; either               #
#   version 3 of the License, or (at your option) any later version.           #
#                                                                              #
#   This program is distributed in the hope that it will be useful,            #
#   but WITHOUT ANY WARRANTY; without even the implied warranty of             #
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.                       #
#                                                                              #
#   See the GNU Lesser General Public License for more details.                #
#                                                                              #
#   You should have received a copy of the GNU Lesser General Public License   #
#   along with this program; if not, write to the Free Software Foundation,    #
#   Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.        #
#                                                                              #
################################################################################

import os
import os.path
import math
from FreeCAD import Units, Vector
from CfdOF import CfdTools
from CfdOF.TemplateBuilder import TemplateBuilder
from CfdOF.CfdTools import cfdMessage
from CfdOF.Mesh import CfdMeshTools
from CfdOF.Mesh import CfdDynamicMeshRefinement
from CfdOF.Solve.CfdSolidMaterial import CfdSolidMaterial


def _shape_from_object_subshape(obj, sub_shape_name):
    if sub_shape_name:
        return obj.Shape.getElement(sub_shape_name)
    return obj.Shape


def _shape_from_mesh_object(mesh_obj):
    return _shape_from_object_subshape(mesh_obj.Part, getattr(mesh_obj, 'PartSubShape', ''))


def _faces_from_shape_refs(shape_refs):
    faces = []
    for ref in shape_refs:
        shape_obj = ref[0]
        if shape_obj is None or not hasattr(shape_obj, 'Shape'):
            raise ValueError("Boundary reference points to a missing geometry object.")
        sub_list = ref[1] if ref[1] else []
        if sub_list:
            for sub_name in sub_list:
                try:
                    face = shape_obj.Shape.getElement(sub_name)
                except Exception as exc:
                    raise ValueError("Invalid boundary face reference '{}:{}'.".format(
                        shape_obj.Name, sub_name)) from exc
                if getattr(face, 'ShapeType', '') != 'Face':
                    raise ValueError("Boundary reference '{}:{}' is not a face.".format(
                        shape_obj.Name, sub_name))
                faces.append(face)
        else:
            faces.extend(shape_obj.Shape.Faces)
    return faces


class CfdCaseWriterFoam:
    def __init__(self, analysis_obj):
        self.case_folder = None
        self.mesh_file_name = None
        self.template_path = None

        self.analysis_obj = analysis_obj
        self.solver_obj = CfdTools.getSolver(analysis_obj)
        if not self.solver_obj:
            raise RuntimeError("No solver object was found in analysis " + analysis_obj.Label)
        self.physics_model = CfdTools.getPhysicsModel(analysis_obj)
        if not self.physics_model:
            raise RuntimeError("No physics model was found in analysis " + analysis_obj.Label)
        self.mesh_objs = CfdTools.getMeshObjects(analysis_obj)
        self.mesh_obj = self.mesh_objs[0] if self.mesh_objs else None
        if not self.mesh_obj:
            raise RuntimeError("No mesh object was found in analysis " + analysis_obj.Label)
        if len(self.mesh_objs) > 1:
            self._validateMultiRegionMeshRoles()
        self.material_objs = CfdTools.getMaterials(analysis_obj)
        self.solid_material_objs = CfdTools.getSolidMaterials(analysis_obj)
        if not self.material_objs and not self.solid_material_objs:
            raise RuntimeError("No material properties were found in analysis " + analysis_obj.Label)
        self.bc_group = CfdTools.getCfdBoundaryGroupWithRegionInterfaces(analysis_obj)
        self.initial_conditions = CfdTools.getInitialConditions(analysis_obj)
        if not self.initial_conditions:
            raise RuntimeError("No initial conditions object was found in analysis " + analysis_obj.Label)
        self.reporting_functions = CfdTools.getReportingFunctionsGroup(analysis_obj)
        self.scalar_transport_objs = CfdTools.getScalarTransportFunctionsGroup(analysis_obj)
        _all_mvf_objs = CfdTools.getMeanVelocityForceObjects(analysis_obj)
        _all_mode_objs = [o for o in _all_mvf_objs if o.SelectionMode == 'all']
        self.mean_velocity_force_obj = _all_mode_objs[0] if _all_mode_objs else None
        self.mean_velocity_force_cellzone_objs = [
            o for o in _all_mvf_objs if o.SelectionMode == 'cellZone']
        self.porous_zone_objs = CfdTools.getPorousZoneObjects(analysis_obj)
        self.initialisation_zone_objs = CfdTools.getInitialisationZoneObjects(analysis_obj)
        self.zone_objs = CfdTools.getZoneObjects(analysis_obj)
        self.dynamic_mesh_refinement_obj = CfdTools.getDynamicMeshAdaptation(self.mesh_obj)
        self.mesh_generated = False
        self.working_dir = CfdTools.getOutputPath(self.analysis_obj)
        self.progressCallback = None

        self.settings = None
        self.SnappySettings = None
        self._mean_velocity_force_part_names = {}
        self._mean_velocity_force_settings = {}

    def reThetatFromIntensity(I_percent):
        """ Langtry & Menter (2009) transition-onset momentum-thickness Reynolds
        number at zero pressure gradient (F(lambda) = 1), with clipping as
        in OpenFOAM 
        """
        I = max(I_percent, 0.027)
        if I <= 1.3:
            re_thetat = 1173.51 - 589.428*I + 0.2196/I**2
        else:
            re_thetat = 331.5/((I - 0.5658)**0.671)
        return max(re_thetat, 20.0)

    def writeCase(self):
        """ writeCase() will collect case settings, and finally build a runnable case. """
        cfdMessage("Writing case to folder {}\n".format(self.working_dir))
        # Try to create the path
        try:
            os.makedirs(self.working_dir)
        except OSError as exc:
            import errno
            if exc.errno == errno.EEXIST and os.path.isdir(self.working_dir):
                pass
            else:
                raise

        # Perform initialisation here rather than __init__ in case of path changes
        self.case_folder = os.path.join(self.working_dir, self.solver_obj.InputCaseName)
        self.case_folder = os.path.expanduser(os.path.abspath(self.case_folder))
        self.mesh_file_name = os.path.join(self.case_folder, self.solver_obj.InputCaseName, u".unv")
        self.template_path = os.path.join(CfdTools.getModulePath(), "Data", "Templates", "case")

        # Collect settings into single dictionary
        if not self.mesh_obj:
            raise RuntimeError("No mesh object found in analysis")
        phys_settings = CfdTools.propsToDict(self.physics_model)
        if self.physics_model.Phase != 'MultiRegion' and any(
                getattr(bc, 'SolidBoundary', False) for bc in self.bc_group):
            raise ValueError("Solid thermal boundaries require a multi-region CHT analysis.")

        CfdTools.validateBoundaryFaceAssignments(self.bc_group)

        # Validate BC labels
        bc_labels = [b.Label for b in self.bc_group]
        for i, l in enumerate(bc_labels):
            if bc_labels[i].find(' ') >= 0:
                raise ValueError("Boundary condition label '" + bc_labels[i] + "' is not valid: May not contain spaces")
        for i, l in enumerate(bc_labels):
            for j in range(i+1, len(bc_labels)):
                if bc_labels[j] == l:
                    raise ValueError("Boundary condition label '" + bc_labels[i] + "' is duplicated")
        
        self.settings = {
            'physics': phys_settings,
            'fluidProperties': [],  # Order is important, so use a list
            'solidProperties': [],  # Solid material properties for multi-region CHT
            'multiRegionEnabled': False,
            'multiRegionFluidNames': [],
            'multiRegionSolidNames': [],
            'multiRegionFluidNamesDict': {},
            'multiRegionSolidNamesDict': {},
            'multiRegionFluidBoundaries': {},
            'multiRegionSolidBoundaries': {},
            'multiRegionFluidBoundariesByRegion': {},
            'multiRegionSolidBoundariesByRegion': {},
            'multiRegionUseSplitMeshRegions': True,
            'multiRegionMeshDirs': {},
            'multiRegionNonConformalCouples': {},
            'multiRegionNonConformalCouplesPresent': False,
            'initialValues': CfdTools.propsToDict(self.initial_conditions),
            'boundaries': dict((b.Label, CfdTools.boundaryToDict(b)) for b in self.bc_group),
            'reportingFunctions': dict((fo.Label, CfdTools.propsToDict(fo)) for fo in self.reporting_functions),
            'reportingFunctionsEnabled': False,
            'scalarTransportFunctions': dict((st.Label, CfdTools.propsToDict(st)) for st in self.scalar_transport_objs),
            'scalarTransportFunctionsEnabled': False,
            'meanVelocityForce': CfdTools.propsToDict(self.mean_velocity_force_obj) if self.mean_velocity_force_obj else {},
            'meanVelocityForceEnabled': self.mean_velocity_force_obj is not None,
            'meanVelocityForceCellZones': {},
            'meanVelocityForceCellZonesPresent': False,
            'fvOptionsPresent': (self.mean_velocity_force_obj is not None or
                                 len(self.mean_velocity_force_cellzone_objs) > 0),
            'dynamicMesh': {},
            'dynamicMeshEnabled': False,
            'MovingMeshRegions': {},
            'MovingMeshRegionsPresent': False,
            'SnappySettings': self.SnappySettings,
            'bafflesPresent': self.bafflesPresent(),
            'porousZones': {},
            'porousZonesPresent': False,
            'initialisationZones': {o.Label: CfdTools.propsToDict(o) for o in self.initialisation_zone_objs},
            'initialisationZonesPresent': len(self.initialisation_zone_objs) > 0,
            'zones': {o.Label: {'PartNameList': tuple(r[0].Name for r in o.ShapeRefs)} for o in self.zone_objs},
            'zonesPresent': len(self.zone_objs) > 0,
            'meshType': self.mesh_obj.Proxy.Type,
            'meshDimension': self.mesh_obj.ElementDimension,
            'meshDir': os.path.relpath(os.path.join(self.working_dir, self.mesh_obj.CaseName), self.case_folder),
            'solver': CfdTools.propsToDict(self.solver_obj),
            'system': {},
            'runChangeDictionary': False
            }


        mr_objs = CfdTools.getMeshRefinementObjs(self.mesh_obj)
        for mr_id, mr_obj in enumerate(mr_objs):
            # moving mesh
            if self.mesh_obj.MeshUtility == 'snappyHexMesh' and not mr_obj.Internal and mr_obj.MovingMeshRegion and not mr_obj.Extrusion:
                self.settings['MovingMeshRegions'][mr_obj.Label] = {
                    'MMRModelCoR': mr_obj.MMRModelCoR,
                    'MMRModelAxis': mr_obj.MMRModelAxis,
                    't_MMRModelCoR': tuple(Units.Quantity(p, Units.Length).getValueAs('m') for p in mr_obj.MMRModelCoR),
                    't_MMRModelAxis': tuple(d for d in mr_obj.MMRModelAxis),
                    'MMRModelRPM': mr_obj.MMRModelRPM,# revolution per minute
                    'MMRModelRPS': (mr_obj.MMRModelRPM/9.5), # rad/s #for the openCFD version
                    'SpeedType': mr_obj.SpeedType,
                    'VariableSpeedRPM': "",
                    'VariableSpeedRPS': ""
                }

                longer = max(len(mr_obj.TimeList), len(mr_obj.SpeedList))
                for i in range(longer):
                    self.settings['MovingMeshRegions'][mr_obj.Label]['VariableSpeedRPM'] += "\t\t\t\t\t("
                    self.settings['MovingMeshRegions'][mr_obj.Label]['VariableSpeedRPS'] += "\t\t\t\t\t\t("
                    for j in range(2): # iterate over the 2 lists to copy the values to the buff
                        try:
                            entery = [mr_obj.TimeList, mr_obj.SpeedList][j][i]
                        except:
                            entery = 0 # make the value 0 when the lists are not the same length
                        self.settings['MovingMeshRegions'][mr_obj.Label]['VariableSpeedRPM'] += str(entery)
                        if j == 0:
                            self.settings['MovingMeshRegions'][mr_obj.Label]['VariableSpeedRPS'] += str(entery) + " "
                            self.settings['MovingMeshRegions'][mr_obj.Label]['VariableSpeedRPM'] += " "
                        else:
                            self.settings['MovingMeshRegions'][mr_obj.Label]['VariableSpeedRPS'] += str(entery/9.5)
                    self.settings['MovingMeshRegions'][mr_obj.Label]['VariableSpeedRPM'] += ")\n"
                    self.settings['MovingMeshRegions'][mr_obj.Label]['VariableSpeedRPS'] += ")\n"
                # if the first time in the list is not 0 then add a 0 with a speed eqaul the first speed
                # to avoid getting an error in the OpenCFD version
                if mr_obj.TimeList[0] > 0:
                    self.settings['MovingMeshRegions'][mr_obj.Label]['VariableSpeedRPS'] = "\t\t\t\t\t\t(0 "+str(mr_obj.SpeedList[0]/9.5)+")\n" + self.settings['MovingMeshRegions'][mr_obj.Label]['VariableSpeedRPS']
                # if the last time in the list is less than the EndTime then add a new pair with time = EndTime and with a speed eqaul the last speed
                # to avoid getting an error in the OpenCFD version
                if mr_obj.TimeList[len(mr_obj.TimeList)-1] < self.settings['solver']['EndTime']:
                    self.settings['MovingMeshRegions'][mr_obj.Label]['VariableSpeedRPS'] += "\t\t\t\t\t\t("+str(self.settings['solver']['EndTime'])+" "+str(mr_obj.SpeedList[len(mr_obj.SpeedList)-1]/9.5)+")\n"



        if len(self.settings["MovingMeshRegions"]) > 0:
            self.settings['MovingMeshRegionsPresent'] = True
        else:
            self.settings['MovingMeshRegionsPresent'] = False

        if CfdTools.DockerContainer.usedocker:
            mesh_d = os.path.relpath(os.path.join(self.working_dir,self.mesh_obj.CaseName),CfdTools.getDefaultOutputPath())
            self.settings['meshDir'] = '/tmp/{}'.format(mesh_d)

        self.settings['meshDir'] = self.settings['meshDir'].replace('\\', '/')

        self.processSystemSettings()
        self.processSolverSettings()
        self.processFluidProperties()
        self.processBoundaryConditions()
        self.processReferenceFrames()
        self.processInitialConditions()
        CfdTools.clearCase(self.case_folder)

        self.exportZoneStlSurfaces()
        if self.porous_zone_objs:
            self.processPorousZoneProperties()
        self.processInitialisationZoneProperties()

        if self.settings['multiRegionEnabled']:
            cfdMessage('Multi-region CHT case detected\n')
            self.processMultiRegionBoundaries()

        if self.mean_velocity_force_cellzone_objs:
            cfdMessage('Mean velocity force cell zone(s) present\n')
            self.exportMeanVelocityForceCellZoneStlSurfaces()
            self.processMeanVelocityForceCellZoneProperties()

        if self.reporting_functions:
            cfdMessage('Reporting functions present\n')
            self.processReportingFunctions()

        if self.scalar_transport_objs:
            cfdMessage('Scalar transport functions present\n')
            self.processScalarTransportFunctions()

        if self.dynamic_mesh_refinement_obj:
            cfdMessage('Dynamic mesh adaptation rule present\n')
            self.processDynamicMeshRefinement()

        self.settings['createPatchesFromSnappyBaffles'] = False
        self.settings['createPatchesForPeriodics'] = False
        cfdMessage("Matching boundary conditions ...\n")
        if self.progressCallback:
            self.progressCallback("Matching boundary conditions ...")
        self.setupPatchNames()

        TemplateBuilder(self.case_folder, self.template_path, self.settings)

        # Update Allrun permission - will fail silently on Windows
        file_name = os.path.join(self.case_folder, "Allrun")
        import stat
        s = os.stat(file_name)
        os.chmod(file_name, s.st_mode | stat.S_IEXEC)

        cfdMessage("Successfully wrote case to folder {}\n".format(self.working_dir))
        if self.progressCallback:
            self.progressCallback("Case written successfully")

        return True

    def getSolverName(self):
        """
        Solver name is selected based on selected physics. This should only be extended as additional physics are
        included.
        """
        solver = None
        if self.physics_model.Phase == 'Single':
            if len(self.material_objs) == 1:
                if self.physics_model.Flow == 'Isothermal':
                    if self.physics_model.Time == 'Transient':
                        solver = 'pimpleFoam'
                    else:
                        if self.porous_zone_objs or self.porousBafflesPresent():
                            solver = 'porousSimpleFoam'
                        elif self.physics_model.SRFModelEnabled:
                            solver = 'SRFSimpleFoam'
                        else:
                            solver = 'simpleFoam'
                elif self.physics_model.Flow == 'NonIsothermal':
                    if self.physics_model.Time == 'Transient':
                        solver = 'buoyantPimpleFoam'
                    else:
                        solver = 'buoyantSimpleFoam'
                elif self.physics_model.Flow == 'HighMachCompressible':
                    solver = 'hisa'
                else:
                    raise RuntimeError(self.physics_model.Flow + " flow model currently not supported.")
            else:
                raise RuntimeError("Only one material object may be present for single phase simulation.")
        elif self.physics_model.Phase == 'FreeSurface':
            if self.physics_model.Time == 'Transient':
                if self.physics_model.Flow == 'Isothermal':
                    if len(self.material_objs) == 2:
                        solver = 'interFoam'
                    elif len(self.material_objs) > 2:
                        solver = 'multiphaseInterFoam'
                    else:
                        raise RuntimeError("At least two material objects must be present for free surface simulation.")
                else:
                    raise RuntimeError("Only isothermal analysis is currently supported for free surface flow simulation.")
            else:
                raise RuntimeError("Only transient analysis is supported for free surface flow simulation.")
        elif self.physics_model.Phase == 'MultiRegion':
            if self.physics_model.Flow == 'NonIsothermal':
                if self.physics_model.Time == 'Steady':
                    solver = 'chtMultiRegionSimpleFoam'
                else:
                    solver = 'chtMultiRegionFoam'
            else:
                raise RuntimeError("Only NonIsothermal flow is supported for MultiRegion (CHT) simulation.")
        else:
            raise RuntimeError(self.physics_model.Phase + " phase model currently not supported.")

        # Catch-all in case
        if solver is None:
            raise RuntimeError("No solver is supported to handle the selected physics with {} phases.".format(
                len(self.material_objs)))
        return solver

    def processSolverSettings(self):
        solver_settings = self.settings['solver']
        if solver_settings['Parallel']:
            if solver_settings['ParallelCores'] < 2:
                solver_settings['ParallelCores'] = 2
        solver_settings['SolverName'] = self.getSolverName()

    def processSystemSettings(self):
        installation_path = CfdTools.getFoamDir()
        if CfdTools.getFoamRuntime() == 'BlueCFD2':
            norm_inst_path = os.path.normpath(os.path.join(installation_path, '..'))
        else:
            norm_inst_path = installation_path

        system_settings = self.settings['system']
        system_settings['FoundationChtModels'] = False
        if self.getSolverName() in ('chtMultiRegionSimpleFoam', 'chtMultiRegionFoam'):
            foam_environment = CfdTools.runFoamCommand('echo "${WM_PROJECT_VERSION}:${FOAM_API:-}"')[0].strip()
            version, api = foam_environment.rsplit('\n', 1)[-1].split(':', 1)
            system_settings['FoundationChtModels'] = not api and (
                version == 'dev' or (version.isdigit() and 13 <= int(version) < 1000))
        system_settings['FoamRuntime'] = CfdTools.getFoamRuntime()
        system_settings['SolidEnergyField'] = 'e' if system_settings['FoundationChtModels'] else 'h'
        system_settings['CasePath'] = self.case_folder
        system_settings['FoamPath'] = norm_inst_path
        system_settings['TranslatedFoamPath'] = CfdTools.translatePath(installation_path)
        system_settings['hostFileRequired'] = self.analysis_obj.UseHostfile
        if system_settings['hostFileRequired'] == True:
            system_settings['hostFileName'] = self.analysis_obj.HostfileName
            CfdTools.cfdWarning("Please note: The 'Use Host File' setting is deprecated. Please edit the MPI options "
                                "directly under 'Tools | Edit parameters | Preferences | Mod | CfdOF'")
        if CfdTools.getFoamRuntime() == "MinGW":
            system_settings['FoamVersion'] = os.path.split(installation_path)[-1].lstrip('v')
        elif CfdTools.getFoamRuntime() == 'BlueCFD2':
            system_settings['FoamVersion'] = os.path.split(installation_path)[-1].lstrip('OpenFOAM-')
        elif CfdTools.getFoamRuntime() == 'BlueCFD':
            # search for OpenFOAM-XX
            with os.scandir('{}'.format(installation_path)) as dirs:
                for dir in dirs:
                    if dir.is_dir() and dir.name.startswith('OpenFOAM-'):
                        system_settings['FoamVersion'] = os.path.split(dir.name)[-1].lstrip('OpenFOAM-')
                        break
        system_settings['MPIOptionsOMPI'], system_settings['MPIOptionsMSMPI'] = CfdTools.getMPISettings()

    def setupMesh(self, updated_mesh_path, scale):
        if os.path.exists(updated_mesh_path):
            CfdTools.convertMesh(self.case_folder, updated_mesh_path, scale)

    def processFluidProperties(self):
        # self.material_obj currently stores everything as a string
        # Convert to (mostly) SI numbers for OpenFOAM
        settings = self.settings
        solver_name = settings['solver']['SolverName']
        is_multiregion = solver_name in ['chtMultiRegionSimpleFoam', 'chtMultiRegionFoam']

        multi_mesh_regions = is_multiregion and len(self.mesh_objs) > 1
        solid_property_entries = []

        # Process dedicated CfdSolidMaterial objects (new path)
        for solid_obj in self.solid_material_objs:
            mp = solid_obj.Material.copy()
            mp['Name'] = solid_obj.Label
            region_name = CfdTools.getRegionName(solid_obj)
            if 'ThermalConductivity' in mp:
                mp['ThermalConductivity'] = Units.Quantity(mp['ThermalConductivity']).getValueAs("W/m/K").Value
            if 'Density' in mp:
                mp['Density'] = Units.Quantity(mp['Density']).getValueAs("kg/m^3").Value
            if 'SpecificHeat' in mp:
                mp['Cp'] = Units.Quantity(mp['SpecificHeat']).getValueAs("J/kg/K").Value
            if hasattr(solid_obj, 'HeatGeneration'):
                heat_gen = solid_obj.HeatGeneration.getValueAs("W/m^3").Value
            else:
                heat_gen = 0.0
            mp['HeatGeneration'] = heat_gen
            mp['HeatGenerationActive'] = 'true' if heat_gen != 0 else 'false'
            solid_property_entries.append((solid_obj, region_name, mp))
            if not multi_mesh_regions:
                settings['solidProperties'].append(mp)
                settings['multiRegionSolidNames'].append(region_name)

        for material_obj in self.material_objs:
            mp = material_obj.Material.copy()
            mp['Name'] = material_obj.Label
            if is_multiregion:
                # Derive fluid region name from the Internal mesh refinement zone label so the
                # region identity follows selected geometry rather than material metadata.
                mr_objs = CfdTools.getMeshRefinementObjs(self.mesh_obj)
                internal_zones = [o.Label for o in mr_objs if o.Internal]
                region_name = internal_zones[0] if internal_zones else material_obj.Label
            else:
                region_name = material_obj.Label

            if is_multiregion and not multi_mesh_regions:
                settings['multiRegionFluidNames'].append(region_name)

            # Add type if absent
            mat_type = mp.get('Type', 'Isothermal')
            mp['Type'] = mat_type

            # Check compatibility between physics and material type
            flow_type = self.physics_model.Flow
            if ((flow_type == 'Isothermal') != (mat_type == 'Isothermal')) or \
               (flow_type == 'HighMachCompressible' and mat_type != 'Compressible'):
                raise ValueError("The material type of object '{}' is not compatible with the selected flow physics. "
                                 "Please modify the material properties.".format(mp['Name']))

            if 'Density' in mp:
                mp['Density'] = Units.Quantity(mp['Density']).getValueAs("kg/m^3").Value
            if 'DynamicViscosity' in mp:
                if self.physics_model.Turbulence == 'Inviscid':
                    mp['DynamicViscosity'] = 0.0
                else:
                    mp['DynamicViscosity'] = Units.Quantity(mp['DynamicViscosity']).getValueAs("kg/m/s").Value
                mp['KinematicViscosity'] = mp['DynamicViscosity']/mp['Density']
            if 'MolarMass' in mp:
                # OpenFOAM uses kg/kmol
                mp['MolarMass'] = Units.Quantity(mp['MolarMass']).getValueAs("kg/mol").Value*1000
            if 'Cp' in mp:
                mp['Cp'] = Units.Quantity(mp['Cp']).getValueAs("J/kg/K").Value
            if 'SutherlandTemperature' in mp:
                mp['SutherlandTemperature'] = Units.Quantity(mp['SutherlandTemperature']).getValueAs("K").Value
                if 'SutherlandRefViscosity' in mp and 'SutherlandRefTemperature' in mp:
                    mu0 = Units.Quantity(mp['SutherlandRefViscosity']).getValueAs("kg/m/s").Value
                    T0 = Units.Quantity(mp['SutherlandRefTemperature']).getValueAs("K").Value
                    mp['SutherlandConstant'] = mu0/T0**(3./2)*(T0+mp['SutherlandTemperature'])
            for k in mp:
                if k.endswith('Polynomial'):
                    poly = mp[k].split()
                    poly8 = [0.0]*8
                    for i in range(len(poly)):
                        try:
                            poly8[i] = float(poly[i])
                        except ValueError:
                            raise ValueError("Invalid coefficient {} in polynomial coefficient {}".format(poly[i], k))
                    mp[k] = ' '.join(str(v) for v in poly8)

            settings['fluidProperties'].append(mp)

        if is_multiregion:
            settings['multiRegionEnabled'] = True
            self.processMultiRegionMeshObjects()
            if multi_mesh_regions:
                self._validateMultiRegionMeshRoles()
            if multi_mesh_regions:
                self._alignMultiRegionPropertiesFromMeshes(solid_property_entries)
            if not settings['multiRegionSolidNames']:
                raise ValueError("{} requires at least one solid material region. "
                                 "Add a Solid Properties object for the solid body, or use a "
                                 "single-region buoyant solver with a fixed-temperature wall "
                                 "if the body is only meant to be a boundary."
                                 .format(solver_name))
            settings['multiRegionFluidNamesDict'] = {n: {} for n in settings['multiRegionFluidNames']}
            settings['multiRegionSolidNamesDict'] = {n: {} for n in settings['multiRegionSolidNames']}

    def _alignMultiRegionPropertiesFromMeshes(self, solid_property_entries):
        settings = self.settings
        material_by_object_name = {}
        for solid_obj, _region_name, material_props in solid_property_entries:
            for ref_obj, subnames in getattr(solid_obj, 'ShapeRefs', []):
                for subname in subnames:
                    try:
                        selected_shape = ref_obj.Shape.getElement(subname)
                        if selected_shape.ShapeType != 'Solid':
                            raise ValueError("The selected sub-shape is not a solid")
                    except Exception as exc:
                        raise ValueError(
                            "Solid Properties '{}' has an invalid solid reference '{}:{}'. "
                            "Reselect the solid in that material's Solid Properties panel.".format(
                                solid_obj.Label, ref_obj.Name, subname)) from exc
                material_by_object_name[ref_obj.Name] = material_props

        aligned_solid_properties = []
        missing_regions = []
        for mesh_obj in self.mesh_objs:
            if self._getMeshRegionType(mesh_obj) != 'solid':
                continue
            region_name = CfdTools.getRegionName(mesh_obj)
            material_props = material_by_object_name.get(mesh_obj.Part.Name)
            if material_props is None:
                missing_regions.append(region_name)
                continue
            region_props = material_props.copy()
            region_props['Name'] = region_name
            aligned_solid_properties.append(region_props)

        if missing_regions:
            raise ValueError(
                "No solid material properties were assigned to solid mesh region(s): {}. "
                "Select each generated solid region in a Solid Properties object.".format(
                    ", ".join(missing_regions)))

        settings['solidProperties'] = aligned_solid_properties

    def processMultiRegionMeshObjects(self):
        """Collect explicit region mesh metadata for non-conformal CHT cases.

        Multiple CfdMesh objects indicate that the fluid and solid regions are meshed
        separately and coupled later through mappedWall AMI interfaces.
        """
        settings = self.settings
        if len(self.mesh_objs) <= 1:
            raise ValueError("Multi-region CHT requires separate fluid and solid region meshes. "
                             "Create a mesh for each region instead of meshing a combined object.")

        settings['multiRegionUseSplitMeshRegions'] = False
        settings['multiRegionFluidNames'] = []
        settings['multiRegionSolidNames'] = []
        settings['multiRegionMeshDirs'] = {}
        for mesh_obj in self.mesh_objs:
            region_name = CfdTools.getRegionName(mesh_obj)
            region_type = self._getMeshRegionType(mesh_obj)
            mesh_dir = os.path.relpath(os.path.join(self.working_dir, mesh_obj.CaseName), self.case_folder)
            settings['multiRegionMeshDirs'][region_name] = {
                'MeshDir': mesh_dir.replace('\\', '/'),
            }
            if region_type == 'solid':
                if region_name not in settings['multiRegionSolidNames']:
                    settings['multiRegionSolidNames'].append(region_name)
            else:
                if region_name not in settings['multiRegionFluidNames']:
                    settings['multiRegionFluidNames'].append(region_name)

    def _validateMultiRegionMeshRoles(self):
        for mesh_obj in self.mesh_objs:
            self._getMeshRegionType(mesh_obj)

    def _getMeshRegionType(self, mesh_obj):
        part_obj = mesh_obj.Part
        if part_obj is None:
            raise ValueError(
                "Mesh '{}' has no shape. Select a shape in the mesh settings.".format(mesh_obj.Label))
        role = getattr(part_obj, 'RegionRole', None)
        if role is None and len(self.mesh_objs) == 1:
            return 'fluid'
        region_type = str(role or '').strip().lower()
        if region_type not in ('fluid', 'solid'):
            raise ValueError(
                "Region '{}' has no valid Fluid/Solid role. "
                "Choose its role in the Region-coupled interface panel.".format(part_obj.Label))
        return region_type

    def processBoundaryConditions(self):
        """ Compute any quantities required before case build """
        # Copy keys so that we can delete while iterating
        settings = self.settings
        bc_names = list(settings['boundaries'].keys())
        for bc_name in bc_names:
            bc = settings['boundaries'][bc_name]
            if not bc['VelocityIsCartesian']:
                velo_mag = bc['VelocityMag']
                face = bc['DirectionFace'].split(':')
                print(bc['ShapeRefs'])
                if not face[0] and len(bc['ShapeRefs']):
                    face = bc['ShapeRefs'][0][0].Name
                if not face[0]:
                    raise RuntimeError(str("No face specified for velocity direction in boundary '" + bc_name + "'"))
                # See if entered face actually exists and is planar
                try:
                    selected_object = self.analysis_obj.Document.getObject(face[0])
                    if hasattr(selected_object, "Shape"):
                        elt = selected_object.Shape.getElement(face[1])
                        if elt.ShapeType == 'Face' and CfdTools.isPlanar(elt):
                            n = elt.normalAt(0.5, 0.5)
                            if bc['ReverseNormal']:
                               n = [-ni for ni in n]
                            velocity = [ni*velo_mag for ni in n]
                            bc['Ux'] = velocity[0]
                            bc['Uy'] = velocity[1]
                            bc['Uz'] = velocity[2]
                        else:
                            raise RuntimeError
                    else:
                        raise RuntimeError
                except (SystemError, RuntimeError):
                    if bc['DirectionFace']:
                        raise RuntimeError(str(bc['DirectionFace']) + ", specified for velocity direction in boundary '" + bc_name + "', is not a valid, planar face.")
                    else:
                        raise RuntimeError(str("No face specified for velocity direction in boundary '" + bc_name + "'"))
            if settings['solver']['SolverName'] in ['simpleFoam', 'porousSimpleFoam', 'pimpleFoam', 'SRFSimpleFoam']:
                bc['KinematicPressure'] = bc['Pressure']/settings['fluidProperties'][0]['Density']

            if bc['PorousBaffleMethod'] == 'porousScreen':
                wireDiam = bc['ScreenWireDiameter']
                spacing = bc['ScreenSpacing']
                CD = 1.0  # Drag coeff of wire (Simmons - valid for Re > ~300)
                beta = (1-wireDiam/spacing)**2
                bc['PressureDropCoeff'] = CD*(1-beta)

            if bc['BoundaryType'] == 'wall' and bc['BoundarySubType'] == 'rotatingWall':
                ax = bc['RotationAxis']
                if ax[0]**2 + ax[1]**2 + ax[2]**2 == 0:
                    raise RuntimeError(str("The rotation axis in boundary '" + bc_name + "' cannot be zero."))

            if settings['solver']['SolverName'] in ['interFoam', 'multiphaseInterFoam']:
                # Make sure the first n-1 alpha values exist, and write the n-th one
                # consistently for multiphaseInterFoam
                sum_alpha = 0.0
                alphas_new = {}
                for i, m in enumerate(settings['fluidProperties']):
                    alpha_name = m['Name']
                    if i == len(settings['fluidProperties']) - 1:
                        if settings['solver']['SolverName'] == 'multiphaseInterFoam':
                            alphas_new[alpha_name] = 1.0 - sum_alpha
                    else:
                        alpha = Units.Quantity(bc.get('VolumeFractions', {}).get(alpha_name, '0')).Value
                        alphas_new[alpha_name] = alpha
                        sum_alpha += alpha
                bc['VolumeFractions'] = alphas_new

            # Copy turbulence settings
            bc['TurbulenceIntensity'] = bc['TurbulenceIntensityPercentage']/100.0
            physics = settings['physics']
            if (bc['BoundaryType'] == 'inlet' or bc['BoundaryType'] == 'open') and \
                bc['TurbulenceInletSpecification'] == 'intensityAndLengthScale':
                if physics['Turbulence'] in ('RANS', 'DES') and \
                    physics['TurbulenceModel'].startswith('SpalartAllmaras'):
                        if bc['BoundarySubType'] == 'uniformVelocityInlet' or bc['BoundarySubType'] == 'farField':
                            Uin = (bc['Ux']**2 + bc['Uy']**2 + bc['Uz']**2)**0.5

                            # Turb Intensity and length scale
                            I = bc['TurbulenceIntensity']
                            l = bc['TurbulenceLengthScale']

                            # Spalart Allmaras
                            bc['NuTilda'] = (3.0/2.0)**0.5 * Uin * I * l

                        else:
                            raise RuntimeError(
                                "Inlet type currently unsupported for calculating turbulence inlet conditions from "
                                "intensity and length scale.")

                # Langtry-Menter transition model
                if physics['Turbulence'] == 'RANS' and physics['TurbulenceModel'] == 'kOmegaSSTLM':
                    bc['ReThetat'] = self.reThetatFromIntensity(bc['TurbulenceIntensityPercentage'])

            if bc['DefaultBoundary']:
                if settings['boundaries'].get('defaultFaces'):
                    raise ValueError("More than one default boundary defined")
                settings['boundaries']['defaultFaces'] = bc

        if not settings['boundaries'].get('defaultFaces'):
            settings['boundaries']['defaultFaces'] = {
                'BoundaryType': 'wall',
                'BoundarySubType': 'slipWall',
                'ThermalBoundaryType': 'zeroGradient'
            }

        # Assign any extruded patches as the appropriate type
        mr_objs = CfdTools.getMeshRefinementObjs(self.mesh_obj)
        for mr_id, mr_obj in enumerate(mr_objs):
            if mr_obj.Extrusion and mr_obj.ExtrusionType == "2DPlanar":
                settings['boundaries'][mr_obj.Label] = {
                    'BoundaryType': 'constraint',
                    'BoundarySubType': 'empty'
                }
                settings['boundaries'][mr_obj.Label+"BackFace"] = {
                    'BoundaryType': 'constraint',
                    'BoundarySubType': 'empty'
                }
            if mr_obj.Extrusion and mr_obj.ExtrusionType == "2DWedge":
                settings['boundaries'][mr_obj.Label] = {
                    'BoundaryType': 'constraint',
                    'BoundarySubType': 'symmetry'
                }
                settings['boundaries'][mr_obj.Label+"BackFace"] = {
                    'BoundaryType': 'constraint',
                    'BoundarySubType': 'symmetry'
                }

    def parseFaces(self, shape_refs):
        pass

    def processReferenceFrames(self):
        pass

    def processInitialConditions(self):
        """ Do any required computations before case build. Boundary conditions must be processed first. """
        settings = self.settings
        initial_values = settings['initialValues']
        # NOTE: KinematicPressure is derived from initial_values['Pressure'] at the
        # end of this function, after the 'Copy pressure' block below has had a
        # chance to replace Pressure with the value taken from the outlet boundary.
        # Deriving it here instead would ignore UseOutletPValue entirely.
        if settings['solver']['SolverName'] in ['interFoam', 'multiphaseInterFoam']:
            # Make sure the first n-1 alpha values exist, and write the n-th one
            # consistently for multiphaseInterFoam
            sum_alpha = 0.0
            alphas_new = {}
            for i, m in enumerate(settings['fluidProperties']):
                alpha_name = m['Name']
                if i == len(settings['fluidProperties'])-1:
                    if settings['solver']['SolverName'] == 'multiphaseInterFoam':
                        alphas_new[alpha_name] = 1.0-sum_alpha
                else:
                    alpha = Units.Quantity(initial_values.get('VolumeFractions', {}).get(alpha_name, '0')).Value
                    alphas_new[alpha_name] = alpha
                    sum_alpha += alpha
            initial_values['VolumeFractions'] = alphas_new

        if initial_values['PotentialFlow']:
            if settings['solver']['SolverName'] in ['SRFSimpleFoam']:
                raise RuntimeError("Selected solver does not support potential flow velocity initialisation.")
            
        if initial_values['PotentialFlow'] or initial_values['PotentialFlowP']:
            if settings['solver']['SolverName'] in ['buoyantSimpleFoam', 'buoyantPimpleFoam', 'hisa']:
                for bc in settings['boundaries']:
                    if settings['boundaries'][bc]['BoundarySubType'] == 'massFlowRateInlet':
                        raise RuntimeError("Selected solver does not support potential flow initialisation with "
                                           "a mass flow inlet boundary.")

        if initial_values['PotentialFlowP']:
            if settings['solver']['SolverName'] not in ['simpleFoam', 'porousSimpleFoam', 'pimpleFoam', 'hisa']:
                raise RuntimeError("Selected solver does not support potential flow pressure initialisation.")

        physics = settings['physics']

        # Copy velocity
        if initial_values['UseInletUValues']:
            if initial_values['BoundaryU']:
                inlet_bc = settings['boundaries'][initial_values['BoundaryU'].Label]
                if inlet_bc['BoundarySubType'] == 'uniformVelocityInlet' or inlet_bc['BoundarySubType'] == 'farField':
                    initial_values['Ux'] = inlet_bc['Ux']
                    initial_values['Uy'] = inlet_bc['Uy']
                    initial_values['Uz'] = inlet_bc['Uz']
                else:
                    raise RuntimeError("Boundary type not appropriate to determine initial velocity.")
            else:
                raise RuntimeError("No boundary selected to copy initial velocity value from.")

        # Copy pressure
        if initial_values['UseOutletPValue']:
            if initial_values['BoundaryP']:
                outlet_bc = settings['boundaries'][initial_values['BoundaryP'].Label]
                if outlet_bc['BoundarySubType'] == 'staticPressureOutlet' or \
                        outlet_bc['BoundarySubType'] == 'totalPressureOpening' or \
                        outlet_bc['BoundarySubType'] == 'totalPressureInlet' or \
                        outlet_bc['BoundarySubType'] == 'staticPressureInlet' or \
                        outlet_bc['BoundarySubType'] == 'farField':
                    initial_values['Pressure'] = outlet_bc['Pressure']
                else:
                    raise RuntimeError("Boundary type not appropriate to determine initial pressure.")
            else:
                raise RuntimeError("No boundary selected to copy initial pressure value from.")

        if physics['Flow'] != 'Isothermal' and initial_values['UseInletTemperatureValue']:
            inlet_bc = settings['boundaries'][initial_values['BoundaryT'].Label]
            if inlet_bc['BoundaryType'] == 'inlet':
                if inlet_bc['ThermalBoundaryType'] == 'fixedValue':
                    initial_values['Temperature'] = inlet_bc['Temperature']
                else:
                    raise RuntimeError("Inlet type not appropriate to determine initial temperature")
            elif inlet_bc['BoundarySubType'] == 'farField':
                initial_values['Temperature'] = inlet_bc['Temperature']
            else:
                raise RuntimeError("Inlet type not appropriate to determine initial temperature.")

        # Copy turbulence settings
        if physics['TurbulenceModel'] is not None:
            if initial_values['UseInletTurbulenceValues']:
                if initial_values['BoundaryTurb']:
                    inlet_bc = settings['boundaries'][initial_values['BoundaryTurb'].Label]

                    if inlet_bc['TurbulenceInletSpecification'] == 'TKEAndSpecDissipationRate':
                        initial_values['k'] = inlet_bc['TurbulentKineticEnergy']
                        initial_values['omega'] = inlet_bc['SpecificDissipationRate']
                    elif inlet_bc['TurbulenceInletSpecification'] == 'TKEAndDissipationRate':
                        initial_values['k'] = inlet_bc['TurbulentKineticEnergy']
                        initial_values['epsilon'] = inlet_bc['DissipationRate']
                    elif inlet_bc['TurbulenceInletSpecification'] == 'TransportedNuTilda':
                        initial_values['nuTilda'] = inlet_bc['NuTilda']
                    elif inlet_bc['TurbulenceInletSpecification'] == 'TKESpecDissipationRateGammaAndReThetat':
                        initial_values['k'] = inlet_bc['TurbulentKineticEnergy']
                        initial_values['omega'] = inlet_bc['SpecificDissipationRate']
                        initial_values['gammaInt'] = inlet_bc['Intermittency']
                        initial_values['ReThetat'] = inlet_bc['ReThetat']
                    elif inlet_bc['TurbulenceInletSpecification'] == 'TurbulentViscosity':
                        initial_values['nut'] = inlet_bc['TurbulentViscosity']
                    elif inlet_bc['TurbulenceInletSpecification'] == 'TurbulentViscosityAndK':
                        initial_values['k'] = inlet_bc['kEqnTurbulentKineticEnergy']
                        initial_values['nut'] = inlet_bc['kEqnTurbulentViscosity']
                    elif inlet_bc['TurbulenceInletSpecification'] == 'intensityAndLengthScale':
                        if inlet_bc['BoundarySubType'] == 'uniformVelocityInlet' or \
                           inlet_bc['BoundarySubType'] == 'farField':
                            Uin = (inlet_bc['Ux']**2 +
                                   inlet_bc['Uy']**2 +
                                   inlet_bc['Uz']**2)**0.5

                            # Turb Intensity (or Tu) and length scale
                            I = inlet_bc['TurbulenceIntensityPercentage'] / 100.0  # Convert from percent to fraction
                            l = inlet_bc['TurbulenceLengthScale']
                            Cmu = 0.09  # Standard turbulence model parameter

                            # k omega, k epsilon
                            k = 3.0/2.0*(Uin*I)**2
                            omega = k**0.5/(Cmu**0.25*l)
                            epsilon = (k**(3.0/2.0) * Cmu**0.75) / l

                            # Spalart Allmaras
                            nuTilda = inlet_bc['NuTilda']

                            # k omega (transition)
                            gammaInt = 1
                            ReThetat = self.reThetatFromIntensity(inlet_bc['TurbulenceIntensityPercentage'])

                            # Set the values
                            initial_values['k'] = k
                            initial_values['omega'] = omega
                            initial_values['epsilon'] = epsilon
                            initial_values['nuTilda'] = nuTilda
                            initial_values['gammaInt'] = gammaInt
                            initial_values['ReThetat'] = ReThetat

                        else:
                            raise RuntimeError(
                                "Inlet type currently unsupported for copying turbulence initial conditions.")
                    else:
                        raise RuntimeError(
                            "Turbulence inlet specification currently unsupported for copying turbulence initial conditions")
                else:
                    raise RuntimeError("No boundary selected to copy initial turbulence values from.")
            #TODO: Check that the required values have actually been set for each turbulent model

        # Incompressible solvers work in kinematic pressure. This must be derived
        # after the 'Copy pressure' block above, so that an outlet-derived
        # Pressure (UseOutletPValue) is reflected in the initial field.
        if settings['solver']['SolverName'] in ['simpleFoam', 'porousSimpleFoam', 'pimpleFoam', 'SRFSimpleFoam']:
            mat_prop = settings['fluidProperties'][0]
            initial_values['KinematicPressure'] = initial_values['Pressure'] / mat_prop['Density']

    # Function objects (reporting functions, probes)
    def processReportingFunctions(self):
        """ Compute any Function objects required before case build """
        settings = self.settings
        settings['reportingFunctionsEnabled'] = True

        for name in settings['reportingFunctions']:
            rf = settings['reportingFunctions'][name]

            if rf['ReportingFunctionType'] == 'Force' or rf['ReportingFunctionType'] == 'ForceCoefficients':
                rf['PatchName'] = rf['Patch'].Label

            if rf['ReportingFunctionType'] == 'ForceCoefficients':
                rf['Pitch'] = Vector(rf['Lift']).cross(Vector(rf['Drag']))
                rf['Pitch'] = tuple(p for p in rf['Pitch'])

    def processScalarTransportFunctions(self):
        settings = self.settings
        settings['scalarTransportFunctionsEnabled'] = True
        for name in settings['scalarTransportFunctions']:
            stf = settings['scalarTransportFunctions'][name]
            if settings['solver']['SolverName'] in ['simpleFoam', 'porousSimpleFoam', 'pimpleFoam']:
                stf['InjectionRate'] = stf['InjectionRate']/settings['fluidProperties'][0]['Density']
                stf['DiffusivityFixedValue'] = stf['DiffusivityFixedValue']/settings['fluidProperties'][0]['Density']

    # Mesh related
    def processDynamicMeshRefinement(self):
        settings = self.settings
        settings['dynamicMeshEnabled'] = True

        # Check whether cellLevel supported
        if self.mesh_obj.MeshUtility not in ['cfMesh', 'snappyHexMesh']:
            raise RuntimeError("Dynamic mesh refinement is only supported by cfMesh and snappyHexMesh")
    
        # Check whether 2D extrusion present
        mesh_refinements = CfdTools.getMeshRefinementObjs(self.mesh_obj)
        for mr in mesh_refinements:
            if mr.Extrusion:
                if mr.ExtrusionType == '2DPlanar' or mr.ExtrusionType == '2DWedge':
                    raise RuntimeError("Dynamic mesh refinement will not work with 2D or wedge mesh")
        
        settings['dynamicMesh'] = CfdTools.propsToDict(self.dynamic_mesh_refinement_obj)
        if isinstance(self.dynamic_mesh_refinement_obj.Proxy, CfdDynamicMeshRefinement.CfdDynamicMeshShockRefinement):
            settings['dynamicMesh']['Type'] = 'shock'
            settings['dynamicMesh']['RefinementLevel'] = CfdTools.relLenToRefinementLevel(
                self.dynamic_mesh_refinement_obj.RelativeElementSize)
        else:
            settings['dynamicMesh']['Type'] = 'interface'

    def processMultiRegionBoundaries(self):
        """Use selected mesh geometry and stored interface partners, not geometric guesses."""
        settings = self.settings
        regions = {}
        for mesh in self.mesh_objs:
            name = CfdTools.getRegionName(mesh)
            regions[name] = (self._getMeshRegionType(mesh), mesh.Part, _shape_from_mesh_object(mesh))
        maps = {kind: {name: {} for name, (role, _, _) in regions.items() if role == kind}
                for kind in ('fluid', 'solid')}
        boundaries = {bc.Label: bc for bc in self.bc_group}
        couples = {}
        for bc in self.bc_group:
            is_default = getattr(bc, 'DefaultBoundary', False)
            if not is_default and not _faces_from_shape_refs(bc.ShapeRefs):
                raise ValueError("Boundary '{}' has no selected faces.".format(bc.Label))
            owners = set()
            if is_default:
                # Default fluid boundaries apply to the remaining fluid faces.
                owners.update(name for name, (role, _, _) in regions.items() if role == 'fluid')
            elif hasattr(bc, 'InterfaceObject'):
                if bc.RegionName not in regions:
                    raise ValueError("Boundary '{}' references an unmeshed region '{}'.".format(
                        bc.Label, bc.RegionName))
                owners.add(bc.RegionName)
            else:
                for obj, subs in bc.ShapeRefs:
                    for face in _faces_from_shape_refs([(obj, subs)]):
                        matches = [name for name, (_, part, shape) in regions.items()
                                   if part == obj and any(face.isSame(f) for f in shape.Faces)]
                        if len(matches) != 1:
                            message = ("must reference faces on a solid region" if
                                       getattr(bc, 'SolidBoundary', False) else
                                       "must reference faces on exactly one meshed region")
                            raise ValueError("Boundary '{}' {}: '{}' has no unique owner.".format(
                                bc.Label, message, obj.Label))
                        owners.add(matches[0])
            if getattr(bc, 'SolidBoundary', False):
                if bc.BoundaryType != 'wall' or bc.BoundarySubType != 'fixedWall':
                    raise ValueError("Solid boundary '{}' must use a stationary wall.".format(bc.Label))
                if any(regions[name][0] != 'solid' for name in owners):
                    raise ValueError("Solid boundary '{}' must reference faces on a solid region.".format(bc.Label))
                if any(not subs for _, subs in bc.ShapeRefs):
                    raise ValueError("Solid boundary '{}' must reference faces, not whole solids.".format(bc.Label))
            for name in owners:
                maps[regions[name][0]][name][bc.Label] = settings['boundaries'][bc.Label]
            if bc.BoundaryType != 'wall' or bc.BoundarySubType != 'regionCoupledWall':
                continue
            partners = getattr(bc, 'PartnerBoundaryLabels', [])
            if not hasattr(bc, 'InterfaceObject') or not partners:
                raise ValueError("Boundary '{}' has no explicit interface pair. "
                                 "Generate interface faces in Region-coupled interface settings.".format(bc.Label))
            for label in partners:
                partner = boundaries.get(label)
                if (partner is None or getattr(partner, 'InterfaceObject', None) != bc.InterfaceObject or
                        partner.BoundarySubType != 'regionCoupledWall' or
                        bc.Label not in partner.PartnerBoundaryLabels or
                        partner.RegionName == bc.RegionName):
                    raise ValueError("Boundary '{}' has an invalid interface partner '{}'.".format(bc.Label, label))
                sides = sorted([(bc.RegionName, bc.Label), (partner.RegionName, partner.Label)])
                key = "{}_{}_to_{}_{}".format(*sides[0], *sides[1])
                couples[key] = {
                    'MasterRegion': sides[0][0], 'MasterPatch': sides[0][1],
                    'SlaveRegion': sides[1][0], 'SlavePatch': sides[1][1],
                }
        for kind in ('fluid', 'solid'):
            prefix = 'multiRegion' + kind.capitalize()
            settings[prefix + 'BoundariesByRegion'] = maps[kind]
            settings[prefix + 'Boundaries'] = {
                label: value for region in maps[kind].values() for label, value in region.items()}
        settings['multiRegionNonConformalCouples'] = couples
        settings['multiRegionNonConformalCouplesPresent'] = bool(couples)

    # Zones
    def exportZoneStlSurfaces(self):
        for zo in self.zone_objs:
            for r in zo.ShapeRefs:
                path = os.path.join(self.working_dir,
                                    self.solver_obj.InputCaseName,
                                    "constant",
                                    "triSurface")
                if not os.path.exists(path):
                    os.makedirs(path)
                sel_obj = r[0]
                shape = sel_obj.Shape
                CfdMeshTools.writeSurfaceMeshFromShape(shape, path, r[0].Name, self.mesh_obj)
                print("Successfully wrote stl surface\n")

    def processPorousZoneProperties(self):
        settings = self.settings
        settings['porousZonesPresent'] = True
        porousZoneSettings = settings['porousZones']
        for po in self.porous_zone_objs:
            pd = {'PartNameList': tuple(r[0].Name for r in po.ShapeRefs)}
            po = CfdTools.propsToDict(po)
            if po['PorousCorrelation'] == 'DarcyForchheimer':
                pd['D'] = (po['D1'], po['D2'], po['D3'])
                pd['F'] = (po['F1'], po['F2'], po['F3'])
                pd['e1'] = po['e1']
                pd['e3'] = po['e3']
            elif po['PorousCorrelation'] == 'Jakob':
                # Calculate effective Darcy-Forchheimer coefficients
                # This is for equilateral triangles arranged with the triangles pointing in BundleLayerNormal
                # direction (direction of greater spacing - sqrt(3)*triangleEdgeLength)
                pd['e1'] = po['SpacingDirection']  # OpenFOAM modifies to be orthog to e3
                pd['e3'] = po['TubeAxis']
                spacing = po['TubeSpacing']
                d0 = po['OuterDiameter']
                u0 = po['VelocityEstimate']
                aspectRatio = po['AspectRatio']
                kinVisc = self.settings['fluidProperties']['KinematicViscosity']
                if kinVisc == 0.0:
                    raise ValueError("Viscosity must be set for Jakob correlation")
                if spacing < d0:
                    raise ValueError("Tube spacing may not be less than diameter")
                D = [0, 0, 0]
                F = [0, 0, 0]
                for (i, Sl, St) in [(0, aspectRatio*spacing, spacing), (1, spacing, aspectRatio*spacing)]:
                    C = 1.0/St*0.5*(1.0+0.47/(Sl/d0-1)**1.06)*(1.0/(1-d0/Sl))**(2.0-0.16)
                    Di = C/d0*0.5*(u0*d0/kinVisc)**(1.0-0.16)
                    Fi = C*(u0*d0/kinVisc)**(-0.16)
                    D[i] = Di
                    F[i] = Fi
                pd['D'] = tuple(D)
                pd['F'] = tuple(F)
                # Currently assuming zero drag parallel to tube bundle (3rd principal dirn)
            else:
                raise RuntimeError("Unrecognised method for porous baffle resistance")
            porousZoneSettings[po['Label']] = pd

    # Mean velocity force cell zones
    def exportMeanVelocityForceCellZoneStlSurfaces(self):
        for o in self.mean_velocity_force_cellzone_objs:
            force_name = o.Name
            force_label = o.Label
            direction = tuple(p for p in o.Direction)
            ubar = tuple(p for p in o.Ubar)
            relaxation = o.Relaxation
            part_name_list = []
            cylinder_specs = getattr(o, 'CellZoneCylinderSpecs', [])
            if cylinder_specs:
                path = os.path.join(self.working_dir,
                                    self.solver_obj.InputCaseName,
                                    "constant",
                                    "triSurface")
                if not os.path.exists(path):
                    os.makedirs(path)
                for spec in cylinder_specs:
                    name, radius, height, x, y, z = [v.strip() for v in spec.split(',')]
                    self._writeMeanVelocityForceCylinderStl(
                        name, float(radius), float(height), Vector(float(x), float(y), float(z)), path)
                    part_name_list.append(name)
                    print("Successfully wrote stl surface for mean velocity force cell zone\n")
                self._cacheMeanVelocityForceSettings(
                    force_name, force_label, part_name_list, direction, ubar, relaxation)
                continue
            for part_obj in self._getMeanVelocityForceCellZonePartObjects(o):
                path = os.path.join(self.working_dir,
                                    self.solver_obj.InputCaseName,
                                    "constant",
                                    "triSurface")
                if not os.path.exists(path):
                    os.makedirs(path)
                if part_obj.TypeId == "Part::Cylinder":
                    self._writeMeanVelocityForceCylinderStl(
                        part_obj.Name,
                        Units.Quantity(part_obj.Radius, Units.Length).getValueAs("mm"),
                        Units.Quantity(part_obj.Height, Units.Length).getValueAs("mm"),
                        part_obj.Placement.Base,
                        path)
                else:
                    shape = part_obj.Shape
                    CfdMeshTools.writeSurfaceMeshFromShape(shape, path, part_obj.Name, self.mesh_obj)
                part_name_list.append(part_obj.Name)
                print("Successfully wrote stl surface for mean velocity force cell zone\n")
            self._cacheMeanVelocityForceSettings(
                force_name, force_label, part_name_list, direction, ubar, relaxation)

    def _cacheMeanVelocityForceSettings(self, force_name, force_label, part_name_list, direction, ubar, relaxation):
        part_name_tuple = tuple(part_name_list)
        self._mean_velocity_force_part_names[force_name] = part_name_tuple
        self._mean_velocity_force_settings[force_name] = {
            'Label': force_label,
            'PartNameList': part_name_tuple,
            'Direction': direction,
            'Ubar': ubar,
            'Relaxation': relaxation,
        }

    def _getMeanVelocityForceCellZonePartObjects(self, force_obj):
        doc = self.analysis_obj.Document
        part_names = getattr(force_obj, 'CellZoneShapeNames', [])
        if part_names:
            part_objs = []
            for part_name in part_names:
                part_obj = doc.getObject(part_name)
                if part_obj is None:
                    raise RuntimeError(
                        "Mean velocity force cell zone object '{}' was not found".format(part_name))
                part_objs.append(part_obj)
            return part_objs
        return [r[0] for r in force_obj.ShapeRefs]

    def _writeMeanVelocityForceCylinderStl(self, name, radius, height, base, path):
        output_file_name = os.path.join(path, name + '.stl')
        scaling_factor = Units.Quantity(1, Units.Length).getValueAs("m")
        segments = 96

        def point(x, y, z):
            p = (base + Vector(x, y, z)) * scaling_factor
            return (p.x, p.y, p.z)

        bottom_center = point(0, 0, 0)
        top_center = point(0, 0, height)
        bottom = []
        top = []
        for i in range(segments):
            angle = 2.0 * math.pi * i / segments
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            bottom.append(point(x, y, 0))
            top.append(point(x, y, height))

        def normal(p1, p2, p3):
            ux, uy, uz = (p2[i] - p1[i] for i in range(3))
            vx, vy, vz = (p3[i] - p1[i] for i in range(3))
            nx = uy * vz - uz * vy
            ny = uz * vx - ux * vz
            nz = ux * vy - uy * vx
            mag = (nx * nx + ny * ny + nz * nz) ** 0.5
            if mag == 0:
                return (0.0, 0.0, 0.0)
            return (nx / mag, ny / mag, nz / mag)

        def write_facet(fid, p1, p2, p3):
            n = normal(p1, p2, p3)
            fid.write(" facet normal {} {} {}\n".format(*n))
            fid.write("  outer loop\n")
            for p in (p1, p2, p3):
                fid.write("   vertex {} {} {}\n".format(*p))
            fid.write("  endloop\n")
            fid.write(" endfacet\n")

        with open(output_file_name, 'w') as fid:
            fid.write("solid {}\n".format(name))
            for i in range(segments):
                j = (i + 1) % segments
                write_facet(fid, bottom[i], bottom[j], top[j])
                write_facet(fid, bottom[i], top[j], top[i])
                write_facet(fid, bottom_center, bottom[i], bottom[j])
                write_facet(fid, top_center, top[j], top[i])
            fid.write("endsolid {}\n".format(name))

    def processMeanVelocityForceCellZoneProperties(self):
        settings = self.settings
        settings['meanVelocityForceCellZonesPresent'] = True
        settings['fvOptionsPresent'] = True
        if self._mean_velocity_force_settings:
            zone_settings = list(self._mean_velocity_force_settings.values())
        else:
            zone_settings = []
            for o in self.mean_velocity_force_cellzone_objs:
                part_name_list = tuple(
                    part_obj.Name for part_obj in self._getMeanVelocityForceCellZonePartObjects(o))
                zone_settings.append({
                    'Label': o.Label,
                    'PartNameList': part_name_list,
                    'Direction': tuple(p for p in o.Direction),
                    'Ubar': tuple(p for p in o.Ubar),
                    'Relaxation': o.Relaxation,
                })
        for zone_setting in zone_settings:
            zone_label = zone_setting['Label']
            settings['meanVelocityForceCellZones'][zone_label] = {
                'PartNameList': zone_setting['PartNameList'],
                'Direction': zone_setting['Direction'],
                'Ubar': zone_setting['Ubar'],
                'Relaxation': zone_setting['Relaxation'],
            }
            if not settings['multiRegionEnabled']:
                # Register the zone for topoSetZonesDict so the cellZoneSet is created
                settings['zones'][zone_label] = {'PartNameList': zone_setting['PartNameList']}
        if not settings['multiRegionEnabled']:
            settings['zonesPresent'] = True

    def processInitialisationZoneProperties(self):
        settings = self.settings
        
        for zone_name in settings['initialisationZones']:
            z = settings['initialisationZones'][zone_name]

            if not z['VolumeFractionSpecified']:
                del z['VolumeFractions']
            if not z['VelocitySpecified']:
                del z['Ux']
                del z['Uy']
                del z['Uz']
            if not z['PressureSpecified']:
                del z['Pressure']
            if not z['TemperatureSpecified']:
                del z['Temperature']

            if settings['solver']['SolverName'] in ['interFoam', 'multiphaseInterFoam']:
                # Make sure the first n-1 alpha values exist, and write the n-th one
                # consistently for multiphaseInterFoam
                sum_alpha = 0.0
                if 'VolumeFractions' in z:
                    alphas_new = {}
                    for i, m in enumerate(settings['fluidProperties']):
                        alpha_name = m['Name']
                        if i == len(settings['fluidProperties'])-1:
                            if settings['solver']['SolverName'] == 'multiphaseInterFoam':
                                alphas_new[alpha_name] = 1.0-sum_alpha
                        else:
                            alpha = Units.Quantity(z['VolumeFractions'].get(alpha_name, '0')).Value
                            alphas_new[alpha_name] = alpha
                            sum_alpha += alpha
                    z['VolumeFractions'] = alphas_new
        
            if settings['solver']['SolverName'] in ['simpleFoam', 'porousSimpleFoam', 'pimpleFoam', 'SRFSimpleFoam']:
                if 'Pressure' in z:
                    z['KinematicPressure'] = z['Pressure']/settings['fluidProperties'][0]['Density']

    def bafflesPresent(self):
        for b in self.bc_group:
            if b.BoundaryType == 'baffle':
                return True
        return False

    def porousBafflesPresent(self):
        for b in self.bc_group:
            if b.BoundaryType == 'baffle' and \
               b.BoundarySubType == 'porousBaffle':
                return True
        return False

    def setupPatchNames(self):
        print('Populating createPatchDict to update BC names')
        settings = self.settings
        settings['createPatches'] = {}
        settings['createPatchesSnappyBaffles'] = {}
        settings['createPeriodics'] = {}
        bc_group = self.bc_group

        defaultPatchType = "patch"
        for bc_id, bc_obj in enumerate(bc_group):
            bcType = bc_obj.BoundaryType
            bcSubType = bc_obj.BoundarySubType
            patchType = CfdTools.getPatchType(bcType, bcSubType)

            if not bcType == 'baffle' and not bcSubType == 'cyclicAMI':
                settings['createPatches'][bc_obj.Label] = {
                    'PatchNamesList': '"' + CfdTools.getBoundaryPatchPrefix(bc_obj, bc_id) + '_.*"',
                    'PatchType': patchType
                }

            if bc_obj.DefaultBoundary:
                defaultPatchType = patchType

            if bcType == 'baffle' and self.mesh_obj.MeshUtility == 'snappyHexMesh':
                settings['createPatchesFromSnappyBaffles'] = True
                settings['createPatchesSnappyBaffles'][bc_obj.Label] = {
                    'PatchNamesList': '"'+bc_obj.Name+'_[^_]*"',
                    'PatchNamesListSlave': '"'+bc_obj.Name+'_.*_slave"'}

            if bcSubType == 'cyclicAMI':
                settings['createPatchesForPeriodics'] = True
                if bc_obj.PeriodicMaster:
                    slave_bc_obj = None
                    slave_bc_id = -1
                    for bc_id2, bc_obj2 in enumerate(bc_group):
                        if bc_obj2.PeriodicPartner == bc_obj.Label:
                            slave_bc_obj = bc_obj2
                            slave_bc_id = bc_id2
                            break
                    if slave_bc_obj is None:
                        raise ValueError("No periodic slave boundary linked to master boundary {} was found.".format(
                            bc_obj.Label))
                    settings['createPeriodics'][bc_obj.Label] = {
                        'PeriodicMaster': bc_obj.PeriodicMaster,
                        'PeriodicPartner': slave_bc_obj.Label if bc_obj.PeriodicMaster else slave_bc_obj.PeriodicPartner,
                        'RotationalPeriodic': slave_bc_obj.RotationalPeriodic,
                        'PeriodicCentreOfRotation': tuple(
                            Units.Quantity(p, Units.Length).getValueAs('m').Value
                            for p in slave_bc_obj.PeriodicCentreOfRotation),
                        'PeriodicCentreOfRotationAxis': tuple(p for p in slave_bc_obj.PeriodicCentreOfRotationAxis),
                        'PeriodicSeparationVector': tuple(
                            Units.Quantity(p, Units.Length).getValueAs('m').Value
                            for p in slave_bc_obj.PeriodicSeparationVector),
                        'PatchNamesList': '"patch_'+str(bc_id+1)+'_.*"',
                        'PatchNamesListSlave': '"patch_'+str(slave_bc_id+1)+'_.*"'}

        # Set up default BC for unassigned faces
        settings['createPatches']['defaultFaces'] = {
            'PatchNamesList': '"patch_0_0"',
            'PatchType': defaultPatchType
        }

        # Assign any extruded patches as the appropriate type
        mr_objs = CfdTools.getMeshRefinementObjs(self.mesh_obj)
        for mr_id, mr_obj in enumerate(mr_objs):
            if mr_obj.Extrusion and mr_obj.ExtrusionType == "2DPlanar":
                settings['createPatches'][mr_obj.Label] = {
                    'PatchNamesList': '"patch_.*_'+str(mr_id+1)+'"',
                    'PatchType': "empty"
                }
            elif mr_obj.Extrusion and mr_obj.ExtrusionType == "2DWedge":
                settings['createPatches'][mr_obj.Label] = {
                    'PatchNamesList': '"patch_.*_'+str(mr_id+1)+'"',
                    'PatchType': "symmetry"
                }
            else:
                # Add others to default faces list
                settings['createPatches']['defaultFaces']['PatchNamesList'] += ' "patch_0_'+str(mr_id+1) + '"'
