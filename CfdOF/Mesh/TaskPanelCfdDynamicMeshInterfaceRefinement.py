# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2022 Jonathan Bergh <bergh.jonathan@gmail.com>          *
# *   Copyright (c) 2022 Oliver Oxtoby <oliveroxtoby@gmail.com>             *
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
from math import ceil
import FreeCADGui
from CfdOF import CfdTools
from CfdOF.CfdTools import indexOrDefault, setQuantity, getQuantity, storeIfChanged


class TaskPanelCfdDynamicMeshInterfaceRefinement:
    def __init__(self, obj, physics_model, material_objs):
        FreeCADGui.Selection.clearSelection()
        self.obj = obj

        self.physics_model = physics_model
        self.material_objs = material_objs

        self.form = FreeCADGui.PySideUic.loadUi(
                    os.path.join(CfdTools.getModulePath(), 'Gui', "TaskPanelCfdDynamicMeshInterfaceRefinement.ui"))

        self.load()

        FreeCADGui.Selection.addObserver(self)

        self.updateUI()

    def load(self):
        """ fills the widgets """

        # Add volume fraction fields
        if self.physics_model.Phase != 'Single':
            mat_names = []
            for m in self.material_objs:
                mat_names.append(m.Label)
            self.form.cb_fluid.clear()
            items = mat_names[:-1]
            self.form.cb_fluid.addItems(items)
            idx = indexOrDefault(items, self.obj.Phase, 0)
            self.form.cb_fluid.setCurrentIndex(idx)
        else:
            self.form.cb_fluid.clear()
        self.form.sb_refinement_interval.setValue(self.obj.RefinementInterval)
        self.form.sb_max_refinement_levels.setValue(self.obj.MaxRefinementLevel)
        self.form.sb_no_buffer_layers.setValue(self.obj.BufferLayers)
        self.form.cb_write_refinement_volscalarfield.setChecked(self.obj.WriteFields)

    def updateUI(self):
        pass

    def accept(self):
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()

        storeIfChanged(self.obj, 'Phase', self.form.cb_fluid.currentText())
        storeIfChanged(self.obj, 'RefinementInterval', int(self.form.sb_refinement_interval.value()))
        storeIfChanged(self.obj, 'MaxRefinementLevel', int(self.form.sb_max_refinement_levels.value()))
        storeIfChanged(self.obj, 'BufferLayers', int(self.form.sb_no_buffer_layers.value()))
        storeIfChanged(self.obj, 'WriteFields', self.form.cb_write_refinement_volscalarfield.isChecked())

        # Finalise
        FreeCADGui.doCommand("FreeCAD.ActiveDocument.recompute()")

    def reject(self):
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()

