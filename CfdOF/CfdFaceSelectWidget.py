# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2017 Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>          *
# *   Copyright (c) 2017 Johan Heyns (CSIR) <jheyns@csir.co.za>             *
# *   Copyright (c) 2017 Alfred Bogaers (CSIR) <abogaers@csir.co.za>        *
# *   Copyright (c) 2019-2022 Oliver Oxtoby <oliveroxtoby@gmail.com>        *
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
import os
import os.path
from CfdOF import CfdTools
from CfdOF.Mesh import CfdMeshRefinement
from CfdOF.Solve import CfdFluidBoundary
from CfdOF.Solve import CfdZone
if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore
    from PySide import QtCore
    from PySide import QtGui
    from PySide.QtCore import QTimer

from PySide.QtCore import QT_TRANSLATE_NOOP

class CfdFaceSelectWidget:
    def __init__(self, parent_widget, obj, allow_obj_sel, allow_face_sel, allow_solid_sel,
                 allow_point_sel=False, allow_edge_sel=False):
        ui_path = os.path.join(CfdTools.getModulePath(), 'Gui', "TaskPanelCfdListOfFaces.ui")
        self.parent_widget = parent_widget
        self.form = FreeCADGui.PySideUic.loadUi(ui_path, self.parent_widget)
        self.parent_widget.layout().addWidget(self.form)

        self.selecting_references = False
        self.recompute_timer = QTimer()
        self.recompute_timer.setSingleShot(True)
        self.recompute_timer.timeout.connect(self.recomputeDocument)

        self.obj = obj
        self.ShapeRefs = self.obj.ShapeRefs
        self.doc_name = self.obj.Document.Name
        self.view_object = self.obj.ViewObject

        self.allow_obj_sel = allow_obj_sel
        self.allow_face_sel = allow_face_sel
        self.allow_solid_sel = allow_solid_sel
        self.allow_point_sel = allow_point_sel
        self.allow_edge_sel = allow_edge_sel
        self.selection_mode_solid = (not allow_face_sel) and allow_solid_sel

        sel_list = []
        sel_rb_list = []

        if allow_face_sel:
            sel_list.append("faces")
            sel_rb_list.append("Face")
        if allow_edge_sel:
            sel_list.append("edges")
            sel_rb_list.append("Edge")
        if allow_point_sel:
            sel_list.append("vertices")
            sel_rb_list.append("Vertex")

        sel_rb_text = ' / '.join(sel_rb_list)
        sel_msg = ""

        if len(sel_list) > 0:
            sel_msg = sel_list[0]
            if len(sel_list) > 1:
                for i in range(len(sel_list)-2):
                    sel_msg += ", " + sel_list[i+1]
                sel_msg += " and " + sel_list[-1]

        self.form.rb_standard.setText(sel_rb_text)

        self.selection_mode_std_print_message = "Select {} by single-clicking on them".format(sel_msg)
        self.selection_mode_solid_print_message = "Select solids by single-clicking on a face or edge which belongs " \
                                                  "to the solid"
        if self.allow_obj_sel:
            self.selection_mode_std_print_message += ", or entire object by double-clicking on it."
            self.selection_mode_solid_print_message += ", or entire object by double-clicking on it."
        else:
            self.selection_mode_std_print_message += "."
            self.selection_mode_solid_print_message += "."

        exclusive_sel = (not allow_solid_sel) or not (allow_face_sel or allow_edge_sel or allow_point_sel)
        self.form.labelSelection.setVisible(not exclusive_sel)
        self.form.rb_standard.setVisible(not exclusive_sel)
        self.form.rb_solid.setVisible(not exclusive_sel)
        self.form.faceSelectPushButton.setVisible(allow_obj_sel)
        self.form.rb_standard.toggled.connect(self.choose_selection_mode_standard)
        self.form.rb_solid.toggled.connect(self.choose_selection_mode_solid)

        self.form.listReferences.currentRowChanged.connect(self.setReferenceListSelection)
        self.form.buttonAddFace.clicked.connect(self.buttonAddFaceClicked)
        self.form.buttonAddFace.setCheckable(True)
        self.form.buttonRemoveFace.clicked.connect(self.buttonRemoveFaceClicked)

        self.form.individualFacesFrame.setVisible(not allow_obj_sel)
        self.form.faceSelectPushButton.setChecked(not allow_obj_sel)

        self.shapeNames = []
        self.shapeLabels = []

        for i in FreeCADGui.ActiveDocument.Document.Objects:
            if "Shape" in i.PropertiesList:
                if not i.Shape.isNull() and \
                        not (hasattr(i, 'Proxy') and isinstance(i.Proxy, CfdFluidBoundary.CfdFluidBoundary)) and \
                        not (hasattr(i, 'Proxy') and isinstance(i.Proxy, CfdMeshRefinement.CfdMeshRefinement)) and \
                        not (hasattr(i, 'Proxy') and isinstance(i.Proxy, CfdZone.CfdZone)):
                    self.shapeNames.append(i.Name)
                    self.shapeLabels.append(i.Label)

        for i, label in enumerate(self.shapeLabels):
            item = QtGui.QListWidgetItem(label)
            if allow_obj_sel:
                item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
                item.setCheckState(QtCore.Qt.Unchecked)
            item.setData(QtCore.Qt.UserRole, i)
            self.form.objectListWidget.addItem(item)

        # Face list selection
        self.form.objectListWidget.itemSelectionChanged.connect(self.faceListShapeChosen)
        self.form.objectListWidget.itemChanged.connect(self.objectListItemChanged)
        self.form.faceSelectPushButton.toggled.connect(self.faceSelectPushButtonChanged)
        self.form.faceListWidget.itemSelectionChanged.connect(self.faceHighlightChange)
        self.form.faceListWidget.itemChanged.connect(self.faceListItemChanged)
        self.form.selectAllButton.clicked.connect(self.selectAllButtonClicked)
        self.form.selectNoneButton.clicked.connect(self.selectNoneButtonClicked)
        self.form.objectListWidget.setToolTip("Choose solid objects from the list and optionally select one or more of "
                                              "the sub-components associated with the currently selected shape.")
        self.form.tabWidget.currentChanged.connect(self.tabChanged)

        self.rebuildReferenceList()

        # First time, add any currently selected faces to list
        if len(self.ShapeRefs) == 0:
            self.addSelectionToRefList()
            self.scheduleRecompute()
            FreeCADGui.Selection.clearSelection()

        self.updateSelectionbuttonUI()

    def setReferenceListSelection(self, row):
        if row > -1:
            self.enableSelectingMode(False)
            item = self.form.listReferences.item(row)
            selection_object, sub = item.data(QtCore.Qt.UserRole)
            if sub is None:
                FreeCADGui.Selection.addSelection(selection_object)
            else:
                FreeCADGui.Selection.addSelection(selection_object, [str(sub)])

    def addSelectionToRefList(self):
        """ Add currently selected objects to reference list. """
        for sel in FreeCADGui.Selection.getSelectionEx():
            if sel.HasSubObjects:
                for sub in sel.SubElementNames:
                    print("Adding selection {}:{}".format(sel.ObjectName, sub))
                    self.addSelection(sel.DocumentName, sel.ObjectName, sub)
            elif self.allow_obj_sel:
                print("Adding selection {}".format(sel.ObjectName))
                self.addSelection(sel.DocumentName, sel.ObjectName, None)
        self.scheduleRecompute()

    def enableSelectingMode(self, selecting):
        self.selecting_references = selecting
        FreeCADGui.Selection.clearSelection()

        # start SelectionObserver and parse the function to add the References to the widget
        if self.selecting_references:
            FreeCADGui.Selection.addObserver(self)
        else:
            FreeCADGui.Selection.removeObserver(self)

        self.scheduleRecompute()
        self.updateSelectionbuttonUI()

    def buttonAddFaceClicked(self):
        self.selecting_references = not self.selecting_references

        if self.selecting_references:
            # Add any currently selected objects
            if len(FreeCADGui.Selection.getSelectionEx()) >= 1:
                self.addSelectionToRefList()
                self.selecting_references = False

        self.enableSelectingMode(self.selecting_references)

    def buttonRemoveFaceClicked(self):
        if not self.ShapeRefs:
            return
        if not self.form.listReferences.selectedItems():
            return
        for item in self.form.listReferences.selectedItems():
            object, sub = item.data(QtCore.Qt.UserRole)
            for i, ref in enumerate(self.ShapeRefs):
                if ref[0].Name == object.Name:
                    if not sub:
                        self.ShapeRefs.remove(ref)
                    else:
                        newsub = tuple([ss for ss in ref[1] if ss != sub])
                        if len(newsub):
                            self.ShapeRefs[i] = tuple([ref[0], newsub])
                        else:
                            self.ShapeRefs.remove(ref)

        self.rebuildReferenceList()
        self.scheduleRecompute()

    def choose_selection_mode_standard(self, state):
        self.selection_mode_solid = not state
        self.updateSelectionbuttonUI()

    def choose_selection_mode_solid(self, state):
        self.selection_mode_solid = state
        self.updateSelectionbuttonUI()

    def tabChanged(self, index):
        self.enableSelectingMode(False)

    def updateSelectionbuttonUI(self):
        self.form.buttonAddFace.setChecked(self.selecting_references)
        if self.selection_mode_solid:
            print_message = self.selection_mode_solid_print_message
        else:
            print_message = self.selection_mode_std_print_message
        self.form.labelHelpText.setText(print_message)

    def addSelection(self, doc_name, obj_name, sub, selected_point=None, as_is=False):
        """
        Add the selected sub-element (face) of the part to the Reference list. Prevent selection in other
        document.
        """
        if FreeCADGui.activeDocument().Document.Name != self.doc_name:
            return
        selected_object = FreeCAD.getDocument(doc_name).getObject(obj_name)
        if selected_object.Shape.isNull():
            return

        # On double click of a shape, sub is None and obj is the shape
        print('Selection: ' + selected_object.Shape.ShapeType + '  ' + selected_object.Name + ':' +
              str(sub) + " @ " + str(selected_point))
        if hasattr(selected_object, "Shape"):
            if sub:
                if sub.startswith('Solid'):  # getElement doesn't work for solids
                    elt = selected_object.Shape.Solids[int(sub.lstrip('Solid')) - 1]
                else:
                    elt = selected_object.Shape.getElement(sub)
            else:
                elt = selected_object.Shape
            selection = None
            if as_is:
                selection = (selected_object, (sub if sub else '',))
            elif self.allow_obj_sel and \
                    (elt.ShapeType == 'Shell' or elt.ShapeType == 'Solid' or elt.ShapeType == 'Compound'):
                selection = (selected_object, ('',))
            elif self.selection_mode_solid:
                # in solid selection mode use edges and faces for selection of a solid
                solid_to_add = None
                if elt.ShapeType == 'Edge':
                    found_edge = False
                    for i, s in enumerate(selected_object.Shape.Solids):
                        for e in s.Edges:
                            if elt.isSame(e):
                                if not found_edge:
                                    solid_to_add = 'Solid' + str(i + 1)
                                else:
                                    FreeCAD.Console.PrintMessage('Edge belongs to more than one solid\n')
                                    solid_to_add = None
                                found_edge = True
                elif elt.ShapeType == 'Face':
                    found_face = False
                    for i, s in enumerate(selected_object.Shape.Solids):
                        for e in s.Faces:
                            if elt.isSame(e):
                                if not found_face:
                                    solid_to_add = 'Solid' + str(i + 1)
                                else:
                                    FreeCAD.Console.PrintMessage('Face belongs to more than one solid\n')
                                    solid_to_add = None
                                found_face = True
                elif elt.ShapeType == 'Solid':
                    solid_to_add = sub
                if solid_to_add:
                    selection = (selected_object, (solid_to_add,))
                    print('Selection element changed to Solid: ' +
                          selected_object.Shape.ShapeType + '  ' +
                          selection[0].Name + '  ' +
                          selection[1][0])
            else:
                # Allow Vertex, Edge, Face or just Face selection
                if (elt.ShapeType == 'Face' and self.allow_face_sel) or \
                        (elt.ShapeType == 'Edge' and self.allow_edge_sel) or \
                        (elt.ShapeType == 'Vertex' and self.allow_point_sel):
                    selection = (selected_object, (sub,))
            if selection:
                # Override sub-selections with whole-object selection
                if not selection[1][0]:
                    for ref in self.ShapeRefs:
                        if ref[0] == selection[0] and ref[1] != ('',):
                            self.ShapeRefs.remove(ref)
                            break
                if selection not in self.ShapeRefs:
                    self.ShapeRefs.append(selection)
                else:
                    if not selection[1][0]:
                        FreeCAD.Console.PrintMessage(
                            selection[0].Name + ' already in reference list\n')
                    else:
                        FreeCAD.Console.PrintMessage(
                            selection[0].Name + ':' + selection[1][0] + ' already in reference list\n')
            self.rebuildReferenceList()
            self.scheduleRecompute()
        self.updateSelectionbuttonUI()

    def rebuildReferenceList(self):
        # Disable change notifications while we add new items
        self.form.objectListWidget.itemChanged.disconnect(self.objectListItemChanged)

        # Initialise all to unchecked
        if self.allow_obj_sel:
            for i in range(self.form.objectListWidget.count()):
                listItem = self.form.objectListWidget.item(i)
                listItem.setCheckState(QtCore.Qt.Unchecked)

        self.form.listReferences.clear()
        items = []
        remove_refs = []
        for ref in self.ShapeRefs:
            try:
                idx = self.shapeNames.index(ref[0].Name)
            except ValueError:  # If shape doesn't exist anymore
                remove_refs.append(ref)
            else:
                listItem = self.form.objectListWidget.item(idx)
                for rr in ref[1]:
                    if rr:
                        item_label = self.shapeLabels[idx] + ':' + rr
                        if self.allow_obj_sel:
                            if listItem.checkState() == QtCore.Qt.Unchecked:
                                listItem.setCheckState(QtCore.Qt.PartiallyChecked)
                    else:
                        item_label = self.shapeLabels[idx]
                        if self.allow_obj_sel:
                            listItem.setCheckState(QtCore.Qt.Checked)
                    items.append((item_label, (ref[0], rr)))
        for ref in remove_refs:
            self.ShapeRefs.remove(ref)
        if remove_refs:
            self.scheduleRecompute()
        for listItem in items:
            item = QtGui.QListWidgetItem(listItem[0])
            item.setData(QtCore.Qt.UserRole, listItem[1])
            self.form.listReferences.addItem(item)
        self.form.listReferences.setSortingEnabled(False)
        self.form.objectListWidget.itemChanged.connect(self.objectListItemChanged)

    def objectListItemChanged(self, item):
        idx = item.data(QtCore.Qt.UserRole)
        object_name = self.shapeNames[idx]
        refs_to_remove = []
        for ref in self.ShapeRefs:
            if ref[0].Name == object_name:
                refs_to_remove.append(ref)
        for r in refs_to_remove:
            self.ShapeRefs.remove(r)
        if item.checkState() == QtCore.Qt.Checked:
            self.addSelection(self.doc_name, object_name, None, as_is=True)
        self.rebuildReferenceList()
        self.faceListShapeChosen()
        self.scheduleRecompute()

    def faceListShapeChosen(self):
        if self.form.faceListWidget.isVisible():
            self.populateFaceList()

    def faceSelectPushButtonChanged(self, checked):
        if checked:
            self.form.individualFacesFrame.setVisible(True)
            self.populateFaceList()
        else:
            self.form.individualFacesFrame.setVisible(False)

    def populateFaceList(self):
        ind = self.form.objectListWidget.currentIndex().row()
        object_name = self.shapeNames[ind]
        # Disable change notifications while we add new items
        self.form.faceListWidget.itemChanged.disconnect()
        self.shapeObj = FreeCADGui.ActiveDocument.Document.getObject(object_name)
        self.hideObjects()
        refs = list(self.ShapeRefs)
        self.form.faceListWidget.clear()
        FreeCADGui.showObject(self.shapeObj)
        if self.allow_face_sel:
            self.listOfShapeFaces = self.shapeObj.Shape.Faces
            selected_faces = []
            for ref in refs:
                if ref[0].Name == object_name:
                    selected_faces += ref[1]
            for i in range(len(self.listOfShapeFaces)):
                face_name = "Face" + str(i + 1)
                item = QtGui.QListWidgetItem(face_name, self.form.faceListWidget)
                item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
                checked = face_name in selected_faces
                if checked:
                    item.setCheckState(QtCore.Qt.Checked)
                else:
                    item.setCheckState(QtCore.Qt.Unchecked)
                self.form.faceListWidget.insertItem(i, item)
        if self.allow_solid_sel:
            self.listOfShapeSolids = self.shapeObj.Shape.Solids
            selected_solids = []
            for ref in refs:
                if ref[0].Name == object_name:
                    selected_solids += ref[1]
            for i in range(len(self.listOfShapeSolids)):
                solid_name = "Solid" + str(i + 1)
                item = QtGui.QListWidgetItem(solid_name, self.form.faceListWidget)
                item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
                checked = solid_name in selected_solids
                if checked:
                    item.setCheckState(QtCore.Qt.Checked)
                else:
                    item.setCheckState(QtCore.Qt.Unchecked)
                self.form.faceListWidget.insertItem(i, item)
        if self.allow_edge_sel:
            self.listOfShapeEdges = self.shapeObj.Shape.Edges
            selected_edges = [ref[1] for ref in refs if ref[0].Name == object_name]
            for i in range(len(self.listOfShapeEdges)):
                face_name = "Edge" + str(i + 1)
                item = QtGui.QListWidgetItem(face_name, self.form.faceListWidget)
                item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
                checked = face_name in selected_edges
                if checked:
                    item.setCheckState(QtCore.Qt.Checked)
                else:
                    item.setCheckState(QtCore.Qt.Unchecked)
                self.form.faceListWidget.insertItem(i, item)
        if self.allow_point_sel:
            self.listOfShapeVertices = self.shapeObj.Shape.Vertexes
            selected_solids = [ref[1] for ref in refs if ref[0].Name == object_name]
            for i in range(len(self.listOfShapeVertices)):
                face_name = "Vertex" + str(i + 1)
                item = QtGui.QListWidgetItem(face_name, self.form.faceListWidget)
                item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
                checked = face_name in selected_solids
                if checked:
                    item.setCheckState(QtCore.Qt.Checked)
                else:
                    item.setCheckState(QtCore.Qt.Unchecked)
                self.form.faceListWidget.insertItem(i, item)

        self.form.faceListWidget.itemChanged.connect(self.faceListItemChanged)

    def hideObjects(self):
        for i in FreeCADGui.ActiveDocument.Document.Objects:
            if 'Shape' in i.PropertiesList and len(i.Shape.Faces):
                FreeCADGui.hideObject(i)
        self.view_object.show()

    def faceHighlightChange(self):
        FreeCADGui.Selection.clearSelection()
        if self.form.faceListWidget.currentItem():
            FreeCADGui.Selection.addSelection(self.shapeObj, self.form.faceListWidget.currentItem().text())
        self.scheduleRecompute()

    def faceListItemChanged(self, item):
        object_name = self.shapeNames[self.form.objectListWidget.currentIndex().row()]
        face_name = item.text()
        if item.checkState() == QtCore.Qt.Checked:
            # If current object was already added in its entirety, remove it since we are now editing on the face level
            for ref in self.ShapeRefs:
                if ref[0].Name == object_name and ref[1] == ('',):
                    self.ShapeRefs.remove(ref)
            self.addSelection(self.doc_name, object_name, face_name, as_is=True)
        else:
            if not self.ShapeRefs:
                return
            for i, ref in enumerate(self.ShapeRefs):
                if ref[0].Name == object_name:
                    newsub = tuple([rr for rr in ref[1] if rr != face_name])
                    if not len(newsub):
                        self.ShapeRefs.remove(ref)
                    else:
                        self.ShapeRefs[i] = (ref[0], newsub)
            self.rebuildReferenceList()
        self.scheduleRecompute()

    def selectAllButtonClicked(self):
        for i in range(self.form.faceListWidget.count()):
            item = self.form.faceListWidget.item(i)
            item.setCheckState(QtCore.Qt.Checked)

    def selectNoneButtonClicked(self):
        for i in range(self.form.faceListWidget.count()):
            item = self.form.faceListWidget.item(i)
            item.setCheckState(QtCore.Qt.Unchecked)

    def scheduleRecompute(self):
        """ Only do one (costly) recompute when done processing - call this in preference to document.recompute() """
        self.recompute_timer.start()

    def recomputeDocument(self):
        # Re-assign to force update of FreeCAD property
        self.obj.ShapeRefs = self.ShapeRefs
        FreeCAD.getDocument(self.doc_name).recompute()

    def closing(self):
        """ Call this on close to let the widget to its proper cleanup """
        FreeCADGui.Selection.removeObserver(self)

    def __del__(self):
        # Just in case, make sure any stray selection observer is removed before object deleted
        FreeCADGui.Selection.removeObserver(self)
