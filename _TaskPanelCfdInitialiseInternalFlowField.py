# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2013-2015 - Juergen Riegel <FreeCAD@juergen-riegel.net> *
# *   Copyright (c) 2017 Alfred Bogaers (CSIR) <abogaers@csir.co.za>        *
# *   Copyright (c) 2017 Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>          *
# *   Copyright (c) 2017 Johan Heyns (CSIR) <jheyns@csir.co.za>             *
# *   Copyright (c) 2019-2020 Oliver Oxtoby <oliveroxtoby@gmail.com>        *
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

import FreeCAD
import os
import os.path
from CfdTools import getQuantity, setQuantity
if FreeCAD.GuiUp:
    import FreeCADGui


class _TaskPanelCfdInitialiseInternalFlowField:
    def __init__(self, obj, physics_model, boundaries, material_objs):
        FreeCADGui.Selection.clearSelection()
        self.obj = obj
        self.physicsModel = physics_model
        self.boundaries = boundaries
        self.material_objs = material_objs

        self.form = FreeCADGui.PySideUic.loadUi(os.path.join(os.path.dirname(__file__),
                                                             "core/gui/TaskPanelCfdInitialiseInternalField.ui"))

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
        setQuantity(self.form.inputk, self.obj.k)
        setQuantity(self.form.inputOmega, self.obj.omega)
        setQuantity(self.form.inputEpsilon, self.obj.epsilon)
        setQuantity(self.form.inputnuTilda, self.obj.nuTilda)

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
        potential_flow = self.form.radioButtonPotentialFlowU.isChecked()
        potential_flow_P = self.form.radioButtonPotentialFlowP.isChecked()
        use_inlet_U = self.form.radioButtonUseInletValuesU.isChecked()
        use_outlet_P = self.form.radioButtonUseInletValuesP.isChecked()
        use_inlet_turb = self.form.checkUseInletValuesTurb.isChecked()
        use_inlet_temp = self.form.checkUseInletValuesThermal.isChecked()
        self.form.velocityFrame.setVisible(not (potential_flow or use_inlet_U))
        self.form.pressureFrame.setVisible(not (potential_flow_P or use_outlet_P))

        if self.physicsModel.Phase != 'Single':
            self.form.volumeFractionsFrame.setVisible(True)
        else:
            self.form.volumeFractionsFrame.setVisible(False)

        if self.physicsModel.Turbulence in ['RANS', 'LES']:
            self.form.turbulencePropertiesFrame.setVisible(True)
        else:
            self.form.turbulencePropertiesFrame.setVisible(False)

        if self.physicsModel.Thermal == 'Energy':
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
        if self.physicsModel.TurbulenceModel == 'kOmegaSST':
            self.form.kOmegaSSTFrame.setVisible(not use_inlet_turb)
        elif self.physicsModel.TurbulenceModel == 'kEpsilon':
            self.form.kEpsilonFrame.setVisible(not use_inlet_turb)
        elif self.physicsModel.TurbulenceModel == 'SpalartAllmaras':
            self.form.SpalartAllmarasFrame.setVisible(not use_inlet_turb)
        elif self.physicsModel.TurbulenceModel == 'kOmegaSSTLM':
            self.form.kOmegaSSTFrame.setVisible(not use_inlet_turb)
            self.form.kOmegaSSTLMFrame.setVisible(not use_inlet_turb)

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

        FreeCADGui.doCommand("\ninit = FreeCAD.ActiveDocument.{}".format(self.obj.Name))
        FreeCADGui.doCommand("init.PotentialFlow = {}".format(self.form.radioButtonPotentialFlowU.isChecked()))
        FreeCADGui.doCommand("init.UseInletUValues = {}".format(self.form.radioButtonUseInletValuesU.isChecked()))
        FreeCADGui.doCommand("init.Ux = '{}'".format(getQuantity(self.form.Ux)))
        FreeCADGui.doCommand("init.Uy = '{}'".format(getQuantity(self.form.Uy)))
        FreeCADGui.doCommand("init.Uz = '{}'".format(getQuantity(self.form.Uz)))
        FreeCADGui.doCommand("init.UseOutletPValue = {}".format(self.form.radioButtonUseInletValuesP.isChecked()))
        FreeCADGui.doCommand("init.PotentialFlowP = {}".format(self.form.radioButtonPotentialFlowP.isChecked()))
        FreeCADGui.doCommand("init.Pressure = '{}'".format(getQuantity(self.form.pressure)))
        FreeCADGui.doCommand("init.VolumeFractions = {}".format(self.alphas))
        FreeCADGui.doCommand("init.UseInletTemperatureValue "
                             "= {}".format(self.form.checkUseInletValuesThermal.isChecked()))
        FreeCADGui.doCommand("init.Temperature "
                             "= '{}'".format(getQuantity(self.form.inputTemperature)))
        FreeCADGui.doCommand("init.UseInletTurbulenceValues "
                             "= {}".format(self.form.checkUseInletValuesTurb.isChecked()))
        FreeCADGui.doCommand("init.nuTilda = '{}'".format(getQuantity(self.form.inputnuTilda)))
        FreeCADGui.doCommand("init.epsilon = '{}'".format(getQuantity(self.form.inputEpsilon)))
        FreeCADGui.doCommand("init.omega = '{}'".format(getQuantity(self.form.inputOmega)))
        FreeCADGui.doCommand("init.k = '{}'".format(getQuantity(self.form.inputk)))
        FreeCADGui.doCommand("init.gammaInt = '{}'".format(getQuantity(self.form.inputGammaInt)))
        FreeCADGui.doCommand("init.ReThetat = '{}'".format(getQuantity(self.form.inputReThetat)))

        boundaryU = self.form.comboBoundaryU.currentData()
        boundaryP = self.form.comboBoundaryP.currentData()
        boundaryT = self.form.comboBoundaryT.currentData()
        boundaryTurb = self.form.comboBoundaryTurb.currentData()

        if boundaryU:
            FreeCADGui.doCommand("init.BoundaryU = FreeCAD.ActiveDocument.{}".format(boundaryU))
        else:
            FreeCADGui.doCommand("init.BoundaryU = None")
        if boundaryP:
            FreeCADGui.doCommand("init.BoundaryP = FreeCAD.ActiveDocument.{}".format(boundaryP))
        else:
            FreeCADGui.doCommand("init.BoundaryP = None")
        if boundaryT:
            FreeCADGui.doCommand("init.BoundaryT = FreeCAD.ActiveDocument.{}".format(boundaryT))
        else:
            FreeCADGui.doCommand("init.BoundaryT = None")
        if boundaryTurb:
            FreeCADGui.doCommand("init.BoundaryTurb = FreeCAD.ActiveDocument.{}".format(boundaryTurb))
        else:
            FreeCADGui.doCommand("init.BoundaryTurb = None")

    def reject(self):
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()
