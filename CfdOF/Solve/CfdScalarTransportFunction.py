# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2022 Jonathan Bergh <bergh.jonathan@gmail.com>          *
# *   Copyright (c) 2022 Oliver Oxtoby <oliveroxtoby@gmail.com>             *
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

import os

import FreeCAD
import FreeCADGui
from pivy import coin

from CfdOF import CfdTools
from CfdOF.CfdTools import addObjectProperty

QT_TRANSLATE_NOOP = FreeCAD.Qt.QT_TRANSLATE_NOOP


def makeCfdScalarTransportFunction(name="ScalarTransportFunction"):
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", name)
    CfdScalarTransportFunction(obj)
    if FreeCAD.GuiUp:
        ViewProviderCfdScalarTransportFunction(obj.ViewObject)
    return obj


class CommandCfdScalarTransportFunction:

    def __init__(self):
        pass

    def GetResources(self):
        icon_path = os.path.join(CfdTools.getModulePath(), "Gui", "Icons", "scalartransport.svg")
        return {'Pixmap': icon_path,
                'MenuText': QT_TRANSLATE_NOOP("CfdOF_ScalarTransportFunctions",
                                                     "Cfd scalar transport function"),
                'ToolTip': QT_TRANSLATE_NOOP("CfdOF_ScalarTransportFunctions",
                                                    "Create a scalar transport function")}

    def IsActive(self):
        return CfdTools.getActiveAnalysis() is not None

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Create CfdScalarTransportFunction object")
        FreeCADGui.doCommand("")
        FreeCADGui.doCommand("from CfdOF.Solve import CfdScalarTransportFunction")
        FreeCADGui.doCommand("from CfdOF import CfdTools")
        FreeCADGui.doCommand(
            "CfdTools.getActiveAnalysis().addObject(CfdScalarTransportFunction.makeCfdScalarTransportFunction())")
        FreeCADGui.ActiveDocument.setEdit(FreeCAD.ActiveDocument.ActiveObject.Name)


class CfdScalarTransportFunction:

    def __init__(self, obj):
        self.Type = "ScalarTransportFunction"
        self.Object = obj
        obj.Proxy = self
        self.initProperties(obj)

    def initProperties(self, obj):
        addObjectProperty(
            obj,
            "FieldName",
            "S",
            "App::PropertyString",
            "Scalar transport",
            QT_TRANSLATE_NOOP("App::Property", "Name of the scalar transport field"),
        )

        addObjectProperty(
            obj,
            "DiffusivityFixed",
            False,
            "App::PropertyBool",
            "Scalar transport",
            QT_TRANSLATE_NOOP(
                "App::Property", "Use fixed value for diffusivity rather than viscosity"
            ),
        )

        # This is actually rho*diffusivity, but this is what OpenFOAM uses
        addObjectProperty(
            obj,
            "DiffusivityFixedValue",
            "0.001 kg/m/s",
            "App::PropertyQuantity",
            "Scalar transport",
            QT_TRANSLATE_NOOP("App::Property", "Diffusion coefficient for fixed diffusivity"),
        )

        addObjectProperty(
            obj,
            "RestrictToPhase",
            False,
            "App::PropertyBool",
            "Scalar transport",
            QT_TRANSLATE_NOOP("App::Property", "Restrict transport within phase"),
        )

        addObjectProperty(
            obj,
            "PhaseName",
            "water",
            "App::PropertyString",
            "Scalar transport",
            QT_TRANSLATE_NOOP("App::Property", "Transport within phase"),
        )

        addObjectProperty(
            obj,
            "InjectionRate",
            "1 kg/s",
            "App::PropertyQuantity",
            "Scalar transport",
            QT_TRANSLATE_NOOP("App::Property", "Injection rate"),
        )

        addObjectProperty(
            obj,
            "InjectionPoint",
            FreeCAD.Vector(0, 0, 0),
            "App::PropertyPosition",
            "Scalar transport",
            QT_TRANSLATE_NOOP("App::Property", "Location of the injection point"),
        )

    def onDocumentRestored(self, obj):
        self.initProperties(obj)

    def execute(self, obj):
        pass

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None

    # dumps and loads replace __getstate__ and __setstate__ post v. 0.21.2
    def dumps(self):
        return None

    def loads(self, state):
        return None


class ViewProviderCfdScalarTransportFunction:

    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        icon_path = os.path.join(CfdTools.getModulePath(), "Gui", "Icons", "scalartransport.svg")
        return icon_path

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object
        self.standard = coin.SoGroup()
        vobj.addDisplayMode(self.standard, "Standard")
        return

    def updateData(self, obj, prop):
        analysis_obj = CfdTools.getParentAnalysisObject(obj)
        if analysis_obj and not analysis_obj.Proxy.loading:
            analysis_obj.NeedsCaseRewrite = True

    def onChanged(self, vobj, prop):
        return

    def doubleClicked(self, vobj):
        doc = FreeCADGui.getDocument(vobj.Object.Document)
        if not doc.getInEdit():
            doc.setEdit(vobj.Object.Name)
        else:
            FreeCAD.Console.PrintError('Task dialog already active\n')
            FreeCADGui.Control.showTaskView()
        return True

    def setEdit(self, vobj, mode):
        analysis_object = CfdTools.getParentAnalysisObject(self.Object)
        if analysis_object is None:
            CfdTools.cfdErrorBox("Scalar transport object must have a parent analysis object")
            return False

        from CfdOF.Solve import TaskPanelCfdScalarTransportFunctions
        import importlib
        importlib.reload(TaskPanelCfdScalarTransportFunctions)
        taskd = TaskPanelCfdScalarTransportFunctions.TaskPanelCfdScalarTransportFunctions(self.Object)
        taskd.obj = vobj.Object
        FreeCADGui.Control.showDialog(taskd)
        return True

    def unsetEdit(self, vobj, mode):
        FreeCADGui.Control.closeDialog()
        return

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None

    # dumps and loads replace __getstate__ and __setstate__ post v. 0.21.2
    def dumps(self):
        return None

    def loads(self, state):
        return None


class _ViewProviderCfdScalarTransportFunction:
    """ Backward compatibility for old class name when loading from file """
    def attach(self, vobj):
        new_proxy = ViewProviderCfdScalarTransportFunction(vobj)
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
