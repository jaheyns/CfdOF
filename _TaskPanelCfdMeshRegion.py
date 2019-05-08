# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2016 - Bernd Hahnebach <bernd@bimstatik.org>            *
# *   Copyright (c) 2017 - Johan Heyns (CSIR) <jheyns@csir.co.za>           *
# *   Copyright (c) 2017 - Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>        *
# *   Copyright (c) 2017 - Alfred Bogaers (CSIR) <abogaers@csir.co.za>      *
# *   Copyright (c) 2019 - Oliver Oxtoby <oliveroxtoby@gmail.com>           *
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


class _TaskPanelCfdMeshRegion:
    '''The TaskPanel for editing References property of MeshRegion objects'''
    def __init__(self, obj):
        FreeCADGui.Selection.clearSelection()
        self.sel_server = None
        self.obj = obj
        self.mesh_obj = self.getMeshObject()

        self.form = FreeCADGui.PySideUic.loadUi(os.path.join(os.path.dirname(__file__), "TaskPanelCfdMeshRegion.ui"))

        self.form.baffle_check.stateChanged.connect(self.updateUI)

        self.form.check_boundlayer.stateChanged.connect(self.updateUI)

        tool_tip_mes = "Cell size relative to base cell size"
        self.form.if_rellen.setToolTip(tool_tip_mes)
        self.form.label_rellen.setToolTip(tool_tip_mes)

        self.InternalOrig = self.obj.Internal
        self.InternalRegionOrig = self.obj.InternalRegion.copy()

        self.validTypesOfInternalPrimitives = ["Box", "Sphere", "Cone"]

        self.form.internalVolumePrimitiveSelection.addItems(self.validTypesOfInternalPrimitives)

        self.form.internalVolumePrimitiveSelection.currentIndexChanged.connect(self.internalTypeChanged)
        self.form.surfaceRefinementToggle.toggled.connect(self.change_internal_surface)
        self.form.volumeRefinementToggle.toggled.connect(self.change_internal_surface)

        self.load()

        # Adding the following changed events to allow for real time update of the internal shape
        self.form.radius.valueChanged.connect(self.internalParameterChanged)
        self.form.xCenter.valueChanged.connect(self.internalParameterChanged)
        self.form.yCenter.valueChanged.connect(self.internalParameterChanged)
        self.form.zCenter.valueChanged.connect(self.internalParameterChanged)
        self.form.xLength.valueChanged.connect(self.internalParameterChanged)
        self.form.yLength.valueChanged.connect(self.internalParameterChanged)
        self.form.zLength.valueChanged.connect(self.internalParameterChanged)
        self.form.xPoint1.valueChanged.connect(self.internalParameterChanged)
        self.form.yPoint1.valueChanged.connect(self.internalParameterChanged)
        self.form.zPoint1.valueChanged.connect(self.internalParameterChanged)
        self.form.xPoint2.valueChanged.connect(self.internalParameterChanged)
        self.form.yPoint2.valueChanged.connect(self.internalParameterChanged)
        self.form.zPoint2.valueChanged.connect(self.internalParameterChanged)
        self.form.radius1.valueChanged.connect(self.internalParameterChanged)
        self.form.radius2.valueChanged.connect(self.internalParameterChanged)

        self.form.if_refinethick.setToolTip("Distance the refinement region extends from the reference "
                                            "surface")
        self.form.if_numlayer.setToolTip("Number of boundary layers if the reference surface is an external or "
                                         "mesh patch")
        self.form.if_expratio.setToolTip("Expansion ratio of boundary layers (limited to be greater than 1.0 and "
                                         "smaller than 1.2)")
        self.form.if_firstlayerheight.setToolTip("Maximum first cell height (ignored if set to 0.0)")
        self.form.if_edgerefinement.setToolTip("Number of edge or feature refinement levels")
        self.form.baffle_check.setToolTip("Create a zero thickness baffle")

        self.ReferencesOrig = list(self.obj.References)

        # Face list selection panel - modifies obj.References passed to it
        self.faceSelector = CfdFaceSelectWidget.CfdFaceSelectWidget(self.form.referenceSelectWidget,
                                                                    self.obj,
                                                                    True,
                                                                    self.mesh_obj.MeshUtility == 'gmsh',
                                                                    self.mesh_obj.MeshUtility == 'gmsh',
                                                                    self.mesh_obj.MeshUtility == 'gmsh')

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
                                 "= {}".format(self.obj.Name, self.obj.Internal))
            FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.InternalRegion "
                                 "= {}".format(self.obj.Name, self.obj.InternalRegion))
        return True

    def reject(self):
        self.obj.References = self.ReferencesOrig
        if self.sel_server:
            FreeCADGui.Selection.removeObserver(self.sel_server)
        FreeCADGui.ActiveDocument.resetEdit()

        doc_name = str(self.obj.Document.Name)
        obj = FreeCAD.getDocument(doc_name).getObject(self.obj.Name)
        obj.InternalRegion = self.InternalRegionOrig
        obj.Internal = self.InternalOrig
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
            index = self.validTypesOfInternalPrimitives.index(self.obj.InternalRegion["Type"])
            self.form.internalVolumePrimitiveSelection.setCurrentIndex(index)
            setQuantity(self.form.xCenter, self.obj.InternalRegion["Center"]["x"])
            setQuantity(self.form.yCenter, self.obj.InternalRegion["Center"]["y"])
            setQuantity(self.form.zCenter, self.obj.InternalRegion["Center"]["z"])
            setQuantity(self.form.xLength, self.obj.InternalRegion["BoxLengths"]["x"])
            setQuantity(self.form.yLength, self.obj.InternalRegion["BoxLengths"]["y"])
            setQuantity(self.form.zLength, self.obj.InternalRegion["BoxLengths"]["z"])
            setQuantity(self.form.radius, self.obj.InternalRegion["SphereRadius"])
            p1 = self.obj.InternalRegion["Point1"]
            setQuantity(self.form.xPoint1, p1["x"])
            setQuantity(self.form.yPoint1, p1["y"])
            setQuantity(self.form.zPoint1, p1["z"])
            p2 = self.obj.InternalRegion["Point2"]
            setQuantity(self.form.xPoint2, p2["x"])
            setQuantity(self.form.yPoint2, p2["y"])
            setQuantity(self.form.zPoint2, p2["z"])
            setQuantity(self.form.radius1, self.obj.InternalRegion["Radius1"])
            setQuantity(self.form.radius2, self.obj.InternalRegion["Radius2"])

    def updateUI(self):
        self.form.boundlayer_frame.setVisible(self.form.check_boundlayer.isChecked())
        if self.mesh_obj.MeshUtility == 'gmsh':
            self.form.cartesianInternalVolumeFrame.setVisible(False)
            self.form.surfaceOrInernalVolume.setVisible(False)
            self.form.cf_frame.setVisible(False)
            self.form.snappy_frame.setVisible(False)
        elif self.mesh_obj.MeshUtility == 'cfMesh':
            self.form.surfaceOrInernalVolume.setVisible(True)
        elif self.mesh_obj.MeshUtility == 'snappyHexMesh':
            self.form.surfaceOrInernalVolume.setVisible(False)
        if self.obj.Internal:
            self.form.surfaceOrInernalVolume.setVisible(True)
            self.form.cf_frame.setVisible(False)
            self.form.snappy_frame.setVisible(False)
            self.form.refinement_frame.setVisible(False)
            self.form.ReferencesFrame.setVisible(False)
            self.form.cartesianInternalVolumeFrame.setVisible(True)
            if self.mesh_obj.MeshUtility == 'cfMesh':
                self.form.cf_frame.setVisible(True)
                self.form.refinement_frame.setVisible(False)
            elif self.mesh_obj.MeshUtility == 'snappyHexMesh':
                self.form.snappy_frame.setVisible(True)
                self.form.snappySurfaceFrame.setVisible(False)
        else:
            self.form.cartesianInternalVolumeFrame.setVisible(False)
            if self.mesh_obj.MeshUtility == 'cfMesh':
                self.form.cf_frame.setVisible(True)
                self.form.snappy_frame.setVisible(False)
                self.form.refinement_frame.setVisible(True)
            elif self.mesh_obj.MeshUtility == 'snappyHexMesh':
                self.form.cf_frame.setVisible(False)
                self.form.snappy_frame.setVisible(True)
                self.form.snappySurfaceFrame.setVisible(True)
        if self.form.internalVolumePrimitiveSelection.currentText() == "Box":
            self.form.centerLayout.setVisible(True)
            self.form.lengthLayout.setVisible(True)
            self.form.radiusLayout.setVisible(False)
            self.form.coneLayout.setVisible(False)
        elif self.form.internalVolumePrimitiveSelection.currentText() == "Sphere":
            self.form.centerLayout.setVisible(True)
            self.form.lengthLayout.setVisible(False)
            self.form.radiusLayout.setVisible(True)
            self.form.coneLayout.setVisible(False)
        elif self.form.internalVolumePrimitiveSelection.currentText() == "Cone":
            self.form.centerLayout.setVisible(False)
            self.form.lengthLayout.setVisible(False)
            self.form.radiusLayout.setVisible(False)
            self.form.coneLayout.setVisible(True)

    def getMeshObject(self):
        analysis_obj = CfdTools.getActiveAnalysis()
        mesh_obj = CfdTools.getMeshObject(analysis_obj)
        if mesh_obj is None:
            message = "Mesh object not found - please re-create."
            QtGui.QMessageBox.critical(None, 'Missing mesh object', message)
            doc = FreeCADGui.getDocument(self.obj.Document)
            doc.resetEdit()
        return mesh_obj

    def change_internal_surface(self):
        if self.form.volumeRefinementToggle.isChecked():
            self.obj.Internal = True
        else:
            self.obj.Internal = False
        self.updateUI()
        doc_name = str(self.obj.Document.Name)
        obj = FreeCAD.getDocument(doc_name).getObject(self.obj.Name)
        obj.InternalRegion = self.obj.InternalRegion
        obj.Internal = self.obj.Internal
        FreeCAD.getDocument(doc_name).recompute()

    def internalTypeChanged(self):
        self.obj.InternalRegion['Type'] = self.form.internalVolumePrimitiveSelection.currentText()
        doc_name = str(self.obj.Document.Name)
        obj = FreeCAD.getDocument(doc_name).getObject(self.obj.Name)
        obj.InternalRegion = self.obj.InternalRegion
        FreeCAD.getDocument(doc_name).recompute()
        self.updateUI()

    def internalParameterChanged(self, value):
        self.obj.InternalRegion['SphereRadius'] = getQuantity(self.form.radius)
        self.obj.InternalRegion['Center'] = {'x': getQuantity(self.form.xCenter),
                                             'y': getQuantity(self.form.yCenter),
                                             'z': getQuantity(self.form.zCenter)}
        self.obj.InternalRegion['BoxLengths'] = {'x': getQuantity(self.form.xLength),
                                                 'y': getQuantity(self.form.yLength),
                                                 'z': getQuantity(self.form.zLength)}
        self.obj.InternalRegion['Point1'] = {'x': getQuantity(self.form.xPoint1),
                                             'y': getQuantity(self.form.yPoint1),
                                             'z': getQuantity(self.form.zPoint1)}
        self.obj.InternalRegion['Point2'] = {'x': getQuantity(self.form.xPoint2),
                                             'y': getQuantity(self.form.yPoint2),
                                             'z': getQuantity(self.form.zPoint2)}
        self.obj.InternalRegion['Radius1'] = getQuantity(self.form.radius1)
        self.obj.InternalRegion['Radius2'] = getQuantity(self.form.radius2)
        doc_name = str(self.obj.Document.Name)
        obj = FreeCAD.getDocument(doc_name).getObject(self.obj.Name)
        obj.InternalRegion = self.obj.InternalRegion
        FreeCAD.getDocument(doc_name).recompute()
