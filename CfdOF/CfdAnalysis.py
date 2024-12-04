# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2017 Johan Heyns (CSIR) <jheyns@csir.co.za>             *
# *   Copyright (c) 2017 Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>          *
# *   Copyright (c) 2017 Alfred Bogaers (CSIR) <abogaers@csir.co.za>        *
# *   Copyright (c) 2019-2022 Oliver Oxtoby <oliveroxtoby@gmail.com>        *
# *   Copyright (c) 2024 Jonathan Bergh <bergh.jonathan@gmail.com>          *
# *									    *
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

import FreeCAD

from CfdOF import CfdTools
from CfdOF.CfdTools import addObjectProperty

if FreeCAD.GuiUp:
    import FreeCADGui

QT_TRANSLATE_NOOP = FreeCAD.Qt.QT_TRANSLATE_NOOP


def makeCfdAnalysis(name):
    """ Create a Cfd Analysis group object """
    obj = FreeCAD.ActiveDocument.addObject("App::DocumentObjectGroupPython", name)
    CfdAnalysis(obj)

    if FreeCAD.GuiUp:
        ViewProviderCfdAnalysis(obj.ViewObject)
    return obj


class CfdAnalysis:
    """ The CFD analysis group """
    def __init__(self, obj):
        self.loading = False
        self.ignore_next_grouptouched = False
        obj.Proxy = self
        self.Type = "CfdAnalysis"
        self.initProperties(obj)

    def initProperties(self, obj):
        addObjectProperty(
            obj,
            "OutputPath",
            "",
            "App::PropertyPath",
            "",
            QT_TRANSLATE_NOOP(
                "App::Property",
                "Path to which cases are written (blank to use system default; relative path is relative "
                "to location of current file)",
            ),
        )
        addObjectProperty(
            obj,
            "IsActiveAnalysis",
            False,
            "App::PropertyBool",
            "",
            QT_TRANSLATE_NOOP("App::Property", "Active analysis object in document"),
        )
        obj.setEditorMode("IsActiveAnalysis", 1)  # Make read-only (2 = hidden)
        addObjectProperty(
            obj,
            "NeedsMeshRewrite",
            True,
            "App::PropertyBool",
            "",
            QT_TRANSLATE_NOOP("App::Property", "Mesh setup needs to be re-written"),
        )
        addObjectProperty(
            obj,
            "NeedsCaseRewrite",
            True,
            "App::PropertyBool",
            "",
            QT_TRANSLATE_NOOP("App::Property", "Case setup needs to be re-written"),
        )
        addObjectProperty(
            obj,
            "NeedsMeshRerun",
            True,
            "App::PropertyBool",
            "",
            QT_TRANSLATE_NOOP("App::Property", "Mesher needs to be re-run before running solver"),
        )
        addObjectProperty(
            obj,
            "UseHostfile",
            False,
            "App::PropertyBool",
            "",
            QT_TRANSLATE_NOOP("App::Property", "Use a hostfile for parallel cluster runs"),
        )
        addObjectProperty(
            obj,
            "HostfileName",
            "../mpi_hostfile",
            "App::PropertyString",
            "",
            QT_TRANSLATE_NOOP("App::Property", "Hostfile name"),
        )

    def onDocumentRestored(self, obj):
        self.loading = False
        self.initProperties(obj)

    def __setstate__(self, state_dict):
        self.__dict__ = state_dict
        # Set while we are loading from file
        self.loading = True

    # dumps and loads replace __getstate__ and __setstate__ post v. 0.21.2

    def loads(self, state_dict):
        self.__dict__ = state_dict
        # Set while we are loading from file
        self.loading = True


class _CfdAnalysis:
    """ Backward compatibility for old class name when loading from file """
    def onDocumentRestored(self, obj):
        CfdAnalysis(obj)

    def __setstate__(self, state_dict):
        self.__dict__ = state_dict
        # Set while we are loading from file
        self.loading = True

    # dumps and loads replace __getstate__ and __setstate__ post v. 0.21.2

    def loads(self, state_dict):
        self.__dict__ = state_dict
        # Set while we are loading from file
        self.loading = True


class CommandCfdAnalysis:
    """ The CfdOF_Analysis command definition """
    def __init__(self):
        pass

    def GetResources(self):
        icon_path = os.path.join(CfdTools.getModulePath(), "Gui", "Icons", "cfd_analysis.svg")
        return {'Pixmap': icon_path,
                'MenuText': QT_TRANSLATE_NOOP("CfdOF_Analysis", "Analysis container"),
                'Accel': "N, C",
                'ToolTip': QT_TRANSLATE_NOOP("CfdOF_Analysis", "Creates an analysis container with a CFD solver")}

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Create CFD Analysis")
        FreeCADGui.doCommand("from CfdOF import CfdAnalysis")
        FreeCADGui.doCommand("from CfdOF import CfdTools")
        FreeCADGui.doCommand("analysis = CfdAnalysis.makeCfdAnalysis('CfdAnalysis')")
        FreeCADGui.doCommand("CfdTools.setActiveAnalysis(analysis)")

        # Objects ordered according to expected workflow
        # Add physics object when CfdAnalysis container is created
        FreeCADGui.doCommand("from CfdOF.Solve import CfdPhysicsSelection")
        FreeCADGui.doCommand("analysis.addObject(CfdPhysicsSelection.makeCfdPhysicsSelection())")

        # Add fluid properties object when CfdAnalysis container is created
        FreeCADGui.doCommand("from CfdOF.Solve import CfdFluidMaterial")
        FreeCADGui.doCommand("analysis.addObject(CfdFluidMaterial.makeCfdFluidMaterial('FluidProperties'))")

        # Add initialisation object when CfdAnalysis container is created
        FreeCADGui.doCommand("from CfdOF.Solve import CfdInitialiseFlowField")
        FreeCADGui.doCommand("analysis.addObject(CfdInitialiseFlowField.makeCfdInitialFlowField())")

        # Add solver object when CfdAnalysis container is created
        FreeCADGui.doCommand("from CfdOF.Solve import CfdSolverFoam")
        FreeCADGui.doCommand("analysis.addObject(CfdSolverFoam.makeCfdSolverFoam())")


class ViewProviderCfdAnalysis:
    """ A View Provider for the CfdAnalysis container object. """
    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        icon_path = os.path.join(CfdTools.getModulePath(), "Gui", "Icons", "cfd_analysis.svg")
        return icon_path

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object

    def updateData(self, obj, prop):
        if not obj.Proxy.loading:
            if prop == 'OutputPath':
                obj.NeedsMeshRewrite = True
                obj.NeedsCaseRewrite = True
            elif prop == 'Group':
                # Something was added or deleted
                obj.NeedsCaseRewrite = True

    def onChanged(self, vobj, prop):
        self.makePartTransparent(vobj)
        #CfdTools.setCompSolid(vobj)
        return

    def doubleClicked(self, vobj):
        if not CfdTools.getActiveAnalysis() == self.Object:
            if FreeCADGui.activeWorkbench().name() != 'CfdOFWorkbench':
                FreeCADGui.activateWorkbench("CfdOFWorkbench")
            CfdTools.setActiveAnalysis(self.Object)
            return True
        return True

    def makePartTransparent(self, vobj):
        """ Make parts transparent so that the boundary conditions and cell zones are clearly visible. """
        docName = str(vobj.Object.Document.Name)
        doc = FreeCAD.getDocument(docName)
        for obj in doc.Objects:
            if obj.isDerivedFrom("Part::Feature") and not ("CfdFluidBoundary" in obj.Name):
                vobj2 = FreeCAD.getDocument(docName).getObject(obj.Name).ViewObject
                if hasattr(vobj2, 'Transparency'):
                    vobj2.Transparency = 70
                if obj.isDerivedFrom("PartDesign::Feature"):
                    doc.getObject(obj.Name).ViewObject.LineWidth = 1
                    doc.getObject(obj.Name).ViewObject.LineColor = (0.5, 0.5, 0.5)
                    doc.getObject(obj.Name).ViewObject.PointColor = (0.5, 0.5, 0.5)

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None

    # dumps and loads replace __getstate__ and __setstate__ post v. 0.21.2
    def dumps(self):
        return None

    def loads(self, state):
        return None


class _ViewProviderCfdAnalysis:
    """ Backward compatibility for old class name when loading from file """
    def attach(self, vobj):
        new_proxy = ViewProviderCfdAnalysis(vobj)
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
