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
import os
import os.path
import shutil
import platform
import tempfile
import multiprocessing
import subprocess

_using_pyfoam = True
if _using_pyfoam:
    from PyFoam.RunDictionary.ParsedParameterFile import ParsedParameterFile
    from PyFoam.RunDictionary.BoundaryDict import BoundaryDict
    from PyFoam.Applications.PlotRunner import PlotRunner
    #from PyFoam.FoamInformation import foamVersionString, foamVersionNumber  # works only in console
    from PyFoam.ThirdParty.six import string_types, iteritems
else:
    # implement our own class: ParsedParameterFile, getDict, setDict
    raise NotImplementedError("drop in replacement of PyFoam is not implemented")

from FoamTemplateString import *

_debug = True
# ubuntu 14.04 defaullt to 3.x, while ubuntu 16.04 default to 4.x, windows 10 WSL simulate ubuntu 14.04/16.04
#DEFAULT_FOAM_DIR = '/opt/openfoam30'
#DEFAULT_FOAM_VERSION = (3,0,0)
_DEFAULT_FOAM_DIR = '/opt/openfoam4'
_DEFAULT_FOAM_VERSION = (4,0)


def _isWindowsPath(p):
    if p.find(':') > 0:
        return True
    else:
        return False

def _toWindowsPath(p):
    #fixedme: it does not deal with path with quote, space
    pp = p.split('/')
    assert pp[0] == '' and pp[1] == 'mnt' 
    return pp[2] + ":\\" + ('\\').join(pp[3:])

def _fromWindowsPath(p):
    # bash on windows "C:\Path" -> /mnt/c/Path
    # cygwin can set the mount point for all windows drives under /mnt in /etc/fstab
    drive, tail = os.path.splitdrive(p)
    pp = tail.replace('\\', '/')
    return "/mnt/" + (drive[:-1]).lower() + pp

def translatePath(p):
    # remove quote at first, leave the quote protection done outside
    pp = os.path.abspath(p)
    if _isWindowsPath(p) and getFoamRuntime() == "BashWSL":
        pp = _fromWindowsPath(pp)
    return pp

def runFoamCommandOnWSL(case, cmds, output_file=None):
    """ Wait for command to complete on bash on windows 10
    case path and output file path will be converted into ubuntu pass automatically in this function
    """
    if not output_file:
        if tempfile.tempdir:
            output_file = tempfile.tempdir + os.path.sep + "tmp_output.txt"
        else:
            output_file = "tmp_output.txt"
    output_file = os.path.abspath(output_file)
    print(output_file)
    if os.path.exists(output_file):
        os.remove(output_file)
    output_file_wsl = _fromWindowsPath(output_file)
    # using double quote to protect space in file path
    app = cmds[0]
    if case:
        case_path = _fromWindowsPath(os.path.abspath(case))
        cmdline = app + ' -case "' + case_path +'" ' + ' '.join(cmds[1:])
    else:
        cmdline = app + ' ' + ' '.join(cmds[1:])
    #cmdline = ['bash', '-i', '-c', 'source ~/.bashrc && {} > "{}"'.format(cmdline, output_file_wsl)]
    #cmdline = """bash -c 'source ~/.bashrc && {} > "{}"' """.format(cmdline, output_file_wsl)
    cmdline = """bash -c 'source ~/.bashrc && {} > {}' """.format(cmdline, output_file_wsl)
    print("Running: ", cmdline)

    retcode = subprocess.call(cmdline)  # os.system() does not work!
    if int(retcode):
        print("Error: command line return with code", retcode)
    # corret and write to file on ubuntu path
    if os.path.exists(output_file):
        of = open(output_file)
        result = of.read()
        of.close()
        return result
    else:
        print("Error: can not find the output file: ",output_file)
        return None

###################################################

def _detectFoamDir():
    ''' Set foam installation directory if WM_PROJECT_DIR is detected else return none. If the user specified an
        Instalation path it will overwrite the aforementioned.
    '''
    if platform.system() == 'Windows':
        case_path = None
        foam_dir = runFoamCommandOnWSL(case_path, 'echo $WM_PROJECT_DIR')
    else:
        cmdline = ['bash', '-i', '-c', 'source ~/.bashrc && echo $WM_PROJECT_DIR']
        foam_dir = subprocess.check_output(cmdline, stderr=subprocess.PIPE)
    # Python 3 compatible, check_output() return type byte
    foam_dir = str(foam_dir)
    if len(foam_dir)>1:                 # If env var is not defined, python 3 returns `b'\n'` and python 2`\n`
        if foam_dir[:2] == "b'":
            foam_dir = foam_dir[2:-3]   # Python3: Strip 'b' from front and EOL char
        else:
            foam_dir= foam_dir.strip()  # Python2: Strip EOL char
        return foam_dir
    else:
        ''' A warning message is generated when the installation path is also not available. '''
        return None

def _detectFoamVersion():
    if platform.system() == 'Windows':
        case_path = None
        foam_ver = runFoamCommandOnWSL(case_path, 'echo $WM_PROJECT_VERSION')
    else:
        cmdline = ['bash', '-i', '-c', 'source ~/.bashrc && echo $WM_PROJECT_VERSION']
        foam_ver = subprocess.check_output(cmdline, stderr=subprocess.PIPE)
    # Python 3 compatible, check_output() return type byte
    foam_ver = str(foam_ver)
    if len(foam_ver)>1:
        if foam_ver[:2] == "b'":
            foam_ver = foam_ver[2:-3]    # Python3: Strip 'b' from front and EOL char
        else:
            foam_ver = foam_ver.strip()  # Python2: Strip EOL char
        #return tuple([int(s) if s.isdigit() else 0 for s in foam_ver.split('.')])  # version string 4.x should be parsed as 4.0
        return foam_ver.split('.')
        # return tuple([int(s) for s in foam_ver.split('.')])
    else:
        ''' A warning message is generated when the installation path is also not available. '''
        return None

_FOAM_SETTINGS = {"FOAM_DIR": _detectFoamDir(), "FOAM_VERSION": _detectFoamVersion()}


# public API getter and setter for FOAM_SETTINGS
def setFoamDir(dir):
    if os.path.exists(dir + os.path.sep + "etc/bashrc") and os.path.isabs(dir):
        # Overwrite using user specified installation path
        _FOAM_SETTINGS['FOAM_DIR'] = dir
    elif (os.path.exists(getFoamDir() + os.path.sep + "etc/bashrc")):
        # Keep sourced WM_PROJECT_DIR
        _FOAM_SETTINGS['FOAM_DIR'] = getFoamDir()
    else:
        print("Warning: The installation directory is not defined. Either source the relevant 'bashrc' file or \n)")
        print("specify the installation path in Solver. \n")

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

# # see more details on variants: https://openfoamwiki.net/index.php/Forks_and_Variants
# # http://www.cfdsupport.com/install-openfoam-for-windows.html, using cygwin
# #FOAM_VARIANTS = ['OpenFOAM', 'foam-extend', 'OpenFOAM+']
# #FOAM_RUNTIMES = ['FreeFOAM', 'Cygwin', 'BashWSL']
# def _detectFoamVarient():
#     """ FOAM_EXT version is also detected from 'bash -i -c "echo $WM_PROJECT_VERSION"'  or $WM_FORK
#     """
#     if getFoamDir().find('ext') > 0:
#         return  "foam-extend"
#     else:
#        return "OpenFOAM"

# Bash on Ubuntu on Windows detection and path translation
def _detectFoamRuntime():
    if platform.system() == 'Windows':
        return "BashWSL"  # 'Cygwin'
    else:
        return "Posix"

# _FOAM_SETTINGS['FOAM_VARIANT'] = _detectFoamVarient()
_FOAM_SETTINGS['FOAM_RUNTIME'] = _detectFoamRuntime()
# def getFoamVariant():
#     """detect from output of 'bash -i -c "echo $WM_PROJECT_DIR"', if default is not set
#     """
#     if 'FOAM_VARIANT' in _FOAM_SETTINGS:
#         return _FOAM_SETTINGS['FOAM_VARIANT']
#
# def isFoamExt():
#     return _FOAM_SETTINGS['FOAM_VARIANT'] == "foam-extend"

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
        if getFoamVersion()[0] < 3: # or isFoamExt():
            return 'muSgs'
        else:
            return 'nuSgs'
    if solverSettings['compressible']:
        if getFoamVersion()[0] < 3: # or isFoamExt():
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
    # elif turbulenceModelName in kOmege_models:
    #     var_list = ['k', 'omega', viscosity_var]
    elif turbulenceModelName in spalartAllmaras_models:
        var_list = [viscosity_var, 'nuTilda'] # incompressible/simpleFoam/airFoil2D/
    #elif turbulenceModelName in LES_models:
    #    var_list = ['k', viscosity_var, 'nuTilda']
    #elif turbulenceModelName == "qZeta":  # transient models has different var
    #    var_list = []  # not supported yet in boundary settings
    else:
        print("Error: Turbulence model {} is not supported yet".format(turbulenceModelName))
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
    elif source_path.find("defaults")>=0:
        if not os.path.isabs(source_path):  # create case from existent case folder
            source_path = os.path.join(getFoamDir(), os.path.sep, source_path)
        if os.path.exists(source_path):
            copySettingsFromExistentCase(output_path, source_path)
        else:
            raise Exception("Error: defaults case folder: {} not found".format(source_path))
    elif source_path[-4:] == ".zip":  # zipped case template,outdated
        template_path = source_path
        if os.path.isfile(template_path):
            import zipfile
            with zipfile.ZipFile(source_path, "r") as z:
                z.extractall(output_path)  #auto replace existent case setup without warning
        else:
            raise Exception("Error: template case file {} not found".format(source_path))
    else:
        raise Exception('Error: template {} is not a tutorials case path, defaults case path, or zipped file'.format(source_path))
    #foamCleanPolyMesh
    mesh_dir = os.path.join(output_path, "constant", "polyMesh")
    if os.path.isdir(mesh_dir):
        shutil.rmtree(mesh_dir)
    meshOrg_dir = os.path.join(output_path, "constant", "polyMesh.org")
    if os.path.isdir(meshOrg_dir):
        shutil.rmtree(meshOrg_dir)
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
    shutil.copytree(source_path + os.path.sep + "system", output_path + os.path.sep + "system")
    source_const = os.path.join(source_path, "constant")
    dest_const = os.path.join(output_path, "constant")
    if os.path.exists(source_const):
        shutil.copytree(source_const, dest_const)
    else:
        if not os.path.exists(dest_const):
            os.makedirs(dest_const)
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

def createRunScript(case, init_potential, run_parallel, solver_name, num_proc):
    print("Create Allrun script ")

    fname = case + os.path.sep + "Allrun"
    meshOrg_dir = case + os.path.sep + "constant/polyMesh.org"
    mesh_dir = case + os.path.sep + "constant/polyMesh"

    if os.path.exists(fname):
        if _debug: print("Warning: Overwrite existing Allrun script ")
    with open(fname, 'w+') as f:
        f.write("#!/bin/sh \n\n")

        f.write("# Unset and source bashrc\n")
        f.write("source {}/etc/config/unset.sh\n".format(getFoamDir()))
        f.write("source {}/etc/bashrc\n\n".format(getFoamDir()))

        ''' Mesh is stored in PolyMesh.org to ensure the mesh is preserved if the user decide to clean the case from
            the terminal.
        '''
        f.write("# Create symbolic links to polyMesh.org\n")
        f.write("mkdir {}\n".format(mesh_dir))
        f.write("ln -s {}/boundary {}\n".format(meshOrg_dir, mesh_dir))
        f.write("ln -s {}/faces {}\n".format(meshOrg_dir, mesh_dir))
        f.write("ln -s {}/neighbour {}\n".format(meshOrg_dir, mesh_dir))
        f.write("ln -s {}/owner {}\n".format(meshOrg_dir, mesh_dir))
        f.write("ln -s {}/points {}\n".format(meshOrg_dir, mesh_dir))
        f.write("\n")
        
        if (init_potential):
            f.write ("# Initialise flow\n")
            f.write ("potentialFoam -case "+case+" 2>&1 | tee "+case+"/log.potentialFoam\n\n")
        
        if (run_parallel):
            f.write ("# Run application in parallel\n")
            f.write ("decomposePar 2>&1 | tee log.decomposePar\n")
            f.write ("mpirun -np {} {} -parallel -case {} 2>&1 | tee {}/log.{}\n\n".format(str(num_proc), solver_name, case, case,solver_name))
        else:
            f.write ("# Run application\n")
            f.write ("{} -case {} 2>&1 | tee {}/log.{}\n\n".format(solver_name,case,case,solver_name))

    cmdline = ("chmod a+x "+fname) # Update Allrun permission, it will fail silently on windows
    out = subprocess.check_output(['bash', '-l', '-c', cmdline], stderr=subprocess.PIPE)

    
def copySettingsFromExistentCase(output_path, source_path):
    """build case structure from string template, both folder paths must existent
    """
    shutil.copytree(source_path + os.path.sep + "system", output_path + os.path.sep + "system")
    source_const = os.path.join(source_path, "constant")
    dest_const = os.path.join(output_path, "constant")
    if os.path.exists(source_const):
        shutil.copytree(source_const, dest_const)
    else:
        if not os.path.exists(dest_const):
            os.makedirs(dest_const)
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
| ===========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  {}.{}                                   |
|   \\\\  /    A nd           | Web:      www.OpenFOAM.org                      |
|    \\\\/     M anipulation  |                                                 |
\*---------------------------------------------------------------------------*/
'''

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

def runFoamApplication(cmd, case):
    """ Run OpenFOAM application and automatically generate the log.application file (Wait until finished)
        cmd  - String with the application being the first entry followied by the options.
              e.g. `transformPoints -scale "(0.001 0.001 0.001)"
        case - Case directory or path
    """
    if (isinstance(cmd, list) or isinstance(cmd, tuple)):
        cmds = cmd
    elif isinstance(cmd, str):
        cmds = cmd.split(' ')  # Insensitive to incorrect split like space and quote
    else:
        raise Exception("Error: Application and options must be specified as a list or tuple.")

    app = cmds[0]
    logFile = "{}/log.{}".format(os.path.abspath(case), app)

    if os.path.exists(logFile):
        print("Warning: {} already exists, removed to rerun {}.".format(logFile,app))
        os.remove(logFile)

    if getFoamRuntime() == "BashWSL":
        out = runFoamCommandOnWSL(case, cmds, logFile)
    else:
        cmdline = app+' -case "'+case+'" '+' '.join(cmds[1:])   # Space to separate options
        env_setup_script = "{}/etc/bashrc".format(getFoamDir())

        print("Running ", cmdline)
        # cmdline += (" | tee "+logFile) # Pipe to screen and log file
        cmdline += (" > " + logFile)     # Pipe to log file
        cmdline = ['bash', '-c', """source "{}" && {} """.format(env_setup_script, cmdline)]

        out = subprocess.check_output(cmdline, cwd=case, stderr=subprocess.PIPE)
    if _debug: print(out)


# not a good way to extract path in command line, double quote and space cause problem      
# deprecated, just for compatible propurse, remove in next commit
def _translateFoamCasePath(cmd):
    """ Bash on Windows (Windows Linux Subsystem) needs a translation from windows path to linux path
    """
    if not (isinstance(cmd, list) or isinstance(cmd, tuple)):
        print("Warning: command and options must be specified in a list or tuple")
    l = len(cmd)
    for i,s in enumerate(cmd):
        if s == "-case" and i+1 < l:
            p = cmd[i+1]  # it must exist
            pp = translatePath(p)
            cmd[i+1] = pp
    return cmd


########################################  Mesh manupulation  ###############################

def convertMesh(case, mesh_file, scale):
    """ FOAM mesh conversion: www.openfoam.com/documentation/user-guide/mesh-conversion.php
        Scale: CAD is always in mm while FOAM uses SI units (m)
    """
    mesh_file = translatePath(mesh_file)

    if mesh_file.find(".unv")>0:
        cmdline = ['ideasUnvToFoam', '"{}"'.format(mesh_file)]  # mesh_file path may also need translate
        runFoamApplication(cmdline,case)
        changeBoundaryType(case, 'defaultFaces', 'wall')  # rename default boundary type to wall
    if mesh_file[-4:] == ".geo":  # GMSH mesh
        print('Error:GMSH exported *.geo mesh is not support yet')
    if mesh_file[-4:] == ".msh":  # ansys fluent mesh
        cmdline = ['fluentMeshToFoam', '"{}"'.format(mesh_file)]  # mesh_file path may also need translate
        runFoamApplication(cmdline, case)
        changeBoundaryType(case, 'defaultFaces', 'wall')  # rename default boundary name (could be any name)
        print("Info: boundary exported from named selection, started with lower case")

    if scale and isinstance(scale, numbers.Number):
        cmdline = ['transformPoints', '-scale', '"({} {} {})"'.format(scale, scale, scale)]
        runFoamApplication(cmdline, case)
    else:
        print("Error: mesh scaling ratio is must be a float or integer\n")

def listBoundaryNames(case):
    return BoundaryDict(case).patches()

def changeBoundaryType(case, bc_name, bc_type):
    """ Change boundary named `bc_name` to `bc_type`
    """    
    f = BoundaryDict(case)
    if bc_name in f.patches():
        f[bc_name]['type'] = bc_type
    else:
        print("Boundary `{}` not found, so type is not changed".format(bc_name))
    f.writeFile()

def movePolyMesh(case):
    """ Move polyMesh to polyMesh.org 
    """
    meshOrg_dir = case + os.path.sep + "constant/polyMesh.org"
    mesh_dir = case + os.path.sep + "constant/polyMesh"
    if os.path.isdir(meshOrg_dir):
        shutil.rmtree(meshOrg_dir)
    shutil.copytree(mesh_dir, meshOrg_dir)
    shutil.rmtree(mesh_dir)


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
    key: create the key if not existent
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

def modifyControlDictEntries(dict_file,key,value):
    """Intent of this function is to change startTime,endTime,deltaT and writeInterval
    for which setDict does not work because there is only 1 entry in the dict file
    No error checking is done in this function, as it is assumed to be called correctly
    """
    f = ParsedParameterFile(dict_file)
    f[key] = value
    f.writeFile()


#################################topoSet, multiregion#####################################

def listVarablesInFolder(path):
    """ list variable (fields) name for the case or under 0 path
    """
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
    raise NotImplementedError()  # check topoSetDict file???  mesh file folder should have a file 

def listRegions(case):
    """
    conjugate heat transfer model needs multi-region
    """
    raise NotImplementedError()
    
def listTimeSteps(case):
    """
    return a list of float time for tranisent simulation or iteration for steady case
    """
    raise NotImplementedError()

def plotSolverProgress(case):
    """GNUplot to plot convergence progress of simulation
    """
    raise NotImplementedError()
