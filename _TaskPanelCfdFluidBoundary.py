# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2013-2015 - Juergen Riegel <FreeCAD@juergen-riegel.net> *
# *   Copyright (c) 2017 Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>          *
# *   Copyright (c) 2017 Johan Heyns (CSIR) <jheyns@csir.co.za>             *
# *   Copyright (c) 2017 Alfred Bogaers (CSIR) <abogaers@csir.co.za>        *
# *   Copyright (c) 2019 Oliver Oxtoby <oliveroxtoby@gmail.com>             *
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
import os
import os.path
import CfdTools
from CfdTools import getQuantity, setQuantity, indexOrDefault
import CfdFaceSelectWidget
import CfdFluidBoundary
if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtGui
    try:  # Qt5
        from PySide2 import QtUiTools
    except ImportError:
        from PySide import QtUiTools
    from PySide.QtGui import QFormLayout


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

        # Store values which are changed on the fly for visual update
        self.ReferencesOrig = list(self.obj.References)
        self.BoundaryTypeOrig = str(self.obj.BoundaryType)
        self.BoundarySubTypeOrig = str(self.obj.BoundarySubType)

        self.alphas = {}

        ui_path = os.path.join(os.path.dirname(__file__), "TaskPanelCfdFluidBoundary.ui")
        self.form = FreeCADGui.PySideUic.loadUi(ui_path)

        self.form.buttonDirection.setCheckable(True)
        # Annoyingly can't find a way to set ID's for button group from .ui file...
        self.form.buttonGroupPorous.setId(self.form.radioButtonPorousCoeff, 0)
        self.form.buttonGroupPorous.setId(self.form.radioButtonPorousScreen, 1)

        self.form.comboBoundaryType.addItems(CfdFluidBoundary.BOUNDARY_NAMES)
        bi = indexOrDefault(CfdFluidBoundary.BOUNDARY_TYPES, self.obj.BoundaryType, 0)
        self.form.comboBoundaryType.currentIndexChanged.connect(self.comboBoundaryTypeChanged)
        self.form.comboBoundaryType.setCurrentIndex(bi)
        self.comboBoundaryTypeChanged()

        si = indexOrDefault(CfdFluidBoundary.SUBTYPES[bi], self.obj.BoundarySubType, 0)
        self.form.comboSubtype.currentIndexChanged.connect(self.comboSubtypeChanged)
        self.form.comboSubtype.setCurrentIndex(si)
        self.comboSubtypeChanged()

        cart = self.obj.VelocityIsCartesian
        self.form.radioButtonCart.setChecked(cart)
        self.form.radioButtonMagNormal.setChecked(not cart)
        setQuantity(self.form.inputCartX, self.obj.Ux)
        setQuantity(self.form.inputCartY, self.obj.Uy)
        setQuantity(self.form.inputCartZ, self.obj.Uz)
        setQuantity(self.form.inputVelocityMag, self.obj.VelocityMag)
        self.form.lineDirection.setText(self.obj.DirectionFace)
        self.form.checkReverse.setChecked(self.obj.ReverseNormal)
        setQuantity(self.form.inputPressure, self.obj.Pressure)
        setQuantity(self.form.inputSlipRatio, self.obj.SlipRatio)
        setQuantity(self.form.inputVolFlowRate, self.obj.VolFlowRate)
        setQuantity(self.form.inputMassFlowRate, self.obj.MassFlowRate)

        buttonId = indexOrDefault(CfdFluidBoundary.POROUS_METHODS, self.obj.PorousBaffleMethod, 0)
        selButton = self.form.buttonGroupPorous.button(buttonId)
        if selButton is not None:
            selButton.setChecked(True)
        setQuantity(self.form.inputPressureDropCoeff, self.obj.PressureDropCoeff)
        setQuantity(self.form.inputWireDiameter, self.obj.ScreenWireDiameter)
        setQuantity(self.form.inputSpacing, self.obj.ScreenSpacing)

        self.form.comboThermalBoundaryType.addItems(CfdFluidBoundary.THERMAL_BOUNDARY_NAMES)
        thi = indexOrDefault(CfdFluidBoundary.THERMAL_BOUNDARY_TYPES, self.obj.ThermalBoundaryType, 0)
        self.form.comboThermalBoundaryType.setCurrentIndex(thi)
        setQuantity(self.form.inputTemperature, self.obj.Temperature)
        setQuantity(self.form.inputHeatFlux, self.obj.HeatFlux)
        setQuantity(self.form.inputHeatTransferCoeff, self.obj.HeatTransferCoeff)

        if self.turbModel is not None:
            self.form.comboTurbulenceSpecification.addItems(CfdFluidBoundary.TURBULENT_INLET_SPEC[self.turbModel][0])
            ti = indexOrDefault(CfdFluidBoundary.TURBULENT_INLET_SPEC[self.turbModel][1],
                                self.obj.TurbulenceInletSpecification, 0)
            self.form.comboTurbulenceSpecification.setCurrentIndex(ti)

        # Add volume fraction fields
        self.alphas = self.obj.VolumeFractions
        if len(self.material_objs) > 1:
            mat_names = []
            for m in self.material_objs:
                mat_names.append(m.Label)
            self.form.comboFluid.clear()
            self.form.comboFluid.addItems(mat_names[:-1])
            self.comboFluidChanged(self.form.comboFluid.currentIndex())
        else:
            self.form.comboFluid.clear()

        setQuantity(self.form.inputKineticEnergy, self.obj.TurbulentKineticEnergy)
        setQuantity(self.form.inputSpecificDissipationRate, self.obj.SpecificDissipationRate)
        setQuantity(self.form.inputIntensity, self.obj.TurbulenceIntensity)
        setQuantity(self.form.inputLengthScale, self.obj.TurbulenceLengthScale)

        self.form.radioButtonCart.toggled.connect(self.updateUI)
        self.form.radioButtonMagNormal.toggled.connect(self.updateUI)
        self.form.lineDirection.textChanged.connect(self.lineDirectionChanged)
        self.form.buttonDirection.clicked.connect(self.buttonDirectionClicked)
        self.form.buttonGroupPorous.buttonClicked.connect(self.updateUI)
        self.form.comboTurbulenceSpecification.currentIndexChanged.connect(self.updateUI)
        self.form.comboFluid.currentIndexChanged.connect(self.comboFluidChanged)
        self.form.inputVolumeFraction.valueChanged.connect(self.inputVolumeFractionChanged)
        self.form.comboThermalBoundaryType.currentIndexChanged.connect(self.updateUI)

        # Face list selection panel - modifies obj.References passed to it
        self.faceSelector = CfdFaceSelectWidget.CfdFaceSelectWidget(self.form.faceSelectWidget,
                                                                    self.obj, True, False)

        self.updateUI()

    def updateUI(self):
        type_index = self.form.comboBoundaryType.currentIndex()
        subtype_index = self.form.comboSubtype.currentIndex()
        tab_enabled = CfdFluidBoundary.BOUNDARY_UI[type_index][subtype_index][0]
        self.form.basicFrame.setVisible(tab_enabled)
        for paneli in range(self.form.layoutBasicValues.count()):
            if isinstance(self.form.layoutBasicValues.itemAt(paneli), QtGui.QWidgetItem):
                self.form.layoutBasicValues.itemAt(paneli).widget().setVisible(False)
        if tab_enabled:
            panel_numbers = CfdFluidBoundary.BOUNDARY_UI[type_index][subtype_index][1]
            for panel_number in panel_numbers:
                self.form.layoutBasicValues.itemAt(panel_number).widget().setVisible(True)
                if panel_number == 0:
                    reverse = CfdFluidBoundary.BOUNDARY_UI[type_index][subtype_index][2]
                    # If user hasn't set a patch yet, initialise 'reverse' to default
                    if self.form.lineDirection.text() == "":
                        self.form.checkReverse.setChecked(reverse)
        turb_enabled = CfdFluidBoundary.BOUNDARY_UI[type_index][subtype_index][3]
        self.form.turbulenceFrame.setVisible(turb_enabled and self.turbModel is not None)
        alpha_enabled = CfdFluidBoundary.BOUNDARY_UI[type_index][subtype_index][4]
        self.form.volumeFractionsFrame.setVisible(alpha_enabled and len(self.material_objs) > 1)
        if self.physics_model.Thermal != 'None' and CfdFluidBoundary.BOUNDARY_UI[type_index][subtype_index][5]:
            self.form.thermalFrame.setVisible(True)
            selected_rows = CfdFluidBoundary.BOUNDARY_UI[type_index][subtype_index][6]
            for rowi in range(self.form.layoutThermal.count()):
                for role in [QFormLayout.LabelRole, QFormLayout.FieldRole, QFormLayout.SpanningRole]:
                    item = self.form.layoutThermal.itemAt(rowi, role)
                    if item:
                        if isinstance(item, QtGui.QWidgetItem):
                            item.widget().setVisible(selected_rows is None)
            if selected_rows:
                for row_enabled in selected_rows:
                    for role in [QFormLayout.LabelRole, QFormLayout.FieldRole, QFormLayout.SpanningRole]:
                        item = self.form.layoutThermal.itemAt(row_enabled, role)
                        if item:
                            item.widget().setVisible(True)
        else:
            self.form.thermalFrame.setVisible(False)

        self.form.frameCart.setVisible(self.form.radioButtonCart.isChecked())
        self.form.frameMagNormal.setVisible(self.form.radioButtonMagNormal.isChecked())

        method = self.form.buttonGroupPorous.checkedId()
        self.form.stackedWidgetPorous.setCurrentIndex(method)

        if self.turbModel:
            index = self.form.comboTurbulenceSpecification.currentIndex()
            self.form.labelTurbulenceDescription.setText(
                CfdFluidBoundary.TURBULENT_INLET_SPEC[self.turbModel][2][index])
            panel_numbers = CfdFluidBoundary.TURBULENT_INLET_SPEC[self.turbModel][3][index]
            # Enables specified rows of a QFormLayout
            for rowi in range(self.form.layoutTurbulenceValues.count()):
                for role in [QFormLayout.LabelRole, QFormLayout.FieldRole, QFormLayout.SpanningRole]:
                    item = self.form.layoutTurbulenceValues.itemAt(rowi, role)
                    if isinstance(item, QtGui.QWidgetItem):
                        item.widget().setVisible(rowi in panel_numbers)

        if CfdFluidBoundary.BOUNDARY_UI[type_index][subtype_index][6] is None:
            # Rows of thermal not stipulated - choose with dropdown
            index = self.form.comboThermalBoundaryType.currentIndex()
            self.form.labelThermalDescription.setText(CfdFluidBoundary.THERMAL_HELPTEXT[index])
            panel_numbers = CfdFluidBoundary.BOUNDARY_THERMALTAB[index]
            # Enables specified rows of a QFormLayout
            for rowi in range(2, self.form.layoutThermal.count()):  # Input values only start at row 2 of this form
                for role in [QFormLayout.LabelRole, QFormLayout.FieldRole, QFormLayout.SpanningRole]:
                    item = self.form.layoutThermal.itemAt(rowi, role)
                    if isinstance(item, QtGui.QWidgetItem):
                        item.widget().setVisible(rowi-2 in panel_numbers)

    def comboBoundaryTypeChanged(self):
        index = self.form.comboBoundaryType.currentIndex()
        self.form.comboSubtype.clear()
        self.form.comboSubtype.addItems(CfdFluidBoundary.SUBNAMES[index])
        self.form.comboSubtype.setCurrentIndex(0)
        self.obj.BoundaryType = CfdFluidBoundary.BOUNDARY_TYPES[self.form.comboBoundaryType.currentIndex()]

        # Change the color of the boundary condition as the selection is made
        doc_name = str(self.obj.Document.Name)
        FreeCAD.getDocument(doc_name).recompute()

    def comboSubtypeChanged(self):
        type_index = self.form.comboBoundaryType.currentIndex()
        subtype_index = self.form.comboSubtype.currentIndex()
        self.form.labelBoundaryDescription.setText(CfdFluidBoundary.SUBTYPES_HELPTEXT[type_index][subtype_index])
        self.obj.BoundarySubType = CfdFluidBoundary.SUBTYPES[type_index][self.form.comboSubtype.currentIndex()]
        self.updateUI()

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
                        self.addSelection(sel.DocumentName, sel.ObjectName, sub)
        FreeCADGui.Selection.clearSelection()
        # start SelectionObserver and parse the function to add the References to the widget
        if self.selecting_direction:
            FreeCAD.Console.PrintMessage("Select face to define direction\n")
            FreeCADGui.Selection.addObserver(self)
        else:
            FreeCADGui.Selection.removeObserver(self)
        self.form.buttonDirection.setChecked(self.selecting_direction)

    def addSelection(self, doc_name, obj_name, sub, selectedPoint=None):
        # This is the direction selection
        if not self.selecting_direction:
            # Shouldn't be here
            return
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
        self.form.buttonDirection.setChecked(self.selecting_direction)

    def lineDirectionChanged(self, value):
        selection = value.split(':')
        # See if entered face actually exists and is planar
        try:
            selected_object = self.obj.Document.getObject(selection[0])
            if hasattr(selected_object, "Shape"):
                elt = selected_object.Shape.getElement(selection[1])
                if elt.ShapeType == 'Face' and CfdTools.is_planar(elt):
                    return
        except SystemError:
            pass
        FreeCAD.Console.PrintMessage(value + " is not a valid, planar face\n")

    def getMaterialName(self, index):
        return self.material_objs[index].Label

    def comboFluidChanged(self, index):
        setQuantity(self.form.inputVolumeFraction, str(self.alphas.get(self.getMaterialName(index), 0.0)))

    def inputVolumeFractionChanged(self, value):
        self.alphas[self.form.comboFluid.currentText()] = getQuantity(self.form.inputVolumeFraction)

    def accept(self):
        if self.obj.Label.startswith("CfdFluidBoundary"):
            self.obj.Label = self.obj.BoundaryType
        FreeCADGui.Selection.removeObserver(self)

        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()

        FreeCADGui.doCommand("\nbc = FreeCAD.ActiveDocument.{}".format(self.obj.Name))
        # Type
        FreeCADGui.doCommand("bc.BoundaryType "
                             "= '{}'".format(self.obj.BoundaryType))
        FreeCADGui.doCommand("bc.BoundarySubType "
                             "= '{}'".format(self.obj.BoundarySubType))
        FreeCADGui.doCommand("bc.ThermalBoundaryType "
                             "= '{}'".format(CfdFluidBoundary.THERMAL_BOUNDARY_TYPES[
                                self.form.comboThermalBoundaryType.currentIndex()]))
        # Velocity
        FreeCADGui.doCommand("bc.VelocityIsCartesian "
                             "= {}".format(self.form.radioButtonCart.isChecked()))
        FreeCADGui.doCommand("bc.Ux "
                             "= '{}'".format(getQuantity(self.form.inputCartX)))
        FreeCADGui.doCommand("bc.Uy "
                             "= '{}'".format(getQuantity(self.form.inputCartY)))
        FreeCADGui.doCommand("bc.Uz "
                             "= '{}'".format(getQuantity(self.form.inputCartZ)))
        FreeCADGui.doCommand("bc.VelocityMag "
                             "= '{}'".format(getQuantity(self.form.inputVelocityMag)))
        FreeCADGui.doCommand("bc.DirectionFace "
                             "= '{}'".format(self.form.lineDirection.text()))
        FreeCADGui.doCommand("bc.ReverseNormal "
                             "= {}".format(self.form.checkReverse.isChecked()))
        FreeCADGui.doCommand("bc.MassFlowRate "
                             "= '{}'".format(getQuantity(self.form.inputMassFlowRate)))
        FreeCADGui.doCommand("bc.VolFlowRate "
                             "= '{}'".format(getQuantity(self.form.inputVolFlowRate)))
        # Presure
        FreeCADGui.doCommand("bc.Pressure "
                             "= '{}'".format(getQuantity(self.form.inputPressure)))
        # Wall
        FreeCADGui.doCommand("bc.SlipRatio "
                             "= '{}'".format(getQuantity(self.form.inputSlipRatio)))
        # Thermal
        FreeCADGui.doCommand("bc.Temperature "
                             "= '{}'".format(getQuantity(self.form.inputTemperature)))
        FreeCADGui.doCommand("bc.HeatFlux "
                             "= '{}'".format(getQuantity(self.form.inputHeatFlux)))
        FreeCADGui.doCommand("bc.HeatTransferCoeff "
                             "= '{}'".format(getQuantity(self.form.inputHeatTransferCoeff)))

        # Turbulence
        if self.turbModel in CfdFluidBoundary.TURBULENT_INLET_SPEC:
            turb_index = self.form.comboTurbulenceSpecification.currentIndex()
            FreeCADGui.doCommand("bc.TurbulenceInletSpecification "
                                 "= '{}'".format(CfdFluidBoundary.TURBULENT_INLET_SPEC[self.turbModel][1][turb_index]))
        else:
            FreeCADGui.doCommand("bc.TurbulenceInletSpecification "
                                 "= '{}'".format(self.obj.TurbulenceInletSpecification))
        FreeCADGui.doCommand("bc.TurbulentKineticEnergy "
                             "= '{}'".format(getQuantity(self.form.inputKineticEnergy)))
        FreeCADGui.doCommand("bc.SpecificDissipationRate "
                             "= '{}'".format(getQuantity(self.form.inputSpecificDissipationRate)))
        FreeCADGui.doCommand("bc.TurbulenceIntensity "
                             "= '{}'".format(getQuantity(self.form.inputIntensity)))
        FreeCADGui.doCommand("bc.TurbulenceLengthScale "
                             "= '{}'".format(getQuantity(self.form.inputLengthScale)))
        FreeCADGui.doCommand("bc.VolumeFractions = {}".format(self.alphas))

        # Porous
        FreeCADGui.doCommand("bc.PorousBaffleMethod "
                             "= '{}'".format(CfdFluidBoundary.POROUS_METHODS[self.form.buttonGroupPorous.checkedId()]))
        FreeCADGui.doCommand("bc.PressureDropCoeff "
                             "= '{}'".format(getQuantity(self.form.inputPressureDropCoeff)))
        FreeCADGui.doCommand("bc.ScreenWireDiameter "
                             "= '{}'".format(getQuantity(self.form.inputWireDiameter)))
        FreeCADGui.doCommand("bc.ScreenSpacing "
                             "= '{}'".format(getQuantity(self.form.inputSpacing)))
        FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.Label = '{}'".format(self.obj.Name, self.obj.Label))
        faces = []
        for ref in self.obj.References:
            faces.append(ref)
        self.obj.References = []
        FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.References = []".format(self.obj.Name))
        for f in faces:
            FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.References.append({})".format(self.obj.Name, f))
        FreeCADGui.doCommand("FreeCAD.ActiveDocument.recompute()")
        self.faceSelector.closing()

    def reject(self):
        self.obj.References = self.ReferencesOrig
        self.obj.BoundaryType = self.BoundaryTypeOrig
        self.obj.BoundarySubType = self.BoundarySubTypeOrig
        FreeCADGui.Selection.removeObserver(self)
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc_name = str(self.obj.Document.Name)
        FreeCAD.getDocument(doc_name).recompute()
        doc.resetEdit()
        self.faceSelector.closing()
        return True
