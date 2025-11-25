# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileNotice: Part of the CfdOF addon.

################################################################################
#                                                                              #
#   Copyright (c) 2022 Jonathan Bergh <bergh.jonathan@gmail.com>               #
#   Copyright (c) 2022 Oliver Oxtoby <oliveroxtoby@gmail.com>                  #
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

import FreeCAD
import os
import os.path
from CfdOF import CfdTools
from CfdOF.CfdTools import getQuantity, setQuantity, storeIfChanged, indexOrDefault
if FreeCAD.GuiUp:
    import FreeCADGui


class TaskPanelCfdScalarTransportFunctions:
    """
    Task panel for adding solver scalar transport function objects
    """
    def __init__(self, obj):
        self.obj = obj
        self.analysis_obj = CfdTools.getParentAnalysisObject(obj)
        self.physics_model = CfdTools.getPhysicsModel(self.analysis_obj)
        self.material_objs = CfdTools.getMaterials(self.analysis_obj)

        ui_path = os.path.join(CfdTools.getModulePath(), 'Gui', "TaskPanelCfdScalarTransportFunctions.ui")
        self.form = FreeCADGui.PySideUic.loadUi(ui_path)
        
        self.load()
        self.updateUI()

    def load(self):
        self.form.inputScalarFieldName.setText(self.obj.FieldName)
        if self.obj.DiffusivityFixed:
            self.form.radioUniformDiffusivity.toggle()
        else:
            self.form.radioViscousDiffusivity.toggle()
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

        setQuantity(self.form.inputInjectionPointx, self.obj.InjectionPoint.x)
        setQuantity(self.form.inputInjectionPointy, self.obj.InjectionPoint.y)
        setQuantity(self.form.inputInjectionPointz, self.obj.InjectionPoint.z)

        setQuantity(self.form.inputInjectionRate, self.obj.InjectionRate)

    def updateUI(self):
        # Multiphase
        mp = (self.physics_model and self.physics_model.Phase != 'Single')
        self.form.checkRestrictToPhase.setVisible(mp)
        self.form.comboPhase.setVisible(mp)

    def accept(self):
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()

        # Type
        storeIfChanged(self.obj, 'FieldName', self.form.inputScalarFieldName.text())
        storeIfChanged(self.obj, 'DiffusivityFixed', self.form.radioUniformDiffusivity.isChecked())
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
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()
