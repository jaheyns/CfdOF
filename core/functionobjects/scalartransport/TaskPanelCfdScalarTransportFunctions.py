# ***************************************************************************
# *                                                                         *
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
import os
import os.path
import CfdTools
from CfdTools import getQuantity, setQuantity
if FreeCAD.GuiUp:
    import FreeCADGui


class TaskPanelCfdScalarTransportFunctions:
    """
    Task panel for adding solver scalar transport function objects
    """
    def __init__(self, obj):
        self.obj = obj
        self.analysis_obj = CfdTools.getActiveAnalysis()

        ui_path = os.path.join(os.path.dirname(__file__), "../../gui/TaskPanelCfdScalarTransportFunctions.ui")
        self.form = FreeCADGui.PySideUic.loadUi(ui_path)

        self.load()
        self.updateUI()

    def load(self):
        self.form.inputScalarFieldName.setText(self.obj.FieldName)
        self.form.inputFluxFieldName.setText(self.obj.FluxFieldName)
        self.form.inputDensityFieldName.setText(self.obj.DensityFieldName)
        self.form.inputPhaseFieldName.setText(self.obj.PhaseFieldName)
        self.form.cb_resetonstartup.setChecked(self.obj.ResetOnStartup)
        self.form.inputSchemeFieldName.setText(self.obj.SchemeFieldName)
        setQuantity(self.form.inputDiffusivityFixed, self.obj.DiffusivityFixedValue)
        self.form.inputDiffusivityField.setText(self.obj.DiffusivityFieldName)

    def updateUI(self):
        pass

    def accept(self):
        FreeCADGui.Selection.removeObserver(self)

        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()

        FreeCADGui.doCommand("\nfo = FreeCAD.ActiveDocument.{}".format(self.obj.Name))
        # Type
        FreeCADGui.doCommand("fo.FieldName "
                             "= '{}'".format(self.form.inputScalarFieldName.text()))
        FreeCADGui.doCommand("fo.FluxFieldName "
                             "= '{}'".format(self.form.inputFluxFieldName.text()))
        FreeCADGui.doCommand("fo.DensityFieldName "
                             "= '{}'".format(self.form.inputDensityFieldName.text()))
        FreeCADGui.doCommand("fo.PhaseFieldName "
                             "= '{}'".format(self.form.inputPhaseFieldName.text()))
        FreeCADGui.doCommand("fo.SchemeFieldName "
                             "= '{}'".format(self.form.inputSchemeFieldName.text()))
        FreeCADGui.doCommand("fo.DiffusivityFixedValue "
                             "= '{}'".format(getQuantity(self.form.inputDiffusivityFixed)))
        FreeCADGui.doCommand("fo.DiffusivityFieldName "
                             "= '{}'".format(self.form.inputDiffusivityField.text()))
        FreeCADGui.doCommand("fo.ResetOnStartup "
                             "= {}".format(self.form.cb_resetonstartup.isChecked()))

        # Finalise
        FreeCADGui.doCommand("FreeCAD.ActiveDocument.recompute()")

    def reject(self):
        FreeCADGui.Selection.removeObserver(self)
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc_name = str(self.obj.Document.Name)
        FreeCAD.getDocument(doc_name).recompute()
        doc.resetEdit()
        return True
