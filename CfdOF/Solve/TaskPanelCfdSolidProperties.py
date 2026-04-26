# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: © 2024 CfdOF contributors
# SPDX-FileNotice: Part of the CfdOF addon.

import os
import FreeCAD
if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtGui
from CfdOF import CfdTools, CfdFaceSelectWidget
from CfdOF.CfdTools import setQuantity, getQuantity, storeIfChanged

translate = FreeCAD.Qt.translate

SOLID_FIELDS = ['ThermalConductivity', 'Density', 'SpecificHeat']
HEAT_GENERATION_UNIT = 'W/m^3'


class TaskPanelCfdSolidProperties:
    """Task panel for CfdSolidMaterial objects."""

    def __init__(self, obj):
        self.obj = obj

        self.form = FreeCADGui.PySideUic.loadUi(
            os.path.join(CfdTools.getModulePath(), 'Gui', "TaskPanelCfdSolidProperties.ui"))

        self.material = dict(self.obj.Material)
        self.ShapeRefsOrig = list(self.obj.ShapeRefs)

        # Body selector — whole-solid selection only
        self.solidSelector = CfdFaceSelectWidget.CfdFaceSelectWidget(
            self.form.solidBodyWidget, self.obj,
            allow_obj_sel=False, allow_face_sel=False, allow_solid_sel=True)

        # Build property input widgets dynamically into frame_solid
        self.text_boxes = {}
        layout = self.form.frame_solid.layout()
        for name in SOLID_FIELDS:
            widget = FreeCADGui.UiLoader().createWidget("Gui::InputField")
            widget.setObjectName(name)
            widget.setProperty("format", "g")
            val = self.material.get(name, '0')
            widget.setProperty("unit", val)
            widget.setProperty("minimum", 0)
            widget.setProperty("singleStep", 0.1)
            layout.addRow(name + ":", widget)
            self.text_boxes[name] = widget
            setQuantity(widget, val)
            widget.valueChanged.connect(self.manualEdit)

        if hasattr(self.obj, 'HeatGeneration'):
            self.setHeatGenerationQuantity(self.obj.HeatGeneration)
        self.form.inputHeatGeneration.editingFinished.connect(self.heatGenChanged)

        self.form.material_name.setText(self.obj.Label)
        self.form.saveButton.clicked.connect(self.saveCustomMaterial)
        self.form.saveButton.setVisible(False)
        self.form.PredefinedMaterialLibraryComboBox.currentIndexChanged.connect(self.selectPredefined)

        self.selecting_predefined = True
        try:
            self.populateMaterialsList()
            idx = self.form.PredefinedMaterialLibraryComboBox.findText(self.obj.Material.get('Name', ''))
            if idx == -1:
                idx = 0
            self.form.PredefinedMaterialLibraryComboBox.setCurrentIndex(idx)
            self.selectPredefined()
        finally:
            self.selecting_predefined = False
        # Restore the user's saved values: populateMaterialsList and selectPredefined
        # both fire signals that overwrite self.material and the widget values.
        self.material = dict(self.obj.Material)
        for name in SOLID_FIELDS:
            setQuantity(self.text_boxes[name], self.material.get(name, '0'))
        self.form.solidDescriptor.setText(self.material.get("Description", ""))
        self.form.material_name.setText(self.obj.Label)

    def populateMaterialsList(self):
        self.form.PredefinedMaterialLibraryComboBox.clear()
        self.materials, material_name_path_list = CfdTools.importMaterials()
        for mat in material_name_path_list:
            if self.materials[mat[1]].get('Type') == 'Solid':
                mat_name = self.materials[mat[1]]['Name']
                self.form.PredefinedMaterialLibraryComboBox.addItem(
                    QtGui.QIcon(":/Icons/freecad.svg"), mat_name, mat[1])
        self.form.PredefinedMaterialLibraryComboBox.addItem("Custom")

    def selectPredefined(self):
        index = self.form.PredefinedMaterialLibraryComboBox.currentIndex()
        mat_file_path = self.form.PredefinedMaterialLibraryComboBox.itemData(index)
        if mat_file_path:
            self.material = dict(self.materials[mat_file_path])
            self.selecting_predefined = True
            try:
                for name in SOLID_FIELDS:
                    setQuantity(self.text_boxes[name], self.material.get(name, '0'))
            finally:
                self.selecting_predefined = False
            self.form.material_name.setText(self.material['Name'])
        self.form.solidDescriptor.setText(self.material.get("Description", ""))

    def manualEdit(self):
        if not self.selecting_predefined:
            self.form.PredefinedMaterialLibraryComboBox.setCurrentIndex(
                self.form.PredefinedMaterialLibraryComboBox.findText('Custom'))
            self.form.solidDescriptor.setText("User-entered properties")
            self.material = {'Name': 'Custom', 'Description': 'User-entered properties', 'Type': 'Solid'}
            for name in SOLID_FIELDS:
                self.material[name] = getQuantity(self.text_boxes[name])
            self.form.saveButton.setVisible(True)

    def heatGenChanged(self):
        quantity = self.getHeatGenerationQuantity(show_error=False)
        if quantity is not None:
            self.form.inputHeatGeneration.setText(quantity)

    def setHeatGenerationQuantity(self, quantity):
        if isinstance(quantity, str):
            q = FreeCAD.Units.Quantity(quantity)
        else:
            q = quantity
        display_value = q.getValueAs(HEAT_GENERATION_UNIT).Value
        self.form.inputHeatGeneration.setText("{:g} {}".format(display_value, HEAT_GENERATION_UNIT))

    def getHeatGenerationQuantity(self, show_error=True):
        text = self.form.inputHeatGeneration.text().strip()
        if not text:
            text = "0 {}".format(HEAT_GENERATION_UNIT)
        try:
            q = FreeCAD.Units.Quantity(text).getValueAs(HEAT_GENERATION_UNIT)
        except Exception:
            if show_error:
                CfdTools.cfdErrorBox("Invalid heat generation value: {}".format(text))
            return None
        if q.Value < 0:
            if show_error:
                CfdTools.cfdErrorBox("Heat generation must be greater than or equal to 0")
            return None
        return "{:g} {}".format(q.Value, HEAT_GENERATION_UNIT)

    def saveCustomMaterial(self):
        system_mat_dir = os.path.join(CfdTools.getModulePath(), "Data", "CfdFluidMaterialProperties")
        d = QtGui.QFileDialog(None, "Save Custom Solid Material", system_mat_dir, "FCMat (*.FCMat)")
        d.setDefaultSuffix("FCMat")
        d.setAcceptMode(QtGui.QFileDialog.AcceptMode.AcceptSave)
        d.exec()
        file_names = d.selectedFiles()
        if file_names:
            mat_name = self.form.material_name.text()
            with open(file_names[0], 'w') as f:
                f.write('; {}\n;\n; FreeCAD Material card: see https://www.freecad.org/wiki/Material\n\n[FCMat]\n'.format(mat_name))
                f.write('Name = {}\nType = Solid\n'.format(mat_name))
                for key, val in self.material.items():
                    if key not in ('Name', 'Type'):
                        f.write('{} = {}\n'.format(key, val))
            FreeCAD.Console.PrintMessage(translate("Console", "Custom solid material saved\n"))

    def accept(self):
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()
        doc.Document.recompute()
        storeIfChanged(self.obj, 'Material', self.material)
        storeIfChanged(self.obj, 'Label', self.form.material_name.text())
        if hasattr(self.obj, 'HeatGeneration'):
            heat_generation = self.getHeatGenerationQuantity()
            if heat_generation is None:
                return False
            self.form.inputHeatGeneration.setText(heat_generation)
            storeIfChanged(self.obj, 'HeatGeneration', heat_generation)
        if self.obj.ShapeRefs != self.ShapeRefsOrig:
            refstr = "FreeCAD.ActiveDocument.{}.ShapeRefs = [\n".format(self.obj.Name)
            refstr += ",\n".join(
                "(FreeCAD.ActiveDocument.getObject('{}'), {})".format(ref[0].Name, ref[1])
                for ref in self.obj.ShapeRefs)
            refstr += "]\n"
            FreeCADGui.doCommand(refstr)

    def reject(self):
        self.obj.ShapeRefs = self.ShapeRefsOrig
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()

    def closing(self):
        return
