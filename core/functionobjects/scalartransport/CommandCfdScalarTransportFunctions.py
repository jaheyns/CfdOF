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
from PySide2 import QtCore
import CfdTools
import os
from core.functionobjects.scalartransport.CfdScalarTransportFunction import CfdScalarTransportFunction
from core.functionobjects.scalartransport.ViewProviderCfdScalarTransportFunction \
    import ViewProviderCfdScalarTransportFunction


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
        icon_path = os.path.join(CfdTools.get_module_path(), "Gui", "Resources", "icons", "scalartransport.svg")
        return {'Pixmap': icon_path,
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Cfd_ScalarTransportFunction",
                                                     "Cfd scalar transport function"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Cfd_ScalarTransportFunction",
                                                    "Create a scalar transport function")}

    def IsActive(self):
        return CfdTools.getActiveAnalysis() is not None

    def Activated(self):
        is_present = False
        members = CfdTools.getScalarTransportFunctionsGroup(CfdTools.getActiveAnalysis())
        for i in members:
            if hasattr(i, 'Proxy') and isinstance(i.Proxy, CfdScalarTransportFunction):
                FreeCADGui.activeDocument().setEdit(i.Name)
                is_present = True

        # Allow to re-create if deleted
        if not is_present:
            FreeCADGui.Selection.clearSelection()

            FreeCAD.ActiveDocument.openTransaction("Create CfdScalarTransportFunctions object")
            FreeCADGui.doCommand("")
            FreeCADGui.addModule("core.functionobjects.scalartransport.CommandCfdScalarTransportFunctions " \
                                 + "as CommandCfdScalarTransportFunctions")
            FreeCADGui.addModule("CfdTools")
            FreeCADGui.doCommand(
                "CfdTools.getActiveAnalysis().addObject(CommandCfdScalarTransportFunctions.makeCfdScalarTransportFunction())")
            FreeCADGui.ActiveDocument.setEdit(FreeCAD.ActiveDocument.ActiveObject.Name)

        FreeCADGui.Selection.clearSelection()


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Cfd_ScalarTransportFunction', CommandCfdScalarTransportFunction())


