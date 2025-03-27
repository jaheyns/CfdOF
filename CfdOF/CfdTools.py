# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2015 - Qingfeng Xia <qingfeng xia eng.ox.ac.uk>         *
# *   Copyright (c) 2017 Johan Heyns (CSIR) <jheyns@csir.co.za>             *
# *   Copyright (c) 2017 Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>          *
# *   Copyright (c) 2017 Alfred Bogaers (CSIR) <abogaers@csir.co.za>        *
# *   Copyright (c) 2019-2024 Oliver Oxtoby <oliveroxtoby@gmail.com>        *
# *   Copyright (c) 2022-2024 Jonathan Bergh <bergh.jonathan@gmail.com>     *
# *                                                                         *
# *   This program is free software: you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License as        *
# *   published by the Free Software Foundation, either version 3 of the    *
# *   License, or (at your option) any later version.                       *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Lesser General Public License for more details.                   *
# *                                                                         *
# *   You should have received a copy of the GNU Lesser General Public      *
# *   License along with this program.  If not,                             *
# *   see <https://www.gnu.org/licenses/>.                                  *
# *                                                                         *
# ***************************************************************************

# Utility functions like mesh exporting, shared by any CFD solver

from __future__ import print_function

import os
import os.path
import glob
import shutil
import tempfile
import platform
import subprocess
import sys
import math
import importlib
import types
from datetime import timedelta
import FreeCAD
from FreeCAD import Units
import Part
import BOPTools
from CfdOF.CfdConsoleProcess import CfdConsoleProcess
from CfdOF.CfdConsoleProcess import removeAppimageEnvironment
from PySide import QtCore
import CfdOF
import time
import atexit
if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtGui
    from PySide.QtGui import QFormLayout, QGridLayout

from PySide.QtWidgets import QApplication

translate = FreeCAD.Qt.translate

# Some standard install locations that are searched if an install directory is not specified
# Supports variable expansion and Unix-style globs (in which case the last lexically-sorted match will be used)
FOAM_DIR_DEFAULTS = {'Windows': ['C:\\Program Files\\ESI-OpenCFD\\OpenFOAM\\v*',
                                 '~\\AppData\\Roaming\\ESI-OpenCFD\\OpenFOAM\\v*',
                                 'C:\\Program Files\\blueCFD-Core-*\\OpenFOAM-*'],
                     'Linux': ['/usr/lib/openfoam/openfoam*',  # ESI official packages
                               '/opt/openfoam*', '/opt/openfoam-dev',  # Foundation official packages
                               '~/openfoam/OpenFOAM-v*',
                               '~/OpenFOAM/OpenFOAM-*.*', '~/OpenFOAM/OpenFOAM-dev'],  # Typical self-built locations
                     "Darwin": ['~/OpenFOAM/OpenFOAM-*.*', '~/OpenFOAM/OpenFOAM-dev']
                     }

PARAVIEW_PATH_DEFAULTS = {
                    "Windows": ["C:\\Program Files\\ParaView *\\bin\\paraview.exe"],
                    "Linux": ["/usr/bin/paraview", "/usr/local/bin/paraview"],
                    "Darwin": ["/Applications/ParaView-*.app/Contents/MacOS/paraview"]
                    }

QUANTITY_PROPERTIES = ['App::PropertyQuantity',
                       'App::PropertyLength',
                       'App::PropertyDistance',
                       'App::PropertyAngle',
                       'App::PropertyArea',
                       'App::PropertyVolume',
                       'App::PropertySpeed',
                       'App::PropertyAcceleration',
                       'App::PropertyForce',
                       'App::PropertyPressure',
                       'App::PropertyTemperature']

docker_container = None

def getDefaultOutputPath():
    prefs = getPreferencesLocation()
    output_path = FreeCAD.ParamGet(prefs).GetString("DefaultOutputPath", "")
    if not output_path:
        output_path = tempfile.gettempdir()
    output_path = os.path.normpath(output_path)
    return output_path


def getOutputPath(analysis):
    if analysis and 'OutputPath' in analysis.PropertiesList:
        output_path = analysis.OutputPath
    else:
        output_path = ""
    if not output_path:
        output_path = getDefaultOutputPath()
    if not os.path.isabs(output_path):
        if not FreeCAD.ActiveDocument.FileName:
            raise RuntimeError("The output directory is specified as a path relative to the current file's location; "
                "however, it needs to be saved in order to determine this.")
        output_path = os.path.join(os.path.dirname(FreeCAD.ActiveDocument.FileName), output_path)
    prefs = getPreferencesLocation()
    if FreeCAD.ParamGet(prefs).GetBool("AppendDocNameToOutputPath", 0):
        output_path = os.path.join(output_path, FreeCAD.ActiveDocument.Name)
    output_path = os.path.normpath(output_path)
    return output_path


# Get functions
if FreeCAD.GuiUp:
    def getResultObject():
        sel = FreeCADGui.Selection.getSelection()
        if len(sel) == 1:
            if sel[0].isDerivedFrom("Fem::FemResultObject"):
                return sel[0]
        for i in getActiveAnalysis().Group:
            if i.isDerivedFrom("Fem::FemResultObject"):
                return i
        return None


def getParentAnalysisObject(obj):
    """
    Return CfdAnalysis object to which this obj belongs in the tree
    """
    from CfdOF import CfdAnalysis
    parent = obj.getParentGroup()
    if parent is None:
        return None
    elif hasattr(parent, 'Proxy') and isinstance(parent.Proxy, CfdAnalysis.CfdAnalysis):
        return parent
    else:
        return getParentAnalysisObject(parent)


def getPhysicsModel(analysis_object):
    is_present = False
    for i in analysis_object.Group:
        if "PhysicsModel" in i.Name:
            physics_model = i
            is_present = True
    if not is_present:
        physics_model = None
    return physics_model


def getDynamicMeshAdaptation(mesh_object):
    dynamic_mesh_adaption_model = None
    for i in mesh_object.Group:
        if i.Name.startswith("DynamicMeshInterfaceRefinement") or i.Name.startswith("DynamicMeshShockRefinement"):
            dynamic_mesh_adaption_model = i
    return dynamic_mesh_adaption_model


def getMeshObject(analysis_object):
    is_present = False
    mesh_obj = []
    if analysis_object:
        members = analysis_object.Group
    else:
        members = FreeCAD.activeDocument().Objects
    from CfdOF.Mesh.CfdMesh import CfdMesh
    for i in members:
        if hasattr(i, "Proxy") and isinstance(i.Proxy, CfdMesh):
            if is_present:
                FreeCAD.Console.PrintError("Analysis contains more than one mesh object.")
            else:
                mesh_obj.append(i)
                is_present = True
    if not is_present:
        mesh_obj = [None]
    return mesh_obj[0]


def getPorousZoneObjects(analysis_object):
    return [i for i in analysis_object.Group if i.Name.startswith('PorousZone')]


def getInitialisationZoneObjects(analysis_object):
    return [i for i in analysis_object.Group if i.Name.startswith('InitialisationZone')]


def getZoneObjects(analysis_object):
    return [i for i in analysis_object.Group if 'Zone' in i.Name]


def getInitialConditions(analysis_object):
    from CfdOF.Solve.CfdInitialiseFlowField import CfdInitialVariables
    for i in analysis_object.Group:
        if isinstance(i.Proxy, CfdInitialVariables):
            return i
    return None


def getMaterials(analysis_object):
    return [i for i in analysis_object.Group if i.isDerivedFrom('App::MaterialObjectPython')]


def getSolver(analysis_object):
    from CfdOF.Solve.CfdSolverFoam import CfdSolverFoam
    for i in analysis_object.Group:
        if isinstance(i.Proxy, CfdSolverFoam):
            return i


def getSolverSettings(solver):
    """
    Convert properties into python dict, while key must begin with lower letter.
    """
    dict = {}
    f = lambda s: s[0].lower() + s[1:]
    for prop in solver.PropertiesList:
        dict[f(prop)] = solver.getPropertyByName(prop)
    return dict


def getCfdBoundaryGroup(analysis_object):
    group = []
    from CfdOF.Solve.CfdFluidBoundary import CfdFluidBoundary
    for i in analysis_object.Group:
        if isinstance(i.Proxy, CfdFluidBoundary):
            group.append(i)
    return group


def isPlanar(shape):
    """
    Return whether the shape is a planar face
    """
    n = shape.normalAt(0.5, 0.5)
    if len(shape.Vertexes) <= 3:
        return True
    for v in shape.Vertexes[1:]:
        t = v.Point - shape.Vertexes[0].Point
        c = t.dot(n)
        if c / t.Length > 1e-8:
            return False
    return True


def getMesh(analysis_object):
    from CfdOF.Mesh.CfdMesh import CfdMesh
    for i in analysis_object.Group:
        if hasattr(i, "Proxy") and isinstance(i.Proxy, CfdMesh):
            return i
    return None


def getResult(analysis_object):
    for i in analysis_object.Group:
        if i.isDerivedFrom("Fem::FemResultObject"):
            return i
    return None


def getModulePath():
    """
    Returns the current Cfd module path.
    Determines where this file is running from, so works regardless of whether
    the module is installed in the app's module directory or the user's app data folder.
    (The second overrides the first.)
    """
    return os.path.normpath(os.path.join(os.path.dirname(__file__), os.path.pardir))


# Function objects
def getReportingFunctionsGroup(analysis_object):
    group = []
    from CfdOF.PostProcess.CfdReportingFunction import CfdReportingFunction
    for i in analysis_object.Group:
        if isinstance(i.Proxy, CfdReportingFunction):
            group.append(i)
    return group


def getScalarTransportFunctionsGroup(analysis_object):
    group = []
    from CfdOF.Solve.CfdScalarTransportFunction import CfdScalarTransportFunction
    for i in analysis_object.Group:
        if isinstance(i.Proxy, CfdScalarTransportFunction):
            group.append(i)
    return group


# Mesh
def getMeshRefinementObjs(mesh_obj):
    from CfdOF.Mesh.CfdMeshRefinement import CfdMeshRefinement
    ref_objs = []
    for obj in mesh_obj.Group:
        if hasattr(obj, "Proxy") and isinstance(obj.Proxy, CfdMeshRefinement):
            ref_objs = ref_objs + [obj]
    return ref_objs


# Set functions
def setCompSolid(vobj):
    """
    To enable correct mesh refinement, boolean fragments are set to compSolid mode
    """
    doc_name = str(vobj.Object.Document.Name)
    doc = FreeCAD.getDocument(doc_name)
    for obj in doc.Objects:
        if hasattr(obj, 'Proxy') and isinstance(obj.Proxy, BOPTools.SplitFeatures.FeatureBooleanFragments):
            FreeCAD.getDocument(doc_name).getObject(obj.Name).Mode = 'CompSolid'


def normalise(v):
    import numpy
    mag = numpy.sqrt(sum(vi**2 for vi in v))
    import sys
    if mag < sys.float_info.min:
        mag += sys.float_info.min
    return [vi/mag for vi in v]


def cfdMessage(msg):
    """
    Print a message to console and refresh GUI
    """
    FreeCAD.Console.PrintMessage(msg)
    if FreeCAD.GuiUp:
        FreeCAD.Gui.updateGui()
        FreeCAD.Gui.updateGui()


def cfdWarning(msg):
    """
    Print a message to console and refresh GUI
    """
    FreeCAD.Console.PrintWarning(msg)
    if FreeCAD.GuiUp:
        FreeCAD.Gui.updateGui()
        FreeCAD.Gui.updateGui()


def cfdError(msg):
    """
    Print a message to console and refresh GUI
    """
    FreeCAD.Console.PrintError(msg)
    if FreeCAD.GuiUp:
        FreeCAD.Gui.updateGui()
        FreeCAD.Gui.updateGui()


def cfdErrorBox(msg):
    """
    Show message for an expected error
    """
    QtGui.QApplication.restoreOverrideCursor()
    if FreeCAD.GuiUp:
        QtGui.QMessageBox.critical(None, translate("Dialogs", "CfdOF Workbench"), msg)
    else:
        FreeCAD.Console.PrintError(msg + "\n")


def formatTimer(seconds):
    """
    Put the elapsed time printout into a nice format
    """
    return str(timedelta(seconds=seconds)).split('.', 2)[0].lstrip('0').lstrip(':')


def getColour(type):
    """
    type: 'Error', 'Warning', 'Logging', 'Text'
    """
    col_int = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/OutputWindow").GetUnsigned('color'+type)
    return '#{:08X}'.format(col_int)[:-2]


def setQuantity(inputField, quantity):
    """
    Set the quantity (quantity object or unlocalised string) into the inputField correctly
    """
    # Must set in the correctly localised value as the user would enter it.
    # A bit painful because the python locale settings seem to be based on language,
    # not input settings as the FreeCAD settings are. So can't use that; hence
    # this rather roundabout way involving the UserString of Quantity
    q = Units.Quantity(quantity)
    # Avoid any truncation
    if isinstance(q.Format, tuple):  # Backward compat
        q.Format = (12, 'e')
    else:
        q.Format = {'Precision': 12, 'NumberFormat': 'e', 'Denominator': q.Format['Denominator']}
    inputField.setProperty("quantityString", q.UserString)


def getQuantity(inputField):
    """
    Get the quantity as an unlocalised string from an inputField
    """
    q = inputField.property("quantity")
    return str(q)


def indexOrDefault(list, findItem, defaultIndex):
    """
    Look for findItem in list, and return defaultIndex if not found
    """
    try:
        return list.index(findItem)
    except ValueError:
        return defaultIndex


def storeIfChanged(obj, prop, val):
    cur_val = getattr(obj, prop)
    if isinstance(cur_val, Units.Quantity):
        if str(cur_val) != str(val):
            FreeCADGui.doCommand("App.ActiveDocument.{}.{} = '{}'".format(obj.Name, prop, val))
    elif cur_val != val:
        if isinstance(cur_val, str):
            FreeCADGui.doCommand("App.ActiveDocument.{}.{} = '{}'".format(obj.Name, prop, val))
        elif isinstance(cur_val, FreeCAD.Vector):
            FreeCADGui.doCommand("App.ActiveDocument.{}.{} = App.{}".format(obj.Name, prop, val))
        else:
            FreeCADGui.doCommand("App.ActiveDocument.{}.{} = {}".format(obj.Name, prop, val))


def copyFilesRec(src, dst, symlinks=False, ignore=None):
    """
    Recursively copy files from src dir to dst dir
    """
    if not os.path.exists(dst):
        os.makedirs(dst)
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if not os.path.isdir(s):
            shutil.copy2(s, d)


def getPatchType(bcType, bcSubType):
    """
    Get the boundary type based on selected BC condition
    """
    if bcType == 'wall':
        return 'wall'
    elif bcType == 'empty':
        return 'empty'
    elif bcType == 'constraint':
        if bcSubType == 'symmetry':
            return 'symmetry'
        elif bcSubType == 'cyclic':
            return 'cyclic'
        elif bcSubType == 'wedge':
            return 'wedge'
        elif bcSubType == 'empty':
            return 'empty'
        elif bcSubType == 'cyclicAMI':
            return 'cyclicAMI'
        else:
            return 'patch'
    else:
        return 'patch'


def movePolyMesh(case):
    """
    Move polyMesh to polyMesh.org to ensure availability if cleanCase is ran from the terminal.
    """
    meshOrg_dir = case + os.path.sep + "constant/polyMesh.org"
    mesh_dir = case + os.path.sep + "constant/polyMesh"
    if os.path.isdir(meshOrg_dir):
        shutil.rmtree(meshOrg_dir)
    shutil.copytree(mesh_dir, meshOrg_dir)
    shutil.rmtree(mesh_dir)


def getPreferencesLocation():
    # Set parameter location
    return "User parameter:BaseApp/Preferences/Mod/CfdOF"


def setFoamDir(installation_path):
    prefs = getPreferencesLocation()
    # Set OpenFOAM install path in parameters
    FreeCAD.ParamGet(prefs).SetString("InstallationPath", installation_path)

def startDocker():
    global docker_container
    if docker_container==None:
        docker_container = DockerContainer()
    if docker_container.container_id==None:
        if "podman" in docker_container.docker_cmd and platform.system() != "Linux":
            # Start podman machine if not already started, and we are on either MacOS or windows
            exit_code = checkPodmanMachineRunning()
            if exit_code==2:
                startPodmanMachine()
                if checkPodmanMachineRunning():
                    print("Aborting docker container initialization")
                    return 1
            elif exit_code==1:
                print("Aborting docker container initialization")
                return 1
        docker_container.start_container()
        if docker_container.container_id != None:
            print("Docker image {} started. ID = {}".format(docker_container.image_name, docker_container.container_id))
            return 0
        else:
            print(f"Unable to start {docker_container.docker_cmd} container. Refer to README for installation instructions.")
            return 1
    else:
        return 0 # startDocker() called but already running

def checkPodmanMachineRunning():
    print("Checking podman machine running")
    cmd = "podman machine list"
    proc = QtCore.QProcess()
    proc.start(cmd)
    proc.waitForFinished()
    line = ""
    while proc.canReadLine():
        line = str(proc.readLine().data(), encoding="utf-8")
        if len(line)>0:
            print(line)
    if "Currently running" in line:
        print("Podman machine running")
        return 0
    elif line[-9:]=="DISK SIZE":
        print("Podman machine not initialized - please refer to readme")
        return 1
    else:
        print("Podman machine not running")
        return 2

def startPodmanMachine():
    print("Attempting podman machine start")
    cmd = "podman machine start"
    proc = QtCore.QProcess()
    proc.start(cmd)
    proc.waitForFinished()
    line = ""
    while proc.canReadLine():
        line = str(proc.readLine().data(), encoding="utf-8")
        if len(line)>0:
            print(line)

def getFoamDir():
    global docker_container
    if docker_container==None:
        docker_container = DockerContainer()
    if docker_container.usedocker:
        return ""

    prefs = getPreferencesLocation()
    # Get OpenFOAM install path from parameters
    installation_path = FreeCAD.ParamGet(prefs).GetString("InstallationPath", "")
    # Ensure parameters exist for future editing
    setFoamDir(installation_path)

    # If not specified, try to detect from shell environment settings and defaults
    if not installation_path:
        installation_path = detectFoamDir()

    if installation_path:
        installation_path = os.path.normpath(installation_path)

    return installation_path


def getFoamRuntime():
    global docker_container
    if docker_container==None:
        docker_container = DockerContainer()
    if docker_container.usedocker:
        return 'PosixDocker'

    installation_path = getFoamDir()
    if installation_path is None:
        raise IOError("OpenFOAM installation path not set and not detected")

    runtime = None
    if platform.system() == 'Windows':
        if os.path.exists(os.path.join(installation_path, "msys64", "home", "ofuser", ".blueCFDCore")):
            runtime = 'BlueCFD'
        elif os.path.exists(os.path.join(installation_path, "..", "msys64", "home", "ofuser", ".blueCFDCore")):
            runtime = 'BlueCFD2'
        elif os.path.exists(os.path.join(installation_path, "msys64", "home", "ofuser", ".bashrc")):
            runtime = 'MinGW'
        elif os.path.exists(os.path.join(installation_path, "Windows", "Scripts")):
            runtime = 'WindowsDocker'
        elif os.path.exists(os.path.join(getFoamDir(), "etc", "bashrc")):
            runtime = 'BashWSL'
    else:
        if not len(getFoamDir()):
            runtime = 'PosixPreloaded'
        if os.path.exists(os.path.join(getFoamDir(), "etc", "bashrc")):
            runtime = 'Posix'

    if not runtime:
        raise IOError("The directory {} is not a recognised OpenFOAM installation".format(installation_path))

    return runtime


def findInDefaultPaths(paths):
    for d in paths.get(platform.system(), []):
        d = glob.glob(os.path.expandvars(os.path.expanduser(d)))
        if len(d):
            d = sorted(d)[-1]
            if os.path.exists(d):
                return d
    return None


def detectFoamDir():
    """
    Try to guess Foam install dir from WM_PROJECT_DIR or, failing that, various defaults
    """
    foam_dir = None
    if platform.system() == "Linux":
        # Detect pre-loaded environment
        cmdline = ['bash', '-l', '-c', 'echo $WM_PROJECT_DIR']
        foam_dir = subprocess.check_output(cmdline, stderr=subprocess.PIPE, universal_newlines=True)
        if len(foam_dir) > 1:               # If env var is not defined, `\n` returned
            foam_dir = foam_dir.strip()  # Python2: Strip EOL char
        else:
            foam_dir = None
        if foam_dir and not os.path.exists(os.path.join(foam_dir, "etc", "bashrc")):
            foam_dir = None
        if not foam_dir:
            foam_dir = None

    if foam_dir is None:
        foam_dir = findInDefaultPaths(FOAM_DIR_DEFAULTS)
    return foam_dir


def setParaviewPath(paraview_path):
    prefs = getPreferencesLocation()
    # Set Paraview install path in parameters
    FreeCAD.ParamGet(prefs).SetString("ParaviewPath", paraview_path)


def getParaviewPath():
    prefs = getPreferencesLocation()
    # Get path from parameters
    paraview_path = FreeCAD.ParamGet(prefs).GetString("ParaviewPath", "")
    # Ensure parameters exist for future editing
    setParaviewPath(paraview_path)
    return paraview_path


def setGmshPath(gmsh_path):
    prefs = getPreferencesLocation()
    # Set Paraview install path in parameters
    FreeCAD.ParamGet(prefs).SetString("GmshPath", gmsh_path)


def getGmshPath():
    prefs = getPreferencesLocation()
    # Get path from parameters
    gmsh_path = FreeCAD.ParamGet(prefs).GetString("GmshPath", "")
    # Ensure parameters exist for future editing
    setGmshPath(gmsh_path)
    return gmsh_path


def translatePath(p):
    """
    Transform path to the perspective of the Linux subsystem in which OpenFOAM is run (e.g. mingw)
    """
    if getFoamRuntime().startswith('BlueCFD'):
        return fromWindowsPath(p)
    else:
        return p


def reverseTranslatePath(p):
    """
    Transform path from the perspective of the OpenFOAM subsystem to the host system
    """
    if getFoamRuntime().startswith('BlueCFD'):
        return toWindowsPath(p)
    else:
        return p


def fromWindowsPath(p):
    drive, tail = os.path.splitdrive(p)
    pp = tail.replace('\\', '/')
    if getFoamRuntime() == "MinGW" or getFoamRuntime() == "BlueCFD" or getFoamRuntime() == "BlueCFD2":
        # Under mingw: c:\path -> /c/path
        if os.path.isabs(p):
            return "/" + (drive[:-1]).lower() + pp
        else:
            return pp
    elif getFoamRuntime() == "WindowsDocker":
        # Under docker: <userDir>/<path> -> /home/ofuser/workingDir/<path>
        if os.path.isabs(p):
            homepath = os.path.expanduser('~')
            try:
                if os.path.commonpath((os.path.normpath(p), homepath)) == homepath:
                    return '/home/ofuser/workingDir/' + os.path.relpath(p, homepath).replace('\\', '/')
                else:
                    raise ValueError("The path {} is not inside the users's home directory.".format(p))
            except ValueError:
                cfdError(
                    "The path {} cannot be used in the Docker environment. "
                    "Only paths inside the user's home directory are accessible.".format(p))
                raise
        else:
            return pp
    elif getFoamRuntime() == "BashWSL":
        # bash on windows: C:\Path -> /mnt/c/Path
        if os.path.isabs(p):
            return "/mnt/" + (drive[:-1]).lower() + pp
        else:
            return pp
    else:  # Nothing needed for posix
        return p


def toWindowsPath(p):
    pp = p.split('/')
    if getFoamRuntime() == "MinGW":
        # Under mingw: /c/path -> c:\path; /home/ofuser -> <instDir>/msys64/home/ofuser
        if p.startswith('/home/ofuser'):
            return getFoamDir() + '\\msys64\\home\\ofuser\\' + '\\'.join(pp[3:])
        elif p.startswith('/'):
            return pp[1].upper() + ':\\' + '\\'.join(pp[2:])
        else:
            return p.replace('/', '\\')
    elif getFoamRuntime() == "WindowsDocker":
        # Under docker: /home/ofuser/workingDir/<path> ->  <userDir>/<path>
        homepath = os.path.expanduser('~')
        if p.startswith('/home/ofuser/workingDir/'):
            return os.path.join(homepath, "\\".join(pp[4:]))
        else:
            return p.replace('/', '\\')
    elif getFoamRuntime() == "BashWSL":
        # bash on windows: /mnt/c/Path -> C:\Path
        if p.startswith('/mnt/'):
            return pp[2].toupper() + ':\\' + '\\'.join(pp[3:])
        else:
            return p.replace('/', '\\')
    elif getFoamRuntime().startswith("BlueCFD"):
        # Under blueCFD (mingw): /c/path -> c:\path; /home/ofuser/blueCFD -> <blueCFDDir>
        if p.startswith('/home/ofuser/blueCFD'):
            if getFoamRuntime() == "BlueCFD2":
                foam_dir = getFoamDir() + '\\' + '..'
            else:
                foam_dir = getFoamDir()
            return foam_dir + '\\' + '\\'.join(pp[4:])
        elif p.startswith('/'):
            return pp[1].upper() + ':\\' + '\\'.join(pp[2:])
        else:
            return p.replace('/', '\\')
    else:  # Nothing needed for posix
        return p


def getShortWindowsPath(long_name):
    """
    Gets the short path name of a given long path. http://stackoverflow.com/a/23598461/200291
    """
    import ctypes
    from ctypes import wintypes
    _GetShortPathNameW = ctypes.windll.kernel32.GetShortPathNameW
    _GetShortPathNameW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
    _GetShortPathNameW.restype = wintypes.DWORD

    output_buf_size = 0
    while True:
        output_buf = ctypes.create_unicode_buffer(output_buf_size)
        needed = _GetShortPathNameW(os.path.normpath(long_name), output_buf, output_buf_size)
        if output_buf_size >= needed:
            return output_buf.value
        else:
            output_buf_size = needed


def getRunEnvironment():
    """
    Return native environment settings necessary for running on relevant platform
    """
    if getFoamRuntime().startswith("BlueCFD"):
        return {"MSYSTEM": "MINGW64",
                "USERNAME": "ofuser",
                "USER": "ofuser",
                "HOME": "/home/ofuser"}
    else:
        return {}


def makeRunCommand(cmd, dir=None, source_env=True):
    """
    Generate native command to run the specified Linux command in the relevant environment,
    including changing to the specified working directory if applicable
    """

    if getFoamRuntime() == "PosixDocker" and ' pull ' in cmd:
        # Case where running from Install Docker thread
        return cmd.split()

    installation_path = getFoamDir()
    if installation_path is None:
        raise IOError("OpenFOAM installation directory not found")

    if dir is None:
        FreeCAD.Console.PrintMessage('Executing: {}\n'.format(cmd))
    else:
        FreeCAD.Console.PrintMessage('Executing: {} in {}\n'.format(cmd, dir))

    source = ""
    if source_env and len(installation_path):
        if getFoamRuntime() == "MinGW":
            foam_dir = getFoamDir()
            foam_version = os.path.split(installation_path)[-1].lstrip('v')
            source = 'call "{}\\setEnvVariables-v{}.bat" && '.format(foam_dir, foam_version)
        else:
            env_setup_script = "{}/etc/bashrc".format(installation_path)
            source = 'source "{}" && '.format(env_setup_script)

    if getFoamRuntime() == "PosixDocker":
        # Set source for docker container
        source = 'source /etc/bashrc && '

    cd = ""
    if dir:
        if getFoamRuntime() == "MinGW":
            cd = 'cd /d "{}" && '.format(translatePath(dir))
        else:
            cd = 'cd "{}" && '.format(translatePath(dir))

    if getFoamRuntime() == "PosixDocker":
        prefs = getPreferencesLocation()
        if dir:
            cd = cd.replace(FreeCAD.ParamGet(prefs).GetString("DefaultOutputPath", ""),'/tmp').replace('\\','/')

    if getFoamRuntime() == "MinGW":
        cmdline = [os.environ['COMSPEC'], '/V:ON', '/C', source + cd + cmd]
        return cmdline

    if getFoamRuntime() == "PosixDocker":
        global docker_container
        if docker_container.container_id is None:
            if startDocker():
                return("echo docker failure") # Need to return a string - shouldn't actually be used
        if docker_container.output_path_used!=FreeCAD.ParamGet(prefs).GetString("DefaultOutputPath", ""):
            print("Output path changed - restarting container")
            docker_container.start_container()
        if platform.system() == 'Windows' and FreeCAD.ParamGet(prefs).GetString("DefaultOutputPath", "")[:5]=='\\\\wsl' and cmd[:5] == './All':
            cmd = 'chmod 744 {0} && {0}'.format(cmd)  # If using windows wsl$ output directory, need to make the command executable
        if 'podman' in docker_container.docker_cmd:
            cmd = f'export OMPI_ALLOW_RUN_AS_ROOT=1 && export OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1 && {cmd}'
        cmdline = [docker_container.docker_cmd, 'exec', docker_container.container_id, 'bash', '-c', source + cd + cmd]
        print('Using command: ' + ' '.join(cmdline))
        return cmdline

    if getFoamRuntime() == "WindowsDocker":
        foamVersion = os.path.split(installation_path)[-1].lstrip('v')
        cmdline = ['powershell.exe',
                   'docker-machine.exe start default; '
                   'docker-machine.exe env --shell powershell default | Invoke-Expression; '
                   'docker start of_{}; '.format(foamVersion) +
                   'docker exec --privileged of_{} '.format(foamVersion) +
                   'bash -c "su -c \'' +  # $ -> `$: escaping for powershell
                   (cd + cmd).replace('$', '`$').replace('"', '\\`"') + # Escape quotes for powershell and also cmdline to bash
                   '\' -l ofuser"']
        return cmdline
    elif getFoamRuntime() == "BashWSL":
        cmdline = ['bash', '-c', source + cd + cmd]
        return cmdline
    elif getFoamRuntime().startswith("BlueCFD"):
        # Set-up necessary for running a command - only needs doing once, but to be safe...
        if getFoamRuntime() == "BlueCFD2":
            inst_path = "{}\\..".format(installation_path)
        else:
            inst_path = "{}".format(installation_path)
        short_bluecfd_path = getShortWindowsPath(inst_path)
        with open('{}\\msys64\\home\\ofuser\\.blueCFDOrigin'.format(inst_path), "w") as f:
            f.write(short_bluecfd_path)
            f.close()
        srcdir = '{}\\msys64\\mingw64\\bin'.format(inst_path)
        destdir1 = None
        destdir2 = None
        with os.scandir('{}'.format(inst_path)) as dirs:
            for dir in dirs:
                if dir.is_dir() and dir.name.startswith('OpenFOAM-'):
                    destdir1 = os.path.join(inst_path, dir.name, 'platforms\\mingw_w64GccDPInt32Opt\\bin')
                if dir.is_dir() and dir.name.startswith('ofuser-of'):
                    destdir2 = os.path.join(inst_path, dir.name, 'platforms\\mingw_w64GccDPInt32Opt\\bin')
        if not destdir1 or not destdir2:
            cfdError("Unable to find directories 'OpenFOAM-*' and 'ofuser-of*' in path {}. "
                     "Possible error in BlueCFD installation.".format(inst_path))
        try:
            file = 'libstdc++-6.dll'
            if destdir1 and not os.path.isfile(os.path.join(destdir1, file)):
                shutil.copy(os.path.join(srcdir, file), os.path.join(destdir1, file))
            if destdir2 and not os.path.isfile(os.path.join(destdir2, file)):
                shutil.copy(os.path.join(srcdir, file), os.path.join(destdir2, file))
            file = 'libgomp-1.dll'
            if not os.path.isfile(os.path.join(destdir1, file)):
                shutil.copy(os.path.join(srcdir, file), os.path.join(destdir1, file))
            if not os.path.isfile(os.path.join(destdir2, file)):
                shutil.copy(os.path.join(srcdir, file), os.path.join(destdir2, file))
        except IOError as err:
            cfdError("Unable to copy file {} from directory {} to {} and {}: {}\n"
                     "Try running FreeCAD again with administrator privileges, or copy the file manually."
                     .format(file, srcdir, destdir1, destdir2, str(err)))

        # Note: Prefixing bash call with the *short* path can prevent errors due to spaces in paths
        # when running linux tools - specifically when building
        cmdline = ['{}\\msys64\\usr\\bin\\bash'.format(short_bluecfd_path), '--login', '-O', 'expand_aliases', '-c',
                   cd + cmd]
        return cmdline
    else:
        cmdline = ['bash', '-c', source + cd + cmd]
        return cmdline


def runFoamCommand(cmdline, case=None):
    """
    Run a command in the OpenFOAM environment and wait until finished. Return output as (stdout, stderr, combined)
        Also print output as we go.
        cmdline - The command line to run as a string
              e.g. transformPoints -scale "(0.001 0.001 0.001)"
        case - Case directory or path
    """
    proc = CfdSynchronousFoamProcess()
    exit_code = proc.run(cmdline, case)
    # Reproduce behaviour of failed subprocess run
    if exit_code:
        raise subprocess.CalledProcessError(exit_code, cmdline)
    return proc.output, proc.outputErr, proc.outputAll


def startFoamApplication(cmd, case, log_name='', finished_hook=None, stdout_hook=None, stderr_hook=None):
    """
    Run command cmd in OpenFOAM environment, sending output to log file.
        Returns a CfdConsoleProcess object after launching
        cmd  - List or string with the application being the first entry followed by the options.
              e.g. ['transformPoints', '-scale', '"(0.001 0.001 0.001)"']
        case - Case path
        log_name - File name to pipe output to, if not None. If zero-length string, will generate automatically
            as log.<application> where <application> is the first element in cmd.
    """
    if isinstance(cmd, list) or isinstance(cmd, tuple):
        cmds = cmd
    elif isinstance(cmd, str):
        cmds = cmd.split(' ')  # Insensitive to incorrect split like space and quote
    else:
        raise Exception("Error: Application and options must be specified as a list or tuple.")

    if log_name == '':
        app = cmds[0].rsplit('/', 1)[-1]
        logFile = "log.{}".format(app)
    else:
        logFile = log_name

    cmdline = ' '.join(cmds)  # Space to separate options
    # Pipe to log file and terminal
    if logFile:
        cmdline += " 1> >(tee -a " + logFile + ") 2> >(tee -a " + logFile + " >&2)"
        # Tee appends to the log file, so we must remove first. Can't do directly since
        # paths may be specified using variables only available in foam runtime environment.
        cmdline = "{{ rm -f {}; {}; }}".format(logFile, cmdline)

    proc = CfdConsoleProcess(finished_hook=finished_hook, stdout_hook=stdout_hook, stderr_hook=stderr_hook)
    if logFile:
        print("Running ", ' '.join(cmds), " -> ", logFile)
    else:
        print("Running ", ' '.join(cmds))

    proc.start(makeRunCommand(cmdline, case), env_vars=getRunEnvironment())
    if not proc.waitForStarted():
        raise Exception("Unable to start command " + ' '.join(cmds))
    return proc


def runFoamApplication(cmd, case, log_name=''):
    """
    Same as startFoamApplication, but waits until complete. Returns exit code.
    """
    proc = startFoamApplication(cmd, case, log_name)
    proc.waitForFinished()
    return proc.exitCode()


def checkCfdDependencies(msgFn):
    FC_MAJOR_VER_REQUIRED = 0
    FC_MINOR_VER_REQUIRED = 20
    FC_PATCH_VER_REQUIRED = 0
    FC_COMMIT_REQUIRED = 29177

    CF_MAJOR_VER_REQUIRED = 1
    CF_MINOR_VER_REQUIRED = 21

    HISA_MAJOR_VER_REQUIRED = 1
    HISA_MINOR_VER_REQUIRED = 11
    HISA_PATCH_VER_REQUIRED = 3

    MIN_FOUNDATION_VERSION = 9
    MIN_OCFD_VERSION = 2206
    MIN_MINGW_VERSION = 2206

    MAX_FOUNDATION_VERSION = 11
    MAX_OCFD_VERSION = 2312
    MAX_MINGW_VERSION = 2212

    message = ""
    FreeCAD.Console.PrintMessage(
        translate("Console", "Checking CFD workbench dependencies...\n")
    )

    # Check FreeCAD version
    print("Checking FreeCAD version")
    ver = FreeCAD.Version()
    major_ver = int(ver[0])
    minor_vers = ver[1].split('.')
    minor_ver = int(minor_vers[0])
    if minor_vers[1:] and minor_vers[1]:
        patch_ver = int(minor_vers[1])
    else:
        patch_ver = 0
    gitver = ver[2].split()
    if gitver:
        gitver = gitver[0]
    if gitver and gitver != 'Unknown':
        gitver = int(gitver)
    else:
        # If we don't have the git version, assume it's OK.
        gitver = FC_COMMIT_REQUIRED

    msgFn("FreeCAD version: {}.{}".format(major_ver, minor_ver))
    if (major_ver < FC_MAJOR_VER_REQUIRED or
        (major_ver == FC_MAJOR_VER_REQUIRED and
         (minor_ver < FC_MINOR_VER_REQUIRED or
          (minor_ver == FC_MINOR_VER_REQUIRED and
           (patch_ver < FC_PATCH_VER_REQUIRED or
            (patch_ver == FC_PATCH_VER_REQUIRED and
             gitver < FC_COMMIT_REQUIRED)))))):
        msgFn("FreeCAD version (currently {}.{}.{} ({})) must be at least {}.{}.{} ({})".format(
            int(ver[0]), minor_ver, patch_ver, gitver,
            FC_MAJOR_VER_REQUIRED, FC_MINOR_VER_REQUIRED, FC_PATCH_VER_REQUIRED, FC_COMMIT_REQUIRED))

    # check openfoam
    print("Checking for OpenFOAM:")
    try:
        foam_dir = getFoamDir()
        msgFn("System: {}\nRuntime: {}\nOpenFOAM directory: {}".format(
            platform.system(), getFoamRuntime(), foam_dir if len(foam_dir) else "(system installation)"))
    except IOError as e:
        msgFn("Could not find OpenFOAM installation: " + str(e))
    else:
        if foam_dir is None:
            msgFn("OpenFOAM installation path not set and OpenFOAM environment neither pre-loaded before " + \
                  "running FreeCAD nor detected in standard locations")
        else:
            if getFoamRuntime() == "PosixDocker":
                if startDocker():
                    return
            try:
                if getFoamRuntime() == "MinGW":
                    foam_ver = runFoamCommand("echo !WM_PROJECT_VERSION!")[0]
                else:
                    foam_ver = runFoamCommand("echo $WM_PROJECT_VERSION")[0]
            except Exception as e:
                msgFn("OpenFOAM installation found, but unable to run command: " + str(e))
                raise
            else:
                foam_ver = foam_ver.rstrip()
                if foam_ver:
                    foam_ver = foam_ver.split()[-1]
                msgFn("OpenFOAM version: " + foam_ver.lstrip('v'))
                if foam_ver and foam_ver != 'dev' and foam_ver != 'plus':
                    try:
                        # Isolate major version number
                        foam_ver = foam_ver.lstrip('v')
                        foam_ver = int(foam_ver.split('.')[0])
                        if getFoamRuntime() == "MinGW":
                            if foam_ver < MIN_MINGW_VERSION or foam_ver > MAX_MINGW_VERSION:
                                msgFn("OpenFOAM version " + str(foam_ver) + \
                                      " is not currently supported with MinGW installation")
                        if foam_ver >= 1000:  # Plus version
                            if foam_ver < MIN_OCFD_VERSION:
                                msgFn("OpenFOAM version " + str(foam_ver) + " is outdated:\n" + \
                                      "Minimum version " + str(MIN_OCFD_VERSION) + " or " + str(MIN_FOUNDATION_VERSION) + \
                                      " required for full functionality")
                            if foam_ver > MAX_OCFD_VERSION:
                                msgFn("OpenFOAM version " + str(foam_ver) + " is not yet supported:\n" + \
                                      "Last tested version is " + str(MAX_OCFD_VERSION))
                        else:  # Foundation version
                            if foam_ver < MIN_FOUNDATION_VERSION:
                                msgFn("OpenFOAM version " + str(foam_ver) + " is outdated:\n" + \
                                      "Minimum version " + str(MIN_OCFD_VERSION) + " or " + str(MIN_FOUNDATION_VERSION) + \
                                      " required for full functionality")
                            if foam_ver > MAX_FOUNDATION_VERSION:
                                msgFn("OpenFOAM version " + str(foam_ver) + " is not yet supported:\n" + \
                                      "Last tested version is " + str(MAX_FOUNDATION_VERSION))
                    except ValueError:
                        msgFn("Error parsing OpenFOAM version string " + foam_ver)
                # Check for wmake
                if getFoamRuntime() != "MinGW" and getFoamRuntime() != "PosixDocker":
                    try:
                        runFoamCommand("wmake -help")
                    except subprocess.CalledProcessError:
                        msgFn("OpenFOAM installation does not include 'wmake'. " + \
                              "Installation of cfMesh and HiSA will not be possible. " + \
                              "An OpenFOAM 'development' package should be installed if available.")

                # Check for mpiexec
                try:
                    if getFoamRuntime() == "MinGW":
                        runFoamCommand("mpiexec -help")
                    else:
                        if platform.system() == "Windows":
                            runFoamCommand('"$(which mpiexec)" -help')
                        else:
                            runFoamCommand("mpiexec --help")
                except subprocess.CalledProcessError:
                    msgFn("MPI was not found. " + \
                            "Parallel execution will not be possible.")

                # Check for cfMesh
                try:
                    cfmesh_ver = runFoamCommand("cartesianMesh -version")[0]
                    cfmesh_ver = cfmesh_ver.rstrip().split()[-1]
                    msgFn("cfMesh-CfdOF version: " + cfmesh_ver)
                    cfmesh_ver = cfmesh_ver.split('.')
                    if (not cfmesh_ver or len(cfmesh_ver) != 2 or
                        int(cfmesh_ver[0]) < CF_MAJOR_VER_REQUIRED or
                        (int(cfmesh_ver[0]) == CF_MAJOR_VER_REQUIRED and
                         int(cfmesh_ver[1]) < CF_MINOR_VER_REQUIRED)):
                        msgFn("cfMesh-CfdOF version {}.{} required".format(CF_MAJOR_VER_REQUIRED,
                                                                           CF_MINOR_VER_REQUIRED))
                except subprocess.CalledProcessError:
                    msgFn("cfMesh (CfdOF version) not found")

                # Check for HiSA
                try:
                    hisa_ver = runFoamCommand("hisa -version")[0]
                    hisa_ver = hisa_ver.rstrip().split()[-1]
                    msgFn("HiSA version: " + hisa_ver)
                    hisa_ver = hisa_ver.split('.')
                    if (not hisa_ver or len(hisa_ver) != 3 or
                        int(hisa_ver[0]) < HISA_MAJOR_VER_REQUIRED or
                        (int(hisa_ver[0]) == HISA_MAJOR_VER_REQUIRED and
                         (int(hisa_ver[1]) < HISA_MINOR_VER_REQUIRED or
                          (int(hisa_ver[1]) == HISA_MINOR_VER_REQUIRED and
                           int(hisa_ver[2]) < HISA_PATCH_VER_REQUIRED)))):
                        msgFn("HiSA version {}.{}.{} required".format(HISA_MAJOR_VER_REQUIRED,
                                                                      HISA_MINOR_VER_REQUIRED,
                                                                      HISA_PATCH_VER_REQUIRED))
                except subprocess.CalledProcessError:
                    msgFn("HiSA not found")

        # Check for paraview
        print("Checking for paraview:")
        paraview_cmd = getParaviewExecutable()
        failed = False
        if not paraview_cmd:
            paraview_cmd = 'paraview'
            # If not found, try to run from the OpenFOAM environment, in case a bundled version is
            # available from there
            try:
                runFoamCommand('which paraview')
            except subprocess.CalledProcessError:
                failed = True
        if failed or not os.path.isfile(paraview_cmd):
            msgFn("Paraview executable '" + paraview_cmd + "' not found.")
        else:
            msgFn("Paraview executable: {}".format(paraview_cmd))
            from PySide.QtCore import QProcess, QTextStream
            proc = QProcess()
            proc.setProgram(paraview_cmd)
            proc.setArguments(['--version'])
            env = QtCore.QProcessEnvironment.systemEnvironment()
            removeAppimageEnvironment(env)
            proc.setProcessEnvironment(env)
            proc.start()
            if proc.waitForFinished():
                pvversion = proc.readAllStandardOutput()
                pvversion = QTextStream(pvversion).readAll().split()
                # The --version flag doesn't seem to work on Winodws, so quietly ignore if nothing returned
                if len(pvversion):
                    pvversion = pvversion[-1].rstrip()
                    msgFn("Paraview version: " + pvversion)
                    versionlist = pvversion.split(".")
                    if int(versionlist[0]) < 5:
                        msgFn("Paraview version is older than minimum required (5)")
            else:
                msgFn("Unable to run paraview")

        # Check for paraview python support
        if not failed:
            failed = False
            paraview_cmd = getParaviewExecutable()
            if not paraview_cmd:
                pvpython_cmd = 'pvpython'
                # If not found, try to run from the OpenFOAM environment, in case a bundled version is
                # available from there
                try:
                    runFoamCommand('which pvpython')
                except subprocess.CalledProcessError:
                    failed = True
            else:
                if platform.system() == 'Windows':
                    pvpython_cmd = paraview_cmd.rstrip('paraview.exe')+'pvpython.exe'
                elif platform.system() == "Darwin":
                    pvpython_cmd = paraview_cmd.rstrip('paraview').rstrip('/')
                    dirs = os.path.split(pvpython_cmd)
                    if dirs[1] == 'MacOS':
                        pvpython_cmd = os.path.join(dirs[0], 'bin', 'pvpython')
                    else:
                        pvpython_cmd = os.path.join(paraview_cmd, 'pvpython')
                else:
                    pvpython_cmd = paraview_cmd.rstrip('paraview')+'pvpython'
            if failed or not os.path.isfile(pvpython_cmd):
                msgFn("Python support in paraview not found. Please install paraview python packages.")

    print("Checking Plot module:")

    try:
        import matplotlib
    except ImportError:
        msgFn("Could not load matplotlib package (required by Plot module)")

    try:
        from FreeCAD.Plot import Plot  # Built-in plot module
    except ImportError:
        msgFn("Could not load Plot module")

    print("Checking for gmsh:")
    # check that gmsh version 2.13 or greater is installed
    gmshversion = ""
    gmsh_exe = getGmshExecutable()
    if gmsh_exe is None:
        msgFn("gmsh not found (optional)")
    else:
        msgFn("gmsh executable: " + gmsh_exe)
        try:
            # Needs to be runnable from OpenFOAM environment
            gmshversion = runFoamCommand('"' + gmsh_exe + '"' + " -version")[2]
        except (OSError, subprocess.CalledProcessError):
            msgFn("gmsh could not be run from OpenFOAM environment")
        if getFoamRuntime() == "MinGW":
            # For some reason the output of gmsh -version gets lost when running via the command prompt, so try to run
            # directly to get hold of this
            from PySide.QtCore import QProcess, QTextStream
            proc = QProcess()
            proc.setProgram(gmsh_exe)
            proc.setArguments(['-version'])
            proc.start()
            if proc.waitForFinished():
                gmshversion = proc.readAllStandardOutput() + proc.readAllStandardError()
                gmshversion = QTextStream(gmshversion).readAll()
        gmshversion = gmshversion.rstrip()
        msgFn("gmsh version: " + gmshversion)
        if len(gmshversion) > 1:
            # Only the last line contains gmsh version number
            gmshversion = gmshversion.split()
            gmshversion = gmshversion[-1]
            versionlist = gmshversion.split(".")
            if int(versionlist[0]) < 2 or (int(versionlist[0]) == 2 and int(versionlist[1]) < 13):
                msgFn("gmsh version is older than minimum required (2.13)")

    msgFn("Completed CFD dependency check")


def getParaviewExecutable():
    # If path of paraview executable specified, use that
    paraview_cmd = getParaviewPath()
    if not paraview_cmd:
        # If using blueCFD, use paraview supplied
        if getFoamRuntime() == 'BlueCFD':
            paraview_cmd = '{}\\AddOns\\ParaView\\bin\\paraview.exe'.format(getFoamDir())
        elif getFoamRuntime() == 'BlueCFD2':
            paraview_cmd = '{}\\..\\AddOns\\ParaView\\bin\\paraview.exe'.format(getFoamDir())
        else:
            # Check the defaults
            paraview_cmd = findInDefaultPaths(PARAVIEW_PATH_DEFAULTS)
    if not paraview_cmd:
        # Otherwise, see if the command 'paraview' is in the path.
        paraview_cmd = shutil.which('paraview')
    return paraview_cmd


def getGmshExecutable():
    # If path of gmsh executable specified, use that
    gmsh_cmd = getGmshPath()
    if not gmsh_cmd:
        # On Windows, use gmsh supplied
        if platform.system() == "Windows":
            # Use forward slashes to avoid escaping problems
            gmsh_cmd = '/'.join([FreeCAD.getHomePath().rstrip('/'), 'bin', 'gmsh.exe'])
    if not gmsh_cmd:
        # Otherwise, see if the command 'gmsh' is in the path.
        gmsh_cmd = shutil.which("gmsh")
    gmsh_cmd = os.path.normpath(gmsh_cmd)
    if getFoamRuntime() == "PosixDocker":
        gmsh_cmd='gmsh'
    return gmsh_cmd


def startParaview(case_path, script_name, console_message_fn):
    proc = QtCore.QProcess()
    paraview_cmd = getParaviewExecutable()
    arg = '--script={}'.format(script_name)

    if not paraview_cmd:
        # If not found, try to run from the OpenFOAM environment, in case a bundled version is available from there
        paraview_cmd = "$(which paraview)"  # 'which' required due to mingw weirdness(?) on Windows
        try:
            cmds = [paraview_cmd, arg]
            cmd = ' '.join(cmds)
            console_message_fn(f"Running {cmd} at {case_path}")
            args = makeRunCommand(cmd, case_path)
            paraview_cmd = args[0]
            args = args[1:] if len(args) > 1 else []
            proc.setProgram(paraview_cmd)
            proc.setArguments([arg])
            proc.setProcessEnvironment(getRunEnvironment())
            success = proc.startDetached()
            if not success:
                raise Exception("Unable to start command " + cmd)
            console_message_fn("Paraview started")
        except QtCore.QProcess.ProcessError:
            console_message_fn("Error starting paraview")
    else:
        console_message_fn(f"Running {paraview_cmd} {arg} at {case_path}")
        proc.setProgram(paraview_cmd)
        proc.setArguments([arg])
        proc.setWorkingDirectory(case_path)
        env = QtCore.QProcessEnvironment.systemEnvironment()
        removeAppimageEnvironment(env)
        proc.setProcessEnvironment(env)
        success = proc.startDetached()
        if success:
            console_message_fn("Paraview started")
        else:
            console_message_fn("Error starting paraview")
    return success


def startGmsh(working_dir, args, console_message_fn, stdout_fn=None, stderr_fn=None):
    proc = CfdConsoleProcess(stdout_hook=stdout_fn, stderr_hook=stderr_fn)
    gmsh_cmd = getGmshExecutable()

    if not gmsh_cmd:
        console_message_fn("GMSH not found")
    else:
        console_message_fn("Running " + gmsh_cmd + " " + ' '.join(args))

        proc.start([gmsh_cmd] + args, working_dir=working_dir)
        if proc.waitForStarted():
            console_message_fn("GMSH started")
        else:
            console_message_fn("Error starting GMSH")
    return proc


def floatEqual(a, b):
    """
    Test whether a and b are equal within an absolute and relative tolerance
    """
    reltol = 10*sys.float_info.epsilon
    abstol = 1e-11  # Seems to be necessary on file read/write
    return abs(a-b) < abstol or abs(a - b) <= reltol*max(abs(a), abs(b))


def isSameGeometry(shape1, shape2):
    """
    Copy of FemMeshTools.is_same_geometry, with fixes
    """
    # Check Area, CenterOfMass because non-planar shapes might not have more than one vertex defined
    same_Vertexes = 0
    # Bugfix: below was 1 - did not work for non-planar shapes
    if len(shape1.Vertexes) == len(shape2.Vertexes) and len(shape1.Vertexes) > 0:
        # compare CenterOfMass
        # Bugfix: Precision seems to be lost on load/save
        if hasattr(shape1, "CenterOfMass") and hasattr(shape2, "CenterOfMass"):
            if not floatEqual(shape1.CenterOfMass[0], shape2.CenterOfMass[0]) or \
                    not floatEqual(shape1.CenterOfMass[1], shape2.CenterOfMass[1]) or \
                    not floatEqual(shape1.CenterOfMass[2], shape2.CenterOfMass[2]):
                return False
        if hasattr(shape1, "Area") and hasattr(shape2, "Area"):
            if not floatEqual(shape1.Area, shape2.Area):
                return False
        # compare the Vertices
        for vs1 in shape1.Vertexes:
            for vs2 in shape2.Vertexes:
                if floatEqual(vs1.X, vs2.X) and floatEqual(vs1.Y, vs2.Y) and floatEqual(vs1.Z, vs2.Z):
                    same_Vertexes += 1
                    # Bugfix: was 'continue' - caused false-negative with repeated vertices
                    break
        if same_Vertexes == len(shape1.Vertexes):
            return True
        else:
            return False


def findElementInShape(a_shape, an_element):
    """
    Copy of FemMeshTools.find_element_in_shape, but calling isSameGeometry
    """
    # import Part
    ele_st = an_element.ShapeType
    if ele_st == 'Solid' or ele_st == 'CompSolid':
        for index, solid in enumerate(a_shape.Solids):
            # print(is_same_geometry(solid, anElement))
            if isSameGeometry(solid, an_element):
                # print(index)
                # Part.show(aShape.Solids[index])
                ele = ele_st + str(index + 1)
                return ele
        FreeCAD.Console.PrintError('Solid ' + str(an_element) + ' not found in: ' + str(a_shape) + '\n')
        if ele_st == 'Solid' and a_shape.ShapeType == 'Solid':
            print('We have been searching for a Solid in a Solid and we have not found it. In most cases this should be searching for a Solid inside a CompSolid. Check the ShapeType of your Part to mesh.')
        # Part.show(anElement)
        # Part.show(aShape)
    elif ele_st == 'Face' or ele_st == 'Shell':
        for index, face in enumerate(a_shape.Faces):
            # print(is_same_geometry(face, anElement))
            if isSameGeometry(face, an_element):
                # print(index)
                # Part.show(aShape.Faces[index])
                ele = ele_st + str(index + 1)
                return ele
    elif ele_st == 'Edge' or ele_st == 'Wire':
        for index, edge in enumerate(a_shape.Edges):
            # print(is_same_geometry(edge, anElement))
            if isSameGeometry(edge, an_element):
                # print(index)
                # Part.show(aShape.Edges[index])
                ele = ele_st + str(index + 1)
                return ele
    elif ele_st == 'Vertex':
        for index, vertex in enumerate(a_shape.Vertexes):
            # print(is_same_geometry(vertex, anElement))
            if isSameGeometry(vertex, an_element):
                # print(index)
                # Part.show(aShape.Vertexes[index])
                ele = ele_st + str(index + 1)
                return ele
    elif ele_st == 'Compound':
        FreeCAD.Console.PrintError('Compound is not supported.\n')


def matchFaces(faces1, faces2):
    """
    This function does a geometric matching of face lists much faster than doing face-by-face search
    :param faces1: List of tuples - first item is face object, second is any user data
    :param faces2: List of tuples - first item is face object, second is any user data
    :return:  A list of (data1, data2) containing the user data for any/all matching faces
    Note that faces1 and faces2 are sorted in place and can be re-used for faster subsequent searches
    """

    def compKeyFn(key):
        class K(object):
            def __init__(self, val, *args):
                self.val = key(val)

            def __eq__(self, other):
                return floatEqual(self.val, other.val)

            def __ne__(self, other):
                return not floatEqual(self.val, other.val)

            def __lt__(self, other):
                return self.val < other.val and not floatEqual(self.val, other.val)

            def __gt__(self, other):
                return self.val > other.val and not floatEqual(self.val, other.val)

            def __le__(self, other):
                return self.val < other.val or floatEqual(self.val, other.val)

            def __ge__(self, other):
                return self.val > other.val or floatEqual(self.val, other.val)

        return K

    # Sort face list by first vertex, x then y then z in case all in plane
    faces1.sort(key=compKeyFn(lambda bf: bf[0].Vertexes[0].Point.z))
    faces1.sort(key=compKeyFn(lambda bf: bf[0].Vertexes[0].Point.y))
    faces1.sort(key=compKeyFn(lambda bf: bf[0].Vertexes[0].Point.x))

    # Same on other face list
    faces2.sort(key=compKeyFn(lambda mf: mf[0].Vertexes[0].Point.z))
    faces2.sort(key=compKeyFn(lambda mf: mf[0].Vertexes[0].Point.y))
    faces2.sort(key=compKeyFn(lambda mf: mf[0].Vertexes[0].Point.x))

    # Find faces with matching first vertex
    i = 0
    j = 0
    j_match_start = 0
    matching = False
    candidate_mesh_faces = []
    while i < len(faces1) and j < len(faces2):
        bf = faces1[i][0]
        mf = faces2[j][0]
        if floatEqual(bf.Vertexes[0].Point.x, mf.Vertexes[0].Point.x):
            if floatEqual(bf.Vertexes[0].Point.y, mf.Vertexes[0].Point.y):
                if floatEqual(bf.Vertexes[0].Point.z, mf.Vertexes[0].Point.z):
                    candidate_mesh_faces.append((i, j))
                    cmp = 0
                else:
                    cmp = (-1 if bf.Vertexes[0].Point.z < mf.Vertexes[0].Point.z else 1)
            else:
                cmp = (-1 if bf.Vertexes[0].Point.y < mf.Vertexes[0].Point.y else 1)
        else:
            cmp = (-1 if bf.Vertexes[0].Point.x < mf.Vertexes[0].Point.x else 1)
        if cmp == 0:
            if not matching:
                j_match_start = j
            j += 1
            matching = True
            if j == len(faces2):
                i += 1
                j = j_match_start
                matching = False
        elif cmp < 0:
            i += 1
            if matching:
                j = j_match_start
            matching = False
        elif cmp > 0:
            j += 1
            matching = False

    # Do comprehensive matching, and reallocate to original index
    successful_candidates = []
    for k in range(len(candidate_mesh_faces)):
        i, j = candidate_mesh_faces[k]
        if isSameGeometry(faces1[i][0], faces2[j][0]):
            successful_candidates.append((faces1[i][1], faces2[j][1]))

    return successful_candidates


def makeShapeFromReferences(refs, raise_error=True):
    face_list = []
    for ref in refs:
        shapes = resolveReference(ref, raise_error)
        if len(shapes):
            face_list += [s[0] for s in shapes]
    if len(face_list) > 0:
        shape = Part.makeCompound(face_list)
        return shape
    else:
        return None


def resolveReference(r, raise_error=True):
    obj = r[0]
    if not r[1] or r[1] == ('',):
        return [(obj.Shape, (r[0], None))]
    f = []
    for rr in r[1]:
        try:
            if rr.startswith('Solid'):  # getElement doesn't work with solids for some reason
                f += [(obj.Shape.Solids[int(rr.lstrip('Solid')) - 1], (r[0], rr))]
            else:
                ff = obj.Shape.getElement(rr)
                if ff is None:
                    if raise_error:
                        raise RuntimeError("Face '{}:{}' was not found - geometry may have changed".format(r[0].Name, rr))
                else:
                    f += [(ff, (r[0], rr))]
        except Part.OCCError:
            if raise_error:
                raise RuntimeError("Face '{}:{}' was not found - geometry may have changed".format(r[0].Name, r[1]))
    return f


def setActiveAnalysis(analysis):
    from CfdOF.CfdAnalysis import CfdAnalysis
    for obj in FreeCAD.ActiveDocument.Objects:
        if hasattr(obj, 'Proxy') and isinstance(obj.Proxy, CfdAnalysis):
            obj.IsActiveAnalysis = False

    analysis.IsActiveAnalysis = True


def getActiveAnalysis():
    from CfdOF.CfdAnalysis import CfdAnalysis
    for obj in FreeCAD.ActiveDocument.Objects:
        if hasattr(obj, 'Proxy') and isinstance(obj.Proxy, CfdAnalysis):
            if obj.IsActiveAnalysis:
                return obj
    return None


def addObjectProperty(obj, prop: str, init_val, type: str, *args):
    """
    Call addProperty on the object if it does not yet exist
    """
    added = False
    if prop not in obj.PropertiesList:
        added = obj.addProperty(
            type, prop, *args
        )  # 3rd parameter  is property group, 4th parameter is property tooltip
    if type == "App::PropertyQuantity":
        # Set the unit so that the quantity will be accepted
        # Has to be repeated on load as unit gets lost
        setattr(obj, prop, Units.Unit(init_val))
    if added:
        setattr(obj, prop, init_val)
    elif type == "App::PropertyEnumeration":
        # For enumeration, re-assign the list of allowed values anyway in case some were added
        # Make sure the currently set value is unaffected by this
        curr_item = getattr(obj, prop)
        setattr(obj, prop, init_val)
        setattr(obj, prop, curr_item)
    return added


def relLenToRefinementLevel(rel_len):
    return math.ceil(math.log(1.0/rel_len)/math.log(2))


def importMaterials():
    materials = {}
    material_name_path_list = []

    # Store the defaults inside the module directory rather than the resource dir
    # system_mat_dir = FreeCAD.getResourceDir() + "/Mod/Material/FluidMaterialProperties"
    system_mat_dir = os.path.join(getModulePath(), "Data", "CfdFluidMaterialProperties")
    material_name_path_list = material_name_path_list + addMatDir(system_mat_dir, materials)
    return materials, material_name_path_list


def addMatDir(mat_dir, materials):
    import importFCMat
    mat_file_extension = ".FCMat"
    ext_len = len(mat_file_extension)
    dir_path_list = glob.glob(mat_dir + '/*' + mat_file_extension)
    material_name_path_list = []
    for a_path in dir_path_list:
        material_name = os.path.basename(a_path[:-ext_len])
        materials[a_path] = importFCMat.read(a_path)
        material_name_path_list.append([material_name, a_path])
    material_name_path_list.sort()

    return material_name_path_list


def propsToDict(obj):
    """
    Convert an object's properties to dictionary entries, converting any PropertyQuantity to float in SI units and
    vectors/positions to tuples
    """

    d = {}
    for k in obj.PropertiesList:
        if obj.getTypeIdOfProperty(k) in QUANTITY_PROPERTIES:
            q = Units.Quantity(getattr(obj, k))
            # q.Value is in FreeCAD internal units, which is same as SI except for mm instead of m and deg instead of
            # rad
            d[k] = q.Value/1000**q.Unit.Signature[0]/(180/math.pi)**q.Unit.Signature[7]
        elif obj.getTypeIdOfProperty(k) == 'App::PropertyPosition':
            d[k] = tuple(Units.Quantity(p, Units.Length).getValueAs('m') for p in getattr(obj, k))
        elif obj.getTypeIdOfProperty(k) == 'App::PropertyVector':
            d[k] = tuple(p for p in getattr(obj, k))
        else:
            d[k] = getattr(obj, k)
    return d


def openFileManager(case_path):
    case_path = os.path.abspath(case_path)
    if platform.system() == 'Darwin':
        subprocess.Popen(['open', '--', case_path])
    elif platform.system() == 'Linux':
        subprocess.Popen(['xdg-open', case_path])
    elif platform.system() == 'Windows':
        subprocess.Popen(['explorer', case_path])


def writePatchToStl(solid_name, face_mesh, fid, scale=1):
    fid.write("solid {}\n".format(solid_name))
    for face in face_mesh.Facets:
        n = face.Normal
        fid.write(" facet normal {} {} {}\n".format(n[0], n[1], n[2]))
        fid.write("  outer loop\n")
        for i in range(3):
            p = [i * scale for i in face.Points[i]]
            fid.write("   vertex {} {} {}\n".format(p[0], p[1], p[2]))
        fid.write("  endloop\n")
        fid.write(" endfacet\n")
    fid.write("endsolid {}\n".format(solid_name))


def enableLayoutRows(layout, selected_rows):
    if isinstance(layout, QFormLayout):
        for rowi in range(layout.count()):
            for role in [QFormLayout.LabelRole, QFormLayout.FieldRole, QFormLayout.SpanningRole]:
                item = layout.itemAt(rowi, role)
                if item:
                    if isinstance(item, QtGui.QWidgetItem):
                        item.widget().setVisible(selected_rows is None or rowi in selected_rows)
    elif isinstance(layout, QGridLayout):
        for rowi in range(layout.rowCount()):
            for coli in range(layout.columnCount()):
                item = layout.itemAtPosition(rowi, coli)
                if item:
                    if isinstance(item, QtGui.QWidgetItem):
                        item.widget().setVisible(selected_rows is None or rowi in selected_rows)
    else:
        for rowi in range(layout.count()):
            item = layout.itemAt(rowi)
            if item:
                if isinstance(item, QtGui.QWidgetItem):
                    item.widget().setVisible(selected_rows is None or rowi in selected_rows)


def clearCase(case_path, backup_path=None):
    """
    Remove and recreate contents of the case directory, optionally backing up
    Does not remove the directory entry itself as this requires paraview to be reloaded
    """
    if backup_path:
        os.makedirs(backup_path)  #mkdir -p
    if os.path.isdir(case_path):
        for entry in os.scandir(case_path):
            if backup_path:
                dest = os.path.join(backup_path, entry.name)
                shutil.move(entry.path, dest)
            else:
                if entry.is_dir():
                    shutil.rmtree(entry.path)
                else:
                    os.remove(entry.path)
    else:
        os.makedirs(case_path)  # mkdir -p


def executeMacro(macro_name):
    macro_contents = "import FreeCAD\nimport FreeCADGui\nimport FreeCAD as App\nimport FreeCADGui as Gui\n"
    macro_contents += open(macro_name).read()
    exec(compile(macro_contents, macro_name, 'exec'), {'__file__': macro_name})


def reloadWorkbench():
    """ Code obtained from David_D at https://forum.freecad.org/viewtopic.php?t=34658#p291438 """
    reload_module = CfdOF

    fn = reload_module.__file__
    fn_dir = os.path.dirname(fn) + os.sep
    module_visit = {fn}
    del fn

    def reloadWorkbenchRecursive(module):
        importlib.reload(module)

        for module_child in vars(module).values():
            if isinstance(module_child, types.ModuleType):
                fn_child = getattr(module_child, "__file__", None)
                if (fn_child is not None) and fn_child.startswith(fn_dir):
                    if fn_child not in module_visit:
                        FreeCAD.Console.PrintMessage("Reloading: {}, from: {}\n".format(
                            fn_child, module
                            ))
                        module_visit.add(fn_child)
                        reloadWorkbenchRecursive(module_child)

    return reloadWorkbenchRecursive(reload_module)


class CfdSynchronousFoamProcess:
    def __init__(self):
        self.process = CfdConsoleProcess(stdout_hook=self.readOutput, stderr_hook=self.readError)
        self.output = ""
        self.outputErr = ""
        self.outputAll = ""

    def run(self, cmdline, case=None):
        if getFoamRuntime() == "PosixDocker" and ' pull ' not in cmdline:
            if startDocker():
                return 1
        self.process.start(makeRunCommand(cmdline, case), env_vars=getRunEnvironment())
        if not self.process.waitForFinished():
            raise Exception("Unable to run command " + cmdline)
        return self.process.exitCode()

    def readOutput(self, output):
        self.output += output
        self.outputAll += output

    def readError(self, output):
        self.outputErr += output
        self.outputAll += output

# Only one container is needed. Start one for the CfdOF workbench as required
class DockerContainer:
    container_id = None
    usedocker = False
    output_path_used = None
    docker_cmd = None

    def __init__(self):
        self.image_name = None
        import shutil

        if shutil.which('podman') is not None:
            self.docker_cmd = shutil.which('podman')
        elif shutil.which('docker') is not None:
            self.docker_cmd = shutil.which('docker')
        else:
            self.docker_cmd = None

        if self.docker_cmd is not None:
            self.docker_cmd = self.docker_cmd.split(os.path.sep)[-1]

    def start_container(self):
        prefs = getPreferencesLocation()
        self.image_name = FreeCAD.ParamGet(prefs).GetString("DockerURL", "")
        output_path = FreeCAD.ParamGet(prefs).GetString("DefaultOutputPath", "")

        if not output_path:
            output_path = tempfile.gettempdir()
        output_path = os.path.normpath(output_path)

        if not os.path.isdir(output_path):
            print("Default output directory not found")
            return 1

        if self.container_id is not None:
            print("Attempting to start container but id already set")
            print("Clear container first...")
            self.clean_container()

        if self.image_name == "":
            print("Docker image name not set")
            return 1

        if self.docker_cmd == None:
            print("Need to install either podman or docker")
            return 1

        if platform.system() == 'Windows':
            out_d = output_path.split(os.sep)
            if len(out_d)>2 and out_d[2][:3] == 'wsl':
                output_path = '/' + '/'.join(out_d[4:])

        if 'podman' in self.docker_cmd: # podman runs without root privileges, so the user in the container can be root.
            usr_str = '-u0:0'
        else:
            if platform.system() == 'Windows':
                usr_str = "-u1000:1000" # Windows under docker
            else:
                usr_str = "-u{}:{}".format(os.getuid(),os.getgid())

        cmd = [self.docker_cmd, "run", "-t", "-d", usr_str, "-v" + output_path + ":/tmp", self.image_name]

        if 'podman' in self.docker_cmd:
            cmd.insert(2, "--security-opt=label=disable") # Allows /tmp to be mounted to the podman container

        # if 'docker' in self.docker_cmd:
        #     cmd = cmd.replace('docker.io/','')

        print("Starting docker with command:", ' '.join(cmd))
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        while proc.poll() is None:
            QApplication.processEvents()
            time.sleep(0.1)

        output, _ = proc.communicate()
        if proc.returncode:
            print("Command exited with error code {}".format(proc.returncode))
            if output is not None:
                print("Command output:", output.decode('utf-8').strip())
            return 1
        self.container_id = output.decode('utf-8').split('\n')[0][:12]
        print("Docker container started with id:", self.container_id)

        self.output_path_used = FreeCAD.ParamGet(prefs).GetString("DefaultOutputPath", "")
        return 0

    def clean_container(self):
        if self.container_id is not None:
            cmd = [self.docker_cmd, "stop", self.container_id]
            print("Stopping docker with command:", ' '.join(cmd))
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            output, _ = proc.communicate()
            if proc.returncode:
                print("Command exited with error code {}".format(proc.returncode))
                if output is not None:
                    print("Command output:", output.decode('utf-8').strip())
                return 1
            self.container_id = None
