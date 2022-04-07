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

PERMISSIBLE_SOLVER_FIELDS = ['gradP', 'gradU']


class _TaskPanelCfdDynamicMeshRefinement:
    """ The TaskPanel for editing References property of MeshRefinement objects """

    def __init__(self, obj):
        FreeCADGui.Selection.clearSelection()
        self.obj = obj
        # self.mesh_obj = self.getMeshObject()

        self.form = FreeCADGui.PySideUic.loadUi(
            os.path.join(os.path.dirname(__file__), "../../gui/TaskPanelCfdDynamicMeshRefinement.ui"))

        self.ShapeRefsOrig = list(self.obj.ShapeRefs)

        self.form.cb_write_refinement_volscalarfield.stateChanged.connect(self.updateUI)
        self.form.sb_max_refinement_levels.stateChanged.connect(self.updateUI)
        self.form.sb_no_buffer_layers.stateChanged.connect(self.updateUI)
        self.form.sb_refinement_interval.stateChanged.connect(self.updateUI)

        self.form.cb_refinement_field.stateChanged.connect(self.updateUI)
        self.form.if_lower_refinement.stateChanged.connect(self.updateUI)
        self.form.if_upper_refinement.stateChanged.connect(self.updateUI)
        self.form.if_unrefine_level.stateChanged.connect(self.updateUI)

        self.load()

        FreeCADGui.Selection.addObserver(self)
        self.last_selected_edge = None

        self.updateUI()

    def accept(self):
        FreeCADGui.Selection.removeObserver(self)
        FreeCADGui.ActiveDocument.resetEdit()

        # Macro script
        FreeCADGui.doCommand("\nobj = FreeCAD.ActiveDocument.{}".format(self.obj.Name))
        FreeCADGui.doCommand("obj.RefinementInterval = {}".format(self.form.sb_refinement_interval))
        FreeCADGui.doCommand("obj.MaxRefinementLevel = {}".format(self.form.sb_max_refinement_levels))
        FreeCADGui.doCommand("obj.BufferLayers = {}".format(self.form.sb_no_buffer_layers))
        FreeCADGui.doCommand("obj.MaxRefinementCells = {}".format(self.form.if_max_cells))
        FreeCADGui.doCommand("obj.RefinementField = {}".format(self.form.cb_refinement_field))
        FreeCADGui.doCommand("obj.LowerRefinementLevel = {}".format(self.form.if_lower_refinement))
        FreeCADGui.doCommand("obj.UpperRefinementLevel = {}".format(self.form.if_upper_refinement))
        FreeCADGui.doCommand("obj.UnRefinementLevel = {}".format(self.form.if_unrefine_level))
        FreeCADGui.doCommand("obj.WriteFields = {}".format(self.form.cb_write_refinement_volscalarfield))

        return True

    def reject(self):
        FreeCADGui.Selection.removeObserver(self)
        self.obj.ShapeRefs = self.ShapeRefsOrig
        FreeCADGui.ActiveDocument.resetEdit()
        FreeCAD.ActiveDocument.recompute()
        return True

    def load(self):
        """ fills the widgets """
        # Mesh controls
        self.form.sb_refinement_interval.setValue(self.obj.RefinementInterval)
        self.form.sb_max_refinement_levels.setValue(self.obj.MaxRefinementLevel)
        self.form.sb_no_buffer_layers.setValue(self.obj.BufferLayers)
        self.form.if_max_cells.setText(self.obj.MaxRefinementCells)

        # Trigger field
        # self.form.cb_refinement_field.setValue(self.obj.RefinementField) # leave for now, find index etc
        self.form.if_unrefine_level.setValue(self.obj.UnRefinementLevel)
        self.form.if_lower_refinement.setValue(self.obj.LowerRefinementLevel)
        self.form.if_upper_refinement.setValue(self.obj.UpperRefinementLevel)

        self.form.cb_write_refinement_volscalarfield.setChecked(self.obj.WriteFields)

    def updateUI(self):
        # We dont need to do anything to the UI at this stage
        pass

    def changeInternal(self):
        self.obj.ShapeRefs.clear()
        self.faceSelector.rebuildReferenceList()
        self.solidSelector.rebuildReferenceList()
        self.updateUI()

