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
from CfdTools import addObjectProperty
import os
import CfdTools


def makeCfdReportingProbes(name="CfdReportingProbes"):
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", name)
    CfdReportingProbes(obj)
    if FreeCAD.GuiUp:
        ViewProviderCfdReportingProbes(obj.ViewObject)
    return obj


class CommandCfdReportingProbes:

    def GetResources(self):
        icon_path = os.path.join(CfdTools.get_module_path(), "Gui", "Resources", "icons", "monitor_probes.svg")
        return {'Pixmap': icon_path,
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Cfd_ReportingProbes",
                                                     "Cfd reporting probes"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Cfd_ReportingProbes",
                                                    "Create a reporting probe for the current case")}

    def IsActive(self):
        return CfdTools.getActiveAnalysis() is not None

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Create CfdReportingFunctions object")
        FreeCADGui.doCommand("")
        FreeCADGui.addModule("core.functionobjects.probes.CfdReportingProbes as CfdReportingProbes")
        FreeCADGui.addModule("CfdTools")
        FreeCADGui.doCommand("CfdTools.getActiveAnalysis().addObject(CfdReportingProbes.makeCfdReportingProbes())")
        FreeCADGui.ActiveDocument.setEdit(FreeCAD.ActiveDocument.ActiveObject.Name)


class CfdReportingProbes:

    def __init__(self, obj):
        self.Type = "CfdReportingFunctions"
        self.Object = obj
        obj.Proxy = self
        self.initProperties(obj)

    def initProperties(self, obj):

        addObjectProperty(obj, 'FieldName', "p", "App::PropertyString", "Function object",
                          "Name of the field to sample")

        addObjectProperty(obj, 'ProbePosition', FreeCAD.Vector(0, 0, 0), "App::PropertyPosition", "Function object",
                          "Location of the probe sample location")

    def onDocumentRestored(self, obj):
        self.initProperties(obj)

    def execute(self, obj):
        pass

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None


class ViewProviderCfdReportingProbes:

    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        icon_path = os.path.join(CfdTools.get_module_path(), "Gui", "Resources", "icons", "monitor_probes.svg")
        return icon_path

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object
        self.standard = coin.SoGroup()
        vobj.addDisplayMode(self.standard, "Standard")
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
            CfdTools.cfdErrorBox("Reporting probes must have a parent analysis object")
            return False

        import core.functionobjects.probes.TaskPanelCfdReportingProbes as TaskPanelCfdReportingProbes
        taskd = TaskPanelCfdReportingProbes.TaskPanelCfdReportingProbes(self.Object)
        self.Object.ViewObject.show()
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


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Cfd_ReportingProbes', CommandCfdReportingProbes())
