#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2015 - FreeCAD Developers                               *
#*   Author (c) 2015 - Qingfeng Xia <qingfeng xia eng.ox.ac.uk>                    *
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
import tempfile

import FreeCAD
import Fem


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

    def getActiveAnalysis(fem_object):
        """ Find the Fem analysis object to which this fem_object belongs. """
        doc = fem_object.Document
        for analysis_obj in doc.findObjects('Fem::FemAnalysis'):
            if fem_object in analysis_obj.Member:
                return analysis_obj


def getPhysicsModel(analysis_object):
    isPresent = False
    for i in analysis_object.Member:
        if "PhysicsModel" in i.Name:
            physicsModel = i.PhysicsModel
            isPresent = True
    if not(isPresent):
        physicsModel = None  # A placeholder to be created in event that it is not present.
    return physicsModel,isPresent

def getPorousObject(analysis_object):
    isPresent = False
    porousZone = []
    for i in analysis_object.Member:
        if "PorousZone" in i.Name:
            porousZone.append(i)
            isPresent = True
    if not(isPresent):
        porousZone = None #just a placeholder to be created in event that it is not present
    return porousZone,isPresent

def getInitialConditions(analysis_object):
    isPresent = False
    for i in analysis_object.Member:
        if "InitializeInternalVariables" in i.Name:
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
    user_mod_path = os.path.join(FreeCAD.ConfigGet("UserAppData"), "Mod/Cfd")
    app_mod_path = os.path.join(FreeCAD.ConfigGet("AppHomePath"), "Mod/Cfd")
    if os.path.exists(user_mod_path):
        return user_mod_path
    else:
        return app_mod_path

# NOTE: Code depreciated (JH) 27/01/2016
# def convertQuantityToMKS(input, quantity_type, unit_system="MKS"):
#     """ convert non MKS unit quantity to SI MKS (metre, kg, second)
#     FreeCAD default length unit is mm, not metre, thereby, area is mm^2, pressure is MPa, etc
#     MKS (metre, kg, second) could be selected from "Edit->Preference", "General -> Units",
#     but not recommended since all CAD use mm as basic length unit.
#     see:
#     """
#     return input


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
            if ("CfdFluidBoundary" in obj.Name) and not bound_vis:
                ''' Only turn boundary visibility off, if set to true it will keep visibility as is. '''
                FreeCAD.getDocument(doc_name).getObject(obj.Name).ViewObject.Visibility = bound_vis
            if ("Compound" in obj.Name) or ("Fusion" in obj.Name):
                FreeCAD.getDocument(doc_name).getObject(obj.Name).ViewObject.Visibility = compound_vis
        if obj.isDerivedFrom("Fem::FemMeshObject"):
            FreeCAD.getDocument(doc_name).getObject(obj.Name).ViewObject.Visibility = mesh_vis


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
    f = open(unv_mesh_file, 'a')     # Appending bc to the volume mesh, which contains node and
                                     # element definition, ends with '-1'
    f.write("{:6d}\n".format(-1))    # Start of a section
    f.write("{:6d}\n".format(2467))  # Group section
    for bc_id, bc_obj in enumerate(bc_group):
        _write_unv_bc_faces(mesh_obj, f, bc_id + 1, bc_obj)
    f.write("{:6d}\n".format(-1))    # end of a section
    f.write("{:6d}\n".format(-1))    # end of file
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


def getOrDefault(dictionary, key, default):
    if key in dictionary:
        return dictionary[key]
    else:
        return default


def normalise(v):
    import numpy
    mag = numpy.sqrt(sum(vi**2 for vi in v))
    import sys
    if mag < sys.float_info.min:
        mag += sys.float_info.min
    return [vi/mag for vi in v]
