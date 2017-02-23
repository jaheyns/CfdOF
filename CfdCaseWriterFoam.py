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
2D meshing is hard to converted to OpenFOAM, but possible to export UNV mesh
"""

__title__ = "FoamCaseWriter"
__author__ = "Qingfeng Xia"
__url__ = "http://www.freecadweb.org"


import FreeCAD
import CfdTools
import os
import os.path
import FoamCaseBuilder as fcb  # independent module, not depending on FreeCAD


# Write CFD analysis setup into OpenFOAM case
# write_case() is the only public API

class CfdCaseWriterFoam:
    def __init__(self, analysis_obj):
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

    def write_case(self, updating=False):
        """ Write_case() will collect case setings, and finally build a runnable case. """
        FreeCAD.Console.PrintMessage("Start to write case to folder {}\n".format(self.solver_obj.WorkingDir))
        _cwd = os.curdir
        os.chdir(self.solver_obj.WorkingDir)  # pyFoam can not write to cwd if FreeCAD is started NOT from terminal

        # Perform initialisation here rather than __init__ in case of path changes
        self.case_folder = os.path.join(self.solver_obj.WorkingDir, self.solver_obj.InputCaseName)
        self.mesh_file_name = os.path.join(self.case_folder, self.solver_obj.InputCaseName, u".unv")

        # Get OpenFOAM install path from parameters
        paramPath = "User parameter:BaseApp/Preferences/Mod/Cfd/OpenFOAM"
        self.installation_path = FreeCAD.ParamGet(paramPath).GetString("InstallationPath", "")
        # Ensure parameter exists for future editing
        FreeCAD.ParamGet(paramPath).SetString("InstallationPath", self.installation_path)
        self.solverName = self.getSolverName()

        # Initialise case
        self.builder = fcb.BasicBuilder(casePath=self.case_folder,
                                        installationPath=self.installation_path,
                                        solverSettings=CfdTools.getSolverSettings(self.solver_obj),
                                        physicsModel=self.physics_model,
                                        initialConditions=self.initialConditions,
                                        templatePath=os.path.join(CfdTools.get_module_path(), "data", "defaults"),
                                        solverName=self.solverName  # Use var in solverSet
                                        )

        self.builder.setInstallationPath()
        self.builder.pre_build_check()
        self.builder.createCase()

        self.write_mesh()

        self.setMaterial()
        self.setBoundaryConditions()
        # NOTE: Update code when turbulence is revived
        # self.builder.turbulenceProperties = {"name": self.solver_obj.TurbulenceModel}

        # NOTE: Code depreciated (JH) 06/02/2017
        # self.write_solver_control()

        # NOTE: Code deprecated (OO) 22/02/2017 - removed from BasicBuilder
        #self.setTimeControl()

        if not (self.porousZone_objs == None):
            self.exportPorousZoneStlSurfaces()
            self.setPorousZoneProperties()

        self.builder.post_build_check()
        self.builder.build()
        os.chdir(_cwd)  # Restore working dir
        FreeCAD.Console.PrintMessage("{} Sucessfully write {} case to folder \n".format(
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
        Ux = FreeCAD.Units.Quantity(self.initialConditions['Ux'])
        Ux = Ux.getValueAs('m/s')
        Uy = FreeCAD.Units.Quantity(self.initialConditions['Uy'])
        Uy = Uy.getValueAs('m/s')
        Uz = FreeCAD.Units.Quantity(self.initialConditions['Uz'])
        Uz = Uz.getValueAs('m/s')
        P = FreeCAD.Units.Quantity(self.initialConditions['P'])
        P = P.getValueAs('kg*m/s^2')
        internalFields = {'p': float(P), 'U': (float(Ux), float(Uy), float(Uz))}
        return internalFields

    # Mesh

    def write_mesh(self):
        """ Convert Netgen/GMSH created UNV file to OpenFoam """
        caseFolder = self.solver_obj.WorkingDir + os.path.sep + self.solver_obj.InputCaseName
        unvMeshFile = caseFolder + os.path.sep + self.solver_obj.InputCaseName + u".unv"
        self.mesh_generated = CfdTools.write_unv_mesh(self.mesh_obj, self.bc_group, unvMeshFile)
        # FreeCAD always stores the CAD geometry in mm, while FOAM by default uses SI units. This is independent
        # of the user selected unit preferences.
        scale = 0.001
        self.builder.setupMesh(unvMeshFile, scale)

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
        """ Switch case to deal diff fluid boundary condition, thermal and turbulent is not yet fully tested
        """
        #caseFolder = self.solver_obj.WorkingDir + os.path.sep + self.solver_obj.InputCaseName
        bc_settings = []
        for bc in self.bc_group:
            #FreeCAD.Console.PrintMessage("write boundary condition: {}\n".format(bc.Label))

            import _CfdFluidBoundary
            assert(isinstance(bc.Proxy, _CfdFluidBoundary._CfdFluidBoundary))

            # Interface between CfdFluidBoundary (not, in principle, OpenFOAM-specific) and FoamCaseBuilder
            bc_dict = {'name': bc.Label,
                       'type': bc.BoundarySettings['BoundaryType'],
                       'subtype': bc.BoundarySettings['BoundarySubtype']}
            import Units
            if bc.BoundarySettings['VelocityIsCartesian']:
                velocity = [Units.Quantity(bc.BoundarySettings['Ux']).getValueAs("m/s"),
                            Units.Quantity(bc.BoundarySettings['Uy']).getValueAs("m/s"),
                            Units.Quantity(bc.BoundarySettings['Uz']).getValueAs("m/s")]
            else:
                veloMag = Units.Quantity(bc.BoundarySettings['VelocityMag']).getValueAs("m/s")
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
                        else:
                            raise RuntimeError
                    else:
                        raise RuntimeError
                except (SystemError, RuntimeError):
                    from PySide import QtGui
                    QtGui.QMessageBox.critical(None, "Face error",
                                               bc.BoundarySettings['DirectionFace'] + " is not a valid, planar face.")
                    raise RuntimeError

            bc_dict['velocity'] = velocity
            bc_dict['pressure'] = Units.Quantity(bc.BoundarySettings['Pressure']).getValueAs("kg*m/s^2")
            bc_dict['massFlowRate'] = Units.Quantity(bc.BoundarySettings['MassFlowRate']).getValueAs("kg/s")
            bc_dict['volFlowRate'] = Units.Quantity(bc.BoundarySettings['VolFlowRate']).getValueAs("m^3/s")
            bc_dict['slipRatio'] = Units.Quantity(bc.BoundarySettings['SlipRatio']).getValueAs("m/m")
            if bc.BoundarySettings['PorousBaffleMethod'] == 0:
                bc_dict['pressureDropCoeff'] = Units.Quantity(bc.BoundarySettings['PressureDropCoeff']).getValueAs("m/m")
            elif bc.BoundarySettings['PorousBaffleMethod'] == 1:
                wireDiam = Units.Quantity(bc.BoundarySettings['ScreenWireDiameter']).getValueAs("m").Value
                spacing = Units.Quantity(bc.BoundarySettings['ScreenSpacing']).getValueAs("m").Value
                CD = 1.0  # Drag coeff of wire (Simmons - valid for Re > ~300)
                beta = (1-wireDiam/spacing)**2
                bc_dict['pressureDropCoeff'] = CD*(1-beta)
            else:
                raise Exception("Unrecognised method for porous baffle resistance")

            # NOTE: Code depreciated 20/01/2017 (AB)
            # Temporarily disabling turbulent and heat transfer boundary conditon application
            # This functionality has not yet been added and has been removed from the CFDSolver object
            # Turbulence properties have been relocated to physics object
            # if self.solver_obj.HeatTransfering:
            #     bc_dict['thermalSettings'] = {"subtype": bc.ThermalBoundaryType,
            #                                     "temperature": bc.TemperatureValue,
            #                                     "heatFlux": bc.HeatFluxValue,
            #                                     "HTC": bc.HTCoeffValue}
            # bc_dict['turbulenceSettings'] = {'name': self.solver_obj.TurbulenceModel}
            # # ["Intensity&DissipationRate","Intensity&LengthScale","Intensity&ViscosityRatio", "Intensity&HydraulicDiameter"]
            # if self.solver_obj.TurbulenceModel not in set(["laminar", "invisid", "DNS"]):
            #     bc_dict['turbulenceSettings'] = {"name": self.solver_obj.TurbulenceModel,
            #                                     "specification": bc.TurbulenceSpecification,
            #                                     "intensityValue": bc.TurbulentIntensityValue,
            #                                     "lengthValue": bc.TurbulentLengthValue
            #                                     }
            bc_settings.append(bc_dict)

        #self.builder.internalFields = {'p': 0.0, 'U': (0, 0, 0)}
        self.builder.internalFields = self.extractInternalField()
        self.builder.boundaryConditions = bc_settings

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
                    shape.exportStl(fname)
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
                # Calculate Darcy-Forchheimer coefficients
                pd['e1'] = po.porousZoneProperties['BundleLayerNormal']  # OpenFOAM modifies to be orthogonal to e3
                pd['e3'] = po.porousZoneProperties['TubeAxis']
                spacing = po.porousZoneProperties['TubeSpacing']
                d0 = po.porousZoneProperties['OuterDiameter']
                u0 = po.porousZoneProperties['VelocityEstimate']
                kinVisc = self.builder.fluidProperties['kinematicViscosity']
                if kinVisc is None or kinVisc == 0.0:
                    FreeCAD.Console.PrintError("Viscosity must be set for Jakob correlation.\n")
                    raise ValueError
                if spacing < d0:
                    FreeCAD.Console.PrintError("Tube spacing may not be less than diameter.\n")
                    raise ValueError
                C = 1.0/(3.0**0.5/2*spacing)*0.5*(1.0+0.47/(spacing/d0-1)**1.06)
                D = C/d0*(u0*d0/kinVisc)**(1.0-0.16)
                F = C*(u0*d0/kinVisc)**(-0.16)
                pd['D'] = [D, D, 0]  # Currently assuming zero drag parallel to tube bundle
                pd['F'] = [F, F, 0]
            else:
                raise Exception("Unrecognised method for porous baffle resistance")
            porousZoneSettings.append(pd)
        print porousZoneSettings
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
