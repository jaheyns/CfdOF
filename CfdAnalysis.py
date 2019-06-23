# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2019 - Oliver Oxtoby <oliveroxtoby@gmail.com>           *
# *   Copyright (c) 2017 - Johan Heyns (CSIR) <jheyns@csir.co.za>           *
# *   Copyright (c) 2017 - Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>        *
# *   Copyright (c) 2017 - Alfred Bogaers (CSIR) <abogaers@csir.co.za>      *
# *   Copyright (c) 2013-2015 - Juergen Riegel <FreeCAD@juergen-riegel.net> *
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
import CfdTools
from CfdTools import addObjectProperty
import os
if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore


def makeCfdAnalysis(name):
    """ Create a Cfd Analysis group object """
    obj = FreeCAD.ActiveDocument.addObject("App::DocumentObjectGroupPython", name)
    _CfdAnalysis(obj)

    if FreeCAD.GuiUp:
        _ViewProviderCfdAnalysis(obj.ViewObject)
    return obj


class _CfdAnalysis:
    """ The CFD analysis group """
    def __init__(self, obj):
        obj.Proxy = self
        self.Type = "CfdAnalysis"
        self.initProperties(obj)

    def initProperties(self, obj):
        addObjectProperty(obj, "OutputPath", "", "App::PropertyPath", "",
                          "Path to which cases are written (blank to use system default)")
        addObjectProperty(obj, "IsActiveAnalysis", False, "App::PropertyBool", "", "Active analysis object in document")
        obj.setEditorMode("IsActiveAnalysis", 1)  # Make read-only (2 = hidden)

    def onDocumentRestored(self, obj):
        self.initProperties(obj)


class _CommandCfdAnalysis:
    """ The Cfd_Analysis command definition """
    def __init__(self):
        pass

    def GetResources(self):
        icon_path = os.path.join(CfdTools.get_module_path(), "Gui", "Resources", "icons", "cfd_analysis.png")
        return {'Pixmap': icon_path,
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Cfd_Analysis", "Analysis container"),
                'Accel': "N, C",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Cfd_Analysis", "Creates an analysis container with a CFD solver")}

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Create CFD Analysis")
        FreeCADGui.doCommand("")
        FreeCADGui.addModule("CfdAnalysis")
        FreeCADGui.addModule("CfdTools")
        FreeCADGui.doCommand("analysis = CfdAnalysis.makeCfdAnalysis('CfdAnalysis')")
        FreeCADGui.doCommand("CfdTools.setActiveAnalysis(analysis)")

        ''' Objects ordered according to expected workflow '''

        # Add physics object when CfdAnalysis container is created
        FreeCADGui.addModule("CfdPhysicsSelection")
        FreeCADGui.doCommand("analysis.addObject(CfdPhysicsSelection.makeCfdPhysicsSelection())")

        # Add fluid properties object when CfdAnalysis container is created
        FreeCADGui.addModule("CfdFluidMaterial")
        FreeCADGui.doCommand("analysis.addObject(CfdFluidMaterial.makeCfdFluidMaterial('FluidProperties'))")

        # Add initialisation object when CfdAnalysis container is created
        FreeCADGui.addModule("CfdInitialiseFlowField")
        FreeCADGui.doCommand("analysis.addObject(CfdInitialiseFlowField.makeCfdInitialFlowField())")

        # Add solver object when CfdAnalysis container is created
        FreeCADGui.addModule("CfdSolverFoam")
        FreeCADGui.doCommand("analysis.addObject(CfdSolverFoam.makeCfdSolverFoam())")


class _ViewProviderCfdAnalysis:
    """ A View Provider for the CfdAnalysis container object. """
    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        icon_path = os.path.join(CfdTools.get_module_path(), "Gui", "Resources", "icons", "cfd_analysis.png")
        return icon_path

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object
        self.bubbles = None

    def updateData(self, obj, prop):
        return

    def onChanged(self, vobj, prop):
        self.makePartTransparent(vobj)
        CfdTools.setCompSolid(vobj)
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
            if obj.isDerivedFrom("Part::Feature") and not("CfdFluidBoundary" in obj.Name):
                FreeCAD.getDocument(docName).getObject(obj.Name).ViewObject.Transparency = 70
                if obj.isDerivedFrom("PartDesign::Feature"):
                    doc.getObject(obj.Name).ViewObject.LineWidth = 1
                    doc.getObject(obj.Name).ViewObject.LineColor = (0.5, 0.5, 0.5)
                    doc.getObject(obj.Name).ViewObject.PointColor = (0.5, 0.5, 0.5)
            if obj.isDerivedFrom("Part::Feature") and obj.Name.startswith("Compound"):
                FreeCAD.getDocument(docName).getObject(obj.Name).ViewObject.Visibility = False

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None