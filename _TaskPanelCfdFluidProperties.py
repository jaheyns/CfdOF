# ***************************************************************************
# *                                                                         *
# *   (c) Bernd Hahnebach (bernd@bimstatik.org) 2014                        *
# *   (c) Qingfeng Xia @ iesensor.com 2016                                  *
# *   Copyright (c) 2017-2018 Johan Heyns (CSIR) <jheyns@csir.co.za>        *
# *   Copyright (c) 2017-2018 Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>     *
# *   Copyright (c) 2017-2018 Alfred Bogaers (CSIR) <abogaers@csir.co.za>   *
# *   Copyright (c) 2019-2021 Oliver Oxtoby <oliveroxtoby@gmail.com>        *
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
from CfdTools import setQuantity, getQuantity
if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtGui


class TaskPanelCfdFluidProperties:
    """ Task Panel for FluidMaterial objects """
    def __init__(self, obj, physics_obj):
        self.obj = obj
        self.physics_obj = physics_obj

        self.form = FreeCADGui.PySideUic.loadUi(os.path.join(os.path.dirname(__file__),
                                                             "core/gui/TaskPanelCfdFluidProperties.ui"))

        self.material = self.obj.Material

        self.form.compressibleCheckBox.setVisible(self.physics_obj.Flow == "Compressible")
        # Make sure it is checked in the default case since object was initialised with Isothermal
        self.form.compressibleCheckBox.setChecked(self.material.get('Type') != "Incompressible")
        self.form.compressibleCheckBox.stateChanged.connect(self.compressibleCheckBoxChanged)

        self.text_boxes = {}
        self.fields = []
        if self.physics_obj.Flow == 'Incompressible':
            material_type = 'Isothermal'
        else:
            if self.physics_obj.Flow == "Compressible" and not self.form.compressibleCheckBox.isChecked():
                material_type = 'Incompressible'
            else:
                material_type = 'Compressible'
        self.material['Type'] = material_type
        self.createUIBasedOnPhysics()
        self.populateMaterialsList()

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

    def compressibleCheckBoxChanged(self):
        self.material['Type'] = 'Compressible' if self.form.compressibleCheckBox.isChecked() else 'Incompressible'
        self.createUIBasedOnPhysics()
        self.populateMaterialsList()

    def createUIBasedOnPhysics(self):
        for rowi in range(self.form.propertiesLayout.rowCount()):
            self.form.propertiesLayout.removeRow(0)

        if self.material['Type'] == 'Isothermal':
            self.fields = ['Density', 'DynamicViscosity']
        elif self.material['Type'] == 'Incompressible':
            self.fields = ['MolarMass', 'DensityPolynomial', 'CpPolynomial', 'DynamicViscosityPolynomial', 'ThermalConductivityPolynomial']
        else:
            self.fields = ['MolarMass', 'Cp', 'SutherlandTemperature', 'SutherlandRefTemperature', 'SutherlandRefViscosity']

        self.text_boxes = {}
        for name in self.fields:
            if name.endswith("Polynomial"):
                widget = FreeCADGui.UiLoader().createWidget("QLineEdit")
                widget.setObjectName(name)
                widget.setToolTip(
                    "Enter coefficients of temperature-polynomial starting from constant followed by higher powers")
                val = self.material.get(name, '0')
                self.form.propertiesLayout.addRow(name + ":", widget)
                self.text_boxes[name] = widget
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
                self.form.propertiesLayout.addRow(name+":", widget)
                self.text_boxes[name] = widget
                setQuantity(widget, val)
                widget.valueChanged.connect(self.manualEdit)

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

    def accept(self):
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()
        doc.Document.recompute()

        FreeCADGui.doCommand("\nFreeCAD.ActiveDocument." + self.obj.Name + ".Material"
                             " = {}".format(self.material))

    def reject(self):
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()

    def populateMaterialsList(self):
        self.form.PredefinedMaterialLibraryComboBox.clear()
        self.materials, material_name_path_list = CfdTools.importMaterials()
        for mat in material_name_path_list:
            if self.material['Type'] == self.materials[mat[1]]['Type']:
                mat_name = self.materials[mat[1]]['Name']
                self.form.PredefinedMaterialLibraryComboBox.addItem(QtGui.QIcon(":/icons/freecad.svg"), mat_name, mat[1])
        self.form.PredefinedMaterialLibraryComboBox.addItem("Custom")
