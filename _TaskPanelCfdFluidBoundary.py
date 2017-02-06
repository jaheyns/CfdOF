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
import Units

if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore
    from PySide import QtCore
    from PySide import QtGui
    from PySide.QtCore import Qt
    from PySide.QtGui import QApplication
    import FemGui

# Constants

BOUNDARY_TYPES = ["wall", "inlet", "outlet", "interface", "freestream", "baffle"]
SUBTYPES = [["fixed", "slip", "partialSlip", "moving", "rough"],
            ["totalPressure", "uniformVelocity", "volumetricFlowRate", "massFlowRate"],
            ["totalPressure", "staticPressure", "uniformVelocity", "outFlow"],
            ["symmetryPlane", "cyclic", "wedge", "empty", "coupled"],
            ["freestream"],
            ["porousBaffle"]]

SUBTYPES_HELPTEXT = [["Viscous wall boundary (zero velocity)",
                      "Frictionless wall",
                      "Blended fixed/slip",
                      "Viscous moving wall",
                      "Wall roughness function"],
                     ["Total pressure specified, treated as static pressure for reverse flow",
                      "Velocity specified, normal component imposed for reverse flow",
                      "Uniform volume flow rate specified",
                      "Uniform mass flow rate specified"],
                     ["Static pressure specified, treated as total pressure for reverse flow",
                      "Static pressure specified for outflow and reverse flow",
                      "Normal component imposed for outflow, velocity fixed for reverse flow",
                      "All fields extrapolated; use with care!"],
                     ["Symmetry plane",
                      "Periodic boundary, treated as physically connected",
                      "Axi-symmetric periodic boundary",
                      "Front and back for single layer 2D mesh and axi-symmetric axis line",
                      "Exchange boundary value with external program, requires manual setup"],
                     ["Far-field conditions"],
                     ["Permeable screen"]]

# For each sub-type, whether the basic tab is enabled, the panel number to show, and (for panel 0 only) whether
# direction reversal is checked by default
BOUNDARY_BASICTAB = [[[False],
                      [False],
                      [True, 2],
                      [True, 0, False],
                      [True, 0, False]],
                     [[True, 1],
                      [True, 0, True],
                      [True, 3],
                      [True, 4]],
                     [[True, 1],
                      [True, 1],
                      [True, 0, False],
                      [False]],
                     [[False],
                      [False],
                      [False],
                      [False],
                      [False]],
                     [[True, 0, True]],
                     [[True, 5]]]

TURBULENCE_SPECIFICATIONS = ["intensity&DissipationRate",
                             "intensity&LengthScale",
                             "intensity&ViscosityRatio",
                             "intensity&HydraulicDiameter"]

TURBULENCE_HELPTEXT = ["Explicit specific intensity k and dissipation rate epsilon / omega",
                       "Intensity (0.05 ~ 0.15) and characteristic length scale of max eddy",
                       "Intensity (0.05 ~ 0.15) and turbulent viscosity ratio",
                       "For fully developed internal flow, Turbulence intensity (0-1.0); 0.05 typical"]

# For each turbulent specification, the input box(es) presented to the user
BOUNDARY_TURBULENCETAB = [[0], [0, 1], [0], [0, 1]]

THERMAL_BOUNDARY_TYPES = ["fixedValue", "zeroGradient", "fixedGradient", "mixed", "HTC", "coupled"]

THERMAL_HELPTEXT = ["Fixed Temperature", "No heat transfer on boundary", "Fixed value gradient",
                    "Mixed fixedGradient and fixedValue", "Fixed heat flux", "Heat transfer coefficient",
                    "Conjugate heat transfer with solid"]

# For each thermal BC, the input rows presented to the user
BOUNDARY_THERMALTAB = [[0], [], [1], [0, 1], [2], []]


class TaskPanelCfdFluidBoundary:
    """ Taskpanel for adding fluid boundary """
    def __init__(self, obj):
        self.selecting_references = False
        self.selecting_direction = False
        self.obj = obj
        self.References = self.obj.References
        self.BoundarySettings = self.obj.BoundarySettings.copy()
        self.faceList = list(self.obj.faceList)

        ui_path = os.path.dirname(__file__) + os.path.sep + "TaskPanelCfdFluidBoundary.ui"
        self.form = FreeCADGui.PySideUic.loadUi(ui_path)

        self.form.comboBoundaryType.currentIndexChanged.connect(self.comboBoundaryTypeChanged)
        self.form.comboSubtype.currentIndexChanged.connect(self.comboSubtypeChanged)
        self.form.listReferences.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.form.listReferences.connect(self.form.listReferences, QtCore.SIGNAL("customContextMenuRequested(QPoint)"),
                                         self.listReferencesRightClicked)
        self.form.buttonReference.clicked.connect(self.buttonReferenceClicked)
        self.form.buttonReference.setCheckable(True)
        self.form.radioButtonCart.toggled.connect(self.radioButtonVelocityToggled)
        self.form.radioButtonMagNormal.toggled.connect(self.radioButtonVelocityToggled)
        self.form.inputCartX.textChanged.connect(self.inputCartXChanged)
        self.form.inputCartY.textChanged.connect(self.inputCartYChanged)
        self.form.inputCartZ.textChanged.connect(self.inputCartZChanged)
        self.form.inputVelocityMag.textChanged.connect(self.inputVelocityMagChanged)
        self.form.lineDirection.textChanged.connect(self.lineDirectionChanged)
        self.form.buttonDirection.clicked.connect(self.buttonDirectionClicked)
        self.form.buttonDirection.setCheckable(True)
        self.form.checkReverse.toggled.connect(self.checkReverseToggled)
        self.form.inputPressure.textChanged.connect(self.inputPressureChanged)
        self.form.inputSlipRatio.textChanged.connect(self.inputSlipRatioChanged)
        self.form.inputVolFlowRate.textChanged.connect(self.inputVolFlowRateChanged)
        self.form.inputMassFlowRate.textChanged.connect(self.inputMassFlowRateChanged)
        self.form.buttonGroupPorous.buttonClicked.connect(self.buttonGroupPorousClicked)
        # Annoyingly can't find a way to set ID's from .ui file...
        self.form.buttonGroupPorous.setId(self.form.radioButtonPorousCoeff, 0)
        self.form.buttonGroupPorous.setId(self.form.radioButtonPorousScreen, 1)
        self.form.inputPressureDropCoeff.textChanged.connect(self.inputPressureDropCoeffChanged)
        self.form.inputWireDiameter.textChanged.connect(self.inputWireDiameterChanged)
        self.form.inputSpacing.textChanged.connect(self.inputSpacingChanged)
        self.form.comboTurbulenceSpecification.currentIndexChanged.connect(self.comboTurbulenceSpecificationChanged)
        self.form.comboThermalBoundaryType.currentIndexChanged.connect(self.comboThermalBoundaryTypeChanged)

        # Populate UI
        self.form.comboBoundaryType.addItems(BOUNDARY_TYPES)
        self.form.comboBoundaryType.setCurrentIndex(
            self.form.comboBoundaryType.findText(self.obj.BoundarySettings['BoundaryType']))
        self.form.comboSubtype.setCurrentIndex(
            self.form.comboSubtype.findText(self.obj.BoundarySettings['BoundarySubtype']))
        self.rebuild_list_references()
        self.form.radioButtonCart.setChecked(self.obj.BoundarySettings['VelocityIsCartesian'])
        self.form.radioButtonMagNormal.setChecked(not self.obj.BoundarySettings['VelocityIsCartesian'])
        self.form.inputCartX.setText(self.obj.BoundarySettings['Ux'])
        self.form.inputCartY.setText(self.obj.BoundarySettings['Uy'])
        self.form.inputCartZ.setText(self.obj.BoundarySettings['Uz'])
        self.form.inputVelocityMag.setText(self.obj.BoundarySettings['VelocityMag'])
        self.form.lineDirection.setText(self.obj.BoundarySettings['DirectionFace'])
        self.form.checkReverse.setChecked(self.obj.BoundarySettings['ReverseNormal'])
        self.form.inputPressure.setText(self.obj.BoundarySettings['Pressure'])
        self.form.inputSlipRatio.setText(str(self.obj.BoundarySettings['SlipRatio']))
        self.form.inputVolFlowRate.setText(self.obj.BoundarySettings['VolFlowRate'])
        self.form.inputMassFlowRate.setText(self.obj.BoundarySettings['MassFlowRate'])
        self.form.radioButtonCart.setChecked(self.obj.BoundarySettings['VelocityIsCartesian'])
        self.form.radioButtonMagNormal.setChecked(not self.obj.BoundarySettings['VelocityIsCartesian'])
        buttonId = CfdTools.getOrDefault(self.obj.BoundarySettings, 'PorousBaffleMethod', 0)
        selButton = self.form.buttonGroupPorous.button(buttonId)
        if selButton is not None:
            selButton.setChecked(True)
            self.buttonGroupPorousClicked(selButton)  # Signal is not generated on setChecked above
        self.form.inputPressureDropCoeff.setText(
            CfdTools.getOrDefault(self.obj.BoundarySettings, 'PressureDropCoeff', ""))
        self.form.inputWireDiameter.setText(
            CfdTools.getOrDefault(self.obj.BoundarySettings, 'ScreenWireDiameter', ""))
        self.form.inputSpacing.setText(CfdTools.getOrDefault(self.obj.BoundarySettings, 'ScreenSpacing', ""))
        self.form.comboTurbulenceSpecification.addItems(TURBULENCE_SPECIFICATIONS)
        self.form.comboTurbulenceSpecification.setCurrentIndex(
            self.form.comboTurbulenceSpecification.findText(self.obj.BoundarySettings['TurbulenceSpecification']))
        self.form.comboThermalBoundaryType.addItems(THERMAL_BOUNDARY_TYPES)
        self.form.comboThermalBoundaryType.setCurrentIndex(
            self.form.comboThermalBoundaryType.findText(self.obj.BoundarySettings['ThermalBoundaryType']))

        # First time, add any currently selected faces to list
        if len(self.References) == 0:
            self.selecting_references = True
            self.add_selection_to_ref_list()
            self.selecting_references = False
            FreeCADGui.Selection.clearSelection()
            self.update_selectionbuttons_ui()

    def add_selection_to_ref_list(self):
        """ Add currently selected objects to reference list. """
        for sel in FreeCADGui.Selection.getSelectionEx():
            if sel.HasSubObjects:
                for sub in sel.SubElementNames:
                    self.addSelection(sel.DocumentName, sel.ObjectName, sub)

    def comboBoundaryTypeChanged(self):
        index = self.form.comboBoundaryType.currentIndex()
        self.form.comboSubtype.clear()
        self.form.comboSubtype.addItems(SUBTYPES[index])
        self.form.comboSubtype.setCurrentIndex(0)
        self.BoundarySettings['BoundaryType'] = self.form.comboBoundaryType.currentText()

    def comboSubtypeChanged(self):
        type_index = self.form.comboBoundaryType.currentIndex()
        subtype_index = self.form.comboSubtype.currentIndex()
        self.form.labelBoundaryDescription.setText(SUBTYPES_HELPTEXT[type_index][subtype_index])
        self.BoundarySettings['BoundarySubtype'] = self.form.comboSubtype.currentText()
        self.update_boundary_type_ui()

    def update_boundary_type_ui(self):
        type_index = self.form.comboBoundaryType.currentIndex()
        subtype_index = self.form.comboSubtype.currentIndex()
        tab_enabled = BOUNDARY_BASICTAB[type_index][subtype_index][0]
        self.form.basicFrame.setVisible(tab_enabled)
        for paneli in range(self.form.layoutBasicValues.count()):
            if isinstance(self.form.layoutBasicValues.itemAt(paneli), QtGui.QWidgetItem):  # Segfaults otherwise...
                self.form.layoutBasicValues.itemAt(paneli).widget().setVisible(False)
        if tab_enabled:
            panel_number = BOUNDARY_BASICTAB[type_index][subtype_index][1]
            self.form.layoutBasicValues.itemAt(panel_number).widget().setVisible(True)
            if panel_number == 0:
                reverse = BOUNDARY_BASICTAB[type_index][subtype_index][2]
                # If user hasn't set a patch yet, initialise 'reverse' to default
                if self.form.lineDirection.text() == "":
                    self.form.checkReverse.setChecked(reverse)

    def buttonReferenceClicked(self):
        """Called if Button buttonReference is triggered. """
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
        FreeCADGui.doCommand("FreeCAD.getDocument('"+doc_name+"').recompute()")  # Create compound part
        self.update_selectionbuttons_ui()

    def update_selectionbuttons_ui(self):
        self.form.buttonDirection.setChecked(self.selecting_direction)
        self.form.buttonReference.setChecked(self.selecting_references)

    def radioButtonVelocityToggled(self, checked):
        self.BoundarySettings['VelocityIsCartesian'] = self.form.radioButtonCart.isChecked()
        self.form.frameCart.setVisible(self.form.radioButtonCart.isChecked())
        self.form.frameMagNormal.setVisible(self.form.radioButtonMagNormal.isChecked())

    def buttonDirectionClicked(self):
        """Called if Button buttonDirection is triggered. """
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
        print('Selection: ' + selected_object.Shape.ShapeType + '  ' + selected_object.Name + ':' + sub + " @ " + str(extra))
        if hasattr(selected_object, "Shape") and sub:
            elt = selected_object.Shape.getElement(sub)
            if elt.ShapeType == 'Face':
                selection = (selected_object.Name, sub)
                if self.selecting_references:
                    if selection not in self.References:
                        self.References.append(selection)
                        self.rebuild_list_references()
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
        self.update_selectionbuttons_ui()

    def rebuild_list_references(self):
        self.form.listReferences.clear()
        items = []
        for ref in self.References:
            item_name = ref[0] + ':' + ref[1]
            items.append(item_name)
        for listItemName in sorted(items):
            self.form.listReferences.addItem(listItemName)

    def listReferencesRightClicked(self, QPos):
        self.form.contextMenu = QtGui.QMenu()
        menu_item = self.form.contextMenu.addAction("Remove Reference")
        if not self.References:
            menu_item.setDisabled(True)
        self.form.connect(menu_item, QtCore.SIGNAL("triggered()"), self.remove_reference)
        parent_position = self.form.listReferences.mapToGlobal(QtCore.QPoint(0, 0))
        self.form.contextMenu.move(parent_position + QPos)
        self.form.contextMenu.show()

    def remove_reference(self):
        if not self.References:
            return
        current_item_name = str(self.form.listReferences.currentItem().text())
        for ref in self.References:
            refname = ref[0] + ':' + ref[1]
            if refname == current_item_name:
                self.References.remove(ref)
        self.rebuild_list_references()

    def inputCheckAndStore(self, value, units, key):
        value = Units.Quantity(value).getValueAs(units)
        self.BoundarySettings[key] = unicode(value) + units

    def inputCartXChanged(self, value):
        self.inputCheckAndStore(value, "m/s", 'Ux')

    def inputCartYChanged(self, value):
        self.inputCheckAndStore(value, "m/s", 'Uy')

    def inputCartZChanged(self, value):
        self.inputCheckAndStore(value, "m/s", 'Uz')

    def inputVelocityMagChanged(self, value):
        self.inputCheckAndStore(value, "m/s", 'VelocityMag')

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
        self.inputCheckAndStore(value, "kg*m/s^2", 'Pressure')

    def inputSlipRatioChanged(self, value):
        self.inputCheckAndStore(value, "m/m", 'SlipRatio')

    def inputVolFlowRateChanged(self, value):
        self.inputCheckAndStore(value, "m^3/s", 'VolFlowRate')

    def inputMassFlowRateChanged(self, value):
        self.inputCheckAndStore(value, "kg/s", 'MassFlowRate')

    def buttonGroupPorousClicked(self, button):
        method = self.form.buttonGroupPorous.checkedId()
        self.BoundarySettings['PorousBaffleMethod'] = method
        self.form.stackedWidgetPorous.setCurrentIndex(method)

    def inputPressureDropCoeffChanged(self, value):
        self.inputCheckAndStore(value, "m/m", 'PressureDropCoeff')
        print(value)
        print(self.BoundarySettings['PressureDropCoeff'])

    def inputWireDiameterChanged(self, value):
        self.inputCheckAndStore(value, "mm", 'ScreenWireDiameter')

    def inputSpacingChanged(self, value):
        self.inputCheckAndStore(value, "mm", 'ScreenSpacing')

    def comboTurbulenceSpecificationChanged(self, index):
        self.form.labelTurbulenceDescription.setText(TURBULENCE_HELPTEXT[index])
        self.BoundarySettings['TurbulenceSpecification'] = self.form.comboTurbulenceSpecification.currentText()
        self.update_turbulence_ui()

    def update_turbulence_ui(self):
        index = self.form.comboTurbulenceSpecification.currentIndex()
        panel_numbers = BOUNDARY_TURBULENCETAB[index]
        # Enables specified rows of a QFormLayout
        from PySide.QtGui import QFormLayout
        for rowi in range(self.form.layoutTurbulenceValues.rowCount()):
            for role in [QFormLayout.LabelRole, QFormLayout.FieldRole, QFormLayout.SpanningRole]:
                item = self.form.layoutTurbulenceValues.itemAt(rowi, role)
                if isinstance(item, QtGui.QWidgetItem):
                    item.widget().setVisible(rowi in panel_numbers)

    def comboThermalBoundaryTypeChanged(self, index):
        self.form.labelThermalDescription.setText(THERMAL_HELPTEXT[index])
        self.BoundarySettings['ThermalBoundaryType'] = self.form.comboThermalBoundaryType.currentText()
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
        if self.selecting_references or self.selecting_direction:
            FreeCADGui.Selection.removeObserver(self)
        self.obj.References = self.References
        self.obj.BoundarySettings = self.BoundarySettings.copy()
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc_name = str(self.obj.Document.Name)
        FreeCADGui.doCommand("FreeCAD.getDocument('"+doc_name+"').recompute()")
        doc.resetEdit()

    def reject(self):
        if self.selecting_references or self.selecting_direction:
            FreeCADGui.Selection.removeObserver(self)
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()
        return True
