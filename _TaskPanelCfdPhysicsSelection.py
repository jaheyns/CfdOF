# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2017-2018 Johan Heyns (CSIR) <jheyns@csir.co.za>        *
# *   Copyright (c) 2017-2018 Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>     *
# *   Copyright (c) 2017-2018 Alfred Bogaers (CSIR) <abogaers@csir.co.za>   *
# *   Copyright (c) 2019 Oliver Oxtoby <oliveroxtoby@gmail.com>             *
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
import CfdTools
from CfdTools import setQuantity
if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore, QtGui

RANS_MODELS = ['kOmegaSST', 'kEpsilon', 'SpalartAllmaras', 'kOmegaSSTLM']
DES_MODELS = ['kOmegaSSTDES', 'kOmegaSSTDDES', 'kOmegaSSTIDDES', 'SpalartAllmarasDES', 'SpalartAllmarasDDES',
              'SpalartAllmarasIDDES']
LES_MODELS = ['kEqn', 'Smagorinsky', 'WALE']

class _TaskPanelCfdPhysicsSelection:
    def __init__(self, obj):
        FreeCADGui.Selection.clearSelection()
        self.sel_server = None
        self.obj = obj
        self.form = FreeCADGui.PySideUic.loadUi(os.path.join(os.path.dirname(__file__), "core/gui/TaskPanelPhysics.ui"))

        self.form.radioButtonSteady.toggled.connect(self.updateUI)
        self.form.radioButtonTransient.toggled.connect(self.updateUI)
        self.form.radioButtonSinglePhase.toggled.connect(self.updateUI)
        self.form.radioButtonFreeSurface.toggled.connect(self.updateUI)
        self.form.radioButtonIncompressible.toggled.connect(self.updateUI)
        self.form.radioButtonCompressible.toggled.connect(self.updateUI)
        self.form.viscousCheckBox.stateChanged.connect(self.updateUI)
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

        # Flow
        if self.obj.Flow == 'Incompressible':
            self.form.radioButtonIncompressible.toggle()
        elif self.obj.Flow == 'Compressible':
            self.form.radioButtonCompressible.toggle()
            self.form.checkBoxHighMach.setChecked(False)
        elif self.obj.Flow == 'HighMachCompressible':
            self.form.radioButtonCompressible.toggle()
            self.form.checkBoxHighMach.setChecked(True)

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

        self.updateUI()

    def updateUI(self):
        self.form.TimeFrame.setVisible(True)
        self.form.FlowFrame.setVisible(True)
        self.form.turbulenceFrame.setVisible(True)

        # Steady / transient
        if self.form.radioButtonSteady.isChecked():
            self.form.radioButtonFreeSurface.setEnabled(False)
            self.form.radioButtonDES.setEnabled(False)
            self.form.radioButtonLES.setEnabled(False)
            if self.form.radioButtonFreeSurface.isChecked():
                self.form.radioButtonSinglePhase.toggle()
        else:
            self.form.radioButtonFreeSurface.setEnabled(True)
            self.form.radioButtonDES.setEnabled(True)
            self.form.radioButtonLES.setEnabled(True)

        # Gravity
        self.form.gravityFrame.setEnabled(
            self.form.radioButtonFreeSurface.isChecked() or
            (self.form.radioButtonCompressible.isChecked() and not self.form.checkBoxHighMach.isChecked()))

        # Free surface
        if self.form.radioButtonFreeSurface.isChecked():
            self.form.radioButtonCompressible.setEnabled(False)
            if self.form.radioButtonCompressible.isChecked():
                self.form.radioButtonIncompressible.toggle()
        else:
            self.form.radioButtonCompressible.setEnabled(True)

        # High Mach capability
        self.form.checkBoxHighMach.setEnabled(self.form.radioButtonCompressible.isChecked())

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

        FreeCADGui.doCommand("\nobj = FreeCAD.ActiveDocument.{}".format(self.obj.Name))
        if self.form.radioButtonSteady.isChecked():
            FreeCADGui.doCommand("obj.Time = 'Steady'")
        elif self.form.radioButtonTransient.isChecked():
            FreeCADGui.doCommand("obj.Time = 'Transient'")

        if self.form.radioButtonSinglePhase.isChecked():
            FreeCADGui.doCommand("obj.Phase = 'Single'")
        elif self.form.radioButtonFreeSurface.isChecked():
            FreeCADGui.doCommand("obj.Phase = 'FreeSurface'")

        if self.form.radioButtonIncompressible.isChecked():
            FreeCADGui.doCommand("obj.Flow = 'Incompressible'")
            FreeCADGui.doCommand("obj.Thermal = 'None'")
        elif self.form.radioButtonCompressible.isChecked():
            if self.form.checkBoxHighMach.isChecked():
                FreeCADGui.doCommand("obj.Flow = 'HighMachCompressible'")
            else:
                FreeCADGui.doCommand("obj.Flow = 'Compressible'")
            FreeCADGui.doCommand("obj.Thermal = 'Energy'")

        if self.form.viscousCheckBox.isChecked():
            if self.form.radioButtonLaminar.isChecked():
                FreeCADGui.doCommand("obj.Turbulence = 'Laminar'")
            elif self.form.radioButtonRANS.isChecked():
                FreeCADGui.doCommand("obj.Turbulence = 'RANS'")
                FreeCADGui.doCommand("obj.TurbulenceModel = '{}'".format(
                    self.form.turbulenceComboBox.currentText()))
            elif self.form.radioButtonDES.isChecked():
                FreeCADGui.doCommand("obj.Turbulence = 'DES'")
                FreeCADGui.doCommand("obj.TurbulenceModel = '{}'".format(
                    self.form.turbulenceComboBox.currentText()))
            elif self.form.radioButtonLES.isChecked():
                FreeCADGui.doCommand("obj.Turbulence = 'LES'")
                FreeCADGui.doCommand("obj.TurbulenceModel = '{}'".format(
                    self.form.turbulenceComboBox.currentText()))
        else:
            FreeCADGui.doCommand("obj.Turbulence = 'Inviscid'")

        FreeCADGui.doCommand("obj.gx = '{}'".format(self.form.gx.text()))
        FreeCADGui.doCommand("obj.gy = '{}'".format(self.form.gy.text()))
        FreeCADGui.doCommand("obj.gz = '{}'".format(self.form.gz.text()))

        if self.form.srfCheckBox.isChecked():
            FreeCADGui.doCommand("obj.SRFModelEnabled = {}".format(self.form.srfCheckBox.isChecked()))
            FreeCADGui.doCommand("obj.SRFModelRPM = '{}'".getQuantity(self.form.inputSRFModelRPM))
            FreeCADGui.doCommand("obj.SRFModelCoR.x "
                                 "= '{}'".format(self.form.inputSRFCoRx.property("quantity").Value))
            FreeCADGui.doCommand("obj.SRFModelCoR.y "
                                 "= '{}'".format(self.form.inputSRFCoRy.property("quantity").Value))
            FreeCADGui.doCommand("obj.SRFModelCoR.z "
                                 "= '{}'".format(self.form.inputSRFCoRz.property("quantity").Value))
            FreeCADGui.doCommand("obj.SRFModelAxis.x "
                                 "= '{}'".format(self.form.inputSRFAxisx.property("quantity").Value))
            FreeCADGui.doCommand("obj.SRFModelAxis.y "
                                 "= '{}'".format(self.form.inputSRFAxisy.property("quantity").Value))
            FreeCADGui.doCommand("obj.SRFModelAxis.z "
                                 "= '{}'".format(self.form.inputSRFAxisz.property("quantity").Value))

    def reject(self):
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()
