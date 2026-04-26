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
from FreeCAD import Units, Vector
from CfdOF import CfdTools
from CfdOF.TemplateBuilder import TemplateBuilder
from CfdOF.CfdTools import cfdMessage
from CfdOF.Mesh import CfdMeshTools
from CfdOF.Mesh import CfdDynamicMeshRefinement
from CfdOF.Solve.CfdSolidMaterial import CfdSolidMaterial



def _getCompoundLinks(part_obj):
    """Return the list of child body objects from a compound or BooleanFragments shape object."""
    if hasattr(part_obj, 'Links'):      # Part::Compound
        return list(part_obj.Links)
    if hasattr(part_obj, 'Shapes'):     # Part::BooleanFragments (older FreeCAD)
        return list(part_obj.Shapes)
    if hasattr(part_obj, 'Objects'):    # Part::BooleanFragments (FreeCAD 1.x)
        return list(part_obj.Objects)
    return [part_obj]


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
        self.mesh_obj = CfdTools.getMesh(analysis_obj)
        if not self.mesh_obj:
            raise RuntimeError("No mesh object was found in analysis " + analysis_obj.Label)
        self.material_objs = CfdTools.getMaterials(analysis_obj)
        self.solid_material_objs = CfdTools.getSolidMaterials(analysis_obj)
        if not self.material_objs and not self.solid_material_objs:
            raise RuntimeError("No material properties were found in analysis " + analysis_obj.Label)
        self.bc_group = CfdTools.getCfdBoundaryGroup(analysis_obj)
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
            'initialValues': CfdTools.propsToDict(self.initial_conditions),
            'boundaries': dict((b.Label, CfdTools.propsToDict(b)) for b in self.bc_group),
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
                    'MMRModelRPS': (mr_obj.MMRModelRPM/9.5) # rad/s #for the openCFD version
                }

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
            self._checkChtGeometryConformality()
            self.exportChtRegionStlSurfaces()
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

        # For CHT: rename template fluid/solid subdirs to actual region names so the
        # solver finds thermophysicalProperties, fvSchemes, etc. in the right places.
        self._renameChtRegionDirs()

        # Update Allrun permission - will fail silently on Windows
        file_name = os.path.join(self.case_folder, "Allrun")
        import stat
        s = os.stat(file_name)
        os.chmod(file_name, s.st_mode | stat.S_IEXEC)

        cfdMessage("Successfully wrote case to folder {}\n".format(self.working_dir))
        if self.progressCallback:
            self.progressCallback("Case written successfully")

        return True

    def _renameChtRegionDirs(self):
        """Rename constant/fluid, 0/fluid, system/fluid template subdirs to actual fluid region name.

        Solid region files are written directly to per-region paths by the template's
        filename-loop mechanism, so no renaming is needed for solids.
        """
        import shutil
        fluid_names = self.settings.get('multiRegionFluidNames', [])
        if not fluid_names:
            return
        for top in ('constant', '0', 'system'):
            src = os.path.join(self.case_folder, top, 'fluid')
            dst = os.path.join(self.case_folder, top, fluid_names[0])
            if src == dst or not os.path.isdir(src):
                continue
            if os.path.isdir(dst):
                for fname in os.listdir(src):
                    shutil.copy2(os.path.join(src, fname), os.path.join(dst, fname))
                shutil.rmtree(src)
            else:
                os.rename(src, dst)

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
        system_settings['FoamRuntime'] = CfdTools.getFoamRuntime()
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

        # Process dedicated CfdSolidMaterial objects (new path)
        for solid_obj in self.solid_material_objs:
            mp = solid_obj.Material.copy()
            mp['Name'] = solid_obj.Label
            region_name = getattr(solid_obj, 'RegionName', '') or solid_obj.Label
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
            mp['HeatGenerationActive'] = 'true' if heat_gen > 0 else 'false'
            settings['solidProperties'].append(mp)
            settings['multiRegionSolidNames'].append(region_name)

        for material_obj in self.material_objs:
            mp = material_obj.Material.copy()
            mp['Name'] = material_obj.Label
            # Legacy: CfdFluidMaterial with Category='Solid' (backward compatibility)
            is_solid = (getattr(material_obj, 'Category', 'Fluid') == 'Solid')
            explicit_region = getattr(material_obj, 'RegionName', '')
            if explicit_region:
                region_name = explicit_region
            elif is_multiregion and not is_solid:
                # Derive fluid region name from the Internal mesh refinement zone label so the
                # user does not have to set RegionName manually. Falls back to material Label.
                mr_objs = CfdTools.getMeshRefinementObjs(self.mesh_obj)
                internal_zones = [o.Label for o in mr_objs if o.Internal]
                region_name = internal_zones[0] if internal_zones else material_obj.Label
            else:
                region_name = material_obj.Label

            if is_solid and is_multiregion:
                if 'ThermalConductivity' in mp:
                    mp['ThermalConductivity'] = Units.Quantity(mp['ThermalConductivity']).getValueAs("W/m/K").Value
                if 'Density' in mp:
                    mp['Density'] = Units.Quantity(mp['Density']).getValueAs("kg/m^3").Value
                if 'SpecificHeat' in mp:
                    mp['Cp'] = Units.Quantity(mp['SpecificHeat']).getValueAs("J/kg/K").Value
                if hasattr(material_obj, 'HeatGeneration'):
                    heat_gen = material_obj.HeatGeneration.getValueAs("W/m^3").Value
                else:
                    heat_gen = 0.0
                mp['HeatGeneration'] = heat_gen
                mp['HeatGenerationActive'] = 'true' if heat_gen > 0 else 'false'
                settings['solidProperties'].append(mp)
                settings['multiRegionSolidNames'].append(region_name)
                continue

            if is_multiregion:
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
            settings['multiRegionFluidNamesDict'] = {n: {} for n in settings['multiRegionFluidNames']}
            settings['multiRegionSolidNamesDict'] = {n: {} for n in settings['multiRegionSolidNames']}

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
            if physics['Turbulence'] == 'RANS' and physics['TurbulenceModel'] == 'SpalartAllmaras':
                if (bc['BoundaryType'] == 'inlet' or bc['BoundaryType'] == 'open') and \
                        bc['TurbulenceInletSpecification'] == 'intensityAndLengthScale':
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
        if settings['solver']['SolverName'] in ['simpleFoam', 'porousSimpleFoam', 'pimpleFoam', 'SRFSimpleFoam']:
            mat_prop = settings['fluidProperties'][0]
            initial_values['KinematicPressure'] = initial_values['Pressure'] / mat_prop['Density']
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
                            if I <= 1.3:
                                ReThetat = 1173.51 - (589.428 * I) + (0.2196 / (I**2))
                            else:
                                ReThetat = 331.5 / ((I - 0.5658)**0.671)

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

    # Multi-region CHT
    def exportChtRegionStlSurfaces(self):
        """Export STL surfaces for CHT regions.

        Fluid regions: sourced from Internal CfdMeshRefinement zones matching multiRegionFluidNames.
        Solid regions: sourced from CfdSolidMaterial.ShapeRefs (new path) or legacy Internal zones.
        """
        settings = self.settings
        path = os.path.join(self.working_dir, self.solver_obj.InputCaseName, "constant", "triSurface")

        # Fluid regions: use Internal mesh refinement zones
        mr_objs = CfdTools.getMeshRefinementObjs(self.mesh_obj)
        fluid_zones_written = set()
        for mr_obj in mr_objs:
            if mr_obj.Internal and mr_obj.Label in settings['multiRegionFluidNames']:
                if not os.path.exists(path):
                    os.makedirs(path)
                for r in mr_obj.ShapeRefs:
                    CfdMeshTools.writeSurfaceMeshFromShape(r[0].Shape, path, mr_obj.Label, self.mesh_obj)
                    cfdMessage("Wrote STL for fluid region '{}'\n".format(mr_obj.Label))
                settings['zones'][mr_obj.Label] = {'PartNameList': (mr_obj.Label,)}
                fluid_zones_written.add(mr_obj.Label)

        # Fallback: if no Internal zone was found for a fluid region, derive the fluid body
        # from the compound mesh part by excluding known solid bodies.
        solid_obj_names = set()
        for solid_obj in self.solid_material_objs:
            for r in solid_obj.ShapeRefs:
                solid_obj_names.add(r[0].Name)
        for region_name in settings['multiRegionFluidNames']:
            if region_name not in fluid_zones_written:
                mesh_part = self.mesh_obj.Part
                compound_links = _getCompoundLinks(mesh_part)
                fluid_bodies = [lnk for lnk in compound_links if lnk.Name not in solid_obj_names]
                if fluid_bodies:
                    if not os.path.exists(path):
                        os.makedirs(path)
                    for body in fluid_bodies:
                        CfdMeshTools.writeSurfaceMeshFromShape(body.Shape, path, region_name, self.mesh_obj)
                    cfdMessage("Wrote STL for fluid region '{}' (auto-derived from compound)\n".format(region_name))
                    settings['zones'][region_name] = {'PartNameList': (region_name,)}
                else:
                    cfdMessage("Warning: no geometry found for fluid region '{}' - "
                               "add an Internal mesh refinement zone\n".format(region_name))

        # Solid regions: use CfdSolidMaterial.ShapeRefs directly
        for solid_obj in self.solid_material_objs:
            region_name = getattr(solid_obj, 'RegionName', '') or solid_obj.Label
            if not os.path.exists(path):
                os.makedirs(path)
            for r in solid_obj.ShapeRefs:
                CfdMeshTools.writeSurfaceMeshFromShape(r[0].Shape, path, region_name, self.mesh_obj)
                cfdMessage("Wrote STL for solid region '{}'\n".format(region_name))
            settings['zones'][region_name] = {'PartNameList': (region_name,)}

        # Legacy: solid regions from Internal mesh refinement zones (CfdFluidMaterial Category='Solid')
        for mr_obj in mr_objs:
            if mr_obj.Internal and mr_obj.Label in settings['multiRegionSolidNames']:
                if mr_obj.Label not in settings['zones']:  # skip if already handled above
                    if not os.path.exists(path):
                        os.makedirs(path)
                    for r in mr_obj.ShapeRefs:
                        CfdMeshTools.writeSurfaceMeshFromShape(r[0].Shape, path, mr_obj.Label, self.mesh_obj)
                        cfdMessage("Wrote STL for solid region '{}'\n".format(mr_obj.Label))
                    settings['zones'][mr_obj.Label] = {'PartNameList': (mr_obj.Label,)}

        # For gmsh CHT cases, cell zones come directly from per-region Physical Volumes
        # in the .geo file (written by CfdMeshTools). topoSet zone creation is not needed.
        if (settings['multiRegionFluidNames'] or settings['multiRegionSolidNames']) and \
                self.mesh_obj.MeshUtility != 'gmsh':
            settings['zonesPresent'] = True

    def _checkChtGeometryConformality(self):
        """Warn if solid bodies are enclosed inside fluid bodies without shared faces (non-conformal topology).

        A simple Part::Compound of an enclosed heatsink produces non-conformal mesh —
        splitMeshRegions won't create an interface patch in the fluid region.
        BooleanFragments is required to create shared surfaces.
        """
        if self.mesh_obj.MeshUtility != 'gmsh':
            return
        if not self.solid_material_objs:
            return
        mesh_part = self.mesh_obj.Part
        links = _getCompoundLinks(mesh_part)
        if len(links) < 2:
            return
        solid_names = set()
        for solid_obj in self.solid_material_objs:
            for r in solid_obj.ShapeRefs:
                solid_names.add(r[0].Name)
        fluid_links = [lnk for lnk in links if lnk.Name not in solid_names]
        solid_links = [lnk for lnk in links if lnk.Name in solid_names]
        if not fluid_links or not solid_links:
            return
        # Check whether any solid body shares a face with the fluid compound shape.
        # If the compound has no shared/fused topology (i.e. it was created with
        # Part::Compound rather than BooleanFragments), the sub-shapes are independent
        # and share no faces. We detect this by checking if the compound compound object
        # has a Links attribute (Part::Compound) and its Placement is default — a proxy
        # for "not Boolean-fused". A more robust check: count faces in compound vs sum of faces.
        compound_shape = mesh_part.Shape
        sub_face_count = sum(len(lnk.Shape.Faces) for lnk in links)
        compound_face_count = len(compound_shape.Faces)
        if compound_face_count >= sub_face_count:
            # No face reduction means no shared faces — BooleanFragments reduces face count
            # by merging coincident faces into one shared face.
            # Only warn if at least one solid body is spatially enclosed in a fluid body
            # (bounding box of solid is inside bounding box of a fluid link).
            for s_lnk in solid_links:
                s_bb = s_lnk.Shape.BoundBox
                for f_lnk in fluid_links:
                    f_bb = f_lnk.Shape.BoundBox
                    if (f_bb.XMin <= s_bb.XMin and f_bb.XMax >= s_bb.XMax and
                            f_bb.YMin <= s_bb.YMin and f_bb.YMax >= s_bb.YMax and
                            f_bb.ZMin <= s_bb.ZMin and f_bb.ZMax >= s_bb.ZMax):
                        cfdMessage(
                            "WARNING: Solid body '{}' appears to be enclosed inside fluid body '{}', "
                            "but the compound was not created with BooleanFragments. "
                            "This will produce a non-conformal mesh — splitMeshRegions will NOT create "
                            "a defaultFaces interface patch in the fluid region and the CHT solver will "
                            "fail. Use Part → Boolean → BooleanFragments instead of Part → Create a "
                            "compound.\n".format(s_lnk.Label, f_lnk.Label))

    def processMultiRegionBoundaries(self):
        """Categorize boundary conditions by region (fluid vs solid) for CHT cases."""
        settings = self.settings
        fluid_region_shapes = set()
        solid_region_shapes = set()

        # Fluid region shapes from Internal mesh refinement zones
        mr_objs = CfdTools.getMeshRefinementObjs(self.mesh_obj)
        for mr_obj in mr_objs:
            if mr_obj.Internal:
                for r in mr_obj.ShapeRefs:
                    if mr_obj.Label in settings['multiRegionFluidNames']:
                        fluid_region_shapes.add(r[0].Name)

        # Solid region shapes from CfdSolidMaterial.ShapeRefs (new path)
        solid_shapes_geom = []  # actual FreeCAD shapes for geometry-based fallback
        for solid_obj in self.solid_material_objs:
            for r in solid_obj.ShapeRefs:
                solid_region_shapes.add(r[0].Name)
                # Also add names of all child features (e.g. PartDesign Pad inside Body)
                for child in getattr(r[0], 'OutList', []):
                    if hasattr(child, 'Shape'):
                        solid_region_shapes.add(child.Name)
                # Collect actual shape for geometry fallback
                try:
                    solid_shapes_geom.append(r[0].Shape)
                except Exception:
                    pass

        # Legacy: solid region shapes from Internal mesh refinement zones
        for mr_obj in mr_objs:
            if mr_obj.Internal and mr_obj.Label in settings['multiRegionSolidNames']:
                for r in mr_obj.ShapeRefs:
                    solid_region_shapes.add(r[0].Name)

        # Auto-detect fluid shapes: compound children that are not solid bodies
        fluid_shapes_geom = []  # actual FreeCAD shapes for geometry-based fallback
        if not fluid_region_shapes and settings.get('multiRegionFluidNames'):
            mesh_part = self.mesh_obj.Part
            links = _getCompoundLinks(mesh_part)
            for lnk in links:
                if lnk.Name not in solid_region_shapes:
                    fluid_region_shapes.add(lnk.Name)
                    try:
                        fluid_shapes_geom.append(lnk.Shape)
                    except Exception:
                        pass

        fluid_bcs = {}
        solid_bcs = {}
        for bc_obj in self.bc_group:
            matched = False
            for ref in bc_obj.ShapeRefs:
                if ref[0].Name in fluid_region_shapes:
                    fluid_bcs[bc_obj.Label] = settings['boundaries'][bc_obj.Label]
                    matched = True
                    break
                elif ref[0].Name in solid_region_shapes:
                    solid_bcs[bc_obj.Label] = settings['boundaries'][bc_obj.Label]
                    matched = True
                    break
            if not matched and solid_shapes_geom:
                # Geometry fallback: classify by whether face centroid is inside the fluid
                # region. Faces outside the fluid region are solid BCs; faces inside (or on
                # the boundary of) the fluid region are fluid BCs. This handles cases where
                # BCs reference the BooleanFragments compound directly, whose face centroids
                # may lie geometrically inside the original solid shape even when the face
                # belongs to the fluid domain boundary (e.g. interface faces at z=0).
                is_solid = False
                for ref in bc_obj.ShapeRefs:
                    try:
                        shape_obj = ref[0]
                        sub_list = ref[1] if ref[1] else []
                        faces = [shape_obj.Shape.getElement(s) for s in sub_list] if sub_list \
                            else [shape_obj.Shape]
                        for face in faces:
                            if face is None:
                                continue
                            centroid = face.CenterOfMass
                            if fluid_shapes_geom:
                                # Solid BC only if centroid is outside every fluid shape
                                in_fluid = any(fs.isInside(centroid, 1e-3, True)
                                               for fs in fluid_shapes_geom)
                                if not in_fluid:
                                    is_solid = True
                                    break
                            else:
                                for solid_shape in solid_shapes_geom:
                                    if solid_shape.isInside(centroid, 1e-3, True):
                                        is_solid = True
                                        break
                            if is_solid:
                                break
                    except Exception:
                        pass
                    if is_solid:
                        break
                if is_solid:
                    solid_bcs[bc_obj.Label] = settings['boundaries'][bc_obj.Label]
                else:
                    fluid_bcs[bc_obj.Label] = settings['boundaries'][bc_obj.Label]

        settings['multiRegionFluidBoundaries'] = fluid_bcs
        settings['multiRegionSolidBoundaries'] = solid_bcs

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
            for r in o.ShapeRefs:
                path = os.path.join(self.working_dir,
                                    self.solver_obj.InputCaseName,
                                    "constant",
                                    "triSurface")
                if not os.path.exists(path):
                    os.makedirs(path)
                shape = r[0].Shape
                CfdMeshTools.writeSurfaceMeshFromShape(shape, path, r[0].Name, self.mesh_obj)
                print("Successfully wrote stl surface for mean velocity force cell zone\n")

    def processMeanVelocityForceCellZoneProperties(self):
        settings = self.settings
        settings['meanVelocityForceCellZonesPresent'] = True
        settings['fvOptionsPresent'] = True
        for o in self.mean_velocity_force_cellzone_objs:
            od = CfdTools.propsToDict(o)
            part_name_list = tuple(r[0].Name for r in o.ShapeRefs)
            settings['meanVelocityForceCellZones'][o.Label] = {
                'PartNameList': part_name_list,
                'Direction': od['Direction'],
                'Ubar': od['Ubar'],
                'Relaxation': od['Relaxation'],
            }
            # Register the zone for topoSetZonesDict so the cellZoneSet is created
            settings['zones'][o.Label] = {'PartNameList': part_name_list}
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
                    'PatchNamesList': '"patch_'+str(bc_id+1)+'_.*"',
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
