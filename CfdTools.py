#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2015 - FreeCAD Developers                               *
#*   Copyright (c) 2015 - Qingfeng Xia <qingfeng xia eng.ox.ac.uk>         *
#*   Copyright (c) 2017 - Johan Heyns (CSIR) <jheyns@csir.co.za>           *
#*   Copyright (c) 2017 - Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>        *
#*   Copyright (c) 2017 - Alfred Bogaers (CSIR) <abogaers@csir.co.za>      *
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

# Utility functions like mesh exporting, shared by any CFD solver

from __future__ import print_function
import os
import os.path  # Is this necessary if os is already imported?
import shutil
import tempfile
import string
import numbers
import platform
import subprocess

import FreeCAD
import Fem
import Units
import subprocess

if FreeCAD.GuiUp:
    import FreeCADGui
    import FemGui
    from PySide import QtGui

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
        for i in FemGui.getActiveAnalysis().Member:
            if(i.isDerivedFrom("Fem::FemResultObject")):
                return i
        return None

    def getParentAnalysisObject(obj):
        """ Return CfdAnalysis object to which this obj belongs in the tree """
        for o in FreeCAD.activeDocument().Objects:
            if o.Name.startswith("CfdAnalysis"):
                if obj in o.Member:
                    return o
        return None


def getPhysicsModel(analysis_object):
    isPresent = False
    for i in analysis_object.Member:
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
        members = analysis_object.Member
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


def getPorousObjects(analysis_object):
    isPresent = False
    porousZones = []
    for i in analysis_object.Member:
        if "PorousZone" in i.Name:
            porousZones.append(i)
            isPresent = True
    if not isPresent:
        porousZones = None  # just a placeholder to be created in event that it is not present
    return porousZones, isPresent


def getInitialConditions(analysis_object):
    isPresent = False
    for i in analysis_object.Member:
        if "InitialiseFields" in i.Name:
            InitialVariables = i.InitialVariables
            isPresent = True
    if not isPresent:
        InitialVariables = None  # A placeholder to be created in event that it is not present.
    return InitialVariables, isPresent


def getMaterial(analysis_object):
    for i in analysis_object.Member:
        if i.isDerivedFrom('App::MaterialObjectPython'):
            return i


def getSolver(analysis_object):
    for i in analysis_object.Member:
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
    for i in analysis_object.Member:
        if i.isDerivedFrom("Fem::Constraint"):
            group.append(i)
    return group


def getCfdConstraintGroup(analysis_object):
    group = []
    for i in analysis_object.Member:
        if i.isDerivedFrom("Fem::ConstraintFluidBoundary"):
            group.append(i)
    return group


def getCfdBoundaryGroup(analysis_object):
    group = []
    import _CfdFluidBoundary
    for i in analysis_object.Member:
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
    for i in analysis_object.Member:
        if i.isDerivedFrom("Fem::FemMeshObject"):
            return i
    # Python return None by default, so check None outside


def isSolidMesh(fem_mesh):
    if fem_mesh.VolumeCount > 0:  # solid mesh
        return True


def getResult(analysis_object):
    for i in analysis_object.Member:
        if i.isDerivedFrom("Fem::FemResultObject"):
            return i
    return None


def get_module_path():
    """ Returns the current Cfd module path.
    Check if the module is installed in the app's module directory or the user's app data folder. The second overrides
    the first.
    """
    import os
    user_mod_path = os.path.join(FreeCAD.ConfigGet("UserAppData"), "Mod", "CfdFoam")
    app_mod_path = os.path.join(FreeCAD.ConfigGet("AppHomePath"), "Mod", "CfdFoam")
    if os.path.exists(user_mod_path):
        return user_mod_path
    else:
        return app_mod_path


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
    """ Store the numeric part of value (string) in dictionary[key] in the given units if compatible"""
    # While the user is typing there will be parsing errors. Don't confuse the user by printing these -
    # the validation icon will show an error.
    try:
        quantity = Units.Quantity(value).getValueAs(units)
    except ValueError:
        pass
    else:
        dictionary[key] = quantity.Value


def indexOrDefault(list, findItem, defaultIndex):
    """ Look for findItem in list, and return defaultIndex if not found """
    try:
        return list.index(findItem)
    except ValueError:
        return defaultIndex

# This is taken from hide_parts_constraints_show_meshes which was removed from FemCommands for some reason
def hide_parts_show_meshes():
    if FreeCAD.GuiUp:
        for acnstrmesh in FemGui.getActiveAnalysis().Member:
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

    # If not specified, try to detect from shell environment settings
    if not installation_path:
        installation_path = detectFoamDir()

    if not os.path.isabs(installation_path) or \
       not os.path.exists(os.path.join(installation_path, "etc", "bashrc")):
        raise IOError("The directory {} is not a valid OpenFOAM installation".format(installation_path))
    else:
        setFoamDir(installation_path)

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
    """ See if WM_PROJECT_DIR is available in the bash environment """
    if platform.system() == 'Windows':
        foam_dir = None
    else:
        cmdline = ['bash', '-l', '-c', 'echo $WM_PROJECT_DIR']
        foam_dir = subprocess.check_output(cmdline, stderr=subprocess.PIPE)
    # Python 3 compatible, check_output() return type byte
    foam_dir = str(foam_dir)
    if len(foam_dir)>1:                 # If env var is not defined, python 3 returns `b'\n'` and python 2`\n`
        if foam_dir[:2] == "b'":
            foam_dir = foam_dir[2:-3]   # Python3: Strip 'b' from front and EOL char
        else:
            foam_dir = foam_dir.strip()  # Python2: Strip EOL char
        return foam_dir
    else:
        ''' A warning message is generated when the installation path is also not available. '''
        return None


def translatePath(p):
    """ Transform path to the perspective of the Linux subsystem in which OpenFOAM is run (e.g. mingw) """
    if platform.system() == 'Windows':
        return fromWindowsPath(p)
    else:
        return p


def fromWindowsPath(p):
    # bash on windows "C:\Path" -> /mnt/c/Path
    # cygwin can set the mount point for all windows drives under /mnt in /etc/fstab
    drive, tail = os.path.splitdrive(p)
    pp = tail.replace('\\', '/')
    if getFoamRuntime() == "BashWSL":
        if os.path.isabs(p):
            return "/mnt/" + (drive[:-1]).lower() + pp
        else:
            return pp
    elif getFoamRuntime() == "BlueCFD":
        if os.path.isabs(p):
            return "/" + (drive[:-1]).lower() + pp
        else:
            return pp
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
    if getFoamRuntime() == "BashWSL":
        if source_env:
            cmdline = ['bash', '-c', 'source ~/.bashrc && cd "{}" && {}'.format(translatePath(dir), cmd)]
        else:
            cmdline = ['bash', '-c', 'cd "{}" && {}'.format(translatePath(dir), cmd)]
        return cmdline
    elif getFoamRuntime() == "BlueCFD":
        # Set-up necessary for running a command - only needs doing once, but to be safe...
        with open('{}\\..\\msys64\\home\\ofuser\\.blueCFDOrigin'.format(installation_path), "w") as f:
            f.write(getShortWindowsPath('{}\\..'.format(installation_path)))
            f.close()

        if installation_path is None:
            raise IOError("OpenFOAM installation directory not found")
        cmdline = ['{}\\..\\msys64\\usr\\bin\\bash'.format(installation_path), '--login', '-O', 'expand_aliases', '-c',
                   'cd "{}" && {}'.format(translatePath(dir), cmd)]
        return cmdline
    else:
        if installation_path is None:
            raise IOError("OpenFOAM installation directory not found")
        env_setup_script = "{}/etc/bashrc".format(installation_path)
        if source_env:
            cmdline = ['bash', '-c',
                       'source "{}" && cd "{}" && {}'.format(env_setup_script, translatePath(dir), cmd)]
        else:
            cmdline = ['bash', '-c', 'cd "{}" && {}'.format(translatePath(dir), cmd)]
        return cmdline


def runFoamApplication(cmd, case):
    """ Run OpenFOAM application and automatically generate the log.application file (Wait until finished)
        cmd  - String with the application being the first entry followied by the options.
              e.g. `transformPoints -scale "(0.001 0.001 0.001)"
        case - Case directory or path
    """
    if isinstance(cmd, list) or isinstance(cmd, tuple):
        cmds = cmd
    elif isinstance(cmd, str):
        cmds = cmd.split(' ')  # Insensitive to incorrect split like space and quote
    else:
        raise Exception("Error: Application and options must be specified as a list or tuple.")

    app = cmds[0]
    logFile = "log.{}".format(app)

    if os.path.exists(logFile):
        print("Warning: {} already exists, removed to rerun {}.".format(logFile, app))
        os.remove(logFile)

    logFile = translatePath(logFile)

    try:  # Catch any output before forwarding exception
        cmdline = app + ' ' + ' '.join(cmds[1:])  # Space to separate options
        print("Running ", cmdline)
        cmdline += (" > " + logFile + " 2>&1")  # Pipe to log file
        cmd = makeRunCommand(cmdline, case)
        env = {}
        # Make a clean copy of os.environ, forcing standard strings
        for k in os.environ:
            env[str(k)] = str(os.environ[k])
        env.update(getRunEnvironment())
        # Prevent terminal window popping up in Windows
        si = None
        if platform.system() == 'Windows':
            si = subprocess.STARTUPINFO()
            si.dwFlags = subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = subprocess.SW_HIDE
        out = subprocess.check_output(cmd, env=env, stderr=subprocess.STDOUT, startupinfo=si)
        print(out)
    except subprocess.CalledProcessError as ex:
        print(ex.output)
        raise


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
