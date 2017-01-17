# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2016 - Qingfeng Xia <qingfeng.xia eng ox ac uk>                 *       *
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

from __future__ import print_function

from BasicBuilder import BasicBuilder
from utility import *
from utility import _debug

supported_thermal_value_types = set([
'fixedValue', #fixed Temperature
'zeroGradient', #no heat transfer 
'fixedGradient', #fixed gradient T/m
'mixed',  # mixed fixedGradient and fixedValue
'coupled',  # for conjugate heat transfer
# boundary dependent
'heatFlux', # derived for wall
'HTC', # derived for wall
'totalTemperature', # only for inlet
])

supported_radiation_models = ['noRadiation', 'P1' , 'viewFactor']
def setupRadiationProperties(case, radiationModel):
    """ $FOAM_DIR/tutorials/heatTransfer/
    """
    pass

def getDefaultHeatTransferSolverSettings():
    return {
            'parallel': False,
            'compressible': False,
            'nonNewtonian': False, 
            'transonic': False,
            #'acoustic': False, # rhoPimpleFOAM
            'porous':False,
            'dynamicMeshing':False,
            'buoyant': True, # body force, like gravity, needs a dict file `constant/g`
            'gravity': (0, -9.81, 0),
            'transient':False,
            'turbulenceModel': 'kEpsilon',
            #
            'potentialInit': False, # CSIP team contributed feature, new property inserted into CfdSolverFoam
            #
            'heatTransfering':True,
            'conjugate': False,
            'radiationModel': 'noRadiation',
            #'conbustionModel': 'noConbustion',
            }  # containing all setting properties


class ThermalBuilder(BasicBuilder):
    """ support both compressible flow and heat transferring
    """
    def __init__(self,  casePath, 
                        solverSettings=getDefaultHeatTransferSolverSettings(),
                        templatePath=None,
                        fluidProperties = {'name':'air', "compressible":False, 'kinematicViscosity':1e5},
                        turbulenceProperties = {'name':'kEpsilon'},
                        boundarySettings = [],
                        internalFields = {},
                        transientSettings = {"startTime":0.0, "endTime":1.0, "timeStep":0.001, "writeInterval":100},
                        paralleSettings = {'method':"simple", "numberOfSubdomains":multiprocessing.cpu_count()},
                ):
        """ must call the super's __init__()
        """
        super(ThermalBuilder, self).__init__(casePath, 
                        solverSettings,
                        templatePath,
                        fluidProperties,
                        turbulenceProperties,
                        boundarySettings,
                        internalFields,
                        transientSettings,
                        paralleSettings,
                        )

    def build(self):
        super(ThermalBuilder, self).build()
        #set extra BC, internal field, radiationProperties, gravity, multiregion
        #compressible flow wall function is deal inside BasicBuilder
        case = self._casePath
        #gravity is setup in BasicBuilder()
        #if radiationModel

    def check(self):
        """ heatTransfer must has buoyant = True, and existent of dict
        """
        msg = super(ThermalBuilder, self).check()
        case = self._casePath
        settings = self._solverSettings
        #call the super's methods firstly
        if settings['heatTransfering']:
            flist = ['constant/g', '0/T', '0/p_rgh']
            for f in flist:
                if not os.path.exists(case + os.path.sep + f):
                    return msg + "Error: {} file not found\n".format(f)
        return msg

    #####################################################################################        
    def setupFluidProperties(self, value=None):
        if value and isinstance(value, dict):
            self.fluidProperties = value
        if self._solverSettings['compressible']:
            self.setupThermophysicalProperties()
        else:
            self.setupTransportProperties()

    def setupTransportProperties(self):
        #
        case = self._casePath
        solver_settings = self._solverSettings

        if solver_settings['nonNewtonian']:
            print('Warning: nonNewtonian case setup is not implemented, please edit dict file directly')
        else:
            if self.fluidProperties['name'] == 'air':
                lines = air_Boussinesq_thermophysicalProperties
            if self.fluidProperties['name'] == 'water':
                lines = water_Boussinesq_thermophysicalProperties
            else:
                print("Error: unrecoginsed fluid name: {}".format(self.fluidProperties['name']))
            if _debug:
                print("Info: Fluid properties is written to constant/transportProperties")
                print(lines)
        createRawFoamFile(case, "constant", "transportProperties", lines)
        #todo: viscosity or other properties should be settable

    def setupThermophysicalProperties(self):
        #
        case = self._casePath
        solver_settings = self._solverSettings

        if solver_settings['nonNewtonian']:
            print('Warning: nonNewtonian case setup is not implemented, please edit dict file directly')
        else:
            if self.fluidProperties['name'] == 'air':
                if solver_settings['compressible'] and not solver_settings['heatTransfering']: 
                    type = 'hePsiThermo'  # transport: sutherland or const, default to const
                else:
                    type = 'heRhoThermo'
                lines = air_thermophysicalProperties % type
            else:
                print("Error: unrecoginsed fluid name: {}".format(self.fluidProperties['name']))
            if _debug:
                print("Infor:Fluid properties is written to constant/thermophysicalProperties")
                print(lines)
        createRawFoamFile(case, "constant", "thermophysicalProperties", lines)

    ###############################################################################################
    """
    /opt/openfoam4/tutorials/heatTransfer/buoyantPimpleFoam/hotRoom
    For compressible flow without heat transfer (mainly with wall), zeroGradient is used, buoyant flow is not considered
    """
    def getSolverCreatedVariables(self):
        # density variable/field 'rho' will be automatically created if not present
        return super(ThermalBuilder, self).getSolverCreatedVariables() | self.getThermalVariables()

    def getThermalVariables(self):
        """ incompressible air flow must calc var 'T' and 'alphat' for turbulence flow
        heatTransfer should consider buoyant effect, adding var 'p_rgh', even for buoyantBoussinesqSimpleFoam
        radiationModel: G for P1 and fvDOM, IDefault for fvDOM, 
        alphat = turbulence->nut()/Prt; // turbulent Prantl number is in general randomly chosen between 0.75 and 0.95
        """
        solverSettings = self._solverSettings
        radiationModel = solverSettings['radiationModel']
        vars = []
        print(solverSettings)
        if solverSettings['heatTransfering']:
            if radiationModel == "noRadiation":
                vars += ['T', 'p_rgh'] # p_rgh for buoyant solver far field pressure field
            else:
                print("Error: radiation is not implemented yet")
                raise NotImplementedError()
        else:
            if solverSettings['compressible']:
                vars += ['T']
        if solverSettings['turbulenceModel'] not in set(['DNS', 'laminar', 'invisid']):
            vars += ['alphat']
        return set(vars)

    '''
    def _createInitVarables(self):
        """all variable file will be created from scratch
        a default fvScheme is needed for each var, but * can be used to match all
        """
        super(ThermalBuilder, self)._createInitVarables()
        vars = self.getThermalVariables()
        casePath = self._casePath

        print("Info: initialize solver created thermal related fields (variables): ",vars)
        for v in vars:

            #clean this file contect if existent
            lines = [
            "dimensions  [0 0 0 0 0 0 0];\n", "\n",
            "internalField uniform 0;\n", "\n",  # will be set again in caseBuilder
            'boundaryField\n', "{\n", "\n", "}\n",
            ]
            if v in set(['T', 'p_rgh',  'alphat']):
                createRawFoamFile(casePath, '0', v, lines, 'volScalarField')
            fname = casePath + os.path.sep + "0" + os.path.sep + v
            f = ParsedParameterFile(fname)
            
            if v == 'T':
                f['dimensions'] = "[0 0 0 1 0 0 0]"
                f['internalField'] = "uniform 300"
  
            elif v == 'alphat': # thermal turbulence viscosity/diffusivity for heat transfer cases
                f['dimensions'] = "[0 2 -1 0 0 0 0]"
                f['internalField'] = 'uniform 0' #
            else:
                print("variable {} is not recognized and dimension is left unchanged".format(v))
                
            f.writeFile()
    '''

    def initBoundaryConditions(self):
        """write default value in 'case/0/p' 'case/0/U' and turbulence related var
        #in polyMesh/boundary  "defaultFaces" must be wall type, but mesh conversion does not rename
        """
        bc_names = listBoundaryNames(self._casePath)
        super(ThermalBuilder, self).initBoundaryConditions()
        self.initThermalBoundaryAsWall(bc_names)

    def initThermalBoundaryAsWall(self, bc_names):
        """ defaultFaces is wall, no heat flux on wall, except for explicitly define
        reference to $FOAM_DIR/tutorials/heatTransfer/buoyantBoussinesqSimpleFoam/hotRoom/0
        """
        f = ParsedParameterFile(self._casePath + "/0/T")
        for bc in bc_names:
            f["boundaryField"][bc]={}
            f["boundaryField"][bc]["type"]="zeroGradient"
        f.writeFile()
            
        if 'alphat' in self._solverCreatedVariables:
            self.initThermalTurbulenceBoundaryAsWall(bc_names)

    def initThermalTurbulenceBoundaryAsWall(self, bc_names):
        # todo: check if this wall function is only for kEpsilon turbulence model?
        # id yplus < 1, set to zero without wall function
        f = ParsedParameterFile(self._casePath + "/0/alphat")
        for bc in bc_names:
            f["boundaryField"][bc]={}
            if self._solverSettings['heatTransfering']:
                if self._solverSettings['compressible']:
                    # tutorials/heatTransfer/buoyantSimpleFoam/buoyantCavity/0/alphat
                    f["boundaryField"][bc]["type"]="compressible::alphatWallFunction"
                    f["boundaryField"][bc]["Prt"]=0.85
                    f["boundaryField"][bc]["value"]="$internalField"
                else:
                    # tutorials/heatTransfer/buoyantBoussinesqSimpleFoam/hotRoom/0/alphat
                    f["boundaryField"][bc]["type"]="alphatJayatillekeWallFunction"
                    f["boundaryField"][bc]["Prt"]=0.85
                    f["boundaryField"][bc]["value"]="$internalField"
            else:
                if self._solverSettings['compressible']:
                    f["boundaryField"][bc]["type"]="compressible::alphatkeWallFunction"
                    f["boundaryField"][bc]["value"]="uniform 0"
                else:
                    f["boundaryField"][bc]["type"]="alphatkeWallFunction"
                    f["boundaryField"][bc]["value"]="uniform 0"         
        f.writeFile()

    def setupThermalBoundary(self):
        """
        - wallHeatTransfer: Tinf and thermal diffusivity of wall
        - externalWallHeatFluxTemperature:  
        - Foam::compressible::convectiveHeatTransferFvPatchScalarField
        Optional thin thermal layer resistances can be specified through thicknessLayers and kappaLayers entries 
        for the fixed heat transfer coefficient mode
        """
        f = ParsedParameterFile(self._casePath + "/0/T")
        for boundary in self._boundarySettings:
            bType = boundary['type']
            s = boundary['thermalSettings']
            bc = boundary['name']
            f["boundaryField"][bc]={}
            # general setup, indepedent of boundary type
            f["boundaryField"][bc]["type"] = s['subtype']
            vType = s['subtype']
            if vType == "fixedValue":
                f["boundaryField"][bc]["value"] = formatValue(s['temperature'])
            elif vType == "zeroGradient": # noHeatFlux
                pass # no need to set a value
            elif vType == "fixedGradient": # T/m
                f["boundaryField"][bc]["gradient"] = formatValue(s['heatFlux'])
            elif vType == "mixed":
                f["boundaryField"][bc]["value"] = formatValue(s['temperature'])
                f["boundaryField"][bc]["gradient"] = formatValue(s['heatFlux'])
            elif vType == "coupled":
                    # type = 'externalCoupledTemperatureMixed'
                    print("{} wall boundary value type is not supproted".format(vType))
                    raise NotImplementedError()
            else: # depedent of boundary type
                if bType == 'wall':    
                    if vType == "heatFlux":
                        # externalWallHeatFluxTemperature seems only for compressible flow
                        if self._solver_settings['compressible']:
                            f["boundaryField"][bc]["type"] = "compressible::externalWallHeatFluxTemperature"
                            f["boundaryField"][bc]["kappa"]= "fluidThermo"
                            f["boundaryField"][bc]["kappaName"]= "none"
                            f["boundaryField"][bc]["q"] = formatValue(s['heatFlux'])
                            f["boundaryField"][bc]["relaxation"] = "1"
                        else:
                            pass
                    elif vType == "HTC":
                        if self._solver_settings['compressible']:
                            f["boundaryField"][bc]["type"] = "compressible::externalWallHeatFluxTemperature"
                            f["boundaryField"][bc]["kappa"]= "fluidThermo"
                            f["boundaryField"][bc]["kappaName"]= "none"
                            f["boundaryField"][bc]["Ta"] = formatValue(s['temperature'])
                            f["boundaryField"][bc]["h"] = formatValue(s['HTC'])
                            f["boundaryField"][bc]["relaxation"] = "1"
                        else:
                            pass
                            #f["boundaryField"][bc]["type"] = "convectiveHeatFlux"
                            #f["boundaryField"][bc]["L"] = 0.1
                    else:
                        print("wall thermal boundary value type: {}    is not defined".format(vType))
                elif bType == 'inlet' and vType == 'totalTemperature':
                    #`gamma` 	ratio of specific heats (Cp/Cv)  for compressible flow, other like U rho can be calculated
                    f["boundaryField"][bc]={'type':'totalTemperature', 'T0': formatValue(s['temperature'])}
                elif bType == 'outlet':
                    assert vType == 'fixedValue' #check: outFlow only?
                    f["boundaryField"][bc]={'type':'inletOutlet', 'inletValue': formatValue(s['temperature']), 'value': formatValue(s['temperature'])}
                elif bType == 'freestream':
                    pass #todo: find the example and code here
                elif bType == 'interface':
                    #todo: find the example and check code here
                    f["boundaryField"][bc]={'type': boundary['subtype']}
                else:
                    print("boundary value type: {}    is not defined".format(bType))
        f.writeFile()
        if 'alphat' in self._solverCreatedVariables:
            self._setupThermalTurbulenceDiffusivity()

    def _setupThermalTurbulenceDiffusivity(self):
        # Prt default value is set in initThermalTurbulenceBoundaryAsWall()
        f = ParsedParameterFile(self._casePath + "/0/alphat")
        for bcDict in self._boundarySettings:
            bc = bcDict['name']
            subtype = bcDict['subtype']
            if bcDict['type'] in set(['inlet', "outlet", "freestream"]):
                f["boundaryField"][bc] = {'type': 'calculated', 'value': "$internalField"}
            elif bcDict['type'] == 'interface':
                ["boundaryField"][bc] = {'type': subtype}
            else:
                pass # done in initThermalTurbulenceBoundaryAsWall() for both compressible and incompressible flow
        f.writeFile()

    def setupBoundaryConditions(self):
        super(ThermalBuilder, self).setupBoundaryConditions()
        self.setupThermalBoundary()
    
    def setupInletBoundary(self, bcDict):
        """ there are four kinds of inlet dependes on: compressible,  transonic
        p and U velocity may need reset for compressible flow
        #T and p_rgh have been setup, alphat has been set
        """
        super(ThermalBuilder, self).setupInletBoundary(bcDict)
        if self._solverSettings['compressible']:
            raise NotImplementedError()

    def setupOutletBoundary(self, bcDict):
        """ outlet dependes on: compressible,  transonic
        """
        super(ThermalBuilder, self).setupOutletBoundary(bcDict)
        #f = ParsedParameterFile(self._casePath + "/0/U")

    def setupFreestreamBoundary(self, bcDict):
        """ atmBoundaryLayer
        """
        super(ThermalBuilder, self).setupFreestreamBoundary(bcDict)
        #f = ParsedParameterFile(self._casePath + "/0/U")

    def setupInterfaceBoundary(self, bcDict):
        """ supersonicFreestream
        """
        super(ThermalBuilder, self).setupInterfaceBoundary(bcDict)
        #f = ParsedParameterFile(self._casePath + "/0/U")


air_Boussinesq_thermophysicalProperties = """

transportModel Newtonian;

// Laminar viscosity
nu              nu [0 2 -1 0 0 0 0] 1e-05;

// Thermal expansion coefficient
beta            beta [0 0 0 -1 0 0 0] 3e-03;

// Reference temperature
TRef            TRef [0 0 0 1 0 0 0] 300;

// Laminar Prandtl number
Pr              Pr [0 0 0 0 0 0 0] 0.9;

// Turbulent Prandtl number
Prt             Prt [0 0 0 0 0 0 0] 0.7;

"""

#compressible: hePsiThermo, transport: sutherland
air_thermophysicalProperties = """

thermoType
{
    type            %s;
    mixture         pureMixture;
    transport       const;
    thermo          hConst;
    equationOfState perfectGas;
    specie          specie;
    energy          sensibleEnthalpy;
}

pRef            100000;

mixture
{
    specie
    {
        nMoles          1;
        molWeight       28.9;
    }
    thermodynamics
    {
        Cp              1000;
        Hf              0;
    }
    transport
    {
        mu              1.8e-05;
        Pr              0.7;
    }
}

"""

# /opt/openfoam4/tutorials/heatTransfer/chtMultiRegionSimpleFoam/heatExchanger/constant/porous
water_thermophysicalProperties = """
thermoType
{
    type            heRhoThermo;
    mixture         pureMixture;
    transport       polynomial;
    thermo          hPolynomial;
    equationOfState icoPolynomial;
    specie          specie;
    energy          sensibleEnthalpy;
}


mixture
{
    // coefficients for water

    specie
    {
        nMoles          1;
        molWeight       18;
    }
    equationOfState
    {
        rhoCoeffs<8>    ( 1000 0 0 0 0 0 0 0 );
    }
    thermodynamics
    {
        Hf              0;
        Sf              0;
        CpCoeffs<8>     ( 4183 0 0 0 0 0 0 0 );
    }
    transport
    {
        muCoeffs<8>     ( 0.001 0 0 0 0 0 0 0 );
        kappaCoeffs<8>  ( 0.58  0 0 0 0 0 0 0 );
    }
}

"""

# for CHT heat transfer
water_thermophysicalProperties_const = """

thermoType
{
    type            heRhoThermo;
    mixture         pureMixture;
    transport       const;
    thermo          hConst;
    equationOfState rhoConst;
    specie          specie;
    energy          sensibleEnthalpy;
}

mixture
{
    specie
    {
        nMoles          1;
        molWeight       18;
    }
    equationOfState
    {
        rho             1000;
    }
    thermodynamics
    {
        Cp              4181;
        Hf              0;
    }
    transport
    {
        mu              959e-6;
        Pr              6.62;
    }
}
"""

# stream model: can be compiled as third-party module Contrib/IAPWS-IF97-OF
