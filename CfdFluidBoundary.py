# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2017 Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>          *
# *   Copyright (c) 2017 Alfred Bogaers (CSIR) <abogaers@csir.co.za>        *
# *   Copyright (c) 2017 Johan Heyns (CSIR) <jheyns@csir.co.za>             *
# *   Copyright (c) 2019-2022 Oliver Oxtoby <oliveroxtoby@gmail.com>        *
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

import os
import FreeCAD
from pivy import coin
import Part
import CfdTools
from CfdTools import addObjectProperty
if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore
    import _TaskPanelCfdFluidBoundary

# Constants
BOUNDARY_NAMES = ["Wall", "Inlet", "Outlet", "Open", "Constraint", "Baffle"]

BOUNDARY_TYPES = ["wall", "inlet", "outlet", "open", "constraint", "baffle"]

SUBNAMES = [["No-slip (viscous)", "Slip (inviscid)", "Partial slip", "Translating", "Rough"],
            ["Uniform velocity", "Volumetric flow rate", "Mass flow rate", "Total pressure", "Static pressure"],
            ["Static pressure", "Uniform velocity", "Extrapolated"],
            ["Ambient pressure", "Far-field"],
            ["Symmetry"],
            ["Porous Baffle"]]

SUBTYPES = [["fixedWall", "slipWall", "partialSlipWall", "translatingWall", "roughWall"],
            ["uniformVelocityInlet", "volumetricFlowRateInlet", "massFlowRateInlet", "totalPressureInlet", "staticPressureInlet"],
            ["staticPressureOutlet", "uniformVelocityOutlet", "outFlowOutlet"],
            ["totalPressureOpening", "farField"],
            ["symmetry"],
            ["porousBaffle"]]

SUBTYPES_HELPTEXT = [["Zero velocity relative to wall",
                      "Frictionless wall; zero normal velocity",
                      "Blended fixed/slip",
                      "Fixed velocity tangential to wall; zero normal velocity",
                      "Wall roughness function"],
                     ["Velocity specified; normal component imposed for reverse flow",
                      "Uniform volume flow rate specified",
                      "Uniform mass flow rate specified",
                      "Total pressure specified; treated as static pressure for reverse flow",
                      "Static pressure specified"],
                     ["Static pressure specified for outflow and total pressure for reverse flow",
                      "Normal component imposed for outflow; velocity fixed for reverse flow",
                      "All fields extrapolated; possibly unstable"],
                     ["Boundary open to surroundings with total pressure specified",
                      "Characteristic-based non-reflecting boundary"],
                     ["Symmetry of flow quantities about boundary face"],
                     ["Permeable screen"]]

# For each sub-type, whether the basic tab is enabled, the panel numbers to show (ignored if false), whether
# direction reversal is checked by default (only used for panel 0), whether turbulent inlet panel is shown,
# whether volume fraction panel is shown, whether thermal GUI is shown,
# rows of thermal UI to show (all shown if None)
BOUNDARY_UI = [[[False, [], False, False, False, True, None],  # No slip
                [False, [], False, False, False, True, None],  # Slip
                [True, [2], False, False, False, True, None],  # Partial slip
                [True, [0], False, False, False, True, None],  # Translating wall
                [True, [0], False, False, False, True, None]],  # Rough
               [[True, [0, 1], True, True, True, True, [2]],  # Velocity
                [True, [3], False, True, True, True, [2]],  # Vol flow rate
                [True, [4], False, True, True, True, [2]],  # Mass Flow rate
                [True, [1], False, True, True, True, [2]],  # Total pressure
                [True, [0, 1], False, True, True, True, [2]]],  # Static pressure
               [[True, [0, 1], False, False, True, True, [2]],  # Static pressure
                [True, [0, 1], False, False, True, True, [2]],  # Uniform velocity
                [False, [], False, False, False, False, None]],  # Outflow
               [[True, [1], False, True, True, True, [2]],  # Opening
                [True, [0, 1], False, True, False, True, [2]]],  # Far-field
               [[False, [], False, False, False, False, None]],  # Symmetry plane
               [[True, [5], False, False, False, False, None]]]  # Permeable screen

# For each turbulence model: Name, label, help text, displayed rows
TURBULENT_INLET_SPEC = {'kOmegaSST':
                        [["Kinetic Energy & Specific Dissipation Rate",
                          "Intensity & Length Scale"],
                         ["TKEAndSpecDissipationRate",
                          "intensityAndLengthScale"],
                         ["k and omega specified",
                          "Turbulence intensity and eddy length scale"],
                         [[0, 2],  # k, omega
                          [3, 4]]],  # I, l
                        'kEpsilon':
                        [["Kinetic Energy & Dissipation Rate",
                          "Intensity & Length Scale"],
                         ["TKEAndDissipationRate",
                          "intensityAndLengthScale"],
                         ["k and epsilon specified",
                          "Turbulence intensity and eddy length scale"],
                         [[0, 1],  # k, epsilon
                          [3, 4]]],  # I, l
                        'SpalartAllmaras':
                        [["Modified Turbulent Viscosity",
                          "Intensity & Length Scale"],
                         ["TransportedNuTilda",
                          "intensityAndLengthScale"],
                         ["nu-tilde specified",
                          "Turbulence intensity and eddy length scale"],
                         [[5],  # nu tilda
                          [3, 4]]],  # I, l
                        "kOmegaSSTLM":
                        [["Kinetic Energy, Specific Dissipation Rate, Intermittency and ReThetat",
                          "Intensity & Length Scale"],
                         ["TKESpecDissipationRateGammaAndReThetat",
                          "intensityAndLengthScale"],
                         ["k, omega, gamma and reThetat specified",
                          "Turbulence intensity and eddy length scale"],
                         [[0, 2, 6, 7],  # k, omega, gamma and reThetat
                          [3, 4]]],  # I, l
                        'kOmegaSSTDES':
                        [["Kinetic Energy & Specific Dissipation Rate",
                          "Intensity & Length Scale"],
                         ["TKEAndSpecDissipationRate",
                          "intensityAndLengthScale"],
                         ["k and omega specified",
                          "Turbulence intensity and eddy length scale"],
                         [[0, 2],  # k, omega
                          [3, 4]]],
                        'kOmegaSSTDDES':
                        [["Kinetic Energy & Specific Dissipation Rate",
                          "Intensity & Length Scale"],
                         ["TKEAndSpecDissipationRate",
                          "intensityAndLengthScale"],
                         ["k and omega specified",
                          "Turbulence intensity and eddy length scale"],
                         [[0, 2],  # k, omega
                          [3, 4]]],
                        'kOmegaSSTIDDES':
                        [["Kinetic Energy & Specific Dissipation Rate",
                          "Intensity & Length Scale"],
                         ["TKEAndSpecDissipationRate",
                          "intensityAndLengthScale"],
                         ["k and omega specified",
                          "Turbulence intensity and eddy length scale"],
                         [[0, 2],  # k, omega
                          [3, 4]]],
                        'SpalartAllmarasDES':
                        [["Modified Turbulent Viscosity",
                          "Intensity & Length Scale"],
                         ["TransportedNuTilda",
                          "intensityAndLengthScale"],
                         ["nu-tilde specified",
                          "Turbulence intensity and eddy length scale"],
                         [[5],  # nu tilda
                          [3, 4]]],
                        'SpalartAllmarasDDES':
                        [["Modified Turbulent Viscosity",
                          "Intensity & Length Scale"],
                         ["TransportedNuTilda",
                          "intensityAndLengthScale"],
                         ["nu-tilde specified",
                          "Turbulence intensity and eddy length scale"],
                         [[5],  # nu tilda
                          [3, 4]]],
                        'SpalartAllmarasIDDES':
                        [["Modified Turbulent Viscosity",
                          "Intensity & Length Scale"],
                         ["TransportedNuTilda",
                          "intensityAndLengthScale"],
                         ["nu-tilde specified",
                          "Turbulence intensity and eddy length scale"],
                         [[5],  # nu tilda
                          [3, 4]]],
                        "kEqn":
                        [["Kinetic Energy & Turbulent viscosity"],
                         ["TurbulentViscosityAndK"],
                         ["k and turbulent viscosity specified"],
                         [[0, 8]]],     # nut
                        "Smagorinsky":
                        [["Turbulent viscosity"],
                         ["TurbulentViscosity"],
                         ["turbulent viscosity specified"],
                         [[8]]],  # nut
                        "WALE":
                        [["Turbulent viscosity"],
                         ["TurbulentViscosity"],
                         ["turbulent viscosity specified"],
                         [[8]]]  # nut
                        }

THERMAL_BOUNDARY_NAMES = ["Fixed temperature",
                          "Adiabatic",
                          "Fixed conductive heat flux",
                          "Heat transfer coefficient"]

THERMAL_BOUNDARY_TYPES = ["fixedValue", "zeroGradient", "fixedGradient", "heatTransferCoeff"]

THERMAL_HELPTEXT = ["Fixed Temperature", "No conductive heat transfer", "Fixed conductive heat flux",
                    "Specified heat transfer coefficient and ambient temperature"]

# For each thermal BC, the input rows presented to the user
BOUNDARY_THERMALTAB = [[0], [], [1], [2, 0]]

POROUS_METHODS = ['porousCoeff', 'porousScreen']


def makeCfdFluidBoundary(name="CfdFluidBoundary"):
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", name)
    _CfdFluidBoundary(obj)
    if FreeCAD.GuiUp:
        _ViewProviderCfdFluidBoundary(obj.ViewObject)
    return obj


class _CommandCfdFluidBoundary:
    def GetResources(self):
        icon_path = os.path.join(CfdTools.get_module_path(), "Gui", "Resources", "icons", "boundary.svg")
        return {
            'Pixmap': icon_path,
            'MenuText': QtCore.QT_TRANSLATE_NOOP("Cfd_FluidBoundary", "Fluid boundary"),
            'Accel': "C, W",
            'ToolTip': QtCore.QT_TRANSLATE_NOOP("Cfd_FluidBoundary", "Creates a CFD fluid boundary")}

    def IsActive(self):
        return CfdTools.getActiveAnalysis() is not None

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Create CfdFluidBoundary")
        FreeCADGui.doCommand("")
        FreeCADGui.addModule("CfdFluidBoundary")
        FreeCADGui.addModule("CfdTools")
        FreeCADGui.doCommand("CfdTools.getActiveAnalysis().addObject(CfdFluidBoundary.makeCfdFluidBoundary())")
        FreeCADGui.ActiveDocument.setEdit(FreeCAD.ActiveDocument.ActiveObject.Name)


class _CfdFluidBoundary:
    def __init__(self, obj):
        obj.Proxy = self
        self.Type = "CfdFluidBoundary"
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

        addObjectProperty(obj, 'DefaultBoundary', False, "App::PropertyBool", "Boundary faces")
        addObjectProperty(obj, 'BoundaryType', BOUNDARY_TYPES, "App::PropertyEnumeration", "",
                          "Boundary condition category")

        all_subtypes = []
        for s in SUBTYPES:
            all_subtypes += s

        addObjectProperty(obj, 'BoundarySubType', all_subtypes, "App::PropertyEnumeration", "",
                          "Boundary condition type")
        addObjectProperty(obj, 'VelocityIsCartesian', True, "App::PropertyBool", "Flow",
                          "Whether to use components of velocity")
        addObjectProperty(obj, 'Ux', '0 m/s', "App::PropertySpeed", "Flow",
                          "Velocity (x component)")
        addObjectProperty(obj, 'Uy', '0 m/s', "App::PropertySpeed", "Flow",
                          "Velocity (y component)")
        addObjectProperty(obj, 'Uz', '0 m/s', "App::PropertySpeed", "Flow",
                          "Velocity (z component)")
        addObjectProperty(obj, 'VelocityMag', '0 m/s', "App::PropertySpeed", "Flow",
                          "Velocity magnitude")
        addObjectProperty(obj, 'DirectionFace', '', "App::PropertyString", "Flow",
                          "Face describing direction (normal)")
        addObjectProperty(obj, 'ReverseNormal', False, "App::PropertyBool", "Flow",
                          "Direction is inward-pointing if true")
        addObjectProperty(obj, 'Pressure', '0 Pa', "App::PropertyPressure", "Flow",
                          "Static pressure")
        addObjectProperty(obj, 'SlipRatio', '0', "App::PropertyQuantity", "Flow",
                          "Slip ratio")
        addObjectProperty(obj, 'VolFlowRate', '0 m^3/s', "App::PropertyQuantity", "Flow",
                          "Volume flow rate")
        addObjectProperty(obj, 'MassFlowRate', '0 kg/s', "App::PropertyQuantity", "Flow",
                          "Mass flow rate")

        if addObjectProperty(obj, 'PorousBaffleMethod', POROUS_METHODS, "App::PropertyEnumeration",
                             "Baffle", "Baffle"):
            obj.PorousBaffleMethod = 'porousCoeff'

        addObjectProperty(obj, 'PressureDropCoeff', '0', "App::PropertyQuantity", "Baffle",
                          "Porous baffle pressure drop coefficient")
        addObjectProperty(obj, 'ScreenWireDiameter', '0.2 mm', "App::PropertyLength", "Baffle",
                          "Porous screen mesh diameter")
        addObjectProperty(obj, 'ScreenSpacing', '2 mm', "App::PropertyLength", "Baffle",
                          "Porous screen mesh spacing")

        addObjectProperty(obj, 'ThermalBoundaryType', THERMAL_BOUNDARY_TYPES, "App::PropertyEnumeration", "Thermal",
                          "Type of thermal boundary")
        addObjectProperty(obj, 'Temperature', '293 K', "App::PropertyQuantity", "Thermal",
                          "Temperature")
        addObjectProperty(obj, 'HeatFlux', '0 W/m^2', "App::PropertyQuantity", "Thermal",
                          "Wall heat flux")
        addObjectProperty(obj, 'HeatTransferCoeff', '0 W/m^2/K', "App::PropertyQuantity", "Thermal",
                          "Wall heat transfer coefficient")

        # Turbulence
        all_turb_specs = []
        for k in TURBULENT_INLET_SPEC:
            all_turb_specs += TURBULENT_INLET_SPEC[k][1]

        all_turb_specs = list(set(all_turb_specs))  # Remove duplicates

        if addObjectProperty(obj, 'TurbulenceInletSpecification', all_turb_specs, "App::PropertyEnumeration",
                             "Turbulence", "Turbulent quantities specified"):
            obj.TurbulenceInletSpecification = 'intensityAndLengthScale'

        # k omega SST
        addObjectProperty(obj, 'TurbulentKineticEnergy', '0.01 m^2/s^2', "App::PropertyQuantity", "Turbulence",
                          "Turbulent kinetic energy")
        addObjectProperty(obj, 'SpecificDissipationRate', '1 rad/s', "App::PropertyQuantity", "Turbulence",
                          "Specific turbulent dissipation rate")

        # k epsilon
        addObjectProperty(obj, 'DissipationRate', '50 m^2/s^3', "App::PropertyQuantity", "Turbulence",
                          "Turbulent dissipation rate")

        # Spalart Allmaras
        addObjectProperty(obj, 'NuTilda', '55 m^2/s^1', "App::PropertyQuantity", "Turbulence",
                          "Modified turbulent viscosity")

        # Langtry Menter 4 eqn k omega SST
        addObjectProperty(obj, 'Intermittency', '1', "App::PropertyQuantity", "Turbulence",
                          "Turbulent intermittency")
        addObjectProperty(obj, 'ReThetat', '1', "App::PropertyQuantity", "Turbulence",
                          "Transition momentum thickness Reynolds number")

        # LES models
        addObjectProperty(obj, 'TurbulentViscosity', '50 m^2/s^1', "App::PropertyQuantity", "Turbulence",
                          "Turbulent viscosity")
        addObjectProperty(obj, 'kEqnTurbulentKineticEnergy', '0.01 m^2/s^2', "App::PropertyQuantity", "Turbulence",
                          "Turbulent viscosity")
        addObjectProperty(obj, 'kEqnTurbulentViscosity', '50 m^2/s^1', "App::PropertyQuantity", "Turbulence",
                          "Turbulent viscosity")

        # General
        addObjectProperty(obj, 'TurbulenceIntensityPercentage', '1', "App::PropertyQuantity", "Turbulence",
                          "Turbulence intensity (percent)")
        # Backward compat
        if 'TurbulenceIntensity' in obj.PropertiesList:
            obj.TurbulenceIntensityPercentage = obj.TurbulenceIntensity*100.0
            obj.removeProperty('TurbulenceIntensity')

        addObjectProperty(obj, 'TurbulenceLengthScale', '0.1 m', "App::PropertyLength", "Turbulence",
                          "Length scale of turbulent eddies")
        addObjectProperty(obj, 'VolumeFractions', {}, "App::PropertyMap", "Volume fraction",
                          "Volume fractions")

    def onDocumentRestored(self, obj):
        self.initProperties(obj)

    def execute(self, obj):
        """ Create compound part at recompute. """
        shape = CfdTools.makeShapeFromReferences(obj.ShapeRefs, False)
        if shape is None:
            shape = Part.Shape()
        if shape != obj.Shape:
            obj.Shape = shape
        self.updateBoundaryColors(obj)

    def updateBoundaryColors(self, obj):
        if FreeCAD.GuiUp:
            vobj = obj.ViewObject
            vobj.Transparency = 20
            if obj.BoundaryType == 'wall':
                vobj.ShapeColor = (0.1, 0.1, 0.1)  # Dark grey
            elif obj.BoundaryType == 'inlet':
                vobj.ShapeColor = (0.0, 0.0, 1.0)  # Blue
            elif obj.BoundaryType == 'outlet':
                vobj.ShapeColor = (1.0, 0.0, 0.0)  # Red
            elif obj.BoundaryType == 'open':
                vobj.ShapeColor = (0.0, 1.0, 1.0)  # Cyan
            elif (obj.BoundaryType == 'constraint') or \
                 (obj.BoundaryType == 'baffle'):
                vobj.ShapeColor = (0.5, 0.0, 1.0)  # Purple
            else:
                vobj.ShapeColor = (1.0, 1.0, 1.0)  # White

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None


class _ViewProviderCfdFluidBoundary:
    def __init__(self, vobj):
        vobj.Proxy = self
        self.taskd = None

    def getIcon(self):
        icon_path = os.path.join(CfdTools.get_module_path(), "Gui", "Resources", "icons", "boundary.svg")
        return icon_path

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object
        self.standard = coin.SoGroup()
        vobj.addDisplayMode(self.standard, "Standard")
        #self.ViewObject.Transparency = 95
        return

    def getDisplayModes(self, obj):
        modes = []
        return modes

    def getDefaultDisplayMode(self):
        return "Shaded"

    def setDisplayMode(self, mode):
        return mode

    def updateData(self, obj, prop):
        analysis_obj = CfdTools.getParentAnalysisObject(obj)
        if prop == 'ShapeRefs' or prop == 'Shape':
            # Only a change to the shape allocation or geometry affects mesh
            if analysis_obj and not analysis_obj.Proxy.loading:
                analysis_obj.NeedsMeshRewrite = True
        else:
            # Else mark case itself as needing updating
            if analysis_obj and not analysis_obj.Proxy.loading:
                analysis_obj.NeedsCaseRewrite = True

    def onChanged(self, vobj, prop):
        CfdTools.setCompSolid(vobj)

    def setEdit(self, vobj, mode):
        analysis_object = CfdTools.getParentAnalysisObject(self.Object)
        if analysis_object is None:
            CfdTools.cfdErrorBox("Boundary must have a parent analysis object")
            return False
        physics_model = CfdTools.getPhysicsModel(analysis_object)
        if not physics_model:
            CfdTools.cfdErrorBox("Analysis object must have a physics object")
            return False
        material_objs = CfdTools.getMaterials(analysis_object)

        import _TaskPanelCfdFluidBoundary
        import importlib
        importlib.reload(_TaskPanelCfdFluidBoundary)
        self.taskd = _TaskPanelCfdFluidBoundary.TaskPanelCfdFluidBoundary(self.Object, physics_model, material_objs)
        self.Object.ViewObject.show()
        self.taskd.obj = vobj.Object
        FreeCADGui.Control.showDialog(self.taskd)
        return True

    def doubleClicked(self, vobj):
        doc = FreeCADGui.getDocument(vobj.Object.Document)
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

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Cfd_FluidBoundary', _CommandCfdFluidBoundary())
