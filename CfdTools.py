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

import FreeCAD
import Fem
import Units

if FreeCAD.GuiUp:
    import FreeCADGui
    import FemGui
    from PySide import QtGui


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
    for i in analysis_object.Member:
        if hasattr(i, "Proxy") \
                and hasattr(i.Proxy, "Type") \
                and (i.Proxy.Type == "FemMeshGmsh" or i.Proxy.Type == "CfdMeshCart"):
            if isPresent:
                FreeCAD.Console.PrintError("Analysis contain more than one mesh object.")
            else:
                meshObj.append(i)
                isPresent = True
    if not isPresent:
        meshObj = None  # just a placeholder to be created in event that it is not present
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

def setPartVisibility(vobj, part_vis, compound_vis, mesh_vis, bound_vis):
    """ Set visibility of feature parts, compounded parts, mesh and boundaries. """
    doc_name = str(vobj.Object.Document.Name)
    doc = FreeCAD.getDocument(doc_name)
    boolean_present = False
    for obj in doc.Objects:
        if ("Boolean" in obj.Name):
            boolean_present = True
    for obj in doc.Objects:
        if obj.isDerivedFrom("Part::Feature"):
            if not ("CfdFluidBoundary" in obj.Name) and not boolean_present:
                # Hide parts if a boolean fragment exists
                FreeCAD.getDocument(doc_name).getObject(obj.Name).ViewObject.Visibility = part_vis
            if ("Boolean" in obj.Name):
                # Show only boolean to prevent duplicate face selection
                FreeCAD.getDocument(doc_name).getObject(obj.Name).ViewObject.Visibility = part_vis
            # Update BC visibility to only show mesh_obj part
            # if ("CfdFluidBoundary" in obj.Name) and not bound_vis:
            #     ''' Only turn boundary visibility off, if set to true it will keep visibility as is. '''
            #     FreeCAD.getDocument(doc_name).getObject(obj.Name).ViewObject.Visibility = bound_vis
            if ("Compound" in obj.Name) or ("Fusion" in obj.Name):
                FreeCAD.getDocument(doc_name).getObject(obj.Name).ViewObject.Visibility = compound_vis
        if obj.isDerivedFrom("Fem::FemMeshObject"):
            FreeCAD.getDocument(doc_name).getObject(obj.Name).ViewObject.Visibility = mesh_vis


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
    if FreeCAD.GuiUp:
        QtGui.QMessageBox.critical(None, "CFDFoam Workbench", msg)
    else:
        FreeCAD.Console.PrintError(msg + "\n")


def inputCheckAndStore(value, units, dictionary, key):
    """ Store the numeric part of value (string) in dictionary[key] in the given units if compatible"""
    quantity = Units.Quantity(value).getValueAs(units)
    dictionary[key] = quantity.Value


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