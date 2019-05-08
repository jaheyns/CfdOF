# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2013-2015 - Juergen Riegel <FreeCAD@juergen-riegel.net> *
# *   Copyright (c) 2017 - Oliver Oxtoby <ooxtoby@csir.co.za>               *
# *   Copyright (c) 2017 - Johan Heyns <jheyns@csir.co.za>                  *
# *   Copyright (c) 2017 - Alfred Bogaers <abogaers@csir.co.za>             *
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
if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore
    from PySide import QtCore
    from PySide import QtGui
    from PySide.QtCore import QTimer
    try:  # Qt5
        from PySide2 import QtUiTools
    except ImportError:
        from PySide import QtUiTools


class CfdFaceSelectWidget:
    def __init__(self, parent_widget, obj, allow_face_sel, allow_solid_sel,
                 allow_point_sel=False, allow_edge_sel=False):
        ui_path = os.path.join(os.path.dirname(__file__), "TaskPanelCfdListOfFaces.ui")
        self.parent_widget = parent_widget
        self.form = FreeCADGui.PySideUic.loadUi(ui_path, self.parent_widget)
        self.parent_widget.layout().addWidget(self.form)

        self.selecting_references = False
        self.recompute_timer = QTimer()
        self.recompute_timer.setSingleShot(True)
        self.recompute_timer.timeout.connect(self.recomputeDocument)

        self.obj = obj
        self.References = self.obj.References
        self.doc_name = self.obj.Document.Name
        self.view_object = self.obj.ViewObject

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

        self.selection_mode_std_print_message = "Select {} by single-clicking " \
                                                "on them.".format(sel_msg)
        self.selection_mode_solid_print_message = "Select solids by single-clicking on a face or edge which belongs " \
                                                  "to the solid."

        exclusive_sel = (not allow_solid_sel) or not (allow_face_sel or allow_edge_sel or allow_point_sel)
        self.form.labelSelection.setVisible(not exclusive_sel)
        self.form.rb_standard.setVisible(not exclusive_sel)
        self.form.rb_solid.setVisible(not exclusive_sel)
        self.form.rb_standard.toggled.connect(self.choose_selection_mode_standard)
        self.form.rb_solid.toggled.connect(self.choose_selection_mode_solid)

        self.form.listReferences.currentRowChanged.connect(self.setReferenceListSelection)
        self.form.buttonAddFace.clicked.connect(self.buttonAddFaceClicked)
        self.form.buttonAddFace.setCheckable(True)
        self.form.buttonRemoveFace.clicked.connect(self.buttonRemoveFaceClicked)

        # Face list selection
        self.form.faceList.clicked.connect(self.faceListSelection)
        self.form.shapeComboBox.currentIndexChanged.connect(self.faceListShapeChosen)
        self.form.faceListWidget.itemSelectionChanged.connect(self.faceHighlightChange)
        self.form.faceListWidget.itemChanged.connect(self.faceListItemChanged)
        self.form.selectAllButton.clicked.connect(self.selectAllButtonClicked)
        self.form.selectNoneButton.clicked.connect(self.selectNoneButtonClicked)
        self.form.doneButton.clicked.connect(self.closeFaceList)
        self.form.shapeComboBox.setToolTip("Choose a solid object from the drop down list and select one or more of "
                                           "the faces associated with the chosen solid.")

        self.solidsNames = ['None']
        self.solidsLabels = ['None']
        for i in FreeCADGui.ActiveDocument.Document.Objects:
            if "Shape" in i.PropertiesList:
                # Do not restrict to solids
                if not i.Name.startswith("CfdFluidBoundary"):
                    self.solidsNames.append(i.Name)
                    self.solidsLabels.append(i.Label)

        self.rebuildReferenceList()

        # First time, add any currently selected faces to list
        if len(self.References) == 0:
            self.addSelectionToRefList()
            self.scheduleRecompute()
            FreeCADGui.Selection.clearSelection()
            self.updateSelectionbuttonUI()

    def setReferenceListSelection(self, row):
        if row > -1:
            self.enableSelectingMode(False)
            docName = str(self.doc_name)
            doc = FreeCAD.getDocument(docName)
            ref = self.References[row]
            selection_object = doc.getObject(ref[0])
            FreeCADGui.Selection.addSelection(selection_object, [str(ref[1])])

    def addSelectionToRefList(self):
        """ Add currently selected objects to reference list. """
        for sel in FreeCADGui.Selection.getSelectionEx():
            if sel.HasSubObjects:
                for sub in sel.SubElementNames:
                    print("{} {}".format(sel.ObjectName, sub))
                    self.addSelection(sel.DocumentName, sel.ObjectName, sub)
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
        if not self.References:
            return
        if not self.form.listReferences.currentItem():
            return
        current_item_name = str(self.form.listReferences.currentItem().text())
        for ref in self.References:
            idx = self.solidsNames.index(ref[0])
            refname = self.solidsLabels[idx] + ':' + ref[1]
            if refname == current_item_name:
                self.References.remove(ref)
        self.rebuildReferenceList()
        self.scheduleRecompute()

    def choose_selection_mode_standard(self, state):
        self.selection_mode_solid = not state
        self.updateSelectionbuttonUI()

    def choose_selection_mode_solid(self, state):
        self.selection_mode_solid = state
        self.updateSelectionbuttonUI()

    def updateSelectionbuttonUI(self):
        self.form.buttonAddFace.setChecked(self.selecting_references)
        if self.selecting_references:
            if self.selection_mode_solid:  # print message on button click
                print_message = self.selection_mode_solid_print_message
            else:
                print_message = self.selection_mode_std_print_message
        else:
            print_message = ""
        self.form.labelHelpText.setText(print_message)

    def addSelection(self, doc_name, obj_name, sub, selected_point=None, as_is=False):
        """ Add the selected sub-element (face) of the part to the Reference list. Prevent selection in other
        document.
        """
        if FreeCADGui.activeDocument().Document.Name != self.doc_name:
            return
        selected_object = FreeCAD.getDocument(doc_name).getObject(obj_name)
        # On double click on a vertex of a solid sub is None and obj is the solid
        print('Selection: ' +
              selected_object.Shape.ShapeType + '  ' +
              selected_object.Name + ':' +
              sub + " @ " + str(selected_point))
        if hasattr(selected_object, "Shape") and sub:
            if sub.startswith('Solid'):  # getElement doesn't work for solids
                elt = selected_object.Shape.Solids[int(sub.lstrip('Solid')) - 1]
            else:
                elt = selected_object.Shape.getElement(sub)
            selection = None
            if as_is:
                selection = (selected_object.Name, sub)
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
                    selection = (selected_object.Name, solid_to_add)
                    print('Selection element changed to Solid: ' +
                          selected_object.Shape.ShapeType + '  ' +
                          selection[0] + '  ' +
                          selection[1])
            else:
                # Allow Vertex, Edge, Face or just Face selection
                if (elt.ShapeType == 'Face' and self.allow_face_sel) or \
                        (elt.ShapeType == 'Edge' and self.allow_edge_sel) or \
                        (elt.ShapeType == 'Vertex' and self.allow_point_sel):
                    selection = (selected_object.Name, sub)
            if selection:
                if selection not in self.References:
                    self.References.append(selection)
                else:
                    FreeCAD.Console.PrintMessage(
                        selection[0] + ':' + selection[1] + ' already in reference list\n')
            self.rebuildReferenceList()
            self.scheduleRecompute()
        self.updateSelectionbuttonUI()

    def rebuildReferenceList(self):
        self.form.listReferences.clear()
        items = []
        remove_refs = []
        for ref in self.References:
            try:
                idx = self.solidsNames.index(ref[0])
            except ValueError:  # If solid doesn't exist anymore
                remove_refs.append(ref)
            else:
                item_name = self.solidsLabels[idx] + ':' + ref[1]
                items.append(item_name)
        for ref in remove_refs:
            self.References.remove(ref)
        if remove_refs:
            self.scheduleRecompute()
        for listItemName in items:
            self.form.listReferences.addItem(listItemName)
        # At the moment we assume order in listbox is the same as order of references
        self.form.listReferences.setSortingEnabled(False)

    def faceListSelection(self):
        self.form.stackedWidget.setCurrentIndex(1)
        self.form.shapeComboBox.clear()
        self.form.faceListWidget.clear()
        self.form.shapeComboBox.insertItems(1, self.solidsLabels)

    def faceListShapeChosen(self):
        ind = self.form.shapeComboBox.currentIndex()
        objectName = self.solidsNames[ind]
        if objectName != 'None':
            # Disable change notifications while we add new items
            self.form.faceListWidget.itemChanged.disconnect(self.faceListItemChanged)
            self.shapeObj = FreeCADGui.ActiveDocument.Document.getObject(objectName)
            self.hideObjects()
            refs = list(self.References)
            self.form.faceListWidget.clear()
            FreeCADGui.showObject(self.shapeObj)
            if self.allow_face_sel:
                self.listOfShapeFaces = self.shapeObj.Shape.Faces
                selected_faces = [ref[1] for ref in refs if ref[0] == objectName]
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
                selected_solids = [ref[1] for ref in refs if ref[0] == objectName]
                for i in range(len(self.listOfShapeSolids)):
                    face_name = "Solid" + str(i + 1)
                    item = QtGui.QListWidgetItem(face_name, self.form.faceListWidget)
                    item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
                    checked = face_name in selected_solids
                    if checked:
                        item.setCheckState(QtCore.Qt.Checked)
                    else:
                        item.setCheckState(QtCore.Qt.Unchecked)
                    self.form.faceListWidget.insertItem(i, item)
            if self.allow_edge_sel:
                self.listOfShapeEdges = self.shapeObj.Shape.Edges
                selected_edges = [ref[1] for ref in refs if ref[0] == objectName]
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
                selected_solids = [ref[1] for ref in refs if ref[0] == objectName]
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
            if "Shape" in i.PropertiesList:
                FreeCADGui.hideObject(i)
        self.view_object.show()

    def faceHighlightChange(self):
        FreeCADGui.Selection.clearSelection()
        FreeCADGui.Selection.addSelection(self.shapeObj, self.form.faceListWidget.currentItem().text())
        self.scheduleRecompute()

    def faceListItemChanged(self, item):
        object_name = self.solidsNames[self.form.shapeComboBox.currentIndex()]
        if object_name != 'None':
            face_name = item.text()
            if item.checkState() == QtCore.Qt.Checked:
                self.addSelection(self.doc_name, object_name, face_name, as_is=True)
            else:
                if not self.References:
                    return
                for ref in self.References:
                    if ref[0] == object_name and ref[1] == face_name:
                        self.References.remove(ref)
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

    def closeFaceList(self):
        self.form.stackedWidget.setCurrentIndex(0)
        # self.obj.ViewObject.show()

    def scheduleRecompute(self):
        """ Only do one (costly) recompute when done processing - call this in preference to document.recompute() """
        self.recompute_timer.start()

    def recomputeDocument(self):
        # Re-assign to force update of FreeCAD property
        self.obj.References = self.References
        FreeCAD.getDocument(self.doc_name).recompute()

    def closing(self):
        """ Call this on close to let the widget to its proper cleanup """
        FreeCADGui.Selection.removeObserver(self)

    def __del__(self):
        # Just in case, make sure any stray selection observer is removed before object deleted
        FreeCADGui.Selection.removeObserver(self)
