# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2017 Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>          *
# *   Copyright (c) 2017 Alfred Bogaers (CSIR) <abogaers@csir.co.za>        *
# *   Copyright (c) 2017 Johan Heyns (CSIR) <jheyns@csir.co.za>             *
# *   Copyright (c) 2019-2021 Oliver Oxtoby <oliveroxtoby@gmail.com>        *
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
import Part
import CfdTools
from CfdTools import addObjectProperty
import os
import os.path
if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore


# Constants
POROUS_CORRELATIONS = ['DarcyForchheimer', 'Jakob']
POROUS_CORRELATION_NAMES = ["Darcy-Forchheimer coefficients", "Staggered tube bundle (Jakob)"]
POROUS_CORRELATION_TIPS = ["Specify viscous and inertial drag tensors by giving their principal components and "
                           "directions (these will be made orthogonal)", "Specify geometry of parallel tube bundle "
                                                                         "with staggered layers."]

ASPECT_RATIOS = ["1.0", "1.73", "1.0"]
ASPECT_RATIO_NAMES = ["User defined", "Equilateral", "Rotated square"]
ASPECT_RATIO_TIPS = ["", "Equilateral triangles pointing perpendicular to spacing direction",
                     "45 degree angles; isotropic"]


def makeCfdPorousZone(name='PorousZone'):
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", name)
    _CfdZone(obj)
    if FreeCAD.GuiUp:
        _ViewProviderCfdZone(obj.ViewObject)
    return obj


def makeCfdInitialisationZone(name='InitialisationZone'):
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", name)
    _CfdZone(obj)
    if FreeCAD.GuiUp:
        _ViewProviderCfdZone(obj.ViewObject)
    return obj


class _CommandCfdPorousZone:
    def GetResources(self):
        icon_path = os.path.join(CfdTools.get_module_path(), "Gui", "Resources", "icons", "porous.png")
        return {'Pixmap': icon_path,
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Cfd_PorousZone", "Porous zone"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Cfd_PorousZone", "Select and create a porous zone")}

    def IsActive(self):
        return CfdTools.getActiveAnalysis() is not None

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Select and create a porous zone")
        FreeCADGui.doCommand("")
        FreeCADGui.addModule("CfdZone")
        FreeCADGui.addModule("CfdTools")
        FreeCADGui.doCommand("CfdTools.getActiveAnalysis().addObject(CfdZone.makeCfdPorousZone())")
        FreeCADGui.ActiveDocument.setEdit(FreeCAD.ActiveDocument.ActiveObject.Name)


class _CommandCfdInitialisationZone:
    def GetResources(self):
        icon_path = os.path.join(CfdTools.get_module_path(), "Gui", "Resources", "icons", "alpha.svg")
        return {'Pixmap': icon_path,
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Cfd_InitialisationZone", "Initialisation zone"),
                'Accel': "",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Cfd_InitialisationZone",
                                                    "Select and create an initialisation zone")}

    def IsActive(self):
        return CfdTools.getActiveAnalysis() is not None

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Select and create an initialisation zone")
        FreeCADGui.doCommand("")
        FreeCADGui.addModule("CfdZone")
        FreeCADGui.addModule("CfdTools")
        FreeCADGui.doCommand(
            "CfdTools.getActiveAnalysis().addObject(CfdZone.makeCfdInitialisationZone())")
        FreeCADGui.ActiveDocument.setEdit(FreeCAD.ActiveDocument.ActiveObject.Name)


class _CfdZone:
    def __init__(self, obj):
        obj.Proxy = self
        self.Type = 'Zone'
        self.initProperties(obj)

    def initProperties(self, obj):
        if addObjectProperty(obj, 'ShapeRefs', [], "App::PropertyLinkSubList", "", "Boundary faces"):
            # Backward compat
            if 'References' in obj.PropertiesList:
                doc = FreeCAD.getDocument(obj.Document.Name)
                for r in obj.References:
                    if not r[1]:
                        obj.ShapeRefs += [doc.getObject(r[0])]
                    else:
                        obj.ShapeRefs += [(doc.getObject(r[0]), r[1])]
                obj.removeProperty('References')
                obj.removeProperty('LinkedObjects')

        if obj.Name.startswith('PorousZone'):
            if addObjectProperty(obj, 'PorousCorrelation', POROUS_CORRELATIONS, "App::PropertyEnumeration",
                                 "Porous zone", "Porous drag model"):
                obj.PorousCorrelation = 'DarcyForchheimer'
            addObjectProperty(obj, 'D1', '0 1/m^2', "App::PropertyQuantity",
                              "Darcy-Forchheimer", "Darcy coefficient (direction 1)")
            addObjectProperty(obj, 'D2', '0 1/m^2', "App::PropertyQuantity",
                              "Darcy-Forchheimer", "Darcy coefficient (direction 2)")
            addObjectProperty(obj, 'D3', '0 1/m^2', "App::PropertyQuantity",
                              "Darcy-Forchheimer", "Darcy coefficient (direction 3)")
            addObjectProperty(obj, 'F1', '0 1/m', "App::PropertyQuantity",
                              "Darcy-Forchheimer", "Forchheimer coefficient (direction 1)")
            addObjectProperty(obj, 'F2', '0 1/m', "App::PropertyQuantity",
                              "Darcy-Forchheimer", "Forchheimer coefficient (direction 2)")
            addObjectProperty(obj, 'F3', '0 1/m', "App::PropertyQuantity",
                              "Darcy-Forchheimer", "Forchheimer coefficient (direction 3)")
            addObjectProperty(obj, 'e1', FreeCAD.Vector(1, 0, 0), "App::PropertyVector",
                              "Darcy-Forchheimer", "Principal direction 1")
            addObjectProperty(obj, 'e2', FreeCAD.Vector(0, 1, 0), "App::PropertyVector",
                              "Darcy-Forchheimer", "Principal direction 2")
            addObjectProperty(obj, 'e3', FreeCAD.Vector(0, 0, 1), "App::PropertyVector",
                              "Darcy-Forchheimer", "Principal direction 3")
            addObjectProperty(obj, 'OuterDiameter', '0 m', "App::PropertyLength",
                              "Jakob", "Tube diameter")
            addObjectProperty(obj, 'TubeAxis', FreeCAD.Vector(0, 0, 1), "App::PropertyVector",
                              "Jakob", "Direction parallel to tubes")
            addObjectProperty(obj, 'TubeSpacing', '0 m', "App::PropertyLength",
                              "Jakob", "Spacing between tube layers")
            addObjectProperty(obj, 'SpacingDirection', FreeCAD.Vector(1, 0, 0), "App::PropertyVector",
                              "Jakob", "Direction normal to tube layers")
            addObjectProperty(obj, 'AspectRatio', '1.73', "App::PropertyQuantity",
                              "Jakob", "Tube spacing aspect ratio (layer-to-layer : tubes in layer)")
            addObjectProperty(obj, 'VelocityEstimate', '0 m/s', "App::PropertySpeed",
                              "Jakob", "Approximate flow velocity")
        elif obj.Name.startswith('InitialisationZone'):
            addObjectProperty(obj, "VelocitySpecified", False, "App::PropertyBool",
                              "Initialisation zone", "Whether the zone initialises velocity")
            addObjectProperty(obj, 'Ux', '0 m/s', "App::PropertySpeed",
                              "Initialisation zone", "Velocity (x component)")
            addObjectProperty(obj, 'Uy', '0 m/s', "App::PropertySpeed",
                              "Initialisation zone", "Velocity (y component)")
            addObjectProperty(obj, 'Uz', '0 m/s', "App::PropertySpeed",
                              "Initialisation zone", "Velocity (z component)")
            addObjectProperty(obj, "PressureSpecified", False, "App::PropertyBool",
                              "Initialisation zone", "Whether the zone initialises pressure")
            addObjectProperty(obj, 'Pressure', '0 kg/m/s^2', "App::PropertyPressure",
                              "Initialisation zone", "Static pressure")
            addObjectProperty(obj, "VolumeFractionSpecified", True, "App::PropertyBool",
                              "Initialisation zone", "Whether the zone initialises volume fraction")
            addObjectProperty(obj, "VolumeFractions", {}, "App::PropertyMap",
                              "Initialisation zone", "Volume fraction values")

    def onDocumentRestored(self, obj):
        self.initProperties(obj)

    def execute(self, fp):
        listOfShapes = []
        for r in fp.ShapeRefs:
            object = r[0]
            try:
                listOfShapes.append(object.Shape)
            except Part.OCCError:  # In case solid deleted
                pass
        if listOfShapes:
            fp.Shape = Part.makeCompound(listOfShapes)
        else:
            fp.Shape = Part.Shape()

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None


class _ViewProviderCfdZone:
    """ A View Provider for Zone objects. """
    def __init__(self, vobj):
        """ Set this object to the proxy object of the actual view provider """
        vobj.Proxy = self

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object
        self.ViewObject.ShapeColor = (0.5,0.0,1.0)
        self.ViewObject.Transparency = 70
        # Setup the scene sub-graph of the view provider, this method is mandatory
        return

    def updateData(self, fp, prop):
        """ If a property of the handled feature has changed we have the chance to handle this here """
        return

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
            icon_path = os.path.join(CfdTools.get_module_path(), "Gui", "Resources", "icons", "porous.png")
        else:
            icon_path = os.path.join(CfdTools.get_module_path(), "Gui", "Resources", "icons", "alpha.svg")
        return icon_path

    def setEdit(self, vobj, mode):
        import _TaskPanelCfdZone
        taskd = _TaskPanelCfdZone._TaskPanelCfdZone(self.Object)
        taskd.obj = vobj.Object
        FreeCADGui.Control.showDialog(taskd)
        return True

    def unsetEdit(self, vobj, mode):
        FreeCADGui.Control.closeDialog()
        return

    def doubleClicked(self, vobj):
        doc = FreeCADGui.getDocument(vobj.Object.Document)
        # Overwrite the doubleClicked to make sure no other Material taskd (and thus no selection observer) is still
        # active
        if not doc.getInEdit():
            doc.setEdit(vobj.Object.Name)
        else:
            FreeCAD.Console.PrintError('Task dialog already open\n')
        return True

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Cfd_PorousZone', _CommandCfdPorousZone())
    FreeCADGui.addCommand('Cfd_InitialisationZone', _CommandCfdInitialisationZone())
