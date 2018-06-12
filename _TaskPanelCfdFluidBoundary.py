# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2013-2015 - Juergen Riegel <FreeCAD@juergen-riegel.net> *
# *   Copyright (c) 2017 - Oliver Oxtoby <ooxtoby@csir.co.za>               *
# *   Copyright (c) 2017 - Johan Heyns <jheyns@csir.co.za>                  *
# *   Copyright (c) 2017 - Alfred Bogaers <abogaers@csir.co.za>             *
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

__title__ = "_TaskPanelCfdFluidBoundary"
__author__ = "AB, JH, OO"
__url__ = "http://www.freecadweb.org"


import FreeCAD
import os
import sys
import os.path
import CfdTools
from CfdTools import inputCheckAndStore, setInputFieldQuantity, indexOrDefault
import CfdFaceSelectWidget

if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore
    from PySide import QtCore
    from PySide import QtGui
    from PySide.QtCore import Qt, QTimer
    from PySide.QtGui import QApplication
    from PySide import QtUiTools
    from PySide.QtGui import QFormLayout

# Constants

BOUNDARY_NAMES = ["Wall", "Inlet", "Outlet", "Opening", "Far-field", "Constraint", "Baffle"]

BOUNDARY_TYPES = ["wall", "inlet", "outlet", "open", "farField", "constraint", "baffle"]

SUBNAMES = [["No-slip (viscous)", "Slip (inviscid)", "Partial slip", "Translating", "Rough"],
            ["Uniform velocity", "Volumetric flow rate", "Mass flow rate", "Total pressure", "Static pressure"],
            ["Static pressure", "Uniform velocity", "Outflow"],
            ["Ambient pressure"],
            ["Characteristic-based"],
            ["Symmetry", "2D bounding plane"],
            ["Porous Baffle"]]

SUBTYPES = [["fixed", "slip", "partialSlip", "translating", "rough"],
            ["uniformVelocity", "volumetricFlowRate", "massFlowRate", "totalPressure", "staticPressure"],
            ["staticPressure", "uniformVelocity", "outFlow"],
            ["totalPressureOpening"],
            ["characteristic"],
            ["symmetry", "twoDBoundingPlane"],
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
                     ["Static pressure specified for outflow and reverse flow",
                      "Normal component imposed for outflow; velocity fixed for reverse flow",
                      "All fields extrapolated; use with care!"],
                     ["Boundary open to surrounding with total pressure specified"],
                     ["Sub-/supersonic inlet/outlet with prescribed far-field values"],
                     ["Symmetry of flow quantities about boundary face",
                      "Bounding planes for 2D meshing and simulation"],
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
               [[True, [0], True, True, True, True, [2]],  # Velocity
                [True, [3], False, True, True, True, [2]],  # Vol flow rate
                [True, [4], False, True, True, True, [2]],  # Mass Flow rate
                [True, [1], False, True, True, True, [2]],  # Total pressure
                [True, [1], False, True, True, True, [2]]],  # Static pressure
               [[True, [1], False, False, True, False, None],  # Static pressure
                [True, [0], False, False, True, False, None],  # Uniform velocity
                [False, [], False, False, False, False, None]],  # Outflow
               [[True, [1], False, True, True, True, [2]]],  # Opening
               [[True, [0, 1], False, True, False, True, [2]]],  # Far-field
               [[False, [], False, False, False, False, None],  # Symmetry plane
                [False, [], False, False, False, False, None]],  # 2D plane
               [[True, [5], False, False, False, False, None]]]  # Permeable screen

# For each turbulence model: Name, label, help text, displayed rows
TURBULENT_INLET_SPEC = {"kOmegaSST":
                        [["Kinetic Energy & Specific Dissipation Rate",
                          "Intensity & Length Scale"],
                         ["TKEAndSpecDissipationRate",
                          "intensityAndLengthScale"],
                         ["k and omega specified",
                          "Turbulence intensity and eddy length scale"],
                         [[0, 1],  # k, omega
                          [2, 3]]]}  # I, l

THERMAL_BOUNDARY_NAMES = ["Fixed temperature",
                          "Adiabatic",
                          "Fixed conductive heat flux"]

THERMAL_BOUNDARY_TYPES = ["fixedValue", "zeroGradient", "fixedGradient"]

THERMAL_HELPTEXT = ["Fixed Temperature", "No conductive heat transfer", "Fixed conductive heat flux"]

# For each thermal BC, the input rows presented to the user
BOUNDARY_THERMALTAB = [[0], [], [1]]


class TaskPanelCfdFluidBoundary:
    """ Taskpanel for adding fluid boundary """
    def __init__(self, obj, physics_model, material_objs):
        self.selecting_direction = False
        self.obj = obj

        self.physics_model = physics_model
        self.turbModel = (physics_model.TurbulenceModel
                          if physics_model.Turbulence == 'RANS' or physics_model.Turbulence == 'LES'
                          else None)
        self.material_objs = material_objs

        self.BoundarySettings = self.obj.BoundarySettings.copy()

        self.ReferencesOrig = list(self.obj.References)
        self.BoundarySettingsOrig = self.obj.BoundarySettings.copy()

        ui_path = os.path.join(os.path.dirname(__file__), "TaskPanelCfdFluidBoundary.ui")
        self.form = FreeCADGui.PySideUic.loadUi(ui_path)

        self.form.comboBoundaryType.currentIndexChanged.connect(self.comboBoundaryTypeChanged)
        self.form.comboSubtype.currentIndexChanged.connect(self.comboSubtypeChanged)
        self.form.radioButtonCart.toggled.connect(self.radioButtonVelocityToggled)
        self.form.radioButtonMagNormal.toggled.connect(self.radioButtonVelocityToggled)
        self.form.inputCartX.valueChanged.connect(self.inputCartXChanged)
        self.form.inputCartY.valueChanged.connect(self.inputCartYChanged)
        self.form.inputCartZ.valueChanged.connect(self.inputCartZChanged)
        self.form.inputVelocityMag.valueChanged.connect(self.inputVelocityMagChanged)
        self.form.lineDirection.textChanged.connect(self.lineDirectionChanged)
        self.form.buttonDirection.clicked.connect(self.buttonDirectionClicked)
        self.form.buttonDirection.setCheckable(True)
        self.form.checkReverse.toggled.connect(self.checkReverseToggled)
        self.form.inputPressure.valueChanged.connect(self.inputPressureChanged)
        self.form.inputSlipRatio.valueChanged.connect(self.inputSlipRatioChanged)
        self.form.inputVolFlowRate.valueChanged.connect(self.inputVolFlowRateChanged)
        self.form.inputMassFlowRate.valueChanged.connect(self.inputMassFlowRateChanged)
        self.form.buttonGroupPorous.buttonClicked.connect(self.buttonGroupPorousClicked)
        # Annoyingly can't find a way to set ID's for button group from .ui file...
        self.form.buttonGroupPorous.setId(self.form.radioButtonPorousCoeff, 0)
        self.form.buttonGroupPorous.setId(self.form.radioButtonPorousScreen, 1)
        self.form.inputPressureDropCoeff.valueChanged.connect(self.inputPressureDropCoeffChanged)
        self.form.inputWireDiameter.valueChanged.connect(self.inputWireDiameterChanged)
        self.form.inputSpacing.valueChanged.connect(self.inputSpacingChanged)

        self.form.inputTemperature.valueChanged.connect(self.inputTemperatureChanged)
        self.form.inputHeatFlux.valueChanged.connect(self.inputHeatFluxChanged)
        self.form.inputHeatTransferCoeff.valueChanged.connect(self.inputHeatTransferCoeffChanged)

        self.form.comboTurbulenceSpecification.currentIndexChanged.connect(self.comboTurbulenceSpecificationChanged)
        self.form.inputKineticEnergy.valueChanged.connect(self.inputKineticEnergyChanged)
        self.form.inputSpecificDissipationRate.valueChanged.connect(self.inputSpecificDissipationRateChanged)
        self.form.inputIntensity.valueChanged.connect(self.inputIntensityChanged)
        self.form.inputLengthScale.valueChanged.connect(self.inputLengthScaleChanged)

        self.form.comboFluid.currentIndexChanged.connect(self.comboFluidChanged)
        self.form.inputVolumeFraction.valueChanged.connect(self.inputVolumeFractionChanged)

        self.form.comboThermalBoundaryType.currentIndexChanged.connect(self.comboThermalBoundaryTypeChanged)

        self.setInitialValues()

        # Face list selection panel - modifies obj.References passed to it
        self.faceSelector = CfdFaceSelectWidget.CfdFaceSelectWidget(self.form.faceSelectWidget,
                                                                    self.obj, True)

    def setInitialValues(self):
        """ Populate UI """
        self.form.comboBoundaryType.addItems(BOUNDARY_NAMES)
        bi = indexOrDefault(BOUNDARY_TYPES, self.BoundarySettingsOrig.get('BoundaryType'), 0)
        self.form.comboBoundaryType.setCurrentIndex(bi)
        si = indexOrDefault(SUBTYPES[bi], self.BoundarySettingsOrig.get('BoundarySubtype'), 0)
        self.form.comboSubtype.setCurrentIndex(si)

        cart = self.BoundarySettings.get('VelocityIsCartesian', False)
        self.form.radioButtonCart.setChecked(cart)
        self.form.radioButtonMagNormal.setChecked(not cart)
        setInputFieldQuantity(self.form.inputCartX, str(self.BoundarySettings.get('Ux'))+"m/s")
        setInputFieldQuantity(self.form.inputCartY, str(self.BoundarySettings.get('Uy'))+"m/s")
        setInputFieldQuantity(self.form.inputCartZ, str(self.BoundarySettings.get('Uz'))+"m/s")
        setInputFieldQuantity(self.form.inputVelocityMag, str(self.BoundarySettings.get('VelocityMag'))+"m/s")
        self.form.lineDirection.setText(self.BoundarySettings.get('DirectionFace'))
        self.form.checkReverse.setChecked(bool(self.BoundarySettings.get('ReverseNormal')))
        setInputFieldQuantity(self.form.inputPressure, str(self.BoundarySettings.get('Pressure'))+"kg/m/s^2")
        setInputFieldQuantity(self.form.inputSlipRatio, str(self.BoundarySettings.get('SlipRatio')))
        setInputFieldQuantity(self.form.inputVolFlowRate, str(self.BoundarySettings.get('VolFlowRate'))+"m^3/s")
        setInputFieldQuantity(self.form.inputMassFlowRate, str(self.BoundarySettings.get('MassFlowRate'))+"kg/s")

        buttonId = self.BoundarySettings.get('PorousBaffleMethod', 0)
        selButton = self.form.buttonGroupPorous.button(buttonId)
        if selButton is not None:
            selButton.setChecked(True)
            self.buttonGroupPorousClicked(selButton)  # Signal is not generated on setChecked above
        setInputFieldQuantity(self.form.inputPressureDropCoeff, str(self.BoundarySettings.get('PressureDropCoeff')))
        setInputFieldQuantity(self.form.inputWireDiameter, str(self.BoundarySettings.get('ScreenWireDiameter'))+"m")
        setInputFieldQuantity(self.form.inputSpacing, str(self.BoundarySettings.get('ScreenSpacing'))+"m")

        self.form.comboThermalBoundaryType.addItems(THERMAL_BOUNDARY_NAMES)
        thi = indexOrDefault(THERMAL_BOUNDARY_TYPES, self.BoundarySettings.get('ThermalBoundaryType'), 0)
        self.form.comboThermalBoundaryType.setCurrentIndex(thi)
        setInputFieldQuantity(self.form.inputTemperature, str(self.BoundarySettings.get('Temperature', 273.0))+"K")
        setInputFieldQuantity(self.form.inputHeatFlux, str(self.BoundarySettings.get('HeatFlux', 0.0))+"W/m^2")
        setInputFieldQuantity(self.form.inputHeatTransferCoeff, str(self.BoundarySettings.get('HeatTransferCoeff', 0.0))+"W/m^2/K")

        if self.turbModel is not None:
            self.form.comboTurbulenceSpecification.addItems(TURBULENT_INLET_SPEC[self.turbModel][0])
            ti = indexOrDefault(TURBULENT_INLET_SPEC[self.turbModel][1],
                                self.BoundarySettingsOrig.get('TurbulenceInletSpecification'), 0)
            self.form.comboTurbulenceSpecification.setCurrentIndex(ti)

        # Add volume fraction fields
        if len(self.material_objs) > 1:
            mat_names = []
            for m in self.material_objs:
                mat_names.append(m.Label)
            self.form.comboFluid.clear()
            self.form.comboFluid.addItems(mat_names[:-1])
        else:
            self.form.comboFluid.clear()

        setInputFieldQuantity(self.form.inputKineticEnergy,
                              str(self.BoundarySettings.get('TurbulentKineticEnergy'))+"m^2/s^2")
        setInputFieldQuantity(self.form.inputSpecificDissipationRate,
                              str(self.BoundarySettings.get('SpecificDissipationRate'))+"rad/s")
        setInputFieldQuantity(self.form.inputIntensity, str(self.BoundarySettings.get('TurbulenceIntensity')))
        setInputFieldQuantity(self.form.inputLengthScale, str(self.BoundarySettings.get('TurbulenceLengthScale'))+"m")

    def comboBoundaryTypeChanged(self):
        index = self.form.comboBoundaryType.currentIndex()
        self.form.comboSubtype.clear()
        self.form.comboSubtype.addItems(SUBNAMES[index])
        self.form.comboSubtype.setCurrentIndex(0)
        self.BoundarySettings['BoundaryType'] = BOUNDARY_TYPES[self.form.comboBoundaryType.currentIndex()]

        # Change the color of the boundary condition as the selection is made
        self.obj.BoundarySettings = self.BoundarySettings.copy()
        doc_name = str(self.obj.Document.Name)
        FreeCAD.getDocument(doc_name).recompute()

    def comboSubtypeChanged(self):
        type_index = self.form.comboBoundaryType.currentIndex()
        subtype_index = self.form.comboSubtype.currentIndex()
        self.form.labelBoundaryDescription.setText(SUBTYPES_HELPTEXT[type_index][subtype_index])
        self.BoundarySettings['BoundarySubtype'] = SUBTYPES[type_index][self.form.comboSubtype.currentIndex()]
        self.updateBoundaryTypeUi()

    def updateBoundaryTypeUi(self):
        type_index = self.form.comboBoundaryType.currentIndex()
        subtype_index = self.form.comboSubtype.currentIndex()
        tab_enabled = BOUNDARY_UI[type_index][subtype_index][0]
        self.form.basicFrame.setVisible(tab_enabled)
        for paneli in range(self.form.layoutBasicValues.count()):
            if isinstance(self.form.layoutBasicValues.itemAt(paneli), QtGui.QWidgetItem):
                self.form.layoutBasicValues.itemAt(paneli).widget().setVisible(False)
        if tab_enabled:
            panel_numbers = BOUNDARY_UI[type_index][subtype_index][1]
            for panel_number in panel_numbers:
                self.form.layoutBasicValues.itemAt(panel_number).widget().setVisible(True)
                if panel_number == 0:
                    reverse = BOUNDARY_UI[type_index][subtype_index][2]
                    # If user hasn't set a patch yet, initialise 'reverse' to default
                    if self.form.lineDirection.text() == "":
                        self.form.checkReverse.setChecked(reverse)
        turb_enabled = BOUNDARY_UI[type_index][subtype_index][3]
        self.form.turbulenceFrame.setVisible(turb_enabled and self.turbModel is not None)
        alpha_enabled = BOUNDARY_UI[type_index][subtype_index][4]
        self.form.volumeFractionsFrame.setVisible(alpha_enabled and len(self.material_objs) > 1)
        if self.physics_model.Thermal != 'None' and BOUNDARY_UI[type_index][subtype_index][5]:
            self.form.thermalFrame.setVisible(True)
            selected_rows = BOUNDARY_UI[type_index][subtype_index][6]
            if selected_rows:
                for rowi in range(self.form.layoutThermal.count()):
                    for role in [QFormLayout.LabelRole, QFormLayout.FieldRole, QFormLayout.SpanningRole]:
                        item = self.form.layoutThermal.itemAt(rowi, role)
                        if item:
                            if isinstance(item, QtGui.QWidgetItem):
                                item.widget().setVisible(False)
                for row_enabled in selected_rows:
                    for role in [QFormLayout.LabelRole, QFormLayout.FieldRole, QFormLayout.SpanningRole]:
                        item = self.form.layoutThermal.itemAt(row_enabled, role)
                        if item:
                            item.widget().setVisible(True)
        else:
            self.form.thermalFrame.setVisible(False)

    def updateSelectionbuttonUI(self):
        self.form.buttonDirection.setChecked(self.selecting_direction)

    def radioButtonVelocityToggled(self, checked):
        self.BoundarySettings['VelocityIsCartesian'] = self.form.radioButtonCart.isChecked()
        self.form.frameCart.setVisible(self.form.radioButtonCart.isChecked())
        self.form.frameMagNormal.setVisible(self.form.radioButtonMagNormal.isChecked())

    def buttonDirectionClicked(self):
        self.selecting_direction = not self.selecting_direction
        if self.selecting_direction:
            # If one object already selected, use it
            sels = FreeCADGui.Selection.getSelectionEx()
            if len(sels) == 1:
                sel = sels[0]
                if sel.HasSubObjects:
                    if len(sel.SubElementNames) == 1:
                        sub = sel.SubElementNames[0]
                        self.directionSelection(sel.DocumentName, sel.ObjectName, sub)
        FreeCADGui.Selection.clearSelection()
        # start SelectionObserver and parse the function to add the References to the widget
        if self.selecting_direction:
            FreeCAD.Console.PrintMessage("Select face to define direction\n")
            FreeCADGui.Selection.addObserver(self)
        else:
            FreeCADGui.Selection.removeObserver(self)
        self.updateSelectionbuttonUI()

    def addSelection(self, doc_name, obj_name, sub, selectedPoint=None):
        # This is the direction selection
        if not self.selecting_direction:
            # Shouldn't be here
            pass
        if FreeCADGui.activeDocument().Document.Name != self.obj.Document.Name:
            return
        selected_object = FreeCAD.getDocument(doc_name).getObject(obj_name)
        # On double click on a vertex of a solid sub is None and obj is the solid
        print('Selection: ' +
              selected_object.Shape.ShapeType + '  ' +
              selected_object.Name + ':' +
              sub + " @ " + str(selectedPoint))
        if hasattr(selected_object, "Shape") and sub:
            elt = selected_object.Shape.getElement(sub)
            if elt.ShapeType == 'Face':
                selection = (selected_object.Name, sub)
                if self.selecting_direction:
                    if CfdTools.is_planar(elt):
                        self.selecting_direction = False
                        self.form.lineDirection.setText(selection[0] + ':' + selection[1])  # TODO: Display label, not name
                    else:
                        FreeCAD.Console.PrintMessage('Face must be planar\n')

    def inputCartXChanged(self, value):
        inputCheckAndStore(value, "m/s", self.BoundarySettings, 'Ux')

    def inputCartYChanged(self, value):
        inputCheckAndStore(value, "m/s", self.BoundarySettings, 'Uy')

    def inputCartZChanged(self, value):
        inputCheckAndStore(value, "m/s", self.BoundarySettings, 'Uz')

    def inputVelocityMagChanged(self, value):
        inputCheckAndStore(value, "m/s", self.BoundarySettings, 'VelocityMag')

    def lineDirectionChanged(self, value):
        selection = value.split(':')
        # See if entered face actually exists and is planar
        try:
            selected_object = self.obj.Document.getObject(selection[0])
            if hasattr(selected_object, "Shape"):
                elt = selected_object.Shape.getElement(selection[1])
                if elt.ShapeType == 'Face' and CfdTools.is_planar(elt):
                    self.BoundarySettings['DirectionFace'] = value
                    return
        except SystemError:
            pass
        FreeCAD.Console.PrintMessage(value + " is not a valid, planar face\n")

    def checkReverseToggled(self, checked):
        self.BoundarySettings['ReverseNormal'] = checked

    def inputPressureChanged(self, value):
        inputCheckAndStore(value, "kg/m/s^2", self.BoundarySettings, 'Pressure')

    def inputSlipRatioChanged(self, value):
        inputCheckAndStore(value, "m/m", self.BoundarySettings, 'SlipRatio')

    def inputVolFlowRateChanged(self, value):
        inputCheckAndStore(value, "m^3/s", self.BoundarySettings, 'VolFlowRate')

    def inputMassFlowRateChanged(self, value):
        inputCheckAndStore(value, "kg/s", self.BoundarySettings, 'MassFlowRate')

    def buttonGroupPorousClicked(self, button):
        method = self.form.buttonGroupPorous.checkedId()
        self.BoundarySettings['PorousBaffleMethod'] = method
        self.form.stackedWidgetPorous.setCurrentIndex(method)

    def inputPressureDropCoeffChanged(self, value):
        inputCheckAndStore(value, "m/m", self.BoundarySettings, 'PressureDropCoeff')

    def inputWireDiameterChanged(self, value):
        inputCheckAndStore(value, "m", self.BoundarySettings, 'ScreenWireDiameter')

    def inputSpacingChanged(self, value):
        inputCheckAndStore(value, "m", self.BoundarySettings, 'ScreenSpacing')

    def inputTemperatureChanged(self, value):
        inputCheckAndStore(value, "K", self.BoundarySettings, 'Temperature')

    def inputHeatFluxChanged(self, value):
        inputCheckAndStore(value, "W/m^2", self.BoundarySettings, 'HeatFlux')

    def inputHeatTransferCoeffChanged(self, value):
        inputCheckAndStore(value, "W/m^2/K", self.BoundarySettings, 'HeatTransferCoeff')

    def comboTurbulenceSpecificationChanged(self, index):
        self.form.labelTurbulenceDescription.setText(TURBULENT_INLET_SPEC[self.turbModel][2][index])
        self.BoundarySettings['TurbulenceInletSpecification'] = TURBULENT_INLET_SPEC[self.turbModel][1][index]
        self.updateTurbulenceUi()

    def inputKineticEnergyChanged(self, value):
        inputCheckAndStore(value, "m^2/s^2", self.BoundarySettings, 'TurbulentKineticEnergy')

    def inputSpecificDissipationRateChanged(self, value):
        inputCheckAndStore(value, "rad/s", self.BoundarySettings, 'SpecificDissipationRate')

    def inputIntensityChanged(self, value):
        inputCheckAndStore(value, "m/m", self.BoundarySettings, 'TurbulenceIntensity')

    def inputLengthScaleChanged(self, value):
        inputCheckAndStore(value, "m", self.BoundarySettings, 'TurbulenceLengthScale')

    def updateTurbulenceUi(self):
        index = self.form.comboTurbulenceSpecification.currentIndex()
        panel_numbers = TURBULENT_INLET_SPEC[self.turbModel][3][index]
        # Enables specified rows of a QFormLayout
        for rowi in range(self.form.layoutTurbulenceValues.count()):
            for role in [QFormLayout.LabelRole, QFormLayout.FieldRole, QFormLayout.SpanningRole]:
                item = self.form.layoutTurbulenceValues.itemAt(rowi, role)
                if isinstance(item, QtGui.QWidgetItem):
                    item.widget().setVisible(rowi in panel_numbers)

    def getMaterialName(self, index):
        return self.material_objs[index].Label

    def comboFluidChanged(self, index):
        if 'alphas' not in self.BoundarySettings:
            self.BoundarySettings['alphas'] = {}
        setInputFieldQuantity(self.form.inputVolumeFraction,
                              str(self.BoundarySettings['alphas'].get(self.getMaterialName(index), 0.0)))

    def inputVolumeFractionChanged(self, value):
        inputCheckAndStore(value, "m/m", self.BoundarySettings['alphas'], self.form.comboFluid.currentText())

    def comboThermalBoundaryTypeChanged(self, index):
        self.form.labelThermalDescription.setText(THERMAL_HELPTEXT[index])
        self.BoundarySettings['ThermalBoundaryType'] = THERMAL_BOUNDARY_TYPES[index]
        self.updateThermalUi()

    def updateThermalUi(self):
        index = self.form.comboThermalBoundaryType.currentIndex()
        panel_numbers = BOUNDARY_THERMALTAB[index]
        # Enables specified rows of a QFormLayout
        for rowi in range(2, self.form.layoutThermal.count()):  # Input values only start at row 2 of this form
            for role in [QFormLayout.LabelRole, QFormLayout.FieldRole, QFormLayout.SpanningRole]:
                item = self.form.layoutThermal.itemAt(rowi, role)
                if isinstance(item, QtGui.QWidgetItem):
                    item.widget().setVisible(rowi-2 in panel_numbers)

    def accept(self):
        if "CfdFluidBoundary" in self.obj.Label:
            self.obj.Label = self.obj.BoundarySettings['BoundaryType']
        FreeCADGui.Selection.removeObserver(self)
        self.obj.BoundarySettings = self.BoundarySettings.copy()
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc_name = str(self.obj.Document.Name)
        FreeCAD.getDocument(doc_name).recompute()
        doc.resetEdit()

        FreeCADGui.doCommand("\n# Values are converted to SI units and stored (eg. m/s)")
        FreeCADGui.doCommand("bc = FreeCAD.ActiveDocument.{}.BoundarySettings".format(self.obj.Name))
        # Type
        FreeCADGui.doCommand("bc['BoundaryType'] "
                             "= '{}'".format(self.BoundarySettings['BoundaryType']))
        FreeCADGui.doCommand("bc['BoundarySubtype'] "
                             "= '{}'".format(self.BoundarySettings['BoundarySubtype']))
        FreeCADGui.doCommand("bc['ThermalBoundaryType'] "
                             "= '{}'".format(self.BoundarySettings['ThermalBoundaryType']))
        # Velocity
        FreeCADGui.doCommand("bc['VelocityIsCartesian'] "
                             "= {}".format(self.BoundarySettings['VelocityIsCartesian']))
        FreeCADGui.doCommand("bc['Ux'] "
                             "= {}".format(self.BoundarySettings['Ux']))
        FreeCADGui.doCommand("bc['Uy'] "
                             "= {}".format(self.BoundarySettings['Uy']))
        FreeCADGui.doCommand("bc['Uz'] "
                             "= {}".format(self.BoundarySettings['Uz']))
        FreeCADGui.doCommand("bc['VelocityMag'] "
                             "= {}".format(self.BoundarySettings['VelocityMag']))
        FreeCADGui.doCommand("bc['DirectionFace'] "
                             "= '{}'".format(self.BoundarySettings['DirectionFace']))
        FreeCADGui.doCommand("bc['ReverseNormal'] "
                             "= {}".format(self.BoundarySettings['ReverseNormal']))
        FreeCADGui.doCommand("bc['MassFlowRate'] "
                             "= {}".format(self.BoundarySettings['MassFlowRate']))
        FreeCADGui.doCommand("bc['VolFlowRate'] "
                             "= {}".format(self.BoundarySettings['VolFlowRate']))
        # Presure
        FreeCADGui.doCommand("bc['Pressure'] "
                             "= {}".format(self.BoundarySettings['Pressure']))
        # Wall
        FreeCADGui.doCommand("bc['SlipRatio'] "
                             "= {}".format(self.BoundarySettings['SlipRatio']))
        # Thermal
        FreeCADGui.doCommand("bc['Temperature'] "
                             "= {}".format(self.BoundarySettings['Temperature']))
        FreeCADGui.doCommand("bc['HeatFlux'] "
                             "= {}".format(self.BoundarySettings['HeatFlux']))
        FreeCADGui.doCommand("bc['HeatTransferCoeff'] "
                             "= {}".format(self.BoundarySettings['HeatTransferCoeff']))

        # Turbulence
        FreeCADGui.doCommand("bc['TurbulenceInletSpecification'] "
                             "= '{}'".format(self.BoundarySettings['TurbulenceInletSpecification']))
        FreeCADGui.doCommand("bc['TurbulentKineticEnergy'] "
                             "= {}".format(self.BoundarySettings['TurbulentKineticEnergy']))
        FreeCADGui.doCommand("bc['SpecificDissipationRate'] "
                             "= {}".format(self.BoundarySettings['SpecificDissipationRate']))
        FreeCADGui.doCommand("bc['TurbulenceIntensity'] "
                             "= {}".format(self.BoundarySettings['TurbulenceIntensity']))
        FreeCADGui.doCommand("bc['TurbulenceLengthScale'] "
                             "= {}".format(self.BoundarySettings['TurbulenceLengthScale']))
        # Volume fraction
        if len(self.material_objs) > 1:
            for i in range(len(self.material_objs)-1):
                alphaName = self.getMaterialName(i)
                FreeCADGui.doCommand("bc['alphas']['{}'] = {}".format(
                    alphaName, self.BoundarySettings['alphas'].get(alphaName, 0.0)))

        # Porous
        FreeCADGui.doCommand("bc['PressureDropCoeff'] "
                             "= {}".format(self.BoundarySettings['PressureDropCoeff']))
        FreeCADGui.doCommand("bc['ScreenWireDiameter'] "
                             "= {}".format(self.BoundarySettings['ScreenWireDiameter']))
        FreeCADGui.doCommand("bc['ScreenSpacing'] "
                             "= {}".format(self.BoundarySettings['ScreenSpacing']))
        FreeCADGui.doCommand("bc['PorousBaffleMethod'] "
                             "= {}".format(self.BoundarySettings['PorousBaffleMethod']))
        FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.BoundarySettings = bc".format(self.obj.Name))
        FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.Label = '{}'".format(self.obj.Name, self.obj.Label))
        faces = []
        for ref in self.obj.References:
            faces.append(ref)
        self.obj.References = []
        FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.References = []".format(self.obj.Name))
        for f in faces:
            FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.References.append({})".format(self.obj.Name, f))
        FreeCADGui.doCommand("FreeCAD.ActiveDocument.recompute()")

    def reject(self):
        self.obj.References = self.ReferencesOrig
        self.obj.BoundarySettings = self.BoundarySettingsOrig.copy()
        FreeCADGui.Selection.removeObserver(self)
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc_name = str(self.obj.Document.Name)
        FreeCAD.getDocument(doc_name).recompute()
        doc.resetEdit()
        return True
