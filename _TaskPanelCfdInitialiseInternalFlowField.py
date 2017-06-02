# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2013-2015 - Juergen Riegel <FreeCAD@juergen-riegel.net> *
# *   Copyright (c) 2017 - Alfred Bogaers <abogaers@csir.co.za>             *
# *   Copyright (c) 2017 - Oliver Oxtoby <ooxtoby@csir.co.za>               *
# *   Copyright (c) 2017 - Johan Heyns <jheyns@csir.co.za>                  *
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

__title__ = "_TaskPanelCfdInitialiseInternalFlowField"
__author__ = ""
__url__ = "http://www.freecadweb.org"


import FreeCAD
import os
import sys
import os.path
import CfdTools
from CfdTools import inputCheckAndStore
import Units

if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore
    from PySide import QtCore
    from PySide import QtGui
    from PySide.QtCore import Qt
    from PySide.QtGui import QApplication
    import FemGui


class _TaskPanelCfdInitialiseInternalFlowField:
    '''The editmode TaskPanel for InitialVariables objects'''
    def __init__(self, obj, physics_model, boundaries):
        FreeCADGui.Selection.clearSelection()
        self.sel_server = None
        self.obj = obj
        self.physicsModel = physics_model
        self.boundaries = boundaries
        self.InitialVariables = self.obj.InitialVariables.copy()

        self.form = FreeCADGui.PySideUic.loadUi(os.path.join(os.path.dirname(__file__),
                                                             "TaskPanelCfdInitialiseInternalField.ui"))

        self.form.basicPropertiesFrame.setVisible(False)
        self.form.potentialFoamCheckBox.stateChanged.connect(self.potentialFoamChanged)
        self.form.turbulencePropertiesFrame.setVisible(False)

        self.form.Ux.textChanged.connect(self.UxChanged)
        self.form.Uy.textChanged.connect(self.UyChanged)
        self.form.Uz.textChanged.connect(self.UzChanged)
        self.form.pressure.textChanged.connect(self.PChanged)

        self.form.checkUseInletValues.stateChanged.connect(self.checkUseInletValuesChanged)
        self.form.comboInlets.currentIndexChanged.connect(self.comboInletsChanged)
        self.form.inputk.textChanged.connect(self.inputkChanged)
        self.form.inputOmega.textChanged.connect(self.inputOmegaChanged)

        self.populateUiBasedOnPhysics()

    def populateUiBasedOnPhysics(self):
        self.form.potentialFoamCheckBox.setToolTip("Initialise the velocity field using an incompressible, potential "
                                                   "or irrotational flow assumption.")
        checked = self.InitialVariables.get('PotentialFoam', False)
        self.form.potentialFoamCheckBox.setChecked(checked)
        self.form.basicPropertiesFrame.setVisible(not checked)

        self.form.Ux.setText(str(self.InitialVariables.get('Ux'))+"m/s")
        self.form.Uy.setText(str(self.InitialVariables.get('Uy'))+"m/s")
        self.form.Uz.setText(str(self.InitialVariables.get('Uz'))+"m/s")
        self.form.pressure.setText(str(self.InitialVariables.get('Pressure'))+"kg*m/s^2")

        if self.physicsModel['Turbulence'] in ['RANS', 'LES']:
            self.form.turbulencePropertiesFrame.setVisible(True)
        else:
            self.form.turbulencePropertiesFrame.setVisible(False)

        self.form.checkUseInletValues.setChecked(self.InitialVariables.get('UseInletTurbulenceValues', True))
        # Add any inlets to the list
        for b in self.boundaries:
            if b.BoundarySettings['BoundaryType'] == 'inlet':
                self.form.comboInlets.addItems([b.Label])
        self.form.comboInlets.setCurrentIndex(self.form.comboInlets.findText(self.InitialVariables.get('Inlet')))
        self.form.inputk.setText(str(self.InitialVariables.get('k'))+"m^2/s^2")
        self.form.inputOmega.setText(str(self.InitialVariables.get('omega'))+"rad/s")
        self.updateTurbulenceModelsUi()

        if self.physicsModel['Thermal'] == 'Energy':
            self.form.energyFrame.setVisible(True)
            self.form.bouyancyFrame.setVisible(False)
        elif self.physicsModel['Thermal'] == 'Buoyancy':
            self.form.energyFrame.setVisible(False)
            self.form.bouyancyFrame.setVisible(True)
        else:
            self.form.thermalPropertiesFrame.setVisible(False)

    def updateTurbulenceModelsUi(self):
        checked = bool(self.InitialVariables.get('UseInletTurbulenceValues'))
        self.form.comboInlets.setVisible(checked and self.form.comboInlets.count() > 1)
        self.form.kEpsilonFrame.setVisible(False)
        self.form.kOmegaSSTFrame.setVisible(False)
        self.form.SpalartAlmerasFrame.setVisible(False)
        if self.physicsModel['TurbulenceModel'] == 'kOmegaSST':
            self.form.kOmegaSSTFrame.setVisible(not checked)

    def potentialFoamChanged(self, checked):
        self.form.basicPropertiesFrame.setVisible(not checked)
        self.InitialVariables['PotentialFoam'] = bool(checked)

    def UxChanged(self, value):
        inputCheckAndStore(value, "m/s", self.InitialVariables, 'Ux')

    def UyChanged(self, value):
        inputCheckAndStore(value, "m/s", self.InitialVariables, 'Uy')

    def UzChanged(self, value):
        inputCheckAndStore(value, "m/s", self.InitialVariables, 'Uz')

    def PChanged(self, value):
        inputCheckAndStore(value, "kg*m/s^2", self.InitialVariables, 'Pressure')

    def checkUseInletValuesChanged(self, checked):
        self.InitialVariables['UseInletTurbulenceValues'] = checked
        self.updateTurbulenceModelsUi()

    def comboInletsChanged(self, index):
        self.InitialVariables['Inlet'] = self.form.comboInlets.currentText()

    def inputkChanged(self, text):
        inputCheckAndStore(text, "m^2/s^2", self.InitialVariables, 'k')

    def inputOmegaChanged(self, text):
        inputCheckAndStore(text, "rad/s", self.InitialVariables, 'omega')

    def accept(self):
        self.obj.InitialVariables = self.InitialVariables
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()

        FreeCADGui.doCommand("\n# Values are converted to SI units and stored (eg. m/s)")
        FreeCADGui.doCommand("init = FreeCAD.ActiveDocument.{}.InitialVariables".format(self.obj.Name))
        FreeCADGui.doCommand("init['PotentialFoam'] = {}".format(self.InitialVariables['PotentialFoam']))
        FreeCADGui.doCommand("init['Ux'] = {}".format(self.InitialVariables['Ux']))
        FreeCADGui.doCommand("init['Uy'] = {}".format(self.InitialVariables['Uy']))
        FreeCADGui.doCommand("init['Uz'] = {}".format(self.InitialVariables['Uz']))
        FreeCADGui.doCommand("init['Pressure'] = {}".format(self.InitialVariables['Pressure']))
        FreeCADGui.doCommand("init['UseInletTurbulenceValues'] "
                             "= {}".format(self.InitialVariables['UseInletTurbulenceValues']))
        FreeCADGui.doCommand("init['omega'] = {}".format(self.InitialVariables['omega']))
        FreeCADGui.doCommand("init['k'] = {}".format(self.InitialVariables['k']))
        FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.InitialVariables = init".format(self.obj.Name))

    def reject(self):
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()
