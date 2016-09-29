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

""" templates string could be used to build up case from scratch instead copying settings form existent case
"""


_fvSolution_template = """
solvers
{
  p
  {
    solver GAMG;
    tolerance 1e-06;
    relTol 0.1;
    smoother GaussSeidel;
  }

    U
    {
        solver          smoothSolver;
        smoother        GaussSeidel;
        nSweeps         2;
        tolerance       1e-08;
        relTol          0.1;
    }

  "(k|h|epsilon|omega|f|v2)"
  {
    solver smoothSolver;
    smoother symGaussSeidel;
    tolerance 1e-05;
    relTol 0.1;
  }
    // only for Sparlart Allmaras turbulence model
    nuTilda
    {
        solver          smoothSolver;
        smoother        GaussSeidel;
        nSweeps         2;
        tolerance       1e-08;
        relTol          0.1;
    }
}

// PIMPLE for transient large time step simulation
PIMPLE
{
    nOuterCorrectors 4;
    nCorrectors     1;
    nNonOrthogonalCorrectors 1;
    pRefCell        0;
    pRefValue       0;  
}

SIMPLE
{
  nNonOrthogonalCorrectors 1; // essential for tetragal cells
  consistent yes;
  residualControl
  {
    p 0.01;
    U 0.001;
    "(k|h|epsilon|omega|f|v2)" 0.001;
  }
  pRefValue 0;
  pRefCell 0;
}

relaxationFactors
{
  fields
  {
     p 0.1; // smaller is needed for bad mesh quality
  }

  equations
  {
    U 0.1;
    ".*" 0.2; 	// smaller is more stable but higher is quicker in convergence
  }
}
"""

def getFvSolutionTemplate():
    """https://github.com/OpenFOAM/OpenFOAM-3.0.x/blob/master/tutorials/incompressible/simpleFoam/pipeCyclic/system/fvSolution"""
    return _fvSolution_template

_decomposeParDict_template = """
numberOfSubdomains %d;

method          %s;

simpleCoeffs
{
    n               ($numberOfSubdomains 1 1);
    delta           0.001;
}

//scotch needs not any coeff input

hierarchicalCoeffs
{
    n               (2 2 1);
    delta           0.001;
    order           xyz;
}

manualCoeffs
{
    dataFile        "";
}

distributed     no;

roots           ( );
"""
def getDecomposeParDictTemplate(numberOfSubdomains, method):
    """"""
    return _decomposeParDict_template % (numberOfSubdomains, method)

def getFvSchemesTemplate(transient=True):
    """for steady and transitionsimulation, significantly change from 2.1 to 3.0
    tutorials/incompressible/simpleFoam/pipeCyclic/system/fvSchemes
    transient solver has different scheme, compressible flow also has diff divSchemes
    LES has its own Schemes
    """
    if transient:
        ddtScheme = "Euler"  # for pimpleFoam
    else:
        ddtScheme = "steadyState"
    return """
    ddtSchemes
    {
        default         %s;
    }

    gradSchemes
    {
        default         Gauss linear;
    }

    divSchemes
    {
        default         none;
        div(phi,U)      bounded Gauss limitedLinearV 1;
        div(phi,K)      bounded Gauss upwind;  // thermal
        div(phi,h)      bounded Gauss upwind;  // thermal
        div(phi,e)      Gauss upwind;  // bouyantSimpleFoam, compressible flow
        div(phi,k)      bounded Gauss limitedLinear 1;  // turbulent flow
        div(phi,epsilon) bounded Gauss limitedLinear 1;
        div(phi,omega)      bounded Gauss limitedLinear 1;
        div(R)          Gauss linear;
        div(phi,R)      bounded Gauss limitedLinear 1;
        div(phi,nuTilda)    bounded Gauss limitedLinear 1;
        div(phi,nuTilda) bounded Gauss linearUpwind grad(nuTilda);  // sparlart turbulent model
        div((nuEff*dev2(T(grad(U)))))       Gauss linear;  // incompressible flow
        div(((rho*nuEff)*dev2(T(grad(U)))))     Gauss linear;  // compressible flow, no bounded scheme
    }

    laplacianSchemes
    {
        default         Gauss linear corrected;
    }

    interpolationSchemes
    {
        default         linear;
    }

    snGradSchemes
    {
        default         corrected;
    }
    """%ddtScheme

    
def getControlDictTemplate(app = 'simpleFoam'):
    return  """
    application     {};

    startFrom       latestTime;

    startTime       0;

    stopAt          endTime;

    endTime         1000;

    deltaT          1;

    writeControl    timeStep;

    writeInterval   100;

    purgeWrite      0;

    writeFormat     ascii;

    writePrecision  6;

    writeCompression off;

    timeFormat      general;

    timePrecision   6;

    runTimeModifiable true;

    // adjustTimeStep  yes;

    // maxCo           1;

    // ************************************************************************* //
    """.format(app)
    
    
def getRASTurbulencePropertiesTemplate(RASModel='kEpsilon'):
    """OpenFOAM 3.0 has unified turbulence setup, simulationType = RAS LES  """
    return   """
    simulationType RAS;

    RAS
    {
        RASModel        %s;

        turbulence      on;

        printCoeffs     on;
    }

    // ************************************************************************* //
    """ % RASModel

def getLESTurbulencePropertiesTemplate(LESModel = 'dynamicKEqn'):
    """https://github.com/OpenFOAM/OpenFOAM-3.0.x/blob/master/tutorials/incompressible/pisoFoam/les/pitzDaily/constant/turbulenceProperties
    """
    return   """
    simulationType  LES;

    LES
    {
        LESModel        %s;

        turbulence      on;

        printCoeffs     on;

        delta           cubeRootVol;

        dynamicKEqnCoeffs
        {
            filter simple;
        }

        cubeRootVolCoeffs
        {
            deltaCoeff      1;
        }

        PrandtlCoeffs
        {
            delta           cubeRootVol;
            cubeRootVolCoeffs
            {
                deltaCoeff      1;
            }

            smoothCoeffs
            {
                delta           cubeRootVol;
                cubeRootVolCoeffs
                {
                    deltaCoeff      1;
                }

                maxDeltaRatio   1.1;
            }

            Cdelta          0.158;
        }

        vanDriestCoeffs
        {
            delta           cubeRootVol;
            cubeRootVolCoeffs
            {
                deltaCoeff      1;
            }

            smoothCoeffs
            {
                delta           cubeRootVol;
                cubeRootVolCoeffs
                {
                    deltaCoeff      1;
                }

                maxDeltaRatio   1.1;
            }

            Aplus           26;
            Cdelta          0.158;
        }

        smoothCoeffs
        {
            delta           cubeRootVol;
            cubeRootVolCoeffs
            {
                deltaCoeff      1;
            }

            maxDeltaRatio   1.1;
        }
    }
    """ % LESModel


def getTopoSetDictTemplate(topoSetName, topoSetType, box):
    return """
    actions
    (
      {
        name    %s;
        type    %s;
        action  new;
        source  boxToPoint;
        sourceInfo
        {
          box (%f %f %f) (%f %f %f);
        }
      }
    );
    """%(topoSetName, topoSetType, box[0][0], box[0][1], box[0][2], box[1][0], box[1][1], box[1][2])