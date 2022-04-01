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

        # Store values which are changed on the fly for visual update
        self.ShapeRefsOrig = list(self.obj.ShapeRefs)
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
        setQuantity(self.form.inputReferencePressure, self.obj.ReferencePressure)
        setQuantity(self.form.inputDensity, self.obj.Density)
        setQuantity(self.form.inputPorosity, self.obj.IncludePorosity)
        setQuantity(self.form.inputWriteFields, self.obj.WriteFields)
        setQuantity(self.form.inputCentreOfRotationx, self.obj.CoRx)
        setQuantity(self.form.inputCentreOfRotationy, self.obj.CoRy)
        setQuantity(self.form.inputCentreOfRotationz, self.obj.CoRz)
        self.form.inputPressure.setToolTip("Pressure field name")
        self.form.inputVelocity.setToolTip("Velocity field name")
        self.form.inputDensity.setToolTip("Density field name")
        self.form.inputReferencePressure.setToolTip("Reference pressure")
        self.form.inputPorosity.setToolTip("Porosity")
        self.form.inputWriteFields.setToolTip("Write output fields")
        self.form.inputCentreOfRotationx.setToolTip("Centre of rotation vector for moments")

        # Force coefficients fo
        setQuantity(self.form.inputLiftDirectionx, self.obj.Liftx)
        setQuantity(self.form.inputLiftDirectiony, self.obj.Lifty)
        setQuantity(self.form.inputLiftDirectionz, self.obj.Liftz)
        setQuantity(self.form.inputDragDirectionx, self.obj.Dragx)
        setQuantity(self.form.inputDragDirectiony, self.obj.Dragy)
        setQuantity(self.form.inputDragDirectionz, self.obj.Dragz)
        setQuantity(self.form.inputPitchAxisx, self.obj.Pitchx)
        setQuantity(self.form.inputPitchAxisy, self.obj.Pitchy)
        setQuantity(self.form.inputPitchAxisz, self.obj.Pitchz)
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
        setQuantity(self.form.inputDirection, self.obj.Direction)
        setQuantity(self.form.inputCumulative, self.obj.Cumulative)
        self.form.inputNBins.setToolTip("Number of bins")
        self.form.inputDirection.setToolTip("Direction")
        self.form.inputCumulative.setToolTip("Cumulative")

        # Face list selection panel - modifies obj.ShapeRefs passed to it
        self.faceSelector = CfdFaceSelectWidget.CfdFaceSelectWidget(self.form.faceSelectWidget,
                                                                    self.obj, True, True, False)

        self.updateUI()

    def updateUI(self):
        # Function object type
        type_index = self.form.comboFunctionObjectType.currentIndex()
        type_name = self.form.comboFunctionObjectType.currentText()
        force_frame_enabled = CfdFunctionObjects.BOUNDARY_UI[type_index][0]
        coefficient_frame_enabled = CfdFunctionObjects.BOUNDARY_UI[type_index][1]
        bin_frame_enabled = CfdFunctionObjects.BOUNDARY_UI[type_index][2]

        self.form.fieldNamesFrame.setVisible(force_frame_enabled)
        self.form.spatialFrame.setVisible(bin_frame_enabled)

        if type_name == 'Force coefficients':
            self.form.coefficientFrame.setVisible(coefficient_frame_enabled)

    def comboFunctionObjectTypeChanged(self):
        index = self.form.comboFunctionObjectType.currentIndex()
        self.obj.FunctionObjectType = CfdFunctionObjects.OBJECT_NAMES[self.form.comboFunctionObjectType.currentIndex()]
        self.form.functionObjectDescription.setText(CfdFunctionObjects.OBJECT_DESCRIPTIONS[index])

        # # Change the color of the boundary condition as the selection is made
        # doc_name = str(self.obj.Document.Name)
        # FreeCAD.getDocument(doc_name).recompute()

    def addSelection(self, doc_name, obj_name, sub, selected_point=None):
        # This is the direction selection
        if not self.selecting_direction:
            # Shouldn't be here
            return

        if FreeCADGui.activeDocument().Document.Name != self.obj.Document.Name:
            return

        selected_object = FreeCAD.getDocument(doc_name).getObject(obj_name)
        # On double click on a vertex of a solid sub is None and obj is the solid
        print('Selection: ' +
              selected_object.Shape.ShapeType + '  ' +
              selected_object.Name + ':' +
              sub + " @ " + str(selected_point))

        if hasattr(selected_object, "Shape") and sub:
            elt = selected_object.Shape.getElement(sub)
            if elt.ShapeType == 'Face':
                selection = (selected_object.Name, sub)
                if self.selecting_direction:
                    if CfdTools.isPlanar(elt):
                        self.selecting_direction = False
                        self.form.lineDirection.setText(
                            selection[0] + ':' + selection[1])  # TODO: Display label, not name
                    else:
                        FreeCAD.Console.PrintMessage('Face must be planar\n')

        self.form.buttonDirection.setChecked(self.selecting_direction)

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

        # Force object
        FreeCADGui.doCommand("fo.Pressure "
                             "= '{}'".format(self.form.inputPressure))
        FreeCADGui.doCommand("fo.Velocity "
                             "= '{}'".format(self.form.inputVelocity))
        FreeCADGui.doCommand("fo.Density "
                             "= '{}'".format(getQuantity(self.form.inputDensity)))
        FreeCADGui.doCommand("fo.ReferencePressure "
                             "= '{}'".format(getQuantity(self.form.inputReferencePressure)))
        FreeCADGui.doCommand("fo.IncludePorosity "
                             "= {}".format(self.form.inputPorosity.isChecked()))
        FreeCADGui.doCommand("fo.WriteFields "
                             "= {}".format(self.form.inputWriteFields.isChecked()))
        FreeCADGui.doCommand("fo.CoRx "
                             "= '{}'".format(getQuantity(self.form.inputCentreOfRotationx)))
        FreeCADGui.doCommand("fo.CoRy "
                             "= '{}'".format(getQuantity(self.form.inputCentreOfRotationy)))
        FreeCADGui.doCommand("fo.CoRz "
                             "= '{}'".format(getQuantity(self.form.inputCentreOfRotationz)))

        # # Coefficient object
        FreeCADGui.doCommand("fo.Liftx "
                             "= '{}'".format(getQuantity(self.form.inputLiftDirectionx)))
        FreeCADGui.doCommand("fo.Lifty "
                             "= '{}'".format(getQuantity(self.form.inputLiftDirectiony)))
        FreeCADGui.doCommand("fo.Liftz "
                             "= '{}'".format(getQuantity(self.form.inputLiftDirectionz)))
        FreeCADGui.doCommand("fo.Dragx "
                             "= '{}'".format(getQuantity(self.form.inputDragDirectionx)))
        FreeCADGui.doCommand("fo.Dragy "
                             "= '{}'".format(getQuantity(self.form.inputDragDirectiony)))
        FreeCADGui.doCommand("fo.Dragz "
                             "= '{}'".format(getQuantity(self.form.inputDragDirectionz)))
        FreeCADGui.doCommand("fo.Pitchx "
                             "= '{}'".format(getQuantity(self.form.inputPitchAxisx)))
        FreeCADGui.doCommand("fo.Pitchy "
                             "= '{}'".format(getQuantity(self.form.inputPitchAxisy)))
        FreeCADGui.doCommand("fo.Pitchz "
                             "= '{}'".format(getQuantity(self.form.inputPitchAxisz)))
        FreeCADGui.doCommand("fo.MagnitudeUInf "
                             "= '{}'".format(getQuantity(self.form.inputMagnitudeUInf)))
        FreeCADGui.doCommand("fo.LengthRef "
                             "= '{}'".format(getQuantity(self.form.inputLengthRef)))
        FreeCADGui.doCommand("fo.AreaRef "
                             "= '{}'".format(getQuantity(self.form.inputAreaRef)))

        # # Spatial binning
        FreeCADGui.doCommand("fo.NBins "
                             "= '{}'".format(getQuantity(self.form.inputNBins)))
        FreeCADGui.doCommand("fo.Direction "
                             "= '{}'".format(getQuantity(self.form.inputDirection)))
        FreeCADGui.doCommand("fo.Cumulative "
                             "= {}".format(self.form.inputCumulative.isChecked()))


        refstr = "FreeCAD.ActiveDocument.{}.ShapeRefs = [\n".format(self.obj.Name)
        refstr += ',\n'.join(
            "(FreeCAD.ActiveDocument.getObject('{}'), {})".format(ref[0].Name, ref[1]) for ref in self.obj.ShapeRefs)
        refstr += "]"
        FreeCADGui.doCommand(refstr)

        # Finalise
        FreeCADGui.doCommand("FreeCAD.ActiveDocument.recompute()")
        self.faceSelector.closing()

    def reject(self):
        self.obj.ShapeRefs = self.ShapeRefsOrig
        self.obj.FunctionObjectType = self.FunctionObjectTypeOrig
        FreeCADGui.Selection.removeObserver(self)
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc_name = str(self.obj.Document.Name)
        FreeCAD.getDocument(doc_name).recompute()
        doc.resetEdit()
        self.faceSelector.closing()
        return True
