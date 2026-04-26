# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: © 2017 Johan Heyns (CSIR) <jheyns@csir.co.za>
# SPDX-FileCopyrightText: © 2017 Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>
# SPDX-FileCopyrightText: © 2017 Alfred Bogaers (CSIR) <abogaers@csir.co.za>
# SPDX-FileCopyrightText: © 2019 Oliver Oxtoby <oliveroxtoby@gmail.com>
# SPDX-FileCopyrightText: © 2022 Jonathan Bergh <bergh.jonathan@gmail.com>
# SPDX-FileNotice: Part of the CfdOF addon.

################################################################################
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


RANS_MODELS = ['kOmegaSST', 'kEpsilon', 'SpalartAllmaras', 'kOmegaSSTLM']
DES_MODELS = ['kOmegaSSTDES', 'kOmegaSSTDDES', 'kOmegaSSTIDDES', 'SpalartAllmarasDES', 'SpalartAllmarasDDES',
              'SpalartAllmarasIDDES']
LES_MODELS = ['kEqn', 'Smagorinsky', 'WALE']


class TaskPanelCfdPhysicsSelection:
    def __init__(self, obj):
        FreeCADGui.Selection.clearSelection()
        self.sel_server = None
        self.obj = obj
        self.form = FreeCADGui.PySideUic.loadUi(os.path.join(CfdTools.getModulePath(), 'Gui', "TaskPanelPhysics.ui"))

        self.form.radioButtonSteady.toggled.connect(self.updateUI)
        self.form.radioButtonTransient.toggled.connect(self.updateUI)
        self.form.radioButtonSinglePhase.toggled.connect(self.updateUI)
        self.form.radioButtonFreeSurface.toggled.connect(self.updateUI)
        self.form.radioButtonMultiRegion.toggled.connect(self.updateUI)
        if hasattr(self.form.checkBoxIsothermal, "checkStateChanged"):
            self.form.checkBoxIsothermal.checkStateChanged.connect(self.updateUI)
            self.form.viscousCheckBox.checkStateChanged.connect(self.updateUI)
            self.form.srfCheckBox.checkStateChanged.connect(self.updateUI)
        else:
            self.form.checkBoxIsothermal.stateChanged.connect(self.updateUI)
            self.form.viscousCheckBox.stateChanged.connect(self.updateUI)
            self.form.srfCheckBox.stateChanged.connect(self.updateUI)
        self.form.radioButtonLaminar.toggled.connect(self.updateUI)
        self.form.radioButtonRANS.toggled.connect(self.updateUI)
        self.form.radioButtonDES.toggled.connect(self.updateUI)
        self.form.radioButtonLES.toggled.connect(self.updateUI)

        self.load()

    def load(self):

        # Time
        if self.obj.Time == 'Steady':
            self.form.radioButtonSteady.toggle()
        elif self.obj.Time == 'Transient':
            self.form.radioButtonTransient.toggle()

        # Phase
        if self.obj.Phase == 'Single':
            self.form.radioButtonSinglePhase.toggle()
        elif self.obj.Phase == 'FreeSurface':
            self.form.radioButtonFreeSurface.toggle()
        elif self.obj.Phase == 'MultiRegion':
            self.form.radioButtonMultiRegion.toggle()

        # Flow
        self.form.checkBoxIsothermal.setChecked(self.obj.Flow == 'Isothermal')
        self.form.checkBoxHighMach.setChecked(self.obj.Flow == 'HighMachCompressible')

        # Turbulence
        if self.obj.Turbulence == 'Inviscid':
            self.form.viscousCheckBox.setChecked(False)
            self.form.radioButtonLaminar.toggle()
        if self.obj.Turbulence == 'Laminar':
            self.form.viscousCheckBox.setChecked(True)
            self.form.radioButtonLaminar.toggle()
        elif self.obj.Turbulence == 'RANS':
            self.form.viscousCheckBox.setChecked(True)
            self.form.radioButtonRANS.toggle()
        elif self.obj.Turbulence == 'DES':
            self.form.viscousCheckBox.setChecked(True)
            self.form.radioButtonDES.toggle()
        elif self.obj.Turbulence == 'LES':
            self.form.viscousCheckBox.setChecked(True)
            self.form.radioButtonLES.toggle()

        # Gravity
        setQuantity(self.form.gx, self.obj.gx)
        setQuantity(self.form.gy, self.obj.gy)
        setQuantity(self.form.gz, self.obj.gz)

        # SRF model
        self.form.srfCheckBox.setChecked(self.obj.SRFModelEnabled)

        setQuantity(self.form.inputSRFCoRx, self.obj.SRFModelCoR.x)
        setQuantity(self.form.inputSRFCoRy, self.obj.SRFModelCoR.y)
        setQuantity(self.form.inputSRFCoRz, self.obj.SRFModelCoR.z)

        setQuantity(self.form.inputSRFAxisx, self.obj.SRFModelAxis.x)
        setQuantity(self.form.inputSRFAxisy, self.obj.SRFModelAxis.y)
        setQuantity(self.form.inputSRFAxisz, self.obj.SRFModelAxis.z)

        setQuantity(self.form.inputSRFRPM, self.obj.SRFModelRPM)

        self.updateUI()

    def updateUI(self):
        self.form.TimeFrame.setVisible(True)
        self.form.FlowFrame.setVisible(True)
        self.form.turbulenceFrame.setVisible(True)

        multi_region = self.form.radioButtonMultiRegion.isChecked()

        # Steady / transient
        if self.form.radioButtonSteady.isChecked():
            free_surface_allowed = not multi_region
            self.form.radioButtonFreeSurface.setEnabled(free_surface_allowed)
            if self.form.radioButtonDES.isChecked() or self.form.radioButtonLES.isChecked():
                self.form.radioButtonRANS.toggle()
            self.form.radioButtonDES.setEnabled(False)
            self.form.radioButtonLES.setEnabled(False)
            if self.form.radioButtonFreeSurface.isChecked():
                self.form.radioButtonSinglePhase.toggle()
        else:
            self.form.radioButtonFreeSurface.setEnabled(not multi_region)
            self.form.radioButtonDES.setEnabled(True)
            self.form.radioButtonLES.setEnabled(True)

        # Multi-region forces NonIsothermal flow and disables flow override controls
        if multi_region:
            self.form.checkBoxIsothermal.setChecked(False)
            self.form.checkBoxIsothermal.setEnabled(False)
            self.form.checkBoxHighMach.setChecked(False)
            self.form.checkBoxHighMach.setEnabled(False)
        else:
            self.form.checkBoxHighMach.setEnabled(not self.form.checkBoxIsothermal.isChecked())

        # Gravity
        self.form.gravityFrame.setEnabled(
            self.form.radioButtonFreeSurface.isChecked() or multi_region or
            (not self.form.checkBoxIsothermal.isChecked() and not self.form.checkBoxHighMach.isChecked()))

        # SRF model
        srf_capable = (self.form.radioButtonSteady.isChecked() and self.form.checkBoxIsothermal.isChecked()
                       and not multi_region)
        srf_should_be_unchecked = ((not self.form.checkBoxIsothermal.isChecked())
                                   or self.form.radioButtonTransient.isChecked()
                                   or self.form.radioButtonFreeSurface.isChecked()
                                   or multi_region)
        self.form.srfCheckBox.setEnabled(srf_capable)
        if srf_should_be_unchecked:
            self.form.srfCheckBox.setChecked(False)
        self.form.srfFrame.setEnabled(self.form.srfCheckBox.isChecked())

        # Free surface forces isothermal (only when not multi-region)
        if self.form.radioButtonFreeSurface.isChecked():
            self.form.checkBoxIsothermal.setChecked(True)
            self.form.checkBoxIsothermal.setEnabled(False)
        elif not multi_region:
            self.form.checkBoxIsothermal.setEnabled(True)

        # High Mach capability (only when not multi-region)
        if not multi_region:
            self.form.checkBoxHighMach.setEnabled(not self.form.checkBoxIsothermal.isChecked())
            if self.form.checkBoxIsothermal.isChecked():
                self.form.checkBoxHighMach.setChecked(False)

        # Viscous 
        if self.form.viscousCheckBox.isChecked():
            self.form.turbulenceFrame.setVisible(True)
            # RANS
            if self.form.radioButtonRANS.isChecked():
                self.form.turbulenceComboBox.clear()
                self.form.turbulenceComboBox.addItems(RANS_MODELS)
                ti = CfdTools.indexOrDefault(RANS_MODELS, self.obj.TurbulenceModel, 0)
                self.form.turbulenceComboBox.setCurrentIndex(ti)
                self.form.turbulenceModelFrame.setVisible(True)
            #DES
            elif self.form.radioButtonDES.isChecked():
                self.form.turbulenceComboBox.clear()
                self.form.turbulenceComboBox.addItems(DES_MODELS)
                ti = CfdTools.indexOrDefault(DES_MODELS, self.obj.TurbulenceModel, 0)
                self.form.turbulenceComboBox.setCurrentIndex(ti)
                self.form.turbulenceModelFrame.setVisible(True)
            # LES
            elif self.form.radioButtonLES.isChecked():
                self.form.turbulenceComboBox.clear()
                self.form.turbulenceComboBox.addItems(LES_MODELS)
                ti = CfdTools.indexOrDefault(LES_MODELS, self.obj.TurbulenceModel, 0)
                self.form.turbulenceComboBox.setCurrentIndex(ti)
                self.form.turbulenceModelFrame.setVisible(True)
            else:
                self.form.turbulenceModelFrame.setVisible(False)
                self.form.turbulenceComboBox.clear()
        else:
            self.form.turbulenceFrame.setVisible(False)
            self.form.turbulenceModelFrame.setVisible(False)

    def accept(self):
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()

        if self.form.radioButtonSteady.isChecked():
            storeIfChanged(self.obj, 'Time', 'Steady')
        elif self.form.radioButtonTransient.isChecked():
            storeIfChanged(self.obj, 'Time', 'Transient')

        if self.form.radioButtonSinglePhase.isChecked():
            storeIfChanged(self.obj, 'Phase', 'Single')
        elif self.form.radioButtonFreeSurface.isChecked():
            storeIfChanged(self.obj, 'Phase', 'FreeSurface')
        elif self.form.radioButtonMultiRegion.isChecked():
            storeIfChanged(self.obj, 'Phase', 'MultiRegion')

        if self.form.checkBoxIsothermal.isChecked():
            storeIfChanged(self.obj, 'Flow', 'Isothermal')
        elif not self.form.checkBoxIsothermal.isChecked():
            if self.form.checkBoxHighMach.isChecked():
                storeIfChanged(self.obj, 'Flow', 'HighMachCompressible')
            else:
                storeIfChanged(self.obj, 'Flow', 'NonIsothermal')

        if self.form.viscousCheckBox.isChecked():
            if self.form.radioButtonLaminar.isChecked():
                storeIfChanged(self.obj, 'Turbulence', 'Laminar')
            else:
                if self.form.radioButtonRANS.isChecked():
                    storeIfChanged(self.obj, 'Turbulence', 'RANS')
                elif self.form.radioButtonDES.isChecked():
                    storeIfChanged(self.obj, 'Turbulence', 'DES')
                elif self.form.radioButtonLES.isChecked():
                    storeIfChanged(self.obj, 'Turbulence', 'LES')
                storeIfChanged(self.obj, 'TurbulenceModel', self.form.turbulenceComboBox.currentText())
        else:
            storeIfChanged(self.obj, 'Turbulence', 'Inviscid')

        storeIfChanged(self.obj, 'gx', getQuantity(self.form.gx))
        storeIfChanged(self.obj, 'gy', getQuantity(self.form.gy))
        storeIfChanged(self.obj, 'gz', getQuantity(self.form.gz))

        storeIfChanged(self.obj, 'SRFModelEnabled', self.form.srfCheckBox.isChecked())
        if self.form.srfCheckBox.isChecked():
            storeIfChanged(self.obj, 'SRFModelRPM', self.form.inputSRFRPM.text())
            centre_of_rotation = FreeCAD.Vector(
                self.form.inputSRFCoRx.property("quantity").Value,
                self.form.inputSRFCoRy.property("quantity").Value,
                self.form.inputSRFCoRz.property("quantity").Value)
            storeIfChanged(self.obj, 'SRFModelCoR', centre_of_rotation)
            model_axis = FreeCAD.Vector(
                self.form.inputSRFAxisx.property("quantity").Value,
                self.form.inputSRFAxisy.property("quantity").Value,
                self.form.inputSRFAxisz.property("quantity").Value)
            storeIfChanged(self.obj, 'SRFModelAxis', model_axis)

    def reject(self):
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()

    def closing(self):
        # We call this from unsetEdit to allow cleanup
        return
