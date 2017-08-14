# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2015 - Qingfeng Xia <qingfeng.xia eng ox ac uk>         *
# *   Copyright (c) 2017 - Alfred Bogaers (CSIR) <abogaers@csir.co.za>      *
# *   Copyright (c) 2017 - Johan Heyns (CSIR) <jheyns@csir.co.za>           *
# *   Copyright (c) 2017 - Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>        *
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

"""
After playback macro, Mesh object need to build up in taskpanel
"""

__title__ = "FoamCaseWriter"
__author__ = "Qingfeng Xia"
__url__ = "http://www.freecadweb.org"


import FreeCAD
import CfdTools
import os
import os.path
import shutil
from PySide import QtCore
from PySide.QtCore import QRunnable, QObject
import Units
import TemplateBuilder


# Write CFD analysis setup into OpenFOAM case
# write_case() is the only public API
# Derived from QRunnable in order to run in a worker thread

class CfdCaseWriterSignals(QObject):
    error = QtCore.Signal(str)  # Signal in PySide, pyqtSignal in PyQt
    finished = QtCore.Signal(bool)


class CfdCaseWriterFoam(QRunnable):
    def __init__(self, analysis_obj):
        super(CfdCaseWriterFoam, self).__init__()
        """ analysis_obj should contains all the information needed,
        boundaryConditionList is a list of all boundary Conditions objects(FemConstraint)
        """

        self.analysis_obj = analysis_obj
        self.solver_obj = CfdTools.getSolver(analysis_obj)
        self.physics_model, isPresent = CfdTools.getPhysicsModel(analysis_obj)
        self.mesh_obj = CfdTools.getMesh(analysis_obj)
        self.material_objs = CfdTools.getMaterials(analysis_obj)
        self.bc_group = CfdTools.getCfdBoundaryGroup(analysis_obj)
        self.initial_conditions, isPresent = CfdTools.getInitialConditions(analysis_obj)
        self.porousZone_objs = CfdTools.getPorousZoneObjects(analysis_obj)
        self.initialisationZone_objs = CfdTools.getInitialisationZoneObjects(analysis_obj)
        self.zone_objs = CfdTools.getZoneObjects(analysis_obj)
        self.mesh_generated = False

        self.signals = CfdCaseWriterSignals()

    def run(self):
        success = False
        try:
            success = self.write_case()
        except Exception as e:
            self.signals.error.emit(str(e))
            self.signals.finished.emit(False)
            raise
        self.signals.finished.emit(success)

    def write_case(self, updating=False):
        """ Write_case() will collect case setings, and finally build a runnable case. """
        FreeCAD.Console.PrintMessage("Start to write case to folder {}\n".format(self.solver_obj.WorkingDir))
        _cwd = os.curdir
        if not os.path.exists(self.solver_obj.WorkingDir):
            raise IOError("Path " + self.solver_obj.WorkingDir + " does not exist.")
        os.chdir(self.solver_obj.WorkingDir)  # pyFoam can not write to cwd if FreeCAD is started NOT from terminal

        try:  # Make sure we restore cwd after exception here
            # Perform initialisation here rather than __init__ in case of path changes
            self.case_folder = os.path.join(self.solver_obj.WorkingDir, self.solver_obj.InputCaseName)
            self.case_folder = os.path.expanduser(os.path.abspath(self.case_folder))
            self.mesh_file_name = os.path.join(self.case_folder, self.solver_obj.InputCaseName, u".unv")

            self.template_path = os.path.join(CfdTools.get_module_path(), "data", "defaults")

            solverSettingsDict = CfdTools.getSolverSettings(self.solver_obj)

            # Collect settings into single dictionary
            self.settings = {
                'physics': self.physics_model,
                'fluidProperties': [],  # Order is important, so use a list
                'initialValues': self.initial_conditions,
                'boundaries': dict((b.Label, b.BoundarySettings) for b in self.bc_group),
                'bafflesPresent': self.bafflesPresent(),
                'porousZones': {},
                'porousZonesPresent': False,
                'initialisationZones': {o.Label: o.initialisationZoneProperties for o in self.initialisationZone_objs},
                'initialisationZonesPresent': len(self.initialisationZone_objs) > 0,
                'zones': {o.Label: {'PartNameList': tuple(o.partNameList)} for o in self.zone_objs},
                'zonesPresent': len(self.zone_objs) > 0,
                'meshType': self.mesh_obj.Proxy.Type,
                'solver': solverSettingsDict,
                'system': {}
                }

            self.processSystemSettings()
            self.processSolverSettings()
            self.processFluidProperties()
            self.processBoundaryConditions()
            self.processInitialConditions()
            self.clearCase()

            self.exportZoneStlSurfaces()
            if self.porousZone_objs:
                self.processPorousZoneProperties()
            self.processInitialisationZoneProperties()

            self.settings['createPatchesFromSnappyBaffles'] = False
            if self.mesh_obj.Proxy.Type == "CfdMeshCart":  # Cut-cell Cartesian
                self.setupPatchNames()

            TemplateBuilder.TemplateBuilder(self.case_folder, self.template_path, self.settings)
            self.writeMesh()

            # Update Allrun permission - will fail silently on Windows
            fname = os.path.join(self.case_folder, "Allrun")
            import stat
            s = os.stat(fname)
            os.chmod(fname, s.st_mode | stat.S_IEXEC)

            # Move mesh files, after being edited, to polyMesh.org
            CfdTools.movePolyMesh(self.case_folder)

        except:
            raise
        finally:
            os.chdir(_cwd)  # Restore working dir
        FreeCAD.Console.PrintMessage("Successfully wrote {} case to folder {}\n".format(
                                     self.solver_obj.SolverName, self.solver_obj.WorkingDir))
        return True

    def getSolverName(self):
        """ Solver name is selected based on selected physics. This should only be extended as additional physics are
        included. """
        solver = None
        if self.physics_model['Flow'] == 'Incompressible':
            if self.physics_model['Thermal'] is None:
                if self.physics_model['Time'] == 'Transient':
                    if len(self.material_objs) == 1:
                        solver = 'pimpleFoam'
                    elif len(self.material_objs) == 2:
                        solver = 'interFoam'
                    elif len(self.material_objs) > 2:
                        solver = 'multiphaseInterFoam'
                else:
                    if len(self.material_objs) == 1:
                        if self.porousZone_objs or self.porousBafflesPresent():
                            solver = 'porousSimpleFoam'
                        else:
                            solver = 'simpleFoam'
        if solver is None:
            raise RuntimeError("No solver is supported to handle the selected physics with {} phases.".format(
                len(self.material_objs)))
        return solver

    def processSolverSettings(self):
        solver_settings = self.settings['solver']
        if solver_settings['parallel']:
            if solver_settings['parallelCores'] < 2:
                solver_settings['parallelCores'] = 2
        solver_settings['solverName'] = self.getSolverName()

    def processSystemSettings(self):
        system_settings = self.settings['system']
        system_settings['FoamRuntime'] = CfdTools.getFoamRuntime()
        system_settings['CasePath'] = self.case_folder
        system_settings['TranslatedCasePath'] = CfdTools.translatePath(self.case_folder)
        system_settings['FoamPath'] = CfdTools.getFoamDir()
        system_settings['TranslatedFoamPath'] = CfdTools.translatePath(CfdTools.getFoamDir())

    def clearCase(self, backup_path=None):
        """ Remove and recreate case directory, optionally backing up """
        output_path = self.case_folder
        if backup_path and os.path.isdir(output_path):
            shutil.move(output_path, backup_path)
        if os.path.isdir(output_path):
            shutil.rmtree(output_path)
        os.makedirs(output_path)  # mkdir -p

    # Mesh

    def writeMesh(self):
        """ Convert or copy mesh files """
        if self.mesh_obj.Proxy.Type == "FemMeshGmsh":  # GMSH
            # Convert GMSH created UNV file to OpenFoam
            FreeCAD.Console.PrintMessage("Writing GMSH")
            unvMeshFile = self.case_folder + os.path.sep + self.solver_obj.InputCaseName + u".unv"
            self.mesh_generated = CfdTools.write_unv_mesh(self.mesh_obj, self.bc_group, unvMeshFile)
            # FreeCAD always stores the CAD geometry in mm, while FOAM by default uses SI units. This is independent
            # of the user selected unit preferences.
            self.setupMesh(unvMeshFile, scale = 0.001)
        elif self.mesh_obj.Proxy.Type == "CfdMeshCart":  # Cut-cell Cartesian
            import CfdCartTools
            ## Move Cartesian mesh files from temporary mesh directory to case directory
            if self.mesh_obj.MeshUtility == "cfMesh":
                FreeCAD.Console.PrintMessage("Writing Cartesian mesh\n")
                #import CfdCartTools
                self.cart_mesh = CfdCartTools.CfdCartTools(self.mesh_obj)
                cart_mesh = self.cart_mesh
                cart_mesh.get_tmp_file_paths("cfMesh")  # Update tmp file locations
                CfdTools.copyFilesRec(cart_mesh.polyMeshDir, os.path.join(self.case_folder,'constant','polyMesh'))
                CfdTools.copyFilesRec(cart_mesh.triSurfaceDir, os.path.join(self.case_folder,'constant','triSurface'))
                shutil.copy2(cart_mesh.temp_file_meshDict, os.path.join(self.case_folder,'system'))
                shutil.copy2(os.path.join(cart_mesh.meshCaseDir,'Allmesh'),self.case_folder)
                shutil.copy2(os.path.join(cart_mesh.meshCaseDir,'log.cartesianMesh'),self.case_folder)
                shutil.copy2(os.path.join(cart_mesh.meshCaseDir,'log.surfaceFeatureEdges'),self.case_folder)

            elif self.mesh_obj.MeshUtility == "snappyHexMesh":
                FreeCAD.Console.PrintMessage("Writing snappyHexMesh generated Cartesian mesh")
                self.cart_mesh = CfdCartTools.CfdCartTools(self.mesh_obj)
                cart_mesh = self.cart_mesh
                cart_mesh.get_tmp_file_paths("snappyHexMesh")  # Update tmp file locations
                CfdTools.copyFilesRec(cart_mesh.polyMeshDir, os.path.join(self.case_folder,'constant','polyMesh'))
                CfdTools.copyFilesRec(cart_mesh.triSurfaceDir, os.path.join(self.case_folder,'constant','triSurface'))
                shutil.copy2(cart_mesh.temp_file_blockMeshDict, os.path.join(self.case_folder,'system'))
                shutil.copy2(cart_mesh.temp_file_snappyMeshDict, os.path.join(self.case_folder,'system'))
                shutil.copy2(cart_mesh.temp_file_surfaceFeatureExtractDict, os.path.join(self.case_folder,'system'))
                shutil.copy2(os.path.join(cart_mesh.meshCaseDir,'Allmesh'),self.case_folder)
                shutil.copy2(os.path.join(cart_mesh.meshCaseDir,'log.blockMesh'),self.case_folder)
                shutil.copy2(os.path.join(cart_mesh.meshCaseDir,'log.surfaceFeatureExtract'),self.case_folder)
                shutil.copy2(os.path.join(cart_mesh.meshCaseDir,'log.snappyHexMesh'),self.case_folder)
        else:
            raise Exception("Unrecognised mesh type")

    def setupMesh(self, updated_mesh_path, scale):
        if os.path.exists(updated_mesh_path):
            CfdTools.convertMesh(self.case_folder, updated_mesh_path, scale)

    def processFluidProperties(self):
        # self.material_obj stores everything as a string for compatibility with FreeCAD material objects.
        # Convert to SI numbers
        settings = self.settings
        for material_obj in self.material_objs:
            mp = {}
            mp['Name'] = material_obj.Label
            mp['Density'] = \
                Units.Quantity(material_obj.Material['Density']).getValueAs("kg/m^3").Value
            if self.physics_model['Turbulence'] == 'Inviscid':
                mp['DynamicViscosity'] = 0.0
            else:
                mp['DynamicViscosity'] = \
                    Units.Quantity(material_obj.Material['DynamicViscosity']).getValueAs("kg/m/s").Value
            mp['KinematicViscosity'] = mp['DynamicViscosity']/mp['Density']
            settings['fluidProperties'].append(mp)

    def processBoundaryConditions(self):
        """ Compute any quantities required before case build """
        settings = self.settings
        for bc_name in settings['boundaries']:
            bc = settings['boundaries'][bc_name]
            if not bc['VelocityIsCartesian']:
                veloMag = bc['VelocityMag']
                face = bc['DirectionFace'].split(':')
                # See if entered face actually exists and is planar
                try:
                    selected_object = self.analysis_obj.Document.getObject(face[0])
                    if hasattr(selected_object, "Shape"):
                        elt = selected_object.Shape.getElement(face[1])
                        if elt.ShapeType == 'Face' and CfdTools.is_planar(elt):
                            n = elt.normalAt(0.5, 0.5)
                            if bc['ReverseNormal']:
                               n = [-ni for ni in n]
                            velocity = [ni*veloMag for ni in n]
                            bc['Ux'] = velocity[0]
                            bc['Uy'] = velocity[1]
                            bc['Uz'] = velocity[2]
                        else:
                            raise RuntimeError
                    else:
                        raise RuntimeError
                except (SystemError, RuntimeError):
                    raise RuntimeError(bc['DirectionFace'] + " is not a valid, planar face.")
            if settings['solver']['solverName'] in ['simpleFoam', 'porousSimpleFoam', 'pimpleFoam']:
                bc['KinematicPressure'] = bc['Pressure']/settings['fluidProperties'][0]['Density']

            if bc['PorousBaffleMethod'] == 1:
                wireDiam = bc['ScreenWireDiameter']
                spacing = bc['ScreenSpacing']
                CD = 1.0  # Drag coeff of wire (Simmons - valid for Re > ~300)
                beta = (1-wireDiam/spacing)**2
                bc['PressureDropCoeff'] = CD*(1-beta)

    def processInitialConditions(self):
        """ Do any required computations before case build. Boundary conditions must be processed first. """
        settings = self.settings
        initial_values = settings['initialValues']
        if settings['solver']['solverName'] in ['simpleFoam', 'porousSimpleFoam', 'pimpleFoam']:
            mat_prop = settings['fluidProperties'][0]
            initial_values['KinematicPressure'] = initial_values['Pressure'] / mat_prop['Density']
        if settings['solver']['solverName'] in ['interFoam', 'multiphaseInterFoam']:
            # Make sure the first n-1 alpha values exist, and write the n-th one
            # consistently for multiphaseInterFoam
            sum_alpha = 0.0
            if 'alphas' not in initial_values:
                initial_values['alphas'] = {}
            for i, m in enumerate(settings['fluidProperties']):
                alpha_name = m['Name']
                if i == len(settings['fluidProperties'])-1 and \
                   settings['solver']['solverName'] == 'multiphaseInterFoam':
                    initial_values['alphas'][alpha_name] = 1.0-sum_alpha
                else:
                    alpha = initial_values['alphas'].get(alpha_name, 0.0)
                    initial_values['alphas'][alpha_name] = alpha
                    sum_alpha += alpha

        physics = settings['physics']
        if physics['TurbulenceModel'] is not None:
            if initial_values['UseInletTurbulenceValues']:
                inlet_bc = None
                first_inlet = None
                ninlets = 0
                for bc_name in settings['boundaries']:
                    bc = settings['boundaries'][bc_name]
                    if bc['BoundaryType'] == "inlet":
                        ninlets = ninlets + 1
                        # Save first inlet in case match not found
                        if ninlets == 1:
                            first_inlet = bc
                        if initial_values['Inlet'] == bc_name:
                            inlet_bc = bc
                            break
                if inlet_bc is None:
                    if initial_values['Inlet']:
                        if ninlets == 1:
                            inlet_bc = first_inlet
                        else:
                            raise Exception("Inlet {} not found to copy turbulence initial conditions from."
                                            .format(initial_values['Inlet']))
                    else:
                        inlet_bc = first_inlet
                if inlet_bc is None:
                    raise Exception("No inlets found to copy turbulence initial conditions from.")

                if inlet_bc['TurbulenceInletSpecification'] == 'TKEAndSpecDissipationRate':
                    initial_values['k'] = inlet_bc['TurbulentKineticEnergy']
                    initial_values['omega'] = inlet_bc['SpecificDissipationRate']
                elif inlet_bc['TurbulenceInletSpecification'] == 'intensityAndLengthScale':
                    if inlet_bc['BoundarySubtype'] == 'uniformVelocity':
                        Uin = (inlet_bc['Ux']**2 +
                               inlet_bc['Uy']**2 +
                               inlet_bc['Uz']**2)**0.5
                        I = inlet_bc['TurbulenceIntensity']
                        k = 3/2*(Uin*I)**2
                        Cmu = 0.09  # Standard turb model parameter
                        l = inlet_bc['TurbulenceLengthScale']
                        omega = k**0.5/(Cmu**0.25*l)
                        initial_values['k'] = k
                        initial_values['omega'] = omega
                    else:
                        raise Exception(
                            "Inlet type currently unsupported for copying turbulence initial conditions.")
                else:
                    raise Exception(
                        "Turbulence inlet specification currently unsupported for copying turbulence initial conditions")

    # Zones

    def exportZoneStlSurfaces(self):
        for zo in self.zone_objs:
            import Mesh
            for i in range(len(zo.shapeList)):
                shape = zo.shapeList[i].Shape
                path = os.path.join(self.solver_obj.WorkingDir,
                                    self.solver_obj.InputCaseName,
                                    "constant",
                                    "triSurface")
                if not os.path.exists(path):
                    os.makedirs(path)
                fname = os.path.join(path, zo.partNameList[i]+u".stl")
                import MeshPart
                #meshStl = MeshPart.meshFromShape(shape, LinearDeflection = self.mesh_obj.STLLinearDeflection)
                meshStl = MeshPart.meshFromShape(shape, LinearDeflection = 0.1)
                meshStl.write(fname)
                FreeCAD.Console.PrintMessage("Successfully wrote stl surface\n")

    def processPorousZoneProperties(self):
        settings = self.settings
        settings['porousZonesPresent'] = True
        porousZoneSettings = settings['porousZones']
        for po in self.porousZone_objs:
            pd = {'PartNameList': tuple(po.partNameList)}
            if po.porousZoneProperties['PorousCorrelation'] == 'DarcyForchheimer':
                pd['D'] = tuple(po.porousZoneProperties['D'])
                pd['F'] = tuple(po.porousZoneProperties['F'])
                pd['e1'] = tuple(po.porousZoneProperties['e1'])
                pd['e3'] = tuple(po.porousZoneProperties['e3'])
            elif po.porousZoneProperties['PorousCorrelation'] == 'Jakob':
                # Calculate effective Darcy-Forchheimer coefficients
                # This is for equilateral triangles arranged with the triangles pointing in BundleLayerNormal
                # direction (direction of greater spacing - sqrt(3)*triangleEdgeLength)
                pd['e1'] = tuple(po.porousZoneProperties['SpacingDirection'])  # OpenFOAM modifies to be orthog to e3
                pd['e3'] = tuple(po.porousZoneProperties['TubeAxis'])
                spacing = po.porousZoneProperties['TubeSpacing']
                d0 = po.porousZoneProperties['OuterDiameter']
                u0 = po.porousZoneProperties['VelocityEstimate']
                aspectRatio = po.porousZoneProperties['AspectRatio']
                kinVisc = self.settings['fluidProperties']['KinematicViscosity']
                if kinVisc == 0.0:
                    raise ValueError("Viscosity must be set for Jakob correlation")
                if spacing < d0:
                    raise ValueError("Tube spacing may not be less than diameter")
                D = [0, 0, 0]
                F = [0, 0, 0]
                for (i, Sl, St) in [(0, aspectRatio*spacing, spacing), (1, spacing, aspectRatio*spacing)]:
                    C = 1.0/St*0.5*(1.0+0.47/(Sl/d0-1)**1.06)*(1.0/(1-d0/Sl))**(2.0-0.16)
                    D = C/d0*0.5*(u0*d0/kinVisc)**(1.0-0.16)
                    F = C*(u0*d0/kinVisc)**(-0.16)
                    D[i] = D
                    F[i] = F
                pd['D'] = tuple(D)
                pd['F'] = tuple(F)
                # Currently assuming zero drag parallel to tube bundle (3rd principal dirn)
            else:
                raise Exception("Unrecognised method for porous baffle resistance")
            porousZoneSettings[po.Label] = pd

    def processInitialisationZoneProperties(self):
        settings = self.settings
        if settings['solver']['solverName'] in ['interFoam', 'multiphaseInterFoam']:
            # Make sure the first n-1 alpha values exist, and write the n-th one
            # consistently for multiphaseInterFoam
            for zone_name in settings['initialisationZones']:
                z = settings['initialisationZones'][zone_name]
                sum_alpha = 0.0
                if 'alphas' in z:
                    for i, m in enumerate(settings['fluidProperties']):
                        alpha_name = m['Name']
                        if i == len(settings['fluidProperties'])-1 and \
                           settings['solver']['solverName'] == 'multiphaseInterFoam':
                            z['alphas'][alpha_name] = 1.0-sum_alpha
                        else:
                            alpha = z['alphas'].get(alpha_name, 0.0)
                            z['alphas'][alpha_name] = alpha
                            sum_alpha += alpha

    def bafflesPresent(self):
        for b in self.bc_group:
            if b.BoundarySettings['BoundaryType'] == 'baffle':
                return True
        return False

    def porousBafflesPresent(self):
        for b in self.bc_group:
            if b.BoundarySettings['BoundaryType'] == 'baffle' and \
               b.BoundarySettings['BoundarySubtype'] == 'porousBaffle':
                return True
        return False

    def setupPatchNames(self):
        print ('Populating createPatchDict to update BC names')
        settings = self.settings
        settings['createPatches'] = {}
        bc_group = self.bc_group
        mobj = self.mesh_obj
        bc_allocated = []
        for bc_id, bc_obj in enumerate(bc_group):
            bc_list = []
            meshFaceList = mobj.Part.Shape.Faces
            for (i, mf) in enumerate(meshFaceList):
                bcFacesList = bc_obj.Shape.Faces
                for bf in bcFacesList:
                    isSameGeo = CfdTools.isSameGeometry(bf, mf)
                    if isSameGeo:
                        bc_list.append(mobj.ShapeFaceNames[i])
                        if mobj.ShapeFaceNames[i] in bc_allocated:
                            print ('Error: {} has been assigned twice'.format(mobj.ShapeFaceNames[i]))
                        else:
                            bc_allocated.append(mobj.ShapeFaceNames[i])

            bcDict = bc_obj.BoundarySettings
            bcType = bcDict["BoundaryType"]
            bcSubType = bcDict["BoundarySubtype"]
            patchType = CfdTools.getPatchType(bcType, bcSubType)
            settings['createPatches'][bc_obj.Label] = {
                'PatchNamesList': tuple(bc_list),  # Tuple used so that case writer outputs as an array
                'PatchType': patchType
            }

            # In almost all cases the number of faces associated with a bc is going to be less than the number of
            # external or mesh faces.
            # if not (len(bc_list) == len(meshFaceList)):
            #     raise Exception('Mismatch between boundary faces and mesh faces')

        if self.mesh_obj.MeshRegionList:
            for regionObj in self.mesh_obj.MeshRegionList:
                #if regionObj.snappedRefine:
                    if regionObj.internalBaffle:
                        settings['createPatchesFromSnappyBaffles'] = True


        if settings['createPatchesFromSnappyBaffles']:
            settings['createPatchesSnappyBaffles'] = {}
            # TODO Still need to include an error checker in the event that 
            # an internal baffle is created using snappy but is not linked up
            # with a baffle boundary condition (as in there is no baffle boundary condition which 
            # corresponds. Currently openfoam will throw a contextually
            # confusing error (only that the boundary does not exist). The primary difficulty with such a checker is 
            # that it is possible to define a boundary face as a baffle, which will be overriden
            # by the actual boundary name and therefore won't exist anymore. 
            for bc_id, bc_obj in enumerate(bc_group):
                bcDict = bc_obj.BoundarySettings
                bcType = bcDict["BoundaryType"]
                if bcType == "baffle":
                    tempBaffleList = []
                    tempBaffleListSlave = []
                    if self.mesh_obj.MeshRegionList:
                        for regionObj in self.mesh_obj.MeshRegionList:
                            print regionObj.Name
                            if regionObj.internalBaffle:
                                for sub in regionObj.References:
                                    print sub[0].Name
                                    for elems in sub[1]:
                                        elt = sub[0].Shape.getElement(elems)
                                        if elt.ShapeType == 'Face':
                                            #isSameGeo = FemMeshTools.is_same_geometry(bf, mf)
                                            bcFacesList = bc_obj.Shape.Faces
                                            for bf in bcFacesList:
                                                import FemMeshTools
                                                isSameGeo = FemMeshTools.is_same_geometry(bf, elt)
                                                if isSameGeo:
                                                    tempBaffleList.append(regionObj.Name+sub[0].Name+elems)
                                                    tempBaffleListSlave.append(regionObj.Name+sub[0].Name+elems+"_slave")
                    settings['createPatchesSnappyBaffles'][bc_obj.Label] = {"PatchNamesList" : tuple(tempBaffleList),
                                                                            "PatchNamesListSlave" : tuple(tempBaffleListSlave)}



        # Add default faces
        flagName = False
        def_bc_list = []
        for name in mobj.ShapeFaceNames:
            if not name in bc_allocated:
                def_bc_list.append(name)
                flagName = True
        if flagName:
            settings['createPatches']['defaultFaces'] = {
                'PatchNamesList': tuple(def_bc_list),
                'PatchType': "patch"
            }
