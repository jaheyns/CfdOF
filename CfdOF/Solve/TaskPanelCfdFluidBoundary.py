# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2017 Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>          *
# *   Copyright (c) 2017 Johan Heyns (CSIR) <jheyns@csir.co.za>             *
# *   Copyright (c) 2017 Alfred Bogaers (CSIR) <abogaers@csir.co.za>        *
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
import os.path
import FreeCAD
if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtGui, QtCore
    from PySide.QtGui import QFormLayout
from CfdOF import CfdTools
from CfdOF.CfdTools import getQuantity, setQuantity, indexOrDefault, storeIfChanged
from CfdOF import CfdFaceSelectWidget
from CfdOF.Solve import CfdFluidBoundary

translate = FreeCAD.Qt.translate

class TaskPanelCfdFluidBoundary:
    """ Task panel for adding fluid boundary """
    def __init__(self, obj, physics_model, material_objs):
        self.selecting_direction = False
        self.obj = obj

        self.physics_model = physics_model
        self.turb_model = (physics_model.TurbulenceModel
                          if physics_model.Turbulence == 'RANS' or physics_model.Turbulence == 'DES'
                             or physics_model.Turbulence == 'LES' else None)

        self.material_objs = material_objs
        self.analysis_obj = CfdTools.getParentAnalysisObject(obj)

        # Store values which are changed on the fly for visual update
        self.ShapeRefsOrig = list(self.obj.ShapeRefs)
        self.BoundaryTypeOrig = str(self.obj.BoundaryType)
        self.BoundarySubTypeOrig = str(self.obj.BoundarySubType)
        self.NeedsMeshRewriteOrig = self.analysis_obj.NeedsMeshRewrite
        self.NeedsCaseRewriteOrig = self.analysis_obj.NeedsCaseRewrite

        self.alphas = {}

        ui_path = os.path.join(CfdTools.getModulePath(), 'Gui', "TaskPanelCfdFluidBoundary.ui")
        self.form = FreeCADGui.PySideUic.loadUi(ui_path)

        self.form.buttonDirection.setCheckable(True)
        # Annoyingly can't find a way to set ID's for button group from .ui file...
        self.form.buttonGroupPorous.setId(self.form.radioButtonPorousCoeff, 0)
        self.form.buttonGroupPorous.setId(self.form.radioButtonPorousScreen, 1)

        # Boundary types
        self.form.comboBoundaryType.addItems(CfdFluidBoundary.BOUNDARY_NAMES)
        bi = indexOrDefault(CfdFluidBoundary.BOUNDARY_TYPES, self.obj.BoundaryType, 0)
        self.form.comboBoundaryType.currentIndexChanged.connect(self.comboBoundaryTypeChanged)
        self.form.comboBoundaryType.setCurrentIndex(bi)
        self.comboBoundaryTypeChanged()

        # Boundary subtypes
        si = indexOrDefault(CfdFluidBoundary.SUBTYPES[bi], self.obj.BoundarySubType, 0)
        self.form.comboSubtype.currentIndexChanged.connect(self.comboSubtypeChanged)
        self.form.comboSubtype.setCurrentIndex(si)
        self.comboSubtypeChanged()

        # Inputs
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
        setQuantity(self.form.inputAngularVelocity, self.obj.AngularVelocity)
        setQuantity(self.form.inputRotationOriginX, self.obj.RotationOrigin.x)
        setQuantity(self.form.inputRotationOriginY, self.obj.RotationOrigin.y)
        setQuantity(self.form.inputRotationOriginZ, self.obj.RotationOrigin.z)
        setQuantity(self.form.inputRotationAxisX, self.obj.RotationAxis.x)
        setQuantity(self.form.inputRotationAxisY, self.obj.RotationAxis.y)
        setQuantity(self.form.inputRotationAxisZ, self.obj.RotationAxis.z)
        setQuantity(self.form.inputSlipRatio, self.obj.SlipRatio)
        setQuantity(self.form.inputVolFlowRate, self.obj.VolFlowRate)
        setQuantity(self.form.inputMassFlowRate, self.obj.MassFlowRate)
        self.form.cb_relative_srf.setChecked(self.obj.RelativeToFrame)

        buttonId = indexOrDefault(CfdFluidBoundary.POROUS_METHODS, self.obj.PorousBaffleMethod, 0)
        selButton = self.form.buttonGroupPorous.button(buttonId)
        if selButton is not None:
            selButton.setChecked(True)
        setQuantity(self.form.inputPressureDropCoeff, self.obj.PressureDropCoeff)
        setQuantity(self.form.inputWireDiameter, self.obj.ScreenWireDiameter)
        setQuantity(self.form.inputSpacing, self.obj.ScreenSpacing)

        setQuantity(self.form.inputRoughnessHeight, self.obj.RoughnessHeight)
        setQuantity(self.form.inputRoughnessConstant, self.obj.RoughnessConstant)

        # Thermal
        self.form.comboThermalBoundaryType.addItems(CfdFluidBoundary.THERMAL_BOUNDARY_NAMES)
        thi = indexOrDefault(CfdFluidBoundary.THERMAL_BOUNDARY_TYPES, self.obj.ThermalBoundaryType, 0)
        self.form.comboThermalBoundaryType.setCurrentIndex(thi)
        setQuantity(self.form.inputTemperature, self.obj.Temperature)
        setQuantity(self.form.inputHeatFlux, self.obj.HeatFlux)
        setQuantity(self.form.inputPower, self.obj.Power)
        setQuantity(self.form.inputHeatTransferCoeff, self.obj.HeatTransferCoeff)

        # Periodics
        self.form.buttonGroupMasterSlavePeriodic.setId(self.form.radioButtonMasterPeriodic, 0)
        self.form.buttonGroupMasterSlavePeriodic.setId(self.form.radioButtonSlavePeriodic, 1)
        self.form.buttonGroupPeriodic.setId(self.form.rb_rotational_periodic, 0)
        self.form.buttonGroupPeriodic.setId(self.form.rb_translational_periodic, 1)

        boundary_patches = CfdTools.getCfdBoundaryGroup(self.analysis_obj)
        periodic_patches = []
        for patch in boundary_patches:
            if patch.BoundarySubType == 'cyclicAMI' and patch.Label != self.obj.Label:
                periodic_patches.append(patch.Label)

        self.form.comboBoxPeriodicPartner.addItems(periodic_patches)
        pi = self.form.comboBoxPeriodicPartner.findText(self.obj.PeriodicPartner, QtCore.Qt.MatchFixedString)
        if pi < 0 and len(periodic_patches):
            pi = 0
        self.form.comboBoxPeriodicPartner.setCurrentIndex(pi)

        self.form.radioButtonMasterPeriodic.setChecked(self.obj.PeriodicMaster)
        self.form.radioButtonSlavePeriodic.setChecked(not self.obj.PeriodicMaster)
        self.form.rb_rotational_periodic.setChecked(self.obj.RotationalPeriodic)
        self.form.rb_translational_periodic.setChecked(not self.obj.RotationalPeriodic)
        setQuantity(self.form.input_corx, self.obj.PeriodicCentreOfRotation.x)
        setQuantity(self.form.input_cory, self.obj.PeriodicCentreOfRotation.y)
        setQuantity(self.form.input_corz, self.obj.PeriodicCentreOfRotation.z)
        setQuantity(self.form.input_axisx, self.obj.PeriodicCentreOfRotationAxis.x)
        setQuantity(self.form.input_axisy, self.obj.PeriodicCentreOfRotationAxis.y)
        setQuantity(self.form.input_axisz, self.obj.PeriodicCentreOfRotationAxis.z)
        setQuantity(self.form.input_sepx, self.obj.PeriodicSeparationVector.x)
        setQuantity(self.form.input_sepy, self.obj.PeriodicSeparationVector.y)
        setQuantity(self.form.input_sepz, self.obj.PeriodicSeparationVector.z)

        # Turbulence
        if self.turb_model is not None:
            self.form.comboTurbulenceSpecification.addItems(CfdFluidBoundary.TURBULENT_INLET_SPEC[self.turb_model][0])
            ti = indexOrDefault(CfdFluidBoundary.TURBULENT_INLET_SPEC[self.turb_model][1], self.obj.TurbulenceInletSpecification, 0)
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

        # Set the inputs for the turbulence models
        # RANS
        setQuantity(self.form.inputKineticEnergy, self.obj.TurbulentKineticEnergy)  # k
        setQuantity(self.form.inputSpecificDissipationRate, self.obj.SpecificDissipationRate)   # omega
        setQuantity(self.form.inputDissipationRate, self.obj.DissipationRate)    # epsilon
        setQuantity(self.form.inputIntensity, self.obj.TurbulenceIntensityPercentage)      # intensity
        setQuantity(self.form.inputLengthScale, self.obj.TurbulenceLengthScale)  # length scale
        setQuantity(self.form.inputGammaInt, self.obj.Intermittency)   # gammaInt
        setQuantity(self.form.inputReThetat, self.obj.ReThetat)  # ReThetat
        setQuantity(self.form.inputNuTilda, self.obj.NuTilda) # Modified nu tilde
        # LES models
        setQuantity(self.form.inputTurbulentViscosity, self.obj.TurbulentViscosity) # nu tilde
        setQuantity(self.form.inputKineticEnergy, self.obj.TurbulentKineticEnergy)  # nu tilde

        # RANS models
        self.form.inputKineticEnergy.setToolTip("Turbulent kinetic energy")
        self.form.inputSpecificDissipationRate.setToolTip("Specific turbulence dissipation rate")
        self.form.inputDissipationRate.setToolTip("Turbulence dissipation rate")
        self.form.inputIntensity.setToolTip("Turbulence intensity")
        self.form.inputLengthScale.setToolTip("Turbulence length scale")
        self.form.inputGammaInt.setToolTip("Turbulence intermittency")
        self.form.inputReThetat.setToolTip("Momentum thickness Reynolds number")
        self.form.inputNuTilda.setToolTip("Modified turbulent viscosity")

        # LES models
        self.form.inputTurbulentViscosity.setToolTip("Turbulent viscosity")

        self.form.checkBoxDefaultBoundary.setChecked(self.obj.DefaultBoundary)

        self.form.radioButtonCart.toggled.connect(self.updateUI)
        self.form.radioButtonMagNormal.toggled.connect(self.updateUI)
        self.form.lineDirection.textChanged.connect(self.lineDirectionChanged)
        self.form.buttonDirection.clicked.connect(self.buttonDirectionClicked)
        self.form.buttonGroupPorous.buttonClicked.connect(self.updateUI)
        self.form.comboTurbulenceSpecification.currentIndexChanged.connect(self.updateUI)
        self.form.comboFluid.currentIndexChanged.connect(self.comboFluidChanged)
        self.form.inputVolumeFraction.valueChanged.connect(self.inputVolumeFractionChanged)
        self.form.comboThermalBoundaryType.currentIndexChanged.connect(self.updateUI)
        if hasattr(self.form.checkBoxDefaultBoundary, "checkStateChanged"):
            self.form.checkBoxDefaultBoundary.checkStateChanged.connect(self.updateUI)
        else:
            self.form.checkBoxDefaultBoundary.stateChanged.connect(self.updateUI)
        self.form.radioButtonMasterPeriodic.toggled.connect(self.updateUI)
        self.form.radioButtonSlavePeriodic.toggled.connect(self.updateUI)
        self.form.rb_rotational_periodic.toggled.connect(self.updateUI)
        self.form.rb_translational_periodic.toggled.connect(self.updateUI)

        # Face list selection panel - modifies obj.ShapeRefs passed to it
        self.faceSelector = CfdFaceSelectWidget.CfdFaceSelectWidget(self.form.faceSelectWidget,
                                                                    self.obj, True, True, False)

        self.updateUI()

    def updateUI(self):
        # Boundary type and subtype
        type_index = self.form.comboBoundaryType.currentIndex()
        subtype_index = self.form.comboSubtype.currentIndex()
        tab_enabled = CfdFluidBoundary.BOUNDARY_UI[type_index][subtype_index][0]

        self.form.basicFrame.setVisible(tab_enabled)
        if tab_enabled:
            is_srf = CfdTools.getPhysicsModel(CfdTools.getActiveAnalysis()).SRFModelEnabled
            self.form.cb_relative_srf.setVisible(is_srf)

        for panel_i in range(self.form.layoutBasicValues.count()):
            if isinstance(self.form.layoutBasicValues.itemAt(panel_i), QtGui.QWidgetItem):
                self.form.layoutBasicValues.itemAt(panel_i).widget().setVisible(False)

        if tab_enabled:
            panel_numbers = CfdFluidBoundary.BOUNDARY_UI[type_index][subtype_index][1]
            for panel_number in panel_numbers:
                self.form.layoutBasicValues.itemAt(panel_number).widget().setVisible(True)
                if panel_number == 0 and self.form.radioButtonMagNormal.isChecked():
                    reverse = CfdFluidBoundary.BOUNDARY_UI[type_index][subtype_index][2]
                    # If user hasn't set a patch yet, initialise 'reverse' to default
                    if self.form.lineDirection.text() == "":
                        self.form.checkReverse.setChecked(reverse)

        turb_enabled = CfdFluidBoundary.BOUNDARY_UI[type_index][subtype_index][3]
        self.form.turbulenceFrame.setVisible(turb_enabled and self.turb_model is not None)

        alpha_enabled = CfdFluidBoundary.BOUNDARY_UI[type_index][subtype_index][4]
        self.form.volumeFractionsFrame.setVisible(alpha_enabled and len(self.material_objs) > 1)

        if not self.physics_model.Flow == 'Isothermal' and CfdFluidBoundary.BOUNDARY_UI[type_index][subtype_index][5]:
            self.form.thermalFrame.setVisible(True)
            selected_rows = CfdFluidBoundary.BOUNDARY_UI[type_index][subtype_index][6]
            CfdTools.enableLayoutRows(self.form.layoutThermal, selected_rows)
        else:
            self.form.thermalFrame.setVisible(False)

        self.form.frameCart.setVisible(self.form.radioButtonCart.isChecked())
        self.form.frameMagNormal.setVisible(self.form.radioButtonMagNormal.isChecked())

        method = self.form.buttonGroupPorous.checkedId()
        self.form.stackedWidgetPorous.setCurrentIndex(method)

        # Turbulence model, set visible gui components
        if self.turb_model:
            index = self.form.comboTurbulenceSpecification.currentIndex()
            self.form.labelTurbulenceDescription.setText(
                CfdFluidBoundary.TURBULENT_INLET_SPEC[self.turb_model][2][index])
            panel_numbers = CfdFluidBoundary.TURBULENT_INLET_SPEC[self.turb_model][3][index]
            # Enables specified rows of a QFormLayout
            CfdTools.enableLayoutRows(self.form.layoutTurbulenceValues, panel_numbers)

        # Thermal model, set visible gui components
        if CfdFluidBoundary.BOUNDARY_UI[type_index][subtype_index][6] is None:
            # Rows of thermal not stipulated - choose with dropdown
            index = self.form.comboThermalBoundaryType.currentIndex()
            self.form.labelThermalDescription.setText(CfdFluidBoundary.THERMAL_HELPTEXT[index])
            panel_numbers = CfdFluidBoundary.BOUNDARY_THERMALTAB[index]
            # Input values only start at row 2 of this form
            CfdTools.enableLayoutRows(self.form.layoutThermal, [0, 1] + [rowi+2 for rowi in panel_numbers])

        periodic_enabled = CfdFluidBoundary.BOUNDARY_UI[type_index][subtype_index][7]
        if periodic_enabled:
            self.form.periodicFrame.setVisible(True)
            self.form.frameSlave.setVisible(not self.form.radioButtonMasterPeriodic.isChecked())
            if self.form.rb_rotational_periodic.isChecked():
                self.form.rotationalFrame.setVisible(True)
                self.form.translationalFrame.setVisible(False)
            else:
                self.form.rotationalFrame.setVisible(False)
                self.form.translationalFrame.setVisible(True)
        else:
            self.form.periodicFrame.setVisible(False)

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
            FreeCAD.Console.PrintMessage(
                translate("Console", "Select face to define direction\n")
            )
            FreeCADGui.Selection.addObserver(self)
        else:
            FreeCADGui.Selection.removeObserver(self)
        self.form.buttonDirection.setChecked(self.selecting_direction)

    def addSelection(self, doc_name, obj_name, sub, selected_point=None):
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
              sub + " @ " + str(selected_point))

        if hasattr(selected_object, "Shape") and sub:
            elt = selected_object.Shape.getElement(sub)
            if elt.ShapeType == 'Face':
                selection = (selected_object.Name, sub)
                if self.selecting_direction:
                    if CfdTools.isPlanar(elt):
                        self.selecting_direction = False
                        self.form.lineDirection.setText(selection[0] + ':' + selection[1])  # TODO: Display label, not name
                    else:
                        FreeCAD.Console.PrintMessage(
                            translate("Console", "Face must be planar\n")
                        )

        self.form.buttonDirection.setChecked(self.selecting_direction)

    def lineDirectionChanged(self, value):
        selection = value.split(':')
        # See if entered face actually exists and is planar
        try:
            selected_object = self.obj.Document.getObject(selection[0])
            if hasattr(selected_object, "Shape"):
                elt = selected_object.Shape.getElement(selection[1])
                if elt.ShapeType == 'Face' and CfdTools.isPlanar(elt):
                    return
        except SystemError:
            pass

        FreeCAD.Console.PrintMessage(
            value + translate("Console", " is not a valid, planar face\n")
        )

    def getMaterialName(self, index):
        return self.material_objs[index].Label

    def comboFluidChanged(self, index):
        setQuantity(self.form.inputVolumeFraction, str(self.alphas.get(self.getMaterialName(index), 0.0)))

    def inputVolumeFractionChanged(self, value):
        self.alphas[self.form.comboFluid.currentText()] = getQuantity(self.form.inputVolumeFraction)

    def accept(self):
        self.analysis_obj.NeedsMeshRewrite = self.NeedsMeshRewriteOrig
        self.analysis_obj.NeedsCaseRewrite = self.NeedsCaseRewriteOrig

        if self.obj.Label.startswith("CfdFluidBoundary"):
            storeIfChanged(self.obj, 'Label', self.obj.BoundaryType)

        # Type
        if self.obj.BoundaryType != self.BoundaryTypeOrig:
            FreeCADGui.doCommand(
                "FreeCAD.ActiveDocument.{}.BoundaryType = '{}'".format(self.obj.Name, self.obj.BoundaryType))
        if self.obj.BoundarySubType != self.BoundarySubTypeOrig:
            FreeCADGui.doCommand(
                "FreeCAD.ActiveDocument.{}.BoundarySubType = '{}'".format(self.obj.Name, self.obj.BoundarySubType))
        storeIfChanged(self.obj, 'ThermalBoundaryType',
                       CfdFluidBoundary.THERMAL_BOUNDARY_TYPES[self.form.comboThermalBoundaryType.currentIndex()])

        # Velocity
        storeIfChanged(self.obj, 'VelocityIsCartesian', self.form.radioButtonCart.isChecked())
        storeIfChanged(self.obj, 'Ux', getQuantity(self.form.inputCartX))
        storeIfChanged(self.obj, 'Uy', getQuantity(self.form.inputCartY))
        storeIfChanged(self.obj, 'Uz', getQuantity(self.form.inputCartZ))
        storeIfChanged(self.obj, 'VelocityMag', getQuantity(self.form.inputVelocityMag))
        storeIfChanged(self.obj, 'DirectionFace', self.form.lineDirection.text())
        storeIfChanged(self.obj, 'ReverseNormal', self.form.checkReverse.isChecked())
        storeIfChanged(self.obj, 'MassFlowRate', getQuantity(self.form.inputMassFlowRate))
        storeIfChanged(self.obj, 'VolFlowRate', getQuantity(self.form.inputVolFlowRate))
        storeIfChanged(self.obj, 'AngularVelocity', getQuantity(self.form.inputAngularVelocity))
        rotation_origin = FreeCAD.Vector(
            self.form.inputRotationOriginX.property("quantity").Value,
            self.form.inputRotationOriginY.property("quantity").Value,
            self.form.inputRotationOriginZ.property("quantity").Value)
        storeIfChanged(self.obj, 'RotationOrigin', rotation_origin)
        rotation_axis = FreeCAD.Vector(
            self.form.inputRotationAxisX.property("quantity").Value,
            self.form.inputRotationAxisY.property("quantity").Value,
            self.form.inputRotationAxisZ.property("quantity").Value)
        storeIfChanged(self.obj, 'RotationAxis', rotation_axis)

        storeIfChanged(self.obj, 'RelativeToFrame', self.form.cb_relative_srf.isChecked())

        # Pressure
        storeIfChanged(self.obj, 'Pressure', getQuantity(self.form.inputPressure))

        # Wall
        storeIfChanged(self.obj, 'SlipRatio', getQuantity(self.form.inputSlipRatio))
        storeIfChanged(self.obj, 'RoughnessHeight', getQuantity(self.form.inputRoughnessHeight))
        storeIfChanged(self.obj, 'RoughnessConstant', getQuantity(self.form.inputRoughnessConstant))

        # Thermal
        storeIfChanged(self.obj, 'Temperature', getQuantity(self.form.inputTemperature))
        storeIfChanged(self.obj, 'HeatFlux', getQuantity(self.form.inputHeatFlux))
        storeIfChanged(self.obj, 'Power', getQuantity(self.form.inputPower))
        storeIfChanged(self.obj, 'HeatTransferCoeff', getQuantity(self.form.inputHeatTransferCoeff))

        # Periodic
        storeIfChanged(self.obj, 'RotationalPeriodic', self.form.rb_rotational_periodic.isChecked())
        centre_of_rotation = FreeCAD.Vector(
            self.form.input_corx.property("quantity").Value,
            self.form.input_cory.property("quantity").Value,
            self.form.input_corz.property("quantity").Value)
        storeIfChanged(self.obj, 'PeriodicCentreOfRotation', centre_of_rotation)

        rotation_axis = FreeCAD.Vector(
            self.form.input_axisx.property("quantity").Value,
            self.form.input_axisy.property("quantity").Value,
            self.form.input_axisz.property("quantity").Value)
        storeIfChanged(self.obj, 'PeriodicCentreOfRotationAxis', rotation_axis)

        separation_vector = FreeCAD.Vector(
            self.form.input_sepx.property("quantity").Value,
            self.form.input_sepy.property("quantity").Value,
            self.form.input_sepz.property("quantity").Value)
        storeIfChanged(self.obj, 'PeriodicSeparationVector', separation_vector)

        storeIfChanged(self.obj, 'PeriodicPartner', self.form.comboBoxPeriodicPartner.currentText())
        storeIfChanged(self.obj, 'PeriodicMaster', self.form.radioButtonMasterPeriodic.isChecked())

        # Turbulence
        if self.turb_model in CfdFluidBoundary.TURBULENT_INLET_SPEC:
            turb_index = self.form.comboTurbulenceSpecification.currentIndex()
            storeIfChanged(self.obj, 'TurbulenceInletSpecification',
                           CfdFluidBoundary.TURBULENT_INLET_SPEC[self.turb_model][1][turb_index])
        else:
            storeIfChanged(self.obj, 'TurbulenceInletSpecification', self.obj.TurbulenceInletSpecification)
        storeIfChanged(self.obj, 'TurbulentKineticEnergy', getQuantity(self.form.inputKineticEnergy))
        storeIfChanged(self.obj, 'SpecificDissipationRate', getQuantity(self.form.inputSpecificDissipationRate))
        storeIfChanged(self.obj, 'DissipationRate', getQuantity(self.form.inputDissipationRate))
        storeIfChanged(self.obj, 'NuTilda', getQuantity(self.form.inputNuTilda))
        storeIfChanged(self.obj, 'Intermittency', getQuantity(self.form.inputGammaInt))
        storeIfChanged(self.obj, 'ReThetat', getQuantity(self.form.inputReThetat))
        storeIfChanged(self.obj, 'TurbulentViscosity', getQuantity(self.form.inputTurbulentViscosity))
        storeIfChanged(self.obj, 'kEqnTurbulentKineticEnergy', getQuantity(self.form.inputKineticEnergy))
        storeIfChanged(self.obj, 'kEqnTurbulentViscosity', getQuantity(self.form.inputTurbulentViscosity))
        storeIfChanged(self.obj, 'TurbulenceIntensityPercentage', getQuantity(self.form.inputIntensity))
        storeIfChanged(self.obj, 'TurbulenceLengthScale', getQuantity(self.form.inputLengthScale))

        # Multiphase
        storeIfChanged(self.obj, 'VolumeFractions', self.alphas)

        # Porous
        storeIfChanged(self.obj, 'PorousBaffleMethod',
                       CfdFluidBoundary.POROUS_METHODS[self.form.buttonGroupPorous.checkedId()])
        storeIfChanged(self.obj, 'PressureDropCoeff', getQuantity(self.form.inputPressureDropCoeff))
        storeIfChanged(self.obj, 'ScreenWireDiameter', getQuantity(self.form.inputWireDiameter))
        storeIfChanged(self.obj, 'ScreenSpacing', getQuantity(self.form.inputSpacing))

        # Only update references if changed
        if self.obj.ShapeRefs != self.ShapeRefsOrig:
            refstr = "FreeCAD.ActiveDocument.{}.ShapeRefs = [\n".format(self.obj.Name)
            refstr += ',\n'.join(
                "(FreeCAD.ActiveDocument.getObject('{}'), {})".format(ref[0].Name, ref[1]) for ref in self.obj.ShapeRefs)
            refstr += "]"
            FreeCADGui.doCommand(refstr)

        # Default boundary
        defaultBoundary = self.form.checkBoxDefaultBoundary.isChecked()
        storeIfChanged(self.obj, 'DefaultBoundary', defaultBoundary)
        if defaultBoundary:
            # Deactivate previous default boundary, if any
            boundaries = CfdTools.getCfdBoundaryGroup(CfdTools.getParentAnalysisObject(self.obj))
            for b in boundaries:
                if b.Name != self.obj.Name and b.DefaultBoundary:
                    FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.DefaultBoundary = False".format(b.Name))

        FreeCADGui.doCommand("FreeCAD.ActiveDocument.recompute()")

        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()

    def reject(self):
        self.obj.ShapeRefs = self.ShapeRefsOrig
        self.obj.BoundaryType = self.BoundaryTypeOrig
        self.obj.BoundarySubType = self.BoundarySubTypeOrig
        self.analysis_obj.NeedsMeshRewrite = self.NeedsMeshRewriteOrig
        self.analysis_obj.NeedsCaseRewrite = self.NeedsCaseRewriteOrig
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc_name = str(self.obj.Document.Name)
        FreeCAD.getDocument(doc_name).recompute()
        doc.resetEdit()
        return True

    def closing(self):
        # We call this from unsetEdit to ensure cleanup
        FreeCADGui.Selection.removeObserver(self)
        self.faceSelector.closing()
