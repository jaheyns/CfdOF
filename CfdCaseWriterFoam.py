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
import FoamCaseBuilder as fcb  # independent module, not depending on FreeCAD
from PySide import QtCore
from PySide.QtCore import QRunnable, QObject
from FoamCaseBuilder.utility import readTemplate
import Units


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
        self.material_obj = CfdTools.getMaterial(analysis_obj)
        self.bc_group = CfdTools.getCfdBoundaryGroup(analysis_obj)
        self.initialConditions, isPresent = CfdTools.getInitialConditions(analysis_obj)
        self.porousZone_objs, self.porousZonePresent = CfdTools.getPorousObjects(analysis_obj)
        self.mesh_generated = False

        self.signals = CfdCaseWriterSignals()

        # Set parameter location
        self.param_path = "User parameter:BaseApp/Preferences/Mod/Cfd/OpenFOAM"
        # Ensure parameters exist for future editing
        installation_path = FreeCAD.ParamGet(self.param_path).GetString("InstallationPath", "")
        FreeCAD.ParamGet(self.param_path).SetString("InstallationPath", installation_path)

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
            self.case_folder = os.path.abspath(self.case_folder)
            self.mesh_file_name = os.path.join(self.case_folder, self.solver_obj.InputCaseName, u".unv")

            # Get OpenFOAM install path from parameters
            self.installation_path = FreeCAD.ParamGet(self.param_path).GetString("InstallationPath", "")

            self.solverName = self.getSolverName()

            # Collect settings into single dictionary
            # self.material_obj stores everything as a string for compatibility with FreeCAD material objects.
            # Convert to SI numbers
            material_properties = {}
            material_properties['Density'] = \
                Units.Quantity(self.material_obj.Material['Density']).getValueAs("kg/m^3").Value
            material_properties['DynamicViscosity'] = \
                Units.Quantity(self.material_obj.Material['DynamicViscosity']).getValueAs("kg/m/s").Value
            settings = {'physics': self.physics_model,
                        'fluidProperties': material_properties,
                        'initialValues': self.initialConditions,
                        'boundaries': dict((b.Label, b.BoundarySettings) for b in self.bc_group)
                        }

            # Initialise case
            self.builder = fcb.BasicBuilder(casePath=self.case_folder,
                                            settings=settings,
                                            installationPath=self.installation_path,
                                            solverSettings=CfdTools.getSolverSettings(self.solver_obj),
                                            physicsModel=self.physics_model,
                                            initialConditions=self.initialConditions,
                                            templatePath=os.path.join(CfdTools.get_module_path(), "data", "defaults"),
                                            solverName=self.solverName  # Use var in solverSet
                                            )

            self.builder.setInstallationPath()
            self.builder.pre_build_check()
            self.setMaterial()
            self.setBoundaryConditions()
            self.processInitialConditions()
            self.builder.createCase()

            self.write_mesh()

            if self.porousZone_objs is not None:
                self.exportPorousZoneStlSurfaces()
                self.setPorousZoneProperties()

            self.builder.post_build_check()
            self.builder.build()

        except:
            raise
        finally:
            os.chdir(_cwd)  # Restore working dir
        FreeCAD.Console.PrintMessage("Sucessfully wrote {} case to folder {}\n".format(
                                     self.solver_obj.SolverName, self.solver_obj.WorkingDir))
        return True

    # Solver

    def getSolverName(self):
        """ Solver name is selected based on selected physics. This should only be extended as additional physics are
        included.
        """
        solver = None
        if self.physics_model['Flow'] == 'Incompressible' and (self.physics_model['Thermal'] is None):
            if self.physics_model['Time'] == 'Transient':
                solver = 'pimpleFoam'
            else:
                solver = 'simpleFoam'
        return solver

    def setTimeControl(self):
        """ Time step settings """
        if self.physics_model["Time"] == "Transient":
            self.builder.timeStepSettings = {"endTime": self.solver_obj.EndTime,
                                             "timeStep": self.solver_obj.TimeStep,
                                             "writeInterval": self.solver_obj.WriteInterval}

    def extractInternalField(self):
        Ux = self.initialConditions['Ux']
        Uy = self.initialConditions['Uy']
        Uz = self.initialConditions['Uz']
        P = self.initialConditions['P']
        internalFields = {'p': P, 'U': (Ux, Uy, Uz)}
        return internalFields

    # Mesh

    def write_mesh(self):
        """ Convert or copy mesh files """
        if self.mesh_obj.Proxy.Type == "FemMeshGmsh":  # GMSH
            # Convert GMSH created UNV file to OpenFoam
            FreeCAD.Console.PrintMessage("Writing GMSH")
            unvMeshFile = self.case_folder + os.path.sep + self.solver_obj.InputCaseName + u".unv"
            self.mesh_generated = CfdTools.write_unv_mesh(self.mesh_obj, self.bc_group, unvMeshFile)
            # FreeCAD always stores the CAD geometry in mm, while FOAM by default uses SI units. This is independent
            # of the user selected unit preferences.
            self.builder.setupMesh(unvMeshFile, scale = 0.001)

        elif self.mesh_obj.Proxy.Type == "CfdMeshCart":  # Cut-cell Cartesian
            # Move Cartesian mesh files from temporary mesh directory to case directory
            FreeCAD.Console.PrintMessage("Writing Cartesian mesh")
            import CfdCartTools
            self.cart_mesh = CfdCartTools.CfdCartTools(self.mesh_obj)
            cart_mesh = self.cart_mesh
            cart_mesh.get_tmp_file_paths()  # Update tmp file locations
            CfdTools.copyFilesRec(cart_mesh.polyMeshDir, os.path.join(self.case_folder,'constant','polyMesh'))
            CfdTools.copyFilesRec(cart_mesh.triSurfaceDir, os.path.join(self.case_folder,'constant','triSurface'))
            shutil.copy2(cart_mesh.temp_file_meshDict, os.path.join(self.case_folder,'system'))
            shutil.copy2(os.path.join(cart_mesh.meshCaseDir,'Allmesh'),self.case_folder)
            shutil.copy2(os.path.join(cart_mesh.meshCaseDir,'log.cartesianMesh'),self.case_folder)
            shutil.copy2(os.path.join(cart_mesh.meshCaseDir,'log.surfaceFeatureEdges'),self.case_folder)

            # Generate createPatch to update boundary patch names
            self.builder.setupCreatePatchDict(self.case_folder, self.bc_group, self.mesh_obj)
        else:
            raise Exception("Unrecognised mesh type")

    def setMaterial(self, material=None):
        """ Compute and set the kinematic viscosity """
        if self.physics_model['Turbulence']=='Inviscid':
            kinVisc = 0.0
        else:
            viscosity = FreeCAD.Units.Quantity(self.material_obj.Material['DynamicViscosity'])
            viscosity = viscosity.getValueAs('Pa*s')
            density = FreeCAD.Units.Quantity(self.material_obj.Material['Density'])
            density = density.getValueAs('kg/m^3')
            kinVisc = viscosity/density
        self.builder.fluidProperties = {'name': 'oneLiquid', 'kinematicViscosity': float(kinVisc)}

    def setBoundaryConditions(self):
        """ Compute any quantities required before case build """
        for bc in self.bc_group:
            import _CfdFluidBoundary
            assert(isinstance(bc.Proxy, _CfdFluidBoundary._CfdFluidBoundary))

            if not bc.BoundarySettings['VelocityIsCartesian']:
                veloMag = bc.BoundarySettings['VelocityMag']
                face = bc.BoundarySettings['DirectionFace'].split(':')
                # See if entered face actually exists and is planar
                try:
                    selected_object = self.analysis_obj.Document.getObject(face[0])
                    if hasattr(selected_object, "Shape"):
                        elt = selected_object.Shape.getElement(face[1])
                        if elt.ShapeType == 'Face' and CfdTools.is_planar(elt):
                            n = elt.normalAt(0.5, 0.5)
                            if bc.BoundarySettings['ReverseNormal']:
                               n = [-ni for ni in n]
                            velocity = [ni*veloMag for ni in n]
                            bc.BoundarySettings['Ux'] = velocity[0]
                            bc.BoundarySettings['Uy'] = velocity[1]
                            bc.BoundarySettings['Uz'] = velocity[2]
                        else:
                            raise RuntimeError
                    else:
                        raise RuntimeError
                except (SystemError, RuntimeError):
                    raise RuntimeError(bc.BoundarySettings['DirectionFace'] + " is not a valid, planar face.")

            if bc.BoundarySettings['PorousBaffleMethod'] == 1:
                wireDiam = bc.BoundarySettings['ScreenWireDiameter']
                spacing = bc.BoundarySettings['ScreenSpacing']
                CD = 1.0  # Drag coeff of wire (Simmons - valid for Re > ~300)
                beta = (1-wireDiam/spacing)**2
                bc.BoundarySettings['PressureDropCoeff'] = CD*(1-beta)

    def processInitialConditions(self):
        """ Do any required computations before case build. Boundary conditions must be processed first. """
        if self.physics_model['TurbulenceModel'] is not None:
            if self.initialConditions['UseInletTurbulenceValues']:
                inlet_bc = None
                first_inlet = None
                ninlets = 0
                for bc in self.bc_group:
                    if bc.BoundarySettings['BoundaryType'] == "inlet":
                        ninlets = ninlets + 1
                        # Save first inlet in case match not found
                        if ninlets == 1:
                            first_inlet = bc
                        if self.initialConditions['Inlet'] == bc.Label:
                            inlet_bc = bc
                            break
                if inlet_bc is None:
                    if self.initialConditions['Inlet']:
                        if ninlets == 1:
                            inlet_bc = first_inlet
                        else:
                            raise Exception("Inlet {} not found to copy turbulence initial conditions from."
                                            .format(self.initialConditions['Inlet']))
                    else:
                        inlet_bc = first_inlet
                if inlet_bc is None:
                    raise Exception("No inlets found to copy turbulence initial conditions from.")

                if inlet_bc.BoundarySettings['TurbulenceInletSpecification'] == 'TKEAndSpecDissipationRate':
                    self.initialConditions['k'] = inlet_bc.BoundarySettings['TurbulentKineticEnergy']
                    self.initialConditions['omega'] = inlet_bc.BoundarySettings['SpecificDissipationRate']
                elif inlet_bc.BoundarySettings['TurbulenceInletSpecification'] == 'intensityAndLengthScale':
                    if inlet_bc.BoundarySettings['BoundarySubtype'] == 'uniformVelocity':
                        Uin = (inlet_bc.BoundarySettings['Ux'] ** 2 +
                               inlet_bc.BoundarySettings['Ux'] ** 2 +
                               inlet_bc.BoundarySettings['Ux'] ** 2) ** 0.5
                        I = inlet_bc.BoundarySettings['TurbulenceIntensity']
                        k = 3 / 2 * (Uin * I) ** 2
                        Cmu = 0.09  # Standard turb model parameter
                        l = inlet_bc.BoundarySettings['TurbulenceLengthScale']
                        omega = k ** 0.5 / (Cmu ** 0.25 * l)
                        self.initialConditions['k'] = k
                        self.initialConditions['omega'] = omega
                    else:
                        raise Exception(
                            "Inlet type currently unsupported for copying turbulence initial conditions.")
                else:
                    raise Exception(
                        "Turbulence inlet specification currently unsupported for copying turbulence initial conditions")

    # Porous

    def exportPorousZoneStlSurfaces(self):
        if self.porousZonePresent:
            for ii in range(len(self.porousZone_objs)):
                import Mesh
                for i in range(len(self.porousZone_objs[ii].shapeList)):
                    shape = self.porousZone_objs[ii].shapeList[i].Shape
                    path = os.path.join(self.solver_obj.WorkingDir,
                                        self.solver_obj.InputCaseName,
                                        "constant",
                                        "triSurface")
                    if not os.path.exists(path):
                        os.makedirs(path)
                    fname = os.path.join(path, self.porousZone_objs[ii]. partNameList[i]+u".stl")
                    import MeshPart
                    #meshStl = MeshPart.meshFromShape(shape, LinearDeflection = self.mesh_obj.STLLinearDeflection)
                    meshStl = MeshPart.meshFromShape(shape, LinearDeflection = 0.1)
                    meshStl.write(fname)
                    FreeCAD.Console.PrintMessage("Successfully wrote stl surface\n")

    def setPorousZoneProperties(self):
        porousZoneSettings = []
        for po in self.porousZone_objs:
            pd = {'PartNameList': po.partNameList}
            if po.porousZoneProperties['PorousCorrelation'] == 'DarcyForchheimer':
                pd['D'] = po.porousZoneProperties['D']
                pd['F'] = po.porousZoneProperties['F']
                pd['e1'] = po.porousZoneProperties['e1']
                pd['e3'] = po.porousZoneProperties['e3']
            elif po.porousZoneProperties['PorousCorrelation'] == 'Jakob':
                # Calculate effective Darcy-Forchheimer coefficients
                # This is for equilateral triangles arranged with the triangles pointing in BundleLayerNormal
                # direction (direction of greater spacing - sqrt(3)*triangleEdgeLength)
                pd['e1'] = po.porousZoneProperties['SpacingDirection']  # OpenFOAM modifies to be orthogonal to e3
                pd['e3'] = po.porousZoneProperties['TubeAxis']
                spacing = po.porousZoneProperties['TubeSpacing']
                d0 = po.porousZoneProperties['OuterDiameter']
                u0 = po.porousZoneProperties['VelocityEstimate']
                aspectRatio = po.porousZoneProperties['AspectRatio']
                kinVisc = self.builder.fluidProperties['kinematicViscosity']
                if kinVisc is None or kinVisc == 0.0:
                    raise ValueError("Viscosity must be set for Jakob correlation")
                if spacing < d0:
                    raise ValueError("Tube spacing may not be less than diameter")
                pd['D'] = [0, 0, 0]
                pd['F'] = [0, 0, 0]
                for (i, Sl, St) in [(0, aspectRatio*spacing, spacing), (1, spacing, aspectRatio*spacing)]:
                    C = 1.0/St*0.5*(1.0+0.47/(Sl/d0-1)**1.06)*(1.0/(1-d0/Sl))**(2.0-0.16)
                    D = C/d0*0.5*(u0*d0/kinVisc)**(1.0-0.16)
                    F = C*(u0*d0/kinVisc)**(-0.16)
                    pd['D'][i] = D
                    pd['F'][i] = F
                # Currently assuming zero drag parallel to tube bundle (3rd principal dirn)
            else:
                raise Exception("Unrecognised method for porous baffle resistance")
            porousZoneSettings.append(pd)
        self.builder.porousZoneSettings = porousZoneSettings

    # def write_solver_control(self):
    #     """ relaxRatio, fvOptions, pressure reference value, residual contnrol
    #     """
    #     self.builder.setupSolverControl()
    #
    #
    # def write_time_control(self):
    #     """ controlDict for time information
    #     """
    #     #if self.solver_obj.Transient:
    #     if self.physics_obj["Time"] == "Transient":
    #         self.builder.transientSettings = {#"startTime": self.solver_obj.StartTime,
    #                                           "endTime": self.solver_obj.EndTime,
    #                                           "timeStep": self.solver_obj.TimeStep,
    #                                           "writeInterval": self.solver_obj.WriteInterval}
