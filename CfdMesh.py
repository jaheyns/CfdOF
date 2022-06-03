# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2019-2022 Oliver Oxtoby <oliveroxtoby@gmail.com>        *
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

from __future__ import print_function

import FreeCAD
import FreeCADGui
from PySide import QtCore
import CfdTools
from CfdTools import addObjectProperty
import os


MESHER_DESCRIPTIONS = ['cfMesh', 'snappyHexMesh', 'gmsh (tetrahedral)', 'gmsh (polyhedral)']
MESHERS = ['cfMesh', 'snappyHexMesh', 'gmsh', 'gmsh']
DIMENSION = ['3D', '3D', '3D', '3D']
DUAL_CONVERSION = [False, False, False, True]


def makeCfdMesh(name="CFDMesh"):
    obj = FreeCAD.ActiveDocument.addObject("App::DocumentObjectGroupPython", name)
    _CfdMesh(obj)
    if FreeCAD.GuiUp:
        _ViewProviderCfdMesh(obj.ViewObject)
    return obj


class _CommandCfdMeshFromShape:
    def GetResources(self):
        icon_path = os.path.join(CfdTools.get_module_path(), "Gui", "Resources", "icons", "mesh.svg")
        return {'Pixmap': icon_path,
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Cfd_MeshFromShape",
                                                     "CFD mesh"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Cfd_MeshFromShape",
                                                    "Create a mesh using cfMesh, snappyHexMesh or gmsh")}

    def IsActive(self):
        sel = FreeCADGui.Selection.getSelection()
        analysis = CfdTools.getActiveAnalysis()
        return analysis is not None and sel and len(sel) == 1 and sel[0].isDerivedFrom("Part::Feature")

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Create CFD mesh")
        analysis_obj = CfdTools.getActiveAnalysis()
        if analysis_obj:
            mesh_obj = CfdTools.getMesh(analysis_obj)
            if not mesh_obj:
                sel = FreeCADGui.Selection.getSelection()
                if len(sel) == 1:
                    if sel[0].isDerivedFrom("Part::Feature"):
                        mesh_obj_name = sel[0].Name + "_Mesh"
                        FreeCADGui.addModule("CfdMesh")
                        FreeCADGui.doCommand("CfdMesh.makeCfdMesh('" + mesh_obj_name + "')")
                        FreeCADGui.doCommand("App.ActiveDocument.ActiveObject.Part = App.ActiveDocument." + sel[0].Name)
                        if CfdTools.getActiveAnalysis():
                            FreeCADGui.addModule("CfdTools")
                            FreeCADGui.doCommand(
                                "CfdTools.getActiveAnalysis().addObject(App.ActiveDocument.ActiveObject)")
                        FreeCADGui.ActiveDocument.setEdit(FreeCAD.ActiveDocument.ActiveObject.Name)
            else:
                print("ERROR: You cannot have more than one mesh object")
        FreeCADGui.Selection.clearSelection()


class _CfdMesh:
    """ CFD mesh properties """

    # Variables that need to be used outside this class and therefore are included outside of the constructor
    known_element_dimensions = ['2D', '3D']

    def __init__(self, obj):
        self.Type = "CfdMesh"
        self.Object = obj
        obj.Proxy = self
        self.initProperties(obj)

    def initProperties(self, obj):
        addObjectProperty(obj, 'CaseName', "meshCase", "App::PropertyString", "",
                          "Name of directory in which the mesh is created")

        # Setup and utility
        addObjectProperty(obj, 'STLRelativeLinearDeflection', 1, "App::PropertyFloat", "Surface triangulation", 
                          "Maximum relative linear deflection for built-in surface triangulation")
        addObjectProperty(obj, 'STLAngularMeshDensity', 100, "App::PropertyFloat", "Surface triangulation", 
                          "Mesh elements per 360 degrees for surface triangulation with GMSH")

        addObjectProperty(obj, 'NumberOfProcesses', 1, "App::PropertyInteger", "",
                          "Number of parallel processes (only applicable to cfMesh and snappyHexMesh)")

        addObjectProperty(obj, 'NumberOfThreads', 0, "App::PropertyInteger", "",
                          "Number of parallel threads per process (only applicable to cfMesh and gmsh). "
                          "0 means use all available (if NumberOfProcesses = 1) or use 1 (if NumberOfProcesses > 1)")

        addObjectProperty(obj, "Part", None, "App::PropertyLink", "Mesh Parameters", "Part object to mesh")

        if addObjectProperty(obj, "MeshUtility", MESHERS, "App::PropertyEnumeration",
                             "Mesh Parameters", "Meshing utilities"):
            obj.MeshUtility = MESHERS[0]

        # Refinement
        addObjectProperty(obj, "CharacteristicLengthMax", "0 m", "App::PropertyLength", "Mesh Parameters",
                          "Max mesh element size (0.0 = infinity)")

        addObjectProperty(obj, 'PointInMesh', {"x": '0 m', "y": '0 m', "z": '0 m'}, "App::PropertyMap",
                          "Mesh Parameters",
                          "Location vector inside the region to be meshed (must not coincide with a cell face)")

        addObjectProperty(obj, 'CellsBetweenLevels', 3, "App::PropertyInteger", "Mesh Parameters",
                          "Number of cells between each level of refinement")

        addObjectProperty(obj, 'EdgeRefinement', 1, "App::PropertyFloat", "Mesh Parameters",
                          "Relative edge (feature) refinement")

        # PolyDualMesh
        addObjectProperty(obj, 'ConvertToDualMesh', False, "App::PropertyBool", "Mesh Parameters",
                          "Convert to polyhedral dual mesh")

        # Edge detection, implicit / explicit (NB Implicit = False implies Explicit = True)
        addObjectProperty(obj, 'ImplicitEdgeDetection', False, "App::PropertyBool", "Mesh Parameters",
                          "Use implicit edge detection")

        # Mesh dimension
        if addObjectProperty(obj, 'ElementDimension', _CfdMesh.known_element_dimensions, "App::PropertyEnumeration",
                             "Mesh Parameters", "Dimension of mesh elements (Default 3D)"):
            obj.ElementDimension = '3D'

    def onDocumentRestored(self, obj):
        self.initProperties(obj)

    def execute(self, obj):
        pass

    def __getstate__(self):
        return self.Type

    def __setstate__(self, state):
        if state:
            self.Type = state


class _ViewProviderCfdMesh:
    """ A View Provider for the CfdMesh object """
    def __init__(self, vobj):
        vobj.Proxy = self
        self.taskd = None

    def getIcon(self):
        icon_path = os.path.join(CfdTools.get_module_path(), "Gui", "Resources", "icons", "mesh.svg")
        return icon_path

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object

    def updateData(self, obj, prop):
        gui_doc = FreeCADGui.getDocument(obj.Document)
        # Ignore this notification when coming out of edit mode, since already accounted for during editing of
        # properties themselves
        if gui_doc.getInEdit() and prop == "_GroupTouched":
            return
        analysis_obj = CfdTools.getParentAnalysisObject(obj)
        if analysis_obj and not analysis_obj.Proxy.loading:
            analysis_obj.NeedsMeshRewrite = True

    def onChanged(self, vobj, prop):
        CfdTools.setCompSolid(vobj)

    def setEdit(self, vobj, mode):
        for obj in FreeCAD.ActiveDocument.Objects:
            if hasattr(obj, 'Proxy') and isinstance(obj.Proxy, _CfdMesh):
                obj.ViewObject.show()

        if self.Object.Part is None:
            FreeCAD.Console.PrintError("Meshed part no longer exists")
            return False

        import _TaskPanelCfdMesh
        import importlib
        importlib.reload(_TaskPanelCfdMesh)
        self.taskd = _TaskPanelCfdMesh._TaskPanelCfdMesh(self.Object)
        self.taskd.obj = vobj.Object
        FreeCADGui.Control.showDialog(self.taskd)
        return True

    def unsetEdit(self, vobj, mode):
        if self.taskd:
            self.taskd.closed()
            self.taskd = None
        FreeCADGui.Control.closeDialog()

    def doubleClicked(self, vobj):
        if FreeCADGui.activeWorkbench().name() != 'CfdOFWorkbench':
            FreeCADGui.activateWorkbench("CfdOFWorkbench")
        gui_doc = FreeCADGui.getDocument(vobj.Object.Document)
        if not gui_doc.getInEdit():
            gui_doc.setEdit(vobj.Object.Name)
        else:
            FreeCAD.Console.PrintError('Task dialog already open\n')
            FreeCADGui.Control.showTaskView()
        return True

    def onDelete(self, feature, subelements):
        try:
            for obj in self.Object.Group:
                obj.ViewObject.show()
        except Exception as err:
            FreeCAD.Console.PrintError("Error in onDelete: " + str(err))
        return True

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None
