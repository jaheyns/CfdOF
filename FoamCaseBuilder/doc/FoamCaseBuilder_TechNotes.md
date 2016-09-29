### boundary types

```python
basic_boundary_value_types = set([
# `ls $FOAM_SRC/finiteVolume/fields/fvPatchFields/basic`
'fixedValue',
'fixedGradient',
'mixed',
'zeroGradient',
'calculated',
'coupled'  # FSI, conjugate heat transfter
# derived: see more by `ls $FOAM_SRC/finiteVolume/fields/fvPatchFields/derived`
])

supported_boundary_value_types = basic_boundary_value_types | supported_outlet_types | 
    supported_inlet_types | supported_interface_types | supported_wall_types 
```


Wall functions `find $FOAM_SRC/TurbulenceModels -name wallFunctions`
epsilonWallFunctions  kqRWallFunctions  omegaWallFunctions nutWallFunctions
alphatWallFunctions
fWallFunctions v2WallFunctions


### solver name deduction

solver is deduced from properties of CfdSolver

fvSolution dict need setup for different algorithms like PISO, SIMPLE PIMPLE

#### incompressible
icoFoam: is transient solver for incompressible, laminar flow of Newtonian fluids.
pimpleFoam: is large time-step transient solver for incompressible (merged PISO-SIMPLE).
pisoFoam: is transient solver for incompressible flow.
simpleFoam: is steady-state solver for compressible, turbulent flow

#### Heat Transferring
buoyantBoussinesqSimpleFoam: Steady-state solver for buoyant, turbulent flow of incompressible fluids
buoyantSimpleFoam: Steady-state solver for buoyant, turbulent flow of compressible fluids
buoyantBoussinesqPimpleFoam: transient solver for buoyant, turbulent flow of incompressible fluids
buoyantPimpleFoam: transient solver for buoyant, turbulent flow of compressible fluids

conjudge heat transfer CHT is not supported yet!
radiation model can be applied to all those solvers

============ not supported by FoamCaseBuilder yet ===============

#### compressible
all solver begin with "rho" is density-based sovler, even if fluid is incompressible
only "sonic*" are designed for truely compressible fluid 
sonicDyMFoam, sonicFoam, sonicLiquidFoam
rhoCentralFoam rhoPimpleFoam  rhoSimpleFoam   
rhoPorousSimpleFoam  rhoPimpleDyMFoam  rhoCentralDyMFoam

#### multiphaseModels, speciesModels
cavitatingFoam                   multiphaseEulerFoam
compressibleInterDyMFoam         multiphaseInterDyMFoam
compressibleInterFoam            multiphaseInterFoam
compressibleMultiphaseInterFoam  potentialFreeSurfaceDyMFoam
driftFluxFoam                    potentialFreeSurfaceFoam
interDyMFoam                     reactingMultiphaseEulerFoam
interFoam                        reactingTwoPhaseEulerFoam
interMixingFoam                  twoLiquidMixingFoam
interPhaseChangeDyMFoam          twoPhaseEulerFoam
interPhaseChangeFoam

#### lagrangian
coalChemistryFoam                reactingParcelFilmFoam
DPMFoam                          reactingParcelFoam
icoUncoupledKinematicParcelFoam  simpleReactingParcelFoam
MPPICFoam                        sprayFoam

#### foam-ext extra solvers
foam-extend 3.0 has viscoelastic solver and coupled, multisolver, mechanical solver


### Fluid properties setup

<http://www.openfoam.com/documentation/user-guide/thermophysical.php>
For compressible fluid use: `thermophysicalProperties`
$FOAM_DIR/tutorials/heatTransfer/buoyantPimpleFoam/hotRoom/constant/thermophysicalProperties

For imcompressible case just set viscosity 'nu'
For incompressible heattransfer fluid use: `transportProperties`, due to Boussinesq approx
    [$FOAM_DIR/tutorials/heatTransfer/buoyantBoussinesqSimpleFoam/hotRoom/constant/transportProperties]
    ```
    transportModel Newtonian;

    // Laminar viscosity for air
    nu              [0 2 -1 0 0 0 0] 1e-05;

    // Thermal expansion coefficient
    beta            [0 0 0 -1 0 0 0] 3e-03;

    // Reference temperature
    TRef            [0 0 0 1 0 0 0] 300;

    // Laminar Prandtl number
    Pr              [0 0 0 0 0 0 0] 0.9;

    // Turbulent Prandtl number
    Prt             [0 0 0 0 0 0 0] 0.7;
    ```
    
### Solver control like SIMPLE, PISO

    ```cpp
    SIMPLE
    {
        nNonOrthogonalCorrectors 2;  //default 0
        residualControl
        {
            p               1e-2;
            U               1e-3;
            "(k|epsilon)"   1e-3;
        }
    }

    relaxationFactors
    {
        fields
        {
            p               0.2; //default 0.7
        }
        equations
        {
            U               0.3; //default 0.7
            k               0.3; //default 0.7
            "epsilon.*"     0.5;
        }
    }
    ```
    
### turbulence models

Two groups: compressible and incompressible: `foamList -incompressibleTurbulenceModels`

For OpenFOAM 3.0+ turbulent viscosity variable, nut, mut, nusgs with specific wallfunctions

<http://www.openfoam.com/documentation/user-guide/turbulence.php>
Turbulence modelling is independent of solver, i.e. laminar, RAS or LES may be selected.

groups of turbulence models into: laminar, RAS, LES (including DES)
- inviscous flow: basic/potentialFoam
- RAS models: low and high Re
- LES models are not listed, see more at <http://www.openfoam.org/features/LES.php>
- DES as a mixed LES and RAS: DES models are defined as a subset of the available LES models.
 see <http://www.openfoam.com/version-v3.0+/solvers-and-physics.php>  
 see also: <http://cfd.direct/openfoam/features/les-des-turbulence-modelling/>  
+ LES, setup is not implemented
- DNS solver: dnsFoam, which is not practical for engineering calculation

================================================
# not needed as RAS model setting which is simple
LES_turbulenceProperties_templates = {
                    'kOmega': "tutorials/incompressible/pisoFoam/les/pitzDaily/",
                    'kOmegaSST': "tutorials/incompressible/pisoFoam/les/pitzDaily/",
                    'kEpsilon': "",
                    'RNGkEpsilon': "",
                    'realizableKE': "",
                    "SpalartAllmaras": "",
                    
}

SpalartAllmaras: tutorials/incompressible/simpleFoam/airfoil2d/0.org
kEpsilonRealizable: tutorials/incompressible/simpleFoam/pipeCyclic/0.org
        
================================================

### Turbulence model coeff

+ kOmega coeff 
/opt/openfoam4/tutorials/heatTransfer/buoyantSimpleFoam/buoyantCavity/0
omega 0.12

see $FOAM_DIR/tutorials/compressible/rhoPimpleFoam/ras/cavity/0
omeaga 2.6
    
+ kEpsilon model ceoff changes in OpenFOAM 2.3.x

   OpenFOAM 2.1.x: tutorials/incompressible/simpleFoam/turbineSiting/constant/RASProperties
    
    ```cpp
    kEpsilonCoeffs
    {
        Cmu         0.09;
        C1          1.44;
        C2          1.92;
        C3          -0.33;
        sigmak      1.0;
        sigmaEps    1.11; //Original value:1.44
        Prt         1.0;
    }
    ```
    
    kEpsilon model in  OpenFOAM 2.3.x
    
    ```cpp
    //NOTE: See "On the use of the k-Epsilon model in commercial CFD software
    // to model the neutral atmospheric boundary layer". J. of wind engineering
    // and inductrial aerodymanics 95(2007) 355-269 by D.M. Hargreaves and N.G. Wright
   
```

### heat transfer boundary condition
=====================================

https://github.com/OpenFOAM/OpenFOAM-2.3.x/blob/master/src/turbulenceModels/incompressible/turbulenceModel/derivedFvPatchFields/turbulentHeatFluxTemperature/turbulentHeatFluxTemperatureFvPatchScalarField.C


https://github.com/OpenFOAM/OpenFOAM-2.3.x/blob/master/src/turbulenceModels/compressible/turbulenceModel/derivedFvPatchFields/turbulentHeatFluxTemperature/turbulentHeatFluxTemperatureFvPatchScalarField.C

https://github.com/OpenFOAM/OpenFOAM-4.x/tree/master/src/TurbulenceModels/compressible/turbulentFluidThermoModels/derivedFvPatchFields

https://github.com/OpenFOAM/OpenFOAM-4.x/blob/master/src/TurbulenceModels/compressible/turbulentFluidThermoModels/derivedFvPatchFields/convectiveHeatTransfer/convectiveHeatTransferFvPatchScalarField.H



    
### wall functions for rough lowRe 

=================================
  - epsilonWallFunction  
 	This boundary condition provides a turbulence dissipation wall function condition for high Reynolds number, turbulent flow cases. More...

  - nutkWallFunction  
 	This boundary condition provides a turbulent kinematic viscosity condition when using wall functions, based on turbulence kinetic energy. More...
  
 - nutWallFunction  
 	This boundary condition provides a turbulent kinematic viscosity condition when using wall functions, based on turbulence kinetic energy. More...
 
 - omegaWallFunction  
 	This boundary condition provides a wall function constraint on turbulnce specific dissipation, omega. The values are computed using: More...
==================================
    
 - epsilonLowReWallFunction  
 	This boundary condition provides a turbulence dissipation wall function condition for low- and high-Reynolds number turbulent flow cases. More...
  
 - fWallFunction  
 	This boundary condition provides a turbulence damping function, f, wall function condition for low- and high Reynolds number, turbulent flow cases. More...
 
 - v2WallFunction  
 	This boundary condition provides a turbulence stress normal to streamlines wall function condition for low- and high-Reynolds number, turbulent flow cases. More...
 
 - nutLowReWallFunction  
 	This boundary condition provides a turbulent kinematic viscosity condition for use with low Reynolds number models. It sets nut to zero, and provides an access function to calculate y+. More...

 - kLowReWallFunction  
 	This boundary condition provides a turbulence kinetic energy wall function condition for low- and high-Reynolds number turbulent flow cases. More...
 
 - kqRWallFunctionFvPatchField< Type >
 	This boundary condition provides a suitable condition for turbulence k, q, and R fields for the case of high Reynolds number flow using wall functions. More...
 
 - nutkAtmRoughWallFunction  
 	This boundary condition provides a turbulent kinematic viscosity for atmospheric velocity profiles. It is desinged to be used in conjunction with the atmBoundaryLayerInletVelocity boundary condition. The values are calculated using: More...
 
 - nutkRoughWallFunction  
 	This boundary condition provides a turbulent kinematic viscosity condition when using wall functions for rough walls, based on turbulence kinetic energy. The condition manipulates the E parameter to account for roughness effects. More...
 ===========================
 - nutURoughWallFunction  
 	This boundary condition provides a turbulent kinematic viscosity condition when using wall functions for rough walls, based on velocity. More...
 
 - nutUSpaldingWallFunction  
 	This boundary condition provides a turbulent kinematic viscosity condition when using wall functions for rough walls, based on velocity, using Spalding's law to give a continuous nut profile to the wall (y+ = 0) More...
 
 - nutUTabulatedWallFunction  
 	This boundary condition provides a turbulent kinematic viscosity condition when using wall functions. As input, the user specifies a look-up table of U+ as a function of near-wall Reynolds number. The table should be located in the $FOAM_CASE/constant directory. More...
 
 - nutUWallFunction  
 	This boundary condition provides a turbulent kinematic viscosity condition when using wall functions, based on velocity. More...
 

### compressible case setup


/opt/openfoam4/tutorials/heatTransfer/buoyantSimpleFoam/buoyantCavity/0

**alphat**
```
dimensions      [ 1 -1 -1 0 0 0 0 ];

internalField   uniform 0;

boundaryField
{
    walls
    {
        type            compressible::alphatWallFunction;
        value           uniform 0;
    }
    inlet
    {
        type            calculated;
        value           uniform 0;
}
```
for heat transfer, one extra variable: **p_rgh**
```
dimensions      [1 -1 -2 0 0 0 0];

internalField   uniform 1e5;

boundaryField
{
    frontAndBack
    {
        type            fixedFluxPressure;
        value           uniform 1e5;
    }

    topAndBottom
    {
        type            fixedFluxPressure;
        value           uniform 1e5;
    }

    hot
    {
        type            fixedFluxPressure;
        value           uniform 1e5;
    }

    cold
    {
        type            fixedFluxPressure;
        value           uniform 1e5;
    }
}
```
    
### radiation model

Fluent  radiatoin models:

- Discrete Ordinates Model (DOM)
- Discrete Transfer Radiation Model (DTRM)
- P-1 Radiation Model
- Rosseland Model
- Surface-to-Surface (S2S)

OpenFOAM: 'noRadiation', 'P1' , 'viewFactor'

example *radiatonProperties* in tutorials:
/opt/openfoam30/tutorials/heatTransfer/buoyantSimpleFoam/hotRadiationRoom/constant
/opt/openfoam30/tutorials/heatTransfer/buoyantSimpleFoam/hotRadiationRoomfvDOM/constant

```
radiation on;

radiationModel  P1;

// Number of flow iterations per radiation iteration
solverFreq 1;

absorptionEmissionModel constantAbsorptionEmission;

constantAbsorptionEmissionCoeffs
{
    absorptivity    absorptivity    [0 -1 0 0 0 0 0] 0.5;
    emissivity      emissivity      [0 -1 0 0 0 0 0] 0.5;
    E               E               [1 -1 -3 0 0 0 0] 0;
}

scatterModel    none;

sootModel       none;
```

```
radiation on;

radiationModel  fvDOM;

fvDOMCoeffs
{
    nPhi        3;          // azimuthal angles in PI/2 on X-Y.(from Y to X)
    nTheta      5;          // polar angles in PI (from Z to X-Y plane)
    convergence 1e-3;   // convergence criteria for radiation iteration
    maxIter     10;         // maximum number of iterations
    cacheDiv    false;
}

// Number of flow iterations per radiation iteration
solverFreq 10;

absorptionEmissionModel constantAbsorptionEmission;

constantAbsorptionEmissionCoeffs
{
   absorptivity    absorptivity    [ m^-1 ]         0.5;
   emissivity      emissivity      [ m^-1 ]         0.5;
   E               E               [ kg m^-1 s^-3 ] 0;
}

scatterModel    none;

sootModel       none;
```

### Conbustion model

OpenFOAM: supported_conbustion_models = set(['noConbustion', 'engine', 'fire', 'PDR', 'reacting', 'Xi'])

"""
[/opt/openfoam30/tutorials/combustion/engineFoam/kivaTest/constant/conbustionProperties]
[/opt/openfoam30/tutorials/combustion/engineFoam/kivaTest/constant/thermophysicalProperties]
"""
def setConbustionProperties(case, conbustionModel):
    pass
    
    
### coupled : conjugagte heat transfer

"coupled"  interfaceType
