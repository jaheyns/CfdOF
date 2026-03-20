# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileNotice: Part of the CfdOF addon.

import os

import FreeCAD
from FreeCAD import Units
from CfdOF import CfdTools, CfdFaceSelectWidget
from CfdOF.CfdTools import setQuantity, getQuantity, storeIfChanged
if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtGui

SELECTION_MODE_LABELS = ["all", "cellZone"]


class TaskPanelCfdMeanVelocityForce:
    """
    Task panel for adding/editing mean velocity force fvOption objects
    """
    def __init__(self, obj):
        self.obj = obj
        self.analysis_obj = CfdTools.getParentAnalysisObject(obj)

        self.ShapeRefsOrig = list(self.obj.ShapeRefs)
        self.NeedsCaseRewriteOrig = self.analysis_obj.NeedsCaseRewrite

        ui_path = os.path.join(CfdTools.getModulePath(), 'Gui', "TaskPanelCfdMeanVelocityForce.ui")
        self.form = FreeCADGui.PySideUic.loadUi(ui_path)

        self.form.faceSelectWidget.setLayout(QtGui.QVBoxLayout())
        self.faceSelector = CfdFaceSelectWidget.CfdFaceSelectWidget(
            self.form.faceSelectWidget, self.obj, False, False, True)

        self.form.comboSelectionMode.currentIndexChanged.connect(self.updateUI)

        self.load()
        self.updateUI()

    def load(self):
        mode = getattr(self.obj, 'SelectionMode', 'all')
        try:
            idx = SELECTION_MODE_LABELS.index(mode)
        except ValueError:
            idx = 0
        self.form.comboSelectionMode.setCurrentIndex(idx)

        setQuantity(self.form.inputDirectionX, Units.Quantity(float(self.obj.Direction.x)))
        setQuantity(self.form.inputDirectionY, Units.Quantity(float(self.obj.Direction.y)))
        setQuantity(self.form.inputDirectionZ, Units.Quantity(float(self.obj.Direction.z)))

        setQuantity(self.form.inputUbarX, Units.Quantity("{} mm/s".format(float(self.obj.Ubar.x) * 1000.0)))
        setQuantity(self.form.inputUbarY, Units.Quantity("{} mm/s".format(float(self.obj.Ubar.y) * 1000.0)))
        setQuantity(self.form.inputUbarZ, Units.Quantity("{} mm/s".format(float(self.obj.Ubar.z) * 1000.0)))

        setQuantity(self.form.inputRelaxation, Units.Quantity(self.obj.Relaxation))

    def updateUI(self):
        is_cell_zone = self.form.comboSelectionMode.currentIndex() == 1
        self.form.faceSelectWidget.setVisible(is_cell_zone)

    def _toMS(self, widget, field_name):
        try:
            return Units.Quantity(getQuantity(widget)).getValueAs('m/s')
        except Exception:
            raise ValueError("{} must be a valid velocity".format(field_name))

    def accept(self):
        try:
            direction = FreeCAD.Vector(
                self.form.inputDirectionX.property("quantity").Value,
                self.form.inputDirectionY.property("quantity").Value,
                self.form.inputDirectionZ.property("quantity").Value)
            ubar = FreeCAD.Vector(
                self._toMS(self.form.inputUbarX, 'Ubar X'),
                self._toMS(self.form.inputUbarY, 'Ubar Y'),
                self._toMS(self.form.inputUbarZ, 'Ubar Z'))
            relaxation = self.form.inputRelaxation.property("quantity").Value
        except ValueError as err:
            CfdTools.cfdErrorBox(str(err))
            return

        mode = SELECTION_MODE_LABELS[self.form.comboSelectionMode.currentIndex()]
        if mode == 'cellZone' and not self.obj.ShapeRefs:
            CfdTools.cfdErrorBox("Please select at least one solid for the cell zone.")
            return

        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()

        storeIfChanged(self.obj, 'SelectionMode', mode)
        storeIfChanged(self.obj, 'Direction', direction)
        storeIfChanged(self.obj, 'Ubar', ubar)
        storeIfChanged(self.obj, 'Relaxation', relaxation)
        # ShapeRefs is modified in-place by CfdFaceSelectWidget — no explicit store needed

        FreeCADGui.doCommand("FreeCAD.ActiveDocument.recompute()")

    def reject(self):
        self.obj.ShapeRefs = self.ShapeRefsOrig
        self.analysis_obj.NeedsCaseRewrite = self.NeedsCaseRewriteOrig
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()

    def closing(self):
        FreeCADGui.Selection.removeObserver(self.faceSelector)
