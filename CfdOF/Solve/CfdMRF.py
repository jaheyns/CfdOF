# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: © 2022 Jonathan Bergh <bergh.jonathan@gmail.com>
# SPDX-FileCopyrightText: © 2022 Oliver Oxtoby <oliveroxtoby@gmail.com>
# SPDX-FileNotice: Part of the CfdOF addon.

################################################################################
#                                                                              #
#   This program is free software; you can redistribute it and/or              #
#   modify it under the terms of the GNU Lesser General Public                 #
#   License as published by the Free Software Foundation; either               #
#   version 3 of the License, or (at your option) any later version.           #
#                                                                              #
#   This program is distributed in the hope that it will be useful,            #
#   but WITHOUT ANY WARRANTY; without even the implied warranty of             #
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.                       #
#                                                                              #
#   See the GNU Lesser General Public License for more details.                #
#                                                                              #
#   You should have received a copy of the GNU Lesser General Public License   #
#   along with this program; if not, write to the Free Software Foundation,    #
#   Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.        #
#                                                                              #
################################################################################

import os

import FreeCAD
import Part
import FreeCADGui
from pivy import coin

from CfdOF import CfdTools
from CfdOF.CfdTools import addObjectProperty

QT_TRANSLATE_NOOP = FreeCAD.Qt.QT_TRANSLATE_NOOP


def makeCfdMRF(name="MRF"):
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", name)
    CfdMRF(obj)
    if FreeCAD.GuiUp:
        ViewProviderCfdMRF(obj.ViewObject)
    return obj


class CommandCfdMRF:

    def __init__(self):
        pass

    def GetResources(self):
        icon_path = os.path.join(CfdTools.getModulePath(), "Gui", "Icons", "MRF.svg")
        return {'Pixmap': icon_path,
                'MenuText': QT_TRANSLATE_NOOP("CfdOF_MRF",
                                                     "Multi-reference frame (MRF)"),
                'ToolTip': QT_TRANSLATE_NOOP("CfdOF_MRF",
                                                    "Create a Multi-reference frame region")}

    def IsActive(self):
        return CfdTools.getActiveAnalysis() is not None

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Create CfdMRF object")
        FreeCADGui.doCommand("")
        FreeCADGui.doCommand("from CfdOF.Solve import CfdMRF")
        FreeCADGui.doCommand("from CfdOF import CfdTools")
        FreeCADGui.doCommand(
            "CfdTools.getActiveAnalysis().addObject(CfdMRF.makeCfdMRF())")
        FreeCADGui.ActiveDocument.setEdit(FreeCAD.ActiveDocument.ActiveObject.Name)


class CfdMRF:

    def __init__(self, obj):
        self.Object = obj
        self.initProperties(obj)

    def initProperties(self, obj):
        obj.Proxy = self
        self.Type = 'CfdMRF'

        addObjectProperty(
            obj,
            "Speed",
            0.0,
            "App::PropertyFloat",
            "MRF",
            QT_TRANSLATE_NOOP("App::Property", "The speed of the MRF region in RPM"),
        )

        addObjectProperty(
            obj,
            "CenterOfRotation",
            FreeCAD.Vector(0, 0, 0),
            "App::PropertyPosition",
            "MRF",
            QT_TRANSLATE_NOOP("App::Property", "Centre of rotation (MMR)"),
        )

        addObjectProperty(
            obj,
            "Axis",
            FreeCAD.Vector(0, 0, 0),
            "App::PropertyVector",
            "MRF",
            QT_TRANSLATE_NOOP("App::Property", "Axis of rotation for the MRF region"),
        )

        addObjectProperty(
            obj,
            "ShapeRefs",
            [],
            "App::PropertyLinkSubListGlobal",
            "MRF",
            QT_TRANSLATE_NOOP("App::Property", "MRF object"),
        )

    def onDocumentRestored(self, obj):
        self.initProperties(obj)

    def execute(self, obj):
        if obj.ShapeRefs:
            list_of_shapes = []
            for r in obj.ShapeRefs:
                try:
                    list_of_shapes.append(r[0].Shape)
                except Part.OCCError:
                    pass
            if list_of_shapes:
                obj.Shape = Part.makeCompound(list_of_shapes)
            else:
                obj.Shape = Part.Shape()
        else:
            obj.Shape = Part.Shape()
        #pass

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None

    # dumps and loads replace __getstate__ and __setstate__ post v. 0.21.2
    def dumps(self):
        return None

    def loads(self, state):
        return None


class ViewProviderCfdMRF:

    def __init__(self, vobj):
        vobj.Proxy = self
        self.taskd = None

    def getIcon(self):
        icon_path = os.path.join(CfdTools.getModulePath(), "Gui", "Icons", "MRF.svg")
        return icon_path

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object
        self.standard = coin.SoGroup()
        vobj.addDisplayMode(self.standard, "Standard")
        vobj.ShapeColor = (0.0, 0.5, 1.0)
        vobj.Transparency = 70
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
            CfdTools.cfdErrorBox("trying to make a table in the task panel. or at least leanrn how the ui works")
            return False

        from CfdOF.Solve import TaskPanelCfdMRF
        import importlib
        importlib.reload(TaskPanelCfdMRF)
        taskd = TaskPanelCfdMRF.TaskPanelCfdMRF(self.Object)
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


class _ViewProviderCfdMRF:
    def attach(self, vobj):
        new_proxy = ViewProviderCfdMRF(vobj)
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


FreeCADGui.addCommand('CfdOF_MRF', CommandCfdMRF())
