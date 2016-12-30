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

"""
utility functions like mesh exporting, shared by any CFD solver
"""

from __future__ import print_function
import os
import os.path

import FreeCAD
import Fem


def isWorkingDirValid(wd):
    if not (os.path.isdir(wd) and os.access(wd, os.W_OK)):
        FreeCAD.Console.PrintError("Working dir: {}, is not existent or writable".format(wd))
        return False
    else:
        return True


def getTempWorkingDir():
    #FreeCAD.Console.PrintMessage(FreeCAD.ActiveDocument.TransientDir)  # tmp folder for save transient data
    #FreeCAD.ActiveDocument.FileName  # abspath to user folder, which is not portable across computers
    #FreeCAD.Console.PrintMessage(os.path.dirname(__file__))  # this function is not usable in InitGui.py

    import tempfile
    if os.path.exists('/tmp/'):
        workDir = '/tmp/'  # must exist for POSIX system
    elif tempfile.tempdir:
        workDir = tempfile.tempdir
    else:
        cwd = os.path.abspath('./')
    return workDir


def setupWorkingDir(solver_object):
    wd = solver_object.WorkingDir
    if not (os.path.exists(wd)):
        try:
            os.makedirs(wd)
        except:
            FreeCAD.Console.PrintWarning("Dir \'{}\' doesn't exist and cannot be created, using tmp dir instead".format(wd))
            wd = getTempWorkingDir()
            solver_object.WorkingDir = wd
    return wd

################################################

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
        # find the fem analysis object this fem_object belongs to
        doc = fem_object.Document
        for analysis_obj in doc.findObjects('Fem::FemAnalysis'):
            if fem_object in analysis_obj.Member:
                return analysis_obj


def getMaterial(analysis_object):
    for i in analysis_object.Member:
        if i.isDerivedFrom('App::MaterialObjectPython'):
            return i


def getSolver(analysis_object):
    for i in analysis_object.Member:
        if i.isDerivedFrom("Fem::FemSolverObjectPython"):  # Fem::FemSolverObject is C++ type name
            return i


def getSolverSettings(solver):
    # convert properties into python dict, while key must begin with lower letter
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


def getMesh(analysis_object):
    for i in analysis_object.Member:
        if i.isDerivedFrom("Fem::FemMeshObject"):
            return i
    # python will return None by default, so check None outside


def isSolidMesh(fem_mesh):
    if fem_mesh.VolumeCount > 0:  # solid mesh
        return True

            
def getResult(analysis_object):
    for i in analysis_object.Member:
        if(i.isDerivedFrom("Fem::FemResultObject")):
            return i
    return None


def convertQuantityToMKS(input, quantity_type, unit_system="MKS"):
    """ convert non MKS unit quantity to SI MKS (metre, kg, second)
    FreeCAD default length unit is mm, not metre, thereby, area is mm^2, pressure is MPa, etc
    MKS (metre, kg, second) could be selected from "Edit->Preference", "General -> Units",
    but not recommended since all CAD use mm as basic length unit.
    see:
    """
    return input


#################### UNV mesh writer #########################################

def write_unv_mesh(mesh_obj, bc_group, mesh_file_name):
    __objs__ = []
    __objs__.append(mesh_obj)
    FreeCAD.Console.PrintMessage("Export FemMesh to UNV format file: {}\n".format(mesh_file_name))
    Fem.export(__objs__, mesh_file_name)
    del __objs__
    # repen this unv file and write the boundary faces
    _write_unv_bc_mesh(mesh_obj, bc_group, mesh_file_name)


def _write_unv_bc_mesh(mesh_obj, bc_group, unv_mesh_file):
    #FreeCAD.Console.PrintMessage('Write face_set on boundaries\n')
    f = open(unv_mesh_file, 'a')  # appending bc to the volume mesh, which contains node and element definition, ends with '-1'
    f.write("{:6d}\n".format(-1))  # start of a section
    f.write("{:6d}\n".format(2467))  # group section
    for bc_id, bc_obj in enumerate(bc_group):
        _write_unv_bc_faces(mesh_obj, f, bc_id + 1, bc_obj)
    f.write("{:6d}\n".format(-1))  # end of a section
    f.write("{:6d}\n".format(-1))  # end of file
    f.close()


def _write_unv_bc_faces(mesh_obj, f, bc_id, bc_object):
    facet_list = []
    for o, e in bc_object.References:  # list of (objectOfType<Part::PartFeature>, (stringName1, stringName2, ...))
        # merge bugfix from https://github.com/jaheyns/FreeCAD/blob/master/src/Mod/Cfd/CfdTools.py
        # loop through all the features in e, since there might be multiple entities within a given boundary definition
        for ii in range(len(e)):
            elem = o.Shape.getElement(e[ii])  # from 0.16 -> 0.17: e is a tuple of string, instead of a string
            #FreeCAD.Console.PrintMessage('Write face_set on face: {} for boundary\n'.format(e[0]))
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
