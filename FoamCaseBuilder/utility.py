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
utitly functions to setup OpenFOAM case, turbulence model, detect solver name
intended to use internally
"""

from __future__ import print_function

import numbers
import os, os.path, shutil
import multiprocessing
import subprocess

_using_pyfoam = True
if _using_pyfoam:
    from PyFoam.RunDictionary.ParsedParameterFile import ParsedParameterFile
    from PyFoam.RunDictionary.BoundaryDict import BoundaryDict
    from PyFoam.Applications.PlotRunner import PlotRunner
    #from PyFoam.FoamInformation import foamVersionString, foamVersionNumber
    from PyFoam.ThirdParty.six import string_types, iteritems
    #import PyFoam.Error, etc
else:
    # implement our own class: ParsedParameterFile, getDict, setDict
    from six import string_types, iteritems

from FoamTemplateString import *

_debug = True
# ubuntu 14.04 defaullt to 3.x, while ubuntu 16.04 default to 4.x
#DEFAULT_FOAM_DIR = '/opt/openfoam30'
#DEFAULT_FOAM_VERSION = (3,0,0)
_DEFAULT_FOAM_DIR = '/opt/openfoam4'
_DEFAULT_FOAM_VERSION = (4,0,0)


def _detectFoamDir():
    # compatible for python3, check_output() return bytes type in python3
    foam_dir = subprocess.check_output(['bash', '-i', '-c', 'echo $WM_PROJECT_DIR'], stderr=subprocess.PIPE)
    foam_dir = str(foam_dir)
    if len(foam_dir)>1:  # if env var is not defined, return `b'\n'` for python3 and `\n` for python2
        if foam_dir[:2] == "b'":  # for python 3
            foam_dir = foam_dir[2:-3] #strip 2 chars from front and tail `b'/opt/openfoam4\n'`
        else:
            foam_dir= foam_dir.strip()  # strip the EOL char
        return foam_dir
    else:
        print("""Environment var 'WM_PROJECT_DIR' is not defined nor FOAM_DIR is set
                 fallback to default {}""".format(_DEFAULT_FOAM_DIR))
        return _DEFAULT_FOAM_DIR

def _detectFoamVersion():
    foam_ver = subprocess.check_output(['bash', '-i', '-c', 'echo $WM_PROJECT_VERSION'], stderr=subprocess.PIPE)
    # there is warning for `-i` interative mode, but output is fine
    foam_ver = str(foam_ver)  # compatible for python3, check_output() return bytes type in python3
    if len(foam_ver)>1:
        if foam_ver[:2] == "b'":  # for python 3
            foam_ver = foam_ver[2:-3] #strip 2 chars from front and tail `b'4.0\n'`
        else:
            foam_ver = foam_ver.strip()  # strip the EOL char
        return tuple([int(s) for s in foam_ver.split('.')])
    else:
        print("""environment var 'WM_PROJECT_VERSION' is not defined\n,
              fallback to default {}""".format(_DEFAULT_FOAM_VERSION))
        return _DEFAULT_FOAM_VERSION

_FOAM_SETTINGS = {"FOAM_DIR": _detectFoamDir(), "FOAM_VERSION": _detectFoamVersion()}


# public API getter and setter for FOAM_SETTINGS
def setFoamDir(dir):
    if os.path.exists(dir) and os.path.isabs(dir):
        if os.path.exists(dir + os.path.sep + "etc/bashrc"):
            _FOAM_SETTINGS['FOAM_DIR'] = dir
    else:
        print("Warning: {} is not an existent folder to set as foam_dir".format(dir))

def setFoamVersion(ver):
    """specify OpenFOAM version by a list or tupe of integer like (3, 0, 0)
    """
    _FOAM_SETTINGS['FOAM_VERSION'] = tuple(ver)
        
def getFoamDir():
    """detect from output of 'bash -i -c "echo $WM_PROJECT_DIR"', if default is not set
    """
    if 'FOAM_DIR' in _FOAM_SETTINGS:
        return _FOAM_SETTINGS['FOAM_DIR']

def getFoamVersion():
    """ detect version from output of 'bash -i -c "echo $WM_PROJECT_VERSION"' if default is not set
    """
    if 'FOAM_VERSION' in _FOAM_SETTINGS:
        return _FOAM_SETTINGS['FOAM_VERSION']

# see more details on variants: https://openfoamwiki.net/index.php/Forks_and_Variants
# http://www.cfdsupport.com/install-openfoam-for-windows.html, using cygwin
#FOAM_VARIANTS = ['OpenFOAM', 'foam-extend', 'OpenFOAM+']
#FOAM_RUNTIMES = ['FreeFOAM', 'Cygwin', 'BashWSL']
def _detectFoamVarient():
    """ FOAM_EXT version is also detected from 'bash -i -c "echo $WM_PROJECT_VERSION"'  or $WM_FORK
    """
    if getFoamDir().find('ext') > 0:
        return  "foam-extend"
    else:
       return "OpenFOAM"

# Bash on Ubuntu on Windows detection and path translation
def _detectFoamRuntime():
    return ""
    #return "BashWSL"

_FOAM_SETTINGS['FOAM_VARIANT'] = _detectFoamVarient()
_FOAM_SETTINGS['FOAM_RUNTIME'] = _detectFoamRuntime()
def getFoamVariant():
    """detect from output of 'bash -i -c "echo $WM_PROJECT_DIR"', if default is not set
    """
    if 'FOAM_VARIANT' in _FOAM_SETTINGS:
        return _FOAM_SETTINGS['FOAM_VARIANT']

def isFoamExt():
    return _FOAM_SETTINGS['FOAM_VARIANT'] == "foam-extend"

def getFoamRuntime():
    """detect from output of 'bash -i -c "echo $WM_PROJECT_DIR"', if default is not set
    """
    if 'FOAM_RUNTIME' in _FOAM_SETTINGS:
        return _FOAM_SETTINGS['FOAM_RUNTIME']
        
######################################################################
"""
turbulence models supporting both compressible and incompressible are listed here
DES is grouped into LES_models
# http://cfd.direct/openfoam/features/les-des-turbulence-modelling/
# v2f of the kEpsilon group has its own variables and wallfunction is not implemented
# kOmegaSSTSAS -> kOmegaSST (a common name)
kOmega: tutorials/incompressible/SRFSimpleFoam/mixer/constant/turbulenceProperties
only kEpsilon group lowRe_models is implemented, yet tested
"qZeta" has its own variables and wallfunction will not be implemented
"LRR": not implemented
"""

kEpsilon_models = set(["kEpsilon", "RNGkEpsilon", "realizableKE", "LaunderSharmaKE"])
lowRe_models = set(["LaunderSharmaKE", "LienCubicKE",])
kOmega_models = set(["kOmega", "kOmegaSST"])
spalartAllmaras_models = set(["SpalartAllmaras"])
RAS_turbulence_models =  spalartAllmaras_models | kEpsilon_models | kOmega_models | lowRe_models
# OpenFOAM 4.0 LES and DES models
LES_turbulence_models = set([
"DeardorffDiffStress", #    Differential SGS Stress Equation Model for incompressible and compressible flows.
"Smagorinsky", #    The Smagorinsky SGS model.
"SpalartAllmarasDDES", #    SpalartAllmaras DDES turbulence model for incompressible and compressible flows.
"SpalartAllmarasDES", #    SpalartAllmarasDES DES turbulence model for incompressible and compressible flows.
"SpalartAllmarasIDDES", #    SpalartAllmaras IDDES turbulence model for incompressible and compressible flows.
"WALE", #    The Wall-adapting local eddy-viscosity (WALE) SGS model.
"dynamicKEqn", #    Dynamic one equation eddy-viscosity model.
"dynamicLagrangian", #    Dynamic SGS model with Lagrangian averaging.
"kEqn", #    One equation eddy-viscosity model.
"kOmegaSSTDES", #    Implementation of the k-omega-SST-DES turbulence model for incompressible and compressible flows. 
])
supported_turbulence_models = set(['laminar', 'DNS', 'invisid']) | RAS_turbulence_models

_LES_turbulenceModel_templates = {
                     'kOmegaSSTDES': "tutorials/incompressible/pisoFoam/les/pitzDaily/",
                     "SpalartAllmarasDES": "", 
                     "Smagorinsky": "", 
                     "kEqn":"tutorials/incompressible/pisoFoam/les/pitzDailyMapped",
                     "WALE":"",
                     "SpalartAllmarasIDDES": ""
}

def getTurbulentViscosityVariable(solverSettings):
    # OpenFOAM versions after v3.0.0+ is always `nut`
    turbulenceModelName = solverSettings['turbulenceModel']
    if turbulenceModelName in LES_turbulence_models:
        if getFoamVersion()[0] < 3 or isFoamExt():
            return 'muSgs'
        else:
            return 'nuSgs'
    if solverSettings['compressible']:
        if getFoamVersion()[0] < 3 or isFoamExt():
            return 'mut'
        else:
            return 'nut'
    else:
        return 'nut'

def getTurbulenceVariables(solverSettings):
    turbulenceModelName = solverSettings['turbulenceModel']
    viscosity_var = getTurbulentViscosityVariable(solverSettings)
    if turbulenceModelName in ["laminar", "invisid", 'DNS'] :  # no need to generate dict file
        var_list = []  # otherwise, generated from filename in folder case/0/, 
    elif turbulenceModelName in kEpsilon_models:
        var_list = ['k', 'epsilon', viscosity_var]
    elif turbulenceModelName in kOmege_models:
        var_list = ['k', 'omega', viscosity_var]
    elif turbulenceModelName in spalartAllmaras_models:
        var_list = [viscosity_var, 'nuTilda'] # incompressible/simpleFoam/airFoil2D/
    #elif turbulenceModelName in LES_models:
    #    var_list = ['k', viscosity_var, 'nuTilda']
    #elif turbulenceModelName == "qZeta":  # transient models has different var
    #    var_list = []  # not supported yet in boundary settings
    else:
        print("Turbulence model {} is not supported yet".format(turbulenceModelName))
    return var_list


#################################################################################

""" access dict as property of class
class PropDict(dict):
    def __init__(self, *args, **kwargs):
        super(PropDict, self).__init__(*args, **kwargs)
        #first letter lowercase conversion by mapping: 
        f = lambda s : s[0].lower() + s[1:]
        d = {f(k):v for k,v in self.iteritems()}
        self.__dict__ = d  # self
"""


def createCaseFromTemplate(output_path, source_path, backup_path=None):
    """create case from zipped template or existent case folder relative to $WM_PROJECT_DIR
    foamCloneCase  foamCopySettings, foamCleanCase
    clear the mesh, result and boundary setup, but keep the dict under system/ constant/ 
    <solver_name>Template_v3.zip: case folder structure without mesh and initialisation of boundary in folder case/0/
    registered dict  from solver name: tutorials/incompressible/icoFoam/elbow/
    """
    if backup_path and os.path.isdir(output_path):
        shutil.move(output_path, backup_path)
    if os.path.isdir(output_path):
        shutil.rmtree(output_path)
    os.makedirs(output_path) # mkdir -p

    if source_path.find("tutorials")>=0:
        if not os.path.isabs(source_path):  # create case from existent case folder
            source_path = getFoamDir() + os.path.sep + source_path
        if os.path.exists(source_path):
            copySettingsFromExistentCase(output_path, source_path)
        else:
            raise Exception("Error: tutorial case folder: {} not found".format(source_path))
    elif source_path[-4:] == ".zip":  # zipped case template,outdated
        template_path = source_path
        if os.path.isfile(template_path):
            import zipfile
            with zipfile.ZipFile(source_path, "r") as z:
                z.extractall(output_path)  #auto replace existent case setup without warning
        else:
            raise Exception("Error: template case file {} not found".format(source_path))
    else:
        raise Exception('Error: template {} is not a tutorials case path or zipped file'.format(source_path))
    #foamCleanPolyMesh
    mesh_dir = os.path.join(output_path, "constant", "polyMesh")
    if os.path.isdir(mesh_dir):
        shutil.rmtree(mesh_dir)
    #clean history result data, etc. is not necessary as they are excluded from zipped template
    if os.path.isfile(output_path + os.path.sep +"system/blockMeshDict"):
        os.remove(output_path + os.path.sep +"system/blockMeshDict")
    #remove the functions section at the end of ControlDict
    """
    f = ParsedParameterFile(output_path + "/system/controlDict")
    if "functions" in f:
        del f["functions"]
        f.writeFile()
    """
    if os.path.isfile(output_path + os.path.sep +"Allrun.sh"):
        os.remove(output_path + os.path.sep +"Allrun.sh")
    if os.path.isfile(output_path + os.path.sep +"Allclean.sh"):
        os.remove(output_path + os.path.sep +"Allclean.sh")

def createCaseFromScratch(output_path, solver_name):
    if os.path.isdir(output_path):
        shutil.rmtree(output_path)
    os.makedirs(output_path) # mkdir -p
    os.makedirs(output_path + os.path.sep + "system")
    os.makedirs(output_path + os.path.sep + "constant")
    os.makedirs(output_path + os.path.sep + "0")
    createRawFoamFile(output_path, 'system', 'controlDict', getControlDictTemplate(solver_name))
    createRawFoamFile(output_path, 'system', 'fvSolution', getFvSolutionTemplate())
    createRawFoamFile(output_path, 'system', 'fvSchemes', getFvSchemesTemplate())
    # turbulence properties and fuid properties will be setup later in base builder


def copySettingsFromExistentCase(output_path, source_path):
    """build case structure from string template, both folder paths must existent
    """
    shutil.copytree(source_path + os.path.sep + "constant", output_path + os.path.sep + "constant")
    shutil.copytree(source_path + os.path.sep + "system", output_path + os.path.sep + "system")
    #runFoamCommand('foamCopySettins  {} {}'.format(source_path, output_path))
    #foamCopySettins: Copy OpenFOAM settings from one case to another, without copying the mesh or results
    if os.path.exists(source_path + os.path.sep + "0"):
        shutil.copytree(source_path + os.path.sep + "0", output_path + os.path.sep + "0")
    init_dir = output_path + os.path.sep + "0"
    if not os.path.exists(init_dir):
        os.makedirs(init_dir) # mkdir -p 
    """
    if os.path.isdir(output_path + os.path.sep +"0.orig") and not os.path.exists(init_dir):
        shutil.copytree(output_path + os.path.sep +"0.orig", init_dir)
    else:
        print("Error: template case {} has no 0 or 0.orig subfolder".format(source_path))
    """
    #foamCloneCase:   Create a new case directory that includes time, system and constant directories from a source case.

#################################################################################

_foamFileHeader_part1 = '''/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  {}.{}                                   |
|   \\\\  /    A nd           | Web:      www.OpenFOAM.org                      |
|    \\\\/     M anipulation  |                                                 |
\*---------------------------------------------------------------------------*/
'''.format(getFoamVersion()[0], getFoamVersion()[1])

_foamFileHeader_part2 = '''FoamFile
{
    version     2.0;
    format      ascii;
    class       %s;
    location    "%s";
    object      %s;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //
// generated by createRawFoamFile

'''
def getFoamFileHeader(location, dictname, classname = 'dictionary'):
        return _foamFileHeader_part1 + _foamFileHeader_part2 % (classname, location, dictname)

def createRawFoamFile(case, location, dictname, lines, classname = 'dictionary'):
    fname = case + os.path.sep + location +os.path.sep + dictname
    if os.path.exists(fname):
        if _debug: print("Warning: overwrite createRawFoamFile if dict file exists  {}".format(fname))
    with open(fname, 'w+') as f:
        f.write(getFoamFileHeader(location, dictname, classname))
        f.writelines(lines)

##################################################################

def _isWindowsPath(p):
    if p.find(':') > 0:
        return True
    else:
        return False
            
def _fromWindowsPath(p):
    # bash on windows "C:\Path" -> /mnt/c/Path
    # cygwin can set the mount point for all windows drives under /mnt in /etc/fstab
    drive, tail = os.path.splitdrive(p)
    pp = tail.replace('\\', '/')
    return "/mnt/" + drive.lower() + os.path.sep + pp

def _toWindowsPath(p):
    #fixedme: it does not deal with path with quote
    pp = p.split('/')
    return pp[1] + ":" + (os.path.sep).join(pp[2:])

def translatePath(p):
    pp = os.path.abspath(p)
    if _isWindowsPath(p) and getFoamRuntime() == "BashWSL":
        pp = _fromWindowsPath(pp)
    if pp.find('"') < 0:  # using double quote to protect space within path, if not yet provided
        pp = '"' + pp + '"'
    return pp

def _translateFoamCasePath(cmd):
    """ Bash on Windows (Windows Linux Subsystem) needs a translation from windows path to linux path
    """
    l = len(cmd)
    for i,s in enumerate(cmd):
        if s == "-case" and i+1 < l:
            p = cmd[i+1]  # it must exist
            pp = translatePath(p)
            cmd[i+1] = pp
    return cmd


def runFoamCommand(cmd):
    """ run OpenFOAM command in Shell mode
    wait until finish, caller is not interested on output but whether succeeded
    source foam_dir/etc/bashrc before run foam related program
    `shell=True` does not work if freeCAD is not started in shell terminal
    Bash on Ubuntu on Windows, may need case path translation done in Builder
    """

    if isinstance(cmd, list):
        cmd = _translateFoamCasePath(cmd)
        #cmd = ' '.join(cmd)
    else:
        print("Warning: runFoamCommand() command and options must be specified in a list")

    env_setup_script = "source {}/etc/bashrc".format(getFoamDir())
    #env_setup_script = "source ~/.bashrc"

    #cmdline = """bash -c ' {} && {}'""".format(env_setup_script, cmd)
    #cmdline = ['bash', '-c', "'", env_setup_script, '&&'] + cmd + ["'"]
    #cmdline = """bash -i -c  '{} && {}' """.format(env_setup_script, ' '.join(cmd))
    cmdline = ' '.join(cmd)
    print("Run command: ", cmdline)
    out = subprocess.check_output(['bash', '-i', '-c', cmdline], stderr=subprocess.PIPE)
    if _debug: print(out)
    '''
    cmdline = ' '.join(cmd)
    cmdline = """bash -c -i '{}'""".format(cmdline)
    print("Run command: ", cmdline)
    process = subprocess.Popen(cmdline, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    stdout, stderr = process.communicate()
    exitCode = process.returncode

    if _debug:
        print(stdout)

    if (exitCode != 0):
        if _debug:
            print(stderr)
        #else:  # should allow runFoamCommand to fail
            #raise SystemError("Error in foamRunCommand:".format(cmdline), exitCode)
    return exitCode
    '''

###########################################################################

def convertMesh(case, mesh_file, scale):
    """ 
    see all mesh conversion tool: <>
    scale: CAD has mm as length unit usually, while CFD meshing using SI metre
    """
    mesh_file = translatePath(mesh_file)

    if mesh_file.find(".unv")>0:
        cmdline = ['ideasUnvToFoam', '-case', case, mesh_file]  # mesh_file path may also need translate
        runFoamCommand(cmdline)
        changeBoundaryType(case, 'defaultFaces', 'wall')  # rename default boundary type to wall
    if mesh_file[-4:] == ".geo":  # GMSH mesh
        print('Error:GMSH exported *.geo mesh is not support yet')
    if mesh_file[-4:] == ".msh":  # ansys fluent mesh
        cmdline = ['fluentMeshToFoam', '-case', case, mesh_file]  # mesh_file path may also need translate
        runFoamCommand(cmdline)
        changeBoundaryType(case, 'defaultFaces', 'wall')  # rename default boundary name (could be any name)
        print("Info: boundary exported from named selection, started with lower case")
    if scale and isinstance(scale, numbers.Number):
        cmdline = ['transformPoints', '-case', case, '-scale', '"({} {} {})"'.format(scale, scale, scale)]
    else:
        print("Error: mesh scaling ratio is must be a float or integer\n")

def listBoundaryNames(case):
    return BoundaryDict(case).patches()

def changeBoundaryType(case, bc_name, bc_type):
    """ change boundary named `bc_name` to `bc_type` in boundary dict file
    """    
    f = BoundaryDict(case)
    if bc_name in f.patches():
        f[bc_name]['type'] = bc_type
    else:
        print("boundary `{}` not found, so boundary type is not changed".format(bc_name))
    f.writeFile()

############################### dict set and getter ###########################################
def formatValue(v):
    """ format scaler or vector into "uniform scaler or uniform (x y z)"
    """
    if isinstance(v, string_types) or isinstance(v, numbers.Number):
        return "uniform {}".format(v)
    elif isinstance(v, list) or isinstance(v, tuple):  # or isinstance(v, tupleProxy))
        return "uniform ({} {} {})".format(v[0], v[1], v[2])
    else:
        raise Exception("Error: vector input {} is not string or sequence type, return zero vector string")

def formatList():
    pass

def getDict(dict_file, key):
    if isinstance(key, string_types) and key.find('/')>=0:
        group = [k for k in key.split('/') if k]
    elif isinstance(key, list) or isinstance(key, tuple):
        group = [s for s in key if isinstance(s, string_types)]
    else:
        print("Warning: input key is not string or sequence type, return None".format(key))
        return None

    f = ParsedParameterFile(dict_file)
    if len(group) >= 1:
        d = f
        for i in range(len(group)-1):
            if group[i] in d:
                d = d[group[i]]
            else:
                return None
        if group[-1] in d:
            return d[group[-1]]
        else:
            return None

def setDict(dict_file, key, value):
    """all parameters are string type, accept, None or empty string
    dict_file: file must exist, checked by caller
    key:
    value: None or empty string  will delet such key
    """

    if isinstance(key, string_types) and key.find('/')>=0:
        group = [k for k in key.split('/') if k]
    elif isinstance(key, list) or isinstance(key, tuple):
        group = [s for s in key if isinstance(s, string_types)]
    else:
        print("Warning: input key is not string or sequence type, so do nothing but return".format(key))
        return

    f = ParsedParameterFile(dict_file)        
    if len(group) == 3:
        d = f[group[0]][group[1]]  # at most 3 levels, assuming it will auto create not existent key
    elif len(group) == 2:
        d = f[group[0]]
    else:
        d = f
    k = group[-1]

    if value:  # 
        d[k] = value
    elif key in d:
        del d[k]  #if None, or empty string is specified, delete this key
    else:
        print('Warning: check parameters for set_dict() key={} value={}'.format(key, value))
    f.writeFile()

#################################topoSet, multiregion#####################################

def listVarablesInFolder(path):
    if os.path.split(path) == '0':
        initFolder = path
    else:
        initFolder = path + os.path.sep + "0"
    if os.path.exists(initFolder):
        import glob
        l = glob.glob(initFolder + os.path.sep + "*")
        #(_, _, filenames) = os.walk(initFolder)
        return [os.path.split(f)[-1] for f in l]
    else:
        print("Warning: {} is not an existent case path".format(initFolder))
        return []

def listZones(case):
    """
    point/face/cellSet's provide a named list of point/face/cell indexes. 
    Zones are an extension to the sets, since zones provide additional information useful for mesh manipulation. Zones are commonly used for MRF, baffles, dynamic meshes, porous mediums and other features available through "fvOptions".
    Sets can be used to create Zones (the opposite also works).

    to create cellSet, faceSet, pointSet: topoSet command and dict of '/system/topoSetDict'
    https://openfoamwiki.net/index.php/TopoSet
    """
    pass  # check topoSetDict file???  mesh file folder should have a file 

def listRegions(case):
    """
    conjugate heat transfer model needs multi-region
    """
    pass
    
def listTimeSteps(case):
    """
    return a list of float time for tranisent simulation or iteration for steady case
    """
    pass

def plotSolverProgress(case):
    """GNUplot to plot convergence progress of simulation
    """
    pass