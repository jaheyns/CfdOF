# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2013-2015 - Juergen Riegel <FreeCAD@juergen-riegel.net> *
# *   Copyright (c) 2018 - Johan Heyns <jheyns@csir.co.za>                  *
# *   Copyright (c) 2018 - Alfred Bogaers <abogaers@csir.co.za>             *
# *   Copyright (c) 2018 - Oliver Oxtoby <ooxtoby@csir.co.za>               *
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
import platform
try:
    from femcommands.manager import CommandManager
except ImportError:  # Backward compatibility
    from PyGui.FemCommands import FemCommands as CommandManager
import CfdTools
import os

if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore
    import FemGui


class setCFDConvert3Dto2D(CommandManager):
    def __init__(self):
        icon_path = os.path.join(CfdTools.get_module_path(), "Gui", "Resources", "icons", "3d-to-2d.png")
        self.resources = {
            'Pixmap': icon_path,
            'MenuText': 'Convert 3D mesh into a 2D OpenFOAM mesh',
            'ToolTip': 'Convert 3D mesh into a 2D OpenFOAM mesh'
            }
        self.is_active = 'with_femmesh'  

    def Activated(self):
        FreeCAD.Console.PrintMessage("Convert 3D mesh into a 2D mesh \n")
        FreeCADGui.addModule("FemGui")
        FreeCADGui.addModule("CfdConverterTo2D")
        analysis_obj = FemGui.getActiveAnalysis()
        obj,isPresent = CfdTools.get2DConversionObject(analysis_obj)

        if not(isPresent):
            sel = FreeCADGui.Selection.getSelection()
            if len(sel) == 1:
                sobj = sel[0]
                if len(sel) == 1 \
                        and hasattr(sobj, "Proxy") \
                        and (sobj.Proxy.Type == "Fem::FemMeshGmsh" or sobj.Proxy.Type == "CfdMeshCart"):
                    FreeCADGui.doCommand("FemGui.getActiveAnalysis().addObject(CfdConverterTo2D.makeCfdConvertTo2D())")
                    FreeCADGui.ActiveDocument.setEdit(FreeCAD.ActiveDocument.ActiveObject.Name)
        else:
            FreeCADGui.ActiveDocument.setEdit(obj.Name)

        FreeCADGui.Selection.clearSelection()
if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Cfd_3DTo2D', setCFDConvert3Dto2D())
