#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2015 - Qingfeng Xia <qingfeng.xia()eng.ox.ac.uk> *
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   This program is distributed in the hope that it will be useful,       *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Library General Public License for more details.                  *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with this program; if not, write to the Free Software   *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************

__title__ = "Classes for New CFD solver"
__author__ = "Qingfeng Xia"
__url__ = "http://www.freecadweb.org"

import FreeCAD
import FreeCADGui
import FemGui
import CfdTools
import os

class _ViewProviderCfdSolverFoam:
    """A View Provider for the Solver object, base class for all derived solver
    derived solver should implement  a specific TaskPanel and set up solver and override setEdit()"""

    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        # """after load from FCStd file, self.icon does not exist, return constant path instead"""
        # return ":/icons/fem-solver.svg"
        icon_path = os.path.join(CfdTools.get_module_path(), "Gui", "Resources", "icons", "solver.png")
        return icon_path

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object

    def updateData(self, obj, prop):
        return

    def onChanged(self, vobj, prop):
        return
        
    def doubleClicked(self, vobj):
        if FreeCADGui.activeWorkbench().name() != 'CfdOFWorkbench':
            FreeCADGui.activateWorkbench("CfdOFWorkbench")
        doc = FreeCADGui.getDocument(vobj.Object.Document)
        # it should be possible to find the AnalysisObject although it is not a documentObjectGroup
        if not FemGui.getActiveAnalysis():
            analysis_obj = CfdTools.getParentAnalysisObject(self.Object)
            if analysis_obj:
                FemGui.setActiveAnalysis(analysis_obj)
            else:
                FreeCAD.Console.PrintError('No Active Analysis is detected from solver object in the active Document!\n')
        if not doc.getInEdit():
            if FemGui.getActiveAnalysis().Document is FreeCAD.ActiveDocument:
                if self.Object in FemGui.getActiveAnalysis().Group:
                    doc.setEdit(vobj.Object.Name)
                else:
                    FreeCAD.Console.PrintError('Activate the analysis this solver belongs to!\n')
            else:
                FreeCAD.Console.PrintError('Active Analysis is not in active Document!\n')
        else:
            FreeCAD.Console.PrintError('Active Task Dialog found! Please close this one first!\n')
        return True
        
    def setEdit(self, vobj, mode):
        if FemGui.getActiveAnalysis():
            from CfdRunnableFoam import CfdRunnableFoam
            foamRunnable = CfdRunnableFoam(FemGui.getActiveAnalysis(), self.Object)
            from _TaskPanelCfdSolverControl import _TaskPanelCfdSolverControl
            taskd = _TaskPanelCfdSolverControl(foamRunnable)
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
