# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2016 - Bernd Hahnebach <bernd@bimstatik.org>            *
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

import FreeCAD
from FreeCAD import Base
from FreeCAD import Units
import FreeCADGui
from CfdMesh import _CfdMesh
from PySide import QtCore
from pivy import coin
import os
import CfdTools
from CfdTools import addObjectProperty
import _TaskPanelCfdMeshRegion


def makeCfdMeshRegion(base_mesh, name="MeshRegion"):
    """ makeCfdMeshRegion([name]):
        Creates a  mesh region object to define properties for a region of the mesh
    """
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", name)
    _CfdMeshRegion(obj)
    # App::PropertyLinkList does not support append, we will use a temporary list to append the mesh region obj.
    tmplist = base_mesh.MeshRegionList
    tmplist.append(obj)
    base_mesh.MeshRegionList = tmplist
    if FreeCAD.GuiUp:
        _ViewProviderCfdMeshRegion(obj.ViewObject)
    return obj


class _CommandMeshRegion:

    def GetResources(self):
        icon_path = os.path.join(CfdTools.get_module_path(), "Gui", "Resources", "icons", "meshRegion.png")
        return {'Pixmap': icon_path,
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Cfd_MeshRegion", "Mesh region"),
                'Accel': "M, R",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Cfd_MeshRegion", "Creates a mesh region")}

    def IsActive(self):
        sel = FreeCADGui.Selection.getSelection()
        return sel and len(sel) == 1 and hasattr(sel[0], "Proxy") and isinstance(sel[0].Proxy, _CfdMesh)

    def Activated(self):
        sel = FreeCADGui.Selection.getSelection()
        if len(sel) == 1:
            sobj = sel[0]
            if len(sel) == 1 and hasattr(sobj, "Proxy") and isinstance(sobj.Proxy, _CfdMesh):
                FreeCAD.ActiveDocument.openTransaction("Create MeshRegion")
                FreeCADGui.doCommand("")
                FreeCADGui.addModule("CfdMeshRegion")
                FreeCADGui.doCommand("CfdMeshRegion.makeCfdMeshRegion(App.ActiveDocument." + sobj.Name + ")")
                FreeCADGui.ActiveDocument.setEdit(FreeCAD.ActiveDocument.ActiveObject.Name)

        FreeCADGui.Selection.clearSelection()


class PartFeature:
    def __init__(self, obj):
        obj.Proxy = self


class _CfdMeshRegion(PartFeature):

    def __init__(self, obj):
        PartFeature.__init__(self, obj)
        obj.Proxy = self
        self.Type = "CfdMeshRegion"
        self.initProperties(obj)

    def initProperties(self, obj):
        # Common to all
        addObjectProperty(obj, "RelativeLength", 0.75, "App::PropertyFloat", "",
                          "Set relative length of the elements for this region")

        addObjectProperty(obj, "References", [], "App::PropertyPythonObject", "",
                          "List of mesh region surfaces")

        #cfMesh:
        addObjectProperty(obj, "RefinementThickness", "0 m", "App::PropertyLength", "cfMesh",
                          "Set refinement region thickness")

        addObjectProperty(obj, "NumberLayers", 0, "App::PropertyInteger", "cfMesh",
                          "Set number of boundary layers")

        addObjectProperty(obj, "ExpansionRatio", 1.2, "App::PropertyFloat", "cfMesh",
                          "Set expansion ratio within boundary layers")

        addObjectProperty(obj, "FirstLayerHeight", "0 m", "App::PropertyLength", "cfMesh",
                          "Set the maximum first layer height")

        # cfMesh refinement type internal
        addObjectProperty(obj, "Internal", False, "App::PropertyBool", "cfMesh",
                          "Whether the refinement region is a volume rather than surface")

        internalRegion = {"Type": "Box",
                          "Center": {"x": '0 m', "y": '0 m', "z": '0 m'},
                          "BoxLengths": {"x": '1e-3 m', "y": '1e-3 m', "z": '1e-3 m'},
                          "SphereRadius": '1e-3 m',
                          "Point1": {"x": '0 m', "y": '0 m', "z": '0 m'},
                          "Point2": {"x": '0 m', "y": '0 m', "z": '0 m'},
                          "Radius1": '1e-3 m',
                          "Radius2": '1e-3 m'}
        addObjectProperty(obj, "InternalRegion", internalRegion, "App::PropertyPythonObject")

        # snappy:
        addObjectProperty(obj, "RegionEdgeRefinement", 1, "App::PropertyFloat", "snappyHexMesh",
                          "Relative edge (feature) refinement")

        addObjectProperty(obj, "Baffle", False, "App::PropertyBool", "snappyHexMesh",
                          "Create a zero thickness baffle")

    def onDocumentRestored(self, obj):
        self.initProperties(obj)

    def execute(self, obj):
        import Part
        #try for problem backward compatibility
        try:
            if obj.Internal:
                shape = None
                cx = Units.Quantity(obj.InternalRegion["Center"]["x"]).Value
                cy = Units.Quantity(obj.InternalRegion["Center"]["y"]).Value
                cz = Units.Quantity(obj.InternalRegion["Center"]["z"]).Value
                if obj.InternalRegion["Type"] == "Box":
                    lenx = Units.Quantity(obj.InternalRegion["BoxLengths"]["x"]).Value
                    leny = Units.Quantity(obj.InternalRegion["BoxLengths"]["y"]).Value
                    lenz = Units.Quantity(obj.InternalRegion["BoxLengths"]["z"]).Value
                    x = cx - lenx/2.0
                    y = cy - leny/2.0
                    z = cz - lenz/2.0
                    shape = Part.makeBox(lenx, leny, lenz, Base.Vector(x,y,z))

                elif obj.InternalRegion["Type"] == "Sphere":
                    rad = Units.Quantity(obj.InternalRegion["SphereRadius"]).Value
                    shape = Part.makeSphere(rad, Base.Vector(cx, cy, cz))
                elif obj.InternalRegion["Type"] == "Cone":
                    p1 = Base.Vector(Units.Quantity(obj.InternalRegion["Point1"]["x"]).Value,
                                     Units.Quantity(obj.InternalRegion["Point1"]["y"]).Value,
                                     Units.Quantity(obj.InternalRegion["Point1"]["z"]).Value)
                    p2 = Base.Vector(Units.Quantity(obj.InternalRegion["Point2"]["x"]).Value,
                                     Units.Quantity(obj.InternalRegion["Point2"]["y"]).Value,
                                     Units.Quantity(obj.InternalRegion["Point2"]["z"]).Value)
                    h = (p2-p1).Length
                    if h > 0:
                        if obj.InternalRegion["Radius1"] == obj.InternalRegion["Radius2"]:
                            # makeCone fails in this special case
                            shape = Part.makeCylinder(Units.Quantity(obj.InternalRegion["Radius1"]).Value,
                                                      h, p1, (p2-p1)/(h+1e-8))
                        else:
                            shape = Part.makeCone(Units.Quantity(obj.InternalRegion["Radius1"]).Value,
                                                  Units.Quantity(obj.InternalRegion["Radius2"]).Value,
                                                  h, p1, (p2-p1)/(h+1e-8))
                if shape:
                    obj.Shape = shape
                else:
                    obj.Shape = Part.Vertex()
            else:
                obj.Shape = Part.Vertex()
        except AttributeError:
            pass


class _ViewProviderCfdMeshRegion:
    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        icon_path = os.path.join(CfdTools.get_module_path(), "Gui", "Resources", "icons", "meshRegion.png")
        return icon_path

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object
        self.standard = coin.SoGroup()
        vobj.addDisplayMode(self.standard, "Standard")

    def getDisplayModes(self, obj):
        return ["Standard"]

    def getDefaultDisplayMode(self):
        return "Shaded"

    def updateData(self, obj, prop):
        return

    def setDisplayMode(self,mode):
        return mode

    def onChanged(self, vobj, prop):
        return

    def setEdit(self, vobj, mode=0):
        if vobj.Object.Internal:
            vobj.Object.ViewObject.show()

        for obj in FreeCAD.ActiveDocument.Objects:
            if obj.isDerivedFrom("Fem::FemMeshObject"):
                obj.ViewObject.hide()
                obj.Part.ViewObject.show()
        taskd = _TaskPanelCfdMeshRegion._TaskPanelCfdMeshRegion(self.Object)
        taskd.obj = vobj.Object
        FreeCADGui.Control.showDialog(taskd)
        return True

    def unsetEdit(self, vobj, mode=0):
        FreeCADGui.Control.closeDialog()
        return

    def doubleClicked(self, vobj):
        doc = FreeCADGui.getDocument(vobj.Object.Document)
        if not doc.getInEdit():
            doc.setEdit(vobj.Object.Name)
        else:
            FreeCAD.Console.PrintError('Task dialog already open\n')
        return True

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None
