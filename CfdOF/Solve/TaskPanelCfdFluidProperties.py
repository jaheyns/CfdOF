# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2017-2018 Johan Heyns (CSIR) <jheyns@csir.co.za>        *
# *   Copyright (c) 2017-2018 Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>     *
# *   Copyright (c) 2017-2018 Alfred Bogaers (CSIR) <abogaers@csir.co.za>   *
# *   Copyright (c) 2019-2022 Oliver Oxtoby <oliveroxtoby@gmail.com>        *
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
    from PySide import QtGui
from CfdOF import CfdTools
from CfdOF.CfdTools import setQuantity, getQuantity, storeIfChanged

translate = FreeCAD.Qt.translate

# The properties presented for each fluid type
ALL_FIELDS = {'Isothermal': ['Density', 'DynamicViscosity'],
              'Incompressible': ['MolarMass', 'DensityPolynomial', 'CpPolynomial', 'DynamicViscosityPolynomial',
                    'ThermalConductivityPolynomial'],
              'Compressible': ['MolarMass', 'Cp', 'SutherlandTemperature', 'SutherlandRefTemperature',
                    'SutherlandRefViscosity']}

class TaskPanelCfdFluidProperties:
    """ Task Panel for FluidMaterial objects """
    def __init__(self, obj, physics_obj):
        self.obj = obj
        self.physics_obj = physics_obj

        self.form = FreeCADGui.PySideUic.loadUi(os.path.join(CfdTools.getModulePath(),
                                                             'Gui', "TaskPanelCfdFluidProperties.ui"))

        self.material = self.obj.Material

        self.form.compressibleCheckBox.setVisible(self.physics_obj.Flow == "NonIsothermal")
        # Make sure it is checked in the default case since object was initialised with Isothermal
        self.form.compressibleCheckBox.setChecked(self.material.get('Type') != "Incompressible")
        if hasattr(self.form.compressibleCheckBox, "checkStateChanged"):
            self.form.compressibleCheckBox.checkStateChanged.connect(self.updateUI)
        else:
            self.form.compressibleCheckBox.stateChanged.connect(self.updateUI)
        self.text_boxes = {}
        self.fields = []
        self.createUI()
        self.updateUI()

        self.form.PredefinedMaterialLibraryComboBox.currentIndexChanged.connect(self.selectPredefined)

        self.selecting_predefined = True
        try:
            idx = self.form.PredefinedMaterialLibraryComboBox.findText(self.material['Name'])
            if idx == -1:
                # Select first one if not found
                idx = 0
            self.form.PredefinedMaterialLibraryComboBox.setCurrentIndex(idx)
            self.selectPredefined()
        finally:
            self.selecting_predefined = False
        self.form.material_name.setText(self.obj.Label)

        self.form.saveButton.clicked.connect(self.saveCustomMaterial)
        self.form.saveButton.setVisible(False)
        #Hide unless materially edited

    def createUI(self):
        layouts = {'Isothermal': self.form.frame_isothermal.layout(), 
                   'Incompressible': self.form.frame_incompressible.layout(), 
                   'Compressible': self.form.frame_compressible.layout()}

        self.all_text_boxes = {'Isothermal': {}, 'Incompressible': {}, 'Compressible': {}}
        for k in ['Isothermal', 'Incompressible', 'Compressible']:
            layout = layouts[k]
            fields = ALL_FIELDS[k]
            text_boxes = self.all_text_boxes[k]

            for name in fields:
                if name.endswith("Polynomial"):
                    widget = FreeCADGui.UiLoader().createWidget("QLineEdit")
                    widget.setObjectName(name)
                    widget.setToolTip(
                        "Enter coefficients of temperature-polynomial starting from constant followed by higher powers")
                    val = self.material.get(name, '0')
                    layout.addRow(name + ":", widget)
                    text_boxes[name] = widget
                    widget.setText(val)
                    widget.textChanged.connect(self.manualEdit)
                else:
                    widget = FreeCADGui.UiLoader().createWidget("Gui::InputField")
                    widget.setObjectName(name)
                    widget.setProperty("format", "g")
                    val = self.material.get(name, '0')
                    widget.setProperty("unit", val)
                    widget.setProperty("minimum", 0)
                    widget.setProperty("singleStep", 0.1)
                    layout.addRow(name+":", widget)
                    text_boxes[name] = widget
                    setQuantity(widget, val)
                    widget.valueChanged.connect(self.manualEdit)

    def updateUI(self):
        if self.physics_obj.Flow == 'Isothermal':
            material_type = 'Isothermal'
        else:
            if self.physics_obj.Flow == 'NonIsothermal' and not self.form.compressibleCheckBox.isChecked():
                material_type = 'Incompressible'
            else:
                material_type = 'Compressible'
        self.material['Type'] = material_type
        self.fields = ALL_FIELDS[self.material['Type']]
        self.text_boxes = self.all_text_boxes[self.material['Type']]
        self.form.frame_isothermal.setVisible(self.material['Type'] == 'Isothermal')
        self.form.frame_incompressible.setVisible(self.material['Type'] == 'Incompressible')
        self.form.frame_compressible.setVisible(self.material['Type'] == 'Compressible')
        self.populateMaterialsList()

    def populateMaterialsList(self):
        self.form.PredefinedMaterialLibraryComboBox.clear()
        self.materials, material_name_path_list = CfdTools.importMaterials()
        for mat in material_name_path_list:
            if self.material['Type'] == self.materials[mat[1]]['Type']:
                mat_name = self.materials[mat[1]]['Name']
                self.form.PredefinedMaterialLibraryComboBox.addItem(QtGui.QIcon(":/Icons/freecad.svg"), mat_name, mat[1])
        self.form.PredefinedMaterialLibraryComboBox.addItem("Custom")

    def selectPredefined(self):
        index = self.form.PredefinedMaterialLibraryComboBox.currentIndex()

        mat_file_path = self.form.PredefinedMaterialLibraryComboBox.itemData(index)
        if mat_file_path:
            self.material = self.materials[mat_file_path]
            self.selecting_predefined = True
            try:
                for m in self.fields:
                    if m.endswith("Polynomial"):
                        self.text_boxes[m].setText(self.material.get(m, ''))
                    else:
                        setQuantity(self.text_boxes[m], self.material.get(m, '0'))
            finally:
                self.selecting_predefined = False
            self.form.material_name.setText(self.material['Name'])
        self.form.fluidDescriptor.setText(self.material["Description"])

    def manualEdit(self):
        if not self.selecting_predefined:
            self.form.PredefinedMaterialLibraryComboBox.setCurrentIndex(
                self.form.PredefinedMaterialLibraryComboBox.findText('Custom'))
            self.form.fluidDescriptor.setText("User-entered properties")
            curr_type = self.material['Type']
            self.material = {'Name': 'Custom', 'Description': 'User-entered properties', 'Type': curr_type}
            for f in self.fields:
                if f.endswith('Polynomial'):
                    self.material[f] = self.text_boxes[f].text()
                else:
                    self.material[f] = getQuantity(self.text_boxes[f])
            self.selectPredefined()
            self.form.saveButton.setVisible(True)

    def saveCustomMaterial(self):
        system_mat_dir = os.path.join(CfdTools.getModulePath(), "Data", "CfdFluidMaterialProperties")
        custom_mat = CfdTools.getMaterials(CfdTools.getActiveAnalysis())
        d = QtGui.QFileDialog(
            None, "Save Custom Material", system_mat_dir, "FCMat (*.FCMat)")
        d.setDefaultSuffix("FCMat")
        d.setAcceptMode(d.AcceptSave)
        d.exec()
        file_name = d.selectedFiles()
        if file_name:
            storeIfChanged(self.obj, 'Label', self.form.material_name.text())
            #makes sure saved name matches what was entered in that task panel session
            f = open(file_name[0], 'w')
            f.write('; ' + FreeCAD.ActiveDocument.FluidProperties.Label + '\n')
            f.write('; \n; FreeCAD Material card: see https://www.freecad.org/wiki/Material \n')
            f.write('\n[FCMat]\n')
            f.write('Name = ' + FreeCAD.ActiveDocument.FluidProperties.Label + '\n')
            #self.material['Name'] will always be 'Custom', which makes name unidentifiable in dropdown
            for key in self.material:
                if key != 'Name':
                    f.write(key + ' = ' + self.material[key] + '\n')
            FreeCAD.Console.PrintMessage(
                translate("Console", "Custom material saved\n")
            )

    def accept(self):
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()
        doc.Document.recompute()
        storeIfChanged(self.obj, 'Material', self.material)
        storeIfChanged(self.obj, 'Label', self.form.material_name.text())

    def reject(self):
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()

    def closing(self):
        # We call this from unsetEdit to allow cleanup
        return
