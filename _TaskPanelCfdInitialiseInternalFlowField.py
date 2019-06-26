# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2013-2015 - Juergen Riegel <FreeCAD@juergen-riegel.net> *
# *   Copyright (c) 2017 Alfred Bogaers (CSIR) <abogaers@csir.co.za>        *
# *   Copyright (c) 2017 Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>          *
# *   Copyright (c) 2017 Johan Heyns (CSIR) <jheyns@csir.co.za>             *
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
                                                "TaskPanelCfdInitialiseInternalField.ui"))

        self.form.basicPropertiesFrame.setVisible(False)
        self.form.radioButtonPotentialFlow.toggled.connect(self.radioUPChanged)
        self.form.radioButtonUseInletValuesUP.toggled.connect(self.radioUPChanged)
        self.form.turbulencePropertiesFrame.setVisible(False)
        self.form.checkUseInletValuesThermal.toggled.connect(self.updateUi)
        self.form.checkUseInletValues.toggled.connect(self.updateUi)

        self.form.comboFluid.currentIndexChanged.connect(self.comboFluidChanged)
        self.form.inputVolumeFraction.valueChanged.connect(self.inputVolumeFractionChanged)

        self.form.radioButtonPotentialFlow.setToolTip(
            "Initialise the velocity field using an incompressible, potential "
            "(irrotational) flow assumption.")

        self.alphas = {}
        self.load()

    def load(self):
        potential_foam = self.obj.PotentialFoam
        use_inlet_UP = self.obj.UseInletUPValues
        if potential_foam:
            self.form.radioButtonPotentialFlow.toggle()
        elif use_inlet_UP:
            self.form.radioButtonUseInletValuesUP.toggle()
        else:
            self.form.radioButtonSpecifyValues.toggle()

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

        use_inlet_turb = self.obj.UseInletTurbulenceValues
        self.form.checkUseInletValues.setChecked(use_inlet_turb)
        setQuantity(self.form.inputk, self.obj.k)
        setQuantity(self.form.inputOmega, self.obj.omega)

        use_inlet_temp = self.obj.UseInletTemperatureValues
        self.form.checkUseInletValuesThermal.setChecked(use_inlet_temp)
        setQuantity(self.form.inputTemperature, self.obj.Temperature)

        # Add any inlets to the list
        for b in self.boundaries:
            if b.BoundaryType in ['inlet', 'open']:
                self.form.comboInlets.addItem(b.Label, b.Name)
        self.form.comboInlets.setCurrentIndex(self.form.comboInlets.findData(self.obj.Inlet))

        self.updateUi()

    def updateUi(self):
        potential_foam = self.form.radioButtonPotentialFlow.isChecked()
        use_inlet_UP = self.form.radioButtonUseInletValuesUP.isChecked()
        use_inlet_turb = self.form.checkUseInletValues.isChecked()
        use_inlet_temp = self.form.checkUseInletValuesThermal.isChecked()
        self.form.basicPropertiesFrame.setVisible(not (potential_foam or use_inlet_UP))

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

        self.form.frameInlets.setVisible(
            (use_inlet_UP or use_inlet_turb or use_inlet_temp) and self.form.comboInlets.count() > 1)
        self.form.kEpsilonFrame.setVisible(False)
        self.form.kOmegaSSTFrame.setVisible(False)
        self.form.SpalartAlmerasFrame.setVisible(False)
        if self.physicsModel.TurbulenceModel == 'kOmegaSST':
            self.form.kOmegaSSTFrame.setVisible(not use_inlet_turb)

    def radioUPChanged(self):
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
        FreeCADGui.doCommand("init.PotentialFoam = {}".format(self.form.radioButtonPotentialFlow.isChecked()))
        FreeCADGui.doCommand("init.UseInletUPValues = {}".format(self.form.radioButtonUseInletValuesUP.isChecked()))
        FreeCADGui.doCommand("init.Ux = '{}'".format(getQuantity(self.form.Ux)))
        FreeCADGui.doCommand("init.Uy = '{}'".format(getQuantity(self.form.Uy)))
        FreeCADGui.doCommand("init.Uz = '{}'".format(getQuantity(self.form.Uz)))
        FreeCADGui.doCommand("init.Pressure = '{}'".format(getQuantity(self.form.pressure)))
        FreeCADGui.doCommand("init.VolumeFractions = {}".format(self.alphas))
        FreeCADGui.doCommand("init.UseInletTemperatureValues "
                             "= {}".format(self.form.checkUseInletValuesThermal.isChecked()))
        FreeCADGui.doCommand("init.Temperature "
                             "= '{}'".format(getQuantity(self.form.inputTemperature)))
        FreeCADGui.doCommand("init.UseInletTurbulenceValues "
                             "= {}".format(self.form.checkUseInletValues.isChecked()))
        FreeCADGui.doCommand("init.omega = '{}'".format(getQuantity(self.form.inputOmega)))
        FreeCADGui.doCommand("init.k = '{}'".format(getQuantity(self.form.inputk)))
        inlet = self.form.comboInlets.currentData()
        if inlet:
            FreeCADGui.doCommand("init.Inlet = FreeCAD.ActiveDocument.{}".format(inlet))
        else:
            FreeCADGui.doCommand("init.Inlet = None")

    def reject(self):
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()
