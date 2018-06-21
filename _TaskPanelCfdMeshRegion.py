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
            print(self.obj.Internal)
        except:
            self.obj.addProperty("App::PropertyBool","Internal","MeshRegionProperties")
            self.obj.Internal = False
            self.obj.addProperty("App::PropertyPythonObject","InternalRegion")
            self.obj.InternalRegion = {"Type": "Box",
                                  "Center": {"x":0,"y":0,"z":0},
                                  "BoxLengths": {"x":0,"y":0,"z":0},
                                  "SphereRadius": 0}

        self.Internal = self.obj.Internal
        self.InternalRegion = self.obj.InternalRegion

        self.validTypesOfInternalPrimitives = ["Box","Sphere"]

        self.form.internalVolumePrimitiveSelection.addItems(self.validTypesOfInternalPrimitives)
        self.changePrimitiveType()

        self.form.internalVolumePrimitiveSelection.currentIndexChanged.connect(self.changePrimitiveType)
        self.form.surfaceRefinementToggle.toggled.connect(self.change_internal_surface)
        self.form.volumeRefinementToggle.toggled.connect(self.change_internal_surface)

        if self.mesh_obj.Proxy.Type == 'Fem::FemMeshGmsh':
            self.form.cartesianInternalVolumeFrame.setVisible(False)
            self.form.surfaceOrInernalVolume.setVisible(False)
            self.form.gmsh_frame.setVisible(True)
            self.form.cf_frame.setVisible(False)
            self.form.snappy_frame.setVisible(False)
        elif self.mesh_obj.Proxy.Type == 'CfdMeshCart':
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
                                                                    self.mesh_obj.Proxy.Type != 'Fem::FemMeshGmsh')

    def accept(self):
        self.set_meshregion_props()

        self.InternalRegion["Type"] = self.form.internalVolumePrimitiveSelection.currentText()
        inputCheckAndStore(self.form.xCenter.text(), "m", self.InternalRegion['Center'], 'x')
        inputCheckAndStore(self.form.yCenter.text(), "m", self.InternalRegion['Center'], 'y')
        inputCheckAndStore(self.form.zCenter.text(), "m", self.InternalRegion['Center'], 'z')
        inputCheckAndStore(self.form.xLength.text(), "m", self.InternalRegion['BoxLengths'], 'x')
        inputCheckAndStore(self.form.yLength.text(), "m", self.InternalRegion['BoxLengths'], 'y')
        inputCheckAndStore(self.form.zLength.text(), "m", self.InternalRegion['BoxLengths'], 'z')
        inputCheckAndStore(self.form.radius.text(), "m", self.InternalRegion, 'SphereRadius')

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
        if self.mesh_obj.Proxy.Type == 'CfdMeshCart':
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
                                 "= {}".format(self.obj.Name, self.obj.Baffle))
            FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.Internal "
                                 "= {}".format(self.obj.Name, self.Internal))
            FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.InternalRegion "
                                 "= {}".format(self.obj.Name, self.InternalRegion))
        return True

    def reject(self):
        self.obj.References = self.ReferencesOrig
        self.set_meshregion_props()
        if self.sel_server:
            FreeCADGui.Selection.removeObserver(self.sel_server)
        FreeCADGui.ActiveDocument.resetEdit()
        return True

    def initialiseUponReload(self):
        """ fills the widgets """
        if self.mesh_obj.Proxy.Type == 'Fem::FemMeshGmsh':
            self.form.if_gmsh_rellen.setValue(self.obj.RelativeLength)
        elif self.mesh_obj.Proxy.Type == 'CfdMeshCart':
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
            if self.Internal:
                self.form.volumeRefinementToggle.toggle()
                #self.form.xCenter.setValue(self.obj.InternalRegion["Center"]["x"])
                index = self.validTypesOfInternalPrimitives.index(self.InternalRegion["Type"])
                self.form.internalVolumePrimitiveSelection.setCurrentIndex(index)
                setInputFieldQuantity(self.form.xCenter, str(self.InternalRegion["Center"]["x"])+"m")
                setInputFieldQuantity(self.form.yCenter, str(self.InternalRegion["Center"]["y"])+"m")
                setInputFieldQuantity(self.form.zCenter, str(self.InternalRegion["Center"]["z"])+"m")
                setInputFieldQuantity(self.form.xLength, str(self.InternalRegion["BoxLengths"]["x"])+"m")
                setInputFieldQuantity(self.form.yLength, str(self.InternalRegion["BoxLengths"]["y"])+"m")
                setInputFieldQuantity(self.form.zLength, str(self.InternalRegion["BoxLengths"]["z"])+"m")
                setInputFieldQuantity(self.form.radius, str(self.InternalRegion["SphereRadius"])+"m")


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
        if self.mesh_obj.Proxy.Type == 'CfdMeshCart':
            self.refinethick = self.obj.RefinementThickness
            self.numlayer = self.obj.NumberLayers
            self.expratio = self.obj.ExpansionRatio
            self.firstlayerheight = self.obj.FirstLayerHeight
            self.refinelevel = self.obj.RefinementLevel
            self.edgerefinement = self.obj.RegionEdgeRefinement

    def set_meshregion_props(self):
        self.obj.RelativeLength = self.rellen
        if self.mesh_obj.Proxy.Type == 'CfdMeshCart':
            self.obj.RefinementThickness = self.refinethick
            self.obj.NumberLayers = self.numlayer
            self.obj.ExpansionRatio = self.expratio
            self.obj.FirstLayerHeight = self.firstlayerheight
            self.obj.RefinementLevel = self.refinelevel
            self.obj.RegionEdgeRefinement = self.edgerefinement
            if self.form.baffle_check.isChecked() and self.mesh_obj.MeshUtility == 'snappyHexMesh':
                self.obj.Baffle = True
            else:
                self.obj.Baffle = False

    def set_internal_surface(self):
        if self.Internal:
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
            self.Internal = True
        else:
            self.Internal = False
        self.set_internal_surface()

    def changePrimitiveType(self):
        if self.form.internalVolumePrimitiveSelection.currentText() == "Box":
            self.form.lengthLayout.setVisible(True)
            self.form.radiusLayout.setVisible(False)
        elif self.form.internalVolumePrimitiveSelection.currentText() == "Sphere":
            self.form.lengthLayout.setVisible(False)
            self.form.radiusLayout.setVisible(True)


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
