# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2017 Johan Heyns (CSIR) <jheyns@csir.co.za>             *
# *   Copyright (c) 2017 Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>          *
# *   Copyright (c) 2017 Alfred Bogaers (CSIR) <abogaers@csir.co.za>        *
# *   Copyright (c) 2019-2022 Oliver Oxtoby <oliveroxtoby@gmail.com>        *
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
from PySide import QtGui
import os
import CfdTools
from CfdTools import getQuantity, setQuantity, indexOrDefault
import CfdFaceSelectWidget
import CfdMeshRefinement
from FreeCAD import Units


class _TaskPanelCfdMeshRefinement:
    """ The TaskPanel for editing References property of MeshRefinement objects """

    def __init__(self, obj):
        FreeCADGui.Selection.clearSelection()
        self.obj = obj
        self.mesh_obj = self.getMeshObject()

        self.form = FreeCADGui.PySideUic.loadUi(
            os.path.join(os.path.dirname(__file__), "core/gui/TaskPanelCfdMeshRefinement.ui"))

        self.ShapeRefsOrig = list(self.obj.ShapeRefs)

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
        self.form.if_expratio.setToolTip("Expansion ratio of boundary layers (limited to be greater than 1.0 and "
                                         "smaller than 1.2)")
        self.form.if_firstlayerheight.setToolTip("Maximum first cell height (ignored if set to 0.0)")
        self.form.if_edgerefinement.setToolTip("Number of edge or feature refinement levels")

        FreeCADGui.Selection.addObserver(self)
        self.last_selected_edge = None

        self.updateUI()

    def accept(self):
        FreeCADGui.Selection.removeObserver(self)
        FreeCADGui.ActiveDocument.resetEdit()
        FreeCAD.ActiveDocument.recompute()

        # Macro script
        FreeCADGui.doCommand("\nobj = FreeCAD.ActiveDocument.{}".format(self.obj.Name))
        FreeCADGui.doCommand("obj.RelativeLength = {}".format(self.form.if_rellen.value()))
        if not self.mesh_obj.MeshUtility == 'gmsh':
            FreeCADGui.doCommand("obj.RefinementThickness = '{}'".format(getQuantity(self.form.if_refinethick)))
            if self.form.check_boundlayer.isChecked():
                num_layers = self.form.if_numlayer.value()
            else:
                num_layers = 1
            FreeCADGui.doCommand("obj.NumberLayers = {}".format(num_layers))
            FreeCADGui.doCommand("obj.ExpansionRatio = {}".format(self.form.if_expratio.value()))
            FreeCADGui.doCommand("obj.FirstLayerHeight = '{}'".format(getQuantity(self.form.if_firstlayerheight)))
            FreeCADGui.doCommand("obj.RegionEdgeRefinement = {}".format(self.form.if_edgerefinement.value()))
            FreeCADGui.doCommand("obj.Internal = {}".format(self.form.volumeRefinementToggle.isChecked()))

        FreeCADGui.doCommand("obj.Extrusion = {}".format(self.form.extrusionToggle.isChecked()))
        if self.obj.Extrusion:
            FreeCADGui.doCommand("obj.ExtrusionType = '{}'".format(CfdMeshRefinement.EXTRUSION_TYPES[
                self.form.extrusionTypeCombo.currentIndex()]))
            FreeCADGui.doCommand("obj.KeepExistingMesh = {}".format(self.form.keepExistingMeshCheck.isChecked()))
            FreeCADGui.doCommand("obj.ExtrusionThickness = '{}'".format(getQuantity(self.form.thicknessInput)))
            FreeCADGui.doCommand("obj.ExtrusionAngle = '{}'".format(getQuantity(self.form.angleInput)))
            FreeCADGui.doCommand("obj.ExtrusionLayers = {}".format(self.form.numLayersInput.value()))
            FreeCADGui.doCommand("obj.ExtrusionRatio = {}".format(self.form.ratioInput.value()))
            FreeCADGui.doCommand("obj.ExtrusionAxisPoint.x = {}".format(
                self.form.axisPointXEdit.property("quantity").getValueAs("m")))
            FreeCADGui.doCommand("obj.ExtrusionAxisPoint.y = {}".format(
                self.form.axisPointYEdit.property("quantity").getValueAs("m")))
            FreeCADGui.doCommand("obj.ExtrusionAxisPoint.z = {}".format(
                self.form.axisPointZEdit.property("quantity").getValueAs("m")))
            FreeCADGui.doCommand("obj.ExtrusionAxisDirection.x = {}".format(
                self.form.axisDirectionXEdit.property("quantity").Value))
            FreeCADGui.doCommand("obj.ExtrusionAxisDirection.y = {}".format(
                self.form.axisDirectionYEdit.property("quantity").Value))
            FreeCADGui.doCommand("obj.ExtrusionAxisDirection.z = {}".format(
                self.form.axisDirectionZEdit.property("quantity").Value))

        refstr = "FreeCAD.ActiveDocument.{}.ShapeRefs = [\n".format(self.obj.Name)
        refstr += ',\n'.join(
            "(FreeCAD.ActiveDocument.getObject('{}'), {})".format(ref[0].Name, ref[1]) for ref in self.obj.ShapeRefs)
        refstr += "]"
        FreeCADGui.doCommand(refstr)
        FreeCADGui.doCommand("FreeCAD.ActiveDocument.recompute()")
        return True

    def reject(self):
        FreeCADGui.Selection.removeObserver(self)
        self.obj.ShapeRefs = self.ShapeRefsOrig
        FreeCADGui.ActiveDocument.resetEdit()
        FreeCAD.ActiveDocument.recompute()
        return True

    def load(self):
        """ fills the widgets """
        self.form.if_rellen.setValue(self.obj.RelativeLength)

        # Boundary layer refinement (SnappyHexMesh and CfMesh only)
        if not self.mesh_obj.MeshUtility == "gmsh":
            setQuantity(self.form.if_refinethick, self.obj.RefinementThickness)
            self.form.check_boundlayer.setChecked(self.obj.NumberLayers > 1)
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
        setQuantity(self.form.axisPointXEdit, "{} m".format(self.obj.ExtrusionAxisPoint.x))
        setQuantity(self.form.axisPointYEdit, "{} m".format(self.obj.ExtrusionAxisPoint.y))
        setQuantity(self.form.axisPointZEdit, "{} m".format(self.obj.ExtrusionAxisPoint.z))
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
                elif self.mesh_obj.MeshUtility == 'snappyHexMesh':
                    self.form.cf_frame.setVisible(True) # cf_frame includes boundarylayer_frame so we need to turn this on
                    self.form.snappy_frame.setVisible(True)
                    self.form.snappySurfaceFrame.setVisible(True)
            self.form.extrusionFrame.setVisible(False)
        self.updateSelectionButtonUI()

    def getMeshObject(self):
        analysis_obj = CfdTools.getActiveAnalysis()
        mesh_obj = CfdTools.getMeshObject(analysis_obj)
        if mesh_obj is None:
            message = "Mesh object not found - please re-create."
            QtGui.QMessageBox.critical(None, 'Missing mesh object', message)
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
