# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2015 - FreeCAD Developers                               *
# *   Copyright (c) 2015 - Qingfeng Xia <qingfeng xia eng.ox.ac.uk>         *
# *   Copyright (c) 2017 Johan Heyns (CSIR) <jheyns@csir.co.za>             *
# *   Copyright (c) 2017 Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>          *
# *   Copyright (c) 2017 Alfred Bogaers (CSIR) <abogaers@csir.co.za>        *
# *   Copyright (c) 2019-2021 Oliver Oxtoby <oliveroxtoby@gmail.com>        *
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

# Utility functions like mesh exporting, shared by any CFD solver

from __future__ import print_function

import FreeCAD
from FreeCAD import Units
import CfdConsoleProcess
import Part
import os
import os.path
import shutil
import tempfile
import numbers
import platform
import subprocess
import sys
import math
from datetime import timedelta
import BOPTools
from BOPTools import SplitFeatures
if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtGui
    from PySide import QtCore

# Some standard install locations that are searched if an install directory is not specified
FOAM_DIR_DEFAULTS = {"Windows": ["C:\\Program Files\\ESI-OpenCFD\\OpenFOAM\\v2012",
                                 "~\\AppData\\Roaming\\ESI-OpenCFD\\OpenFOAM\\v2012",
                                 "C:\\Program Files (x86)\\ESI\\OpenFOAM\\v2012",
                                 "C:\\Program Files (x86)\\ESI\\OpenFOAM\\v2006",
                                 "C:\\Program Files (x86)\\ESI\\OpenFOAM\\v1912",
                                 "C:\\Program Files\\blueCFD-Core-2020\\OpenFOAM-8"],
                     "Linux": ["/usr/lib/openfoam/openfoam2012", "/usr/lib/openfoam/openfoam2006",
                               "/opt/openfoam8", "/opt/openfoam7", "/opt/openfoam6", "/opt/openfoam5",
                               "~/OpenFOAM/OpenFOAM-8.x", "~/OpenFOAM/OpenFOAM-8.0",
                               "~/OpenFOAM/OpenFOAM-7.x", "~/OpenFOAM/OpenFOAM-7.0",
                               "~/OpenFOAM/OpenFOAM-6.x", "~/OpenFOAM/OpenFOAM-6.0",
                               "~/OpenFOAM/OpenFOAM-5.x", "~/OpenFOAM/OpenFOAM-5.0",
                               "~/OpenFOAM/OpenFOAM-4.x", "~/OpenFOAM/OpenFOAM-4.0", "~/OpenFOAM/OpenFOAM-4.1",
                               "~/OpenFOAM/OpenFOAM-dev"],
                     "Darwin": ["~/OpenFOAM/OpenFOAM-8.x", "~/OpenFOAM/OpenFOAM-8.0",
                                "~/OpenFOAM/OpenFOAM-7.x", "~/OpenFOAM/OpenFOAM-7.0",
                                "~/OpenFOAM/OpenFOAM-6.x", "~/OpenFOAM/OpenFOAM-6.0",
                                "~/OpenFOAM/OpenFOAM-5.x", "~/OpenFOAM/OpenFOAM-5.0",
                                "~/OpenFOAM/OpenFOAM-4.x", "~/OpenFOAM/OpenFOAM-4.0", "~/OpenFOAM/OpenFOAM-4.1",
                                "~/OpenFOAM/OpenFOAM-dev"]
                     }
PARAVIEW_PATH_DEFAULTS = {
                    "Windows": ["C:\\Program Files\\ParaView 5.5.2-Qt5-Windows-64bit\\bin\\paraview.exe",
                                "C:\\Program Files\\ParaView 5.5.2-Qt5-MPI-Windows-64bit\\bin\\paraview.exe"],
                    "Linux": [],
                    "Darwin": []
                    }


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
    """ Return CfdAnalysis object to which this obj belongs in the tree """
    return obj.getParentGroup()


def getPhysicsModel(analysis_object):
    isPresent = False
    for i in analysis_object.Group:
        if "PhysicsModel" in i.Name:
            physicsModel = i
            isPresent = True
    if not isPresent:
        physicsModel = None
    return physicsModel


def getMeshObject(analysis_object):
    isPresent = False
    meshObj = []
    if analysis_object:
        members = analysis_object.Group
    else:
        members = FreeCAD.activeDocument().Objects
    from CfdMesh import _CfdMesh
    for i in members:
        if hasattr(i, "Proxy") and isinstance(i.Proxy, _CfdMesh):
            if isPresent:
                FreeCAD.Console.PrintError("Analysis contains more than one mesh object.")
            else:
                meshObj.append(i)
                isPresent = True
    if not isPresent:
        meshObj = [None]
    return meshObj[0]


def getPorousZoneObjects(analysis_object):
    return [i for i in analysis_object.Group if i.Name.startswith('PorousZone')]


def getInitialisationZoneObjects(analysis_object):
    return [i for i in analysis_object.Group if i.Name.startswith('InitialisationZone')]


def getZoneObjects(analysis_object):
    return [i for i in analysis_object.Group if 'Zone' in i.Name]


def getInitialConditions(analysis_object):
    from CfdInitialiseFlowField import _CfdInitialVariables
    for i in analysis_object.Group:
        if isinstance(i.Proxy, _CfdInitialVariables):
            return i
    return None


def getMaterials(analysis_object):
    return [i for i in analysis_object.Group
            if i.isDerivedFrom('App::MaterialObjectPython')]


def getSolver(analysis_object):
    from CfdSolverFoam import _CfdSolverFoam
    for i in analysis_object.Group:
        if isinstance(i.Proxy, _CfdSolverFoam):
            return i


def getSolverSettings(solver):
    """ Convert properties into python dict, while key must begin with lower letter. """
    dict = {}
    f = lambda s: s[0].lower() + s[1:]
    for prop in solver.PropertiesList:
        dict[f(prop)] = solver.getPropertyByName(prop)
    return dict


def getCfdBoundaryGroup(analysis_object):
    group = []
    from CfdFluidBoundary import _CfdFluidBoundary
    for i in analysis_object.Group:
        if isinstance(i.Proxy, _CfdFluidBoundary):
            group.append(i)
    return group


def is_planar(shape):
    """ Return whether the shape is a planar face """
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
    from CfdMesh import _CfdMesh
    for i in analysis_object.Group:
        if hasattr(i, "Proxy") and isinstance(i.Proxy, _CfdMesh):
            return i
    return None


def getMeshRefinementObjs(mesh_obj):
    from CfdMeshRefinement import _CfdMeshRefinement
    ref_objs = []
    for obj in mesh_obj.Group:
        if hasattr(obj, "Proxy") and isinstance(obj.Proxy, _CfdMeshRefinement):
            ref_objs = ref_objs + [obj]
    return ref_objs


def getResult(analysis_object):
    for i in analysis_object.Group:
        if i.isDerivedFrom("Fem::FemResultObject"):
            return i
    return None


def get_module_path():
    """ Returns the current Cfd module path.
    Determines where this file is running from, so works regardless of whether
    the module is installed in the app's module directory or the user's app data folder.
    (The second overrides the first.)
    """
    return os.path.dirname(__file__)


# Set functions

def setCompSolid(vobj):
    """ To enable correct mesh refinement, boolean fragments are set to compSolid mode """
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
    """ Print a message to console and refresh GUI """
    FreeCAD.Console.PrintMessage(msg)
    if FreeCAD.GuiUp:
        FreeCAD.Gui.updateGui()
        FreeCAD.Gui.updateGui()


def cfdWarning(msg):
    """ Print a message to console and refresh GUI """
    FreeCAD.Console.PrintWarning(msg)
    if FreeCAD.GuiUp:
        FreeCAD.Gui.updateGui()
        FreeCAD.Gui.updateGui()


def cfdError(msg):
    """ Print a message to console and refresh GUI """
    FreeCAD.Console.PrintError(msg)
    if FreeCAD.GuiUp:
        FreeCAD.Gui.updateGui()
        FreeCAD.Gui.updateGui()


def cfdErrorBox(msg):
    """ Show message for an expected error """
    QtGui.QApplication.restoreOverrideCursor()
    if FreeCAD.GuiUp:
        QtGui.QMessageBox.critical(None, "CfdOF Workbench", msg)
    else:
        FreeCAD.Console.PrintError(msg + "\n")


def formatTimer(seconds):
    """ Put the elapsed time printout into a nice format """
    return str(timedelta(seconds=seconds)).split('.', 2)[0].lstrip('0').lstrip(':')


def setQuantity(inputField, quantity):
    """ Set the quantity (quantity object or unlocalised string) into the inputField correctly """
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
    """ Get the quantity as an unlocalised string from an inputField """
    q = inputField.property("quantity")
    return str(q)


def indexOrDefault(list, findItem, defaultIndex):
    """ Look for findItem in list, and return defaultIndex if not found """
    try:
        return list.index(findItem)
    except ValueError:
        return defaultIndex


def hide_parts_show_meshes():
    if FreeCAD.GuiUp:
        for acnstrmesh in getActiveAnalysis().Group:
            if "Mesh" in acnstrmesh.TypeId:
                aparttoshow = acnstrmesh.Name.replace("_Mesh", "")
                for apart in FreeCAD.activeDocument().Objects:
                    if aparttoshow == apart.Name:
                        apart.ViewObject.Visibility = False
                acnstrmesh.ViewObject.Visibility = True


def copyFilesRec(src, dst, symlinks=False, ignore=None):
    """ Recursively copy files from src dir to dst dir """
    if not os.path.exists(dst):
        os.makedirs(dst)
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if not os.path.isdir(s):
            shutil.copy2(s, d)


def getPatchType(bcType, bcSubType):
    """ Get the boundary type based on selected BC condition """
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
        elif bcSubType == 'twoDBoundingPlane':
            return 'empty'
        elif bcSubType == 'empty':
            return 'empty'
        else:
            return 'patch'
    else:
        return 'patch'


def movePolyMesh(case):
    """ Move polyMesh to polyMesh.org to ensure availability if cleanCase is ran from the terminal. """
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


def getFoamDir():
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
    installation_path = getFoamDir()
    if installation_path is None:
        raise IOError("OpenFOAM installation path not set and not detected")

    runtime = None
    if platform.system() == 'Windows':
        if os.path.exists(os.path.join(installation_path, "msys64", "home", "ofuser", ".blueCFDCore")):
            runtime = 'BlueCFD'
        elif os.path.exists(os.path.join(installation_path, "..", "msys64", "home", "ofuser", ".blueCFDCore")):
            runtime = 'BlueCFD2'
        elif os.path.exists(os.path.join(installation_path, "msys64", "home", "ofuser")):
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


def detectFoamDir():
    """ Try to guess Foam install dir from WM_PROJECT_DIR or, failing that, various defaults """
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
        for d in FOAM_DIR_DEFAULTS[platform.system()]:
            foam_dir = os.path.expanduser(d)
            if foam_dir and not os.path.exists(foam_dir):
                foam_dir = None
            else:
                break
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


def translatePath(p):
    """ Transform path to the perspective of the Linux subsystem in which OpenFOAM is run (e.g. mingw) """
    if platform.system() == 'Windows':
        return fromWindowsPath(p)
    else:
        return p


def reverseTranslatePath(p):
    """ Transform path from the perspective of the OpenFOAM subsystem to the host system """
    if platform.system() == 'Windows':
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
    Gets the short path name of a given long path.
    http://stackoverflow.com/a/23598461/200291
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
    """ Return native environment settings necessary for running on relevant platform """
    if getFoamRuntime() == "MinGW":
        return {"MSYSTEM": "MSYS",
                "USERNAME": "ofuser",
                "USER": "ofuser",
                "HOME": "/home/ofuser"}
    elif getFoamRuntime().startswith("BlueCFD"):
        return {"MSYSTEM": "MINGW64",
                "USERNAME": "ofuser",
                "USER": "ofuser",
                "HOME": "/home/ofuser"}
    else:
        return {}


def makeRunCommand(cmd, dir, source_env=True):
    """ Generate native command to run the specified Linux command in the relevant environment,
        including changing to the specified working directory if applicable
    """
    installation_path = getFoamDir()
    if installation_path is None:
        raise IOError("OpenFOAM installation directory not found")

    source = ""
    if source_env and len(installation_path):
        env_setup_script = "{}/etc/bashrc".format(installation_path)
        source = 'source "{}" && '.format(env_setup_script)
    cd = ""
    if dir:
        cd = 'cd "{}" && '.format(translatePath(dir))

    if getFoamRuntime() == "MinGW":
        # .bashrc will exit unless shell is interactive, so we have to manually load the foam bashrc
        foamVersion = os.path.split(installation_path)[-1].lstrip('v')
        cmdline = ['{}\\msys64\\usr\\bin\\bash'.format(installation_path), '--login', '-O', 'expand_aliases', '-c',
                    'echo Sourcing OpenFOAM environment...; '
                    'source $HOME/OpenFOAM/OpenFOAM-v{}/etc/bashrc; '.format(foamVersion) +
                    'export PATH=$FOAM_LIBBIN/msmpi:$FOAM_LIBBIN:$WM_THIRD_PARTY_DIR/platforms/linux64MingwDPInt32/lib:$PATH; '
                     + cd + cmd]
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
    """ Run a command in the OpenFOAM environment and wait until finished. Return output as (stdout, stderr, combined)
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


class CfdSynchronousFoamProcess:
    def __init__(self):
        self.process = CfdConsoleProcess.CfdConsoleProcess(stdoutHook=self.readOutput, stderrHook=self.readError)
        self.output = ""
        self.outputErr = ""
        self.outputAll = ""

    def run(self, cmdline, case=None):
        print("Running ", cmdline)
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


def startFoamApplication(cmd, case, log_name='', finishedHook=None, stdoutHook=None, stderrHook=None):
    """ Run command cmd in OpenFOAM environment, sending output to log file.
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
        cmdline = "{{ rm {}; {}; }}".format(logFile, cmdline)

    proc = CfdConsoleProcess.CfdConsoleProcess(finishedHook=finishedHook, stdoutHook=stdoutHook, stderrHook=stderrHook)
    if logFile:
        print("Running ", ' '.join(cmds), " -> ", logFile)
    else:
        print("Running ", ' '.join(cmds))
    proc.start(makeRunCommand(cmdline, case), env_vars=getRunEnvironment())
    if not proc.waitForStarted():
        raise Exception("Unable to start command " + ' '.join(cmds))
    return proc


def runFoamApplication(cmd, case, log_name=''):
    """ Same as startFoamApplication, but waits until complete. Returns exit code. """
    proc = startFoamApplication(cmd, case, log_name)
    proc.waitForFinished()
    return proc.exitCode()


def convertMesh(case, mesh_file, scale):
    """ Convert gmsh created UNV mesh to FOAM. A scaling of 1e-3 is prescribed as the CAD is always in mm while FOAM
    uses SI units (m). """

    if mesh_file.find(".unv") > 0:
        mesh_file = translatePath(mesh_file)
        cmdline = ['ideasUnvToFoam', '"{}"'.format(mesh_file)]
        runFoamApplication(cmdline, case)
        # changeBoundaryType(case, 'defaultFaces', 'wall')  # rename default boundary type to wall
        # Set in the correct patch types
        cmdline = ['changeDictionary']
        runFoamApplication(cmdline, case)
    else:
        raise Exception("Error: Only supporting unv mesh files.")

    if scale and isinstance(scale, numbers.Number):
        cmdline = ['transformPoints', '-scale', '"({} {} {})"'.format(scale, scale, scale)]
        runFoamApplication(cmdline, case)
    else:
        print("Error: mesh scaling ratio is must be a float or integer\n")


def checkCfdDependencies(term_print=True):
        FC_MAJOR_VER_REQUIRED = 0
        FC_MINOR_VER_REQUIRED = 18
        FC_PATCH_VER_REQUIRED = 4
        FC_COMMIT_REQUIRED = 16146

        CF_MAJOR_VER_REQUIRED = 1
        CF_MINOR_VER_REQUIRED = 6

        HISA_MAJOR_VER_REQUIRED = 1
        HISA_MINOR_VER_REQUIRED = 2
        HISA_PATCH_VER_REQUIRED = 1

        message = ""
        FreeCAD.Console.PrintMessage("Checking CFD workbench dependencies...\n")

        # Check FreeCAD version
        if term_print:
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

        if (major_ver < FC_MAJOR_VER_REQUIRED or
            (major_ver == FC_MAJOR_VER_REQUIRED and
             (minor_ver < FC_MINOR_VER_REQUIRED or
              (minor_ver == FC_MINOR_VER_REQUIRED and
               (patch_ver < FC_PATCH_VER_REQUIRED or
                (patch_ver == FC_PATCH_VER_REQUIRED and
                 gitver < FC_COMMIT_REQUIRED)))))):
            fc_msg = "FreeCAD version ({}.{}.{}) ({}) must be at least {}.{}.{} ({})".format(
                int(ver[0]), minor_ver, patch_ver, gitver,
                FC_MAJOR_VER_REQUIRED, FC_MINOR_VER_REQUIRED, FC_PATCH_VER_REQUIRED, FC_COMMIT_REQUIRED)
            if term_print:
                print(fc_msg)
            message += fc_msg + '\n'

        # check openfoam
        if term_print:
            print("Checking for OpenFOAM:")
        try:
            foam_dir = getFoamDir()
            if term_print:
                print("OpenFOAM directory: " + (foam_dir if len(foam_dir) else "(system installation)"))
                print("System: {}".format(platform.system()))
                print("Runtime: {}".format(getFoamRuntime()))
        except IOError as e:
            ofmsg = "Could not find OpenFOAM installation: " + str(e)
            if term_print:
                print(ofmsg)
            message += ofmsg + '\n'
        else:
            if foam_dir is None:
                ofmsg = "OpenFOAM installation path not set and OpenFOAM environment neither pre-loaded before " + \
                        "running FreeCAD nor detected in standard locations"
                if term_print:
                    print(ofmsg)
                message += ofmsg + '\n'
            else:
                try:
                    if getFoamRuntime() == "MinGW":
                        foam_ver = runFoamCommand("echo $FOAM_API")[0]
                    else:
                        foam_ver = runFoamCommand("echo $WM_PROJECT_VERSION")[0]
                except Exception as e:
                    runmsg = "OpenFOAM installation found, but unable to run command: " + str(e)
                    message += runmsg + '\n'
                    if term_print:
                        print(runmsg)
                    raise
                else:
                    foam_ver = foam_ver.rstrip()
                    if foam_ver:
                        foam_ver = foam_ver.split()[-1]
                    if foam_ver and foam_ver != 'dev' and foam_ver != 'plus':
                        try:
                            # Isolate major version number
                            foam_ver = foam_ver.lstrip('v')
                            foam_ver = int(foam_ver.split('.')[0])
                            if getFoamRuntime() == "MinGW":
                                if foam_ver != 2012:
                                    vermsg = "OpenFOAM version " + str(foam_ver) + " is not supported:\n" + \
                                             "Only version 2012 supported for MinGW installation"
                                    message += vermsg + "\n"
                                    if term_print:
                                        print(vermsg)
                            if foam_ver >= 1000:  # Plus version
                                if foam_ver < 1706:
                                    vermsg = "OpenFOAM version " + str(foam_ver) + " is outdated:\n" + \
                                             "Minimum version 1706 or 5 required"
                                    message += vermsg + "\n"
                                    if term_print:
                                        print(vermsg)
                                if foam_ver > 2106:
                                    vermsg = "OpenFOAM version " + str(foam_ver) + " is not yet supported:\n" + \
                                             "Last tested version is 2106"
                                    message += vermsg + "\n"
                                    if term_print:
                                        print(vermsg)
                            else:  # Foundation version
                                if foam_ver < 5:
                                    vermsg = "OpenFOAM version " + str(foam_ver) + " is outdated:\n" + \
                                             "Minimum version 5 or 1706 required"
                                    message += vermsg + "\n"
                                    if term_print:
                                        print(vermsg)
                                if foam_ver > 9:
                                    vermsg = "OpenFOAM version " + str(foam_ver) + " is not yet supported:\n" + \
                                             "Last tested version is 9"
                                    message += vermsg + "\n"
                                    if term_print:
                                        print(vermsg)
                        except ValueError:
                            vermsg = "Error parsing OpenFOAM version string " + foam_ver
                            message += vermsg + "\n"
                            if term_print:
                                print(vermsg)
                    # Check for wmake
                    if getFoamRuntime() != "MinGW":
                        try:
                            runFoamCommand("wmake -help")
                        except subprocess.CalledProcessError:
                            wmakemsg = "OpenFOAM installation does not include 'wmake'. " + \
                                       "Installation of cfMesh and HiSA will not be possible."
                            message += wmakemsg + "\n"
                            if term_print:
                                print(wmakemsg)

                    # Check for cfMesh
                    try:
                        cfmesh_ver = runFoamCommand("cartesianMesh -version")[0]
                        cfmesh_ver = cfmesh_ver.rstrip().split()[-1]
                        cfmesh_ver = cfmesh_ver.split('.')
                        if (not cfmesh_ver or len(cfmesh_ver) != 2 or
                            int(cfmesh_ver[0]) < CF_MAJOR_VER_REQUIRED or
                            (int(cfmesh_ver[0]) == CF_MAJOR_VER_REQUIRED and
                             int(cfmesh_ver[1]) < CF_MINOR_VER_REQUIRED)):
                            vermsg = "cfMesh-CfdOF version {}.{} required".format(CF_MAJOR_VER_REQUIRED,
                                                                                  CF_MINOR_VER_REQUIRED)
                            message += vermsg + "\n"
                            if term_print:
                                print(vermsg)
                    except subprocess.CalledProcessError:
                        cfmesh_msg = "cfMesh (CfdOF version) not found"
                        message += cfmesh_msg + '\n'
                        if term_print:
                            print(cfmesh_msg)

                    # Check for HiSA
                    try:
                        hisa_ver = runFoamCommand("hisa -version")[0]
                        hisa_ver = hisa_ver.rstrip().split()[-1]
                        hisa_ver = hisa_ver.split('.')
                        if (not hisa_ver or len(hisa_ver) != 3 or
                            int(hisa_ver[0]) < HISA_MAJOR_VER_REQUIRED or
                            (int(hisa_ver[0]) == HISA_MAJOR_VER_REQUIRED and
                             (int(hisa_ver[1]) < HISA_MINOR_VER_REQUIRED or
                              (int(hisa_ver[1]) == HISA_MINOR_VER_REQUIRED and
                               int(hisa_ver[2]) < HISA_PATCH_VER_REQUIRED)))):
                            vermsg = "HiSA version {}.{}.{} required".format(HISA_MAJOR_VER_REQUIRED,
                                                                             HISA_MINOR_VER_REQUIRED,
                                                                             HISA_PATCH_VER_REQUIRED)
                            message += vermsg + "\n"
                            if term_print:
                                print(vermsg)
                    except subprocess.CalledProcessError:
                        hisa_msg = "HiSA not found"
                        message += hisa_msg + '\n'
                        if term_print:
                            print(hisa_msg)

            # Check for paraview
            if term_print:
                print("Checking for paraview:")
            paraview_cmd = getParaviewExecutable()
            failed = False
            if not paraview_cmd:
                paraview_cmd = 'paraview'
                # If not found, try to run from the OpenFOAM environment, in case a bundled version is
                # available from there
                try:
                    runFoamCommand("which paraview")
                except subprocess.CalledProcessError:
                    failed = True
            if failed or not os.path.exists(paraview_cmd):
                pv_msg = "Paraview executable '" + paraview_cmd + "' not found."
                message += pv_msg + '\n'
                if term_print:
                    print(pv_msg)

        if term_print:
            print("Checking for Plot module:")
        try:
            from FreeCAD.Plot import Plot
        except ImportError:
            try:
                from freecad.plot import Plot
            except ImportError:
                plot_msg = "Could not load Plot module\nPlease install it using Tools | Addon manager"
                message += plot_msg + '\n'
                if term_print:
                    print(plot_msg)

        try:
            import matplotlib
        except ImportError:
            matplot_msg = "Could not load matplotlib package (required by Plot module)"
            message += matplot_msg + '\n'
            if term_print:
                print(matplot_msg)

        if term_print:
            print("Checking for gmsh:")
        # check that gmsh version 2.13 or greater is installed
        gmshversion = ""
        if platform.system() == "Windows":
            # Use forward slashes to avoid escaping problems
            gmsh_exe = '/'.join([FreeCAD.getHomePath().rstrip('/'), 'bin', 'gmsh.exe'])
        else:
            gmsh_exe = shutil.which("gmsh")
        if gmsh_exe is None:
            gmsh_msg = "gmsh not found (optional)"
            message += gmsh_msg + '\n'
            if term_print:
                print(gmsh_msg)
        else:
            try:
                # Needs to be runnable from OpenFOAM environment
                gmshversion = runFoamCommand("'" + gmsh_exe + "'" + " -version")[1]
            except (OSError, subprocess.CalledProcessError):
                gmsh_msg = "gmsh could not be run from OpenFOAM environment"
                message += gmsh_msg + '\n'
                if term_print:
                    print(gmsh_msg)
            if len(gmshversion) > 1:
                # Only the last line contains gmsh version number
                gmshversion = gmshversion.rstrip().split()
                gmshversion = gmshversion[-1]
                versionlist = gmshversion.split(".")
                if int(versionlist[0]) < 2 or (int(versionlist[0]) == 2 and int(versionlist[1]) < 13):
                    gmsh_ver_msg = "gmsh version is older than minimum required (2.13)"
                    message += gmsh_ver_msg + '\n'
                    if term_print:
                        print(gmsh_ver_msg)

        if term_print:
            print("Completed CFD dependency check")
        return message


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
            # Go through the defaults and see if any are found
            for d in PARAVIEW_PATH_DEFAULTS[platform.system()]:
                paraview_cmd = os.path.expanduser(d)
                if paraview_cmd and not os.path.exists(paraview_cmd):
                    paraview_cmd = None
                else:
                    break
    if not paraview_cmd:
        # Otherwise, see if the command 'paraview' is in the path.
        paraview_cmd = shutil.which("paraview")
    return paraview_cmd


def startParaview(case_path, script_name, consoleMessageFn):
    proc = QtCore.QProcess()
    paraview_cmd = getParaviewExecutable()
    arg = '--script={}'.format(script_name)

    if not paraview_cmd:
        # If not found, try to run from the OpenFOAM environment, in case a bundled version is available from there
        paraview_cmd = "$(which paraview)"  # 'which' required due to mingw weirdness(?) on Windows
        try:
            consoleMessageFn("Running " + paraview_cmd + " " + arg)
            proc = startFoamApplication([paraview_cmd, arg], case_path, log_name=None)
            consoleMessageFn("Paraview started")
        except QtCore.QProcess.ProcessError:
            consoleMessageFn("Error starting paraview")
    else:
        consoleMessageFn("Running " + paraview_cmd + " " + arg)
        proc.setWorkingDirectory(case_path)

        env = QtCore.QProcessEnvironment.systemEnvironment()
        removeAppimageEnvironment(env)
        proc.setProcessEnvironment(env)

        proc.start(paraview_cmd, [arg])
        if proc.waitForStarted():
            consoleMessageFn("Paraview started")
        else:
            consoleMessageFn("Error starting paraview")
    return proc


def removeAppimageEnvironment(env):
    """ When running from an AppImage, the changes to the system environment can interfere with the running of
        external commands. This tries to remove them. """
    if env.contains("APPIMAGE"):
        # Strip any value starting with the appimage directory, to attempt to revert to the system environment
        appdir = env.value("APPDIR")
        keys = env.keys()
        for k in keys:
            vals = env.value(k).split(':')
            newvals = ''
            for val in vals:
                if not val.startswith(appdir):
                    newvals += val + ':'
            newvals = newvals.rstrip(':')
            if newvals:
                env.insert(k, newvals)
            else:
                env.remove(k)


def floatEqual(a, b):
    """ Test whether a and b are equal within an absolute and relative tolerance """
    reltol = 10*sys.float_info.epsilon
    abstol = 1e-12  # Seems to be necessary on file read/write
    return abs(a-b) < abstol or abs(a - b) <= reltol*max(abs(a), abs(b))


def isSameGeometry(shape1, shape2):
    """ Copy of FemMeshTools.is_same_geometry, with fixes """
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


def findElementInShape(aShape, anElement):
    """ Copy of FemMeshTools.find_element_in_shape, but calling isSameGeometry"""
    # import Part
    ele_st = anElement.ShapeType
    if ele_st == 'Solid' or ele_st == 'CompSolid':
        for index, solid in enumerate(aShape.Solids):
            # print(is_same_geometry(solid, anElement))
            if isSameGeometry(solid, anElement):
                # print(index)
                # Part.show(aShape.Solids[index])
                ele = ele_st + str(index + 1)
                return ele
        FreeCAD.Console.PrintError('Solid ' + str(anElement) + ' not found in: ' + str(aShape) + '\n')
        if ele_st == 'Solid' and aShape.ShapeType == 'Solid':
            print('We have been searching for a Solid in a Solid and we have not found it. In most cases this should be searching for a Solid inside a CompSolid. Check the ShapeType of your Part to mesh.')
        # Part.show(anElement)
        # Part.show(aShape)
    elif ele_st == 'Face' or ele_st == 'Shell':
        for index, face in enumerate(aShape.Faces):
            # print(is_same_geometry(face, anElement))
            if isSameGeometry(face, anElement):
                # print(index)
                # Part.show(aShape.Faces[index])
                ele = ele_st + str(index + 1)
                return ele
    elif ele_st == 'Edge' or ele_st == 'Wire':
        for index, edge in enumerate(aShape.Edges):
            # print(is_same_geometry(edge, anElement))
            if isSameGeometry(edge, anElement):
                # print(index)
                # Part.show(aShape.Edges[index])
                ele = ele_st + str(index + 1)
                return ele
    elif ele_st == 'Vertex':
        for index, vertex in enumerate(aShape.Vertexes):
            # print(is_same_geometry(vertex, anElement))
            if isSameGeometry(vertex, anElement):
                # print(index)
                # Part.show(aShape.Vertexes[index])
                ele = ele_st + str(index + 1)
                return ele
    elif ele_st == 'Compound':
        FreeCAD.Console.PrintError('Compound is not supported.\n')


def matchFaces(faces1, faces2):
    """ This function does a geometric matching of face lists much faster than doing face-by-face search
    :param faces1: List of tuples - first item is face object, second is any user data
    :param faces2: List of tuples - first item is face object, second is any user data
    :return:  A list of (data1, data2) containing the user data for any/all matching faces
    Note that faces1 and faces2 are sorted in place and can be re-used for faster subsequent searches
    """

    if sys.version_info >= (3,):  # Python 3

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

    else:  # Python 2

        def compFn(x, y):
            if floatEqual(x, y):
                return 0
            elif x < y:
                return -1
            else:
                return 1

        # Sort face list by first vertex, x then y then z in case all in plane
        faces1.sort(cmp=compFn, key=lambda bf: bf[0].Vertexes[0].Point.z)
        faces1.sort(cmp=compFn, key=lambda bf: bf[0].Vertexes[0].Point.y)
        faces1.sort(cmp=compFn, key=lambda bf: bf[0].Vertexes[0].Point.x)

        # Same on other face list
        faces2.sort(cmp=compFn, key=lambda mf: mf[0].Vertexes[0].Point.z)
        faces2.sort(cmp=compFn, key=lambda mf: mf[0].Vertexes[0].Point.y)
        faces2.sort(cmp=compFn, key=lambda mf: mf[0].Vertexes[0].Point.x)

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
    from CfdAnalysis import _CfdAnalysis
    for obj in FreeCAD.ActiveDocument.Objects:
        if hasattr(obj, 'Proxy') and isinstance(obj.Proxy, _CfdAnalysis):
            obj.IsActiveAnalysis = False

    analysis.IsActiveAnalysis = True


def getActiveAnalysis():
    from CfdAnalysis import _CfdAnalysis
    for obj in FreeCAD.ActiveDocument.Objects:
        if hasattr(obj, 'Proxy') and isinstance(obj.Proxy, _CfdAnalysis):
            if obj.IsActiveAnalysis:
                return obj
    return None


def addObjectProperty(obj, prop, init_val, type, *args):
    """ Call addProperty on the object if it does not yet exist """
    added = False
    if prop not in obj.PropertiesList:
        added = obj.addProperty(type, prop, *args)
    if type == "App::PropertyQuantity":
        # Set the unit so that the quantity will be accepted
        # Has to be repeated on load as unit gets lost
        setattr(obj, prop, Units.Unit(init_val))
    if added:
        setattr(obj, prop, init_val)
        return True
    else:
        return False


def relLenToRefinementLevel(rel_len):
    return math.ceil(math.log(1.0/rel_len)/math.log(2))


def importMaterials():
    materials = {}
    material_name_path_list = []

    # Store the defaults inside the module directory rather than the resource dir
    # system_mat_dir = FreeCAD.getResourceDir() + "/Mod/Material/FluidMaterialProperties"
    system_mat_dir = os.path.join(get_module_path(), "data/CfdFluidMaterialProperties")
    material_name_path_list = material_name_path_list + addMatDir(system_mat_dir, materials)
    return materials, material_name_path_list


def addMatDir(mat_dir, materials):
    import glob
    import os
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


QUANTITY_PROPERTIES = ['App::PropertyQuantity',
                       'App::PropertyLength',
                       'App::PropertyDistance',
                       'App::PropertyAngle',
                       'App::PropertyArea',
                       'App::PropertyVolume',
                       'App::PropertySpeed',
                       'App::PropertyAcceleration',
                       'App::PropertyForce',
                       'App::PropertyPressure']


def propsToDict(obj):
    """ Convert an object's properties to dictionary entries, converting any PropertyQuantity to float in SI units """
    d = {}
    for k in obj.PropertiesList:
        if obj.getTypeIdOfProperty(k) in QUANTITY_PROPERTIES:
            q = Units.Quantity(getattr(obj, k))
            # q.Value is in FreeCAD internal units, which is same as SI except for mm instead of m
            d[k] = q.Value/1000**q.Unit.Signature[0]
        else:
            d[k] = getattr(obj, k)
    return d


def openFileManager(case_path):
    case_path = os.path.abspath(case_path)
    if platform.system() == 'MacOS':
        subprocess.Popen(['open', '--', case_path])
    elif platform.system() == 'Linux':
        subprocess.Popen(['xdg-open', case_path])
    elif platform.system() == 'Windows':
        subprocess.Popen(['explorer', case_path])


def writePatchToStl(solid_name, facemesh, fid, scale=1):
    fid.write("solid {}\n".format(solid_name))
    for face in facemesh.Facets:
        n = face.Normal
        fid.write(" facet normal {} {} {}\n".format(n[0], n[1], n[2]))
        fid.write("  outer loop\n")
        for i in range(3):
            p = [i * scale for i in face.Points[i]]
            fid.write("   vertex {} {} {}\n".format(p[0], p[1], p[2]))
        fid.write("  endloop\n")
        fid.write(" endfacet\n")
    fid.write("endsolid {}\n".format(solid_name))
