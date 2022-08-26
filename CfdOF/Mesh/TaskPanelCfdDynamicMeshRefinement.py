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
from CfdOF.CfdTools import setQuantity, getQuantity


class TaskPanelCfdDynamicMeshRefinement:
    def __init__(self, obj):
        FreeCADGui.Selection.clearSelection()
        self.obj = obj


        self.form = FreeCADGui.PySideUic.loadUi(
                    os.path.join(CfdTools.getModulePath(), 'Gui', "TaskPanelCfdDynamicMeshRefinement.ui"))

        self.load()

        FreeCADGui.Selection.addObserver(self)

        self.updateUI()

    def load(self):
        """ fills the widgets """

        # Mesh controls
        self.form.sb_refinement_interval.setValue(self.obj.RefinementInterval)
        self.form.sb_max_refinement_levels.setValue(self.obj.MaxRefinementLevel)
        self.form.sb_no_buffer_layers.setValue(self.obj.BufferLayers)
        setQuantity(self.form.if_max_cells, self.obj.MaxRefinementCells)

        # Trigger field
        self.form.le_refinement_field.setText(self.obj.RefinementField)
        setQuantity(self.form.if_unrefine_level, self.obj.UnRefinementLevel)
        setQuantity(self.form.if_lower_refinement, self.obj.LowerRefinementLevel)
        setQuantity(self.form.if_upper_refinement, self.obj.UpperRefinementLevel)

        self.form.cb_write_refinement_volscalarfield.setChecked(self.obj.WriteFields)

    def updateUI(self):
        pass

    def accept(self):
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()

        # Macro script
        FreeCADGui.doCommand("\nobj = FreeCAD.ActiveDocument.{}".format(self.obj.Name))
        FreeCADGui.doCommand("obj.RefinementInterval = {}".format(int(self.form.sb_refinement_interval.value())))
        FreeCADGui.doCommand("obj.MaxRefinementLevel = {}".format(int(self.form.sb_max_refinement_levels.value())))
        FreeCADGui.doCommand("obj.BufferLayers = {}".format(int(self.form.sb_no_buffer_layers.value())))
        FreeCADGui.doCommand(
            "obj.MaxRefinementCells = {}".format(int(ceil(float(getQuantity(self.form.if_max_cells))))))
        FreeCADGui.doCommand("obj.RefinementField = '{}'".format(self.form.le_refinement_field.text()))
        FreeCADGui.doCommand("obj.LowerRefinementLevel = {}".format(getQuantity(self.form.if_lower_refinement)))
        FreeCADGui.doCommand("obj.UpperRefinementLevel = {}".format(getQuantity(self.form.if_upper_refinement)))
        FreeCADGui.doCommand("obj.UnRefinementLevel = {}".format(int(float(getQuantity(self.form.if_unrefine_level)))))
        FreeCADGui.doCommand("obj.WriteFields = {}".format(self.form.cb_write_refinement_volscalarfield.isChecked()))

        # Finalise
        FreeCADGui.doCommand("FreeCAD.ActiveDocument.recompute()")

    def reject(self):
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()

