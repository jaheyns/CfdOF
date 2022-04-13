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
import os
import os.path
import CfdTools
from CfdTools import getQuantity, setQuantity, indexOrDefault
import CfdFaceSelectWidget
from core.functionobjects import CfdFunctionObjects
if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtGui
    from PySide.QtGui import QFormLayout


class TaskPanelCfdFunctionObjects:
    """
    Task panel for adding solver function objects
    """
    def __init__(self, obj):
        self.selecting_direction = False
        self.obj = obj
        self.analysis_obj = CfdTools.getActiveAnalysis()

        # Store values which are changed on the fly for visual update
        # self.ShapeRefsOrig = list(self.obj.ShapeRefs)
        self.FunctionObjectTypeOrig = str(self.obj.FunctionObjectType)

        ui_path = os.path.join(os.path.dirname(__file__), "../gui/TaskPanelCfdFunctionObjects.ui")
        self.form = FreeCADGui.PySideUic.loadUi(ui_path)

        # Function Object types
        self.form.comboFunctionObjectType.addItems(CfdFunctionObjects.OBJECT_NAMES)
        bi = indexOrDefault(CfdFunctionObjects.OBJECT_NAMES, self.obj.FunctionObjectType, 0)
        self.form.comboFunctionObjectType.currentIndexChanged.connect(self.comboFunctionObjectTypeChanged)
        self.form.comboFunctionObjectType.setCurrentIndex(bi)
        self.comboFunctionObjectTypeChanged()

        # Set the inputs for various function objects
        # Force fo
        self.form.inputPressure.setText(self.obj.Pressure)
        self.form.inputVelocity.setText(self.obj.Velocity)
        self.form.inputDensity.setText(self.obj.Density)
        setQuantity(self.form.inputReferencePressure, self.obj.ReferencePressure)
        setQuantity(self.form.inputPorosity, self.obj.IncludePorosity)
        setQuantity(self.form.inputWriteFields, self.obj.WriteFields)
        setQuantity(self.form.inputCentreOfRotationx, self.obj.CoR.x)
        setQuantity(self.form.inputCentreOfRotationy, self.obj.CoR.y)
        setQuantity(self.form.inputCentreOfRotationz, self.obj.CoR.z)
        self.form.inputPressure.setToolTip("Pressure field name")
        self.form.inputVelocity.setToolTip("Velocity field name")
        self.form.inputDensity.setToolTip("Density field name")
        self.form.inputReferencePressure.setToolTip("Reference pressure")
        self.form.inputPorosity.setToolTip("Porosity")
        self.form.inputWriteFields.setToolTip("Write output fields")
        self.form.inputCentreOfRotationx.setToolTip("Centre of rotation vector for moments")

        # Force coefficients fo
        setQuantity(self.form.inputLiftDirectionx, self.obj.Lift.x)
        setQuantity(self.form.inputLiftDirectiony, self.obj.Lift.y)
        setQuantity(self.form.inputLiftDirectionz, self.obj.Lift.z)
        setQuantity(self.form.inputDragDirectionx, self.obj.Drag.x)
        setQuantity(self.form.inputDragDirectiony, self.obj.Drag.y)
        setQuantity(self.form.inputDragDirectionz, self.obj.Drag.z)
        setQuantity(self.form.inputPitchAxisx, self.obj.Pitch.x)
        setQuantity(self.form.inputPitchAxisy, self.obj.Pitch.y)
        setQuantity(self.form.inputPitchAxisz, self.obj.Pitch.z)
        setQuantity(self.form.inputMagnitudeUInf, self.obj.MagnitudeUInf)
        setQuantity(self.form.inputLengthRef, self.obj.LengthRef)
        setQuantity(self.form.inputAreaRef, self.obj.AreaRef)
        self.form.inputLiftDirectionx.setToolTip("Lift direction vector")
        self.form.inputDragDirectionx.setToolTip("Drag direction vector")
        self.form.inputPitchAxisx.setToolTip("Pitch axis for moment coefficient")
        self.form.inputMagnitudeUInf.setToolTip("Velocity magnitude reference")
        self.form.inputLengthRef.setToolTip("Length reference")
        self.form.inputAreaRef.setToolTip("Area reference")

        # Spatial binning
        setQuantity(self.form.inputNBins, self.obj.NBins)
        setQuantity(self.form.inputDirectionx, self.obj.Direction.x)
        setQuantity(self.form.inputDirectiony, self.obj.Direction.y)
        setQuantity(self.form.inputDirectionz, self.obj.Direction.z)
        setQuantity(self.form.inputCumulative, self.obj.Cumulative)
        self.form.inputNBins.setToolTip("Number of bins")
        self.form.inputDirectionx.setToolTip("Binning direction")
        self.form.inputCumulative.setToolTip("Cumulative")
        self.form.cb_patch_list.setToolTip("Patch (BC) group to monitor")

        self.list_of_bcs = [bc.Label for bc in CfdTools.getCfdBoundaryGroup(self.analysis_obj)]
        self.form.cb_patch_list.addItems(self.list_of_bcs)

        self.load()
        self.updateUI()

    def load(self):
        try:
            previous_index = self.list_of_bcs.index(self.obj.PatchName)
            self.form.cb_patch_list.setCurrentIndex(previous_index)
        except:
            pass

        self.form.inputPressure.setText(self.obj.Pressure)
        self.form.inputVelocity.setText(self.obj.Velocity)
        self.form.inputDensity.setText(self.obj.Density)
        setQuantity(self.form.inputReferencePressure, self.obj.ReferencePressure)
        self.form.inputPorosity.setChecked(self.obj.IncludePorosity)
        self.form.inputWriteFields.setChecked(self.obj.WriteFields)

        setQuantity(self.form.inputCentreOfRotationx, self.obj.CoR.x)
        setQuantity(self.form.inputCentreOfRotationy, self.obj.CoR.y)
        setQuantity(self.form.inputCentreOfRotationz, self.obj.CoR.z)

        setQuantity(self.form.inputLiftDirectionx, self.obj.Lift.x)
        setQuantity(self.form.inputLiftDirectiony, self.obj.Lift.y)
        setQuantity(self.form.inputLiftDirectionz, self.obj.Lift.z)

        setQuantity(self.form.inputDragDirectionx, self.obj.Drag.x)
        setQuantity(self.form.inputDragDirectiony, self.obj.Drag.y)
        setQuantity(self.form.inputDragDirectionz, self.obj.Drag.z)

        setQuantity(self.form.inputPitchAxisx, self.obj.Pitch.x)
        setQuantity(self.form.inputPitchAxisy, self.obj.Pitch.y)
        setQuantity(self.form.inputPitchAxisz, self.obj.Pitch.z)

        setQuantity(self.form.inputMagnitudeUInf, self.obj.MagnitudeUInf)
        setQuantity(self.form.inputLengthRef, self.obj.LengthRef)
        setQuantity(self.form.inputAreaRef, self.obj.AreaRef)

        setQuantity(self.form.inputNBins, self.obj.NBins)
        setQuantity(self.form.inputDirectionx, self.obj.Direction.x)
        setQuantity(self.form.inputDirectiony, self.obj.Direction.y)
        setQuantity(self.form.inputDirectionz, self.obj.Direction.z)
        self.form.inputCumulative.setChecked(self.obj.Cumulative)

    def updateUI(self):
        # Function object type
        type_index = self.form.comboFunctionObjectType.currentIndex()
        field_name_frame_enabled = CfdFunctionObjects.BOUNDARY_UI[type_index][0]
        coefficient_frame_enabled = CfdFunctionObjects.BOUNDARY_UI[type_index][1]
        spatial_bin_frame_enabled = CfdFunctionObjects.BOUNDARY_UI[type_index][2]

        self.form.fieldNamesFrame.setVisible(field_name_frame_enabled)
        self.form.coefficientFrame.setVisible(coefficient_frame_enabled)
        self.form.spatialFrame.setVisible(spatial_bin_frame_enabled)

    def comboFunctionObjectTypeChanged(self):
        index = self.form.comboFunctionObjectType.currentIndex()
        self.obj.FunctionObjectType = CfdFunctionObjects.OBJECT_NAMES[self.form.comboFunctionObjectType.currentIndex()]
        self.form.functionObjectDescription.setText(CfdFunctionObjects.OBJECT_DESCRIPTIONS[index])

        self.updateUI()

    def accept(self):
        if self.obj.Label.startswith("CfdFunctionObjects"):
            self.obj.Label = self.obj.BoundaryType
        FreeCADGui.Selection.removeObserver(self)

        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()

        FreeCADGui.doCommand("\nfo = FreeCAD.ActiveDocument.{}".format(self.obj.Name))
        # Type
        FreeCADGui.doCommand("fo.FunctionObjectType "
                             "= '{}'".format(self.obj.FunctionObjectType))
        FreeCADGui.doCommand("fo.PatchName "
                             "= '{}'".format(self.form.cb_patch_list.currentText()))

        # Force object
        FreeCADGui.doCommand("fo.Pressure "
                             "= '{}'".format(self.form.inputPressure.text()))
        FreeCADGui.doCommand("fo.Velocity "
                             "= '{}'".format(self.form.inputVelocity.text()))
        FreeCADGui.doCommand("fo.Density "
                             "= '{}'".format(self.form.inputDensity.text()))
        FreeCADGui.doCommand("fo.ReferencePressure "
                             "= '{}'".format(getQuantity(self.form.inputReferencePressure)))
        FreeCADGui.doCommand("fo.IncludePorosity "
                             "= {}".format(self.form.inputPorosity.isChecked()))
        FreeCADGui.doCommand("fo.WriteFields "
                             "= {}".format(self.form.inputWriteFields.isChecked()))
        FreeCADGui.doCommand("fo.CoR.x "
                             "= '{}'".format(self.form.inputCentreOfRotationx.property("quantity").Value))
        FreeCADGui.doCommand("fo.CoR.y "
                             "= '{}'".format(self.form.inputCentreOfRotationy.property("quantity").Value))
        FreeCADGui.doCommand("fo.CoR.z "
                             "= '{}'".format(self.form.inputCentreOfRotationz.property("quantity").Value))

        # # Coefficient object
        FreeCADGui.doCommand("fo.Lift.x "
                             "= '{}'".format(self.form.inputLiftDirectionx.property("quantity").Value))
        FreeCADGui.doCommand("fo.Lift.y "
                             "= '{}'".format(self.form.inputLiftDirectiony.property("quantity").Value))
        FreeCADGui.doCommand("fo.Lift.z "
                             "= '{}'".format(self.form.inputLiftDirectionz.property("quantity").Value))
        FreeCADGui.doCommand("fo.Drag.x "
                             "= '{}'".format(self.form.inputDragDirectionx.property("quantity").Value))
        FreeCADGui.doCommand("fo.Drag.y "
                             "= '{}'".format(self.form.inputDragDirectiony.property("quantity").Value))
        FreeCADGui.doCommand("fo.Drag.z "
                             "= '{}'".format(self.form.inputDragDirectionz.property("quantity").Value))
        FreeCADGui.doCommand("fo.Pitch.x "
                             "= '{}'".format(self.form.inputPitchAxisx.property("quantity").Value))
        FreeCADGui.doCommand("fo.Pitch.y "
                             "= '{}'".format(self.form.inputPitchAxisy.property("quantity").Value))
        FreeCADGui.doCommand("fo.Pitch.z "
                             "= '{}'".format(self.form.inputPitchAxisz.property("quantity").Value))
        FreeCADGui.doCommand("fo.MagnitudeUInf "
                             "= '{}'".format(getQuantity(self.form.inputMagnitudeUInf)))
        FreeCADGui.doCommand("fo.LengthRef "
                             "= '{}'".format(getQuantity(self.form.inputLengthRef)))
        FreeCADGui.doCommand("fo.AreaRef "
                             "= '{}'".format(getQuantity(self.form.inputAreaRef)))

        # # Spatial binning
        FreeCADGui.doCommand("fo.NBins "
                             "= '{}'".format(getQuantity(self.form.inputNBins)))
        FreeCADGui.doCommand("fo.Direction.x "
                             "= '{}'".format(self.form.inputDirectionx.property("quantity").Value))
        FreeCADGui.doCommand("fo.Direction.y "
                             "= '{}'".format(self.form.inputDirectiony.property("quantity").Value))
        FreeCADGui.doCommand("fo.Direction.z "
                             "= '{}'".format(self.form.inputDirectionz.property("quantity").Value))
        FreeCADGui.doCommand("fo.Cumulative "
                             "= {}".format(self.form.inputCumulative.isChecked()))

        # Finalise
        FreeCADGui.doCommand("FreeCAD.ActiveDocument.recompute()")
        # self.faceSelector.closing()

    def reject(self):
        self.obj.FunctionObjectType = self.FunctionObjectTypeOrig
        FreeCADGui.Selection.removeObserver(self)
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc_name = str(self.obj.Document.Name)
        FreeCAD.getDocument(doc_name).recompute()
        doc.resetEdit()
        return True
