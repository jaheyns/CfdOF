# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileNotice: Part of the CfdOF addon.

################################################################################
#                                                                              #
#   Copyright (c) 2017 Alfred Bogaers (CSIR) <abogaers@csir.co.za>             #
#   Copyright (c) 2017 Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>               #
#   Copyright (c) 2017 Johan Heyns (CSIR) <jheyns@csir.co.za>                  #
#   Copyright (c) 2019-2022 Oliver Oxtoby <oliveroxtoby@gmail.com>             #
#   Copyright (c) 2022 Jonathan Bergh <bergh.jonathan@gmail.com>               #
#                                                                              #
#   This program is free software; you can redistribute it and/or              #
#   modify it under the terms of the GNU Lesser General Public                 #
#   License as published by the Free Software Foundation; either               #
#   version 3 of the License, or (at your option) any later version.           #
#                                                                              #
#   This program is distributed in the hope that it will be useful,            #
#   but WITHOUT ANY WARRANTY; without even the implied warranty of             #
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.                       #
#                                                                              #
#   See the GNU Lesser General Public License for more details.                #
#                                                                              #
#   You should have received a copy of the GNU Lesser General Public License   #
#   along with this program; if not, write to the Free Software Foundation,    #
#   Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.        #
#                                                                              #
################################################################################

import os
import os.path
import FreeCAD
if FreeCAD.GuiUp:
    import FreeCADGui
from CfdOF import CfdTools
from CfdOF.CfdTools import getQuantity, setQuantity, storeIfChanged


class TaskPanelCfdInitialiseInternalFlowField:
    def __init__(self, obj, physics_model, boundaries, material_objs):
        FreeCADGui.Selection.clearSelection()
        self.obj = obj
        self.physicsModel = physics_model
        self.boundaries = boundaries
        self.material_objs = material_objs

        self.form = FreeCADGui.PySideUic.loadUi(os.path.join(CfdTools.getModulePath(), 'Gui',
                                                             "TaskPanelCfdInitialiseInternalField.ui"))

        self.form.velocityFrame.setVisible(False)
        self.form.pressureFrame.setVisible(False)
        self.form.radioButtonPotentialFlowU.toggled.connect(self.radioChanged)
        self.form.radioButtonUseInletValuesU.toggled.connect(self.radioChanged)
        self.form.radioButtonPotentialFlowP.toggled.connect(self.radioChanged)
        self.form.radioButtonUseInletValuesP.toggled.connect(self.radioChanged)
        self.form.turbulencePropertiesFrame.setVisible(False)
        self.form.checkUseInletValuesThermal.toggled.connect(self.updateUi)
        self.form.checkUseInletValuesTurb.toggled.connect(self.updateUi)

        self.form.comboFluid.currentIndexChanged.connect(self.comboFluidChanged)
        self.form.inputVolumeFraction.valueChanged.connect(self.inputVolumeFractionChanged)

        self.form.radioButtonPotentialFlowU.setToolTip(
            "Initialise the velocity field using an incompressible, potential "
            "(irrotational) flow assumption.")
        self.form.radioButtonPotentialFlowP.setToolTip(
            "Initialise the pressure field using an incompressible, potential "
            "(irrotational) flow assumption.")

        self.alphas = {}
        self.load()

    def load(self):
        potential_u = self.obj.PotentialFlow
        potential_p = self.obj.PotentialFlowP
        use_inlet_U = self.obj.UseInletUValues
        use_outlet_P = self.obj.UseOutletPValue
        if potential_u:
            self.form.radioButtonPotentialFlowU.toggle()
        elif use_inlet_U:
            self.form.radioButtonUseInletValuesU.toggle()
        else:
            self.form.radioButtonSpecifyValuesU.toggle()
        if potential_p:
            self.form.radioButtonPotentialFlowP.toggle()
        elif use_outlet_P:
            self.form.radioButtonUseInletValuesP.toggle()
        else:
            self.form.radioButtonSpecifyValuesP.toggle()

        setQuantity(self.form.Ux, self.obj.Ux)
        setQuantity(self.form.Uy, self.obj.Uy)
        setQuantity(self.form.Uz, self.obj.Uz)
        setQuantity(self.form.pressure, self.obj.Pressure)

        # Add volume fraction fields
        self.alphas = self.obj.VolumeFractions
        if self.physicsModel.Phase != 'Single':
            mat_names = []
            for m in self.material_objs:
                mat_names.append(m.Label)
            self.form.comboFluid.clear()
            self.form.comboFluid.addItems(mat_names[:-1])
            self.comboFluidChanged(self.form.comboFluid.currentIndex())
        else:
            self.form.comboFluid.clear()

        # Use INLET turbulence values (k, omega, epsilon etc)
        use_inlet_turb = self.obj.UseInletTurbulenceValues
        self.form.checkUseInletValuesTurb.setChecked(use_inlet_turb)
        setQuantity(self.form.inputkEpsk, self.obj.k)
        setQuantity(self.form.inputEpsilon, self.obj.epsilon)
        setQuantity(self.form.inputkOmegak, self.obj.k)
        setQuantity(self.form.inputOmega, self.obj.omega)
        setQuantity(self.form.inputnuTilda, self.obj.nuTilda)
        setQuantity(self.form.inputGammaInt, self.obj.gammaInt)
        setQuantity(self.form.inputReThetat, self.obj.ReThetat)
        setQuantity(self.form.inputTurbulentViscosity, self.obj.nut)
        setQuantity(self.form.inputkEqnKineticEnergy, self.obj.k)
        setQuantity(self.form.inputkEqnTurbulentViscosity, self.obj.nut)

        use_inlet_temp = self.obj.UseInletTemperatureValue
        self.form.checkUseInletValuesThermal.setChecked(use_inlet_temp)
        setQuantity(self.form.inputTemperature, self.obj.Temperature)

        # Add any inlets to the lists
        for b in self.boundaries:
            if b.BoundaryType in ['inlet', 'open']:
                self.form.comboBoundaryU.addItem(b.Label, b.Name)
                self.form.comboBoundaryT.addItem(b.Label, b.Name)
                self.form.comboBoundaryTurb.addItem(b.Label, b.Name)
            if b.BoundaryType in ['inlet', 'outlet', 'open']:
                self.form.comboBoundaryP.addItem(b.Label, b.Name)
        if self.obj.BoundaryU is not None:
            self.form.comboBoundaryU.setCurrentIndex(self.form.comboBoundaryU.findData(self.obj.BoundaryU.Name))
        if self.obj.BoundaryP is not None:
            self.form.comboBoundaryP.setCurrentIndex(self.form.comboBoundaryP.findData(self.obj.BoundaryP.Name))
        if self.obj.BoundaryT is not None:
            self.form.comboBoundaryT.setCurrentIndex(self.form.comboBoundaryT.findData(self.obj.BoundaryT.Name))
        if self.obj.BoundaryTurb is not None:
            self.form.comboBoundaryTurb.setCurrentIndex(self.form.comboBoundaryTurb.findData(self.obj.BoundaryTurb.Name))

        self.updateUi()

    def updateUi(self):

        # General
        potential_flow = self.form.radioButtonPotentialFlowU.isChecked()
        potential_flow_P = self.form.radioButtonPotentialFlowP.isChecked()
        use_inlet_U = self.form.radioButtonUseInletValuesU.isChecked()
        use_outlet_P = self.form.radioButtonUseInletValuesP.isChecked()
        use_inlet_turb = self.form.checkUseInletValuesTurb.isChecked()
        use_inlet_temp = self.form.checkUseInletValuesThermal.isChecked()
        self.form.velocityFrame.setVisible(not (potential_flow or use_inlet_U))
        self.form.pressureFrame.setVisible(not (potential_flow_P or use_outlet_P))

        # Multiphase
        if self.physicsModel.Phase != 'Single':
            self.form.volumeFractionsFrame.setVisible(True)
        else:
            self.form.volumeFractionsFrame.setVisible(False)

        # Turbulence
        if self.physicsModel.Turbulence in ['RANS', 'DES', 'LES']:
            self.form.turbulencePropertiesFrame.setVisible(True)
        else:
            self.form.turbulencePropertiesFrame.setVisible(False)

        # Thermal / energy
        if self.physicsModel.Flow != 'Isothermal':
            self.form.energyFrame.setVisible(not use_inlet_temp)
        else:
            self.form.thermalPropertiesFrame.setVisible(False)

        self.form.comboBoundaryU.setVisible(use_inlet_U)
        self.form.comboBoundaryP.setVisible(use_outlet_P)
        self.form.comboBoundaryT.setVisible(use_inlet_temp)
        self.form.comboBoundaryTurb.setVisible(use_inlet_turb)

        potlU = self.form.radioButtonPotentialFlowU.isChecked()
        self.form.radioButtonPotentialFlowP.setEnabled(potlU)
        if self.form.radioButtonPotentialFlowP.isChecked() and not potlU:
            self.form.radioButtonSpecifyValuesP.toggle()

        self.form.kEpsilonFrame.setVisible(False)
        self.form.kOmegaSSTFrame.setVisible(False)
        self.form.SpalartAllmarasFrame.setVisible(False)
        self.form.kOmegaSSTLMFrame.setVisible(False)
        self.form.lesModelsFrame.setVisible(False)
        self.form.leskEqnFrame.setVisible(False)

        # RANS
        if self.physicsModel.TurbulenceModel == 'kOmegaSST':
            self.form.kOmegaSSTFrame.setVisible(not use_inlet_turb)
        elif self.physicsModel.TurbulenceModel == 'kEpsilon':
            self.form.kEpsilonFrame.setVisible(not use_inlet_turb)
        elif self.physicsModel.TurbulenceModel == 'SpalartAllmaras':
            self.form.SpalartAllmarasFrame.setVisible(not use_inlet_turb)
        elif self.physicsModel.TurbulenceModel == 'kOmegaSSTLM':
            self.form.kOmegaSSTFrame.setVisible(not use_inlet_turb)
            self.form.kOmegaSSTLMFrame.setVisible(not use_inlet_turb)
        #DES
        elif self.physicsModel.TurbulenceModel == 'kOmegaSSTDES':
            self.form.kOmegaSSTFrame.setVisible(not use_inlet_turb)
        elif self.physicsModel.TurbulenceModel == 'kOmegaSSTDDES':
            self.form.kOmegaSSTFrame.setVisible(not use_inlet_turb)
        elif self.physicsModel.TurbulenceModel == 'kOmegaSSTIDDES':
            self.form.kOmegaSSTFrame.setVisible(not use_inlet_turb)
        elif self.physicsModel.TurbulenceModel == 'SpalartAllmarasDES':
            self.form.SpalartAllmarasFrame.setVisible(not use_inlet_turb)
        elif self.physicsModel.TurbulenceModel == 'SpalartAllmarasDDES':
            self.form.SpalartAllmarasFrame.setVisible(not use_inlet_turb)
        elif self.physicsModel.TurbulenceModel == 'SpalartAllmarasIDDES':
            self.form.SpalartAllmarasFrame.setVisible(not use_inlet_turb)
        #LES
        elif self.physicsModel.TurbulenceModel == 'Smagorinsky' or \
            self.physicsModel.TurbulenceModel == 'WALE':
            self.form.lesModelsFrame.setVisible(not use_inlet_turb)
        elif self.physicsModel.TurbulenceModel == 'kEqn':
            self.form.leskEqnFrame.setVisible(not use_inlet_turb)

    def radioChanged(self):
        self.updateUi()

    def getMaterialName(self, index):
        return self.material_objs[index].Label

    def comboFluidChanged(self, index):
        setQuantity(self.form.inputVolumeFraction, self.alphas.get(self.getMaterialName(index), '0.0'))

    def inputVolumeFractionChanged(self):
        self.alphas[self.form.comboFluid.currentText()] = getQuantity(self.form.inputVolumeFraction)

    def accept(self):
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()

        # Velocity
        storeIfChanged(self.obj, 'PotentialFlow', self.form.radioButtonPotentialFlowU.isChecked())
        storeIfChanged(self.obj, 'UseInletUValues', self.form.radioButtonUseInletValuesU.isChecked())
        storeIfChanged(self.obj, 'Ux', getQuantity(self.form.Ux))
        storeIfChanged(self.obj, 'Uy', getQuantity(self.form.Uy))
        storeIfChanged(self.obj, 'Uz', getQuantity(self.form.Uz))

        # Pressure
        storeIfChanged(self.obj, 'UseOutletPValue', self.form.radioButtonUseInletValuesP.isChecked())
        storeIfChanged(self.obj, 'PotentialFlowP', self.form.radioButtonPotentialFlowP.isChecked())
        storeIfChanged(self.obj, 'Pressure', getQuantity(self.form.pressure))

        # Multiphase
        storeIfChanged(self.obj, 'VolumeFractions', self.alphas)

        # Thermal
        storeIfChanged(self.obj, 'UseInletTemperatureValue', self.form.checkUseInletValuesThermal.isChecked())
        storeIfChanged(self.obj, 'Temperature', getQuantity(self.form.inputTemperature))

        # Turbulence
        storeIfChanged(self.obj, 'UseInletTurbulenceValues', self.form.checkUseInletValuesTurb.isChecked())
        if self.form.kEpsilonFrame.isVisible():
            storeIfChanged(self.obj, 'k', getQuantity(self.form.inputkEpsk))
        storeIfChanged(self.obj, 'epsilon', getQuantity(self.form.inputEpsilon))
        if self.form.kOmegaSSTFrame.isVisible():
            storeIfChanged(self.obj, 'k', getQuantity(self.form.inputkOmegak))
        storeIfChanged(self.obj, 'omega', getQuantity(self.form.inputOmega))
        storeIfChanged(self.obj, 'nuTilda', getQuantity(self.form.inputnuTilda))
        storeIfChanged(self.obj, 'gammaInt', getQuantity(self.form.inputGammaInt))
        storeIfChanged(self.obj, 'ReThetat', getQuantity(self.form.inputReThetat))
        if self.form.lesModelsFrame.isVisible():        
            storeIfChanged(self.obj, 'nut', getQuantity(self.form.inputTurbulentViscosity))
        if self.form.leskEqnFrame.isVisible():
            storeIfChanged(self.obj, 'k', getQuantity(self.form.inputkEqnKineticEnergy))
            storeIfChanged(self.obj, 'nut', getQuantity(self.form.inputkEqnTurbulentViscosity))

        boundaryU = self.form.comboBoundaryU.currentData()
        boundaryP = self.form.comboBoundaryP.currentData()
        boundaryT = self.form.comboBoundaryT.currentData()
        boundaryTurb = self.form.comboBoundaryTurb.currentData()

        if boundaryU and self.obj.UseInletUValues:
            if not self.obj.BoundaryU or boundaryU != self.obj.BoundaryU.Name:
                FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.BoundaryU = FreeCAD.ActiveDocument.{}".format(
                    self.obj.Name, boundaryU))
        elif self.obj.BoundaryU:
            FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.BoundaryU = None".format(self.obj.Name))
        if boundaryP and self.obj.UseOutletPValue:
            if not self.obj.BoundaryP or boundaryP != self.obj.BoundaryP.Name:
                FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.BoundaryP = FreeCAD.ActiveDocument.{}".format(
                    self.obj.Name, boundaryP))
        elif self.obj.BoundaryP:
            FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.BoundaryP = None".format(self.obj.Name))
        if boundaryT and self.obj.UseInletTemperatureValue:
            if not self.obj.BoundaryT or boundaryT != self.obj.BoundaryT.Name:
                FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.BoundaryT = FreeCAD.ActiveDocument.{}".format(
                    self.obj.Name, boundaryT))
        elif self.obj.BoundaryT:
            FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.BoundaryT = None".format(self.obj.Name))
        if boundaryTurb and self.obj.UseInletTurbulenceValues:
            if not self.obj.BoundaryTurb or boundaryTurb != self.obj.BoundaryTurb.Name:
                FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.BoundaryTurb = FreeCAD.ActiveDocument.{}".format(
                    self.obj.Name, boundaryTurb))
        elif self.obj.BoundaryTurb:
            FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.BoundaryTurb = None".format(self.obj.Name))

    def reject(self):
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()

    def closing(self):
        # We call this from unsetEdit to allow cleanup
        return