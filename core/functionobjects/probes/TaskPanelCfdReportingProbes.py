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
import CfdTools
import os
from CfdTools import setQuantity
if FreeCAD.GuiUp:
    import FreeCADGui


class TaskPanelCfdReportingProbes:

    def __init__(self, obj):
        self.obj = obj
        self.analysis_obj = CfdTools.getActiveAnalysis()

        ui_path = os.path.join(os.path.dirname(__file__), "../../gui/TaskPanelCfdReportingProbes.ui")
        self.form = FreeCADGui.PySideUic.loadUi(ui_path)

        self.load()
        self.updateUI()
        
    def load(self):
        self.form.inputFieldName.setText(self.obj.FieldName)
        setQuantity(self.form.inputProbeLocx, self.obj.ProbePosition.x)
        setQuantity(self.form.inputProbeLocy, self.obj.ProbePosition.y)
        setQuantity(self.form.inputProbeLocz, self.obj.ProbePosition.z)

    def updateUI(self):
        pass

    def accept(self):
        FreeCADGui.Selection.removeObserver(self)

        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()

        FreeCADGui.doCommand("\nfo = FreeCAD.ActiveDocument.{}".format(self.obj.Name))

        # Probe info
        FreeCADGui.doCommand("fo.FieldName "
                             "= '{}'".format(self.form.inputFieldName.text()))
        FreeCADGui.doCommand("fo.ProbePosition.x "
                             "= '{}'".format(self.form.inputProbeLocx.property("quantity").getValueAs("m")))
        FreeCADGui.doCommand("fo.ProbePosition.y "
                             "= '{}'".format(self.form.inputProbeLocy.property("quantity").getValueAs("m")))
        FreeCADGui.doCommand("fo.ProbePosition.z "
                             "= '{}'".format(self.form.inputProbeLocz.property("quantity").getValueAs("m")))

        # Finalise
        FreeCADGui.doCommand("FreeCAD.ActiveDocument.recompute()")

    def reject(self):
        FreeCADGui.Selection.removeObserver(self)
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc_name = str(self.obj.Document.Name)
        FreeCAD.getDocument(doc_name).recompute()
        doc.resetEdit()
        return True
