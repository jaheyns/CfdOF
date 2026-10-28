# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: © 2022 Jonathan Bergh <bergh.jonathan@gmail.com>
# SPDX-FileCopyrightText: © 2022 Oliver Oxtoby <oliveroxtoby@gmail.com>
# SPDX-FileNotice: Part of the CfdOF addon.

################################################################################
#                                                                              #
#   This program is free software; you can redistribute it and/or              #
#   modify it under the terms of the GNU Lesser General Public                 #
#   License as published by the Free Software Foundation; either               #
#   version 3 of the License, or (at your option) any later version.           #
#                                                                              #
#   This program is distributed in the hope that it will be useful,            #
#   but WITHOUT ANY WARRANTY; without even the implied warranty of             #
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.                       #
#                                                                              #
#   See the GNU Lesser General Public License for more details.                #
#                                                                              #
#   You should have received a copy of the GNU Lesser General Public License   #
#   along with this program; if not, write to the Free Software Foundation,    #
#   Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.        #
#                                                                              #
################################################################################

import os
import os.path
import FreeCAD
from FreeCAD import Units
from CfdOF import CfdTools
from CfdOF import CfdFaceSelectWidget
from CfdOF.CfdTools import getQuantity, setQuantity, storeIfChanged, indexOrDefault
from PySide6.QtWidgets import QTableWidgetItem
if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtGui


def getCellValue(row, colum, table):
        cell = table.item(row, colum)
        return(float(cell.text()))

class TaskPanelCfdMRF:
    """
    Task panel for adding multi-reference frame objects
    """
    def __init__(self, obj):
        self.obj = obj
        self.analysis_obj = CfdTools.getParentAnalysisObject(obj)

        self.ShapeRefsOrig = list(self.obj.ShapeRefs)
        self.NeedsCaseRewriteOrig = self.analysis_obj.NeedsCaseRewrite

        ui_path = os.path.join(CfdTools.getModulePath(), 'Gui', "TaskPanelCfdMRF.ui")
        self.form = FreeCADGui.PySideUic.loadUi(ui_path)

        self.form.faceSelectWidget.setLayout(QtGui.QVBoxLayout())
        self.faceSelector = CfdFaceSelectWidget.CfdFaceSelectWidget(
            self.form.faceSelectWidget, self.obj, False, False, True)
        
        self.load()

    def load(self):
        setQuantity(self.form.InputFieldAxisX, self.obj.Axis.x)
        setQuantity(self.form.InputFieldAxisY, self.obj.Axis.y)
        setQuantity(self.form.InputFieldAxisZ, self.obj.Axis.z)

        setQuantity(self.form.InputFieldCoRX, Units.Quantity(self.obj.CenterOfRotation.x, Units.Length))
        setQuantity(self.form.InputFieldCoRY, Units.Quantity(self.obj.CenterOfRotation.y, Units.Length))
        setQuantity(self.form.InputFieldCoRZ, Units.Quantity(self.obj.CenterOfRotation.z, Units.Length))

        setQuantity(self.form.InputFieldSpeed, self.obj.Speed)

    def accept(self):
        axis = FreeCAD.Vector(
            self.form.InputFieldAxisX.property("quantity").Value,
            self.form.InputFieldAxisY.property("quantity").Value,
            self.form.InputFieldAxisZ.property("quantity").Value)
        centre_of_rotation = FreeCAD.Vector(
            self.form.InputFieldCoRX.property("quantity").Value,
            self.form.InputFieldCoRY.property("quantity").Value,
            self.form.InputFieldCoRZ.property("quantity").Value)

        storeIfChanged(self.obj, 'Speed', self.form.InputFieldSpeed.text())
        storeIfChanged(self.obj, 'Axis', axis)
        storeIfChanged(self.obj, 'CenterOfRotation', centre_of_rotation)

        # Only update references if changed
        if self.obj.ShapeRefs != self.ShapeRefsOrig:
            refstr = "FreeCAD.ActiveDocument.{}.ShapeRefs = [\n".format(self.obj.Name)
            refstr += ',\n'.join(
                "(FreeCAD.ActiveDocument.getObject('{}'), {})".format(ref[0].Name, ref[1]) for ref in self.obj.ShapeRefs)
            refstr += "]"
            FreeCADGui.doCommand(refstr)

        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()

        # Finalise
        FreeCADGui.doCommand("FreeCAD.ActiveDocument.recompute()")

    def reject(self):
        self.obj.ShapeRefs = self.ShapeRefsOrig
        self.analysis_obj.NeedsCaseRewrite = self.NeedsCaseRewriteOrig
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()
