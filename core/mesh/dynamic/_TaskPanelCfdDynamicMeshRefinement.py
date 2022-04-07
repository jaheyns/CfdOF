# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2022 Jonathan Bergh <bergh.jonathan@gmail.com>          *
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
import FreeCADGui
import os
from CfdTools import setQuantity, getQuantity

PERMISSIBLE_SOLVER_FIELDS = ['gradP', 'gradU']


class _TaskPanelCfdDynamicMeshRefinement:
    """ The TaskPanel for editing References property of MeshRefinement objects """

    def __init__(self, obj):
        FreeCADGui.Selection.clearSelection()
        self.obj = obj
        # self.mesh_obj = self.getMeshObject()

        self.form = FreeCADGui.PySideUic.loadUi(
            os.path.join(os.path.dirname(__file__), "../../gui/TaskPanelCfdDynamicMeshRefinement.ui"))

        self.load()

        FreeCADGui.Selection.addObserver(self)
        self.last_selected_edge = None

        self.updateUI()

    def accept(self):
        FreeCADGui.Selection.removeObserver(self)
        FreeCADGui.ActiveDocument.resetEdit()

        # Macro script
        FreeCADGui.doCommand("\nobj = FreeCAD.ActiveDocument.{}".format(self.obj.Name))
        FreeCADGui.doCommand("obj.RefinementInterval = {}".format(self.form.sb_refinement_interval.value()))
        FreeCADGui.doCommand("obj.MaxRefinementLevel = {}".format(self.form.sb_max_refinement_levels.value()))
        FreeCADGui.doCommand("obj.BufferLayers = {}".format(self.form.sb_no_buffer_layers.value()))
        FreeCADGui.doCommand("obj.MaxRefinementCells = {}".format(self.form.if_max_cells.text()))
        FreeCADGui.doCommand("obj.RefinementField = '{}'".format(self.form.cb_refinement_field.currentText()))
        FreeCADGui.doCommand("obj.LowerRefinementLevel = {}".format(getQuantity(self.form.if_lower_refinement)))
        FreeCADGui.doCommand("obj.UpperRefinementLevel = {}".format(getQuantity(self.form.if_upper_refinement)))
        FreeCADGui.doCommand("obj.UnRefinementLevel = {}".format(getQuantity(self.form.if_unrefine_level)))
        FreeCADGui.doCommand("obj.WriteFields = {}".format(self.form.cb_write_refinement_volscalarfield.isChecked()))

        return True

    def reject(self):
        FreeCADGui.Selection.removeObserver(self)
        FreeCADGui.ActiveDocument.resetEdit()
        FreeCAD.ActiveDocument.recompute()
        return True

    def load(self):
        """ fills the widgets """
        # Mesh controls
        self.form.sb_refinement_interval.setValue(self.obj.RefinementInterval)
        self.form.sb_max_refinement_levels.setValue(self.obj.MaxRefinementLevel)
        self.form.sb_no_buffer_layers.setValue(self.obj.BufferLayers)
        setQuantity(self.form.if_max_cells, self.obj.MaxRefinementCells)

        # Trigger field
        # self.form.cb_refinement_field.setValue(self.obj.RefinementField) # leave for now, find index etc
        setQuantity(self.form.if_unrefine_level, self.obj.UnRefinementLevel)
        setQuantity(self.form.if_lower_refinement, self.obj.LowerRefinementLevel)
        setQuantity(self.form.if_upper_refinement, self.obj.UpperRefinementLevel)

        self.form.cb_write_refinement_volscalarfield.setChecked(self.obj.WriteFields)

    def updateUI(self):
        # We dont need to do anything to the UI at this stage
        pass

    def changeInternal(self):
        self.obj.ShapeRefs.clear()
        self.faceSelector.rebuildReferenceList()
        self.solidSelector.rebuildReferenceList()
        self.updateUI()

