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

if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore
    from PySide import QtCore
    from PySide import QtGui
    from PySide.QtCore import Qt
    from PySide.QtGui import QApplication
    from PySide import QtUiTools
    import FemGui

# Constants

BOUNDARY_NAMES = ["Wall", "Inlet", "Outlet", "Opening", "Constraint", "Baffle"]

BOUNDARY_TYPES = ["wall", "inlet", "outlet", "open", "constraint", "baffle"]

SUBNAMES = [["No-slip (viscous)", "Slip (inviscid)", "Partial slip", "Translating", "Rough"],
            ["Uniform velocity", "Volumetric flow rate", "Mass flow rate", "Total pressure", "Static pressure"],
            ["Static pressure", "Uniform velocity", "Outflow"],
            ["Ambient pressure"],
            ["Symmetry"],
            ["Porous Baffle"]]

SUBTYPES = [["fixed", "slip", "partialSlip", "translating", "rough"],
            ["uniformVelocity", "volumetricFlowRate", "massFlowRate", "totalPressure", "staticPressure"],
            ["staticPressure", "uniformVelocity", "outFlow"],
            ["totalPressureOpening"],
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
                     ["Static pressure specified for outflow and reverse flow",
                      "Normal component imposed for outflow; velocity fixed for reverse flow",
                      "All fields extrapolated; use with care!"],
                     ["Boundary open to surrounding with total pressure specified"],
                     ["Symmetry of flow quantities about boundary face"],
                     ["Permeable screen"]]

# For each sub-type, whether the basic tab is enabled, the panel number to show (ignored if false), whether
# direction reversal is checked by default (only used for panel 0), whether turbulent inlet panel is shown
BOUNDARY_UI = [[[False, 0, False, False],  # No slip
                [False, 0, False, False],  # Slip
                [True, 2, False, False],  # Partial slip
                [True, 0, False, False],  # Translating wall
                [True, 0, False, False]],  # Rough
               [[True, 0, True, True],  # Velocity
                [True, 3, False, True],  # Vol flow rate
                [True, 4, False, True],  # Mass Flow rate
                [True, 1, False, True],  # Total pressure
                [True, 1, False, True]],  # Static pressure
               [[True, 1, False, False],  # Static pressure
                [True, 0, False, False],  # Uniform velocity
                [False, 0, False, False]],  # Outflow
               [[True, 1, False, True]],  # Opening
               [[False, 0, False, False]],  # Symmetry plane
               [[True, 5, False, False]]]  # Permeable screen

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

THERMAL_BOUNDARY_NAMES = ["Fixed Temperature",
                          "Adiabatic",
                          "Fixed Gradient",
                          "Mixed",
                          "Heat-transfer coefficient",
                          "Coupled"]

THERMAL_BOUNDARY_TYPES = ["fixedValue", "zeroGradient", "fixedGradient", "mixed", "HTC", "coupled"]

THERMAL_HELPTEXT = ["Fixed Temperature", "No heat transfer on boundary", "Fixed value gradient",
                    "Mixed fixedGradient and fixedValue", "Fixed heat flux", "Heat transfer coefficient",
                    "Conjugate heat transfer with solid"]

# For each thermal BC, the input rows presented to the user
BOUNDARY_THERMALTAB = [[0], [], [1], [0, 1], [2], []]


class TaskPanelCfdFluidBoundary:
    """ Taskpanel for adding fluid boundary """
    def __init__(self, obj, physics_model):
        self.selecting_references = False
        self.selecting_direction = False
        self.obj = obj
        self.physics_model = physics_model
        self.turbModel = (physics_model['TurbulenceModel']
                          if physics_model['Turbulence'] == 'RANS' or physics_model['Turbulence'] == 'LES'
                          else None)

        self.References = list(self.obj.References)
        self.BoundarySettings = self.obj.BoundarySettings.copy()

        self.ReferencesOrig = list(self.obj.References)
        self.BoundarySettingsOrig = self.obj.BoundarySettings.copy()

        self.faceList = list(self.obj.faceList)

        ui_path = os.path.join(os.path.dirname(__file__), "TaskPanelCfdFluidBoundary.ui")
        self.form = FreeCADGui.PySideUic.loadUi(ui_path)

        self.form.comboBoundaryType.currentIndexChanged.connect(self.comboBoundaryTypeChanged)
        self.form.comboSubtype.currentIndexChanged.connect(self.comboSubtypeChanged)
        self.form.listReferences.itemPressed.connect(self.setSelection)
        self.form.buttonAddFace.clicked.connect(self.buttonAddFaceClicked)
        self.form.buttonAddFace.setCheckable(True)
        self.form.buttonRemoveFace.clicked.connect(self.buttonRemoveFaceClicked)
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

        self.form.comboTurbulenceSpecification.currentIndexChanged.connect(self.comboTurbulenceSpecificationChanged)
        self.form.inputKineticEnergy.valueChanged.connect(self.inputKineticEnergyChanged)
        self.form.inputSpecificDissipationRate.valueChanged.connect(self.inputSpecificDissipationRateChanged)
        self.form.inputIntensity.valueChanged.connect(self.inputIntensityChanged)
        self.form.inputLengthScale.valueChanged.connect(self.inputLengthScaleChanged)

        self.form.comboThermalBoundaryType.currentIndexChanged.connect(self.comboThermalBoundaryTypeChanged)
        # self.form.thermalFrame.setVisible(physics_model["Thermal"] is not None)
        self.form.thermalFrame.setVisible(False)

        self.form.faceList.clicked.connect(self.faceListSelection)
        self.form.closeListOfFaces.clicked.connect(self.closeFaceList)
        self.form.shapeComboBox.currentIndexChanged.connect(self.faceListShapeChosen)
        self.form.faceListWidget.itemSelectionChanged.connect(self.faceHighlightChange)
        self.form.addFaceListFace.clicked.connect(self.addFaceListFace)
        self.form.shapeComboBox.setToolTip("Choose a solid object from the drop down list and select one or more of the faces associated with the chosen solid.")

        self.setInitialValues()

    def setInitialValues(self):
        """ Populate UI """
        self.form.comboBoundaryType.addItems(BOUNDARY_NAMES)
        bi = indexOrDefault(BOUNDARY_TYPES, self.BoundarySettingsOrig.get('BoundaryType'), 0)
        self.form.comboBoundaryType.setCurrentIndex(bi)
        si = indexOrDefault(SUBTYPES[bi], self.BoundarySettingsOrig.get('BoundarySubtype'), 0)
        self.form.comboSubtype.setCurrentIndex(si)
        self.rebuild_list_references()

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

        if self.turbModel is not None:
            self.form.comboTurbulenceSpecification.addItems(TURBULENT_INLET_SPEC[self.turbModel][0])
            ti = indexOrDefault(TURBULENT_INLET_SPEC[self.turbModel][1],
                                self.BoundarySettingsOrig.get('TurbulenceInletSpecification'), 0)
            self.form.comboTurbulenceSpecification.setCurrentIndex(ti)

        self.form.comboThermalBoundaryType.addItems(THERMAL_BOUNDARY_NAMES)
        thi = indexOrDefault(THERMAL_BOUNDARY_TYPES, self.BoundarySettings.get('ThermalBoundaryType'), 0)
        self.form.comboThermalBoundaryType.setCurrentIndex(thi)
        setInputFieldQuantity(self.form.inputKineticEnergy,
                              str(self.BoundarySettings.get('TurbulentKineticEnergy'))+"m^2/s^2")
        setInputFieldQuantity(self.form.inputSpecificDissipationRate,
                              str(self.BoundarySettings.get('SpecificDissipationRate'))+"rad/s")
        setInputFieldQuantity(self.form.inputIntensity, str(self.BoundarySettings.get('TurbulenceIntensity')))
        setInputFieldQuantity(self.form.inputLengthScale, str(self.BoundarySettings.get('TurbulenceLengthScale'))+"m")

        # First time, add any currently selected faces to list
        if len(self.obj.References) == 0:
            self.selecting_references = True
            self.add_selection_to_ref_list()
            self.selecting_references = False
            FreeCADGui.Selection.clearSelection()
            self.update_selectionbuttons_ui()

    def setSelection(self, value):
        FreeCADGui.Selection.clearSelection()
        docName = str(self.obj.Document.Name)
        doc = FreeCAD.getDocument(docName)
        ref = self.obj.References[self.form.listReferences.row(value)]
        selection_object = doc.getObject(ref[0])
        FreeCADGui.Selection.addSelection(selection_object, [str(ref[1])])

    def add_selection_to_ref_list(self):
        """ Add currently selected objects to reference list. """
        for sel in FreeCADGui.Selection.getSelectionEx():
            if sel.HasSubObjects:
                for sub in sel.SubElementNames:
                    self.addSelection(sel.DocumentName, sel.ObjectName, sub)

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
            panel_number = BOUNDARY_UI[type_index][subtype_index][1]
            self.form.layoutBasicValues.itemAt(panel_number).widget().setVisible(True)
            if panel_number == 0:
                reverse = BOUNDARY_UI[type_index][subtype_index][2]
                # If user hasn't set a patch yet, initialise 'reverse' to default
                if self.form.lineDirection.text() == "":
                    self.form.checkReverse.setChecked(reverse)
        turb_enabled = BOUNDARY_UI[type_index][subtype_index][3]
        self.form.turbulenceFrame.setVisible(turb_enabled and self.turbModel is not None)

    def buttonAddFaceClicked(self):
        self.selecting_direction = False
        self.selecting_references = not self.selecting_references
        if self.selecting_references:
            # Add any currently selected objects
            if len(FreeCADGui.Selection.getSelectionEx()) >= 1:
                self.add_selection_to_ref_list()
                self.selecting_references = False
        FreeCADGui.Selection.clearSelection()
        # start SelectionObserver and parse the function to add the References to the widget
        if self.selecting_references:
            self.form.labelHelpText.setText("Select face(s) to add to list")
            FreeCADGui.Selection.addObserver(self)
        else:
            self.form.labelHelpText.setText("")
            FreeCADGui.Selection.removeObserver(self)
        doc_name = str(self.obj.Document.Name)
        FreeCAD.getDocument(doc_name).recompute()
        self.update_selectionbuttons_ui()

    def buttonRemoveFaceClicked(self):
        if not self.obj.References:
            return
        current_item_name = str(self.form.listReferences.currentItem().text())
        tempList = list(self.obj.References)
        for ref in self.obj.References:
            refname = ref[0] + ':' + ref[1]
            if refname == current_item_name:
                tempList.remove(ref)
        self.obj.References = tempList
        self.rebuild_list_references()
        doc_name = str(self.obj.Document.Name)
        FreeCAD.getDocument(doc_name).recompute()
        FreeCADGui.Selection.clearSelection()

    def update_selectionbuttons_ui(self):
        self.form.buttonDirection.setChecked(self.selecting_direction)
        self.form.buttonAddFace.setChecked(self.selecting_references)

    def radioButtonVelocityToggled(self, checked):
        self.BoundarySettings['VelocityIsCartesian'] = self.form.radioButtonCart.isChecked()
        self.form.frameCart.setVisible(self.form.radioButtonCart.isChecked())
        self.form.frameMagNormal.setVisible(self.form.radioButtonMagNormal.isChecked())

    def buttonDirectionClicked(self):
        self.selecting_references = False
        self.selecting_direction = not self.selecting_direction
        if self.selecting_direction:
            # If one object selected, use it
            sels = FreeCADGui.Selection.getSelectionEx()
            if len(sels) == 1:
                sel = sels[0]
                if sel.HasSubObjects:
                    if len(sel.SubElementNames) == 1:
                        sub = sel.SubElementNames[0]
                        self.addSelection(sel.DocumentName, sel.ObjectName, sub)
        FreeCADGui.Selection.clearSelection()
        # start SelectionObserver and parse the function to add the References to the widget
        if self.selecting_direction:
            FreeCAD.Console.PrintMessage("Select face to define direction\n")
            FreeCADGui.Selection.addObserver(self)
        else:
            FreeCADGui.Selection.removeObserver(self)
        self.update_selectionbuttons_ui()

    def addSelection(self, doc_name, obj_name, sub, selectedPoint=None):
        """ Add the selected sub-element (face) of the part to the Reference list. Prevent selection in other
        document.
        """
        if FreeCADGui.activeDocument().Document.Name != self.obj.Document.Name:
            return
        selected_object = FreeCAD.getDocument(doc_name).getObject(obj_name)
        # On double click on a vertex of a solid sub is None and obj is the solid
        tempList = list(self.obj.References)
        print('Selection: ' +
              selected_object.Shape.ShapeType + '  ' +
              selected_object.Name + ':' +
              sub + " @ " + str(selectedPoint))
        if hasattr(selected_object, "Shape") and sub:
            elt = selected_object.Shape.getElement(sub)
            if elt.ShapeType == 'Face':
                selection = (selected_object.Name, sub)
                if self.selecting_references:
                    if selection not in self.obj.References:
                        tempList.append(selection)
                        # If the user hasn't picked anything for direction the selected face is used as default.
                        if self.form.lineDirection.text() == "":
                            self.form.lineDirection.setText(selection[0] + ':' + selection[1])
                    else:
                        FreeCAD.Console.PrintMessage(
                            selection[0] + ':' + selection[1] + ' already in reference list\n')
                if self.selecting_direction:
                    if CfdTools.is_planar(elt):
                        self.form.lineDirection.setText(selection[0] + ':' + selection[1])
                        self.selecting_direction = False
                    else:
                        FreeCAD.Console.PrintMessage('Face must be planar\n')
        self.obj.References = list(tempList)
        self.rebuild_list_references()
        self.update_selectionbuttons_ui()

        doc_name = str(self.obj.Document.Name)
        FreeCAD.getDocument(doc_name).recompute()

    def rebuild_list_references(self):
        self.form.listReferences.clear()
        items = []
        for ref in self.obj.References:
            item_name = ref[0] + ':' + ref[1]
            items.append(item_name)
        for listItemName in sorted(items):
            self.form.listReferences.addItem(listItemName)

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
        from PySide.QtGui import QFormLayout
        for rowi in range(self.form.layoutTurbulenceValues.rowCount()):
            for role in [QFormLayout.LabelRole, QFormLayout.FieldRole, QFormLayout.SpanningRole]:
                item = self.form.layoutTurbulenceValues.itemAt(rowi, role)
                if isinstance(item, QtGui.QWidgetItem):
                    item.widget().setVisible(rowi in panel_numbers)

    def comboThermalBoundaryTypeChanged(self, index):
        self.form.labelThermalDescription.setText(THERMAL_HELPTEXT[index])
        self.BoundarySettings['ThermalBoundaryType'] = THERMAL_BOUNDARY_TYPES[index]
        self.update_thermal_ui()

    def update_thermal_ui(self):
        index = self.form.comboThermalBoundaryType.currentIndex()
        panel_numbers = BOUNDARY_THERMALTAB[index]
        # Enables specified rows of a QFormLayout
        from PySide.QtGui import QFormLayout
        for rowi in range(2, self.form.layoutThermal.rowCount()):  # Input values only start at row 2 of this form
            for role in [QFormLayout.LabelRole, QFormLayout.FieldRole, QFormLayout.SpanningRole]:
                item = self.form.layoutThermal.itemAt(rowi, role)
                if isinstance(item, QtGui.QWidgetItem):
                    item.widget().setVisible(rowi-2 in panel_numbers)

    def accept(self):
        if "CfdFluidBoundary" in self.obj.Label:
            self.obj.Label = self.obj.BoundarySettings['BoundaryType']
        if self.selecting_references or self.selecting_direction:
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
        for f in faces:
            FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.References.append({})".format(self.obj.Name, f))
        FreeCADGui.doCommand("FreeCAD.getDocument('{}').recompute()".format(doc_name))

    def reject(self):
        self.obj.References = self.ReferencesOrig
        self.obj.BoundarySettings = self.BoundarySettingsOrig.copy()
        if self.selecting_references or self.selecting_direction:
            FreeCADGui.Selection.removeObserver(self)
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc_name = str(self.obj.Document.Name)
        FreeCAD.getDocument(doc_name).recompute()
        doc.resetEdit()
        return True

    def faceListSelection(self):
        self.form.stackedWidget.setCurrentIndex(1)
        analysis_obj = FemGui.getActiveAnalysis()
        self.solidsNames = ['None']
        self.solidsLabels = ['None']
        for i in FreeCADGui.ActiveDocument.Document.Objects:
            if "Shape" in i.PropertiesList:
                if len(i.Shape.Solids)>0:
                    self.solidsNames.append(i.Name)
                    self.solidsLabels.append(i.Label)
                    #FreeCADGui.hideObject(i)
        self.form.shapeComboBox.clear()
        #self.form.shapeComboBox.insertItems(1,self.solidsNames)
        self.form.shapeComboBox.insertItems(1,self.solidsLabels)

    def closeFaceList(self):
        self.form.stackedWidget.setCurrentIndex(0)
        #self.obj.ViewObject.show()

    def faceListShapeChosen(self):
        ind = self.form.shapeComboBox.currentIndex()
        objectName = self.solidsNames[ind]
        self.shapeObj = FreeCADGui.ActiveDocument.Document.getObject(objectName)
        self.hideObjects()
        self.form.faceListWidget.clear()
        if objectName != 'None':
            FreeCADGui.showObject(self.shapeObj)
            self.listOfShapeFaces = self.shapeObj.Shape.Faces
            for i in range(len(self.listOfShapeFaces)):
                self.form.faceListWidget.insertItem(i,"Face"+str(i))

    def hideObjects(self):
        for i in FreeCADGui.ActiveDocument.Document.Objects:
            if "Shape" in i.PropertiesList:
                FreeCADGui.hideObject(i)
        self.obj.ViewObject.show()

    def faceHighlightChange(self):
        ind = self.form.faceListWidget.currentRow()
        FreeCADGui.Selection.clearSelection()
        FreeCADGui.Selection.addSelection(self.shapeObj,'Face'+str(ind+1))

    def addFaceListFace(self):
        #print self.form.faceListWidget.currentItem()," : ",self.form.faceListWidget.currentRow()
        if self.form.faceListWidget.count()>0 and self.form.faceListWidget.currentRow()!=-1:
            ind = self.form.shapeComboBox.currentIndex()
            objectName = self.solidsNames[ind]
            ind = self.form.faceListWidget.currentRow()
            self.selecting_references = True
            self.addSelection(self.obj.Document.Name, objectName, 'Face'+str(ind+1))
            self.selecting_references = False

        #self.obj.ViewObject.show()
        #self.addSelection(sel.DocumentName, sel.ObjectName, sub)
