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
import Units
import CfdConsoleProcess

if FreeCAD.GuiUp:
    import FreeCADGui
    import FemGui
    from PySide import QtGui
    from PySide import QtCore

# Some standard install locations that are searched if an install directory is not specified
FOAM_DIR_DEFAULTS = {"Windows": ["C:\\Program Files\\blueCFD-Core-2016\\OpenFOAM-4.x"],
                     "Linux": ["/opt/openfoam4", "/opt/openfoam-dev",
                               "~/OpenFOAM/OpenFOAM-4.x", "~/OpenFOAM/OpenFOAM-4.0", "~/OpenFOAM/OpenFOAM-4.1",
                               "~/OpenFOAM/OpenFOAM-dev"]
                     }

"""
def checkCfdPrerequisites():
    #import Units
    #import FemGui
    #import subprocess
    #import FoamCaseBuilder/utility #doesn't work
    message = ""
    
    # analysis
    analysis = FemGui.getActiveAnalysis()
    if not analysis:
        message += "No active Analysis\n"
    # solver
    solver = getSolver(analysis)
    if not solver:
        message += "No solver object defined in the analysis\n"
    #if not working_dir:
    workingdir = solver.WorkingDir
    if(len(workingdir)<1):
        message += "Working directory not set\n"
    if not checkWorkingDir(workingdir):
            message += "Working directory \'{}\' doesn't exist.".format(workingdir)
    # mesh
    mesh = None #NB! TODO: FIGURE OUT HOW TO FIND MESH!
    if not mesh:
        message += "No mesh object defined in the analysis\n"
    else:
        if mesh.FemMesh.VolumeCount == 0 and mesh.FemMesh.FaceCount == 0 and mesh.FemMesh.EdgeCount == 0:
            message += "CFD mesh has neither volume nor shell or edge elements. Provide a CFD mesh with elements!\n"
    return message

        """

# Working directory

def checkWorkingDir(wd):
    """ Check validity of working directory. """
    if not (os.path.isdir(wd) and os.access(wd, os.W_OK)):
        FreeCAD.Console.PrintError("Working directory \'{}\' is not valid".format(wd))
        return False
    else:
        return True


def getTempWorkingDir():
    """ Return temporary working directory. """
    work_dir = ''
    if os.path.exists('/tmp/'):
        work_dir = '/tmp/'  # Must exist for POSIX system.
    elif tempfile.tempdir:
        work_dir = tempfile.tempdir
    # else:
    #     cwd = os.path.abspath('./')
    return work_dir


def setupWorkingDir(solver_object):
    """Create working directory"""
    wd = solver_object.WorkingDir
    if not (os.path.exists(wd)):
        try:
            os.makedirs(wd)
        except:
            FreeCAD.Console.PrintWarning("Directory \'{}\' doesn't exist and cannot be created, using tmp dir instead".format(wd))
            wd = getTempWorkingDir()
            solver_object.WorkingDir = wd
    return wd


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
            physicsModel = i.PhysicsModel
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
                and (i.Proxy.Type == "FemMeshGmsh" or i.Proxy.Type == "CfdMeshCart"):
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


# UNV mesh writer

def write_unv_mesh(mesh_obj, bc_group, mesh_file_name):
    __objs__ = []
    __objs__.append(mesh_obj)
    FreeCAD.Console.PrintMessage("Export FemMesh to UNV format file: {}\n".format(mesh_file_name))
    Fem.export(__objs__, mesh_file_name)
    del __objs__
    # Repen the unv file and write the boundary faces.
    _write_unv_bc_mesh(mesh_obj, bc_group, mesh_file_name)


def _write_unv_bc_mesh(mesh_obj, bc_group, unv_mesh_file):
    f = open(unv_mesh_file, 'a')  # Appending bc to the volume mesh, which contains node and
                                  # element definition, ends with '-1'
    f.write("{:6d}\n".format(-1))  # Start of a section
    f.write("{:6d}\n".format(2467))  # Group section
    for bc_id, bc_obj in enumerate(bc_group):
        _write_unv_bc_faces(mesh_obj, f, bc_id + 1, bc_obj)
    f.write("{:6d}\n".format(-1))  # end of a section
    f.write("{:6d}\n".format(-1))  # end of file
    f.close()


def _write_unv_bc_faces(mesh_obj, f, bc_id, bc_object):
    facet_list = []
    for o, e in bc_object.References:  # List of (ObjectName, StringName)
        import FreeCADGui
        obj = FreeCADGui.activeDocument().Document.getObject(o)
        elem = obj.Shape.getElement(e)
        if elem.ShapeType == 'Face':  # OpenFOAM needs only 2D face boundary for 3D model, normally
            ret = mesh_obj.FemMesh.getFacesByFace(elem)  # FemMeshPyImp.cpp
            facet_list.extend(i for i in ret)
    nr_facets = len(facet_list)
    f.write("{:>10d}         0         0         0         0         0         0{:>10d}\n".format(bc_id, nr_facets))
    f.writelines(bc_object.Label + "\n")
    for i in range(int(nr_facets / 2)):
        f.write("         8{:>10d}         0         0         ".format(facet_list[2 * i]))
        f.write("         8{:>10d}         0         0         \n".format(facet_list[2 * i + 1]))
    if nr_facets % 2:
        f.write("         8{:>10d}         0         0         \n".format(facet_list[-1]))


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
        QtGui.QMessageBox.critical(None, "CFDFoam Workbench", msg)
    else:
        FreeCAD.Console.PrintError(msg + "\n")


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
    q.Format = (12, 'e')
    inputField.setProperty("quantityString", q.UserString)

def indexOrDefault(list, findItem, defaultIndex):
    """ Look for findItem in list, and return defaultIndex if not found """
    try:
        return list.index(findItem)
    except ValueError:
        return defaultIndex

# This is taken from hide_parts_constraints_show_meshes which was removed from FemCommands for some reason
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
    elif bcType == 'constraint':
        if bcSubType == 'symmetry':
            return 'symmetry'
        elif bcSubType == 'cyclic':
            return 'cyclic'
        elif bcSubType == 'wedge':
            return 'wedge'
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
    return "User parameter:BaseApp/Preferences/Mod/Cfd/OpenFOAM"


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
        foam_dir = subprocess.check_output(cmdline, stderr=subprocess.PIPE)
        # Python 3 compatible, check_output() return type byte
        foam_dir = str(foam_dir)
        if len(foam_dir) > 1:               # If env var is not defined, python 3 returns `b'\n'` and python 2`\n`
            if foam_dir[:2] == "b'":
                foam_dir = foam_dir[2:-3]   # Python3: Strip 'b' from front and EOL char
            else:
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
    proc = CfdFoamProcess()
    exit_code = proc.run(cmdline, case)
    # Reproduce behaviour of failed subprocess run
    if exit_code:
        raise subprocess.CalledProcessError(exit_code, cmdline)
    return proc.output


class CfdFoamProcess:
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


def startFoamApplication(cmd, case, finishedHook=None, stdoutHook=None, stderrHook=None):
    """ Run OpenFOAM application and automatically generate the log.application file.
        Returns a CfdConsoleProcess object after launching
        cmd  - List or string with the application being the first entry followed by the options.
              e.g. ['transformPoints', '-scale', '"(0.001 0.001 0.001)"']
        case - Case path
    """
    if isinstance(cmd, list) or isinstance(cmd, tuple):
        cmds = cmd
    elif isinstance(cmd, str):
        cmds = cmd.split(' ')  # Insensitive to incorrect split like space and quote
    else:
        raise Exception("Error: Application and options must be specified as a list or tuple.")

    app = cmds[0].rsplit('/', 1)[-1]
    logFile = "log.{}".format(app)

    cmdline = ' '.join(cmds)  # Space to separate options
    # Pipe to log file and terminal
    cmdline += " 1> >(tee -a " + logFile + ") 2> >(tee -a " + logFile + " >&2)"
    # Tee appends to the log file, so we must remove first. Can't do directly since
    # paths may be specified using variables only available in foam runtime environment.
    cmdline = "{{ rm {}; {}; }}".format(logFile, cmdline)

    proc = CfdConsoleProcess.CfdConsoleProcess(finishedHook=finishedHook, stdoutHook=stdoutHook, stderrHook=stderrHook)
    print("Running ", ' '.join(cmds), " -> ", logFile)
    proc.start(makeRunCommand(cmdline, case), env_vars=getRunEnvironment())
    if not proc.waitForStarted():
        raise Exception("Unable to start command " + ' '.join(cmds))
    return proc


def runFoamApplication(cmd, case):
    """ Same as startFoamApplication, but waits until complete. Returns exit code. """
    proc = startFoamApplication(cmd, case)
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
        import os
        import subprocess
        import platform

        message = ""
        FreeCAD.Console.PrintMessage("Checking CFD workbench dependencies...\n")

        # Check FreeCAD version
        if term_print:
            print("Checking FreeCAD version")
        ver = FreeCAD.Version()
        gitver = int(ver[2].split()[0])
        if int(ver[0]) == 0 and (int(ver[1]) < 17 or (int(ver[1]) == 17 and gitver < 11832)):
            fc_msg = "FreeCAD version ({}.{}.{}) must be at least 0.17.11832".format(
                int(ver[0]), int(ver[1]), gitver)
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
                else:
                    foam_ver = foam_ver.rstrip().split('\n')[-1]
                    if int(foam_ver.split('.')[0]) < 4:
                        vermsg = "OpenFOAM version " + foam_ver + " pre-loaded is outdated: " \
                                   + "The CFD workbench requires at least OpenFOAM 4.0"
                        message += vermsg + "\n"
                        if term_print:
                            print(vermsg)
                    else:
                        # Check for cfMesh
                        try:
                            runFoamCommand("cartesianMesh -help")
                        except subprocess.CalledProcessError:
                            cfmesh_msg = "cfMesh not found"
                            message += cfmesh_msg + '\n'
                            if term_print:
                                print(cfmesh_msg)

        # check for gnuplot python module
        if term_print:
            print("Checking for gnuplot:")
        try:
            import Gnuplot
        except ImportError:
            gnuplotpy_msg = "gnuplot python module not installed"
            message += gnuplotpy_msg + '\n'
            if term_print:
                print(gnuplotpy_msg)

        gnuplot_cmd = "gnuplot"
        # For blueCFD, use the supplied Gnuplot
        if getFoamRuntime() == 'BlueCFD':
            gnuplot_cmd = '{}\\..\\AddOns\\gnuplot\\bin\\gnuplot.exe'.format(getFoamDir())
        # Otherwise, the command must be in the path - test to see if it exists
        import distutils.spawn
        if distutils.spawn.find_executable(gnuplot_cmd) is None:
            gnuplot_msg = "Gnuplot executable " + gnuplot_cmd + " not found in path."
            message += gnuplot_msg + '\n'
            if term_print:
                print(gnuplot_msg)

        if term_print:
            print("Checking for gmsh:")
        # check that gmsh version 2.13 or greater is installed
        gmshversion = ""
        try:
            gmshversion = subprocess.check_output(["gmsh", "-version"], stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError:
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
            paraview_cmd = '{}\\..\\AddOns\\ParaView\\bin\\paraview.exe'.format(getFoamDir())
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
    if len(shape1.Vertexes) == len(shape2.Vertexes) and len(shape1.Vertexes) == 1:
        vs1 = shape1.Vertexes[0]
        vs2 = shape2.Vertexes[0]
        if floatEqual(vs1.X, vs1.Y) and floatEqual(vs1.Y, vs2.Y) and floatEqual(vs1.Z, vs2.Z):
            return True
        else:
            return False
    else:
        return False

