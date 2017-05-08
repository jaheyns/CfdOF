# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2016 - Qingfeng Xia <qingfeng.xia iesensor.com>         *
# *   Copyright (c) 2017 - Johan Heyns (CSIR) <jheyns@csir.co.za>           *
# *   Copyright (c) 2017 - Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>        *
# *   Copyright (c) 2017 - Alfred Bogaers (CSIR) <abogaers@csir.co.za>      *
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
from utility import *
import subprocess
import platform
import TemplateBuilder
_debug = True


class BasicBuilder(object):
    """ This class to construct the OpenFOAM file structure. """
    def __init__(self,
                 casePath,
                 installationPath,
                 settings,
                 solverSettings,
                 physicsModel,
                 initialConditions,
                 templatePath,
                 solverName=None,
                 fluidProperties={},
                 boundarySettings=[],
                 internalFields={},
                 porousZoneSettings=[]):

        if casePath[0] == "~":
            casePath = os.path.expanduser(casePath)
        self._casePath = os.path.abspath(casePath)
        self._installationPath = installationPath
        self._settings = settings
        self._solverSettings = solverSettings
        self._physicsModel = physicsModel
        self._initialConditions = initialConditions
        self._solverName = solverName
        self._templatePath = templatePath
        self._solverCreatedVariables = self.getSolverCreatedVariables()
        self._fluidProperties = fluidProperties
        self._boundarySettings = boundarySettings
        self._internalFields = internalFields
        self._porousZoneSettings = porousZoneSettings
        self._edit_process = None

    def setInstallationPath(self):
        setFoamDir(self._installationPath)

    def createCase(self):
        """ Remove existing folder and create a new folder. """
        createCaseFromTemplate(self._casePath, os.path.join(self._templatePath, self._solverName))
        TemplateBuilder.TemplateBuilder(self._casePath, self._templatePath, self._settings)

    def pre_build_check(self):
        """ Run pre-build checks. """
        print("Run pre-build check.")
        if self._solverSettings['parallel']:
            if self._solverSettings['parallelCores'] < 2:
                self._solverSettings['parallelCores'] = 2

    def build(self):
        # Should be repeated on rebuild after settings change
        self.updateTemplateControlDict()  # Updates the solver time step controls
        self.modifySolutionResidualTolerance()  # Updates the solver convergence tolerance for p and U fields.
        createRunScript(self._casePath, self._templatePath,
                        self._initialConditions["PotentialFoam"],
                        self._solverSettings['parallel'],
                        self._solverName,
                        self._solverSettings['parallelCores'],
                        self._porousZoneSettings,
                        self.bafflesPresent())

        self.setupFluidProperties()
        self.setupTurbulenceProperties()

        if len(self._porousZoneSettings) > 0:
            self.setupTopoSetDict()
            self.setupFVOptions()
        if self.bafflesPresent():
            self.setupCreateBafflesDict()

        if self._solverSettings['parallel']:
            self.setupParallelSettings()

        # Move mesh files, after being edited, to polyMesh.org
        movePolyMesh(self._casePath)

    def setupMesh(self, updated_mesh_path, scale):
        if os.path.exists(updated_mesh_path):
            convertMesh(self._casePath, updated_mesh_path, scale)

    def post_build_check(self):
        """ Run post-build checks. """
        print ("Run post-build check.")
        case = self._casePath
        # NOTE: Code depreciated (JH) 06/02/2017
        # if self._solverSettings['dynamicMeshing']:
        #     if not os.path.exists(case + os.path.sep + 'constant/dynamicMeshDict'):
        #         return "Error: 'constant/dynamicMeshDict' is not existent while dynamcMeshing opiton is selected"
        #     if not os.path.exists(case + os.path.sep + '0/pointDisplacement'):
        #         return "Error: '0/pointDisplacement' is not existent while dynamcMeshing opiton is selected"
        if self._solverSettings['parallel']:
            if not os.path.exists(case + os.path.sep + 'constant/decomposeParDict'):
                return "Warning: File 'constant/decomposeParDict' is not available for parallel analysis."
        # NOTE: Code depreciated (JH) 06/02/2017
        # if self._solverSettings['buoyant']:
        #     if not os.path.exists(case + os.path.sep + 'constant/g'):
        #         return "Error: 'constant/g' is not existent while buoyant opiton is selected"
        # paired boundary check: cyclic, porous, etc

    # NOTE: Code depreciated (JH) 06/02/2017
    # def summarize(self):
    #     """ Provide a summary the case setup. """
    #     print("================= case summary ==================\n")
    #     print("Solver name: {}".format(self._solverName))
    #     print("Solver template: {}".format(self._templatePath))
    #     print("Solver case path: {}".format(self._casePath))
    #     self._summarizeInternalFields()
    #     print("Defined mesh boundary names: {}".format(listBoundaryNames(self._casePath)))
    #     print("Boundary conditions setup:")
    #     for bc in self._boundarySettings:
    #         print(bc)
    #     if self._solverSettings['transient']:
    #         print("Transient settings:")
    #         print(self._timeStepSettings) # Get for solverSet
    #     # cmdline = self.getSolverCmd()
    #     # foamJob <solver> & foamLog
    #     print("Please run the command in new terminal: \n" + cmdline)
    #
    # NOTE: Code depreciated (JH) 06/02/2017
    # def _summarizeInternalFields(self):
    #     print("Solver created fields are initialized with value:\n")
    #     for var in self._solverCreatedVariables:
    #         f = ParsedParameterFile(self._casePath + os.path.sep + "0" + os.path.sep + var)
    #         print("    {}:      {}".format(var, f['internalField']))
    #

    def editCase(self):
        """ Open case folder externally in file browser. """
        path = self._casePath
        if platform.system() == 'MacOS':
            self._edit_process = subprocess.Popen(['open', '--', path])
        elif platform.system() == 'Linux':
            self._edit_process = subprocess.Popen(['xdg-open', path])
        elif platform.system() == 'Windows':
            self._edit_process = subprocess.Popen(['explorer', path])

    # NOTE: Update code when VTK is revived (JH)
    # def exportResult(self):
    #     """  Export to VTK format (ascii or binary format) and allow user to directly view results in FC. """
    #     if self._solverSettings['parallel']:
    #         runFoamApplication(['reconstructPar'],  self._casePath)
    #     if os.path.exists(self._casePath + os.path.sep + "VTK"):
    #         shutil.rmtree(self._casePath + os.path.sep + "VTK")
    #     # pointSetName = 'wholeDomain'
    #     # createRawFoamFile(self._casePath, 'system', 'topoSetDict',
    #     #                   getTopoSetDictTemplate(pointSetName, 'pointSet', boundingBox))
    #     # runFoamCommand(['topoSet', '-case', self._casePath, '-latestTime'])
    #     # runFoamCommand(['foamToVTK', '-case', self._casePath, '-latestTime', '-pointSet', pointSetName])
    #     runFoamApplication(['foamToVTK', '-latestTime'], self._casePath)
    #     # search for *.vtk
    #     import glob
    #     vtk_files = glob.glob(self._casePath + os.path.sep + "VTK" + os.path.sep + "*.vtk")
    #     if len(vtk_files) >= 1:
    #         print("only one file name with full path is expected for the result vtk file")
    #         return vtk_files[-1]

    def createParaviewScript(self, module_path):
        """ Create python script for Paraview. """
        fname = os.path.join(self._casePath, "pvScript.py")
        if self._solverSettings['parallel']:
            case_type = "Decomposed Case"
        else:
            case_type = "Reconstructed Case"

        script_head = os.path.join(module_path, "data/defaults/paraview/pvScriptHead.py")
        script_tail = os.path.join(module_path, "data/defaults/paraview/pvScriptTail.py")

        if os.path.exists(fname):
            print("Warning: Overwrite existing pvScript.py script")
        with open(fname, 'w+') as f:  # Delete existing content or create new

            # Insert script head
            with open(script_head, "rb") as infile:
                f.write(infile.read())
            f.write("\n# create a new OpenFOAMReader\n")
            f.write("pfoam = OpenFOAMReader(FileName=r'{}')\n".format(os.path.join(self._casePath, "p.foam")))
            f.write("pfoam.CaseType = '{}'\n\n".format(case_type))

            # Insert script tail
            with open(script_tail, "rb") as infile:
                f.write(infile.read())

            if not os.path.exists(os.path.join(self._casePath, "p.foam")):
                f = open(os.path.join(self._casePath, "p.foam"), 'w')  # mknod not available on Windows
                f.close()

            return fname

    # Solver settings: Update time step and convergence controls

    def updateTemplateControlDict(self):
        modifyControlDictEntries(self._casePath + os.path.sep + "system" + os.path.sep + "controlDict",
                                 "endTime",
                                 self._solverSettings['endTime'])
        modifyControlDictEntries(self._casePath + os.path.sep + "system" + os.path.sep + "controlDict",
                                 "writeInterval",
                                 self._solverSettings['writeInterval'])
        modifyControlDictEntries(self._casePath + os.path.sep + "system" + os.path.sep + "controlDict",
                                 "deltaT",
                                 self._solverSettings['timeStep'])

    def modifySolutionResidualTolerance(self):
        f = ParsedParameterFile(self._casePath + os.path.sep + "system" + os.path.sep + "fvSolution")
        if "Simple" in self._solverName or "simple" in self._solverName:
            f["SIMPLE"]['residualControl']['p'] = self._solverSettings['convergenceCriteria']
            f["SIMPLE"]['residualControl']['U'] = self._solverSettings['convergenceCriteria']
        elif "Pimple" in self._solverName or "pimple" in self._solverName:
            f["PIMPLE"]['residualControl']['p']['tolerance'] = self._solverSettings['convergenceCriteria']
            f["PIMPLE"]['residualControl']['U']['tolerance'] = self._solverSettings['convergenceCriteria']
        else:
            print("Solver not yet supported")
        f.writeFile()

    def getSolverCreatedVariables(self):
        """ Create a list of the required solver variables. """
        # NOTE: Update code when added turbulence back to the code (JH)
        # vars = ['p', 'U'] + getTurbulenceVariables(self._solverSettings)
        vars = ['p', 'U']
        # NOTE: Code depreciated (JH) 06/02/2017
        # if self._solverSettings['buoyant']:
        #     vars.append("p_rgh")
        # if self._solverSettings['dynamicMeshing']:
        #     vars.append("pointDisplacement") #only 6DoF motion solver needs this variable
        return set(vars)

    @property
    def solverSettings(self):
        return self._solverSettings

    # @property
    # def parallelSettings(self):
    #     return self._parallelSettings

    def setupParallelSettings(self):
        """ Create the parallel dictionary file 'decomposeParDict' """
        f = self._casePath + os.path.sep + 'decomposeParDict'
        createRawFoamFile(self._casePath, 'system', 'decomposeParDict',
                          getDecomposeParDictTemplate(self._solverSettings['parallelCores'], 'scotch'))

    @property
    def fluidProperties(self):
        return self._fluidProperties

    @fluidProperties.setter
    def fluidProperties(self, value):
        if value and isinstance(value, dict):
            self._fluidProperties = value
        else:
            print("set a invalid fluid property, null or not dict")
        if _debug:
            print(self._fluidProperties)

    def setupFluidProperties(self):
        """ Set density and viscosity in transport properties. """
        case = self._casePath
        # solver_settings = self._solverSettings
        # assert solver_settings['compressible'] == False
        assert self._physicsModel['Flow'] == 'Incompressible'

        lines = ['transportModel  Newtonian;\n']
        # NOTE: Code depreciated (JH) 06/02/2017
        # if solver_settings['nonNewtonian']:
        #     print('Warning: nonNewtonian case setup is not implemented, please edit dict file directly')
        # else:

        for k in self._fluidProperties:
            if k in set(['nu', 'kinematicViscosity']):
                viscosity = self._fluidProperties[k]
                lines.append('nu              nu [ 0 2 -1 0 0 0 0 ] {};\n'.format(viscosity))
            elif k in set(['rho', 'density']):
                density = self._fluidProperties[k]
                lines.append('rho              rho [ -3 1 0 0 0 0 0 ] {};\n'.format(density))
            else:
                print("Warning:unrecoginsed fluid properties: {}".format(k))
        if _debug:
            print("Viscosity settings in constant/transportProperties")
            print(lines)

        createRawFoamFile(case, "constant", "transportProperties", lines)

    def bafflesPresent(self):
        for bcDict in self._boundarySettings:
            if bcDict['type'] == 'baffle':
                return True
        return False

    def setupCreateBafflesDict(self):
        fname = os.path.join(self._casePath, "system", "createBafflesDict")
        fid = open(fname, 'w')

        baffles = ""
        for bc in self._boundarySettings:
            if bc['type'] == 'baffle':
                baffles += readTemplate(os.path.join(self._templatePath, "helperFiles", "createBafflesDictBaffle"),
                                        {"NAME": bc['name']})
        fid.write(readTemplate(os.path.join(self._templatePath, "helperFiles", "createBafflesDict"),
                               {"HEADER": readTemplate(os.path.join(self._templatePath, "helperFiles", "header"),
                                                       {"LOCATION": "system",
                                                        "FILENAME": "createBafflesDict"}),
                                "BAFFLES": baffles}))
        fid.close()

    @property
    def porousZoneSettings(self):
        return self._porousZoneSettings

    @porousZoneSettings.setter
    def porousZoneSettings(self, porousZoneSettings=[]):
        if isinstance(porousZoneSettings, list):
            self._porousZoneSettings = porousZoneSettings
        else:
            raise Exception("Porous settings must be a list.")

    def setupTopoSetDict(self):
        porousObject = self._porousZoneSettings
        fname = os.path.join(self._casePath, "system", "topoSetDict")
        fid = open(fname, 'w')

        actions = ""
        for po in porousObject:
            for partName in po['PartNameList']:
                actions += readTemplate(os.path.join(self._templatePath, "helperFiles", "topoSetDictStlToCellZone"),
                                        {"CELLSETNAME": partName+"SelectedCells",
                                         "STLFILE": os.path.join("constant",
                                                                 "triSurface",
                                                                 partName+u"Scaled.stl"),
                                         "CELLZONENAME": partName})

        fid.write(readTemplate(os.path.join(self._templatePath, "helperFiles", "topoSetDict"),
                               {"HEADER": readTemplate(os.path.join(self._templatePath, "helperFiles", "header"),
                                                       {"LOCATION": "system",
                                                        "FILENAME": "topoSetDict"}),
                                "ACTIONS": actions}))
        fid.close()

    def setupCreatePatchDict(self, case_folder, bc_group, mobj):
        print ('Populating createPatchDict to update BC names')
        fname = os.path.join(case_folder, "system", "createPatchDict")
        fid = open(fname, 'w')
        patch = ""

        bc_allocated = []
        for bc_id, bc_obj in enumerate(bc_group):
            bc_list = []
            meshFaceList = mobj.Part.Shape.Faces
            for (i, mf) in enumerate(meshFaceList):
                bcFacesList = bc_obj.Shape.Faces
                for bf in bcFacesList:
                    import FemMeshTools
                    isSameGeo = FemMeshTools.is_same_geometry(bf, mf)
                    if isSameGeo:
                        bc_list.append(mobj.ShapeFaceNames[i])
                        if mobj.ShapeFaceNames[i] in bc_allocated:
                            print ('Error: {} has been assigned twice'.format(mobj.ShapeFaceNames[i]))
                        else:
                            bc_allocated.append(mobj.ShapeFaceNames[i])

            bc_list_str = ""
            for bc in bc_list:
                bc_list_str += " " + bc

            bcDict = bc_obj.BoundarySettings
            bcType = bcDict["BoundaryType"]
            bcSubType = bcDict["BoundarySubtype"]
            patchType = getPatchType(bcType, bcSubType)

            patch += readTemplate(
                os.path.join(self._templatePath, "helperFiles", "createPatchDictPatch"),
                {"LABEL": bc_obj.Label,
                 "TYPE": patchType,
                 "PATCHLIST": bc_list_str})

            if not (len(bc_list) == len(meshFaceList)):
                print('Error: Miss-match between boundary faces and mesh faces')

        # Add default faces
        flagName = False
        bc_list_str = ""
        for name in mobj.ShapeFaceNames:
            if not name in bc_allocated:
                bc_list_str += " " + name
                flagName = True
        if (flagName):
            patch += readTemplate(
                os.path.join(self._templatePath, "helperFiles", "createPatchDictPatch"),
                {"LABEL": 'defaultFaces',
                 "TYPE": 'patch',
                 "PATCHLIST": bc_list_str})

        fid.write(readTemplate(os.path.join(self._templatePath, "helperFiles", "createPatchDict"),
                               {"HEADER": readTemplate(os.path.join(self._templatePath, "helperFiles", "header"),
                                                       {"LOCATION": "system",
                                                        "FILENAME": "createPatchDict"}),
                                "PATCH": patch}))
        fid.close()


    def setupFVOptions(self):
        porousObject = self._porousZoneSettings
        fname = os.path.join(self._casePath, "constant", "fvOptions")
        fid = open(fname, 'w')

        sources = ""
        for po in porousObject:
            for partName in po['PartNameList']:
                sources += readTemplate(os.path.join(self._templatePath, "helperFiles", "fvOptionsPorousZone"),
                                        {"SOURCENAME": partName,
                                         "DX": str(po['D'][0]),
                                         "DY": str(po['D'][1]),
                                         "DZ": str(po['D'][2]),
                                         "FX": str(po['F'][0]),
                                         "FY": str(po['F'][1]),
                                         "FZ": str(po['F'][2]),
                                         "E1X": str(po['e1'][0]),
                                         "E1Y": str(po['e1'][1]),
                                         "E1Z": str(po['e1'][2]),
                                         "E3X": str(po['e3'][0]),
                                         "E3Y": str(po['e3'][1]),
                                         "E3Z": str(po['e3'][2]),
                                         "CELLZONENAME": partName})

        fid.write(readTemplate(os.path.join(self._templatePath, "helperFiles", "fvOptions"),
                               {"HEADER": readTemplate(
                                                       os.path.join(self._templatePath, "helperFiles", "header"),
                                                       {"LOCATION": "constant",
                                                        "FILENAME": "fvOptions"}),
                                "SOURCES": sources}))
        fid.close()

    def setupTurbulenceProperties(self, turbulenceProperties=None):
        """ Populate constant/turbulenceProperties """
        turbulence_type = self._physicsModel['Turbulence']
        turbulence_model_name = self._physicsModel['TurbulenceModel']
        fname = os.path.join(self._casePath, "constant", "turbulenceProperties")
        fid = open(fname, 'w')

        properties = ""
        if turbulence_type == "RANS":
            properties = readTemplate(os.path.join(self._templatePath, "helperFiles", "turbulencePropertiesRAS"),
                                      {"TURBULENCETYPE": turbulence_model_name})
        fid.write(readTemplate(os.path.join(self._templatePath, "helperFiles", "turbulenceProperties"),
                               {"HEADER": readTemplate(os.path.join(self._templatePath, "helperFiles", "header"),
                                                       {"LOCATION": "constant",
                                                        "FILENAME": "turbulenceProperties"}),
                                "TURBULENCETYPE": "RAS" if turbulence_type == "RANS" else "laminar",
                                "TURBULENCEPROPERTIES": properties}))
        fid.close()
