# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2015 - Qingfeng Xia <qingfeng.xia eng ox ac uk>         *
# *   Copyright (c) 2017 - Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>        *
# *   Copyright (c) 2017 - Alfred Bogaers (CSIR) <abogaers@csir.co.za>      *
# *   Copyright (c) 2017 - Johan Heyns (CSIR) <jheyns@csir.co.za>           *
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

import os
import os.path

import FreeCAD

import CfdTools
import FoamCaseBuilder as fcb  # independent module, not depending on FreeCAD


## write CFD analysis setup into OpenFOAM case
#  write_case() is the only public API
class CfdCaseWriterFoam:
    def __init__(self, analysis_obj):
        """ analysis_obj should contains all the information needed,
        boundaryConditionList is a list of all boundary Conditions objects(FemConstraint)
        """
        self.analysis_obj = analysis_obj
        self.solver_obj = CfdTools.getSolver(analysis_obj)
        self.physics_obj,isPresent = CfdTools.getPhysicsObject(analysis_obj)
        self.mesh_obj = CfdTools.getMesh(analysis_obj)
        self.material_obj = CfdTools.getMaterial(analysis_obj)
        self.bc_group = CfdTools.getCfdBoundaryGroup(analysis_obj)
        self.initialVariables_obj, isPresent = CfdTools.getInitialConditions(analysis_obj)
        self.porousZone_obj, self.porousZonePresent = CfdTools.getPorousObject(analysis_obj)
        self.mesh_generated = False

    def write_case(self, updating=False):
        """ Write_case() will collect case setings, and finally build a runnable case
        """
        FreeCAD.Console.PrintMessage("Start to write case to folder {}\n".format(self.solver_obj.WorkingDir))
        _cwd = os.curdir
        os.chdir(self.solver_obj.WorkingDir)  # pyFoam can not write to cwd if FreeCAD is started NOT from terminal

        # Perform initialisation here rather than __init__ in case of path changes
        self.case_folder = os.path.join(self.solver_obj.WorkingDir, self.solver_obj.InputCaseName)
        self.mesh_file_name = os.path.join(self.case_folder, self.solver_obj.InputCaseName, u".unv")
        self.installation_path = self.solver_obj.InstallationPath
        self.solverName = self.fetchOpenFOAMSolverNameBasedOnPhysicsObject()

        self.transientSettings = {#"startTime":self.solver_obj.StartTime,
                                  "endTime":self.solver_obj.EndTime,
                                  "timeStep":self.solver_obj.TimeStep, 
                                  "writeInterval":self.solver_obj.WriteInterval}


        """ NOTE NOTE NOTE: 20/01/2017 these are the default settings from BasicBuilder, which used to be pulled
        in from the the solver object's settings. These settings currently do not exist within the solver object.
        These settings are reproduced here from basicbuilder for ease of understanding for the intended developments
        to come.
        """
        self.temporarySolverSettings = {
                                        'parallel': False,
                                        'compressible': False,
                                        'nonNewtonian': False, 
                                        'transonic': False,
                                        'porous':False,
                                        'dynamicMeshing':False,
                                        'buoyant': False, # body force, like gravity, needs a dict file `constant/g`
                                        'gravity': (0, -9.81, 0),
                                        'transient':False,
                                        'turbulenceModel': 'laminar',
                                        'potentialInit': self.initialVariables_obj["PotentialFoam"],
                                        # 'heatTransfering':False,
                                        # 'conjugate': False, # conjugate heat transfer (CHT)
                                        # 'radiationModel': 'noRadiation',
                                        'ConvergenceCriteria' : self.solver_obj.ConvergenceCriteria
                                        }

        ''' Initial case from defaults '''
        self.builder = fcb.BasicBuilder(casePath = self.case_folder,
                                        installationPath = self.installation_path,
                                        solverSettings = self.temporarySolverSettings,
                                        #solverSettings = CfdTools.getSolverSettings(self.solver_obj),
                                        templatePath = os.path.join(CfdTools.get_module_path(), "data", "defaults", self.solverName),
                                        solverNameExternal = self.solverName,
                                        transientSettings = self.transientSettings,
                                        porousZonePresent = self.porousZonePresent,
                                        porousZone_obj = self.porousZone_obj)
                                        #internalFields = self.internalFields)

        self.builder.setInstallationPath()

        self.builder.createCase()


        self.exportPorousZoneStlSurfaces()
        self.writeFVOptions()

        self.write_mesh()

        self.write_material()
        self.write_boundary_condition()
        #self.builder.turbulenceProperties = {"name": self.solver_obj.TurbulenceModel}

        self.write_solver_control()
        self.write_time_control()

        self.builder.check()
        self.builder.build()
        os.chdir(_cwd)  # restore working dir
        FreeCAD.Console.PrintMessage("{} Sucessfully write {} case to folder \n".format(
                                                        self.solver_obj.SolverName, self.solver_obj.WorkingDir))
        return True


    def exportPorousZoneStlSurfaces(self):
        if self.porousZonePresent:
            for ii in range(len(self.porousZone_obj)):
                import Mesh
                for i in range(len(self.porousZone_obj[ii].shapeList)):
                    shape = self.porousZone_obj[ii].shapeList[i].Shape
                    path = os.path.join(self.solver_obj.WorkingDir,self.solver_obj.InputCaseName,"STLSurfaces")
                    if not os.path.exists(path):
                        os.makedirs(path)
                    fname = os.path.join(self.solver_obj.WorkingDir,self.solver_obj.InputCaseName,"STLSurfaces",self.porousZone_obj[ii].partNameList[i]+u".stl")
                    shape.exportStl(fname)
                    FreeCAD.Console.PrintMessage("succesfully wrote stl surface\n")
            self.writeTopoSetDictFile()


    def writeTopoSetDictFile(self):
        #NOTE: this function opens the helper file topoSetDuctStlToCellZone and fills in the necessary pieces of information
        #This way, for compatibility with different versions of OpenFOAM, all OF version specific files can be stored in
        #data/defuaults folder. The entries that are entered are located within {} in the specified file.
        porousObject = self.porousZone_obj
        fname = os.path.join(self.solver_obj.WorkingDir,self.solver_obj.InputCaseName,"system","topoSetDict")
        fid  = open(fname,'w')

        helperFile = open(os.path.join(CfdTools.get_module_path(), "data", "defaults", "helperFiles","Header"),'r')
        helperText = helperFile.read()
        fid.write(helperText.format("system","topoSetDict"))
        helperFile.close()


        fid.write("                                                                               \n")
        fid.write("actions                                                                        \n")
        fid.write("(                                                                              \n")
        counter = 0
        for ii in range(len(porousObject)):
            for jj in range(len(porousObject[ii].partNameList)):
                p = porousObject[ii].porousZoneProperties
                counter += 1
                helperFile = open(os.path.join(CfdTools.get_module_path(), "data", "defaults", "helperFiles","topoSetDictStlToCellZone"),'r')
                helperText = helperFile.read()
                fid.write(helperText.format(porousObject[ii].partNameList[jj]+"SelectedCells",
                                            porousObject[ii].partNameList[jj]+u".stl",
                                            str(p["OX"]),
                                            str(p["OY"]),
                                            str(p["OZ"]),
                                            "porosity"+str(counter),
                                            porousObject[ii].partNameList[jj]+"SelectedCells"))
                helperFile.close()
        fid.write(");\n")
        fid.close()


    def writeFVOptions(self):
        #NOTE: this function opens the helper file fvOptionsPorousZone and fills in the necessary pieces of information
        #This way, for compatibility with different versions of OpenFOAM, all OF version specific files can be stored in
        #data/defuaults folder. The entries that are entered are located within {} in the specified file.
        if self.porousZonePresent:
            porousObject = self.porousZone_obj
            fname = os.path.join(self.solver_obj.WorkingDir,self.solver_obj.InputCaseName,"constant","fvOptions")
            fid  = open(fname,'w')

            helperFile = open(os.path.join(CfdTools.get_module_path(), "data", "defaults", "helperFiles","Header"),'r')
            helperText = helperFile.read()
            fid.write(helperText.format("constant","fvOptions"))
            helperFile.close()

            counter = 0
            for ii in range(len(porousObject)):
                for jj in range(len(porousObject[ii].partNameList)):
                    p = porousObject[ii].porousZoneProperties
                    counter += 1

                    helperFile = open(os.path.join(CfdTools.get_module_path(), "data", "defaults", "helperFiles","fvOptionsPorousZone"),'r')
                    helperText = helperFile.read()
                    helperFile.close()
                    fid.write(helperText.format("porosity"+str(counter),
                                                "porosity"+str(counter),
                                                str(p["dx"]),
                                                str(p["dy"]),
                                                str(p["dz"]),
                                                str(p["fx"]),
                                                str(p["fy"]),
                                                str(p["fz"]),
                                                str(p["e1x"]),
                                                str(p["e1y"]),
                                                str(p["e1z"]),
                                                str(p["e3x"]),
                                                str(p["e3y"]),
                                                str(p["e3z"])))

            fid.write("//************************************************************************ //  \n")
            fid.close()

    def fetchOpenFOAMSolverNameBasedOnPhysicsObject(self):
        ''' NOTE: This should be built up slowly from the ground up as more physics is made available. A logical flow
                  of thought would be to follow the outline within the tutorials
        '''
        solver = None

        if self.physics_obj['Flow'] == 'Incompressible' and (self.physics_obj['Thermal'] is None):
            if self.physics_obj['Time'] == 'Transient':
                solver = 'pimpleFoam'
            else:
                solver = 'simpleFoam'

        return solver

    def extractInternalField(self):
        Ux = FreeCAD.Units.Quantity(self.initialVariables_obj['Ux'])
        Ux = Ux.getValueAs('m/s')
        Uy = FreeCAD.Units.Quantity(self.initialVariables_obj['Uy'])
        Uy = Uy.getValueAs('m/s')
        Uz = FreeCAD.Units.Quantity(self.initialVariables_obj['Uz'])
        Uz = Uz.getValueAs('m/s')
        P = FreeCAD.Units.Quantity(self.initialVariables_obj['P'])
        P = P.getValueAs('kg*m/s^2')
        internalFields = {'p': float(P), 'U': (float(Ux), float(Uy), float(Uz))}
        return internalFields

    def write_mesh(self):
        """ This is FreeCAD specific code, convert from UNV to OpenFoam
        """
        caseFolder = self.solver_obj.WorkingDir + os.path.sep + self.solver_obj.InputCaseName
        unvMeshFile = caseFolder + os.path.sep + self.solver_obj.InputCaseName + u".unv"

        self.mesh_generated = CfdTools.write_unv_mesh(self.mesh_obj, self.bc_group, unvMeshFile)

        ''' FreecAD (internal standard length) mm; while in CFD, it is metre, so mesh needs scaling mesh generated
            from FreeCAD nees to be scaled by 0.001 `transformPoints -scale "(1e-3 1e-3 1e-3)"`
        '''
        scale = 0.001
        self.builder.setupMesh(unvMeshFile, scale)
        #FreeCAD.Console.PrintMessage('mesh file {} converted and scaled with ratio {}\n'.format(unvMeshFile, scale))

    def write_material(self, material=None):
        """ Air, Water, CustomedFluid, first step, default to Water, but here increase viscosity for quick convergence
        """
        #self.builder.fluidProperties = {'name': 'oneLiquid', 'kinematicViscosity': 1e-3}

        if self.physics_obj['Turbulence']=='Inviscid':
            kinVisc = 0.0
        else:
            Viscosity = FreeCAD.Units.Quantity(self.material_obj.Material['DynamicViscosity'])
            Viscosity = Viscosity.getValueAs('Pa*s')
            Density = FreeCAD.Units.Quantity(self.material_obj.Material['Density'])
            Density = Density.getValueAs('kg/m^3')

            kinVisc = Viscosity/Density

        self.builder.fluidProperties = {'name': 'oneLiquid', 'kinematicViscosity': float(kinVisc)}


    def write_boundary_condition(self):
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
                except SystemError, RuntimeError:
                    from PySide import QtGui
                    QtGui.QMessageBox.critical(None, "Face error",
                                               bc.BoundarySettings['DirectionFace'] + " is not a valid, planar face.")
                    raise RuntimeError

            bc_dict['velocity'] = velocity
            bc_dict['pressure'] = Units.Quantity(bc.BoundarySettings['Pressure']).getValueAs("kg*m/s^2")
            bc_dict['massflowrate'] = Units.Quantity(bc.BoundarySettings['MassFlowRate']).getValueAs("kg/s")
            bc_dict['volflowrate'] = Units.Quantity(bc.BoundarySettings['VolFlowRate']).getValueAs("m^3/s")
            bc_dict['slipratio'] = Units.Quantity(bc.BoundarySettings['SlipRatio']).getValueAs("m/m")

            ''' NOTE: Code depreciated 20/01/2017 (AB)
                      Temporarily disabling turbulent and heat transfer boundary conditon application
                      This functionality has not yet been added and has been removed from the CFDSolver object
                      Turbulence properties have been relocated to physics object
            '''
            #if self.solver_obj.HeatTransfering:
                #bc_dict['thermalSettings'] = {"subtype": bc.ThermalBoundaryType,
                                                #"temperature": bc.TemperatureValue,
                                                #"heatFlux": bc.HeatFluxValue,
                                                #"HTC": bc.HTCoeffValue}
            #bc_dict['turbulenceSettings'] = {'name': self.solver_obj.TurbulenceModel}
            ## ["Intensity&DissipationRate","Intensity&LengthScale","Intensity&ViscosityRatio", "Intensity&HydraulicDiameter"]
            #if self.solver_obj.TurbulenceModel not in set(["laminar", "invisid", "DNS"]):
                #bc_dict['turbulenceSettings'] = {"name": self.solver_obj.TurbulenceModel,
                                                #"specification": bc.TurbulenceSpecification,
                                                #"intensityValue": bc.TurbulentIntensityValue,
                                                #"lengthValue": bc.TurbulentLengthValue
                                                #}
            bc_settings.append(bc_dict)

        #self.builder.internalFields = {'p': 0.0, 'U': (0, 0, 0)}
        self.builder.internalFields = self.extractInternalField()
        self.builder.boundaryConditions = bc_settings

    def write_solver_control(self):
        """ relaxRatio, fvOptions, pressure reference value, residual contnrol
        """
        self.builder.setupSolverControl()


    def write_time_control(self):
        """ controlDict for time information
        """
        #if self.solver_obj.Transient:
        if self.physics_obj["Time"] == "Transient":
            self.builder.transientSettings = {#"startTime": self.solver_obj.StartTime,
                                              "endTime": self.solver_obj.EndTime,
                                              "timeStep": self.solver_obj.TimeStep,
                                              "writeInterval": self.solver_obj.WriteInterval}
