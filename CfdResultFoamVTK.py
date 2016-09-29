# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2016 - Qingfeng Xia <qingfeng.xia iesensor.com>         *
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

"""
Adapted from ccxFrdReader.py (Calculix result file *.frd reader)
However, readResult() return: list of {'Time': time_step, "Mesh": mesh_data, "Result": result_set}
Python object  Fem::FemResultObjectPython consists of property to hold result data 
like Temperature, NodeNumbers, Time, Mesh, also CFD specific fields:
Pressure (StressValues), Velocity(DisplacementVectors), etc

    /// Von Mises Stress values of analysis
    App::PropertyFloatList StressValues;
    
    FemPipelineObject,  load() all XML vtk files are supported,
"""

__title__ = "FreeCAD Cfd OpenFOAM library"
__author__ = "Juergen Riegel, Michael Hindley, Bernd Hahnebach, Qingfeng Xia"
__url__ = "http://www.freecadweb.org"


import os
from math import pow, sqrt
import numpy as np


try:
    import vtk  # sudo apt-get install python-vtk6
    from vtk.util import numpy_support as VN
except ImportError:
    FreeCAD.Console.PrintMesssage("Warning: Failed to import vtk module")
    FreeCAD.Console.PrintMesssage("python-vtk6 is not installed to load bindary vtk file")
        
if open.__module__ == '__builtin__':
    pyopen = open  # because we'll redefine open below

def insert(filename, docname):
    "called when freecad wants to import a file"
    try:
        doc = FreeCAD.getDocument(docname)
    except NameError:
        doc = FreeCAD.newDocument(docname)
    FreeCAD.ActiveDocument = doc

    importVTK(filename)


def open(filename):
    "called when freecad opens a file"
    docname = os.path.splitext(os.path.basename(filename))[0]
    insert(filename, docname)


def buildMeshFromVTK(mesh_info):
    ''' makes an FreeCAD FEM Mesh object from vtk 3D unstructural grid Mesh data
    No intermediate mesh_info dict is needed to save computation time
    furthermore, cpp version should be made to deal with large CFD mesh
    '''
    if isinstance(mesh_info, str) and os.path.exists(mesh_info):
        vtk_file = mesh_info
        reader = vtk.vtkUnstructuredGridReader()
        reader.SetFileName(vtk_file)
        reader.ReadAllVectorsOn()
        #reader.ReadAllScalersOn()
        reader.Update() # Needed because of GetScalarRange
        m = reader.GetOutput()
    else:
        m = mesh_info

    import Fem
    mesh = Fem.FemMesh()

    VTK_TETRA = vtk.vtkTetra().GetCellType()
    VTK_PRISM = vtk.vtkWedge().GetCellType()
    VTK_HEXAHEDRON = vtk.vtkHexahedron().GetCellType()
    VTK_PYRAMID = vtk.vtkPyramid().GetCellType()

    nPoints = m.GetNumberOfPoints()
    nCells = m.GetNumberOfCells()
    FreeCAD.Console.PrintMessage("{} nodes/points and {} cells/elements found!\n".format(nPoints, nCells))

    if nPoints > 0:
        points = m.GetPoints()
        for i in range(nPoints):
            p = points.GetPoint(i)  # tuple type
            #print(p[0], p[1], p[2], i+1)
            mesh.addNode(p[0], p[1], p[2], i+1)  # node Id start from one, not zero?
        # read mesh topo for element/cell
        cells = m.GetCells()  # vtkCellArray
        pIds = vtk.vtkIdList()
        for iCell in range(nCells):
            cells.GetCell(iCell, pIds)
            if m.GetCellType(iCell) == VTK_TETRA:
                mesh.addVolume([pIds.GetId(i)+1 for i in range(4)], iCell+1)
            elif m.GetCellType(iCell) == VTK_HEXAHEDRON:
                mesh.addVolume([pIds.GetId(i)+1 for i in range(8)], iCell+1)
            elif m.GetCellType(iCell) == VTK_PRISM:
                mesh.addVolume([pIds.GetId(i)+1 for i in range(6)], iCell+1)
            elif m.GetCellType(iCell) == VTK_PYRAMID:
                mesh.addVolume([pIds.GetId(i)+1 for i in range(5)], iCell+1)
            else:
                FreeCAD.Console.PrintError("Only 3D Elements/Cells are supported\n")
    else:
        FreeCAD.Console.PrintError("No Nodes found in mesh!\n")
    return mesh


def readResultVTK(vtk_input, meshChanging = False):
    """ read *.vtk ascii legacy file, containing mesh points and cells,  and values on points
    it is assumed polyhydral cell is broken down to tetra or hex cells(as default in foamToVTK)
    only 3D cell types:  hex, tetra, prism and pyramid are supported
    VTK binary and ascii(textual) file can be import using VTK python library
    """
    mesh_loaded = False
    if isinstance(vtk_input, (list, tuple)):
        vtk_list = vtk_input
    else:
        vtk_list = [vtk_input]

    results = []  # list of result for all time steps
    for i, vtk_file in enumerate(vtk_list):
        reader = vtk.vtkUnstructuredGridReader()
        reader.SetFileName(vtk_file)
        reader.ReadAllVectorsOn()
        #reader.ReadAllScalersOn()
        reader.Update() # Needed because of GetScalarRange
        data = reader.GetOutput()

        result_set = {}
        if i == 0 and not meshChanging:
            mesh_data = data
        else:
            mesh_data = None

        #timestep parse
        ts = vtk_input.split('_')[-1]
        time_step = float(ts[:-4])
        FreeCAD.Console.PrintMessage("parsed the time step {}\n".format(time_step))

        pointData = data.GetPointData()
        nPoints = data.GetNumberOfPoints()
        U = pointData.GetArray('U')
        #vel = VN.vtk_to_numpy(U)
        Ux = np.zeros(nPoints)
        Uy = np.zeros(nPoints)
        Uz = np.zeros(nPoints)
        velocity = []
        for i in range(U.GetNumberOfTuples()):
            t = U.GetTuple(i)
            Ux[i] = t[0]
            Uy[i] = t[1]
            Uz[i] = t[2]
            velocity.append(FreeCAD.Vector(*t))
        Umag = np.sqrt(Ux*Ux + Uy*Uy + Uz*Uz)
        p = VN.vtk_to_numpy(pointData.GetArray('p'))
        result_set = {'Pressure': p, 'Velocity': velocity, 'Ux': Ux, 'Uy': Uy, 'Uz': Uz, 'Umag': Umag}

        try:
            T = VN.vtk_to_numpy(pointData.GetArray('T'))
            result_set['Temperature'] = T
        except:
            pass
        # for turbulence variables

        results.append({'Time': time_step, "Mesh": mesh_data, "Result": result_set})

    return results


## import result data, create ResultObject and show result within FemMesh
#   parameter filename: support multiple filename as a list
def importVTK(filename, analysis=None, result_name_prefix=None):
    if result_name_prefix is None:
        result_name_prefix = ''

    all_results = readResultVTK(filename)
    print("data imported")
    if analysis is None:
        analysis_name = os.path.splitext(os.path.basename(filename))[0]
        import CfdAnalysis  # FemAnalysis -> CfdAnalysis
        analysis_object = CfdAnalysis.makeCfdAnalysis('CfdAnalysis')
        analysis_object.Label = analysis_name
    else:
        analysis_object = analysis  # see if statement few lines later, if not analysis -> no FemMesh object is created !

    number_of_timesteps = len(all_results)  # number_of_increments -> number_of_timesteps
    mesh_object = None
    # add a new result object for each time step, also create a mesh if mesh_data is not None
    for this_result in all_results:  
        result_set = this_result['Result']
        time_step = this_result['Time']
        mesh_data = this_result['Mesh']

        # pressure and velocity must existents for CFD result
        if ("Velocity" not in result_set) or ("Pressure" not in result_set):
            FreeCAD.Console.PrintMessage("Warning: no velocity and pressure field for time: {}".format(time_step))
            continue

        if mesh_data:  # Mesh node coordination should not be empty
            #from FemMeshTools import make_femmesh
            mesh = buildMeshFromVTK(mesh_data)
            # create a new ResultMesh  which can be diff from solver input mesh
            mesh_object = FreeCAD.ActiveDocument.addObject('Fem::FemMeshObject', 'ResultMesh')
            mesh_object.FemMesh = mesh
            analysis_object.Member = analysis_object.Member + [mesh_object]

        #step_time = round(step_time, 2)
        if number_of_timesteps > 1:
            result_obj_name = result_name_prefix + 'time_' + str(time_step) + '_result'
        else:
            result_obj_name = result_name_prefix + 'result'

        #result_obj= FreeCAD.ActiveDocument.addObject('Fem::FemResultObject', result_obj_name)
        from CfdResult import makeCfdResult
        result_obj = makeCfdResult(result_obj_name)
        for m in analysis_object.Member:
            if m.isDerivedFrom("Fem::FemMeshObject"):
                result_obj.Mesh = m  # binding the first found mesh to this result object
                break

        result_obj.Time = time_step
        result_obj.Pressure = result_set['Pressure'].tolist()  # StressValues -> Pressure
        nPoints = (result_set['Pressure']).shape[0]
        result_obj.NodeNumbers = range(1, nPoints+1)
        vel = result_set["Velocity"]

        if len(vel) > 0:  # DisplacementVectors -> Velocity
            result_obj.Velocity = vel
            if(mesh_object):
                result_obj.Mesh = mesh_object
        # Read temperatures if they exist
        stats = [0 for i in range(30)]
        stats[:3] = (np.min(result_set["Ux"]), np.mean(result_set["Ux"]), np.max(result_set["Ux"]))
        stats[3:6] = (np.min(result_set["Uy"]), np.mean(result_set["Uy"]), np.max(result_set["Uy"]))
        stats[6:9] = (np.min(result_set["Uz"]), np.mean(result_set["Uz"]), np.max(result_set["Uz"]))
        stats[9:12] = (np.min(result_set["Umag"]), np.mean(result_set["Umag"]), np.max(result_set["Umag"]))
        stats[12:15] = (np.min(result_set["Pressure"]), np.mean(result_set["Pressure"]), np.max(result_set["Pressure"]))
        try:
            temperature = result_set['Temperature'].tolist()
            if len(temperature) > 0:
                result_obj.Temperature = temperature
                stats[15:18] = (np.min(result_set["Temperature"]), np.mean(result_set["Temperature"]), np.max(result_set["Temperature"]))
        except:
            pass
        # turbulence variables
        result_obj.Stats = stats.tolist()
        
    # end of time steps loop
    if(FreeCAD.GuiUp):
        import FemGui
        FemGui.setActiveAnalysis(analysis_object)
