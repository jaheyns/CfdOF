# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2015 - Qingfeng Xia <qingfeng.xia()eng.ox.ac.uk>        *
# *   Copyright (c) 2017 Johan Heyns (CSIR) <jheyns@csir.co.za>             *
# *   Copyright (c) 2017 Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>          *
# *   Copyright (c) 2017 Alfred Bogaers (CSIR) <abogaers@csir.co.za>        *
# *   Copyright (c) 2019-2022 Oliver Oxtoby <oliveroxtoby@gmail.com>        *
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

import os
import os.path
import FreeCAD
from CfdOF import CfdTools
from CfdOF.CfdTools import addObjectProperty
from CfdOF.CfdTimePlot import TimePlot
if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore


def makeCfdSolverFoam(name="CfdSolver"):
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", name)
    CfdSolverFoam(obj)
    if FreeCAD.GuiUp:
        ViewProviderCfdSolverFoam(obj.ViewObject)
    return obj


class CommandCfdSolverFoam:
    def GetResources(self):
        icon_path = os.path.join(CfdTools.getModulePath(), "Gui", "Icons", "solver.svg")
        return {'Pixmap': icon_path,
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Cfd_SolverControl", "Solver job control"),
                'Accel': "S, C",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Cfd_SolverControl", "Edit properties and run solver")}

    def IsActive(self):
        return CfdTools.getActiveAnalysis() is not None

    def Activated(self):
        is_present = False
        members = CfdTools.getActiveAnalysis().Group
        for i in members:
            if isinstance(i.Proxy, CfdSolverFoam):
                FreeCADGui.activeDocument().setEdit(i.Name)
                is_present = True

        # Allowing user to re-create if CFDSolver was deleted.
        if not is_present:
            FreeCADGui.doCommand("from CfdOF import CfdTools")
            FreeCADGui.doCommand("from CfdOF.Solve import CfdSolverFoam")
            FreeCADGui.doCommand("CfdTools.getActiveAnalysis().addObject(CfdSolverFoam.makeCfdSolverFoam())")
            FreeCADGui.doCommand("Gui.activeDocument().setEdit(App.ActiveDocument.ActiveObject.Name)")


class CfdSolverFoam(object):
    """ Solver-specific properties """
    def __init__(self, obj):
        self.Type = "CfdSolverFoam"
        self.Object = obj  # keep a ref to the DocObj for nonGui usage
        obj.Proxy = self  # link between App::DocumentObject to  this object

        self.initProperties(obj)

    def initProperties(self, obj):
        addObjectProperty(obj, "InputCaseName", "case", "App::PropertyFile", "Solver",
                          "Name of case directory where the input files are written")
        addObjectProperty(obj, "Parallel", True, "App::PropertyBool", "Solver",
                          "Parallel analysis on multiple CPU cores")
        addObjectProperty(obj, "ParallelCores", 4, "App::PropertyInteger", "Solver",
                          "Number of cores on which to run parallel analysis")

        addObjectProperty(obj, "MaxIterations", 2000, "App::PropertyInteger", "IterationControl",
                          "Maximum number of iterations to run steady-state analysis")
        addObjectProperty(obj, "SteadyWriteInterval", 100, "App::PropertyInteger", "IterationControl",
                          "Iteration output interval")
        addObjectProperty(obj, "ConvergenceTol", 1e-3, "App::PropertyFloat", "IterationControl",
                          "Global absolute solution convergence criterion")
        addObjectProperty(obj, "EndTime", "1 s", "App::PropertyQuantity", "TimeStepControl",
                          "Total time to run transient solution")
        addObjectProperty(obj, "TimeStep", "0.001 s", "App::PropertyQuantity", "TimeStepControl",
                          "Time step increment")
        addObjectProperty(obj, "TransientWriteInterval", "0.1 s", "App::PropertyQuantity", "TimeStepControl",
                          "Output time interval")

        self.residual_plotter = TimePlot(title="Simulation residuals", y_label="Residual", is_log=True)
        self.forces_plotters = {}
        self.force_coeffs_plotters = {}
        self.probes_plotters = {}


    def onDocumentRestored(self, obj):
        self.initProperties(obj)

    def execute(self, obj):
        return

    def onChanged(self, obj, prop):
        return

    def __getstate__(self):
        return self.Type

    def __setstate__(self, state):
        if state:
            self.Type = state


class _CfdSolverFoam:
    """ Backward compatibility for old class name when loading from file """
    def onDocumentRestored(self, obj):
        CfdSolverFoam(obj)

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None


class ViewProviderCfdSolverFoam:
    """A View Provider for the Solver object, base class for all derived solver
    derived solver should implement  a specific TaskPanel and set up solver and override setEdit()"""

    def __init__(self, vobj):
        vobj.Proxy = self
        self.taskd = None

    def getIcon(self):
        # """after load from FCStd file, self.icon does not exist, return constant path instead"""
        icon_path = os.path.join(CfdTools.getModulePath(), "Gui", "Icons", "solver.svg")
        return icon_path

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object

    def updateData(self, obj, prop):
        analysis_obj = CfdTools.getParentAnalysisObject(obj)
        if analysis_obj and not analysis_obj.Proxy.loading:
            analysis_obj.NeedsCaseRewrite = True

    def onChanged(self, vobj, prop):
        return

    def setEdit(self, vobj, mode):
        if CfdTools.getActiveAnalysis():
            from CfdOF.Solve.CfdRunnableFoam import CfdRunnableFoam
            foam_runnable = CfdRunnableFoam(CfdTools.getActiveAnalysis(), self.Object)
            from CfdOF.Solve import TaskPanelCfdSolverControl
            import importlib
            importlib.reload(TaskPanelCfdSolverControl)
            self.taskd = TaskPanelCfdSolverControl.TaskPanelCfdSolverControl(foam_runnable)
            self.taskd.obj = vobj.Object
            FreeCADGui.Control.showDialog(self.taskd)
        return True

    def doubleClicked(self, vobj):
        if FreeCADGui.activeWorkbench().name() != 'CfdOFWorkbench':
            FreeCADGui.activateWorkbench("CfdOFWorkbench")
        doc = FreeCADGui.getDocument(vobj.Object.Document)
        if not CfdTools.getActiveAnalysis():
            analysis_obj = CfdTools.getParentAnalysisObject(self.Object)
            if analysis_obj:
                CfdTools.setActiveAnalysis(analysis_obj)
            else:
                FreeCAD.Console.PrintError(
                    'No Active Analysis detected from Solver object in the active Document\n')
        if not doc.getInEdit():
            if CfdTools.getActiveAnalysis().Document is FreeCAD.ActiveDocument:
                if self.Object in CfdTools.getActiveAnalysis().Group:
                    doc.setEdit(vobj.Object.Name)
                else:
                    FreeCAD.Console.PrintError('Please activate the Analysis this solver belongs to.\n')
            else:
                FreeCAD.Console.PrintError('Active Analysis is not in active Document\n')
        else:
            FreeCAD.Console.PrintError('Task dialog already active\n')
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


class _ViewProviderCfdSolverFoam:
    """ Backward compatibility for old class name when loading from file """
    def attach(self, vobj):
        new_proxy = ViewProviderCfdSolverFoam(vobj)
        new_proxy.attach(vobj)

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None
