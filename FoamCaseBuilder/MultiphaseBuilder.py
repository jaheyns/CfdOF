#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2016 - Qingfeng Xia <qingfeng.xia()eng.ox.ac.uk> *
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   This program is distributed in the hope that it will be useful,       *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Library General Public License for more details.                  *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with this program; if not, write to the Free Software   *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************




"""
MultiphaseBuilder: 
naming of dict file: fieldname.phasename, like 'U.air' except for pressure field
`EularFoam` implies "compressible", while `iterFoam` suggests incompressible
sovler program name without the ending "Foam", `Lagrangian`, `Multiphase`

Lagrangian: kinematicCloudProperties  kinematicCloudPositions
"""

def _listPhases(case):
    pass

_Eular_multiphase_models = set(['singlePhase', 'twoLiquidMixing', 'twoPhaseEuler', 'multiphaseImmiscible'])
_Lagrangian_multiphase_models = set(['DPM', 'spray']) # there is a continuous phase: phasec
supported_multiphase_models = _Eular_multiphase_models + _Langarange_multiphase_models

def getDefaultMultiphaseSolverSettings():
    pass

def _getMultiphaseSolver(settings):
    if multiphaseModel in settigns and settings['multiphaseModel'] != "":
        if settings['multiphaseModel'] in _Eular_multiphase_models:
            if settings['compressible']:
                if settings['multiphaseModel'] in set([]):
                    return settings['multiphaseModel'] + "Foam"
                elif settings['multiphaseModel'] in set([]):
                    return settings['multiphaseModel'] + "Foam"
                else:
                    raise Exception("You should not get here")
            else:
                if settings['multiphaseModel'] in set([]):
                    return settings['multiphaseModel'] + "Foam"
                elif settings['multiphaseModel'] in set([]):
                    return settings['multiphaseModel'] + "Foam"
                else:
                    raise Exception("You should not get here")
        else: # Langarange models
            return settings['multiphaseModel'] + "Foam"
    else:
        raise Exception("") 

class MultiphaseBuilder(ThermalBuilder):
    """ support both compressible flow and heat transferring
    """
    def __init__(self,  casePath, 
                        solverSettings=getDefaultMultiphaseSolverSettings(),
                        templatePath="tutorials/heatTransfer/buoyantBoussinesqSimpleFoam/hotRoom/",
                        fluidProperties = {'name':'air', "compressible":False, 'kinematicViscosity':1e5},
                        turbulenceProperties = {'name':'kEpsilon'},
                        boundarySettings = [],
                        internalFields = {},
                        paralleSettings = {'method':"simple", "numberOfSubdomains":multiprocessing.cpu_count()},
                        transientSettings = {"startTime":0.0, "endTime":1.0, "timeStep":0.001, "writeInterval":100}
                ):
        """ 
        """
        super(MultiphaseBuilder, self).__init__(casePath, 
                        solverSettings,
                        templatePath,
                        fluidProperties,
                        turbulenceProperties,
                        boundarySettings,
                        internalFields,
                        paralleSettings,
                        transientSettings,
                        )
        self._solverName = getMultiphaseSolver(self._solverSettings)
        self._solverCreatedVariables = self.getSolverCreatedVariables()
    
    def build(self):
        pass

    def getSolverName(self):
        return _getMultiphaseSolver(self._solverSettings)
    
    def getFoamTemplate(self):
        raise
        
    def setupFluidProperties(self, value=None):
        if value and isinstance(value, dict):
            self.fluidProperties = value
        if self._solverSettings['compressible']:
            self.setupThermophysicalProperties()
        else:
            self.setupTransportProperties()
        
    def setInternalFields(self):
        pass
    
    def getPhases(self):
        pass

    def getSolverCreatedVariables(self):
        pass
         
    
    
    
    
    
    
    
    
'''
# cat constant/transportProperties

phases ( water air );

water
{
	transportModel  Newtonian;
	nu              nu [ 0 2 -1 0 0 0 0 ] 1e-06;
	rho             rho [ 1 -3 0 0 0 0 0 ] 1000;
}

air
{
	transportModel  Newtonian;
	nu              nu [ 0 2 -1 0 0 0 0 ] 1.48e-05;
	rho             rho [ 1 -3 0 0 0 0 0 ] 1;
}

sigma           sigma [ 1 0 -2 0 0 0 0 ] 0;
'''