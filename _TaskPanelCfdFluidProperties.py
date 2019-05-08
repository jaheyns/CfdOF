# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2017-2018                                               *
# *   Johan Heyns (CSIR) <jheyns@csir.co.za>                                *
# *   Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>                             *
# *   Alfred Bogaers (CSIR) <abogaers@csir.co.za>                           *
# *   (c) Bernd Hahnebach (bernd@bimstatik.org) 2014                        *
# *   (c) Qingfeng Xia @ iesensor.com 2016                                  *
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
                                                             "TaskPanelCfdFluidProperties.ui"))

        self.material = self.obj.Material

        self.import_materials()
        self.form.PredefinedMaterialLibraryComboBox.addItem("Custom")

        self.form.PredefinedMaterialLibraryComboBox.currentIndexChanged.connect(self.selectPredefine)

        self.text_boxes = {}
        self.fields = []
        self.createTextBoxesBasedOnPhysics()

        self.selecting_predefined = True
        try:
            self.form.PredefinedMaterialLibraryComboBox.setCurrentIndex(
                self.form.PredefinedMaterialLibraryComboBox.findText(self.material['Name']))
            self.selectPredefine()
        finally:
            self.selecting_predefined = False

    def createTextBoxesBasedOnPhysics(self):
        if self.physics_obj.Flow == 'Incompressible':
            self.fields = ['Density', 'DynamicViscosity']
        else:
            self.fields = ['MolarMass', 'Cp', 'SutherlandConstant', 'SutherlandTemperature']
        self.text_boxes = {}
        for name in self.fields:
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

    def selectPredefine(self):
        index = self.form.PredefinedMaterialLibraryComboBox.currentIndex()

        mat_file_path = self.form.PredefinedMaterialLibraryComboBox.itemData(index)
        if mat_file_path:
            self.material = self.materials[mat_file_path]
            self.selecting_predefined = True
            try:
                for m in self.fields:
                    setQuantity(self.text_boxes[m], self.material.get(m, ''))
            finally:
                self.selecting_predefined = False
        self.form.fluidDescriptor.setText(self.material["Description"])

    def manualEdit(self):
        if not self.selecting_predefined:
            self.form.PredefinedMaterialLibraryComboBox.setCurrentIndex(
                self.form.PredefinedMaterialLibraryComboBox.findText('Custom'))
            self.material = {'Name': 'Custom', 'Description': 'User-entered properties'}
            for f in self.fields:
                self.material[f] = getQuantity(self.text_boxes[f])
            self.selectPredefine()

    def accept(self):
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()
        doc.Document.recompute()

        FreeCADGui.doCommand("\nFreeCAD.ActiveDocument." + self.obj.Name + ".Material"
                             " = {}".format(self.material))

    def reject(self):
        #self.remove_active_sel_server()
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()

    def import_materials(self):
        self.form.PredefinedMaterialLibraryComboBox.clear()
        self.materials, material_name_path_list = CfdTools.importMaterials()
        for mat in material_name_path_list:
            self.form.PredefinedMaterialLibraryComboBox.addItem(QtGui.QIcon(":/icons/freecad.svg"), mat[0], mat[1])
