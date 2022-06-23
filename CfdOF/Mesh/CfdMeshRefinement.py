# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2017 Johan Heyns (CSIR) <jheyns@csir.co.za>             *
# *   Copyright (c) 2017 Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>          *
# *   Copyright (c) 2017 Alfred Bogaers (CSIR) <abogaers@csir.co.za>        *
# *   Copyright (c) 2019-2022 Oliver Oxtoby <oliveroxtoby@gmail.com>        *
# *   Copyright (c) 2022 Jonathan bergh <bergh.jonathan@gmail.com>          *
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

import FreeCAD
import FreeCADGui
from CfdOF.Mesh.CfdMesh import CfdMesh
from PySide import QtCore
import os
from CfdOF import CfdTools
from CfdOF.CfdTools import addObjectProperty
from pivy import coin
import Part
from CfdOF.Mesh import TaskPanelCfdMeshRefinement

# Constants
EXTRUSION_NAMES = ["2D planar mesh", "2D wedge mesh", "Patch-normal", "Rotational"]
EXTRUSION_TYPES = ["2DPlanar", "2DWedge", "PatchNormal", "Rotational"]
EXTRUSION_UI = [[2], [6], [1, 2, 4, 5], [1, 3, 4, 5, 6]]


def makeCfdMeshRefinement(base_mesh, name="MeshRefinement"):
    """
    makeCfdMeshRefinement([name]): Creates an object to define refinement properties for a surface or region of the mesh
    """
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", name)
    CfdMeshRefinement(obj)
    if FreeCAD.GuiUp:
        ViewProviderCfdMeshRefinement(obj.ViewObject)
    base_mesh.addObject(obj)
    return obj


class CommandMeshRegion:

    def GetResources(self):
        icon_path = os.path.join(CfdTools.getModulePath(), "Gui", "Icons", "mesh_region.svg")
        return {'Pixmap': icon_path,
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Cfd_MeshRegion", "Mesh refinement"),
                'Accel': "M, R",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Cfd_MeshRegion", "Creates a mesh refinement")}

    def IsActive(self):
        sel = FreeCADGui.Selection.getSelection()
        return sel and len(sel) == 1 and hasattr(sel[0], "Proxy") and isinstance(sel[0].Proxy, CfdMesh)

    def Activated(self):
        sel = FreeCADGui.Selection.getSelection()
        if len(sel) == 1:
            sobj = sel[0]
            if len(sel) == 1 and hasattr(sobj, "Proxy") and isinstance(sobj.Proxy, CfdMesh):
                FreeCAD.ActiveDocument.openTransaction("Create MeshRegion")
                FreeCADGui.doCommand("")
                FreeCADGui.doCommand("from CfdOF.Mesh import CfdMeshRefinement")
                FreeCADGui.doCommand(
                    "CfdMeshRefinement.makeCfdMeshRefinement(App.ActiveDocument.{})".format(sobj.Name))
                FreeCADGui.ActiveDocument.setEdit(FreeCAD.ActiveDocument.ActiveObject.Name)

        FreeCADGui.Selection.clearSelection()


class CfdMeshRefinement:

    def __init__(self, obj):
        obj.Proxy = self
        self.Type = "CfdMeshRefinement"
        self.initProperties(obj)

    def initProperties(self, obj):
        # Common to all
        if addObjectProperty(obj, 'ShapeRefs', [], "App::PropertyLinkSubList", "", "List of mesh refinement objects"):
            # Backward compat
            if 'References' in obj.PropertiesList:
                doc = FreeCAD.getDocument(obj.Document.Name)
                for r in obj.References:
                    if not r[1]:
                        obj.ShapeRefs += [doc.getObject(r[0])]
                    else:
                        obj.ShapeRefs += [(doc.getObject(r[0]), r[1])]
                obj.removeProperty('References')
                obj.removeProperty('LinkedObjects')

        addObjectProperty(obj, "Internal", False, "App::PropertyBool", "",
                          "Whether the refinement region is a volume rather than surface")

        addObjectProperty(obj, "Extrusion", False, "App::PropertyBool", "",
                          "Defines an extrusion from a patch")

        addObjectProperty(obj, "RelativeLength", 0.75, "App::PropertyFloat", "Refinement",
                          "Set relative length of the elements for this region")

        addObjectProperty(obj, "RefinementThickness", "0 m", "App::PropertyLength", "Surface refinement",
                          "Set refinement region thickness")

        addObjectProperty(obj, "NumberLayers", 0, "App::PropertyInteger", "Surface refinement",
                          "Set number of boundary layers")

        addObjectProperty(obj, "ExpansionRatio", 1.0, "App::PropertyFloat", "Surface refinement",
                          "Set expansion ratio within boundary layers")

        addObjectProperty(obj, "FirstLayerHeight", "0 m", "App::PropertyLength", "Surface refinement",
                          "Set the maximum first layer height")

        addObjectProperty(obj, "RegionEdgeRefinement", 1, "App::PropertyFloat", "Surface refinement",
                          "Relative edge (feature) refinement")

        addObjectProperty(obj, "ExtrusionType", EXTRUSION_TYPES[0], "App::PropertyString", "Extrusion",
                          "Type of extrusion")

        addObjectProperty(obj, "KeepExistingMesh", False, "App::PropertyBool", "Extrusion",
                          "If true, then the extrusion extends the existing mesh rather than replacing it")

        addObjectProperty(obj, "ExtrusionThickness", "1 mm", "App::PropertyLength", "Extrusion",
                          "Total distance of the extruded layers")

        addObjectProperty(obj, "ExtrusionAngle", 5, "App::PropertyAngle", "Extrusion",
                          "Total angle through which the patch is extruded")

        addObjectProperty(obj, "ExtrusionLayers", 1, "App::PropertyInteger", "Extrusion",
                          "Number of extrusion layers to add")

        addObjectProperty(obj, "ExtrusionRatio", 1.0, "App::PropertyFloat", "Extrusion",
                          "Expansion ratio of extrusion layers")

        addObjectProperty(obj, "ExtrusionAxisPoint", FreeCAD.Vector(0, 0, 0), "App::PropertyPosition", "Extrusion",
                          "Point on axis for sector extrusion")

        addObjectProperty(obj, "ExtrusionAxisDirection", FreeCAD.Vector(1, 0, 0), "App::PropertyVector", "Extrusion",
                          "Direction of axis for sector extrusion")

    def onDocumentRestored(self, obj):
        self.initProperties(obj)

    def execute(self, obj):
        """ Create compound part at recompute. """
        shape = CfdTools.makeShapeFromReferences(obj.ShapeRefs, False)
        if shape is None:
            shape = Part.Shape()
        if not CfdTools.isSameGeometry(obj.Shape, shape):
            obj.Shape = shape
        if FreeCAD.GuiUp:
            vobj = obj.ViewObject
            vobj.Transparency = 20
            vobj.ShapeColor = (1.0, 0.4, 0.0)  # Orange


class _CfdMeshRefinement:
    """ Backward compatibility for old class name when loading from file """
    def onDocumentRestored(self, obj):
        CfdMeshRefinement(obj)


class ViewProviderCfdMeshRefinement:
    def __init__(self, vobj):
        vobj.Proxy = self
        self.taskd = None

    def getIcon(self):
        icon_path = os.path.join(CfdTools.getModulePath(), "Gui", "Icons", "mesh_region.svg")
        return icon_path

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object
        self.standard = coin.SoGroup()
        vobj.addDisplayMode(self.standard, "Standard")

    def getDisplayModes(self, obj):
        modes = []
        return modes

    def getDefaultDisplayMode(self):
        return "Shaded"

    def setDisplayMode(self, mode):
        return mode

    def updateData(self, obj, prop):
        analysis_obj = CfdTools.getParentAnalysisObject(obj)
        if analysis_obj and not analysis_obj.Proxy.loading:
            analysis_obj.NeedsMeshRewrite = True

    def onChanged(self, vobj, prop):
        return

    def setEdit(self, vobj, mode=0):
        import importlib
        importlib.reload(TaskPanelCfdMeshRefinement)
        self.taskd = TaskPanelCfdMeshRefinement.TaskPanelCfdMeshRefinement(self.Object)
        self.taskd.obj = vobj.Object
        FreeCADGui.Control.showDialog(self.taskd)
        return True

    def doubleClicked(self, vobj):
        doc = FreeCADGui.getDocument(vobj.Object.Document)
        if not doc.getInEdit():
            doc.setEdit(vobj.Object.Name)
        else:
            FreeCAD.Console.PrintError('Task dialog already open\n')
            FreeCADGui.Control.showTaskView()
        return True

    def unsetEdit(self, vobj, mode):
        if self.taskd:
            self.taskd.closing()
            self.taskd = None
        FreeCADGui.Control.closeDialog()

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None


class _ViewProviderCfdMeshRefinement:
    """ Backward compatibility for old class name when loading from file """
    def attach(self, vobj):
        new_proxy = ViewProviderCfdMeshRefinement(vobj)
        new_proxy.attach(vobj)

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None
