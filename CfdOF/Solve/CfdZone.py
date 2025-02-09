# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2017 Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>          *
# *   Copyright (c) 2017 Alfred Bogaers (CSIR) <abogaers@csir.co.za>        *
# *   Copyright (c) 2017 Johan Heyns (CSIR) <jheyns@csir.co.za>             *
# *   Copyright (c) 2019-2024 Oliver Oxtoby <oliveroxtoby@gmail.com>        *
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
import Part

if FreeCAD.GuiUp:
    import FreeCADGui
from CfdOF import CfdTools
from CfdOF.CfdTools import addObjectProperty

QT_TRANSLATE_NOOP = FreeCAD.Qt.QT_TRANSLATE_NOOP

# Constants
POROUS_CORRELATIONS = ['DarcyForchheimer', 'Jakob']
POROUS_CORRELATION_NAMES = ["Darcy-Forchheimer coefficients", "Staggered tube bundle (Jakob)"]
POROUS_CORRELATION_TIPS = ["Specify viscous and inertial drag tensors by giving their principal components and "
                           "directions (these will be made orthogonal)", 
                           "Specify geometry of parallel tube bundle with staggered layers."]

ASPECT_RATIOS = ["1.0", "1.73", "1.0"]
ASPECT_RATIO_NAMES = ["User defined", "Equilateral", "Rotated square"]
ASPECT_RATIO_TIPS = ["", "Equilateral triangles pointing perpendicular to spacing direction",
                     "45 degree angles; isotropic"]


def makeCfdPorousZone(name='PorousZone'):
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", name)
    CfdZone(obj)
    if FreeCAD.GuiUp:
        ViewProviderCfdZone(obj.ViewObject)
    return obj


def makeCfdInitialisationZone(name='InitialisationZone'):
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", name)
    CfdZone(obj)
    if FreeCAD.GuiUp:
        ViewProviderCfdZone(obj.ViewObject)
    return obj


class CommandCfdPorousZone:
    def GetResources(self):
        icon_path = os.path.join(CfdTools.getModulePath(), "Gui", "Icons", "porous.svg")
        return {'Pixmap': icon_path,
                'MenuText': QT_TRANSLATE_NOOP("CfdOF_PorousZone", "Porous zone"),
                'Accel': "",
                'ToolTip': QT_TRANSLATE_NOOP("CfdOF_PorousZone", "Select and create a porous zone")}

    def IsActive(self):
        return CfdTools.getActiveAnalysis() is not None

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Select and create a porous zone")
        FreeCADGui.doCommand("")
        FreeCADGui.doCommand("from CfdOF.Solve import CfdZone")
        FreeCADGui.doCommand("from CfdOF import CfdTools")
        FreeCADGui.doCommand("CfdTools.getActiveAnalysis().addObject(CfdZone.makeCfdPorousZone())")
        FreeCADGui.ActiveDocument.setEdit(FreeCAD.ActiveDocument.ActiveObject.Name)


class CommandCfdInitialisationZone:
    def GetResources(self):
        icon_path = os.path.join(CfdTools.getModulePath(), "Gui", "Icons", "alpha.svg")
        return {'Pixmap': icon_path,
                'MenuText': QT_TRANSLATE_NOOP("CfdOF_InitialisationZone", "Initialisation zone"),
                'Accel': "",
                'ToolTip': QT_TRANSLATE_NOOP("CfdOF_InitialisationZone",
                                                    "Select and create an initialisation zone")}

    def IsActive(self):
        return CfdTools.getActiveAnalysis() is not None

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Select and create an initialisation zone")
        FreeCADGui.doCommand("")
        FreeCADGui.doCommand("from CfdOF.Solve import CfdZone")
        FreeCADGui.doCommand("from CfdOF import CfdTools")
        FreeCADGui.doCommand(
            "CfdTools.getActiveAnalysis().addObject(CfdZone.makeCfdInitialisationZone())")
        FreeCADGui.ActiveDocument.setEdit(FreeCAD.ActiveDocument.ActiveObject.Name)


class CfdZone:
    def __init__(self, obj):
        obj.Proxy = self
        self.Type = 'Zone'
        self.initProperties(obj)

    def initProperties(self, obj):
        if addObjectProperty(
            obj,
            "ShapeRefs",
            [],
            "App::PropertyLinkSubListGlobal",
            "",
            QT_TRANSLATE_NOOP("App::Property", "Boundary faces"),
        ):
            # Backward compat
            if 'References' in obj.PropertiesList:
                doc = FreeCAD.getDocument(obj.Document.Name)
                for r in obj.References:
                    if not r[1]:
                        obj.ShapeRefs += [doc.getObject(r[0])]
                    else:
                        obj.ShapeRefs += [(doc.getObject(r[0]), r[1])]
                obj.removeProperty("References")
                obj.removeProperty("LinkedObjects")

        if obj.Name.startswith("PorousZone"):
            if addObjectProperty(
                obj,
                "PorousCorrelation",
                POROUS_CORRELATIONS,
                "App::PropertyEnumeration",
                "Porous zone",
                QT_TRANSLATE_NOOP("App::Property", "Porous drag model"),
            ):
                obj.PorousCorrelation = "DarcyForchheimer"
            addObjectProperty(
                obj,
                "D1",
                "0 1/m^2",
                "App::PropertyQuantity",
                "Darcy-Forchheimer",
                QT_TRANSLATE_NOOP("App::Property", "Darcy coefficient (direction 1)"),
            )
            addObjectProperty(
                obj,
                "D2",
                "0 1/m^2",
                "App::PropertyQuantity",
                "Darcy-Forchheimer",
                QT_TRANSLATE_NOOP("App::Property", "Darcy coefficient (direction 2)"),
            )
            addObjectProperty(
                obj,
                "D3",
                "0 1/m^2",
                "App::PropertyQuantity",
                "Darcy-Forchheimer",
                QT_TRANSLATE_NOOP("App::Property", "Darcy coefficient (direction 3)"),
            )
            addObjectProperty(
                obj,
                "F1",
                "0 1/m",
                "App::PropertyQuantity",
                "Darcy-Forchheimer",
                QT_TRANSLATE_NOOP("App::Property", "Forchheimer coefficient (direction 1)"),
            )
            addObjectProperty(
                obj,
                "F2",
                "0 1/m",
                "App::PropertyQuantity",
                "Darcy-Forchheimer",
                QT_TRANSLATE_NOOP("App::Property", "Forchheimer coefficient (direction 2)"),
            )
            addObjectProperty(
                obj,
                "F3",
                "0 1/m",
                "App::PropertyQuantity",
                "Darcy-Forchheimer",
                QT_TRANSLATE_NOOP("App::Property", "Forchheimer coefficient (direction 3)"),
            )
            addObjectProperty(
                obj,
                "e1",
                FreeCAD.Vector(1, 0, 0),
                "App::PropertyVector",
                "Darcy-Forchheimer",
                QT_TRANSLATE_NOOP("App::Property", "Principal direction 1"),
            )
            addObjectProperty(
                obj,
                "e2",
                FreeCAD.Vector(0, 1, 0),
                "App::PropertyVector",
                "Darcy-Forchheimer",
                QT_TRANSLATE_NOOP("App::Property", "Principal direction 2"),
            )
            addObjectProperty(
                obj,
                "e3",
                FreeCAD.Vector(0, 0, 1),
                "App::PropertyVector",
                "Darcy-Forchheimer",
                QT_TRANSLATE_NOOP("App::Property", "Principal direction 3"),
            )
            addObjectProperty(
                obj,
                "OuterDiameter",
                "0 m",
                "App::PropertyLength",
                "Jakob",
                QT_TRANSLATE_NOOP("App::Property", "Tube diameter"),
            )
            addObjectProperty(
                obj,
                "TubeAxis",
                FreeCAD.Vector(0, 0, 1),
                "App::PropertyVector",
                "Jakob",
                QT_TRANSLATE_NOOP("App::Property", "Direction parallel to tubes"),
            )
            addObjectProperty(
                obj,
                "TubeSpacing",
                "0 m",
                "App::PropertyLength",
                "Jakob",
                QT_TRANSLATE_NOOP("App::Property", "Spacing between tube layers"),
            )
            addObjectProperty(
                obj,
                "SpacingDirection",
                FreeCAD.Vector(1, 0, 0),
                "App::PropertyVector",
                "Jakob",
                QT_TRANSLATE_NOOP("App::Property", "Direction normal to tube layers"),
            )
            addObjectProperty(
                obj,
                "AspectRatio",
                "1.73",
                "App::PropertyQuantity",
                "Jakob",
                QT_TRANSLATE_NOOP(
                    "App::Property", "Tube spacing aspect ratio (layer-to-layer : tubes in layer)"
                ),
            )
            addObjectProperty(
                obj,
                "VelocityEstimate",
                "0 m/s",
                "App::PropertySpeed",
                "Jakob",
                QT_TRANSLATE_NOOP("App::Property", "Approximate flow velocity"),
            )
        elif obj.Name.startswith("InitialisationZone"):
            addObjectProperty(
                obj,
                "VelocitySpecified",
                False,
                "App::PropertyBool",
                "Initialisation zone",
                QT_TRANSLATE_NOOP("App::Property", "Whether the zone initialises velocity"),
            )
            addObjectProperty(
                obj,
                "Ux",
                "0 m/s",
                "App::PropertySpeed",
                "Initialisation zone",
                QT_TRANSLATE_NOOP("App::Property", "Velocity (x component)"),
            )
            addObjectProperty(
                obj,
                "Uy",
                "0 m/s",
                "App::PropertySpeed",
                "Initialisation zone",
                QT_TRANSLATE_NOOP("App::Property", "Velocity (y component)"),
            )
            addObjectProperty(
                obj,
                "Uz",
                "0 m/s",
                "App::PropertySpeed",
                "Initialisation zone",
                QT_TRANSLATE_NOOP("App::Property", "Velocity (z component)"),
            )
            addObjectProperty(
                obj,
                "PressureSpecified",
                False,
                "App::PropertyBool",
                "Initialisation zone",
                QT_TRANSLATE_NOOP("App::Property", "Whether the zone initialises pressure"),
            )
            addObjectProperty(
                obj,
                "Pressure",
                "0 kg/m/s^2",
                "App::PropertyPressure",
                "Initialisation zone",
                QT_TRANSLATE_NOOP("App::Property", "Static pressure"),
            )
            addObjectProperty(
                obj,
                "TemperatureSpecified",
                False,
                "App::PropertyBool",
                "Initialisation zone",
                QT_TRANSLATE_NOOP("App::Property", "Whether the zone initialises temperature"),
            )
            addObjectProperty(
                obj,
                "Temperature",
                "293 K",
                "App::PropertyTemperature",
                "Initialisation zone",
                QT_TRANSLATE_NOOP("App::Property", "Temperature"),
            )
            addObjectProperty(
                obj,
                "VolumeFractionSpecified",
                True,
                "App::PropertyBool",
                "Initialisation zone",
                QT_TRANSLATE_NOOP("App::Property", "Whether the zone initialises volume fraction"),
            )
            addObjectProperty(
                obj,
                "VolumeFractions",
                {},
                "App::PropertyMap",
                "Initialisation zone",
                QT_TRANSLATE_NOOP("App::Property", "Volume fraction values"),
            )

    def onDocumentRestored(self, obj):
        self.initProperties(obj)

    def execute(self, fp):
        list_of_shapes = []
        for r in fp.ShapeRefs:
            object = r[0]
            try:
                list_of_shapes.append(object.Shape)
            except Part.OCCError:  # In case solid deleted
                pass
        if list_of_shapes:
            fp.Shape = Part.makeCompound(list_of_shapes)
        else:
            fp.Shape = Part.Shape()

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None

    # dumps and loads replace __getstate__ and __setstate__ post v. 0.21.2
    def dumps(self):
        return None

    def loads(self, state):
        return None


class _CfdZone:
    """ Backward compatibility for old class name when loading from file """
    def onDocumentRestored(self, obj):
        CfdZone(obj)

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None

    # dumps and loads replace __getstate__ and __setstate__ post v. 0.21.2
    def dumps(self):
        return None

    def loads(self, state):
        return None


class ViewProviderCfdZone:
    """ A View Provider for Zone objects. """
    def __init__(self, vobj):
        """ Set this object to the proxy object of the actual view provider """
        vobj.Proxy = self
        self.taskd = None

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object
        self.ViewObject.ShapeColor = (0.5, 0.0, 1.0)
        self.ViewObject.Transparency = 70
        # Setup the scene sub-graph of the view provider, this method is mandatory
        return

    def updateData(self, obj, prop):
        analysis_obj = CfdTools.getParentAnalysisObject(obj)
        if analysis_obj and not analysis_obj.Proxy.loading:
            analysis_obj.NeedsCaseRewrite = True

    def getDisplayModes(self, obj):
        """ Return a list of display modes. """
        modes = []
        return modes

    def getDefaultDisplayMode(self):
        """ Return the name of the default display mode. It must be defined in getDisplayModes. """
        return "Shaded"

    def setDisplayMode(self, mode):
        """ Map the display mode defined in attach with those defined in getDisplayModes. Since they have the same
        names nothing needs to be done. This method is optional.
        """
        return mode

    def onChanged(self, vp, prop):
        return

    def getIcon(self):
        if self.Object.Name.startswith('PorousZone'):
            icon_path = os.path.join(CfdTools.getModulePath(), "Gui", "Icons", "porous.svg")
        else:
            icon_path = os.path.join(CfdTools.getModulePath(), "Gui", "Icons", "alpha.svg")
        return icon_path

    def setEdit(self, vobj, mode):
        from CfdOF.Solve import TaskPanelCfdZone
        import importlib
        importlib.reload(TaskPanelCfdZone)
        self.taskd = TaskPanelCfdZone.TaskPanelCfdZone(self.Object)
        self.taskd.obj = vobj.Object
        FreeCADGui.Control.showDialog(self.taskd)
        return True

    def doubleClicked(self, vobj):
        doc = FreeCADGui.getDocument(vobj.Object.Document)
        # Overwrite the doubleClicked to make sure no other Material taskd (and thus no selection observer) is still
        # active
        if not doc.getInEdit():
            doc.setEdit(vobj.Object.Name)
        else:
            FreeCAD.Console.PrintError('Task dialog already active\n')
            FreeCADGui.Control.showTaskView()
        return True

    def unsetEdit(self, vobj, mode):
        if self.taskd:
            self.taskd.closing()
            self.taskd = None
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


class _ViewProviderCfdZone:
    """ Backward compatibility for old class name when loading from file """
    def attach(self, vobj):
        new_proxy = ViewProviderCfdZone(vobj)
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
