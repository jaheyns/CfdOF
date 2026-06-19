# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: © 2022 Jonathan Bergh <bergh.jonathan@gmail.com>
# SPDX-FileCopyrightText: © 2022 Oliver Oxtoby <oliveroxtoby@gmail.com>
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
from FreeCAD import Units
from CfdOF import CfdTools
from CfdOF.CfdTools import getQuantity, setQuantity, storeIfChanged, indexOrDefault
if FreeCAD.GuiUp:
    import FreeCADGui
    from CfdOF.CfdTools import if2Float
    from CfdOF.PreviewShapes import getPrevPointSize, initPrevPoint
    from pivy import coin


class TaskPanelCfdScalarTransportFunctions:
    """
    Task panel for adding solver scalar transport function objects
    """
    if FreeCAD.GuiUp:
        prev_point_move_node = coin.SoTranslation()
        prev_point_node = coin.SoSeparator()
    def __init__(self, obj):
        self.obj = obj
        self.analysis_obj = CfdTools.getParentAnalysisObject(obj)
        self.physics_model = CfdTools.getPhysicsModel(self.analysis_obj)
        self.material_objs = CfdTools.getMaterials(self.analysis_obj)

        ui_path = os.path.join(CfdTools.getModulePath(), 'Gui', "TaskPanelCfdScalarTransportFunctions.ui")
        self.form = FreeCADGui.PySideUic.loadUi(ui_path)
        self.form.inputInjectionPointx.valueChanged.connect(self.inputInjectionPointChanged)
        self.form.inputInjectionPointy.valueChanged.connect(self.inputInjectionPointChanged)
        self.form.inputInjectionPointz.valueChanged.connect(self.inputInjectionPointChanged)

        if hasattr(self.form.checkBoxDiffusivityFixed, "checkStateChanged"):
            self.form.checkBoxDiffusivityFixed.checkStateChanged.connect(self.diffusivityCheckBoxChanged)
        else:
            self.form.checkBoxDiffusivityFixed.stateChanged.connect(self.diffusivityCheckBoxChanged)
        
        self.load()
        self.updateUI()

    def load(self):
        self.form.inputScalarFieldName.setText(self.obj.FieldName)
        self.form.checkBoxDiffusivityFixed.setChecked(self.obj.DiffusivityFixed)
        self.diffusivityCheckBoxChanged()
        setQuantity(self.form.inputDiffusivity, self.obj.DiffusivityFixedValue)

        self.form.checkRestrictToPhase.setChecked(self.obj.RestrictToPhase)

        # Add phases
        mat_names = []
        for m in self.material_objs:
            mat_names.append(m.Label)
        self.form.comboPhase.clear()
        # Seems to be a restriction of the FO - can't use last (passive) phase
        self.form.comboPhase.addItems(mat_names[:-1])

        self.form.comboPhase.setCurrentIndex(indexOrDefault(mat_names, self.obj.PhaseName, 0))

        setQuantity(self.form.inputInjectionPointx, Units.Quantity(self.obj.InjectionPoint.x, Units.Length))
        setQuantity(self.form.inputInjectionPointy, Units.Quantity(self.obj.InjectionPoint.y, Units.Length))
        setQuantity(self.form.inputInjectionPointz, Units.Quantity(self.obj.InjectionPoint.z, Units.Length))

        setQuantity(self.form.inputInjectionRate, self.obj.InjectionRate)

        if FreeCAD.GuiUp:
            # create the point every time the taskpanel is loaded
            point_size = 5; # defualt value when there is no mesh object
            analysis_object = CfdTools.getParentAnalysisObject(self.obj)
            mesh_object = CfdTools.getMeshObject(analysis_object)
            if mesh_object is not None:
                point_size = getPrevPointSize(mesh_object.Part.Shape)
            initPrevPoint(self.prev_point_node, self.prev_point_move_node, point_size, 0, 1, 0,
                         if2Float(self.form.inputInjectionPointx),
                         if2Float(self.form.inputInjectionPointy),
                         if2Float(self.form.inputInjectionPointz))

    def updateUI(self):
        # Multiphase
        mp = (self.physics_model and self.physics_model.Phase != 'Single')
        self.form.checkRestrictToPhase.setVisible(mp)
        self.form.comboPhase.setVisible(mp)

    def diffusivityCheckBoxChanged(self):
        if self.form.checkBoxDiffusivityFixed.isChecked():
            self.form.inputDiffusivity.setVisible(True)
            self.form.specifiedCoefficientLabel.setVisible(True)
        else:
            self.form.inputDiffusivity.setVisible(False)
            self.form.specifiedCoefficientLabel.setVisible(False)

    def inputInjectionPointChanged(self):
        if FreeCAD.GuiUp:
            self.prev_point_move_node.translation.setValue(
                             if2Float(self.form.inputInjectionPointx),
                             if2Float(self.form.inputInjectionPointy),
                             if2Float(self.form.inputInjectionPointz))

    def accept(self):
        if FreeCAD.GuiUp:
            FreeCADGui.ActiveDocument.ActiveView.getSceneGraph().removeChild(self.prev_point_node)

        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()

        # Type
        storeIfChanged(self.obj, 'FieldName', self.form.inputScalarFieldName.text())
        storeIfChanged(self.obj, 'DiffusivityFixed', self.form.checkBoxDiffusivityFixed.isChecked())
        storeIfChanged(self.obj, 'DiffusivityFixedValue', getQuantity(self.form.inputDiffusivity))
        storeIfChanged(self.obj, 'RestrictToPhase', self.form.checkRestrictToPhase.isChecked())
        storeIfChanged(self.obj, 'PhaseName', self.form.comboPhase.currentText())

        injection_point = FreeCAD.Vector(
            self.form.inputInjectionPointx.property("quantity").Value,
            self.form.inputInjectionPointy.property("quantity").Value,
            self.form.inputInjectionPointz.property("quantity").Value)
        storeIfChanged(self.obj, 'InjectionPoint', injection_point)
        storeIfChanged(self.obj, 'InjectionRate', getQuantity(self.form.inputInjectionRate))

        # Finalise
        FreeCADGui.doCommand("FreeCAD.ActiveDocument.recompute()")

    def reject(self):
        if FreeCAD.GuiUp:
            FreeCADGui.ActiveDocument.ActiveView.getSceneGraph().removeChild(self.prev_point_node)

        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()
