# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2017 Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>          *
# *   Copyright (c) 2017 Alfred Bogaers (CSIR) <abogaers@csir.co.za>        *
# *   Copyright (c) 2017 Johan Heyns (CSIR) <jheyns@csir.co.za>             *
# *   Copyright (c) 2019-2025 Oliver Oxtoby <oliveroxtoby@gmail.com>        *
# *   Copyright (c) 2022 Jonathan Bergh <bergh.jonathan@gmail.com>          *
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

import FreeCAD
import Part
from pivy import coin

from CfdOF import CfdTools
from CfdOF.CfdTools import addObjectProperty

if FreeCAD.GuiUp:
    import FreeCADGui

    from CfdOF.Solve import TaskPanelCfdFluidBoundary


translate = FreeCAD.Qt.translate
QT_TRANSLATE_NOOP = FreeCAD.Qt.QT_TRANSLATE_NOOP

# Constants
BOUNDARY_NAMES = [
    translate("Boundary", "Wall"),
    translate("Boundary", "Inlet"),
    translate("Boundary", "Outlet"),
    translate("Boundary", "Open"),
    translate("Boundary", "Constraint"),
    translate("Boundary", "Baffle"),
]

# NOTE: don't translate this
BOUNDARY_TYPES = ["wall", "inlet", "outlet", "open", "constraint", "baffle"]

SUBNAMES = [
    [
        translate("Subnames", "No-slip (viscous)"),
        translate("Subnames", "Slip (inviscid)"),
        translate("Subnames", "Partial slip"),
        translate("Subnames", "Rotating"),
        translate("Subnames", "Translating"),
        translate("Subnames", "Rough"),
    ],
    [
        translate("Subnames", "Uniform velocity"),
        translate("Subnames", "Volumetric flow rate"),
        translate("Subnames", "Mass flow rate"),
        translate("Subnames", "Total pressure"),
        translate("Subnames", "Static pressure"),
    ],
    [
        translate("Subnames", "Static pressure"),
        translate("Subnames", "Uniform velocity"),
        translate("Subnames", "Extrapolated"),
    ],
    [translate("Subnames", "Ambient pressure"), translate("Subnames", "Far-field")],
    [translate("Subnames", "Symmetry"), translate("Subnames", "Periodic")],
    [translate("Subnames", "Porous Baffle")],
]

# NOTE: don't translate this
SUBTYPES = [
    ["fixedWall", "slipWall", "partialSlipWall", "rotatingWall", "translatingWall", "roughWall"],
    [
        "uniformVelocityInlet",
        "volumetricFlowRateInlet",
        "massFlowRateInlet",
        "totalPressureInlet",
        "staticPressureInlet",
    ],
    ["staticPressureOutlet", "uniformVelocityOutlet", "outFlowOutlet"],
    ["totalPressureOpening", "farField"],
    ["symmetry", "cyclicAMI"],
    ["porousBaffle"],
]

SUBTYPES_HELPTEXT = [
    [
        translate("Subtypes", "Zero velocity relative to wall"),
        translate("Subtypes", "Frictionless wall; zero normal velocity"),
        translate("Subtypes", "Blended fixed/slip"),
        translate("Subtypes", "Fixed velocity corresponding to rotation about an axis"),
        translate("Subtypes", "Fixed velocity tangential to wall; zero normal velocity"),
        translate("Subtypes", "Wall roughness function"),
    ],
    [
        translate("Subtypes", "Velocity specified; normal component imposed for reverse flow"),
        translate("Subtypes", "Uniform volume flow rate specified"),
        translate("Subtypes", "Uniform mass flow rate specified"),
        translate(
            "Subtypes", "Total pressure specified; treated as static pressure for reverse flow"
        ),
        translate("Subtypes", "Static pressure specified"),
    ],
    [
        translate(
            "Subtypes", "Static pressure specified for outflow and total pressure for reverse flow"
        ),
        translate(
            "Subtypes", "Normal component imposed for outflow; velocity fixed for reverse flow"
        ),
        translate("Subtypes", "All fields extrapolated; possibly unstable"),
    ],
    [
        translate("Subtypes", "Boundary open to surroundings with total pressure specified"),
        translate("Subtypes", "Characteristic-based non-reflecting boundary"),
    ],
    [
        translate("Subtypes", "Symmetry of flow quantities about boundary face"),
        translate(
            "Subtypes", "Rotationally or translationally periodic flows between two boundary faces"
        ),
    ],
    [translate("Subtypes", "Permeable screen")],
]

# For each sub-type, whether the basic tab is enabled, the panel numbers to show (ignored if false), whether
# direction reversal is checked by default (only used for panel 0), whether turbulent inlet panel is shown,
# whether volume fraction panel is shown, whether thermal GUI is shown,
# rows of thermal UI to show (all shown if None)
BOUNDARY_UI = [[[False, [], False, False, False, True, None, False],  # No slip
                [False, [], False, False, False, True, None, False],  # Slip
                [True, [2], False, False, False, True, None, False],  # Partial slip
                [True, [8], False, False, False, True, None, False],  # Rotating wall
                [True, [0], False, False, False, True, None, False],  # Translating wall
                [True, [0, 6], False, False, False, True, None, False]],  # Rough
               [[True, [0, 1], True, True, True, True, [2], False],  # Velocity
                [True, [3], False, True, True, True, [2], False],  # Vol flow rate
                [True, [4], False, True, True, True, [2], False],  # Mass Flow rate
                [True, [1], False, True, True, True, [2], False],  # Total pressure
                [True, [0, 1], False, True, True, True, [2], False]],  # Static pressure
               [[True, [0, 1], False, False, True, True, [2], False],  # Static pressure
                [True, [0, 1], False, False, True, True, [2], False],  # Uniform velocity
                [False, [], False, False, False, False, None, False]],  # Outflow
               [[True, [1], False, True, True, True, [2], False],  # Opening
                [True, [0, 1], False, True, False, True, [2], False]],  # Far-field
               [[False, [], False, False, False, False, None, False],  # Symmetry plane
                [False, [], False, False, False, False, None, True]],  # Periodic
               [[True, [5], False, False, False, False, None, False]]]  # Permeable screen

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
    CfdFluidBoundary(obj)
    if FreeCAD.GuiUp:
        ViewProviderCfdFluidBoundary(obj.ViewObject)
    return obj


class CommandCfdFluidBoundary:
    def GetResources(self):
        icon_path = os.path.join(CfdTools.getModulePath(), "Gui", "Icons", "boundary.svg")
        return {
            'Pixmap': icon_path,
            'MenuText': QT_TRANSLATE_NOOP("CfdOF_FluidBoundary", "Fluid boundary"),
            'Accel': "C, W",
            'ToolTip': QT_TRANSLATE_NOOP("CfdOF_FluidBoundary", "Creates a CFD fluid boundary")}

    def IsActive(self):
        return CfdTools.getActiveAnalysis() is not None

    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Create CfdFluidBoundary")
        FreeCADGui.doCommand("from CfdOF.Solve import CfdFluidBoundary")
        FreeCADGui.doCommand("from CfdOF import CfdTools")
        FreeCADGui.doCommand("CfdTools.getActiveAnalysis().addObject(CfdFluidBoundary.makeCfdFluidBoundary())")
        FreeCADGui.ActiveDocument.setEdit(FreeCAD.ActiveDocument.ActiveObject.Name)


class CfdFluidBoundary:
    def __init__(self, obj):
        obj.Proxy = self
        self.Type = "CfdFluidBoundary"
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
            if "References" in obj.PropertiesList:
                doc = FreeCAD.getDocument(obj.Document.Name)
                for r in obj.References:
                    if not r[1]:
                        obj.ShapeRefs += [doc.getObject(r[0])]
                    else:
                        obj.ShapeRefs += [(doc.getObject(r[0]), r[1])]
                obj.removeProperty("References")
                obj.removeProperty("LinkedObjects")

        addObjectProperty(
            obj,
            "DefaultBoundary",
            False,
            "App::PropertyBool",
            "Boundary faces",
        )
        addObjectProperty(
            obj,
            "BoundaryType",
            BOUNDARY_TYPES,
            "App::PropertyEnumeration",
            "",
            QT_TRANSLATE_NOOP("App::Property", "Boundary condition category"),
        )

        all_subtypes = []
        for s in SUBTYPES:
            all_subtypes += s

        addObjectProperty(
            obj,
            "BoundarySubType",
            all_subtypes,
            "App::PropertyEnumeration",
            "",
            QT_TRANSLATE_NOOP("App::Property", "Boundary condition type"),
        )
        addObjectProperty(
            obj,
            "VelocityIsCartesian",
            True,
            "App::PropertyBool",
            "Flow",
            QT_TRANSLATE_NOOP("App::Property", "Whether to use components of velocity"),
        )
        addObjectProperty(
            obj,
            "Ux",
            "0 m/s",
            "App::PropertySpeed",
            "Flow",
            QT_TRANSLATE_NOOP("App::Property", "Velocity (x component)"),
        )
        addObjectProperty(
            obj,
            "Uy",
            "0 m/s",
            "App::PropertySpeed",
            "Flow",
            QT_TRANSLATE_NOOP("App::Property", "Velocity (y component)"),
        )
        addObjectProperty(
            obj,
            "Uz",
            "0 m/s",
            "App::PropertySpeed",
            "Flow",
            QT_TRANSLATE_NOOP("App::Property", "Velocity (z component)"),
        )
        addObjectProperty(
            obj,
            "VelocityMag",
            "0 m/s",
            "App::PropertySpeed",
            "Flow",
            QT_TRANSLATE_NOOP("App::Property", "Velocity magnitude"),
        )
        addObjectProperty(
            obj,
            "DirectionFace",
            "",
            "App::PropertyString",
            "Flow",
            QT_TRANSLATE_NOOP("App::Property", "Face describing direction (normal)"),
        )
        addObjectProperty(
            obj,
            "ReverseNormal",
            False,
            "App::PropertyBool",
            "Flow",
            QT_TRANSLATE_NOOP("App::Property", "Direction is inward-pointing if true"),
        )
        addObjectProperty(
            obj,
            "Pressure",
            "100 kPa",
            "App::PropertyPressure",
            "Flow",
            QT_TRANSLATE_NOOP("App::Property", "Static pressure"),
        )
        addObjectProperty(
            obj,
            "SlipRatio",
            "0",
            "App::PropertyQuantity",
            "Flow",
            QT_TRANSLATE_NOOP("App::Property", "Slip ratio"),
        )
        addObjectProperty(
            obj,
            "VolFlowRate",
            "0 m^3/s",
            "App::PropertyQuantity",
            "Flow",
            QT_TRANSLATE_NOOP("App::Property", "Volume flow rate"),
        )
        addObjectProperty(
            obj,
            "MassFlowRate",
            "0 kg/s",
            "App::PropertyQuantity",
            "Flow",
            QT_TRANSLATE_NOOP("App::Property", "Mass flow rate"),
        )

        addObjectProperty(
            obj,
            "RelativeToFrame",
            False,
            "App::PropertyBool",
            "Flow",
            QT_TRANSLATE_NOOP("App::Property", "Relative velocity"),
        )

        if addObjectProperty(
            obj,
            "PorousBaffleMethod",
            POROUS_METHODS,
            "App::PropertyEnumeration",
            "Baffle",
            QT_TRANSLATE_NOOP("App::Property", "Baffle"),
        ):
            obj.PorousBaffleMethod = "porousCoeff"

        addObjectProperty(
            obj,
            "PressureDropCoeff",
            "0",
            "App::PropertyQuantity",
            "Baffle",
            QT_TRANSLATE_NOOP("App::Property", "Porous baffle pressure drop coefficient"),
        )
        addObjectProperty(
            obj,
            "ScreenWireDiameter",
            "0.2 mm",
            "App::PropertyLength",
            "Baffle",
            QT_TRANSLATE_NOOP("App::Property", "Porous screen mesh diameter"),
        )
        addObjectProperty(
            obj,
            "ScreenSpacing",
            "2 mm",
            "App::PropertyLength",
            "Baffle",
            QT_TRANSLATE_NOOP("App::Property", "Porous screen mesh spacing"),
        )

        addObjectProperty(
            obj, 
            'AngularVelocity', 
            '0 rad/s', 
            "App::PropertyQuantity", 
            "Rotating",
            QT_TRANSLATE_NOOP("App::Property", "Rotational angular velocity"),
        )
        addObjectProperty(
            obj, 
            'RotationOrigin', 
            FreeCAD.Vector(0, 0, 0), 
            "App::PropertyPosition", 
            "Rotating",
            QT_TRANSLATE_NOOP("App::Property", "Origin of rotation"),
        )
        addObjectProperty(
            obj, 
            'RotationAxis', 
            FreeCAD.Vector(0, 0, 1), 
            "App::PropertyVector", 
            "Rotating",
            QT_TRANSLATE_NOOP("App::Property", "Axis of rotation"),
        )

        addObjectProperty(
            obj,
            "RoughnessHeight",
            "0 mm",
            "App::PropertyQuantity",
            "Turbulence",
            QT_TRANSLATE_NOOP("App::Property", "Sand-grain roughness"),
        )
        addObjectProperty(
            obj,
            "RoughnessConstant",
            "0.5",
            "App::PropertyQuantity",
            "Turbulence",
            QT_TRANSLATE_NOOP("App::Property", "Coefficient of roughness [0.5-1]"),
        )

        addObjectProperty(
            obj,
            "ThermalBoundaryType",
            THERMAL_BOUNDARY_TYPES,
            "App::PropertyEnumeration",
            "Thermal",
            QT_TRANSLATE_NOOP("App::Property", "Type of thermal boundary"),
        )
        addObjectProperty(
            obj,
            "Temperature",
            "293 K",
            "App::PropertyQuantity",
            "Thermal",
            QT_TRANSLATE_NOOP("App::Property", "Temperature"),
        )
        addObjectProperty(
            obj,
            "HeatFlux",
            "0 W/m^2",
            "App::PropertyQuantity",
            "Thermal",
            QT_TRANSLATE_NOOP("App::Property", "Wall heat flux"),
        )
        addObjectProperty(
            obj,
            "HeatTransferCoeff",
            "0 W/m^2/K",
            "App::PropertyQuantity",
            "Thermal",
            QT_TRANSLATE_NOOP("App::Property", "Wall heat transfer coefficient"),
        )

        # Periodic
        addObjectProperty(
            obj,
            "RotationalPeriodic",
            False,
            "App::PropertyBool",
            "Periodic",
            QT_TRANSLATE_NOOP("App::Property", "Rotational or translational periodicity"),
        )
        addObjectProperty(
            obj,
            "PeriodicCentreOfRotation",
            FreeCAD.Vector(0, 0, 0),
            "App::PropertyPosition",
            "Periodic",
            QT_TRANSLATE_NOOP("App::Property", "Centre of rotation for rotational periodics"),
        )
        addObjectProperty(
            obj,
            "PeriodicCentreOfRotationAxis",
            FreeCAD.Vector(0, 0, 0),
            "App::PropertyVector",
            "Periodic",
            QT_TRANSLATE_NOOP("App::Property", "Axis of rotation for rotational periodics"),
        )
        addObjectProperty(
            obj,
            "PeriodicSeparationVector",
            FreeCAD.Vector(0, 0, 0),
            "App::PropertyPosition",
            "Periodic",
            QT_TRANSLATE_NOOP("App::Property", "Separation vector for translational periodics"),
        )
        addObjectProperty(
            obj,
            "PeriodicPartner",
            "",
            "App::PropertyString",
            "Periodic",
            QT_TRANSLATE_NOOP("App::Property", "Partner patch for the slave periodic"),
        )
        addObjectProperty(
            obj,
            "PeriodicMaster",
            True,
            "App::PropertyBool",
            "Periodic",
            QT_TRANSLATE_NOOP(
                "App::Property", "Whether the current patch is the master or slave patch"
            ),
        )

        # Turbulence
        all_turb_specs = []
        for k in TURBULENT_INLET_SPEC:
            all_turb_specs += TURBULENT_INLET_SPEC[k][1]

        all_turb_specs = list(set(all_turb_specs))  # Remove duplicates

        if addObjectProperty(
            obj,
            "TurbulenceInletSpecification",
            all_turb_specs,
            "App::PropertyEnumeration",
            "Turbulence",
            QT_TRANSLATE_NOOP("App::Property", "Turbulent quantities specified"),
        ):
            obj.TurbulenceInletSpecification = "intensityAndLengthScale"

        # k omega SST
        addObjectProperty(
            obj,
            "TurbulentKineticEnergy",
            "0.01 m^2/s^2",
            "App::PropertyQuantity",
            "Turbulence",
            QT_TRANSLATE_NOOP("App::Property", "Turbulent kinetic energy"),
        )
        addObjectProperty(
            obj,
            "SpecificDissipationRate",
            "1 1/s",
            "App::PropertyQuantity",
            "Turbulence",
            QT_TRANSLATE_NOOP("App::Property", "Specific turbulent dissipation rate"),
        )

        # k epsilon
        addObjectProperty(
            obj,
            "DissipationRate",
            "50 m^2/s^3",
            "App::PropertyQuantity",
            "Turbulence",
            QT_TRANSLATE_NOOP("App::Property", "Turbulent dissipation rate"),
        )

        # Spalart Allmaras
        addObjectProperty(
            obj,
            "NuTilda",
            "55 m^2/s^1",
            "App::PropertyQuantity",
            "Turbulence",
            QT_TRANSLATE_NOOP("App::Property", "Modified turbulent viscosity"),
        )

        # Langtry Menter 4 eqn k omega SST
        addObjectProperty(
            obj,
            "Intermittency",
            "1",
            "App::PropertyQuantity",
            "Turbulence",
            QT_TRANSLATE_NOOP("App::Property", "Turbulent intermittency"),
        )
        addObjectProperty(
            obj,
            "ReThetat",
            "1",
            "App::PropertyQuantity",
            "Turbulence",
            QT_TRANSLATE_NOOP("App::Property", "Transition momentum thickness Reynolds number"),
        )

        # LES models
        addObjectProperty(
            obj,
            "TurbulentViscosity",
            "50 m^2/s^1",
            "App::PropertyQuantity",
            "Turbulence",
            QT_TRANSLATE_NOOP("App::Property", "Turbulent viscosity"),
        )
        addObjectProperty(
            obj,
            "kEqnTurbulentKineticEnergy",
            "0.01 m^2/s^2",
            "App::PropertyQuantity",
            "Turbulence",
            QT_TRANSLATE_NOOP("App::Property", "Turbulent viscosity"),
        )
        addObjectProperty(
            obj,
            "kEqnTurbulentViscosity",
            "50 m^2/s^1",
            "App::PropertyQuantity",
            "Turbulence",
            QT_TRANSLATE_NOOP("App::Property", "Turbulent viscosity"),
        )

        # General
        addObjectProperty(
            obj,
            "TurbulenceIntensityPercentage",
            "1",
            "App::PropertyQuantity",
            "Turbulence",
            QT_TRANSLATE_NOOP("App::Property", "Turbulence intensity (percent)"),
        )
        # Backward compat
        if "TurbulenceIntensity" in obj.PropertiesList:
            obj.TurbulenceIntensityPercentage = obj.TurbulenceIntensity * 100.0
            obj.removeProperty("TurbulenceIntensity")

        addObjectProperty(
            obj,
            "TurbulenceLengthScale",
            "0.1 m",
            "App::PropertyLength",
            "Turbulence",
            QT_TRANSLATE_NOOP("App::Property", "Length scale of turbulent eddies"),
        )
        addObjectProperty(
            obj,
            "VolumeFractions",
            {},
            "App::PropertyMap",
            "Volume fraction",
            QT_TRANSLATE_NOOP("App::Property", "Volume fractions"),
        )

    def onDocumentRestored(self, obj):
        self.initProperties(obj)

    def execute(self, obj):
        """ Create compound part at recompute. """
        shape = CfdTools.makeShapeFromReferences(obj.ShapeRefs, False)
        if shape is None:
            shape = Part.Shape()
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

    # dumps and loads replace __getstate__ and __setstate__ post v. 0.21.2
    def dumps(self):
        return None

    def loads(self, state):
        return None


class _CfdFluidBoundary:
    """ Backward compatibility for old class name when loading from file """
    def onDocumentRestored(self, obj):
        CfdFluidBoundary(obj)

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None

    # dumps and loads replace __getstate__ and __setstate__ post v. 0.21.2
    def dumps(self):
        return None

    def loads(self, state):
        return None


class ViewProviderCfdFluidBoundary:
    def __init__(self, vobj):
        vobj.Proxy = self
        self.taskd = None

    def getIcon(self):
        icon_path = os.path.join(CfdTools.getModulePath(), "Gui", "Icons", "boundary.svg")
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
        if analysis_obj and not analysis_obj.Proxy.loading:
            if prop == 'Shape':
                # Updates to the shape should be taken care of via links in 
                # ShapeRefs
                pass
            elif prop == 'ShapeRefs':
                # Only a change to the shape allocation or geometry affects mesh
                analysis_obj.NeedsMeshRewrite = True
            else:
                # Else mark case itself as needing updating
                analysis_obj.NeedsCaseRewrite = True

    def onChanged(self, vobj, prop):
        #CfdTools.setCompSolid(vobj)
        return

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

        import importlib
        importlib.reload(TaskPanelCfdFluidBoundary)
        self.taskd = TaskPanelCfdFluidBoundary.TaskPanelCfdFluidBoundary(self.Object, physics_model, material_objs)
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

    # dumps and loads replace __getstate__ and __setstate__ post v. 0.21.2
    def dumps(self):
        return None

    def loads(self, state):
        return None


class _ViewProviderCfdFluidBoundary:
    """ Backward compatibility for old class name when loading from file """
    def attach(self, vobj):
        new_proxy = ViewProviderCfdFluidBoundary(vobj)
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
