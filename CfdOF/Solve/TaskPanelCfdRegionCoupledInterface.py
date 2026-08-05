# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileNotice: Part of the CfdOF addon.

import FreeCAD

if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore, QtGui

from CfdOF import CfdTools
from CfdOF.Solve import CfdRegionCoupledInterface


class TaskPanelCfdRegionCoupledInterface:
    """Task panel for selecting and generating region-coupled interfaces."""

    def __init__(self, obj):
        self.obj = obj
        self.analysis_obj = CfdTools.getParentAnalysisObject(obj)
        self.RegionNamesOrig = list(obj.RegionNames)
        self.RegionObjectsOrig = list(getattr(obj, 'RegionObjects', []))
        self.ShapeRefsOrig = list(obj.ShapeRefs)
        self.InterfacePairsOrig = list(getattr(obj, 'InterfacePairs', []))
        self.ThermalBoundaryTypeOrig = obj.ThermalBoundaryType
        self.DisplayInterfaceOrig = bool(getattr(obj, 'DisplayInterface', True))
        self.DisplaySolidSolidInterfaceOrig = bool(getattr(obj, 'DisplaySolidSolidInterface', True))
        self.DisplaySolidLiquidInterfaceOrig = bool(getattr(obj, 'DisplaySolidLiquidInterface', True))
        self.RegionRolesOrig = dict(
            (region_obj.Name, getattr(region_obj, 'RegionRole'))
            for region_obj in getattr(obj, 'RegionObjects', [])
            if hasattr(region_obj, 'RegionRole')
        )
        self.NeedsCaseRewriteOrig = self.analysis_obj.NeedsCaseRewrite
        self.candidates_by_selection_object = {}
        self.candidates = self._collect_candidates()
        self.candidates_by_object = dict((candidate[1].Name, candidate) for candidate in self.candidates)
        self.choosing_regions = False
        self.choosing_faces = False

        self.form = QtGui.QWidget()
        self.form.setWindowTitle("Region-coupled interface")
        layout = QtGui.QVBoxLayout(self.form)

        self.regionHelpLabel = QtGui.QLabel("Select multiple generated region objects, then press Generate interface faces to automatically detect paired touching faces.")

        layout.addWidget(QtGui.QLabel("Region objects"))
        choose_layout = QtGui.QHBoxLayout()
        self.chooseRegionsButton = QtGui.QPushButton("Choose regions")
        self.chooseRegionsButton.setCheckable(True)
        self.chooseRegionsButton.clicked.connect(self.chooseRegionsClicked)
        choose_layout.addWidget(self.chooseRegionsButton)
        self.selectFromListButton = QtGui.QPushButton("Select from list")
        self.selectFromListButton.setCheckable(True)
        self.selectFromListButton.clicked.connect(self.selectFromList)
        choose_layout.addWidget(self.selectFromListButton)
        self.clearRegionsButton = QtGui.QPushButton("Clear")
        self.clearRegionsButton.clicked.connect(self.clearRegions)
        choose_layout.addWidget(self.clearRegionsButton)
        layout.addLayout(choose_layout)

        self.selectedRegionList = QtGui.QTableWidget()
        self.selectedRegionList.setColumnCount(2)
        self.selectedRegionList.setHorizontalHeaderLabels(["Region object", "Role"])
        self.selectedRegionList.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.selectedRegionList.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.selectedRegionList.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.selectedRegionList.setMinimumHeight(120)
        self.selectedRegionList.currentCellChanged.connect(self.setSelectedRegionListSelection)
        selected_resize_mode = getattr(self.selectedRegionList.horizontalHeader(), 'setSectionResizeMode',
                                       self.selectedRegionList.horizontalHeader().setResizeMode)
        selected_resize_mode(0, QtGui.QHeaderView.Stretch)
        selected_resize_mode(1, QtGui.QHeaderView.ResizeToContents)
        layout.addWidget(self.selectedRegionList)

        self.regionHelpLabel.setWordWrap(True)
        layout.addWidget(self.regionHelpLabel)

        edit_layout = QtGui.QGridLayout()
        edit_layout.setColumnStretch(0, 1)
        edit_layout.setColumnStretch(1, 1)
        edit_layout.setColumnStretch(3, 1)
        edit_layout.setColumnStretch(5, 1)
        self.addRegionButton = QtGui.QPushButton("Add")
        self.addRegionButton.setCheckable(True)
        self.addRegionButton.clicked.connect(self.addRegionButtonClicked)
        edit_layout.addWidget(self.addRegionButton, 0, 2)
        self.removeRegionButton = QtGui.QPushButton("Remove")
        self.removeRegionButton.clicked.connect(self.removeSelectedRegions)
        edit_layout.addWidget(self.removeRegionButton, 0, 4)
        layout.addLayout(edit_layout)

        self.availableRegionList = QtGui.QListWidget()
        self.availableRegionList.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
        self.availableRegionList.setMinimumHeight(120)
        self.availableRegionList.itemChanged.connect(self.availableRegionListItemChanged)
        self.availableRegionList.setVisible(False)
        layout.addWidget(self.availableRegionList)

        self.thermalCombo = QtGui.QComboBox()
        for item in CfdRegionCoupledInterface.THERMAL_BOUNDARY_TYPES:
            self.thermalCombo.addItem(item)

        self.generateButton = QtGui.QPushButton("Generate interface faces")
        self.generateButton.clicked.connect(self.generateTouchingPatches)
        layout.addWidget(self.generateButton)

        self.displayInterfaceButton = QtGui.QPushButton("Display interface")
        self.displayInterfaceButton.setCheckable(True)
        self.displayInterfaceButton.clicked.connect(self.displayInterfaceToggled)
        layout.addWidget(self.displayInterfaceButton)

        display_filter_layout = QtGui.QHBoxLayout()
        self.displaySolidSolidInterfaceButton = QtGui.QPushButton("Hide solid-solid interface")
        self.displaySolidSolidInterfaceButton.setCheckable(True)
        self.displaySolidSolidInterfaceButton.clicked.connect(self.displaySolidSolidInterfaceToggled)
        display_filter_layout.addWidget(self.displaySolidSolidInterfaceButton)
        self.displaySolidLiquidInterfaceButton = QtGui.QPushButton("Hide solid-liquid interface")
        self.displaySolidLiquidInterfaceButton.setCheckable(True)
        self.displaySolidLiquidInterfaceButton.clicked.connect(self.displaySolidLiquidInterfaceToggled)
        display_filter_layout.addWidget(self.displaySolidLiquidInterfaceButton)
        layout.addLayout(display_filter_layout)

        layout.addWidget(QtGui.QLabel("Interface faces"))
        self.faceTable = QtGui.QTableWidget()
        self.faceTable.setColumnCount(4)
        self.faceTable.setHorizontalHeaderLabels(["Face A", "Face B", "Thermal type", "Value"])
        self.faceTable.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.faceTable.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.faceTable.setEditTriggers(QtGui.QAbstractItemView.DoubleClicked |
                                       QtGui.QAbstractItemView.EditKeyPressed)
        self.faceTable.itemChanged.connect(self.interfaceFaceTableItemChanged)
        self.faceTable.currentCellChanged.connect(self.setInterfaceFaceTableSelection)
        self.faceTable.horizontalHeader().setStretchLastSection(True)
        resize_mode = getattr(self.faceTable.horizontalHeader(), 'setSectionResizeMode',
                              self.faceTable.horizontalHeader().setResizeMode)
        resize_mode(0, QtGui.QHeaderView.Stretch)
        resize_mode(1, QtGui.QHeaderView.Stretch)
        resize_mode(3, QtGui.QHeaderView.Stretch)
        layout.addWidget(self.faceTable)

        face_edit_layout = QtGui.QGridLayout()
        face_edit_layout.setColumnStretch(0, 1)
        face_edit_layout.setColumnStretch(1, 1)
        face_edit_layout.setColumnStretch(3, 1)
        face_edit_layout.setColumnStretch(5, 1)
        self.selectFaceButton = QtGui.QPushButton("Select face")
        self.selectFaceButton.setCheckable(True)
        self.selectFaceButton.clicked.connect(self.selectFaceButtonClicked)
        face_edit_layout.addWidget(self.selectFaceButton, 0, 1)
        self.removeFaceButton = QtGui.QPushButton("Remove face")
        self.removeFaceButton.clicked.connect(self.removeSelectedInterfaceFaceCell)
        face_edit_layout.addWidget(self.removeFaceButton, 0, 2)
        self.addPairButton = QtGui.QPushButton("Add pair")
        self.addPairButton.clicked.connect(self.addInterfacePair)
        face_edit_layout.addWidget(self.addPairButton, 0, 3)
        self.removePairButton = QtGui.QPushButton("Remove pair")
        self.removePairButton.clicked.connect(self.removeSelectedInterfacePairs)
        face_edit_layout.addWidget(self.removePairButton, 0, 4)
        layout.addLayout(face_edit_layout)

        self.statusLabel = QtGui.QLabel("")
        self.statusLabel.setWordWrap(True)
        layout.addWidget(self.statusLabel)

        self._load()
        self._refreshFaceTable()

    def _collect_candidates(self):
        candidates = []
        candidate_names = set()
        names_seen = set()
        represented_shapes = set()

        def add_candidate(region_name, region_obj, shape, selection_objects=()):
            if region_obj.Name in candidate_names:
                return
            candidate = (region_name, region_obj, shape)
            candidates.append(candidate)
            candidate_names.add(region_obj.Name)
            for selection_obj in selection_objects:
                if selection_obj is not None:
                    self.candidates_by_selection_object[selection_obj.Name] = candidate

        if self.analysis_obj is None:
            return candidates
        for mesh_obj in CfdTools.getMeshObjects(self.analysis_obj):
            region_name = CfdRegionCoupledInterface.getRegionName(mesh_obj)
            region_obj = mesh_obj
            shape = CfdRegionCoupledInterface.getRegionShape(mesh_obj)
            part = getattr(mesh_obj, 'Part', None)
            interface_region = CfdRegionCoupledInterface.getInterfaceRegionForSource(part)
            if interface_region is not None:
                region_obj = interface_region
                shape = interface_region.Shape
            if region_name and shape is not None:
                add_candidate(region_name, region_obj, shape, (mesh_obj, part))
                names_seen.add(region_name)
                if part is not None:
                    represented_shapes.add(part.Name)
                represented_shapes.add(region_obj.Name)
        for solid_obj in CfdTools.getSolidMaterials(self.analysis_obj):
            region_name = CfdRegionCoupledInterface.getRegionName(solid_obj)
            region_obj = solid_obj
            shape = CfdRegionCoupledInterface.getRegionShape(solid_obj)
            source_ref = None
            refs = getattr(solid_obj, 'ShapeRefs', [])
            if refs:
                source_ref = refs[0][0]
                interface_region = CfdRegionCoupledInterface.getInterfaceRegionForSource(source_ref)
                if interface_region is not None:
                    region_obj = interface_region
                    shape = interface_region.Shape
            if region_name and shape is not None and region_name not in names_seen:
                add_candidate(region_name, region_obj, shape, (solid_obj, source_ref))
                for ref_obj, _subnames in refs:
                    represented_shapes.add(ref_obj.Name)
                represented_shapes.add(region_obj.Name)
        for shape_obj in self.obj.Document.Objects:
            if shape_obj.Name in represented_shapes or shape_obj is self.obj:
                continue
            if not hasattr(shape_obj, 'Shape') or shape_obj.Shape.isNull():
                continue
            if CfdRegionCoupledInterface.isInterfaceNccGeneratedObject(shape_obj) and \
                    not CfdRegionCoupledInterface.isFinalInterfaceRegionObject(shape_obj):
                continue
            interface_region = CfdRegionCoupledInterface.getInterfaceRegionForSource(shape_obj)
            if interface_region is not None and interface_region is not shape_obj:
                represented_shapes.add(shape_obj.Name)
                continue
            if hasattr(shape_obj, 'Proxy') and getattr(shape_obj.Proxy, 'Type', '').startswith('Cfd'):
                continue
            add_candidate(CfdRegionCoupledInterface.getRegionName(shape_obj), shape_obj, shape_obj.Shape,
                          (shape_obj, getattr(shape_obj, 'SourceObject', None)))
        return candidates

    def _load(self):
        selected_names = set(self.obj.RegionNames)
        selected_objects = []
        selected_roles_by_region = {}
        for region_name, selected_obj in zip(
                getattr(self.obj, 'RegionNames', []), getattr(self.obj, 'RegionObjects', [])):
            selected_objects.append(
                CfdRegionCoupledInterface.getInterfaceRegionForSource(selected_obj) or selected_obj
            )
            role = getattr(selected_obj, 'RegionRole', None)
            if role is not None:
                selected_roles_by_region[region_name] = role
        self.availableRegionList.blockSignals(True)
        if not self.candidates:
            item = QtGui.QListWidgetItem("No region shapes found")
            item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEnabled)
            self.availableRegionList.addItem(item)
        else:
            for region_name, region_obj, _shape in self.candidates:
                item = QtGui.QListWidgetItem(self._candidateListLabel(region_name, region_obj))
                item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
                checked = region_name in selected_names or region_obj in selected_objects
                item.setCheckState(QtCore.Qt.Checked if checked else QtCore.Qt.Unchecked)
                item.setData(QtCore.Qt.UserRole, region_obj.Name)
                self.availableRegionList.addItem(item)
                if checked:
                    self._addCandidateToSelectedList(
                        (region_name, region_obj, _shape),
                        update_object=False,
                        role=selected_roles_by_region.get(region_name),
                    )
        self.availableRegionList.blockSignals(False)
        if self.selectedRegionList.rowCount():
            self._syncObjectFromSelectedList(clear_interface_faces=False)
            self._ensureGeneratedInterfaceFaces(report_errors=False)
        idx = self.thermalCombo.findText(str(self.obj.ThermalBoundaryType))
        self.thermalCombo.setCurrentIndex(idx if idx >= 0 else 0)
        display_interface = bool(getattr(self.obj, 'DisplayInterface', True))
        self.displayInterfaceButton.setChecked(display_interface)
        self._setInterfaceDisplay(display_interface)
        self._setSolidSolidInterfaceDisplay(bool(getattr(self.obj, 'DisplaySolidSolidInterface', True)))
        self._setSolidLiquidInterfaceDisplay(bool(getattr(self.obj, 'DisplaySolidLiquidInterface', True)))

    def _selected_candidates(self):
        selected = []
        for row in range(self.selectedRegionList.rowCount()):
            item = self.selectedRegionList.item(row, 0)
            if item is None:
                continue
            candidate = self.candidates_by_object.get(item.data(QtCore.Qt.UserRole))
            if candidate:
                selected.append(candidate)
        return selected

    def _syncObjectFromSelectedList(self, clear_interface_faces=True):
        selected = self._selected_candidates()
        self._syncRegionRolesFromTable()
        self.obj.RegionNames = [region_name for region_name, _obj, _shape in selected]
        self.obj.RegionObjects = [obj for _region_name, obj, _shape in selected]
        if clear_interface_faces:
            self.obj.ShapeRefs = []
            self.obj.InterfacePairs = []
            self._refreshFaceTable()
        self._recomputeInterfaceObject()
        return selected

    def _syncRegionRolesFromTable(self):
        for row in range(self.selectedRegionList.rowCount()):
            item = self.selectedRegionList.item(row, 0)
            combo = self.selectedRegionList.cellWidget(row, 1)
            if item is None or combo is None:
                continue
            candidate = self.candidates_by_object.get(item.data(QtCore.Qt.UserRole))
            if not candidate:
                continue
            _region_name, region_obj, _shape = candidate
            self._setRegionObjectRole(region_obj, combo.currentText(), recompute=False)

    def _reloadRegionLists(self):
        self.candidates_by_selection_object = {}
        self.candidates = self._collect_candidates()
        self.candidates_by_object = dict((candidate[1].Name, candidate) for candidate in self.candidates)
        self.selectedRegionList.setRowCount(0)
        self.availableRegionList.blockSignals(True)
        self.availableRegionList.clear()
        self.availableRegionList.blockSignals(False)
        self._load()

    def _sourceRolesFromSelectedRegionTable(self):
        source_objects = []
        region_roles = {}
        seen_sources = set()
        for row in range(self.selectedRegionList.rowCount()):
            item = self.selectedRegionList.item(row, 0)
            combo = self.selectedRegionList.cellWidget(row, 1)
            if item is None or combo is None:
                continue
            candidate = self.candidates_by_object.get(item.data(QtCore.Qt.UserRole))
            if not candidate:
                continue
            _region_name, region_obj, _shape = candidate
            source_obj = getattr(region_obj, 'SourceObject', None)
            if source_obj is None:
                part_obj = getattr(region_obj, 'Part', None)
                if part_obj is not None and hasattr(part_obj, 'Shape') and not part_obj.Shape.isNull():
                    source_obj = part_obj
                else:
                    refs = getattr(region_obj, 'ShapeRefs', [])
                    if refs and hasattr(refs[0][0], 'Shape') and not refs[0][0].Shape.isNull():
                        source_obj = refs[0][0]
                    elif hasattr(region_obj, 'Shape') and not region_obj.Shape.isNull():
                        source_obj = region_obj
            if source_obj is None:
                return None, None
            if source_obj.Name not in seen_sources:
                source_objects.append(source_obj)
                seen_sources.add(source_obj.Name)
            region_roles[source_obj.Name] = self._normaliseRegionRole(combo.currentText())
        return source_objects, region_roles

    def _regenerateInterfaceRegionsFromSelectedRoles(self):
        source_objects, region_roles = self._sourceRolesFromSelectedRegionTable()
        if not source_objects or len(source_objects) < 2:
            return False
        from CfdOF.Solve import CfdInterfaceNccRegions
        _compound, _slice_objects, interface = CfdInterfaceNccRegions.createInterfaceNccRegions(
            source_objects,
            analysis_obj=self.analysis_obj,
            region_roles=region_roles,
            interface_obj=self.obj,
        )
        self.obj = interface
        self._reloadRegionLists()
        return True

    def _candidateListLabel(self, region_name, region_obj):
        part = getattr(region_obj, 'Part', None)
        if part is not None:
            sub_shape = getattr(region_obj, 'PartSubShape', '')
            if sub_shape:
                return "{}: {} ({})".format(part.Label, sub_shape, region_name)
            return "{} ({})".format(part.Label, region_name)
        refs = getattr(region_obj, 'ShapeRefs', [])
        if refs:
            ref_obj, subnames = refs[0]
            if subnames:
                return "{}: {} ({})".format(ref_obj.Label, ", ".join(subnames), region_name)
            return "{} ({})".format(ref_obj.Label, region_name)
        return "{} ({})".format(region_obj.Label, region_name)

    def _candidate_for_selection(self, selected_object, subname):
        candidate = self.candidates_by_selection_object.get(selected_object.Name)
        if candidate is not None:
            return candidate
        for candidate in self.candidates:
            _region_name, region_obj, _shape = candidate
            if selected_object is region_obj:
                return candidate
            part = getattr(region_obj, 'Part', None)
            if part is selected_object:
                part_subshape = getattr(region_obj, 'PartSubShape', '')
                if not part_subshape or not subname or subname == part_subshape:
                    return candidate
            refs = getattr(region_obj, 'ShapeRefs', [])
            for ref_obj, subnames in refs:
                if ref_obj is not selected_object:
                    continue
                if not subnames or not subname or subname in subnames:
                    return candidate
        if hasattr(selected_object, 'Shape') and subname:
            try:
                selected_shape = selected_object.Shape.getElement(subname)
                centroid = selected_shape.CenterOfMass
            except Exception:
                return None
            containing = []
            for candidate in self.candidates:
                _region_name, _region_obj, shape = candidate
                try:
                    if shape.isInside(centroid, 1e-5, True):
                        containing.append(candidate)
                except Exception:
                    pass
            if len(containing) == 1:
                return containing[0]
        return None

    def _candidateIsSelected(self, region_obj):
        for row in range(self.selectedRegionList.rowCount()):
            item = self.selectedRegionList.item(row, 0)
            if item is None:
                continue
            if item.data(QtCore.Qt.UserRole) == region_obj.Name:
                return True
        return False

    def _addCandidateToSelectedList(self, candidate, update_object=True, role=None):
        region_name, region_obj, _shape = candidate
        if self._candidateIsSelected(region_obj):
            return False
        row = self.selectedRegionList.rowCount()
        self.selectedRegionList.insertRow(row)
        item = QtGui.QTableWidgetItem(self._candidateListLabel(region_name, region_obj))
        item.setData(QtCore.Qt.UserRole, region_obj.Name)
        self.selectedRegionList.setItem(row, 0, item)
        role_combo = self._makeRegionRoleCombo(region_obj, row, role)
        self.selectedRegionList.setCellWidget(row, 1, role_combo)
        self.selectedRegionList.resizeRowsToContents()
        if update_object:
            self._syncObjectFromSelectedList()
        return True

    def _removeCandidateFromSelectedList(self, region_obj, update_object=True):
        for row in range(self.selectedRegionList.rowCount() - 1, -1, -1):
            item = self.selectedRegionList.item(row, 0)
            if item is None:
                continue
            if item.data(QtCore.Qt.UserRole) == region_obj.Name:
                self.selectedRegionList.removeRow(row)
        if update_object:
            self._syncObjectFromSelectedList()
        return False

    def _normaliseRegionRole(self, role):
        role_text = str(role or '').strip().lower()
        if role_text == CfdRegionCoupledInterface.REGION_ROLE_FLUID.lower():
            return CfdRegionCoupledInterface.REGION_ROLE_FLUID
        return CfdRegionCoupledInterface.REGION_ROLE_SOLID

    def _defaultRegionRoleForRow(self, row):
        return CfdRegionCoupledInterface.REGION_ROLE_FLUID if row == 0 else \
            CfdRegionCoupledInterface.REGION_ROLE_SOLID

    def _setRegionObjectRole(self, region_obj, role, recompute=True):
        role = self._normaliseRegionRole(role)
        if not hasattr(region_obj, 'RegionRole'):
            CfdTools.addObjectProperty(
                region_obj,
                'RegionRole',
                role,
                'App::PropertyString',
                'Interface NCC',
                'Region role for interface NCC coupling',
            )
        region_obj.RegionRole = role
        if recompute:
            self._recomputeInterfaceObject()

    def _makeRegionRoleCombo(self, region_obj, row, role=None):
        role_combo = QtGui.QComboBox()
        for role_option in (CfdRegionCoupledInterface.REGION_ROLE_FLUID,
                            CfdRegionCoupledInterface.REGION_ROLE_SOLID):
            role_combo.addItem(role_option)
        selected_role = role if role is not None else getattr(region_obj, 'RegionRole', None)
        if selected_role is None:
            selected_role = self._defaultRegionRoleForRow(row)
        selected_role = self._normaliseRegionRole(selected_role)
        self._setRegionObjectRole(region_obj, selected_role, recompute=False)
        role_combo.setCurrentIndex(role_combo.findText(selected_role))
        role_combo.currentTextChanged.connect(
            lambda selected_role, obj=region_obj: self._setRegionObjectRole(obj, selected_role))
        return role_combo

    def _setAvailableCandidateChecked(self, region_obj, checked=True):
        self.availableRegionList.blockSignals(True)
        for row in range(self.availableRegionList.count()):
            item = self.availableRegionList.item(row)
            if item.data(QtCore.Qt.UserRole) == region_obj.Name:
                item.setCheckState(QtCore.Qt.Checked if checked else QtCore.Qt.Unchecked)
                break
        self.availableRegionList.blockSignals(False)

    def setSelectedRegionListSelection(self, row, _column=None, _previous_row=None, _previous_column=None):
        if row < 0:
            return
        item = self.selectedRegionList.item(row, 0)
        if item is None:
            return
        candidate = self.candidates_by_object.get(item.data(QtCore.Qt.UserRole))
        if not candidate:
            return
        _region_name, region_obj, _shape = candidate
        FreeCADGui.Selection.clearSelection()
        part = getattr(region_obj, 'Part', None)
        if part is not None:
            sub_shape = getattr(region_obj, 'PartSubShape', '')
            if sub_shape:
                FreeCADGui.Selection.addSelection(part, sub_shape)
            else:
                FreeCADGui.Selection.addSelection(part)
        else:
            FreeCADGui.Selection.addSelection(region_obj)

    def availableRegionListItemChanged(self, item):
        candidate = self.candidates_by_object.get(item.data(QtCore.Qt.UserRole))
        if not candidate:
            return
        _region_name, region_obj, _shape = candidate
        if item.checkState() == QtCore.Qt.Checked:
            self._addCandidateToSelectedList(candidate)
        else:
            self._removeCandidateFromSelectedList(region_obj)
        selected = self._syncObjectFromSelectedList()
        self.statusLabel.setText("{} region object(s) selected from list.".format(len(selected)))

    def selectFromList(self):
        if self.selectFromListButton.isChecked():
            self.availableRegionList.setVisible(True)
            self.availableRegionList.setFocus()
            self.statusLabel.setText(
                "Tick the region shapes to connect. No component selection is required.")
        else:
            self.availableRegionList.setVisible(False)
            self.statusLabel.setText("")

    def _setInterfaceDisplay(self, display_interface):
        self.obj.DisplayInterface = bool(display_interface)
        if getattr(self.obj, 'ViewObject', None):
            self.obj.ViewObject.Visibility = bool(display_interface)
        self.displayInterfaceButton.setText(
            "Hide interface" if display_interface else "Display interface")

    def displayInterfaceToggled(self, checked):
        self._setInterfaceDisplay(checked)
        self.statusLabel.setText(
            "Interface display enabled." if checked else "Interface display hidden.")

    def _recomputeInterfaceDisplay(self):
        try:
            self.obj.Proxy.execute(self.obj)
        except Exception:
            self.obj.Document.recompute()

    def _setSolidSolidInterfaceDisplay(self, display_interface):
        self.obj.DisplaySolidSolidInterface = bool(display_interface)
        self.displaySolidSolidInterfaceButton.setChecked(bool(display_interface))
        self.displaySolidSolidInterfaceButton.setText(
            "Hide solid-solid interface" if display_interface else "Show solid-solid interface")
        self._recomputeInterfaceDisplay()

    def displaySolidSolidInterfaceToggled(self, checked):
        self._setSolidSolidInterfaceDisplay(checked)
        self.statusLabel.setText(
            "Solid-solid interface display enabled." if checked else "Solid-solid interface display hidden.")

    def _setSolidLiquidInterfaceDisplay(self, display_interface):
        self.obj.DisplaySolidLiquidInterface = bool(display_interface)
        self.displaySolidLiquidInterfaceButton.setChecked(bool(display_interface))
        self.displaySolidLiquidInterfaceButton.setText(
            "Hide solid-liquid interface" if display_interface else "Show solid-liquid interface")
        self._recomputeInterfaceDisplay()

    def displaySolidLiquidInterfaceToggled(self, checked):
        self._setSolidLiquidInterfaceDisplay(checked)
        self.statusLabel.setText(
            "Solid-liquid interface display enabled." if checked else "Solid-liquid interface display hidden.")

    def addRegionButtonClicked(self):
        selecting = not self.choosing_regions
        if selecting and len(FreeCADGui.Selection.getSelectionEx()) >= 1:
            for sel in FreeCADGui.Selection.getSelectionEx():
                if sel.HasSubObjects:
                    for sub in sel.SubElementNames:
                        self._addSelectionCandidate(sel.DocumentName, sel.ObjectName, sub)
                else:
                    self._addSelectionCandidate(sel.DocumentName, sel.ObjectName, None)
            selecting = False
        self._enableChoosingRegions(selecting)

    def chooseRegionsClicked(self):
        self._enableChoosingRegions(self.chooseRegionsButton.isChecked())

    def _enableChoosingRegions(self, choosing):
        if self.choosing_regions == choosing:
            self.chooseRegionsButton.setChecked(choosing)
            self.addRegionButton.setChecked(choosing)
            return
        if choosing:
            self._enableChoosingFaces(False)
        self.choosing_regions = choosing
        if self.choosing_regions:
            FreeCADGui.Selection.clearSelection()
            FreeCADGui.Selection.addObserver(self)
            self.statusLabel.setText(
                "Select mesh objects, material objects, or their region geometry in the tree or viewport.")
        else:
            FreeCADGui.Selection.removeObserver(self)
            self.statusLabel.setText("")
        self.chooseRegionsButton.setChecked(self.choosing_regions)
        self.addRegionButton.setChecked(self.choosing_regions)

    def clearRegions(self):
        self.availableRegionList.blockSignals(True)
        for row in range(self.availableRegionList.count()):
            item = self.availableRegionList.item(row)
            if item.flags() & QtCore.Qt.ItemIsUserCheckable:
                item.setCheckState(QtCore.Qt.Unchecked)
        self.availableRegionList.blockSignals(False)
        self.selectedRegionList.setRowCount(0)
        self.obj.RegionNames = []
        self.obj.RegionObjects = []
        self.obj.ShapeRefs = []
        self.obj.InterfacePairs = []
        self._refreshFaceTable()
        self.statusLabel.setText("Region selection cleared.")

    def removeSelectedRegions(self):
        selected_rows = sorted(set(index.row() for index in self.selectedRegionList.selectedIndexes()), reverse=True)
        if not selected_rows:
            return
        for row in selected_rows:
            item = self.selectedRegionList.item(row, 0)
            if item is None:
                continue
            candidate = self.candidates_by_object.get(item.data(QtCore.Qt.UserRole))
            if candidate:
                _region_name, region_obj, _shape = candidate
                self._setAvailableCandidateChecked(region_obj, False)
                self._removeCandidateFromSelectedList(region_obj, update_object=False)
        selected = self._syncObjectFromSelectedList()
        self.statusLabel.setText("{} region object(s) selected.".format(len(selected)))

    def _addSelectionCandidate(self, doc_name, obj_name, sub):
        if FreeCADGui.activeDocument().Document.Name != self.obj.Document.Name:
            return False
        selected_object = FreeCAD.getDocument(doc_name).getObject(obj_name)
        candidate = self._candidate_for_selection(selected_object, sub)
        if candidate is None:
            self.statusLabel.setText("Selection is not a known mesh/material region: {}".format(obj_name))
            return False
        region_name, region_obj, _shape = candidate
        self._addCandidateToSelectedList(candidate)
        self._setAvailableCandidateChecked(region_obj, True)
        selected_count = len(self._selected_candidates())
        self.statusLabel.setText(
            "Selected {}. {} region object(s) selected.".format(region_name, selected_count))
        return True

    def addSelection(self, doc_name, obj_name, sub, selected_point=None):
        if self.choosing_regions:
            self._addSelectionCandidate(doc_name, obj_name, sub)
        elif self.choosing_faces:
            self._addFaceSelection(doc_name, obj_name, sub)

    def _decodedInterfacePairs(self):
        return CfdRegionCoupledInterface._decode_interface_pairs(self.obj)

    def _encodeInterfacePairs(self, pairs):
        self.obj.InterfacePairs = [
            CfdRegionCoupledInterface.encodeInterfacePair(pair)
            for pair in pairs
        ]
        self._syncShapeRefsFromPairs(pairs)

    def _syncShapeRefsFromPairs(self, pairs=None):
        if pairs is None:
            pairs = self._decodedInterfacePairs()
        refs_by_object = {}
        for pair in pairs:
            for object_key, face_key in (('object_a', 'face_a'), ('object_b', 'face_b')):
                obj_name = pair.get(object_key, '')
                face_name = pair.get(face_key, '')
                if not obj_name or not face_name:
                    continue
                ref_obj = self.obj.Document.getObject(obj_name)
                if ref_obj is not None:
                    refs_by_object.setdefault(ref_obj, set()).add(face_name)
        self.obj.ShapeRefs = [
            (ref_obj, tuple(sorted(face_names, key=lambda name: int(name[4:]))))
            for ref_obj, face_names in refs_by_object.items()
        ]

    def _blankInterfacePair(self):
        return {
            'region_a': '',
            'object_a': '',
            'face_a': '',
            'region_b': '',
            'object_b': '',
            'face_b': '',
            'thermal_type': 'zeroGradient',
            'thermal_value': '',
        }

    def _selectedFaceCell(self):
        row = self.faceTable.currentRow()
        column = self.faceTable.currentColumn()
        if row < 0 or column not in (0, 1):
            selected_indexes = self.faceTable.selectedIndexes()
            for index in selected_indexes:
                if index.column() in (0, 1):
                    return index.row(), index.column()
            return None, None
        return row, column

    def _makeFaceLabel(self, object_name, face_name):
        ref_obj = self.obj.Document.getObject(object_name)
        if ref_obj is None:
            return "{}:{}".format(object_name, face_name)
        return "{}:{}".format(ref_obj.Label, face_name)

    def _addFaceTableItem(self, row, column, text, data=None):
        item = QtGui.QTableWidgetItem(text)
        if data is not None:
            item.setData(QtCore.Qt.UserRole, data)
        self.faceTable.setItem(row, column, item)
        return item

    def _setPairThermalType(self, pair_index, thermal_type):
        pairs = self._decodedInterfacePairs()
        if pair_index < 0 or pair_index >= len(pairs):
            return
        if thermal_type not in CfdRegionCoupledInterface.THERMAL_BOUNDARY_TYPES:
            thermal_type = "zeroGradient"
        old_field = CfdRegionCoupledInterface.THERMAL_VALUE_FIELDS.get(
            pairs[pair_index].get('thermal_type')
        )
        new_field = CfdRegionCoupledInterface.THERMAL_VALUE_FIELDS.get(thermal_type)
        pairs[pair_index]['thermal_type'] = thermal_type
        if not new_field:
            pairs[pair_index]['thermal_value'] = ''
        elif old_field != new_field or not pairs[pair_index].get('thermal_value', ''):
            pairs[pair_index]['thermal_value'] = CfdRegionCoupledInterface.defaultThermalValue(
                self.obj,
                thermal_type,
            )
        self._encodeInterfacePairs(pairs)
        self._refreshFaceTable()
        self._recomputeInterfaceObject()

    def _setPairThermalValue(self, pair_index, thermal_value):
        pairs = self._decodedInterfacePairs()
        if pair_index < 0 or pair_index >= len(pairs):
            return
        pairs[pair_index]['thermal_value'] = thermal_value
        self._encodeInterfacePairs(pairs)
        self._recomputeInterfaceObject()

    def interfaceFaceTableItemChanged(self, item):
        if item.column() != 3:
            return
        pair_index = item.data(QtCore.Qt.UserRole)
        if pair_index is None:
            return
        self._setPairThermalValue(pair_index, item.text())

    def _refreshFaceTable(self):
        self.faceTable.blockSignals(True)
        self.faceTable.setRowCount(0)
        interface_pairs = self._decodedInterfacePairs()
        if interface_pairs:
            self.faceTable.setRowCount(len(interface_pairs))
            for row, pair in enumerate(interface_pairs):
                self._addFaceTableItem(
                    row,
                    0,
                    self._makeFaceLabel(pair['object_a'], pair['face_a']) if pair['object_a'] and pair['face_a']
                    else "",
                    (pair['object_a'], pair['face_a'], row),
                )
                self._addFaceTableItem(
                    row,
                    1,
                    self._makeFaceLabel(pair['object_b'], pair['face_b']) if pair['object_b'] and pair['face_b']
                    else "",
                    (pair['object_b'], pair['face_b'], row),
                )
                combo = QtGui.QComboBox()
                combo.addItems(CfdRegionCoupledInterface.THERMAL_BOUNDARY_TYPES)
                combo.setCurrentIndex(max(
                    0,
                    combo.findText(pair.get('thermal_type', "zeroGradient")),
                ))
                combo.currentIndexChanged.connect(
                    lambda _index, pair_index=row, widget=combo:
                    self._setPairThermalType(pair_index, widget.currentText())
                )
                self.faceTable.setCellWidget(row, 2, combo)
                value_item = self._addFaceTableItem(
                    row,
                    3,
                    pair.get('thermal_value', ''),
                    row,
                )
                if pair.get('thermal_type', "zeroGradient") not in \
                        CfdRegionCoupledInterface.THERMAL_VALUE_FIELDS:
                    value_item.setFlags(value_item.flags() & ~QtCore.Qt.ItemIsEditable)
                    value_item.setText("")
        else:
            rows = [
                (ref_obj, subname)
                for ref_obj, subnames in self.obj.ShapeRefs
                for subname in subnames
            ]
            self.faceTable.setRowCount(len(rows))
            for row, (ref_obj, subname) in enumerate(rows):
                self._addFaceTableItem(row, 0, "{}:{}".format(ref_obj.Label, subname),
                                       (ref_obj.Name, subname, None))
                self._addFaceTableItem(row, 1, "")
                combo = QtGui.QComboBox()
                combo.addItems(CfdRegionCoupledInterface.THERMAL_BOUNDARY_TYPES)
                combo.setCurrentIndex(max(0, combo.findText(str(self.obj.ThermalBoundaryType))))
                combo.setEnabled(False)
                self.faceTable.setCellWidget(row, 2, combo)
                self._addFaceTableItem(row, 3, "")
        self.faceTable.resizeRowsToContents()
        self.faceTable.blockSignals(False)

    def setInterfaceFaceTableSelection(self, row, column, _previous_row, _previous_column):
        if row < 0:
            return
        FreeCADGui.Selection.clearSelection()
        columns = (column,) if column in (0, 1) else (0, 1)
        for table_column in columns:
            item = self.faceTable.item(row, table_column)
            if item is None:
                continue
            data = item.data(QtCore.Qt.UserRole)
            if not data:
                continue
            ref_obj_name, subname, _pair_index = data
            ref_obj = self.obj.Document.getObject(ref_obj_name)
            if ref_obj is not None and subname:
                FreeCADGui.Selection.addSelection(ref_obj, subname)

    def selectFaceButtonClicked(self):
        choosing = not self.choosing_faces
        row, column = self._selectedFaceCell()
        if row is None:
            self.statusLabel.setText("Select a Face A or Face B cell first.")
            self.selectFaceButton.setChecked(False)
            return
        if choosing and len(FreeCADGui.Selection.getSelectionEx()) >= 1:
            added = False
            for sel in FreeCADGui.Selection.getSelectionEx():
                if sel.HasSubObjects:
                    for sub in sel.SubElementNames:
                        added = self._addFaceSelection(sel.DocumentName, sel.ObjectName, sub) or added
            choosing = False
            if not added:
                self.statusLabel.setText("Select one face before pressing Select face.")
        self._enableChoosingFaces(choosing)

    def _enableChoosingFaces(self, choosing):
        if self.choosing_faces == choosing:
            self.selectFaceButton.setChecked(choosing)
            return
        if choosing:
            self._enableChoosingRegions(False)
        self.choosing_faces = choosing
        if self.choosing_faces:
            FreeCADGui.Selection.clearSelection()
            FreeCADGui.Selection.addObserver(self)
            self.statusLabel.setText("Select one interface face for the highlighted table cell.")
        else:
            FreeCADGui.Selection.removeObserver(self)
            self.statusLabel.setText("")
        self.selectFaceButton.setChecked(self.choosing_faces)

    def _addFaceSelection(self, doc_name, obj_name, sub):
        if FreeCADGui.activeDocument().Document.Name != self.obj.Document.Name:
            return False
        if not sub or not str(sub).startswith("Face"):
            self.statusLabel.setText("Selection is not a face: {}".format(obj_name))
            return False
        selected_object = FreeCAD.getDocument(doc_name).getObject(obj_name)
        row, column = self._selectedFaceCell()
        if row is None:
            self.statusLabel.setText("Select a Face A or Face B cell first.")
            return False
        if not self._setInterfacePairFace(row, column, selected_object, str(sub)):
            return False
        self._refreshFaceTable()
        self._recomputeInterfaceObject()
        self.statusLabel.setText("Set interface face {}:{}.".format(selected_object.Label, sub))
        return True

    def _setInterfacePairFace(self, row, column, ref_obj, subname):
        pairs = self._decodedInterfacePairs()
        if row < 0 or row >= len(pairs) or column not in (0, 1):
            return False
        try:
            ref_obj.Shape.getElement(subname)
        except Exception:
            self.statusLabel.setText("{}:{} is not a valid face.".format(ref_obj.Label, subname))
            return False
        region_name = CfdRegionCoupledInterface.getRegionName(ref_obj)
        if column == 0:
            pairs[row]['region_a'] = region_name
            pairs[row]['object_a'] = ref_obj.Name
            pairs[row]['face_a'] = subname
        else:
            pairs[row]['region_b'] = region_name
            pairs[row]['object_b'] = ref_obj.Name
            pairs[row]['face_b'] = subname
        self._encodeInterfacePairs(pairs)
        return True

    def removeSelectedInterfaceFaceCell(self):
        row, column = self._selectedFaceCell()
        if row is None:
            self.statusLabel.setText("Select a Face A or Face B cell first.")
            return
        pairs = self._decodedInterfacePairs()
        if row < 0 or row >= len(pairs):
            return
        if column == 0:
            pairs[row]['region_a'] = ''
            pairs[row]['object_a'] = ''
            pairs[row]['face_a'] = ''
        else:
            pairs[row]['region_b'] = ''
            pairs[row]['object_b'] = ''
            pairs[row]['face_b'] = ''
        self._encodeInterfacePairs(pairs)
        self._refreshFaceTable()
        self._recomputeInterfaceObject()
        self.statusLabel.setText("Removed selected face cell.")

    def addInterfacePair(self):
        pairs = self._decodedInterfacePairs()
        pairs.append(self._blankInterfacePair())
        self._encodeInterfacePairs(pairs)
        self._refreshFaceTable()
        row = len(pairs) - 1
        self.faceTable.setCurrentCell(row, 0)
        self.statusLabel.setText("Added interface pair row.")

    def removeSelectedInterfacePairs(self):
        selected_rows = sorted(set(index.row() for index in self.faceTable.selectedIndexes()), reverse=True)
        if not selected_rows:
            return
        remove_rows = set(selected_rows)
        remaining_pairs = [
            pair for row, pair in enumerate(self._decodedInterfacePairs())
            if row not in remove_rows
        ]
        self._encodeInterfacePairs(remaining_pairs)
        self._refreshFaceTable()
        self._recomputeInterfaceObject()
        self.statusLabel.setText("Removed {} interface pair row(s).".format(len(selected_rows)))

    def _recomputeInterfaceObject(self):
        self.obj.touch()
        self.obj.Document.recompute()

    def _storedInterfaceFacesAreCurrent(self, selected):
        if not self.obj.ShapeRefs:
            return False
        selected_object_names = set(obj.Name for _region_name, obj, _shape in selected)
        for ref_obj, _subnames in self.obj.ShapeRefs:
            if ref_obj.Name not in selected_object_names:
                return False
        current_refs = set(
            (ref_obj.Name, subname)
            for ref_obj, subnames in self.obj.ShapeRefs
            for subname in subnames
        )
        paired_refs = set()
        for pair in CfdRegionCoupledInterface._decode_interface_pairs(self.obj):
            if pair['object_a'] not in selected_object_names or pair['object_b'] not in selected_object_names:
                return False
            paired_refs.add((pair['object_a'], pair['face_a']))
            paired_refs.add((pair['object_b'], pair['face_b']))
        return bool(paired_refs) and current_refs == paired_refs

    def _ensureGeneratedInterfaceFaces(self, report_errors=True):
        selected = self._selected_candidates()
        if len(selected) < 2:
            return False
        if self._storedInterfaceFacesAreCurrent(selected):
            return True

        region_names = [region_name for region_name, _obj, _shape in selected]
        region_objects = [obj for _region_name, obj, _shape in selected]
        try:
            shape_refs, interface_pairs = CfdRegionCoupledInterface.generatePairedTouchingFaceData(region_objects)
        except ValueError as err:
            if report_errors:
                CfdTools.cfdErrorBox(str(err))
            else:
                self.statusLabel.setText(str(err))
            return False

        self.obj.RegionNames = region_names
        self.obj.RegionObjects = region_objects
        self.obj.ShapeRefs = shape_refs
        self.obj.InterfacePairs = interface_pairs
        face_count = sum(len(subnames) for _ref_obj, subnames in shape_refs)
        self.statusLabel.setText(
            "Generated {} paired interface face reference(s).".format(face_count))
        self._refreshFaceTable()
        self._recomputeInterfaceObject()
        return True

    def _incompletePairRows(self):
        incomplete_rows = []
        for row, pair in enumerate(self._decodedInterfacePairs(), 1):
            if not all(pair.get(key, '') for key in (
                    'region_a', 'object_a', 'face_a', 'region_b', 'object_b', 'face_b')):
                incomplete_rows.append(row)
        return incomplete_rows

    def _missingThermalValueRows(self):
        missing_rows = []
        for row, pair in enumerate(self._decodedInterfacePairs(), 1):
            if pair.get('thermal_type') in CfdRegionCoupledInterface.THERMAL_VALUE_FIELDS and \
                    not pair.get('thermal_value', '').strip():
                missing_rows.append(row)
        return missing_rows

    def generateTouchingPatches(self):
        self._regenerateInterfaceRegionsFromSelectedRoles()
        selected = self._selected_candidates()
        if len(selected) < 2:
            CfdTools.cfdErrorBox("Select at least two region objects to couple.")
            return

        region_names = [region_name for region_name, _obj, _shape in selected]
        region_objects = [obj for _region_name, obj, _shape in selected]
        try:
            shape_refs, interface_pairs = CfdRegionCoupledInterface.generatePairedTouchingFaceData(region_objects)
        except ValueError as err:
            CfdTools.cfdErrorBox(str(err))
            return

        self.obj.RegionNames = region_names
        self.obj.RegionObjects = region_objects
        self.obj.ShapeRefs = shape_refs
        self.obj.InterfacePairs = interface_pairs
        face_count = sum(len(subnames) for _ref_obj, subnames in shape_refs)
        self.statusLabel.setText(
            "Generated {} paired interface face reference(s).".format(face_count))
        self._refreshFaceTable()
        self._recomputeInterfaceObject()

    def accept(self):
        if self.choosing_regions:
            FreeCADGui.Selection.removeObserver(self)
            self.choosing_regions = False
        if self.choosing_faces:
            FreeCADGui.Selection.removeObserver(self)
            self.choosing_faces = False
        selected = self._selected_candidates()
        if len(selected) < 2:
            CfdTools.cfdErrorBox("Select at least two region objects to couple.")
            return False
        if not self._decodedInterfacePairs():
            self._ensureGeneratedInterfaceFaces(report_errors=True)
        incomplete_rows = self._incompletePairRows()
        if incomplete_rows:
            CfdTools.cfdErrorBox(
                "Complete or remove incomplete interface pair row(s): {}".format(
                    ", ".join(str(row) for row in incomplete_rows)
                )
            )
            return False
        missing_value_rows = self._missingThermalValueRows()
        if missing_value_rows:
            CfdTools.cfdErrorBox(
                "Enter thermal value for interface pair row(s): {}".format(
                    ", ".join(str(row) for row in missing_value_rows)
                )
            )
            return False
        if not self.obj.ShapeRefs:
            CfdTools.cfdErrorBox("Generate touching patches before closing the task panel.")
            return False
        self._syncRegionRolesFromTable()
        self.obj.RegionNames = [region_name for region_name, _obj, _shape in selected]
        self.obj.RegionObjects = [obj for _region_name, obj, _shape in selected]
        self.obj.ThermalBoundaryType = self.thermalCombo.currentText()
        self.analysis_obj.NeedsCaseRewrite = True
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()
        FreeCADGui.doCommand("FreeCAD.ActiveDocument.recompute()")
        return True

    def reject(self):
        if self.choosing_regions:
            FreeCADGui.Selection.removeObserver(self)
            self.choosing_regions = False
        if self.choosing_faces:
            FreeCADGui.Selection.removeObserver(self)
            self.choosing_faces = False
        self.obj.RegionNames = self.RegionNamesOrig
        self.obj.RegionObjects = self.RegionObjectsOrig
        self.obj.ShapeRefs = self.ShapeRefsOrig
        self.obj.InterfacePairs = self.InterfacePairsOrig
        self.obj.ThermalBoundaryType = self.ThermalBoundaryTypeOrig
        self.obj.DisplayInterface = self.DisplayInterfaceOrig
        self.obj.DisplaySolidSolidInterface = self.DisplaySolidSolidInterfaceOrig
        self.obj.DisplaySolidLiquidInterface = self.DisplaySolidLiquidInterfaceOrig
        for candidate in self.candidates:
            _region_name, region_obj, _shape = candidate
            if region_obj.Name in self.RegionRolesOrig:
                region_obj.RegionRole = self.RegionRolesOrig[region_obj.Name]
        if getattr(self.obj, 'ViewObject', None):
            self.obj.ViewObject.Visibility = self.DisplayInterfaceOrig
        self._recomputeInterfaceDisplay()
        self.analysis_obj.NeedsCaseRewrite = self.NeedsCaseRewriteOrig
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()
        return True

    def closing(self):
        if self.choosing_regions:
            FreeCADGui.Selection.removeObserver(self)
            self.choosing_regions = False
        if self.choosing_faces:
            FreeCADGui.Selection.removeObserver(self)
            self.choosing_faces = False
        return
