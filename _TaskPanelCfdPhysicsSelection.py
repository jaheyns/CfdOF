# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2017-2018                                               *
# *   Alfred Bogaers (CSIR) <abogaers@csir.co.za>                           *
# *   Johan Heyns (CSIR) <jheyns@csir.co.za>                                *
# *   Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>                             *
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

"""
UI for CFD PhysicsModel objects allowing selection of flow physics
"""

import FreeCAD
import os
import sys
import os.path
import CfdTools
from CfdTools import setInputFieldQuantity, indexOrDefault

if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore
    from PySide import QtCore
    from PySide import QtGui
    from PySide.QtCore import Qt
    from PySide.QtGui import QApplication
    import FemGui


RANS_MODELS = ["kOmegaSST"]


class _TaskPanelCfdPhysicsSelection:
    def __init__(self, obj):
        # Update object with latest properties for backward-compatibility
        obj.Proxy.initProperties(obj)

        FreeCADGui.Selection.clearSelection()
        self.sel_server = None
        self.obj = obj
        self.form = FreeCADGui.PySideUic.loadUi(os.path.join(os.path.dirname(__file__), "TaskPanelPhysics.ui"))

        self.form.radioButtonSteady.toggled.connect(self.updateUI)
        self.form.radioButtonTransient.toggled.connect(self.updateUI)

        self.form.radioButtonSinglePhase.toggled.connect(self.updateUI)
        self.form.radioButtonFreeSurface.toggled.connect(self.updateUI)

        self.form.radioButtonIncompressible.toggled.connect(self.updateUI)
        self.form.radioButtonCompressible.toggled.connect(self.updateUI)

        self.form.viscousCheckBox.stateChanged.connect(self.updateUI)
        self.form.radioButtonLaminar.toggled.connect(self.updateUI)
        self.form.radioButtonRANS.toggled.connect(self.updateUI)
        #self.form.radioButtonLES_DES.toggled.connect(self.updateUI)

        self.form.thermalCheckBox.stateChanged.connect(self.updateUI)
        self.form.radioButtonEnergy.toggled.connect(self.updateUI)
        self.form.radioButtonBuoyancy.toggled.connect(self.updateUI)

        self.load()

    def load(self):
        if self.obj.Time == 'Steady':
            self.form.radioButtonSteady.toggle()
        elif self.obj.Time == 'Transient':
            self.form.radioButtonTransient.toggle()

        if self.obj.Phase == 'Single':
            self.form.radioButtonSinglePhase.toggle()
        elif self.obj.Phase == 'FreeSurface':
            self.form.radioButtonFreeSurface.toggle()
        if self.obj.Flow == 'Incompressible':
            self.form.radioButtonIncompressible.toggle()
        elif self.obj.Flow == 'Compressible':
            self.form.radioButtonCompressible.toggle()
            self.form.checkBoxHighMach.setChecked(False)
        elif self.obj.Flow == 'HighMachCompressible':
            self.form.radioButtonCompressible.toggle()
            self.form.checkBoxHighMach.setChecked(True)

        if self.obj.Turbulence == 'Inviscid':
            self.form.viscousCheckBox.setChecked(False)
            self.form.radioButtonLaminar.toggle()
        if self.obj.Turbulence == 'Laminar':
            self.form.viscousCheckBox.setChecked(True)
            self.form.radioButtonLaminar.toggle()
        elif self.obj.Turbulence == 'RANS':
            self.form.viscousCheckBox.setChecked(True)
            self.form.radioButtonRANS.toggle()
        ti = CfdTools.indexOrDefault(RANS_MODELS, self.obj.TurbulenceModel, 0)
        self.form.turbulenceComboBox.setCurrentIndex(ti)

        #if self.obj.Thermal == "Energy":
        #    self.form.thermalCheckBox.toggle()
        #    self.form.radioButtonEnergy.toggle()
        #elif self.obj.Thermal == "Buoyancy":
        #    self.form.thermalCheckBox.toggle()
        #    self.form.radioButtonBuoyancy.toggle()

        setInputFieldQuantity(self.form.gx, self.obj.gx)
        setInputFieldQuantity(self.form.gy, self.obj.gy)
        setInputFieldQuantity(self.form.gz, self.obj.gz)

        self.updateUI()

    def updateUI(self):
        self.form.TimeFrame.setVisible(True)
        self.form.FlowFrame.setVisible(True)
        self.form.turbulenceFrame.setVisible(True)
        self.form.thermalFrame.setVisible(False)

        if self.form.radioButtonSteady.isChecked():
            self.form.radioButtonFreeSurface.setEnabled(False)
            if self.form.radioButtonFreeSurface.isChecked():
                self.form.radioButtonSinglePhase.toggle()
        else:
            self.form.radioButtonFreeSurface.setEnabled(True)

        self.form.gravityFrame.setEnabled(self.form.radioButtonFreeSurface.isChecked())

        if self.form.radioButtonFreeSurface.isChecked():
            self.form.radioButtonCompressible.setEnabled(False)
            if self.form.radioButtonCompressible.isChecked():
                self.form.radioButtonIncompressible.toggle()
        else:
            self.form.radioButtonCompressible.setEnabled(True)

        self.form.checkBoxHighMach.setEnabled(self.form.radioButtonCompressible.isChecked())
        self.form.thermalSelectionFrame.setVisible(False)

        if self.form.viscousCheckBox.isChecked():
            self.form.turbulenceFrame.setVisible(True)
            if self.form.radioButtonRANS.isChecked():
                self.form.turbulenceComboBox.clear()
                self.form.turbulenceComboBox.addItems(RANS_MODELS)
                self.form.turbulenceModelFrame.setVisible(True)
            else:
                self.form.turbulenceModelFrame.setVisible(False)
                self.form.turbulenceComboBox.clear()
        else:
            self.form.turbulenceFrame.setVisible(False)
            self.form.turbulenceModelFrame.setVisible(False)

        if self.form.thermalCheckBox.isChecked():
            self.form.thermalSelectionFrame.setVisible(True)
        else:
            self.form.radioButtonEnergy.toggle()
            self.form.thermalSelectionFrame.setVisible(False)

        # Temporarily disabling features which are not yet supported
        self.form.radioButtonEnergy.setEnabled(False)
        self.form.radioButtonBuoyancy.setEnabled(False)
        self.form.thermalCheckBox.setEnabled(False)

    def accept(self):
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()

        FreeCADGui.doCommand("\nobj = FreeCAD.ActiveDocument.{}".format(self.obj.Name))
        changed_transient = False
        if self.form.radioButtonSteady.isChecked():
            if self.obj.Time != 'Steady':
                changed_transient = True
            FreeCADGui.doCommand("obj.Time = 'Steady'")
        elif self.form.radioButtonTransient.isChecked():
            if self.obj.Time != 'Transient':
                changed_transient = True
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
                FreeCADGui.doCommand("obj.Thermal = 'Energy'")
            else:
                FreeCADGui.doCommand("obj.Flow = 'Compressible'")
                FreeCADGui.doCommand("obj.Thermal = 'None'")

        if self.form.viscousCheckBox.isChecked():
            if self.form.radioButtonLaminar.isChecked():
                FreeCADGui.doCommand("obj.Turbulence = 'Laminar'")
            elif self.form.radioButtonRANS.isChecked():
                FreeCADGui.doCommand("obj.Turbulence = 'RANS'")
                FreeCADGui.doCommand("obj.TurbulenceModel = '{}'".format(
                    self.form.turbulenceComboBox.currentText()))
        else:
            FreeCADGui.doCommand("obj.Turbulence = 'Inviscid'")

        #if self.form.radioButtonEnergy.isChecked():
        #    FreeCADGui.doCommand("obj.Thermal = 'Energy'")
        #elif self.form.radioButtonBuoyancy.isChecked():
        #    FreeCADGui.doCommand("obj.Thermal = 'Buoyancy'")

        FreeCADGui.doCommand("obj.gx = '{}'".format(self.form.gx.text()))
        FreeCADGui.doCommand("obj.gy = '{}'".format(self.form.gy.text()))
        FreeCADGui.doCommand("obj.gz = '{}'".format(self.form.gz.text()))

        if changed_transient:
            # TODO
            # For now, init the solver object's time values to sensible defaults for steady or transient
            # The user can then edit further
            a = CfdTools.getParentAnalysisObject(self.obj)
            if a:
                sol = CfdTools.getSolver(a)
                if sol:
                    FreeCADGui.doCommand("\nsol = FreeCAD.ActiveDocument.{}".format(sol.Name))
                    if self.obj.Time == 'Steady':
                        FreeCADGui.doCommand("sol.EndTime = 1000\n"
                                             "sol.TimeStep = 1\n"
                                             "sol.WriteInterval = 100\n")
                    else:
                        FreeCADGui.doCommand("sol.EndTime = 1\n"
                                             "sol.TimeStep = 0.001\n"
                                             "sol.WriteInterval = 0.1\n")

    def reject(self):
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()
