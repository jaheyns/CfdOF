# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2022 Jonathan Bergh <bergh.jonathan@gmail.com>          *
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

from __future__ import print_function

import FreeCAD
import FreeCADGui
from pivy import coin
from PySide import QtCore
import Part
import CfdTools
from CfdTools import addObjectProperty
import os

OBJECT_NAMES = ["Force", "ForceCoefficients"]
OBJECT_DESCRIPTIONS = ["Calculate forces on patches", "Calculate force coefficients from patches"]

# For each sub-type, whether the basic tab is enabled, the panel numbers to show (ignored if false), whether
# direction reversal is checked by default (only used for panel 0), whether turbulent inlet panel is shown,
# whether volume fraction panel is shown, whether thermal GUI is shown,
# rows of thermal UI to show (all shown if None)

# todo adapt all this
BOUNDARY_UI = [[True, False, True],     # Forces
               [True, True, True, ]]   # Force coefficients


def makeCfdFunctionObject(name="CFDFunctionObject"):
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", name)
    _CfdFunctionObjects(obj)
    if FreeCAD.GuiUp:
        _ViewProviderCfdFunctionObjects(obj.ViewObject)
    return obj


class _CommandCfdFunctionObjects:
    def GetResources(self):
        icon_path = os.path.join(CfdTools.get_module_path(), "Gui", "Resources", "icons", "functionobjects.png")
        return {'Pixmap': icon_path,
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Cfd_FunctionObjects",
                                                     "CFD function object"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Cfd_FunctionObjects",
                                                    "Create a function object for the current case")}

    def IsActive(self):
        return CfdTools.getActiveAnalysis() is not None     # Same as for boundary condition commands

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Create CfdFunctionObjects object")
        FreeCADGui.doCommand("")
        FreeCADGui.addModule("core.functionobjects.CfdFunctionObjects as CfdFunctionObjects")
        FreeCADGui.addModule("CfdTools")
        FreeCADGui.doCommand("CfdTools.getActiveAnalysis().addObject(CfdFunctionObjects.makeCfdFunctionObject())")
        FreeCADGui.ActiveDocument.setEdit(FreeCAD.ActiveDocument.ActiveObject.Name)


class _CfdFunctionObjects:
    """ CFD Function objects properties """

    def __init__(self, obj):
        self.Type = "CfdFunctionObjects"
        self.Object = obj
        obj.Proxy = self
        self.initProperties(obj)

    def initProperties(self, obj):
        # if addObjectProperty(obj, 'ShapeRefs', [], "App::PropertyLinkSubList", "", "Boundary faces"): # TODO check if we need this, otherwise remove
        #     # Backward compatible
        #     if 'References' in obj.PropertiesList:
        #         doc = FreeCAD.getDocument(obj.Document.Name)
        #         for r in obj.References:
        #             if not r[1]:
        #                 obj.ShapeRefs += [doc.getObject(r[0])]
        #             else:
        #                 obj.ShapeRefs += [(doc.getObject(r[0]), r[1])]
        #         obj.removeProperty('References')
        #         obj.removeProperty('LinkedObjects')

        addObjectProperty(obj, 'CaseName', "meshCase", "App::PropertyString", "",
                          "Name of directory in which the mesh is created")

        # Setup and utility
        addObjectProperty(obj, 'FunctionObjectType', "functionObjectType", "App::PropertyString", "Function object",
                          "Name of the function object to be created")

        addObjectProperty(obj, 'PatchName', "", "App::PropertyString", "Function object",
                          "Name of the patch on which to create the function object")

        # Forces
        # Field names
        addObjectProperty(obj, 'Pressure', 'p', "App::PropertyString", "Function object",
                          "Pressure field name")
        addObjectProperty(obj, 'Velocity', 'U', "App::PropertyString", "Function object",
                          "Velocity field name")
        addObjectProperty(obj, 'ReferencePressure', '0 Pa', "App::PropertyPressure", "Function object",
                          "Reference pressure")
        addObjectProperty(obj, 'Density', 'rho', "App::PropertyString", "Function object",
                          "Density field name")
        # addObjectProperty(obj, 'CentreOfRotation', '0, 0, 0', "App::PropertyString", "Function object",
        #                   "Centre of Rotation (x, y, z)")
        addObjectProperty(obj, 'CoRx', '0', "App::PropertyQuantity", "Function object",
                          "Centre of rotation (x component)")
        addObjectProperty(obj, 'CoRy', '0', "App::PropertyQuantity", "Function object",
                          "Centre of rotation (y component)")
        addObjectProperty(obj, 'CoRz', '0', "App::PropertyQuantity", "Function object",
                          "Centre of rotation (z component)")
        addObjectProperty(obj, 'IncludePorosity', False, "App::PropertyBool", "Function object",
                          "Whether to include porosity effects")
        addObjectProperty(obj, 'WriteFields', False, "App::PropertyBool", "Function object",
                          "Whether to write output fields")

        # Force coefficients
        # addObjectProperty(obj, 'LiftDirection', '0, 0, 0', "App::PropertyString", "Function object",
        #                   "Lift Direction vector (x, y, z)")
        addObjectProperty(obj, 'Liftx', '1', "App::PropertyQuantity", "Function object",
                          "Lift direction (x component)")
        addObjectProperty(obj, 'Lifty', '0', "App::PropertyQuantity", "Function object",
                          "Lift direction (y component)")
        addObjectProperty(obj, 'Liftz', '0', "App::PropertyQuantity", "Function object",
                          "Lift direction (z component)")

        # addObjectProperty(obj, 'DragDirection', '0, 0, 0', "App::PropertyString", "Function object",
        #                   "Drag direction vector (x, y, z)")
        addObjectProperty(obj, 'Dragx', '0', "App::PropertyQuantity", "Function object",
                          "Drag direction (x component)")
        addObjectProperty(obj, 'Dragy', '1', "App::PropertyQuantity", "Function object",
                          "Drag direction (y component)")
        addObjectProperty(obj, 'Dragz', '0', "App::PropertyQuantity", "Function object",
                          "Drag direction (z component)")

        # addObjectProperty(obj, 'PitchAxis', '0, 0, 0', "App::PropertyString", "Function object",
        #                   "Pitch axis for moment coefficient")
        addObjectProperty(obj, 'Pitchx', '0', "App::PropertyQuantity", "Function object",
                          "Centre of pitch (x component)")
        addObjectProperty(obj, 'Pitchy', '0', "App::PropertyQuantity", "Function object",
                          "Centre of pitch (y component)")
        addObjectProperty(obj, 'Pitchz', '1', "App::PropertyQuantity", "Function object",
                          "Centre of pitch (z component)")

        addObjectProperty(obj, 'MagnitudeUInf', '1 m/s', "App::PropertyQuantity", "Function object",
                          "Freestream velocity magnitude")
        addObjectProperty(obj, 'LengthRef', '1 m', "App::PropertyQuantity", "Function object",
                          "Coefficient length reference")
        addObjectProperty(obj, 'AreaRef', '1 m^2', "App::PropertyQuantity", "Function object",
                          "Coefficient area reference")

        # Spatial binning
        addObjectProperty(obj, 'NBins', '0', "App::PropertyQuantity", "Function object",
                          "Number of bins")
        addObjectProperty(obj, 'Direction', '0', "App::PropertyQuantity", "Function object",
                          "Direction")
        addObjectProperty(obj, 'Cumulative', True, "App::PropertyBool", "Function object",
                          "Cumulative")

    def onDocumentRestored(self, obj):
        self.initProperties(obj)

    def execute(self, obj):
        """ Create compound part at recompute. """
        pass
        # shape = CfdTools.makeShapeFromReferences(obj.ShapeRefs, False)
        # if shape is None:
        #     obj.Shape = Part.Shape()
        # else:
        #     obj.Shape = shape
        # self.updateBoundaryColors(obj)

    def updateBoundaryColors(self, obj): # todo come back and fix me
        pass
        # if FreeCAD.GuiUp:
        #     vobj = obj.ViewObject
        #     vobj.Transparency = 20
        #     if obj.BoundaryType == 'wall':
        #         vobj.ShapeColor = (0.1, 0.1, 0.1)  # Dark grey
        #     elif obj.BoundaryType == 'inlet':
        #         vobj.ShapeColor = (0.0, 0.0, 1.0)  # Blue
        #     elif obj.BoundaryType == 'outlet':
        #         vobj.ShapeColor = (1.0, 0.0, 0.0)  # Red
        #     elif obj.BoundaryType == 'open':
        #         vobj.ShapeColor = (0.0, 1.0, 1.0)  # Cyan
        #     elif (obj.BoundaryType == 'constraint') or \
        #          (obj.BoundaryType == 'baffle'):
        #         vobj.ShapeColor = (0.5, 0.0, 1.0)  # Purple
        #     else:
        #         vobj.ShapeColor = (1.0, 1.0, 1.0)  # White

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None


class _ViewProviderCfdFunctionObjects:
    """
    A View Provider for the CfdFunctionObjects object
    """
    def __init__(self, vobj):
        vobj.Proxy = self
        self.taskd = None

    def getIcon(self):
        icon_path = os.path.join(CfdTools.get_module_path(), "Gui", "Resources", "icons", "functionobjects.png")
        return icon_path

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object
        self.standard = coin.SoGroup()
        vobj.addDisplayMode(self.standard, "Standard")
        #self.ViewObject.Transparency = 95
        return

    def getDisplayModes(self, obj):
        modes = []
        return modes

    def getDefaultDisplayMode(self):
        return "Shaded"

    def setDisplayMode(self,mode):
        return mode

    def updateData(self, obj, prop):
        return

    def onChanged(self, vobj, prop):
        CfdTools.setCompSolid(vobj)
        return

    def doubleClicked(self, vobj):
        doc = FreeCADGui.getDocument(vobj.Object.Document)
        if not doc.getInEdit():
            doc.setEdit(vobj.Object.Name)
        else:
            FreeCAD.Console.PrintError('Task dialog already active\n')
        return True

    def setEdit(self, vobj, mode):
        analysis_object = CfdTools.getParentAnalysisObject(self.Object)
        if analysis_object is None:
            CfdTools.cfdErrorBox("Boundary must have a parent analysis object")
            return False
        # physics_model = CfdTools.getPhysicsModel(analysis_object)
        # if not physics_model:
        #     CfdTools.cfdErrorBox("Analysis object must have a physics object")
        #     return False
        # material_objs = CfdTools.getMaterials(analysis_object)

        import core.functionobjects.TaskPanelCfdFunctionObjects as TaskPanelCfdFunctionObjects
        taskd = TaskPanelCfdFunctionObjects.TaskPanelCfdFunctionObjects(self.Object)
        self.Object.ViewObject.show()
        taskd.obj = vobj.Object
        FreeCADGui.Control.showDialog(taskd)
        return True

    def unsetEdit(self, vobj, mode):
        FreeCADGui.Control.closeDialog()
        return

    # def onDelete(self, feature, sub_elements):
    #     try:
    #         for obj in self.Object.Group:
    #             obj.ViewObject.show()
    #     except Exception as err:
    #         FreeCAD.Console.PrintError("Error in onDelete: " + str(err))
    #     return True

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None
