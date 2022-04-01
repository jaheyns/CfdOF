# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2016 - Bernd Hahnebach <bernd@bimstatik.org>            *
# *   Copyright (c) 2019 Oliver Oxtoby <oliveroxtoby@gmail.com>             *
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
from PySide import QtCore
import CfdTools
from CfdTools import addObjectProperty
import os

OBJECT_NAMES = ["force", "coefficients"]
OBJECT_DESCRIPTIONS = ["Calculate forces on patches", "Calculate force coefficients from patches"]

# For each sub-type, whether the basic tab is enabled, the panel numbers to show (ignored if false), whether
# direction reversal is checked by default (only used for panel 0), whether turbulent inlet panel is shown,
# whether volume fraction panel is shown, whether thermal GUI is shown,
# rows of thermal UI to show (all shown if None)

# todo adapt all this
BOUNDARY_UI = [[[False, [], False, False, False, True, None],  # No slip            # Wall
                [False, [], False, False, False, True, None],  # Slip
                [True, [2], False, False, False, True, None],  # Partial slip
                [True, [0], False, False, False, True, None],  # Translating wall
                [True, [0], False, False, False, True, None]],  # Rough
               [[True, [0, 1], True, True, True, True, [2]],  # Velocity            # Velocity
                [True, [3], False, True, True, True, [2]],  # Vol flow rate
                [True, [4], False, True, True, True, [2]],  # Mass Flow rate
                [True, [1], False, True, True, True, [2]],  # Total pressure
                [True, [0, 1], False, True, True, True, [2]]],  # Static pressure
               [[True, [0, 1], False, False, True, True, [2]],  # Static pressure   # Outlet
                [True, [0, 1], False, False, True, True, [2]],  # Uniform velocity
                [False, [], False, False, False, False, None]],  # Outflow
               [[True, [1], False, True, True, True, [2]],  # Opening               # Open
                [True, [0, 1], False, True, False, True, [2]]],  # Far-field
               [[False, [], False, False, False, False, None]],  # Symmetry plane   # Constraint
               [[True, [5], False, False, False, False, None]]]  # Permeable screen # Baffle


def makeCfdFunctionObject(name="CFDFunctionObject"):
    obj = FreeCAD.ActiveDocument.addObject("App::DocumentObjectGroupPython", name)
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
        if addObjectProperty(obj, 'ShapeRefs', [], "App::PropertyLinkSubList", "", "Boundary faces"):
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

        addObjectProperty(obj, 'CaseName', "meshCase", "App::PropertyString", "",
                          "Name of directory in which the mesh is created")

        # Setup and utility
        addObjectProperty(obj, 'FunctionObjectType', "functionObjectType", "App::PropertyString", "",
                          "Name of the function object to be created")

        # Forces
        # Field names
        addObjectProperty(obj, 'Pressure', '', "App::PropertyString", "Function object",
                          "Pressure field name")
        addObjectProperty(obj, 'Density', '', "App::PropertyString", "Function object",
                          "Density field name")
        addObjectProperty(obj, 'Velocity', '', "App::PropertyString", "Function object",
                          "Velocity field name")
        addObjectProperty(obj, 'ReferencePressure', '0 Pa', "App::PropertyPressure", "Function object",
                          "Reference pressure")
        addObjectProperty(obj, 'CentreOfRotation', '0, 0, 0', "App::PropertyString", "Function object",
                          "Centre of Rotation (x, y, z)")
        addObjectProperty(obj, 'IncludePorosity', False, "App::PropertyBool", "Function objects",
                          "Whether to include porosity effects")
        addObjectProperty(obj, 'WriteFields', False, "App::PropertyBool", "Function objects",
                          "Whether to write output fields")

        # Force coefficients
        addObjectProperty(obj, 'LiftDirection', '0, 0, 0', "App::PropertyString", "Function object",
                          "Lift Direction vector (x, y, z)")
        addObjectProperty(obj, 'DragDirection', '0, 0, 0', "App::PropertyString", "Function object",
                          "Drag direction vector (x, y, z)")
        addObjectProperty(obj, 'PitchAxis', '0, 0, 0', "App::PropertyString", "Function object",
                          "Pitch axis for moment coefficient")
        addObjectProperty(obj, 'MagUInf', '1 m/s', "App::PropertyQuantity", "Function object",
                          "Freestream velocity magnitude")
        addObjectProperty(obj, 'LengthReference', '1 m', "App::PropertyQuantity", "Function object",
                          "Coefficient length reference")
        addObjectProperty(obj, 'AreaReference', '1 m^2', "App::PropertyQuantity", "Function object",
                          "Coefficient area reference")

        # Spatial binning
        addObjectProperty(obj, 'NBins', '0', "App::PropertyQuantity", "Function objects",
                          "Number of bins")
        addObjectProperty(obj, 'Direction', '0', "App::PropertyQuantity", "Function objects",
                          "Direction")
        addObjectProperty(obj, 'Cumulative', True, "App::PropertyBool", "Function objects",
                          "Cumulative")

    def onDocumentRestored(self, obj):
        self.initProperties(obj)

    def execute(self, obj):
        pass

    def __getstate__(self):
        return self.Type

    def __setstate__(self, state):
        if state:
            self.Type = state


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

    def updateData(self, obj, prop):
        return

    def onChanged(self, vobj, prop):
        CfdTools.setCompSolid(vobj)
        return

    def setEdit(self, vobj, mode):
        for obj in FreeCAD.ActiveDocument.Objects:
            if hasattr(obj, 'Proxy') and isinstance(obj.Proxy, _CfdFunctionObjects):
                obj.ViewObject.show()
        from core.functionobjects import TaskPanelCfdFunctionObjects
        self.taskd = TaskPanelCfdFunctionObjects.TaskPanelCfdFunctionObjects(self.Object)
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
        return True

    def onDelete(self, feature, sub_elements):
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
