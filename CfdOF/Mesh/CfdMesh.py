# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2019-2024 Oliver Oxtoby <oliveroxtoby@gmail.com>        *
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

import os

import FreeCAD
import FreeCADGui

from CfdOF import CfdTools
from CfdOF.CfdTools import addObjectProperty

MESHER_DESCRIPTIONS = ["cfMesh", "snappyHexMesh", "gmsh (tetrahedral)", "gmsh (polyhedral)"]
MESHERS = ["cfMesh", "snappyHexMesh", "gmsh", "gmsh"]
DIMENSION = ["3D", "3D", "3D", "3D"]
DUAL_CONVERSION = [False, False, False, True]

QT_TRANSLATE_NOOP = FreeCAD.Qt.QT_TRANSLATE_NOOP


def makeCfdMesh(name="CFDMesh"):
    obj = FreeCAD.ActiveDocument.addObject("App::DocumentObjectGroupPython", name)
    CfdMesh(obj)
    if FreeCAD.GuiUp:
        ViewProviderCfdMesh(obj.ViewObject)
    return obj


class CommandCfdMeshFromShape:
    def GetResources(self):
        icon_path = os.path.join(CfdTools.getModulePath(), "Gui", "Icons", "mesh.svg")
        return {'Pixmap': icon_path,
                'MenuText': QT_TRANSLATE_NOOP("CfdOF_MeshFromShape",
                                                     "CFD mesh"),
                'ToolTip': QT_TRANSLATE_NOOP("CfdOF_MeshFromShape",
                                                    "Create a mesh using cfMesh, snappyHexMesh or gmsh")}

    def IsActive(self):
        sel = FreeCADGui.Selection.getSelection()
        analysis = CfdTools.getActiveAnalysis()
        existing_mesh = CfdTools.getMesh(analysis)
        return existing_mesh is not None or (
            analysis is not None and sel and len(sel) == 1 and sel[0].isDerivedFrom("Part::Feature") and
            not sel[0].Shape.isNull())

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
                        FreeCADGui.doCommand("from CfdOF.Mesh import CfdMesh")
                        FreeCADGui.doCommand("CfdMesh.makeCfdMesh('" + mesh_obj_name + "')")
                        FreeCADGui.doCommand("App.ActiveDocument.ActiveObject.Part = App.ActiveDocument." + sel[0].Name)
                        if CfdTools.getActiveAnalysis():
                            FreeCADGui.doCommand("from CfdOF import CfdTools")
                            FreeCADGui.doCommand(
                                "CfdTools.getActiveAnalysis().addObject(App.ActiveDocument.ActiveObject)")
                        FreeCADGui.ActiveDocument.setEdit(FreeCAD.ActiveDocument.ActiveObject.Name)
            else:
                FreeCADGui.activeDocument().setEdit(mesh_obj.Name)
        FreeCADGui.Selection.clearSelection()


class CfdMesh:
    """ CFD mesh properties """

    # Variables that need to be used outside this class and therefore are included outside of the constructor
    known_element_dimensions = ['2D', '3D']

    def __init__(self, obj):
        self.Type = "CfdMesh"
        self.Object = obj
        obj.Proxy = self
        self.initProperties(obj)

    def initProperties(self, obj):
        addObjectProperty(
            obj,
            "CaseName",
            "meshCase",
            "App::PropertyString",
            "",
            QT_TRANSLATE_NOOP("App::Property", "Name of directory in which the mesh is created"),
        )

        # Setup and utility
        addObjectProperty(
            obj,
            "STLRelativeLinearDeflection",
            0.001,
            "App::PropertyFloat",
            "Surface triangulation",
            QT_TRANSLATE_NOOP(
                "App::Property",
                "Maximum relative linear deflection for built-in surface triangulation",
            ),
        )
        addObjectProperty(
            obj,
            "STLAngularMeshDensity",
            100,
            "App::PropertyFloat",
            "Surface triangulation",
            QT_TRANSLATE_NOOP(
                "App::Property", "Mesh elements per 360 degrees for surface triangulation with GMSH"
            ),
        )

        addObjectProperty(
            obj,
            "NumberOfProcesses",
            1,
            "App::PropertyInteger",
            "",
            QT_TRANSLATE_NOOP(
                "App::Property",
                "Number of parallel processes (only applicable to cfMesh and snappyHexMesh)",
            ),
        )

        addObjectProperty(
            obj,
            "NumberOfThreads",
            0,
            "App::PropertyInteger",
            "",
            QT_TRANSLATE_NOOP(
                "App::Property",
                "Number of parallel threads per process (only applicable to cfMesh and gmsh).\n"
                "0 means use all available (if NumberOfProcesses = 1) or use 1 (if NumberOfProcesses > 1)",
            ),
        )

        addObjectProperty(
            obj,
            "Part",
            None,
            "App::PropertyLinkGlobal",
            "Mesh Parameters",
            QT_TRANSLATE_NOOP("App::Property", "Part object to mesh"),
        )

        if addObjectProperty(
            obj,
            "MeshUtility",
            MESHERS,
            "App::PropertyEnumeration",
            "Mesh Parameters",
            QT_TRANSLATE_NOOP("App::Property", "Meshing utilities"),
        ):
            obj.MeshUtility = MESHERS[0]

        # Refinement
        addObjectProperty(
            obj,
            "CharacteristicLengthMax",
            "0 m",
            "App::PropertyLength",
            "Mesh Parameters",
            QT_TRANSLATE_NOOP("App::Property", "Max mesh element size (0.0 = infinity)"),
        )

        addObjectProperty(
            obj,
            "PointInMesh",
            {"x": "0 m", "y": "0 m", "z": "0 m"},
            "App::PropertyMap",
            "Mesh Parameters",
            QT_TRANSLATE_NOOP(
                "App::Property",
                "Location vector inside the region to be meshed (must not coincide with a cell face)",
            ),
        )

        addObjectProperty(
            obj,
            "CellsBetweenLevels",
            3,
            "App::PropertyInteger",
            "Mesh Parameters",
            QT_TRANSLATE_NOOP("App::Property", "Number of cells between each level of refinement"),
        )

        addObjectProperty(
            obj,
            "EdgeRefinement",
            1,
            "App::PropertyFloat",
            "Mesh Parameters",
            QT_TRANSLATE_NOOP("App::Property", "Relative edge (feature) refinement"),
        )

        # PolyDualMesh
        addObjectProperty(
            obj,
            "ConvertToDualMesh",
            False,
            "App::PropertyBool",
            "Mesh Parameters",
            QT_TRANSLATE_NOOP("App::Property", "Convert to polyhedral dual mesh"),
        )

        # Edge detection, implicit / explicit (NB Implicit = False implies Explicit = True)
        addObjectProperty(
            obj,
            "ImplicitEdgeDetection",
            False,
            "App::PropertyBool",
            "Mesh Parameters",
            QT_TRANSLATE_NOOP("App::Property", "Use implicit edge detection"),
        )

        # Mesh dimension
        if addObjectProperty(
            obj,
            "ElementDimension",
            CfdMesh.known_element_dimensions,
            "App::PropertyEnumeration",
            "Mesh Parameters",
            QT_TRANSLATE_NOOP("App::Property", "Dimension of mesh elements (Default 3D)"),
        ):
            obj.ElementDimension = "3D"

    def onDocumentRestored(self, obj):
        self.initProperties(obj)

    def execute(self, obj):
        pass

    def __getstate__(self):
        return self.Type

    def __setstate__(self, state):
        if state:
            self.Type = state

    # dumps and loads replace __getstate__ and __setstate__ post v. 0.21.2
    def dumps(self):
        return self.Type

    def loads(self, state):
        if state:
            self.Type = state


class _CfdMesh:
    """ Backward compatibility for old class name when loading from file """
    def onDocumentRestored(self, obj):
        CfdMesh(obj)

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None

    # dumps and loads replace __getstate__ and __setstate__ post v. 0.21.2
    def dumps(self):
        return None

    def loads(self, state):
        return None


class ViewProviderCfdMesh:
    """ A View Provider for the CfdMesh object """
    def __init__(self, vobj):
        vobj.Proxy = self
        self.taskd = None
        self.num_refinement_objs = 0
        self.num_dyn_refinement_objs = 0

    def getIcon(self):
        icon_path = os.path.join(CfdTools.getModulePath(), "Gui", "Icons", "mesh.svg")
        return icon_path

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object

    def updateData(self, obj, prop):
        analysis_obj = CfdTools.getParentAnalysisObject(obj)
        num_refinement_objs = len(CfdTools.getMeshRefinementObjs(obj))
        num_dyn_refinement_objs = (0 if CfdTools.getDynamicMeshAdaptation(obj) is None else 1)
        if prop == "Group":
            if analysis_obj and not analysis_obj.Proxy.loading:
                if num_refinement_objs != self.num_refinement_objs:
                    analysis_obj.NeedsMeshRewrite = True
            if analysis_obj and not analysis_obj.Proxy.loading:
                if num_dyn_refinement_objs != self.num_dyn_refinement_objs:
                    analysis_obj.NeedsCaseRewrite = True
            self.num_refinement_objs = num_refinement_objs
            self.num_dyn_refinement_objs = num_dyn_refinement_objs
        else:
            if analysis_obj and not analysis_obj.Proxy.loading:
                if prop == "_GroupTouched":
                    if (analysis_obj and analysis_obj.Proxy.ignore_next_grouptouched):
                        analysis_obj.Proxy.ignore_next_grouptouched = False
                    else:
                        analysis_obj.NeedsMeshRewrite = True
                else:
                    analysis_obj.NeedsMeshRewrite = True

    def onChanged(self, vobj, prop):
        #CfdTools.setCompSolid(vobj)
        return

    def setEdit(self, vobj, mode):
        for obj in FreeCAD.ActiveDocument.Objects:
            if hasattr(obj, 'Proxy') and isinstance(obj.Proxy, CfdMesh):
                obj.ViewObject.show()

        if self.Object.Part is None:
            FreeCAD.Console.PrintError("Meshed part no longer exists")
            return False

        from CfdOF.Mesh import TaskPanelCfdMesh
        import importlib
        importlib.reload(TaskPanelCfdMesh)
        self.taskd = TaskPanelCfdMesh.TaskPanelCfdMesh(self.Object)
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

    # dumps and loads replace __getstate__ and __setstate__ post v. 0.21.2
    def dumps(self):
        return None

    def loads(self, state):
        return None


class _ViewProviderCfdMesh:
    """ Backward compatibility for old class name when loading from file """
    def attach(self, vobj):
        new_proxy = ViewProviderCfdMesh(vobj)
        new_proxy.attach(vobj)

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None

    # dumps and loads replace __getstate__ and __setstate__ post v. 0.21.2
    def dumps(self):
        return None

    def loads(self, state):
        return None
