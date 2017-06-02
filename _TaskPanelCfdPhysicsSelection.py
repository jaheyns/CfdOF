# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2016 - Bernd Hahnebach <bernd@bimstatik.org>            *
# *   Copyright (c) 2017 - Alfred Bogaers (CSIR) <abogaers@csir.co.za>      *
# *   Copyright (c) 2017 - Johan Heyns (CSIR) <jheyns@csir.co.za>           *
# *   Copyright (c) 2017 - Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>        *
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

__title__ = "_TaskPanelCfdPhysicsSelection"
__author__ = "AB, JH, OO"
__url__ = "http://www.freecadweb.org"

import FreeCAD
import os
import sys
import os.path
import CfdTools

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
    """ The editmode TaskPanel for PhysicsModel objects """
    def __init__(self, obj):
        FreeCADGui.Selection.clearSelection()
        self.sel_server = None
        self.obj = obj
        self.physicsModel = self.obj.PhysicsModel.copy()

        self.form = FreeCADGui.PySideUic.loadUi(os.path.join(os.path.dirname(__file__), "TaskPanelPhysics.ui"))

        self.form.TimeFrame.setVisible(True)
        self.form.FlowFrame.setVisible(True)
        self.form.turbulenceFrame.setVisible(True)
        self.form.thermalFrame.setVisible(False)
        
        self.form.turbulenceChoiceFrame.setVisible(False)
        self.form.turbulenceModelFrame.setVisible(False)
        self.form.thermalSelectionFrame.setVisible(False)

        self.form.radioButtonSteady.toggled.connect(self.timeStateChanged)
        self.form.radioButtonTransient.toggled.connect(self.timeStateChanged)

        self.form.radioButtonIncompressible.toggled.connect(self.compressibilityChanged)
        self.form.radioButtonCompressible.toggled.connect(self.compressibilityChanged)

        self.form.turbulenceCheckBox.stateChanged.connect(self.turbulenceStateChanged)
        self.form.radioButtonRANS.toggled.connect(self.RANSChosen)
        #self.form.radioButtonLES_DES.toggled.connect(self.LESChosen)
        self.form.radioButtonLaminar.toggled.connect(self.laminarChosen)
        self.form.turbulenceComboBox.currentIndexChanged.connect(self.turbulenceComboBoxChanged)

        self.form.thermalCheckBox.stateChanged.connect(self.thermalStateChanged)
        self.form.radioButtonEnergy.toggled.connect(self.selectThermal)
        self.form.radioButtonBuoyancy.toggled.connect(self.selectThermal)

        # Temporarily disabling features which are not yet supported
        self.form.radioButtonTransient.setEnabled(False)
        self.form.radioButtonCompressible.setEnabled(False)
        self.form.radioButtonEnergy.setEnabled(False)
        self.form.radioButtonBuoyancy.setEnabled(False)
        self.form.thermalCheckBox.setEnabled(False)

        self.initialiseUponReload()

    def initialiseUponReload(self):
        if self.physicsModel['Time'] == 'Steady':
            self.form.radioButtonSteady.toggle()
        elif self.physicsModel['Time'] == 'Transient':
            self.form.radioButtonTransient.toggle()

        if self.physicsModel['Flow'] == 'Incompressible':
            self.form.radioButtonIncompressible.toggle()
        elif self.physicsModel['Flow'] == 'Compressible':
            self.form.radioButtonCompressible.toggle()

        if self.physicsModel['Turbulence'] == 'Laminar':
            self.form.turbulenceCheckBox.toggle()
            self.form.radioButtonLaminar.toggle()
        elif self.physicsModel['Turbulence'] == 'RANS':
            self.form.turbulenceCheckBox.toggle()
            self.form.radioButtonRANS.toggle()
        ti = CfdTools.indexOrDefault(RANS_MODELS, self.physicsModel.get('TurbulenceType'), 0)
        self.form.turbulenceComboBox.setCurrentIndex(ti)

        if self.physicsModel['Thermal'] == "Energy":
            self.form.thermalCheckBox.toggle()
            self.form.radioButtonEnergy.toggle()
        elif self.physicsModel['Thermal'] == "Buoyancy":
            self.form.thermalCheckBox.toggle()
            self.form.radioButtonBuoyancy.toggle()

    def timeStateChanged(self):
        self.form.FlowFrame.setVisible(True)

        if self.form.radioButtonSteady.isChecked():
            self.physicsModel['Time'] = 'Steady'
        else:
            self.physicsModel['Time'] = 'Transient'

    def selectThermal(self):
        if self.form.radioButtonEnergy.isChecked():
            self.physicsModel['Thermal'] = "Energy"
        elif self.form.radioButtonBuoyancy.isChecked():
            self.physicsModel['Thermal'] = "Buoyancy"

    def compressibilityChanged(self):
        #self.form.turbulenceFrame.setVisible(True)
        #self.form.turbulenceChoiceFrame.setVisible(False)
        #self.form.turbulenceModelFrame.setVisible(False)
        #if self.form.turbulenceCheckBox.isChecked():
            #self.form.turbulenceCheckBox.toggle()

        #self.form.thermalFrame.setVisible(True)
        #self.form.thermalSelectionFrame.setVisible(False)
        #if self.form.thermalCheckBox.isChecked():
            #self.form.thermalCheckBox.toggle()
    
        if self.form.radioButtonIncompressible.isChecked():
            self.physicsModel["Flow"] = 'Incompressible'
        else:
            self.physicsModel["Flow"] = 'Compressible'

    def turbulenceStateChanged(self):
        if self.form.turbulenceCheckBox.isChecked():
            self.form.turbulenceChoiceFrame.setVisible(True)
            self.form.radioButtonLaminar.toggle()
        else:
            self.form.turbulenceChoiceFrame.setVisible(False)
            self.form.turbulenceModelFrame.setVisible(False)
            self.physicsModel["Turbulence"] = 'Inviscid'

    def thermalStateChanged(self):
        if self.form.thermalCheckBox.isChecked():
            self.form.thermalSelectionFrame.setVisible(True)
            self.form.radioButtonEnergy.toggle()
        else:
            self.form.thermalSelectionFrame.setVisible(False)
            self.physicsModel["Thermal"] = None

    def RANSChosen(self):
        self.form.turbulenceModelFrame.setVisible(True)
        self.form.turbulenceComboBox.clear()
        self.form.turbulenceComboBox.addItems(RANS_MODELS)
        self.physicsModel["Turbulence"] = "RANS"

    def laminarChosen(self):
        self.form.turbulenceModelFrame.setVisible(False)
        self.physicsModel["Turbulence"] = "Laminar"

    def turbulenceComboBoxChanged(self):
        self.physicsModel['TurbulenceModel'] = self.form.turbulenceComboBox.currentText()

    def accept(self):
        self.obj.PhysicsModel = self.physicsModel
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()

        FreeCADGui.doCommand("\nphys = FreeCAD.ActiveDocument.{}.PhysicsModel".format(self.obj.Name))
        FreeCADGui.doCommand("phys['Time'] = '{}'".format(self.physicsModel['Time']))
        FreeCADGui.doCommand("phys['Flow'] = '{}'".format(self.physicsModel['Flow']))
        FreeCADGui.doCommand("phys['Turbulence'] = '{}'".format(self.physicsModel['Turbulence']))
        FreeCADGui.doCommand("phys['TurbulenceModel'] = '{}'".format(self.physicsModel['TurbulenceModel']))
        FreeCADGui.doCommand("phys['Thermal'] = {}".format(self.physicsModel['Thermal']))
        FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.PhysicsModel = phys".format(self.obj.Name))

    def reject(self):
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()
