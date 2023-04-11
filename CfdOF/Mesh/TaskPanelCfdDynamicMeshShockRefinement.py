# ***************************************************************************
# *                                                                         *
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
import FreeCAD
import FreeCADGui
from CfdOF import CfdTools
from CfdOF.CfdTools import setQuantity, getQuantity, storeIfChanged


class TaskPanelCfdDynamicMeshShockRefinement:
    def __init__(self, obj, physics_model, material_objs):
        FreeCADGui.Selection.clearSelection()
        self.obj = obj

        self.physics_model = physics_model
        self.material_objs = material_objs

        self.form = FreeCADGui.PySideUic.loadUi(
                    os.path.join(CfdTools.getModulePath(), 'Gui', "TaskPanelCfdDynamicMeshShockRefinement.ui"))

        self.load()

        FreeCADGui.Selection.addObserver(self)

        self.updateUI()

    def load(self):
        """ fills the widgets """

        setQuantity(self.form.inputReferenceVelocityX, self.obj.ReferenceVelocityDirection.x)
        setQuantity(self.form.inputReferenceVelocityY, self.obj.ReferenceVelocityDirection.y)
        setQuantity(self.form.inputReferenceVelocityZ, self.obj.ReferenceVelocityDirection.z)
        self.form.sbRelativeElementSize.setValue(self.obj.RelativeElementSize)
        self.form.sbRefinementInterval.setValue(getattr(self.obj, 'RefinementInterval'+self.physics_model.Time))
        self.form.sbNumBufferLayers.setValue(self.obj.BufferLayers)
        self.form.cbWriteRefinementField.setChecked(self.obj.WriteFields)

    def updateUI(self):
        pass

    def accept(self):
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()

        ref_dir = FreeCAD.Vector(
            self.form.inputReferenceVelocityX.property("quantity").Value,
            self.form.inputReferenceVelocityY.property("quantity").Value,
            self.form.inputReferenceVelocityZ.property("quantity").Value)
        storeIfChanged(self.obj, 'ReferenceVelocityDirection', ref_dir)
        storeIfChanged(self.obj, 'RelativeElementSize', float(self.form.sbRelativeElementSize.value()))
        storeIfChanged(self.obj, 'RefinementInterval'+self.physics_model.Time, int(self.form.sbRefinementInterval.value()))
        storeIfChanged(self.obj, 'BufferLayers', int(self.form.sbNumBufferLayers.value()))
        storeIfChanged(self.obj, 'WriteFields', self.form.cbWriteRefinementField.isChecked())

        # Finalise
        FreeCADGui.doCommand("FreeCAD.ActiveDocument.recompute()")

    def reject(self):
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()

