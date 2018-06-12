# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2016 - Bernd Hahnebach <bernd@bimstatik.org>            *
# *   Copyright (c) 2017 - Johan Heyns (CSIR) <jheyns@csir.co.za>           *
# *   Copyright (c) 2017 - Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>        *
# *   Copyright (c) 2017 - Alfred Bogaers (CSIR) <abogaers@csir.co.za>      *
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

__title__ = "_TaskPanelCfdMeshRegion"
__author__ = "JH, AB, OO"
__url__ = "http://www.freecadweb.org"

## @package TaskPanelCfdMeshRegion
#  \ingroup CFD

import FreeCAD
import FreeCADGui
import FemGui
from PySide import QtGui
from PySide import QtCore
import os
from CfdTools import inputCheckAndStore, setInputFieldQuantity
import CfdFaceSelectWidget


class _TaskPanelCfdMeshRegion:
    '''The TaskPanel for editing References property of MeshRegion objects'''
    def __init__(self, obj):
        FreeCADGui.Selection.clearSelection()
        self.sel_server = None
        self.obj = obj
        self.mesh_obj = self.getMeshObject()

        self.form = FreeCADGui.PySideUic.loadUi(os.path.join(os.path.dirname(__file__), "TaskPanelCfdMeshRegion.ui"))
        self.form.if_gmsh_rellen.valueChanged.connect(self.gmsh_rellen_changed)
        self.form.if_rellen.valueChanged.connect(self.rellen_changed)

        self.form.if_refinethick.valueChanged.connect(self.refinethick_changed)
        self.form.if_numlayer.valueChanged.connect(self.numlayer_changed)
        self.form.if_expratio.valueChanged.connect(self.expratio_changed)
        self.form.if_firstlayerheight.valueChanged.connect(self.firstlayerheight_changed)

        self.form.if_refinelevel.valueChanged.connect(self.refinelevel_changed)
        self.form.if_edgerefinement.valueChanged.connect(self.edgerefinement_changed)

        self.form.baffle_check.stateChanged.connect(self.baffleChanged)

        self.form.refinement_frame.setVisible(False)
        self.form.boundlayer_frame.setVisible(False)
        self.form.check_boundlayer.stateChanged.connect(self.boundary_layer_state_changed)

        tool_tip_mes = "Cell size relative to base cell size."
        self.form.if_gmsh_rellen.setToolTip(tool_tip_mes)
        self.form.if_rellen.setToolTip(tool_tip_mes)
        self.form.label_rellen.setToolTip(tool_tip_mes)
        self.get_meshregion_props()

        #for backward compatibility with pre-Internal refinementRegions
        try:
            self.obj.Internal
        except AttributeError:
            self.obj.addProperty("App::PropertyBool","Internal","MeshRegionProperties")
            self.obj.Internal = False
            self.obj.addProperty("App::PropertyPythonObject","InternalRegion")
            self.obj.InternalRegion = {"Type": "Box",
                                  "Center": {"x":0,"y":0,"z":0},
                                  "BoxLengths": {"x":1e-3,"y":1e-3,"z":1e-3},
                                  "SphereRadius": 1e-3}

        self.InternalOrig = self.obj.Internal
        self.InternalRegionOrig = self.obj.InternalRegion.copy()

        self.validTypesOfInternalPrimitives = ["Box","Sphere"]

        self.form.internalVolumePrimitiveSelection.addItems(self.validTypesOfInternalPrimitives)
        self.changePrimitiveType()

        self.form.internalVolumePrimitiveSelection.currentIndexChanged.connect(self.internalTypeChanged)
        self.form.surfaceRefinementToggle.toggled.connect(self.change_internal_surface)
        self.form.volumeRefinementToggle.toggled.connect(self.change_internal_surface)

        #Adding the following changed events to allow for real time update of the internal shape
        self.form.radius.textChanged.connect(self.radiusChanged)
        self.form.xCenter.valueChanged.connect(self.xCenterChanged)
        self.form.yCenter.textChanged.connect(self.yCenterChanged)
        self.form.zCenter.textChanged.connect(self.zCenterChanged)
        self.form.xLength.textChanged.connect(self.xLengthChanged)
        self.form.yLength.textChanged.connect(self.yLengthChanged)
        self.form.zLength.textChanged.connect(self.zLengthChanged)

        if self.mesh_obj.MeshUtility == 'gmsh':
            self.form.cartesianInternalVolumeFrame.setVisible(False)
            self.form.surfaceOrInernalVolume.setVisible(False)
            self.form.gmsh_frame.setVisible(True)
            self.form.cf_frame.setVisible(False)
            self.form.snappy_frame.setVisible(False)
        else:
            self.set_internal_surface()

        self.form.if_refinethick.setToolTip("Thickness or distance of the refinement region from the reference "
                                            "surface.")
        self.form.if_numlayer.setToolTip("Number of boundary layers if the reference surface is an external or "
                                         "mesh patch.")
        self.form.if_expratio.setToolTip("Expansion ratio of boundary layers (limited to be greater than 1.0 and "
                                         "smaller than 1.2).")
        self.form.if_firstlayerheight.setToolTip("Maximum first cell height (optional value and neglected if set "
                                                 "to 0.0).")
        self.form.if_refinelevel.setToolTip("Number of refinement levels relative to the base cell size")
        self.form.if_edgerefinement.setToolTip("Number of edge or feature refinement levels.")
        self.form.baffle_check.setToolTip("Create a zero thickness baffle.")

        self.initialiseUponReload()

        self.ReferencesOrig = list(self.obj.References)

        # Face list selection panel - modifies obj.References passed to it
        self.faceSelector = CfdFaceSelectWidget.CfdFaceSelectWidget(self.form.referenceSelectWidget,
                                                                    self.obj,
                                                                    self.mesh_obj.MeshUtility != 'gmsh')

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
                             "= {}".format(self.obj.Name, self.rellen))
        if self.mesh_obj.MeshUtility != 'gmsh':
            FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.RefinementThickness "
                                 "= '{}'".format(self.obj.Name, self.refinethick))
            FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.NumberLayers "
                                 "= {}".format(self.obj.Name, self.numlayer))
            FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.ExpansionRatio "
                                 "= {}".format(self.obj.Name, self.expratio))
            FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.FirstLayerHeight "
                                 "= '{}'".format(self.obj.Name, self.firstlayerheight))
            FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.RefinementLevel "
                                 "= {}".format(self.obj.Name, self.refinelevel))
            FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.RegionEdgeRefinement "
                                 "= {}".format(self.obj.Name, self.edgerefinement))
            FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.Baffle "
                                 "= {}".format(self.obj.Name, self.baffle))
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

    def initialiseUponReload(self):
        """ fills the widgets """
        if self.mesh_obj.MeshUtility == "gmsh":
            self.form.if_gmsh_rellen.setValue(self.obj.RelativeLength)
        else:
            self.form.if_rellen.setValue(self.obj.RelativeLength)
            setInputFieldQuantity(self.form.if_refinethick, self.obj.RefinementThickness)
            if self.numlayer > 1:  # Only reload when there are more than one layer
                self.form.check_boundlayer.toggle()
                self.form.if_numlayer.setValue(self.obj.NumberLayers)
                self.form.if_expratio.setValue(self.obj.ExpansionRatio)
                setInputFieldQuantity(self.form.if_firstlayerheight, self.obj.FirstLayerHeight)

            self.form.if_refinelevel.setValue(self.obj.RefinementLevel)
            self.form.if_edgerefinement.setValue(self.obj.RegionEdgeRefinement)
            if self.obj.Baffle:
                self.form.baffle_check.toggle()
            if self.obj.Internal:
                self.form.volumeRefinementToggle.toggle()
            index = self.validTypesOfInternalPrimitives.index(self.obj.InternalRegion["Type"])
            self.form.internalVolumePrimitiveSelection.setCurrentIndex(index)
            setInputFieldQuantity(self.form.xCenter, str(self.obj.InternalRegion["Center"]["x"])+"m")
            setInputFieldQuantity(self.form.yCenter, str(self.obj.InternalRegion["Center"]["y"])+"m")
            setInputFieldQuantity(self.form.zCenter, str(self.obj.InternalRegion["Center"]["z"])+"m")
            setInputFieldQuantity(self.form.xLength, str(self.obj.InternalRegion["BoxLengths"]["x"])+"m")
            setInputFieldQuantity(self.form.yLength, str(self.obj.InternalRegion["BoxLengths"]["y"])+"m")
            setInputFieldQuantity(self.form.zLength, str(self.obj.InternalRegion["BoxLengths"]["z"])+"m")
            setInputFieldQuantity(self.form.radius, str(self.obj.InternalRegion["SphereRadius"])+"m")

    def boundary_layer_state_changed(self):
        if self.form.check_boundlayer.isChecked():
            self.form.boundlayer_frame.setVisible(True)
        else:
            self.form.boundlayer_frame.setVisible(False)
            self.form.if_numlayer.setValue(int(1))
            self.form.if_expratio.setValue(1.0)
            self.form.if_firstlayerheight.setText("0.0 mm")

    def getMeshObject(self):
        analysis_obj = FemGui.getActiveAnalysis()
        from CfdTools import getMeshObject
        mesh_obj, is_present = getMeshObject(analysis_obj)
        if not is_present:
            message = "Missing mesh object! \n\nIt appears that the mesh object is not available, please re-create."
            QtGui.QMessageBox.critical(None, 'Missing mesh object', message)
            doc = FreeCADGui.getDocument(self.obj.Document)
            doc.resetEdit()
        return mesh_obj

    def get_meshregion_props(self):
        self.rellen = self.obj.RelativeLength
        if self.mesh_obj.MeshUtility != "gmsh":
            self.refinethick = self.obj.RefinementThickness
            self.numlayer = self.obj.NumberLayers
            self.expratio = self.obj.ExpansionRatio
            self.firstlayerheight = self.obj.FirstLayerHeight
            self.refinelevel = self.obj.RefinementLevel
            self.edgerefinement = self.obj.RegionEdgeRefinement
            self.baffle = self.obj.Baffle

    def set_internal_surface(self):
        if self.obj.Internal:
            if not(self.form.volumeRefinementToggle.isChecked()):
                self.form.volumeRefinementToggle.toggle()
            self.form.surfaceOrInernalVolume.setVisible(True)
            self.form.gmsh_frame.setVisible(False)
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
            if not(self.form.surfaceRefinementToggle.isChecked()):
                self.form.volumeRefinementToggle.toggle()
            self.form.cartesianInternalVolumeFrame.setVisible(False)
            if self.mesh_obj.MeshUtility == 'cfMesh':
                self.form.gmsh_frame.setVisible(False)
                self.form.cf_frame.setVisible(True)
                self.form.snappy_frame.setVisible(False)
                self.form.refinement_frame.setVisible(True)
            elif self.mesh_obj.MeshUtility == 'snappyHexMesh':
                self.form.gmsh_frame.setVisible(False)
                self.form.cf_frame.setVisible(False)
                self.form.snappy_frame.setVisible(True)
                self.form.snappySurfaceFrame.setVisible(True)

    def change_internal_surface(self):
        if self.form.volumeRefinementToggle.isChecked():
            self.obj.Internal = True
        else:
            self.obj.Internal = False
        self.set_internal_surface()
        doc_name = str(self.obj.Document.Name)
        obj = FreeCAD.getDocument(doc_name).getObject(self.obj.Name)
        obj.InternalRegion = self.obj.InternalRegion
        obj.Internal = self.obj.Internal
        FreeCAD.getDocument(doc_name).recompute()

    def changePrimitiveType(self):
        if self.form.internalVolumePrimitiveSelection.currentText() == "Box":
        #if self.obj.InternalRegion['Type'] == "Box":
            self.form.lengthLayout.setVisible(True)
            self.form.radiusLayout.setVisible(False)
        #elif self.obj.InternalRegion['Type'] == "Sphere":
        elif self.form.internalVolumePrimitiveSelection.currentText() == "Sphere":
            self.form.lengthLayout.setVisible(False)
            self.form.radiusLayout.setVisible(True)

    def internalTypeChanged(self):
        self.obj.InternalRegion['Type'] = self.form.internalVolumePrimitiveSelection.currentText()
        doc_name = str(self.obj.Document.Name)
        obj = FreeCAD.getDocument(doc_name).getObject(self.obj.Name)
        obj.InternalRegion = self.obj.InternalRegion
        FreeCAD.getDocument(doc_name).recompute()
        
        self.changePrimitiveType()


    def gmsh_rellen_changed(self, value):
        self.rellen = value

    def rellen_changed(self, value):
        self.rellen = value

    def refinethick_changed(self, value):
        self.refinethick = value

    def numlayer_changed(self, value):
        self.numlayer = value

    def expratio_changed(self, value):
        self.expratio = value

    def firstlayerheight_changed(self, value):
        self.firstlayerheight = value

    def refinelevel_changed(self, value):
        self.refinelevel = value

    def edgerefinement_changed(self, value):
        self.edgerefinement = value

    def baffleChanged(self, checkedState):
        self.baffle = bool(checkedState)

    def radiusChanged(self,value):
        inputCheckAndStore(value, "m", self.obj.InternalRegion, 'SphereRadius')
        doc_name = str(self.obj.Document.Name)
        obj = FreeCAD.getDocument(doc_name).getObject(self.obj.Name)
        obj.InternalRegion = self.obj.InternalRegion
        FreeCAD.getDocument(doc_name).recompute()

    def xCenterChanged(self,text):
        inputCheckAndStore(text, "m", self.obj.InternalRegion['Center'], 'x')
        doc_name = str(self.obj.Document.Name)
        obj = FreeCAD.getDocument(doc_name).getObject(self.obj.Name)
        obj.InternalRegion = self.obj.InternalRegion
        FreeCAD.getDocument(doc_name).recompute()

    def yCenterChanged(self,text):
        inputCheckAndStore(text, "m", self.obj.InternalRegion['Center'], 'y')
        doc_name = str(self.obj.Document.Name)
        obj = FreeCAD.getDocument(doc_name).getObject(self.obj.Name)
        obj.InternalRegion = self.obj.InternalRegion
        FreeCAD.getDocument(doc_name).recompute()

    def zCenterChanged(self,text):
        inputCheckAndStore(text, "m", self.obj.InternalRegion['Center'], 'z')
        doc_name = str(self.obj.Document.Name)
        obj = FreeCAD.getDocument(doc_name).getObject(self.obj.Name)
        obj.InternalRegion = self.obj.InternalRegion
        FreeCAD.getDocument(doc_name).recompute()

    def xLengthChanged(self,text):
        inputCheckAndStore(text, "m", self.obj.InternalRegion['BoxLengths'], 'x')
        doc_name = str(self.obj.Document.Name)
        obj = FreeCAD.getDocument(doc_name).getObject(self.obj.Name)
        obj.InternalRegion = self.obj.InternalRegion
        FreeCAD.getDocument(doc_name).recompute()

    def yLengthChanged(self,text):
        inputCheckAndStore(text, "m", self.obj.InternalRegion['BoxLengths'], 'y')
        doc_name = str(self.obj.Document.Name)
        obj = FreeCAD.getDocument(doc_name).getObject(self.obj.Name)
        obj.InternalRegion = self.obj.InternalRegion
        FreeCAD.getDocument(doc_name).recompute()

    def zLengthChanged(self,text):
        inputCheckAndStore(text, "m", self.obj.InternalRegion['BoxLengths'], 'z')
        doc_name = str(self.obj.Document.Name)
        obj = FreeCAD.getDocument(doc_name).getObject(self.obj.Name)
        obj.InternalRegion = self.obj.InternalRegion
        FreeCAD.getDocument(doc_name).recompute()