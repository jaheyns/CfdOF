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
__author__ = "Bernd Hahnebach"
__url__ = "http://www.freecadweb.org"

## @package TaskPanelCfdMeshRegion
#  \ingroup CFD

import FreeCAD
import FreeCADGui
import FemGui
from PySide import QtGui
from PySide import QtCore
import os


class _TaskPanelCfdMeshRegion:
    '''The TaskPanel for editing References property of MeshRegion objects'''
    def __init__(self, obj):
        FreeCADGui.Selection.clearSelection()
        self.sel_server = None
        self.obj = obj
        self.selection_mode_solid = False
        self.selection_mode_std_print_message = "Select Faces, Edges and Vertices by single click " \
                                                "on them to add them to the list."
        self.selection_mode_solid_print_message = "Select Solids by single click on a Face or Edge which belongs " \
                                                  "to the Solid, to add the Solid to the list."

        self.form = FreeCADGui.PySideUic.loadUi(os.path.join(os.path.dirname(__file__), "TaskPanelCfdMeshRegion.ui"))
        QtCore.QObject.connect(self.form.if_rellen,
                               QtCore.SIGNAL("valueChanged(double)"),
                               self.rellen_changed)
        QtCore.QObject.connect(self.form.rb_standard,
                               QtCore.SIGNAL("toggled(bool)"),
                               self.choose_selection_mode_standard)
        QtCore.QObject.connect(self.form.rb_solid,
                               QtCore.SIGNAL("toggled(bool)"),
                               self.choose_selection_mode_solid)
        QtCore.QObject.connect(self.form.pushButton_Reference,
                               QtCore.SIGNAL("clicked()"),
                               self.add_references)
        self.form.list_References.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.form.list_References.connect(self.form.list_References,
                                          QtCore.SIGNAL("customContextMenuRequested(QPoint)"),
                                          self.references_list_right_clicked)

        QtCore.QObject.connect(self.form.if_refinethick, QtCore.SIGNAL("valueChanged(Base::Quantity)"),
                               self.refinethick_changed)
        QtCore.QObject.connect(self.form.if_numlayer, QtCore.SIGNAL("valueChanged(int)"),
                               self.numlayer_changed)
        QtCore.QObject.connect(self.form.if_expratio, QtCore.SIGNAL("valueChanged(double)"),
                               self.expratio_changed)
        QtCore.QObject.connect(self.form.if_firstlayerheight, QtCore.SIGNAL("valueChanged(Base::Quantity)"),
                               self.firstlayerheight_changed)

        QtCore.QObject.connect(self.form.if_refinelevel, QtCore.SIGNAL("valueChanged(int)"),
                               self.refinelevel_changed)
        QtCore.QObject.connect(self.form.if_edgerefinement, QtCore.SIGNAL("valueChanged(int)"),
                               self.edgerefinement_changed)

        self.form.refinement_frame.setVisible(False)
        self.form.boundlayer_frame.setVisible(False)
        self.form.check_boundlayer.stateChanged.connect(self.boundary_layer_state_changed)

        tool_tip_mes = "Cell size relative to base cell size."
        self.form.if_rellen.setToolTip(tool_tip_mes)
        self.form.label_rellen.setToolTip(tool_tip_mes)
        self.get_meshregion_props()
        self.mesh_obj = self.getMeshObject()
        if self.mesh_obj.Proxy.Type == 'CfdMeshCart' and self.mesh_obj.MeshUtility == 'cfMesh':
            self.form.cf_frame.setVisible(True)
            self.form.snappy_frame.setVisible(False)
            self.form.refinement_frame.setVisible(True)
            self.form.face_frame.setVisible(False)

        if self.mesh_obj.Proxy.Type == 'CfdMeshCart' and self.mesh_obj.MeshUtility == 'snappyHexMesh':
            self.form.cf_frame.setVisible(False)
            self.form.snappy_frame.setVisible(True)
            self.form.face_frame.setVisible(False)

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

        self.update()

    def accept(self):
        self.set_meshregion_props()
        if self.sel_server:
            FreeCADGui.Selection.removeObserver(self.sel_server)
        FreeCADGui.ActiveDocument.resetEdit()
        FreeCAD.ActiveDocument.recompute()
        # Macro script
        FreeCADGui.doCommand("\nFreeCAD.ActiveDocument.{}.RelativeLength "
                             "= {}".format(self.obj.Name, self.rellen))
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
        ref_list = []
        for ref in self.obj.References:
            for elem in ref[1]:
                ref_list.append((ref[0], elem))
        FreeCADGui.doCommand("referenceList = []")
        for ref in ref_list:
            FreeCADGui.doCommand("part = FreeCAD.ActiveDocument.getObject('{}')".format(ref[0].Name))
            FreeCADGui.doCommand("referenceList.append((part,'{}'))".format(ref[1]))
        FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.References = referenceList".format(self.obj.Name))
        return True

    def reject(self):
        self.set_meshregion_props()
        if self.sel_server:
            FreeCADGui.Selection.removeObserver(self.sel_server)
        FreeCADGui.ActiveDocument.resetEdit()
        return True

    def initialiseUponReload(self):
        if self.numlayer > 1:  # Only reload when there are more than one layer
            self.form.check_boundlayer.toggle()
            self.form.if_numlayer.setValue(self.obj.NumberLayers)
            self.form.if_expratio.setValue(self.obj.ExpansionRatio)
            self.form.if_firstlayerheight.setText(self.obj.FirstLayerHeight.UserString)
        if self.obj.snappedRefine:
            self.form.snapRadio.toggle()
        else:
            self.form.refineRadio.toggle()
        self.form.snappyRefineLevel.setValue(self.obj.snappyRefineLevel)
        if self.obj.internalBaffle:
            self.form.baffleCheckBox.toggle()
        self.form.snappySurfaceEdgeRefinementLevel.setValue(self.obj.localEdgeRefine)
        if self.mesh_obj.MeshUtility == 'snappyHexMesh':
            self.form.cfFrame.setVisible(False)
            self.form.snappyFrame.setVisible(True)
        else:
            self.form.cfFrame.setVisible(True)
            self.form.snappyFrame.setVisible(False)

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
        self.refinethick = self.obj.RefinementThickness
        self.numlayer = self.obj.NumberLayers
        self.expratio = self.obj.ExpansionRatio
        self.firstlayerheight = self.obj.FirstLayerHeight
        self.refinelevel = self.obj.RefinementLevel
        self.edgerefinement = self.obj.RegionEdgeRefinement
        self.references = []
        if self.obj.References:
            self.tuplereferences = self.obj.References
            self.get_references()

    def set_meshregion_props(self):
        self.obj.References = self.references
        self.obj.RelativeLength = self.rellen
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

    def update(self):
        """ fills the widgets """
        self.form.if_rellen.setValue(self.obj.RelativeLength)
        self.form.if_refinethick.setText(self.obj.RefinementThickness.UserString)
        self.rebuild_list_References()
        if self.numlayer > 1:  # Only reload when there are more than one layer
            self.form.check_boundlayer.toggle()
            self.form.if_numlayer.setValue(self.obj.NumberLayers)
            self.form.if_expratio.setValue(self.obj.ExpansionRatio)
            self.form.if_firstlayerheight.setText(self.obj.FirstLayerHeight.UserString)

        self.form.if_refinelevel.setValue(self.obj.RefinementLevel)
        self.form.if_edgerefinement.setValue(self.obj.RegionEdgeRefinement)
        if self.obj.Baffle:
            self.form.baffle_check.toggle()

        if self.mesh_obj.MeshUtility == 'snappyHexMesh':
            self.form.cf_frame.setVisible(False)
            self.form.snappy_frame.setVisible(True)
        else:
            self.form.cf_frame.setVisible(True)
            self.form.snappy_frame.setVisible(False)

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

    def choose_selection_mode_standard(self, state):
        self.selection_mode_solid = not state
        if self.sel_server and not self.selection_mode_solid:
            print(self.selection_mode_std_print_message)

    def choose_selection_mode_solid(self, state):
        self.selection_mode_solid = state
        if self.sel_server and self.selection_mode_solid:
            print(self.selection_mode_solid_print_message)

    def get_references(self):
        for ref in self.tuplereferences:
            for elem in ref[1]:
                self.references.append((ref[0], elem))

    def references_list_right_clicked(self, QPos):
        self.form.contextMenu = QtGui.QMenu()
        menu_item = self.form.contextMenu.addAction("Remove Reference")
        if not self.references:
            menu_item.setDisabled(True)
        self.form.connect(menu_item, QtCore.SIGNAL("triggered()"), self.remove_reference)
        parentPosition = self.form.list_References.mapToGlobal(QtCore.QPoint(0, 0))
        self.form.contextMenu.move(parentPosition + QPos)
        self.form.contextMenu.show()

    def remove_reference(self):
        if not self.references:
            return
        current_item_name = str(self.form.list_References.currentItem().text())
        for ref in self.references:
            refname_to_compare_listentry = ref[0].Name + ':' + ref[1]
            if refname_to_compare_listentry == current_item_name:
                self.references.remove(ref)
        self.rebuild_list_References()

    def add_references(self):
        '''Called if Button add_reference is triggered'''
        # in constraints EditTaskPanel the selection is active as soon as the taskpanel is open
        # here the addReference button EditTaskPanel has to be triggered to start selection mode
        FreeCADGui.Selection.clearSelection()
        # start SelectionObserver and parse the function to add the References to the widget
        if self.selection_mode_solid:  # print message on button click
            print_message = self.selection_mode_solid_print_message
        else:
            print_message = self.selection_mode_std_print_message
        import FemSelectionObserver
        self.sel_server = FemSelectionObserver.FemSelectionObserver(self.selectionParser, print_message)

    def selectionParser(self, selection):
        print('selection: ', selection[0].Shape.ShapeType, '  ', selection[0].Name, '  ', selection[1])
        if hasattr(selection[0], "Shape") and selection[1]:
            elt = selection[0].Shape.getElement(selection[1])
            if self.selection_mode_solid:
                # in solid selection mode use edges and faces for selection of a solid
                solid_to_add = None
                if elt.ShapeType == 'Edge':
                    found_edge = False
                    for i, s in enumerate(selection[0].Shape.Solids):
                        for e in s.Edges:
                            if elt.isSame(e):
                                if not found_edge:
                                    solid_to_add = str(i + 1)
                                else:
                                    FreeCAD.Console.PrintMessage('Edge belongs to more than one solid\n')
                                    solid_to_add = None
                                found_edge = True
                elif elt.ShapeType == 'Face':
                    found_face = False
                    for i, s in enumerate(selection[0].Shape.Solids):
                        for e in s.Faces:
                            if elt.isSame(e):
                                if not found_face:
                                    solid_to_add = str(i + 1)
                                else:
                                    FreeCAD.Console.PrintMessage('Face belongs to more than one solid\n')
                                    solid_to_add = None
                                found_edge = True
                if solid_to_add:
                    selection = (selection[0], 'Solid' + solid_to_add)
                    print('selection element changed to Solid: ',
                          selection[0].Shape.ShapeType, '  ',
                          selection[0].Name, '  ',
                          selection[1])
                else:
                    return
            if selection not in self.references:
                self.references.append(selection)
                self.rebuild_list_References()
            else:
                FreeCAD.Console.PrintMessage(selection[0].Name + ' --> ' + selection[1]
                                             + ' is in reference list already!\n')

    def rebuild_list_References(self):
        self.form.list_References.clear()
        items = []
        for ref in self.references:
            item_name = ref[0].Name + ':' + ref[1]
            items.append(item_name)
        for listItemName in sorted(items):
            self.form.list_References.addItem(listItemName)
