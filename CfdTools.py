# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2015 - FreeCAD Developers                               *
# *   Copyright (c) 2015 - Qingfeng Xia <qingfeng xia eng.ox.ac.uk>         *
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

# Utility functions like mesh exporting, shared by any CFD solver

from __future__ import print_function
import os
import os.path
import shutil
import tempfile
import string
import numbers
import platform
import subprocess
import sys

import FreeCAD
import Fem
from FreeCAD import Units
import CfdConsoleProcess
import Part

if FreeCAD.GuiUp:
    import FreeCADGui
    import FemGui
    from PySide import QtGui
    from PySide import QtCore

# Some standard install locations that are searched if an install directory is not specified
FOAM_DIR_DEFAULTS = {"Windows": ["C:\\Program Files\\blueCFD-Core-2017\\OpenFOAM-5.x",
                                 "C:\\Program Files\\blueCFD-Core-2016\\OpenFOAM-4.x"],
                     "Linux": ["/opt/openfoam4", "/opt/openfoam5", "/opt/openfoam6", "/opt/openfoam-dev",
                               "~/OpenFOAM/OpenFOAM-6.x", "~/OpenFOAM/OpenFOAM-6.0",
                               "~/OpenFOAM/OpenFOAM-5.x", "~/OpenFOAM/OpenFOAM-5.0",
                               "~/OpenFOAM/OpenFOAM-4.x", "~/OpenFOAM/OpenFOAM-4.0", "~/OpenFOAM/OpenFOAM-4.1",
                               "~/OpenFOAM/OpenFOAM-dev"]
                     }


def getDefaultOutputPath():
    prefs = getPreferencesLocation()
    output_path = FreeCAD.ParamGet(prefs).GetString("DefaultOutputPath", "")
    if not output_path:
        output_path = tempfile.gettempdir()
    return output_path


def getOutputPath(analysis):
    if analysis and 'OutputPath' in analysis.PropertiesList:
        output_path = analysis.OutputPath
    else:
        output_path = ""
    if not output_path:
        output_path = getDefaultOutputPath()
    return output_path

# Get functions

if FreeCAD.GuiUp:
    def getResultObject():
        import FreeCADGui
        sel = FreeCADGui.Selection.getSelection()
        if (len(sel) == 1):
            if sel[0].isDerivedFrom("Fem::FemResultObject"):
                return sel[0]
        import FemGui
        for i in FemGui.getActiveAnalysis().Group:
            if(i.isDerivedFrom("Fem::FemResultObject")):
                return i
        return None

def getParentAnalysisObject(obj):
    """ Return CfdAnalysis object to which this obj belongs in the tree """
    for o in FreeCAD.activeDocument().Objects:
        if o.Name.startswith("CfdAnalysis"):
            if obj in o.Group:
                return o
    return None


def getPhysicsModel(analysis_object):
    isPresent = False
    for i in analysis_object.Group:
        if "PhysicsModel" in i.Name:
            physicsModel = i
            isPresent = True
    if not isPresent:
        physicsModel = None  # A placeholder to be created in event that it is not present.
    return physicsModel, isPresent


def getMeshObject(analysis_object):
    isPresent = False
    meshObj = []
    if analysis_object:
        members = analysis_object.Group
    else:
        members = FreeCAD.activeDocument().Objects
    for i in members:
        if hasattr(i, "Proxy") \
                and hasattr(i.Proxy, "Type") \
                and i.Proxy.Type == "CfdMesh":
            if isPresent:
                FreeCAD.Console.PrintError("Analysis contains more than one mesh object.")
            else:
                meshObj.append(i)
                isPresent = True
    if not isPresent:
        meshObj = [None]  # just a placeholder to be created in event that it is not present
    return meshObj[0], isPresent


def getPorousZoneObjects(analysis_object):
    return [i for i in analysis_object.Group if i.Name.startswith('PorousZone')]


def getInitialisationZoneObjects(analysis_object):
    return [i for i in analysis_object.Group if i.Name.startswith('InitialisationZone')]


def getZoneObjects(analysis_object):
    return [i for i in analysis_object.Group if 'Zone' in i.Name]


def getInitialConditions(analysis_object):
    isPresent = False
    for i in analysis_object.Group:
        if "InitialiseFields" in i.Name:
            InitialVariables = i.InitialVariables
            isPresent = True
    if not isPresent:
        InitialVariables = None  # A placeholder to be created in event that it is not present.
    return InitialVariables, isPresent


def getMaterials(analysis_object):
    return [i for i in analysis_object.Group
            if i.isDerivedFrom('App::MaterialObjectPython')]


def getSolver(analysis_object):
    for i in analysis_object.Group:
        if i.isDerivedFrom("Fem::FemSolverObjectPython"):  # Fem::FemSolverObject is C++ type name
            return i


def getSolverSettings(solver):
    """ Convert properties into python dict, while key must begin with lower letter. """
    dict = {}
    f = lambda s: s[0].lower() + s[1:]
    for prop in solver.PropertiesList:
        dict[f(prop)] = solver.getPropertyByName(prop)
    return dict


def getConstraintGroup(analysis_object):
    group = []
    for i in analysis_object.Group:
        if i.isDerivedFrom("Fem::Constraint"):
            group.append(i)
    return group


def getCfdConstraintGroup(analysis_object):
    group = []
    for i in analysis_object.Group:
        if i.isDerivedFrom("Fem::ConstraintFluidBoundary"):
            group.append(i)
    return group


def getCfdBoundaryGroup(analysis_object):
    group = []
    import _CfdFluidBoundary
    for i in analysis_object.Group:
        if isinstance(i.Proxy, _CfdFluidBoundary._CfdFluidBoundary):
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
    for i in analysis_object.Group:
        if i.isDerivedFrom("Fem::FemMeshObject"):
            return i
    # Python return None by default, so check None outside


def isSolidMesh(fem_mesh):
    if fem_mesh.VolumeCount > 0:  # solid mesh
        return True


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
    """ To enable correct mesh refinement boolean fragments are set to compSolid mode, """
    doc_name = str(vobj.Object.Document.Name)
    doc = FreeCAD.getDocument(doc_name)
    for obj in doc.Objects:
        if ("Boolean" in obj.Name) and not ("Mesh" in obj.Name):
            FreeCAD.getDocument(doc_name).getObject(obj.Name).Mode = 'CompSolid'


def normalise(v):
    import numpy
    mag = numpy.sqrt(sum(vi**2 for vi in v))
    import sys
    if mag < sys.float_info.min:
        mag += sys.float_info.min
    return [vi/mag for vi in v]


def cfdError(msg):
    """ Show message for an expected error """
    QtGui.QApplication.restoreOverrideCursor()
    if FreeCAD.GuiUp:
        QtGui.QMessageBox.critical(None, "CfdOF Workbench", msg)
    else:
        FreeCAD.Console.PrintError(msg + "\n")


def cfdMessage(msg):
    """ Print a message to console and refresh GUI """
    FreeCAD.Console.PrintMessage(msg)
    if FreeCAD.GuiUp:
        FreeCAD.Gui.updateGui()


def inputCheckAndStore(value, units, dictionary, key):
    """ Store the numeric part of value (string or value) in dictionary[key] in the given units if compatible"""
    # While the user is typing there will be parsing errors. Don't confuse the user by printing these -
    # the validation icon will show an error.
    try:
        quantity = Units.Quantity(value).getValueAs(units)
    except ValueError:
        pass
    else:
        dictionary[key] = quantity.Value


def setInputFieldQuantity(inputField, quantity):
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


def indexOrDefault(list, findItem, defaultIndex):
    """ Look for findItem in list, and return defaultIndex if not found """
    try:
        return list.index(findItem)
    except ValueError:
        return defaultIndex


def hide_parts_show_meshes():
    if FreeCAD.GuiUp:
        for acnstrmesh in FemGui.getActiveAnalysis().Group:
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

    if installation_path and \
       (not os.path.isabs(installation_path) or not os.path.exists(os.path.join(installation_path, "etc", "bashrc"))):
        raise IOError("The directory {} is not a valid OpenFOAM installation".format(installation_path))

    # If not specified, try to detect from shell environment settings and defaults
    if not installation_path:
        installation_path = detectFoamDir()
    if not installation_path:
        raise IOError("OpenFOAM installation path not set and not found")

    return installation_path


def getFoamRuntime():
    if platform.system() == 'Windows':
        #if os.path.exists(os.path.join(getFoamDir(), "..", "msys64")):
        return 'BlueCFD'  # Not set yet...
        #else:
        #    return 'BashWSL'
    else:
        return 'Posix'


def detectFoamDir():
    """ Try to guess Foam install dir from WM_PROJECT_DIR or, failing that, various defaults """
    foam_dir = None
    if platform.system() == "Linux":
        cmdline = ['bash', '-l', '-c', 'echo $WM_PROJECT_DIR']
        foam_dir = subprocess.check_output(cmdline, stderr=subprocess.PIPE, universal_newlines=True)
        if len(foam_dir) > 1:               # If env var is not defined, `\n` returned
            foam_dir = foam_dir.strip()  # Python2: Strip EOL char
        else:
            foam_dir = None
        if foam_dir and not os.path.exists(os.path.join(foam_dir, "etc", "bashrc")):
            foam_dir = None

    if not foam_dir:
        for d in FOAM_DIR_DEFAULTS[platform.system()]:
            foam_dir = os.path.expanduser(d)
            if foam_dir and not os.path.exists(os.path.join(foam_dir, "etc", "bashrc")):
                foam_dir = None
            else:
                break
    return foam_dir


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
    if getFoamRuntime() == "BashWSL":
        # bash on windows: C:\Path -> /mnt/c/Path
        if os.path.isabs(p):
            return "/mnt/" + (drive[:-1]).lower() + pp
        else:
            return pp
    elif getFoamRuntime() == "BlueCFD":
        # Under blueCFD (mingw): c:\path -> /c/path
        if os.path.isabs(p):
            return "/" + (drive[:-1]).lower() + pp
        else:
            return pp
    else:  # Nothing needed for posix
        return p


def toWindowsPath(p):
    pp = p.split('/')
    if getFoamRuntime() == "BashWSL":
        # bash on windows: /mnt/c/Path -> C:\Path
        if p.startswith('/mnt/'):
            return pp[2].toupper() + ':\\' + '\\'.join(pp[3:])
        else:
            return p.replace('/', '\\')
    elif getFoamRuntime() == "BlueCFD":
        # Under blueCFD (mingw): /c/path -> c:\path; /home/ofuser/blueCFD -> <blueCFDDir>
        if p.startswith('/home/ofuser/blueCFD'):
            return getFoamDir() + '\\' + '..' + '\\' + '\\'.join(pp[4:])
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
        needed = _GetShortPathNameW(long_name, output_buf, output_buf_size)
        if output_buf_size >= needed:
            return output_buf.value
        else:
            output_buf_size = needed


def getRunEnvironment():
    """ Return native environment settings necessary for running on relevant platform """
    if getFoamRuntime() == "BashWSL":
        return {}
    elif getFoamRuntime() == "BlueCFD":
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
    if source_env:
        env_setup_script = "{}/etc/bashrc".format(installation_path)
        source = 'source "{}" && '.format(env_setup_script)
    cd = ""
    if dir:
        cd = 'cd "{}" && '.format(translatePath(dir))

    if getFoamRuntime() == "BashWSL":
        cmdline = ['bash', '-c', source + cd + cmd]
        return cmdline
    elif getFoamRuntime() == "BlueCFD":
        # Set-up necessary for running a command - only needs doing once, but to be safe...
        short_bluecfd_path = getShortWindowsPath('{}\\..'.format(installation_path))
        with open('{}\\..\\msys64\\home\\ofuser\\.blueCFDOrigin'.format(installation_path), "w") as f:
            f.write(short_bluecfd_path)
            f.close()

        # Note: Prefixing bash call with the *short* path can prevent errors due to spaces in paths
        # when running linux tools - specifically when building
        cmdline = ['{}\\msys64\\usr\\bin\\bash'.format(short_bluecfd_path), '--login', '-O', 'expand_aliases', '-c',
                   cd + cmd]
        return cmdline
    else:
        cmdline = ['bash', '-c', source + cd + cmd]
        return cmdline


def runFoamCommand(cmdline, case=None):
    """ Run a command in the OpenFOAM environment and wait until finished. Return output.
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
    return proc.output


class CfdSynchronousFoamProcess:
    def __init__(self):
        self.process = CfdConsoleProcess.CfdConsoleProcess(stdoutHook=self.readOutput, stderrHook=self.readOutput)
        self.output = ""

    def run(self, cmdline, case=None):
        print("Running ", cmdline)
        self.process.start(makeRunCommand(cmdline, case), env_vars=getRunEnvironment())
        if not self.process.waitForFinished():
            raise Exception("Unable to run command " + cmdline)
        return self.process.exitCode()

    def readOutput(self, output):
        self.output += output


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


def readTemplate(fileName, replaceDict=None):
    helperFile = open(fileName, 'r')
    helperText = helperFile.read()
    for key in replaceDict:
        helperText = helperText.replace("#"+key+"#", "{}".format(replaceDict[key]))
    helperFile.close()
    return helperText


def checkCfdDependencies(term_print=True):
        FC_MAJOR_VER_REQUIRED = 0
        FC_MINOR_VER_REQUIRED = 17
        FC_PATCH_VER_REQUIRED = 0
        FC_COMMIT_REQUIRED = 13528

        import os
        import subprocess
        import platform

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
              (minor_ver == FC_MINOR_VER_REQUIRED and patch_ver < FC_PATCH_VER_REQUIRED)
             )
            )
           ) or gitver < FC_COMMIT_REQUIRED:
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
        except IOError as e:
            ofmsg = "Could not find OpenFOAM installation: " + e.message
            if term_print:
                print(ofmsg)
            message += ofmsg + '\n'
        else:
            if not foam_dir:
                ofmsg = "OpenFOAM installation path not set and OpenFOAM environment neither pre-loaded before " + \
                        "running FreeCAD nor detected in standard locations"
                if term_print:
                    print(ofmsg)
                message += ofmsg + '\n'
            else:
                try:
                    foam_ver = runFoamCommand("echo $WM_PROJECT_VERSION")
                except Exception as e:
                    runmsg = "OpenFOAM installation found, but unable to run command: " + e.message
                    message += runmsg + '\n'
                    if term_print:
                        print(runmsg)
                    raise
                else:
                    foam_ver = foam_ver.rstrip().split()[-1]
                    if foam_ver != 'dev' and foam_ver != 'plus':
                        try:
                            # Isolate major version number
                            foam_ver = foam_ver.lstrip('v')
                            foam_ver = int(foam_ver.split('.')[0])
                            if foam_ver >= 1000:  # Plus version
                                if foam_ver < 1706:
                                    vermsg = "OpenFOAM version " + foam_ver + " is outdated:\n" + \
                                             "Minimum version 1706 or 4.0 required"
                                    message += vermsg + "\n"
                                    if term_print:
                                        print(vermsg)
                            else:  # Foundation version
                                if foam_ver < 4:
                                    vermsg = "OpenFOAM version " + foam_ver + " is outdated:\n" + \
                                             "Minimum version 4.0 or 1706 required"
                                    message += vermsg + "\n"
                                    if term_print:
                                        print(vermsg)
                        except ValueError:
                            vermsg = "Error parsing OpenFOAM version string " + foam_ver
                            message += vermsg
                            if term_print:
                                print(vermsg)

                    # Check for cfMesh
                    try:
                        runFoamCommand("cartesianMesh -help")
                    except subprocess.CalledProcessError:
                        cfmesh_msg = "cfMesh not found"
                        message += cfmesh_msg + '\n'
                        if term_print:
                            print(cfmesh_msg)
                    # Check for HiSA
                    try:
                        runFoamCommand("hisa -help")
                    except subprocess.CalledProcessError:
                        hisa_msg = "HiSA not found"
                        message += hisa_msg + '\n'
                        if term_print:
                            print(hisa_msg)

        if term_print:
            print("Checking for Plot workbench:")
        try:
            import Plot
        except ImportError:
            try:
                from freecad.plot import Plot
            except ImportError:
                plot_msg = "Could not load Plot workbench"
                message += plot_msg + '\n'
                if term_print:
                    print(plot_msg)

        try:
            import matplotlib
        except ImportError:
            matplot_msg = "Could not load matplotlib package (required by Plot workbench)"
            message += matplot_msg + '\n'
            if term_print:
                print(matplot_msg)



        if term_print:
            print("Checking for gmsh:")
        # check that gmsh version 2.13 or greater is installed
        gmshversion = ""
        try:
            gmshversion = subprocess.check_output(["gmsh", "-version"],
                                                  stderr=subprocess.STDOUT, universal_newlines=True)
        except OSError or subprocess.CalledProcessError:
            gmsh_msg = "gmsh is not installed"
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

        paraview_cmd = "paraview"
        # If using blueCFD, use paraview supplied
        if getFoamRuntime() == 'BlueCFD':
            try: # In case OpenFOAM not found
                paraview_cmd = '{}\\..\\AddOns\\ParaView\\bin\\paraview.exe'.format(getFoamDir())
            except IOError:
                pass
        # Otherwise, the command 'paraview' must be in the path - test to see if it exists
        import distutils.spawn
        if distutils.spawn.find_executable(paraview_cmd) is None:
            pv_msg = "Paraview executable " + paraview_cmd + " not found in path."
            message += pv_msg + '\n'
            if term_print:
                print(pv_msg)

        if term_print:
            print("Completed CFD dependency check")
        return message


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
        if not floatEqual(shape1.CenterOfMass[0], shape2.CenterOfMass[0]) or \
                not floatEqual(shape1.CenterOfMass[1], shape2.CenterOfMass[1]) or \
                not floatEqual(shape1.CenterOfMass[2], shape2.CenterOfMass[2]):
            return False
        elif not floatEqual(shape1.Area, shape2.Area):
            return False
        else:
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


def matchFacesToTargetShape(ref_lists, shape):
    """ This function does a geometric matching of groups of faces much faster than doing face-by-face search
    :param ref_lists: List of lists of references - outer list is 'group' (e.g. boundary); refs are tuples
    :param shape: The shape to map to
    :return:  A list of tuples: (group index, reference) of matching refs for each face in shape
    """
    # Preserve original indices
    mesh_face_list = list(zip(shape.Faces, range(len(shape.Faces))))
    src_face_list = []
    for i, rl in enumerate(ref_lists):
        for br in rl:
            obj = FreeCAD.ActiveDocument.getObject(br[0])
            if not obj:
                raise RuntimeError("Referenced object '{}' not found - object may "
                                   "have been deleted".format(br[0]))
            try:
                bf = obj.Shape.getElement(br[1])
            except Part.OCCError:
                raise RuntimeError("Referenced face '{}:{}' not found - face may "
                                   "have been deleted".format(br[0], br[1]))
            src_face_list.append((bf, i, br))

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

        # Sort boundary face list by centre of mass, x then y then z in case all in plane
        src_face_list.sort(key=compKeyFn(lambda bf: bf[0].CenterOfMass.z))
        src_face_list.sort(key=compKeyFn(lambda bf: bf[0].CenterOfMass.y))
        src_face_list.sort(key=compKeyFn(lambda bf: bf[0].CenterOfMass.x))

        # Same sorting on mesh face list
        mesh_face_list.sort(key=compKeyFn(lambda mf: mf[0].CenterOfMass.z))
        mesh_face_list.sort(key=compKeyFn(lambda mf: mf[0].CenterOfMass.y))
        mesh_face_list.sort(key=compKeyFn(lambda mf: mf[0].CenterOfMass.x))

    else:  # Python 2

        def compFn(x, y):
            if floatEqual(x, y):
                return 0
            elif x < y:
                return -1
            else:
                return 1

        # Sort boundary face list by centre of mass, x then y then z in case all in plane
        src_face_list.sort(cmp=compFn, key=lambda bf: bf[0].CenterOfMass.z)
        src_face_list.sort(cmp=compFn, key=lambda bf: bf[0].CenterOfMass.y)
        src_face_list.sort(cmp=compFn, key=lambda bf: bf[0].CenterOfMass.x)

        # Same sorting on mesh face list
        mesh_face_list.sort(cmp=compFn, key=lambda mf: mf[0].CenterOfMass.z)
        mesh_face_list.sort(cmp=compFn, key=lambda mf: mf[0].CenterOfMass.y)
        mesh_face_list.sort(cmp=compFn, key=lambda mf: mf[0].CenterOfMass.x)

    # Find faces with matching CofM
    i = 0
    j = 0
    j_match_start = 0
    matching = False
    candidate_mesh_faces = []
    for mf in mesh_face_list:
        candidate_mesh_faces.append([])
    while i < len(src_face_list) and j < len(mesh_face_list):
        bf = src_face_list[i][0]
        mf = mesh_face_list[j][0]
        if floatEqual(bf.CenterOfMass.x, mf.CenterOfMass.x):
            if floatEqual(bf.CenterOfMass.y, mf.CenterOfMass.y):
                if floatEqual(bf.CenterOfMass.z, mf.CenterOfMass.z):
                    candidate_mesh_faces[j].append((i, src_face_list[i][1], src_face_list[i][2]))
                    cmp = 0
                else:
                    cmp = (-1 if bf.CenterOfMass.z < mf.CenterOfMass.z else 1)
            else:
                cmp = (-1 if bf.CenterOfMass.y < mf.CenterOfMass.y else 1)
        else:
            cmp = (-1 if bf.CenterOfMass.x < mf.CenterOfMass.x else 1)
        if cmp == 0:
            if not matching:
                j_match_start = j
            j += 1
            matching = True
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
    for mf in mesh_face_list:
        successful_candidates.append([])
    for j in range(len(candidate_mesh_faces)):
        for k in range(len(candidate_mesh_faces[j])):
            i, nb, bref = candidate_mesh_faces[j][k]
            if isSameGeometry(src_face_list[i][0], mesh_face_list[j][0]):
                orig_idx = mesh_face_list[j][1]
                successful_candidates[orig_idx].append((nb, bref))

    return successful_candidates
