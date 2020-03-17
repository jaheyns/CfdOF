# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2016 - Bernd Hahnebach <bernd@bimstatik.org>            *
# *   Copyright (c) 2017 Johan Heyns (CSIR) <jheyns@csir.co.za>             *
# *   Copyright (c) 2017 Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>          *
# *   Copyright (c) 2017 Alfred Bogaers (CSIR) <abogaers@csir.co.za>        *
# *   Copyright (c) 2019 Oliver Oxtoby <oliveroxtoby@gmail.com>             *
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
from CfdTools import getQuantity, setQuantity
import CfdFaceSelectWidget


class _TaskPanelCfdMeshRefinement:
    """ The TaskPanel for editing References property of MeshRefinement objects """

    def __init__(self, obj):
        FreeCADGui.Selection.clearSelection()
        self.sel_server = None
        self.obj = obj
        self.mesh_obj = self.getMeshObject()

        self.form = FreeCADGui.PySideUic.loadUi(
            os.path.join(os.path.dirname(__file__), "TaskPanelCfdMeshRefinement.ui"))

        self.ReferencesOrig = list(self.obj.References)

        # Face list selection panel - modifies obj.References passed to it
        self.faceSelector = CfdFaceSelectWidget.CfdFaceSelectWidget(self.form.referenceSelectWidget,
                                                                    self.obj, True, False,
                                                                    self.mesh_obj.MeshUtility == 'gmsh',
                                                                    self.mesh_obj.MeshUtility == 'gmsh')

        self.solidSelector = CfdFaceSelectWidget.CfdFaceSelectWidget(self.form.volReferenceSelectWidget,
                                                                     self.obj,
                                                                     False,
                                                                     True)

        self.form.baffle_check.stateChanged.connect(self.updateUI)

        self.form.check_boundlayer.stateChanged.connect(self.updateUI)

        tool_tip_mes = "Cell size relative to base cell size"
        self.form.if_rellen.setToolTip(tool_tip_mes)
        self.form.label_rellen.setToolTip(tool_tip_mes)

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
        self.form.baffle_check.setToolTip("Create a zero thickness baffle")

        self.updateUI()

    def accept(self):
        if self.sel_server:
            FreeCADGui.Selection.removeObserver(self.sel_server)
        FreeCADGui.ActiveDocument.resetEdit()
        FreeCAD.ActiveDocument.recompute()
        # Macro script
        FreeCADGui.doCommand("referenceList = []")
        for ref in self.obj.References:
            FreeCADGui.doCommand("referenceList.append(('{}','{}'))".format(ref[0], ref[1]))
        FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.References = referenceList".format(self.obj.Name))
        FreeCADGui.doCommand("\nFreeCAD.ActiveDocument.{}.RelativeLength "
                             "= {}".format(self.obj.Name, self.form.if_rellen.value()))
        if self.mesh_obj.MeshUtility != 'gmsh':
            FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.RefinementThickness "
                                 "= '{}'".format(self.obj.Name, getQuantity(self.form.if_refinethick)))
            if self.form.check_boundlayer.isChecked():
                num_layers = self.form.if_numlayer.value()
            else:
                num_layers = 1
            FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.NumberLayers "
                                 "= {}".format(self.obj.Name, num_layers))
            FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.ExpansionRatio "
                                 "= {}".format(self.obj.Name, self.form.if_expratio.value()))
            FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.FirstLayerHeight "
                                 "= '{}'".format(self.obj.Name, getQuantity(self.form.if_firstlayerheight)))
            FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.RegionEdgeRefinement "
                                 "= {}".format(self.obj.Name, self.form.if_edgerefinement.value()))
            FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.Baffle "
                                 "= {}".format(self.obj.Name, self.form.baffle_check.isChecked()))
            FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.Internal "
                                 "= {}".format(self.obj.Name, self.form.volumeRefinementToggle.isChecked()))
        return True

    def reject(self):
        self.obj.References = self.ReferencesOrig
        if self.sel_server:
            FreeCADGui.Selection.removeObserver(self.sel_server)
        FreeCADGui.ActiveDocument.resetEdit()

        doc_name = str(self.obj.Document.Name)
        FreeCAD.getDocument(doc_name).recompute()
        return True

    def load(self):
        """ fills the widgets """
        self.form.if_rellen.setValue(self.obj.RelativeLength)
        if not self.mesh_obj.MeshUtility == "gmsh":
            setQuantity(self.form.if_refinethick, self.obj.RefinementThickness)
            self.form.check_boundlayer.setChecked(self.obj.NumberLayers > 1)
            self.form.if_numlayer.setValue(self.obj.NumberLayers)
            self.form.if_expratio.setValue(self.obj.ExpansionRatio)
            setQuantity(self.form.if_firstlayerheight, self.obj.FirstLayerHeight)

            self.form.if_edgerefinement.setValue(self.obj.RegionEdgeRefinement)
            self.form.baffle_check.setChecked(self.obj.Baffle)
            if self.obj.Internal:
                self.form.volumeRefinementToggle.toggle()

    def updateUI(self):
        self.form.surfaceOrInernalVolume.setVisible(True)
        self.form.boundlayer_frame.setVisible(self.form.check_boundlayer.isChecked())
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
                self.form.cf_frame.setVisible(False)
                self.form.snappy_frame.setVisible(True)
                self.form.snappySurfaceFrame.setVisible(True)

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
        self.obj.References.clear()
        self.faceSelector.rebuildReferenceList()
        self.solidSelector.rebuildReferenceList()
        self.updateUI()
