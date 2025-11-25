# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileNotice: Part of the CfdOF addon.

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
import os.path
import FreeCAD
from FreeCAD import Units
from CfdOF import CfdTools
from CfdOF.CfdTools import getQuantity, setQuantity, indexOrDefault, storeIfChanged
from CfdOF.PostProcess import CfdReportingFunction
if FreeCAD.GuiUp:
    import FreeCADGui


class TaskPanelCfdReportingFunction:
    """
    Task panel for adding solver function objects
    """
    def __init__(self, obj):
        self.obj = obj
        self.analysis_obj = CfdTools.getActiveAnalysis()
        self.physics_obj = CfdTools.getPhysicsModel(self.analysis_obj)

        ui_path = os.path.join(CfdTools.getModulePath(), 'Gui', "TaskPanelCfdReportingFunctions.ui")
        self.form = FreeCADGui.PySideUic.loadUi(ui_path)

        # Function Object types
        self.form.comboFunctionObjectType.addItems(CfdReportingFunction.OBJECT_NAMES)
        self.form.comboFunctionObjectType.currentIndexChanged.connect(self.comboFunctionObjectTypeChanged)

        self.form.inputReferencePressure.setToolTip("Reference pressure")
        self.form.inputWriteFields.setToolTip("Write output fields")
        self.form.inputCentreOfRotationx.setToolTip("Centre of rotation vector for moments")

        self.form.inputLiftDirectionx.setToolTip("Lift direction vector")
        self.form.inputDragDirectionx.setToolTip("Drag direction vector")
        self.form.inputMagnitudeUInf.setToolTip("Velocity magnitude reference")
        self.form.inputReferenceDensity.setToolTip("Density reference")
        self.form.inputLengthRef.setToolTip("Length reference")
        self.form.inputAreaRef.setToolTip("Area reference")

        self.form.inputNBins.setToolTip("Number of bins")
        self.form.inputDirectionx.setToolTip("Binning direction")
        self.form.inputCumulative.setToolTip("Cumulative")
        self.form.cb_patch_list.setToolTip("Patch (BC) group to monitor")

        self.list_of_bcs = [bc.Label for bc in CfdTools.getCfdBoundaryGroup(self.analysis_obj)]
        self.form.cb_patch_list.addItems(self.list_of_bcs)

        self.load()
        self.updateUI()

    def load(self):
        bi = indexOrDefault(CfdReportingFunction.OBJECT_NAMES, self.obj.ReportingFunctionType, 0)
        self.form.comboFunctionObjectType.setCurrentIndex(bi)
        self.comboFunctionObjectTypeChanged()
        
        if self.obj.Patch:
            index = self.list_of_bcs.index(self.obj.Patch.Label)
            self.form.cb_patch_list.setCurrentIndex(index)

        setQuantity(self.form.inputReferenceDensity, self.obj.ReferenceDensity)
        setQuantity(self.form.inputReferencePressure, self.obj.ReferencePressure)
        self.form.inputWriteFields.setChecked(self.obj.WriteFields)

        setQuantity(self.form.inputCentreOfRotationx, Units.Quantity(self.obj.CentreOfRotation.x, Units.Length))
        setQuantity(self.form.inputCentreOfRotationy, Units.Quantity(self.obj.CentreOfRotation.y, Units.Length))
        setQuantity(self.form.inputCentreOfRotationz, Units.Quantity(self.obj.CentreOfRotation.z, Units.Length))

        setQuantity(self.form.inputLiftDirectionx, self.obj.Lift.x)
        setQuantity(self.form.inputLiftDirectiony, self.obj.Lift.y)
        setQuantity(self.form.inputLiftDirectionz, self.obj.Lift.z)

        setQuantity(self.form.inputDragDirectionx, self.obj.Drag.x)
        setQuantity(self.form.inputDragDirectiony, self.obj.Drag.y)
        setQuantity(self.form.inputDragDirectionz, self.obj.Drag.z)

        setQuantity(self.form.inputMagnitudeUInf, self.obj.MagnitudeUInf)
        setQuantity(self.form.inputLengthRef, self.obj.LengthRef)
        setQuantity(self.form.inputAreaRef, self.obj.AreaRef)

        self.form.inputNBins.setValue(self.obj.NBins)
        setQuantity(self.form.inputDirectionx, self.obj.Direction.x)
        setQuantity(self.form.inputDirectiony, self.obj.Direction.y)
        setQuantity(self.form.inputDirectionz, self.obj.Direction.z)
        self.form.inputCumulative.setChecked(self.obj.Cumulative)

        self.form.inputFieldName.setText(self.obj.SampleFieldName)
        setQuantity(self.form.inputProbeLocx, Units.Quantity(self.obj.ProbePosition.x, Units.Length))
        setQuantity(self.form.inputProbeLocy, Units.Quantity(self.obj.ProbePosition.y, Units.Length))
        setQuantity(self.form.inputProbeLocz, Units.Quantity(self.obj.ProbePosition.z, Units.Length))

    def updateUI(self):
        # Function object type
        type_index = self.form.comboFunctionObjectType.currentIndex()
        self.form.stackedWidget.setCurrentIndex(CfdReportingFunction.FUNCTIONS_UI[type_index])
        if type_index < len(CfdReportingFunction.FORCES_UI):
            field_name_frame_enabled = CfdReportingFunction.FORCES_UI[type_index][0]
            coefficient_frame_enabled = CfdReportingFunction.FORCES_UI[type_index][1]
            spatial_bin_frame_enabled = CfdReportingFunction.FORCES_UI[type_index][2]
            self.form.fieldNamesFrame.setVisible(field_name_frame_enabled)
            self.form.coefficientFrame.setVisible(coefficient_frame_enabled)
            self.form.spatialFrame.setVisible(spatial_bin_frame_enabled)

        if self.physics_obj.Flow == 'Isothermal':
            self.form.inputReferenceDensity.setVisible(False)
            self.form.labelRefDensity.setVisible(False)
        else:
            self.form.inputReferenceDensity.setVisible(True)
            self.form.labelRefDensity.setVisible(True)

    def comboFunctionObjectTypeChanged(self):
        index = self.form.comboFunctionObjectType.currentIndex()
        self.form.functionObjectDescription.setText(CfdReportingFunction.OBJECT_DESCRIPTIONS[index])
        self.updateUI()

    def accept(self):
        FreeCADGui.Selection.removeObserver(self)

        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()

        # Type
        index = self.form.comboFunctionObjectType.currentIndex()
        storeIfChanged(self.obj, 'ReportingFunctionType', CfdReportingFunction.OBJECT_NAMES[index])

        bcs = CfdTools.getCfdBoundaryGroup(self.analysis_obj)
        bc = bcs[self.form.cb_patch_list.currentIndex()]
        if (not self.obj.Patch and bc) or (bc and bc.Name != self.obj.Patch.Name):
            FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.Patch "
                                 "= FreeCAD.ActiveDocument.{}".format(self.obj.Name, bc.Name))

        # Force object
        storeIfChanged(self.obj, 'ReferenceDensity', getQuantity(self.form.inputReferenceDensity))
        storeIfChanged(self.obj, 'ReferencePressure', getQuantity(self.form.inputReferencePressure))
        storeIfChanged(self.obj, 'WriteFields', self.form.inputWriteFields.isChecked())
        centre_of_rotation = FreeCAD.Vector(
            self.form.inputCentreOfRotationx.property("quantity").Value,
            self.form.inputCentreOfRotationy.property("quantity").Value,
            self.form.inputCentreOfRotationz.property("quantity").Value)
        storeIfChanged(self.obj, 'CentreOfRotation', centre_of_rotation)

        # # Coefficient object
        lift_dir = FreeCAD.Vector(
            self.form.inputLiftDirectionx.property("quantity").Value,
            self.form.inputLiftDirectiony.property("quantity").Value,
            self.form.inputLiftDirectionz.property("quantity").Value)
        storeIfChanged(self.obj, 'Lift', lift_dir)
        drag_dir = FreeCAD.Vector(
            self.form.inputDragDirectionx.property("quantity").Value,
            self.form.inputDragDirectiony.property("quantity").Value,
            self.form.inputDragDirectionz.property("quantity").Value)
        storeIfChanged(self.obj, 'Drag', drag_dir)
        storeIfChanged(self.obj, 'MagnitudeUInf', getQuantity(self.form.inputMagnitudeUInf))
        storeIfChanged(self.obj, 'LengthRef', getQuantity(self.form.inputLengthRef))
        storeIfChanged(self.obj, 'AreaRef', getQuantity(self.form.inputAreaRef))

        # # Spatial binning
        storeIfChanged(self.obj, 'NBins', self.form.inputNBins.value())
        bins_direction = FreeCAD.Vector(
            self.form.inputDirectionx.property("quantity").Value,
            self.form.inputDirectiony.property("quantity").Value,
            self.form.inputDirectionz.property("quantity").Value)
        storeIfChanged(self.obj, 'Direction', bins_direction)
        storeIfChanged(self.obj, 'Cumulative', self.form.inputCumulative.isChecked())

        # Probe info
        storeIfChanged(self.obj, 'SampleFieldName', self.form.inputFieldName.text())
        probe_position = FreeCAD.Vector(
            self.form.inputProbeLocx.property("quantity").Value,
            self.form.inputProbeLocy.property("quantity").Value,
            self.form.inputProbeLocz.property("quantity").Value)
        storeIfChanged(self.obj, 'ProbePosition', probe_position)

        # Finalise
        FreeCADGui.doCommand("FreeCAD.ActiveDocument.recompute()")

    def reject(self):
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc_name = str(self.obj.Document.Name)
        FreeCAD.getDocument(doc_name).recompute()
        doc.resetEdit()
        return True
