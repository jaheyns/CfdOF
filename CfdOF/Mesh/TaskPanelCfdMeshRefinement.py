# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2017 Johan Heyns (CSIR) <jheyns@csir.co.za>             *
# *   Copyright (c) 2017 Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>          *
# *   Copyright (c) 2017 Alfred Bogaers (CSIR) <abogaers@csir.co.za>        *
# *   Copyright (c) 2019-2022 Oliver Oxtoby <oliveroxtoby@gmail.com>        *
# *   Copyright (c) 2022 Jonathan Bergh <bergh.jonathan@gmail.com>          *
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

import FreeCAD
import FreeCADGui
from PySide import QtGui
import os
from CfdOF import CfdTools
from CfdOF.CfdTools import getQuantity, setQuantity, indexOrDefault, storeIfChanged
from CfdOF import CfdFaceSelectWidget
from CfdOF.Mesh import CfdMeshRefinement
from FreeCAD import Units

translate = FreeCAD.Qt.translate

class TaskPanelCfdMeshRefinement:
    """ The TaskPanel for editing References property of MeshRefinement objects """

    def __init__(self, obj):
        FreeCADGui.Selection.clearSelection()
        self.obj = obj
        self.mesh_obj = self.getMeshObject()
        self.analysis_obj = CfdTools.getParentAnalysisObject(obj)

        self.form = FreeCADGui.PySideUic.loadUi(
            os.path.join(CfdTools.getModulePath(), 'Gui', "TaskPanelCfdMeshRefinement.ui"))

        self.ShapeRefsOrig = list(self.obj.ShapeRefs)
        self.ShapeOrig = self.obj.Shape
        self.NeedsMeshRewriteOrig = self.analysis_obj.NeedsMeshRewrite

        # Face list selection panel - modifies obj.References passed to it
        self.faceSelector = CfdFaceSelectWidget.CfdFaceSelectWidget(self.form.referenceSelectWidget,
                                                                    self.obj,
                                                                    self.mesh_obj.MeshUtility != 'gmsh',
                                                                    True,
                                                                    False,
                                                                    self.mesh_obj.MeshUtility == 'gmsh',
                                                                    self.mesh_obj.MeshUtility == 'gmsh')

        self.solidSelector = CfdFaceSelectWidget.CfdFaceSelectWidget(self.form.volReferenceSelectWidget,
                                                                     self.obj,
                                                                     False,
                                                                     False,
                                                                     True)

        self.form.check_boundlayer.stateChanged.connect(self.updateUI)

        self.form.extrusionTypeCombo.addItems(CfdMeshRefinement.EXTRUSION_NAMES)
        self.form.extrusionTypeCombo.currentIndexChanged.connect(self.updateUI)
        self.form.pickAxisButton.clicked.connect(self.pickFromSelection)

        self.form.if_rellen.setToolTip("Cell size relative to base cell size")
        self.form.label_rellen.setToolTip("Cell size relative to base cell size")

        self.load()

        self.form.surfaceRefinementToggle.toggled.connect(self.changeInternal)
        self.form.volumeRefinementToggle.toggled.connect(self.changeInternal)

        self.form.if_refinethick.setToolTip("Distance the refinement region extends from the reference "
                                            "surface")
        self.form.if_numlayer.setToolTip("Number of boundary layers if the reference surface is an external or "
                                         "mesh patch")
        self.form.if_expratio.setToolTip("Expansion ratio of boundary layers")
        self.form.if_firstlayerheight.setToolTip("Maximum first cell height (ignored if set to 0.0)")
        self.form.if_edgerefinement.setToolTip("Number of edge or feature refinement levels")

        FreeCADGui.Selection.addObserver(self)
        self.last_selected_edge = None

        self.updateUI()

    def load(self):
        """ fills the widgets """
        self.form.if_rellen.setValue(self.obj.RelativeLength)

        # Boundary layer refinement (SnappyHexMesh and CfMesh only)
        if not self.mesh_obj.MeshUtility == "gmsh":
            setQuantity(self.form.if_refinethick, self.obj.RefinementThickness)
            self.form.check_boundlayer.setChecked(self.obj.NumberLayers > 0)
            self.form.if_numlayer.setValue(self.obj.NumberLayers)
            self.form.if_expratio.setValue(self.obj.ExpansionRatio)
            setQuantity(self.form.if_firstlayerheight, self.obj.FirstLayerHeight)

            self.form.if_edgerefinement.setValue(self.obj.RegionEdgeRefinement)
            if self.obj.Internal:
                self.form.volumeRefinementToggle.toggle()

        # Extrusion refinement
        if self.obj.Extrusion:
            self.form.extrusionToggle.toggle()

        self.form.extrusionTypeCombo.setCurrentIndex(
            indexOrDefault(CfdMeshRefinement.EXTRUSION_TYPES, self.obj.ExtrusionType, 0))

        self.form.keepExistingMeshCheck.setChecked(self.obj.KeepExistingMesh)
        setQuantity(self.form.thicknessInput, self.obj.ExtrusionThickness)
        setQuantity(self.form.angleInput, self.obj.ExtrusionAngle)

        self.form.numLayersInput.setValue(self.obj.ExtrusionLayers)
        self.form.ratioInput.setValue(self.obj.ExtrusionRatio)
        setQuantity(self.form.axisPointXEdit, Units.Quantity(self.obj.ExtrusionAxisPoint.x, Units.Length))
        setQuantity(self.form.axisPointYEdit, Units.Quantity(self.obj.ExtrusionAxisPoint.y, Units.Length))
        setQuantity(self.form.axisPointZEdit, Units.Quantity(self.obj.ExtrusionAxisPoint.z, Units.Length))
        setQuantity(self.form.axisDirectionXEdit, self.obj.ExtrusionAxisDirection.x)
        setQuantity(self.form.axisDirectionYEdit, self.obj.ExtrusionAxisDirection.y)
        setQuantity(self.form.axisDirectionZEdit, self.obj.ExtrusionAxisDirection.z)

    def updateUI(self):
        self.form.surfaceOrInernalVolume.setVisible(True)
        self.form.boundlayer_frame.setVisible(self.form.check_boundlayer.isChecked())
        self.form.commonFrame.setVisible(True)

        # Extrusion refinement
        if self.form.extrusionToggle.isChecked():
            self.form.extrusionFrame.setVisible(True)
            self.form.commonFrame.setVisible(False)
            self.form.cf_frame.setVisible(False)
            self.form.snappy_frame.setVisible(False)
            self.form.ReferencesFrame.setVisible(True)
            self.form.cartesianInternalVolumeFrame.setVisible(False)

            type_index = self.form.extrusionTypeCombo.currentIndex()
            selected_rows = CfdMeshRefinement.EXTRUSION_UI[type_index]
            CfdTools.enableLayoutRows(self.form.extrusionLayout, selected_rows + [0])

        # Volume or surface refinement
        else:
            if self.mesh_obj.MeshUtility == 'gmsh':
                self.form.cartesianInternalVolumeFrame.setVisible(False)
                self.form.cf_frame.setVisible(False)
                self.form.snappy_frame.setVisible(False)
            if self.form.volumeRefinementToggle.isChecked():
                self.form.cf_frame.setVisible(False)
                self.form.snappy_frame.setVisible(False)
                self.form.ReferencesFrame.setVisible(False)
                self.form.cartesianInternalVolumeFrame.setVisible(True)
                if self.mesh_obj.MeshUtility == 'cfMesh':
                    self.form.cf_frame.setVisible(False)
                elif self.mesh_obj.MeshUtility == 'snappyHexMesh':
                    self.form.snappy_frame.setVisible(True)
                    self.form.snappySurfaceFrame.setVisible(False)
            else:
                self.form.ReferencesFrame.setVisible(True)
                self.form.cartesianInternalVolumeFrame.setVisible(False)
                if self.mesh_obj.MeshUtility == 'cfMesh':
                    self.form.cf_frame.setVisible(True)
                    self.form.snappy_frame.setVisible(False)
                    self.form.if_firstlayerheight.setEnabled(True)
                elif self.mesh_obj.MeshUtility == 'snappyHexMesh':
                    self.form.cf_frame.setVisible(True)
                    self.form.snappy_frame.setVisible(True)
                    self.form.snappySurfaceFrame.setVisible(True)
                    self.form.if_firstlayerheight.setEnabled(False)

            self.form.extrusionFrame.setVisible(False)
        self.updateSelectionButtonUI()

    def getMeshObject(self):
        analysis_obj = CfdTools.getActiveAnalysis()
        mesh_obj = CfdTools.getMeshObject(analysis_obj)
        if mesh_obj is None:
            message = translate("Dialogs", "Mesh object not found - please re-create.")
            QtGui.QMessageBox.critical(None, translate("Dialogs", "Missing mesh object"), message)
            doc = FreeCADGui.getDocument(self.obj.Document)
            doc.resetEdit()
        return mesh_obj

    def changeInternal(self):
        self.obj.ShapeRefs.clear()
        self.faceSelector.rebuildReferenceList()
        self.solidSelector.rebuildReferenceList()
        self.updateUI()

    def addSelection(self, doc_name, obj_name, sub, selected_point):
        self.updateSelectionButtonUI()

    def updateSelectionButtonUI(self):
        self.form.pickAxisButton.setEnabled(False)
        sel = FreeCADGui.Selection.getSelectionEx()
        if len(sel) == 1:
            sel = sel[0]
            if sel.HasSubObjects:
                if sel.HasSubObjects and len(sel.SubElementNames) == 1:
                    sub = sel.SubElementNames[0]
                    selected_object = FreeCAD.getDocument(sel.DocumentName).getObject(sel.ObjectName)
                    if hasattr(selected_object, "Shape"):
                        if not selected_object.Shape.isNull():
                            if not sub.startswith('Solid'):  # getElement doesn't work for solids
                                elt = selected_object.Shape.getElement(sub)
                                if elt.ShapeType == 'Edge':
                                    self.last_selected_edge = elt
                                    self.form.pickAxisButton.setEnabled(True)

    def pickFromSelection(self):
        p0 = self.last_selected_edge.Vertexes[0].Point
        p1 = self.last_selected_edge.Vertexes[1].Point
        ax = p1-p0
        ax /= max(ax.Length, 1e-8)
        setQuantity(self.form.axisPointXEdit, p0.x)
        setQuantity(self.form.axisPointYEdit, p0.y)
        setQuantity(self.form.axisPointZEdit, p0.z)
        setQuantity(self.form.axisDirectionXEdit, ax.x)
        setQuantity(self.form.axisDirectionYEdit, ax.y)
        setQuantity(self.form.axisDirectionZEdit, ax.z)

    def accept(self):
        FreeCADGui.Selection.removeObserver(self)
        self.obj.Shape = self.ShapeOrig
        # Make sure shape is re-calculated before leaving edit mode
        FreeCAD.ActiveDocument.recompute()
        self.analysis_obj.NeedsMeshRewrite = self.NeedsMeshRewriteOrig
        FreeCADGui.ActiveDocument.resetEdit()

        # Macro script
        storeIfChanged(self.obj, 'RelativeLength', self.form.if_rellen.value())
        if not self.mesh_obj.MeshUtility == 'gmsh':
            storeIfChanged(self.obj, 'RefinementThickness', getQuantity(self.form.if_refinethick))

            if self.form.check_boundlayer.isChecked():
                num_layers = self.form.if_numlayer.value()
            else:
                num_layers = 0
            storeIfChanged(self.obj, 'NumberLayers', num_layers)
            storeIfChanged(self.obj, 'ExpansionRatio', self.form.if_expratio.value())
            storeIfChanged(self.obj, 'FirstLayerHeight', getQuantity(self.form.if_firstlayerheight))
            storeIfChanged(self.obj, 'RegionEdgeRefinement', self.form.if_edgerefinement.value())
            storeIfChanged(self.obj, 'Internal', self.form.volumeRefinementToggle.isChecked())

        storeIfChanged(self.obj, 'Extrusion', self.form.extrusionToggle.isChecked())
        if self.obj.Extrusion:
            storeIfChanged(self.obj, 'ExtrusionType',
                CfdMeshRefinement.EXTRUSION_TYPES[self.form.extrusionTypeCombo.currentIndex()])
            storeIfChanged(self.obj, 'KeepExistingMesh', self.form.keepExistingMeshCheck.isChecked())
            storeIfChanged(self.obj, 'ExtrusionThickness', getQuantity(self.form.thicknessInput))
            storeIfChanged(self.obj, 'ExtrusionAngle', getQuantity(self.form.angleInput))
            storeIfChanged(self.obj, 'ExtrusionLayers', self.form.numLayersInput.value())
            storeIfChanged(self.obj, 'ExtrusionRatio', self.form.ratioInput.value())
            new_point = FreeCAD.Vector(
                self.form.axisPointXEdit.property("quantity").Value,
                self.form.axisPointYEdit.property("quantity").Value,
                self.form.axisPointZEdit.property("quantity").Value)
            if self.obj.ExtrusionAxisPoint != new_point:
                FreeCADGui.doCommand(
                    "App.ActiveDocument.{}.ExtrusionAxisPoint = App.{}".format(self.obj.Name, new_point))
            new_dir = FreeCAD.Vector(
                self.form.axisDirectionXEdit.property("quantity").Value,
                self.form.axisDirectionYEdit.property("quantity").Value,
                self.form.axisDirectionZEdit.property("quantity").Value)
            if self.obj.ExtrusionAxisDirection != new_dir:
                FreeCADGui.doCommand(
                    "App.ActiveDocument.{}.ExtrusionAxisDirection = App.{}".format(self.obj.Name, new_dir))

        if self.obj.ShapeRefs != self.ShapeRefsOrig:
            refstr = "FreeCAD.ActiveDocument.{}.ShapeRefs = [\n".format(self.obj.Name)
            refstr += ',\n'.join(
                "(FreeCAD.ActiveDocument.getObject('{}'), {})".format(ref[0].Name, ref[1]) for ref in self.obj.ShapeRefs)
            refstr += "]"
            FreeCADGui.doCommand(refstr)

        FreeCADGui.doCommand("FreeCAD.ActiveDocument.recompute()")
        return True

    def reject(self):
        self.obj.ShapeRefs = self.ShapeRefsOrig
        self.obj.Shape = self.ShapeOrig
        self.analysis_obj.NeedsMeshRewrite = self.NeedsMeshRewriteOrig
        # Make sure shape is re-calculated before leaving edit mode
        FreeCAD.ActiveDocument.recompute()
        FreeCADGui.ActiveDocument.resetEdit()
        return True

    def closing(self):
        # We call this from unsetEdit to ensure cleanup
        FreeCADGui.Selection.removeObserver(self)
        self.faceSelector.closing()
