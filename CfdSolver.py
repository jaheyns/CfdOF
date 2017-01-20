#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2015 - Qingfeng Xia <qingfeng.xia()eng.ox.ac.uk> *
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

__title__ = "Classes for New CFD solver"
__author__ = "Qingfeng Xia"
__url__ = "http://www.freecadweb.org"

import os.path

supported_physical_domains = ['Mechanical', 'Fluidic', 'Electromagnetic']  # to identify physical domains

from FoamCaseBuilder import supported_turbulence_models
#from FoamCaseBuilder import supported_multiphase_models
supported_multiphase_models = ['singplePhase']
from FoamCaseBuilder import supported_radiation_models

"""
NOTE NOTE NOTE: 20/01/2017 
have commented out many of the properties that used to reside within cfdSolver object.
Many will be temporary removals, or relocated to other objects. 
The primary reasoning is that it becomes confusing to have so many
properties available especially since most of them are not yet functional.
Therefore rather opting for a semi-groun up approach here, by systematically
adding and testing functionality..
TODO: once a final design has been decided upon the properties which are
either no longer needed or moved to other objects should be deleted.
"""



## Fem::FemSolverObject 's Proxy python type for CFD solver
## common CFD properties are defined, solver specific properties in derived class
## given solver's property to runner pyobject instance, recorded script can work without GUI
class CfdSolver(object):
    def __init__(self, obj):
        self.Type = "CfdSolver"
        self.Object = obj  # keep a ref to the DocObj for nonGui usage
        obj.Proxy = self  # link between App::DocumentObject to  this object

        # some properties previously defined in FemSolver C++ object are moved here
        if "SolverName" not in obj.PropertiesList:
            obj.addProperty("App::PropertyString", "SolverName", "Solver",
                            "unique solver name to identify the solver")
            obj.SolverName = "OpenFOAM"
            #obj.addProperty("App::PropertyEnumeration", "PhysicalDomain", "Solver",
                            #"unique solver name to identify the solver")
            obj.addProperty("App::PropertyPath", "InstallationPath", "Solver",
                            "Solver installation path")
            #obj.PhysicalDomain = supported_physical_domains
            #obj.PhysicalDomain = 'Fluidic'
            #obj.addProperty("App::PropertyString", "Module", "Solver",
            #                "python module for case writer")
            obj.addProperty("App::PropertyPath", "WorkingDir", "Solver",
                            "Solver process is run in this directory")
            obj.addProperty("App::PropertyString", "InputCaseName", "Solver",
                            "input file name without suffix or case folder name")
            obj.addProperty("App::PropertyBool", "Parallel", "Solver",
                            "solver is run with muliticore or on cluster")
            obj.addProperty("App::PropertyBool", "ResultObtained", "Solver",
                            "result of analysis has been obtained, i.e. case setup is fine")

            import tempfile
            if os.path.exists('/tmp/'):
                obj.WorkingDir = '/tmp/'  # must exist for POSIX system
            elif tempfile.tempdir:
                obj.WorkingDir = tempfile.tempdir
            else:
                obj.WorkingDir = './'
            obj.InputCaseName = 'case'

        ## API: addProperty(self,type,name='',group='',doc='',attr=0,readonly=False,hidden=False)
        if "TurbulenceModel" not in obj.PropertiesList:
            #obj.addProperty("App::PropertyEnumeration", "TurbulenceModel", "CFD",
                            #"Laminar,KE,KW,LES,etc",True)
            #obj.TurbulenceModel = list(supported_turbulence_models)
            #obj.TurbulenceModel = "laminar"
            #obj.addProperty("App::PropertyEnumeration", "MultiPhaseModel", "CFD",
                            #"Mixing, VoF, DiscreteParticleModel")
            #obj.MultiPhaseModel = list(supported_multiphase_models)
            # DynanicMeshing, MultiPhaseModel, Combustion will not be implemented for model setup complexity
            #obj.addProperty("App::PropertyBool", "DynamicMeshing", "CFD",
                            #"mobile/moving meshing function", True)
            #obj.addProperty("App::PropertyBool", "Compressible", "CFD",
                            #"Compressible air or Incompressible like liquid, including temperature field", True)
            #obj.addProperty("App::PropertyBool", "transonic", "CFD",
                            #"to support supersonic compressible flow which has specail boundary condition", True)
            #obj.addProperty("App::PropertyBool", "Porous", "CFD",
                            #"Porous material model enabled or not", True)
            #obj.addProperty("App::PropertyBool", "NonNewtonian", "CFD",
                            #"fluid property, strain-rate and stress constition, water and air are Newtonion", True)
            #obj.addProperty("App::PropertyVector", "Gravity", "CFD",
                            #"gravity and other body accel")
            #obj.addProperty("App::PropertyBool", "Buoyant", "HeatTransfer",
                            #"gravity induced flow, needed by compressible heat transfering analysis")
            # heat transfer group, conjudate and radition is not activated yet
            #obj.addProperty("App::PropertyBool", "HeatTransfering", "HeatTransfer",
                            #"calc temperature field, needed by compressible flow")
            #obj.addProperty("App::PropertyEnumeration", "RadiationModel", "HeatTransfer",
                            #"radiation heat transfer model", True)
            #obj.RadiationModel = list(supported_radiation_models)
            #obj.addProperty("App::PropertyBool", "Conjugate", "HeatTransfer",
                            #"MultiRegion fluid and solid conjugate heat transfering analysis", True)

            # Transient solver related: CurrentTime TimeStep StartTime, StopTime, not activated yet!
            """ 
            NOTE: removed the True from these variables to allow them to be modified in the GUI data tab
            Please note that it is possible to create negative values. 
            Once a proper settings .ui has been created this should be fixed, else the user may enter 
            negative numbers for time step, start time, end time etc
            """
            #obj.addProperty("App::PropertyBool", "Transient", "Transient",
                            #"Static or transient analysis", True)
            obj.addProperty("App::PropertyFloat", "StartTime", "TimeStepControl",
                            "Time settings for transient analysis")
            obj.addProperty("App::PropertyFloat", "EndTime", "TimeStepControl",
                            "Time settings for transient analysis")
            obj.addProperty("App::PropertyFloat", "TimeStep", "TimeStepControl",
                            "Time step (second) for transient analysis")
            obj.addProperty("App::PropertyFloat", "WriteInterval", "TimeStepControl",
                            "WriteInterval (second) for transient analysis")

        """Setting initial default values here for transient settings.
        Unlike the intitial build, where time properties were only added
        in the event that the problem was transient, it is beneficial to be able
        to speficy some of this information for steady state problems as well
        """
        obj.EndTime = 1000
        obj.TimeStep = 1
        obj.WriteInterval = 100
    

    ############ standard FeutureT methods ##########
    def execute(self, obj):
        """"this method is executed on object creation and whenever the document is recomputed"
        update Part or Mesh should NOT lead to recompution of the analysis automatically, time consuming
        """
        return

    def onChanged(self, obj, prop):
        return

    def __getstate__(self):
        return self.Type

    def __setstate__(self, state):
        if state:
            self.Type = state
