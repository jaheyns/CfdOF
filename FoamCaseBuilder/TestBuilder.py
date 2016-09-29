# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2016 - Qingfeng Xia <qingfeng.xia iesensor.com>         *
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

import sys
import os

PACKAGE_PARENT = '..'
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))

script_path = os.path.dirname(os.path.abspath( __file__ ))
mesh_file = script_path + '/TestCase.unv'
from utility import runFoamCommand
if not os.path.exists(mesh_file):
    mesh_file_url = "https://www.iesensor.com/download/TestCase.unv"
    print('using curl to download mesh file first, it will fail if curl is abscent')
    print('you need to run this script twice to get the case built. \n reason unknown, could be mesh download not finished during building')
    runFoamCommand('curl -o {} {}'.format(mesh_file, mesh_file_url))

def test_runCommand():
    runFoamCommand(["icoFoam", '-help'])
    
def test_runCommand1():
    cmd = ['transformPoints','-case', '/home/qingfeng/Documents/TestCase', '-scale', '"(1 1 1)"']
    #cmd = ["icoFoam", '-help']
    import subprocess
    #cmdline = """bash -i -c '{}' """.format(' '.join(cmd))
    cmdline = ' '.join(cmd)
    print(cmdline)
    out = subprocess.check_output(['bash', '-i', '-c', cmdline], stderr=subprocess.PIPE)
    print(out)
    #runFoamCommand(cmd)
    
def test_detectFoam():
    from utility import _detectFoamVersion, _detectFoamDir
    print(_detectFoamVersion())

def test_dictFileLoad():
    #PyFoam 0.66 can parse dict file for OF>=3.0, with "#include file"
    case="/opt/openfoam4/tutorials/incompressible/simpleFoam/pipeCyclic/"
    file="0.orig/U"
    from PyFoam.RunDictionary.ParsedParameterFile import ParsedParameterFile
    f = ParsedParameterFile(case + file)
    print(f['boundaryField']['walls'])

def test_dictFileLoad2():
    #case="/opt/openfoam4/tutorials/incompressible/simpleFoam/pipeCyclic/"
    case = '/tmp/'
    if not os.path.exists(case + os.path.sep + "constant"):
        os.mkdir(case + os.path.sep + "constant")
    lines = ['transportModel  Newtonian;','\n', 'nu              nu [ 0 2 -1 0 0 0 0 ] 1e-06;']
    createRawFoamFile(case, "constant", "transportProperties", lines)
    file = "constant/transportProperties" # #PyFoam 0.6.6 can not parse this dict for OpenFOAM 3.0+
    from PyFoam.RunDictionary.ParsedParameterFile import ParsedParameterFile
    f = ParsedParameterFile(case + file)
    print(f['nu'])
    
def test_dictFileLoad3():
    #case="/opt/openfoam4/tutorials/incompressible/simpleFoam/pipeCyclic/"
    case = '/tmp/TestCaseCLI/'
    file = '0/p'
    from PyFoam.RunDictionary.ParsedParameterFile import ParsedParameterFile
    f = ParsedParameterFile(case + file)
    print(f['internalField'])

    
def test_basic_builder(using_laminar_model = True):
    """assuming mesh has generated with patches name same as bc_names list
    This is only a test, it will not generate accurate result due to low mesh quality
    PyFoam/examples/CaseBuilder/lesSnappy.pfcb
    """
    using_pressure_inlet = False  # only for compressible fluid case, not implemented yet
    # case setup is fine for kEpsilon, but will diverge!
    
    from BasicBuilder import getDefaultSolverSettings, BasicBuilder
    solver_settings = getDefaultSolverSettings()
    case="/tmp/TestCaseCLI"
    #zipped_template_file is deprecated

    #default to setup in ~/.bashrc:  source '/opt/openfoam40/etc/bashrc'
    #but FOAM_DIR can be setup before run any command
    #setFoamDir('/home/qingfeng/OpenFOAM/OpenFOAM-2.1.x/')
    #setFoamVersion((2,1,0))
    #print(FOAM_SETTINGS['FOAM_VERSION'])

    #tutorial_path = "tutorials/incompressible/simpleFoam/pipeCyclic"
    tutorial_path = None # build up case from scratch
    template_path = tutorial_path
            
    #pipe diameter is 20mm
    if using_laminar_model:
        turbulenceSettings={'name': "laminar"}
        inletVelocity = (0, 0, 1)
        kinematicViscosity = 1
    else:
        #"Intensity&LengthScale","unspecific","Intensity&HydraulicDiameter"
        turbulenceSettings={'name': "realizableKE", 'specification':"Intensity&HydraulicDiameter",
                        'intensityValue': 0.05, 'lengthValue': 0.01} 
        solver_settings['turbulenceModel'] = "realizableKE"
        # 'kEpsilon' case setup is fine, but divergent is hard for he bad mesh quality
        inletVelocity = (0, 0, 0.1)
        kinematicViscosity = 0.000001

    transientSettings = {"startTime":0.0, "endTime":1.0, "timeStep":0.001, "writeInterval":100}
    # compressible flow only, currently not supported yet!
    inlet={'name': "Inlet", 'type': "inlet", 'subtype': "totalPressure", 'value': 10000, 
            'turbulenceSettings': turbulenceSettings}
    inlet={'name': "Inlet", 'type': "inlet", 'subtype': "uniformVelocity", 'value': inletVelocity, 
            'turbulenceSettings': turbulenceSettings}
    #inlet={'name': "Inlet", 'type': "inlet", 'subtype': "volumetricFlowRate", 'value': 0.0001, 'turbulenceSettings': turbulenceSettings}

    outlet={'name': "Outlet", 'type': "outlet", 'subtype': "staticPressure", 'value': 0.0}
    #outlet={'name': "Outlet", 'type': "outlet", 'subtype': "outFlow", 'value': 0.0}

    case_builder = BasicBuilder(case,  solver_settings, template_path)
    case_builder.createCase() # clear case,  clear data
    case_builder.setupMesh(mesh_file, 0.001) 
    case_builder.turbulenceProperties = turbulenceSettings
    #print case_builder.fluidProperties
    case_builder.fluidProperties = {'name':'oneLiquid', 'kinematicViscosity': kinematicViscosity}
    #higher viscosity may help converge in coarse mesh
    case_builder.boundaryConditions = [inlet, outlet]
    case_builder.internalFields = {'U': inletVelocity}
    
    case_builder.build()
    case_builder.setupRelaxationFactors(0.1, 0.1, 0.3) # changed the default setting, not necessary
    case_builder.setupPressureReference(0.0, 0) # pRefValue, pRefValue
    msg = case_builder.check()
    if msg:
        print('Error: case setup check failed with message\n, {}, \n please check dict files'.format(msg))

    #fvScheme file: divSchemes, fvSolution file has turbulence model specific var setting up
    case_builder.setupRelaxationFactors(0.1, 0.1)  # reduce for the coarse 3D mesh
    #residual
    
    cmdline = "simpleFoam -case {} > log.{}".format(case, case_builder._solverName)  # foamJob <solver> & foamLog
    print("please run the command in new terminal: \n"+ cmdline) 
    #lauch command outside please, it takes several minutes to converge
    #pyFoamPlotWatcher.py
    
    cmdline = "paraFoam -case {}".format(case)
    print("view result in command with: \n"+ cmdline)

    
def test_heat_transfer_builder(compressible=True):
    #
    from ThermalBuilder import getDefaultHeatTransferSolverSettings
    solver_settings = getDefaultHeatTransferSolverSettings()
    solver_settings['compressible'] = compressible
    case="/tmp/TestCaseCLI"
    #template_path = "tutorials/heatTransfer/buoyantBoussinesqSimpleFoam/hotRoom/"
    template_path = None
    
    using_laminar = False
    if using_laminar: # buoyantBoussinesqSimpleFoam solver does not support laminar flow
        turbulenceSettings={'name': 'laminar'}
        solver_settings['turbulenceModel'] = 'laminar'
        inletVelocity = (0, 0, 0.02)
        inletPressure = 10100
    else:
        turbulenceSettings={'name': solver_settings['turbulenceModel'], 'specification':"intensity&HydraulicDiameter",
                    'intensityValue': 0.05, 'lengthValue': 0.01}
        inletVelocity = (0, 0, 1.0)
        inletPressure = 11000
    
    inlet={'name': "Inlet", 'type': "inlet", 'subtype': "totalPressure", 'value': inletPressure, 
            'turbulenceSettings': turbulenceSettings,
            'thermalSettings': {'subtype':'fixedValue', 'temperature':320}}
    inlet={'name': "Inlet", 'type': "inlet", 'subtype': "uniformVelocity", 'value': inletVelocity, 
            'turbulenceSettings': turbulenceSettings,
            'thermalSettings': {'subtype':'fixedValue', 'temperature':320}}
    outlet={'name': "Outlet", 'type': "outlet", 'subtype': "staticPressure", 'value': 1e5,
            #turbulenceSettings is only necessary for inlet
            'thermalSettings': {'subtype':'fixedValue', 'temperature':300}} # subtype will be overwritten
    wall={'name': "defaultFaces", 'type': "wall",'subtype': "fixed", # faces without allocated boundary condition setting
          #'thermalSettings': {'subtype':'heatFlux', 'heatFlux':100}}
          'thermalSettings': {'subtype':'fixedGradient', 'heatFlux':10000}}
    
    from ThermalBuilder import ThermalBuilder
    case_builder = ThermalBuilder(case,  solver_settings, template_path)
    case_builder.createCase()
    
    case_builder.setupMesh(mesh_file, 0.001) 
    case_builder.turbulenceProperties = turbulenceSettings
    #print case_builder.fluidProperties
    case_builder.fluidProperties = {'name':'air'}
    #higher viscosity may help converge
    case_builder.boundaryConditions = [inlet, outlet, wall]
    case_builder.internalFields = {'U': inletVelocity, 'T': 300, 'p': 100000}
    
    case_builder.build()
    msg = case_builder.check()
    if msg:
        print('Error: case setup check failed with message\n, {}, \n please check dict files'.format(msg))
    
    case_builder.summarize()
    
if __name__ == '__main__':
    #test_runCommand()
    #test_runCommand1()
    #test_dictFileLoad()
    #test_dictFileLoad2()
    #test_dictFileLoad3()
    test_basic_builder()
    #test_basic_builder(using_laminar_model = False)
    #test_heat_transfer_builder()
