# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2015 - Qingfeng Xia <qingfeng.xia eng ox ac uk>                 *       *
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
        self.mesh_obj = CfdTools.getMesh(analysis_obj)
        self.material_obj = CfdTools.getMaterial(analysis_obj)
        self.bc_group = CfdTools.getConstraintGroup(analysis_obj)
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

        # Create initial case from defaults
        # Until module is integrated, store the defaults inside the module directory rather than the resource dir
        if self.solver_obj.HeatTransfering:
            #self.builder = fcb.BasicBuilder(self.case_folder, CfdTools.getSolverSettings(self.solver_obj), os.path.join(FreeCAD.getResourceDir(), "Mod", "Cfd", "defaults", "chtMultiRegionSimpleFoam"))
            self.builder = fcb.BasicBuilder(self.case_folder, CfdTools.getSolverSettings(self.solver_obj), os.path.join(CfdTools.get_module_path(), "data", "defaults", "chtMultiRegionSimpleFoam"))
        else:
            #self.builder = fcb.BasicBuilder(self.case_folder, CfdTools.getSolverSettings(self.solver_obj), os.path.join(FreeCAD.getResourceDir(), "Mod", "Cfd", "defaults", "simpleFoam"))
            self.builder = fcb.BasicBuilder(self.case_folder, CfdTools.getSolverSettings(self.solver_obj), os.path.join(CfdTools.get_module_path(), "data", "defaults", "simpleFoam"))
        self.builder.createCase()

        self.write_mesh()

        self.write_material()
        self.write_boundary_condition()
        self.builder.turbulenceProperties = {"name": self.solver_obj.TurbulenceModel}

        self.write_solver_control()
        self.write_time_control()

        self.builder.check()
        self.builder.build()
        os.chdir(_cwd)  # restore working dir
        FreeCAD.Console.PrintMessage("{} Sucessfully write {} case to folder \n".format(
                                                        self.solver_obj.SolverName, self.solver_obj.WorkingDir))
        return True

    def write_mesh(self):
        """ This is FreeCAD specific code, convert from UNV to OpenFoam
        """
        caseFolder = self.solver_obj.WorkingDir + os.path.sep + self.solver_obj.InputCaseName
        unvMeshFile = caseFolder + os.path.sep + self.solver_obj.InputCaseName + u".unv"

        self.mesh_generated = CfdTools.write_unv_mesh(self.mesh_obj, self.bc_group, unvMeshFile)

        # FreecAD (internal standard length) mm; while in CFD, it is metre, so mesh needs scaling
        # mesh generated from FreeCAD nees to be scaled by 0.001
        # `transformPoints -scale "(1e-3 1e-3 1e-3)"`
        scale = 0.001
        self.builder.setupMesh(unvMeshFile, scale)
        #FreeCAD.Console.PrintMessage('mesh file {} converted and scaled with ratio {}\n'.format(unvMeshFile, scale))

    def write_material(self, material=None):
        """ Air, Water, CustomedFluid, first step, default to Water, but here increase viscosity for quick convergence
        """
        #self.builder.fluidProperties = {'name': 'oneLiquid', 'kinematicViscosity': 1e-3}
        #self.builder.fluidProperties = self.material_obj.FluidicProperties
        
        #try:
            #Code for new material definitons. might have to consider how builder sees fluid properties in future
        #kinVisc = FreeCAD.Units.Quantity(self.material_obj.Material['KinematicViscosity'])
        #kinVisc = kinVisc.getValueAs('m^2/s')
        
        
        Viscosity = FreeCAD.Units.Quantity(self.material_obj.Material['DynamicViscosity'])
        Viscosity = Viscosity.getValueAs('Pa*s')
        Density = FreeCAD.Units.Quantity(self.material_obj.Material['Density'])
        Density = Density.getValueAs('kg/m^3')
        
        kinVisc = Viscosity/Density
        #kinVisc = kinVisc.getValueAs('m^2/s')
        
        
        self.builder.fluidProperties = {'name': 'oneLiquid', 'kinematicViscosity': float(kinVisc)}
        #except:
            #self.builder.fluidProperties = {'name': 'oneLiquid', 'kinematicViscosity': 1e-3}


    def write_boundary_condition(self):
        """ Switch case to deal diff fluid boundary condition, thermal and turbulent is not yet fully tested
        """
        #caseFolder = self.solver_obj.WorkingDir + os.path.sep + self.solver_obj.InputCaseName
        bc_settings = []
        for bc in self.bc_group:
            #FreeCAD.Console.PrintMessage("write boundary condition: {}\n".format(bc.Label))
            assert bc.isDerivedFrom("Fem::ConstraintFluidBoundary")
            bc_dict = {'name': bc.Label, "type": bc.BoundaryType, "subtype": bc.Subtype, "value": bc.BoundaryValue}
            if bc_dict['type'] == 'inlet' and bc_dict['subtype'] == 'uniformVelocity':
                bc_dict['value'] = [abs(v) * bc_dict['value'] for v in tuple(bc.DirectionVector)]
                # fixme: App::PropertyVector should be normalized to unit length
            if self.solver_obj.HeatTransfering:
                bc_dict['thermalSettings'] = {"subtype": bc.ThermalBoundaryType,
                                                "temperature": bc.TemperatureValue,
                                                "heatFlux": bc.HeatFluxValue,
                                                "HTC": bc.HTCoeffValue}
            bc_dict['turbulenceSettings'] = {'name': self.solver_obj.TurbulenceModel}
            # ["Intensity&DissipationRate","Intensity&LengthScale","Intensity&ViscosityRatio", "Intensity&HydraulicDiameter"]
            if self.solver_obj.TurbulenceModel not in set(["laminar", "invisid", "DNS"]):
                bc_dict['turbulenceSettings'] = {"name": self.solver_obj.TurbulenceModel,
                                                "specification": bc.TurbulenceSpecification,
                                                "intensityValue": bc.TurbulentIntensityValue,
                                                "lengthValue": bc.TurbulentLengthValue
                                                }

            bc_settings.append(bc_dict)
        self.builder.internalFields = {'p': 0.0, 'U': (0, 0, 0.001)}  # must set a nonzero for velocity field
        self.builder.boundaryConditions = bc_settings

    def write_solver_control(self):
        """ relaxRatio, fvOptions, pressure reference value, residual contnrol
        """
        self.builder.setupSolverControl()
        # set relaxationFactors like 0.1 for the coarse 3D mesh, this is a temperoary solution

    def write_time_control(self):
        """ controlDict for time information
        """
        if self.solver_obj.Transient:
            self.builder.transientSettings = {"startTime": self.solver_obj.StartTime,
                                        "endTime": self.solver_obj.EndTime,
                                        "timeStep": self.solver_obj.TimeStep,
                                        "writeInterval": self.solver_obj.WriteInterval
                                        }
