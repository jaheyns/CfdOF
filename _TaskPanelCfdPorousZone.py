# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2013-2015 - Juergen Riegel <FreeCAD@juergen-riegel.net> *
# *   Copyright (c) 2017 - Alfred Bogaers (CSIR) <abogaers@csir.co.za>      *
# *   Copyright (c) 2017 - Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>        *
# *   Copyright (c) 2017 - Johan Heyns (CSIR) <jheyns@csir.co.za>           *
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

__title__ = "_TaskPanelCfdPorousZone"
__author__ = "AB, OO, JH"
__url__ = "http://www.freecadweb.org"

import FreeCAD
import os
import sys
import os.path
import Part
import CfdTools

if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore
    from PySide import QtCore
    from PySide import QtGui
    from PySide.QtCore import Qt
    from PySide.QtGui import QApplication
    import FemGui

POROUS_CORRELATIONS = ['DarcyForchheimer', 'Jakob']
POROUS_CORRELATION_NAMES = ["Darcy-Forchheimer coefficients", "Staggered tube bundle (Jakob)"]
POROUS_CORRELATION_TIPS = ["Specify viscous and inertial drag tensors by giving their principal components and directions (these will be made orthogonal)",
                           "Specify geometry of parallel tube bundle with staggered layers."]

ASPECT_RATIOS = ["1.0", "1.73", "1.0"]
ASPECT_RATIO_NAMES = ["User defined", "Equilateral", "Rotated square"]
ASPECT_RATIO_TIPS = ["", "Equilateral triangles pointing perpendicular to spacing direction", "45 degree angles; isotropic"]


class _TaskPanelCfdPorousZone:
    """ Task panel for porous zone objects """
    def __init__(self, obj):
        FreeCADGui.Selection.clearSelection()
        self.sel_server = None
        #obj.addProperty("Part::PropertyPartShape","Shape","Something")
        self.obj = obj
        self.shapeListOrig = list(self.obj.shapeList)
        self.partNameList = list(self.obj.partNameList)
        self.p = self.obj.porousZoneProperties

        self.form = FreeCADGui.PySideUic.loadUi(os.path.join(os.path.dirname(__file__), "TaskPanelPorousZone.ui"))

        self.form.selectReference.clicked.connect(self.selectReference)
        self.form.listWidget.itemPressed.connect(self.setSelection)
        self.form.pushButtonDelete.clicked.connect(self.deleteFeature)

        self.form.comboBoxCorrelation.currentIndexChanged.connect(self.comboBoxCorrelationChanged)

        self.form.e1x.textEdited.connect(self.e1Changed)
        self.form.e1y.textEdited.connect(self.e1Changed)
        self.form.e1z.textEdited.connect(self.e1Changed)
        self.form.e2x.textEdited.connect(self.e2Changed)
        self.form.e2y.textEdited.connect(self.e2Changed)
        self.form.e2z.textEdited.connect(self.e2Changed)
        self.form.e3x.textEdited.connect(self.e3Changed)
        self.form.e3y.textEdited.connect(self.e3Changed)
        self.form.e3z.textEdited.connect(self.e3Changed)
        self.form.e1x.editingFinished.connect(self.e1Done)
        self.form.e1y.editingFinished.connect(self.e1Done)
        self.form.e1z.editingFinished.connect(self.e1Done)
        self.form.e2x.editingFinished.connect(self.e2Done)
        self.form.e2y.editingFinished.connect(self.e2Done)
        self.form.e2z.editingFinished.connect(self.e2Done)
        self.form.e3x.editingFinished.connect(self.e3Done)
        self.form.e3y.editingFinished.connect(self.e3Done)
        self.form.e3z.editingFinished.connect(self.e3Done)
        self.lastEVectorChanged = 1
        self.lastLastEVectorChanged = 2

        self.form.comboAspectRatio.currentIndexChanged.connect(self.comboAspectRatioChanged)

        self.form.pushButtonDelete.setEnabled(False)

        self.form.comboBoxCorrelation.addItems(POROUS_CORRELATION_NAMES)
        self.form.comboAspectRatio.addItems(ASPECT_RATIO_NAMES)

        self.setInitialValues()

    def setInitialValues(self):
        for i in range(len(self.obj.partNameList)):
            self.form.listWidget.addItem(str(self.obj.partNameList[i]))

        try:
            self.form.comboBoxCorrelation.setCurrentIndex(
                POROUS_CORRELATIONS.index(CfdTools.getOrDefault(self.p, 'PorousCorrelation', POROUS_CORRELATIONS[0])))
        except ValueError:
            self.form.comboBoxCorrelation.setCurrentIndex(0)
        d = CfdTools.getOrDefault(self.p, 'D', [0, 0, 0])
        self.form.dx.setText("{}".format(d[0]))
        self.form.dy.setText("{}".format(d[1]))
        self.form.dz.setText("{}".format(d[2]))
        f = CfdTools.getOrDefault(self.p, 'F', [0, 0, 0])
        self.form.fx.setText("{}".format(f[0]))
        self.form.fy.setText("{}".format(f[1]))
        self.form.fz.setText("{}".format(f[2]))
        e1 = CfdTools.getOrDefault(self.p, 'e1', [1, 0, 0])
        self.form.e1x.setText("{}".format(e1[0]))
        self.form.e1y.setText("{}".format(e1[1]))
        self.form.e1z.setText("{}".format(e1[2]))
        e2 = CfdTools.getOrDefault(self.p, 'e2', [0, 1, 0])
        self.form.e2x.setText("{}".format(e2[0]))
        self.form.e2y.setText("{}".format(e2[1]))
        self.form.e2z.setText("{}".format(e2[2]))
        e3 = CfdTools.getOrDefault(self.p, 'e3', [0, 0, 1])
        self.form.e3x.setText("{}".format(e3[0]))
        self.form.e3y.setText("{}".format(e3[1]))
        self.form.e3z.setText("{}".format(e3[2]))
        self.form.inputOuterDiameter.setText("{} mm".format(CfdTools.getOrDefault(self.p, 'OuterDiameter', 0)*1000))
        tubeAxis = CfdTools.getOrDefault(self.p, 'TubeAxis', [0, 0, 1])
        self.form.inputTubeAxisX.setText("{}".format(tubeAxis[0]))
        self.form.inputTubeAxisY.setText("{}".format(tubeAxis[1]))
        self.form.inputTubeAxisZ.setText("{}".format(tubeAxis[2]))
        self.form.inputTubeSpacing.setText("{} mm".format(CfdTools.getOrDefault(self.p, 'TubeSpacing', 0)*1000))
        normalAxis = CfdTools.getOrDefault(self.p, 'SpacingDirection', [1, 0, 0])
        self.form.inputBundleLayerNormalX.setText("{}".format(normalAxis[0]))
        self.form.inputBundleLayerNormalY.setText("{}".format(normalAxis[1]))
        self.form.inputBundleLayerNormalZ.setText("{}".format(normalAxis[2]))
        self.form.inputAspectRatio.setText("{}".format(CfdTools.getOrDefault(self.p, 'AspectRatio', 1.73)))
        self.form.inputVelocityEstimate.setText("{} m/s".format(CfdTools.getOrDefault(self.p, 'VelocityEstimate', 0)))

    def deleteFeature(self):
        shapeList = list(self.obj.shapeList)
        currentItem = self.form.listWidget.currentItem()
        row = self.form.listWidget.row(currentItem)
        self.form.listWidget.takeItem(row)
        shapeList.pop(row)
        self.partNameList.pop(row)
        self.obj.shapeList = shapeList
        #self.obj.partNameList = partNameList
        FreeCADGui.doCommand("App.activeDocument().recompute()")
        FreeCADGui.Selection.clearSelection()
        self.form.pushButtonDelete.setEnabled(False)

    def setSelection(self, value):
        FreeCADGui.Selection.clearSelection()
        FreeCADGui.Selection.addSelection(self.obj.shapeList[self.form.listWidget.row(value)])
        self.form.pushButtonDelete.setEnabled(True)

    def selectReference(self):
        selection = FreeCADGui.Selection.getSelectionEx()
        """
            NOTE: to access the subElement (eg face which was selected) it would be selection[i].Object.SubElementNames
            Access to the actual shapes such as solids, faces, edges etc s[i].Object.Shape.Faces/Edges/Solids
        """
        shapeList = list(self.obj.shapeList)
        for sel in selection:
                if len(sel.Object.Shape.Solids) > 0:
                    if not(sel.Object.Name in self.partNameList):
                        self.form.listWidget.addItem(str(sel.Object.Name))
                        shapeList.append(sel.Object)
                        self.partNameList.append(sel.Object.Name)
        self.obj.shapeList = shapeList
        FreeCADGui.doCommand("App.activeDocument().recompute()")

    def comboBoxCorrelationChanged(self):
        self.updateCorrelationUI()

    def updateCorrelationUI(self):
        method = self.form.comboBoxCorrelation.currentIndex()
        self.form.stackedWidgetCorrelation.setCurrentIndex(method)
        self.form.comboBoxCorrelation.setToolTip(POROUS_CORRELATION_TIPS[method])

    # One of the e vector edit boxes loses focus
    def e1Done(self):
        if not (self.form.e1x.hasFocus() or self.form.e1y.hasFocus() or self.form.e1z.hasFocus()):
            self.eDone(0)

    def e2Done(self):
        if not (self.form.e2x.hasFocus() or self.form.e2y.hasFocus() or self.form.e2z.hasFocus()):
            self.eDone(1)

    def e3Done(self):
        if not (self.form.e3x.hasFocus() or self.form.e3y.hasFocus() or self.form.e3z.hasFocus()):
            self.eDone(2)

    # Value of one of the e vector edit boxes changed
    def e1Changed(self):
        self.eChanged(0)

    def e2Changed(self):
        self.eChanged(1)

    def e3Changed(self):
        self.eChanged(2)

    def eChanged(self, index):
        if index != self.lastEVectorChanged:
            self.lastLastEVectorChanged = self.lastEVectorChanged
            self.lastEVectorChanged = index

    def eDone(self, index):
        e = [[float(self.form.e1x.text()), float(self.form.e1y.text()), float(self.form.e1z.text())],
             [float(self.form.e2x.text()), float(self.form.e2y.text()), float(self.form.e2z.text())],
             [float(self.form.e3x.text()), float(self.form.e3y.text()), float(self.form.e3z.text())]]
        import CfdTools
        for i in range(3):
            e[i] = CfdTools.normalise(e[i])

        # Keep this one fixed. Make the other two orthogonal. The previous one edited gets to stay in its plane; the
        # one edited longest ago just gets recomputed
        if self.lastEVectorChanged == index:
            prevIndex = self.lastLastEVectorChanged
        else:
            prevIndex = self.lastEVectorChanged
        indexplus = (index + 1) % 3
        indexminus = (index - 1) % 3
        import numpy
        if indexplus == prevIndex:  # indexminus must be the one changed longest ago
            e[indexminus] = numpy.cross(e[index], e[indexplus])
            e[indexplus] = numpy.cross(e[indexminus], e[index])
        else:
            e[indexplus] = numpy.cross(e[indexminus], e[index])
            e[indexminus] = numpy.cross(e[index], e[indexplus])
        e[indexplus] = CfdTools.normalise(e[indexplus])
        e[indexminus] = CfdTools.normalise(e[indexminus])

        self.form.e1x.setText("{:.2f}".format(e[0][0]))
        self.form.e1y.setText("{:.2f}".format(e[0][1]))
        self.form.e1z.setText("{:.2f}".format(e[0][2]))
        self.form.e2x.setText("{:.2f}".format(e[1][0]))
        self.form.e2y.setText("{:.2f}".format(e[1][1]))
        self.form.e2z.setText("{:.2f}".format(e[1][2]))
        self.form.e3x.setText("{:.2f}".format(e[2][0]))
        self.form.e3y.setText("{:.2f}".format(e[2][1]))
        self.form.e3z.setText("{:.2f}".format(e[2][2]))

    def comboAspectRatioChanged(self):
        i = self.form.comboAspectRatio.currentIndex()
        self.form.inputAspectRatio.setText(ASPECT_RATIOS[i])
        self.form.comboAspectRatio.setToolTip(ASPECT_RATIO_TIPS[i])

    def accept(self):
        try:
            self.p['PorousCorrelation'] = POROUS_CORRELATIONS[self.form.comboBoxCorrelation.currentIndex()]
            self.p['D'] = [float(FreeCAD.Units.Quantity(self.form.dx.text())),
                           float(FreeCAD.Units.Quantity(self.form.dy.text())),
                           float(FreeCAD.Units.Quantity(self.form.dz.text()))]
            self.p['F'] = [float(FreeCAD.Units.Quantity(self.form.fx.text())),
                           float(FreeCAD.Units.Quantity(self.form.fy.text())),
                           float(FreeCAD.Units.Quantity(self.form.fz.text()))]
            self.p['e1'] = [float(FreeCAD.Units.Quantity(self.form.e1x.text())),
                            float(FreeCAD.Units.Quantity(self.form.e1y.text())),
                            float(FreeCAD.Units.Quantity(self.form.e1z.text()))]
            self.p['e2'] = [float(FreeCAD.Units.Quantity(self.form.e2x.text())),
                            float(FreeCAD.Units.Quantity(self.form.e2y.text())),
                            float(FreeCAD.Units.Quantity(self.form.e2z.text()))]
            self.p['e3'] = [float(FreeCAD.Units.Quantity(self.form.e3x.text())),
                            float(FreeCAD.Units.Quantity(self.form.e3y.text())),
                            float(FreeCAD.Units.Quantity(self.form.e3z.text()))]
            self.p['OuterDiameter'] = float(FreeCAD.Units.Quantity(self.form.inputOuterDiameter.text()).getValueAs('m'))
            self.p['TubeAxis'] = [float(FreeCAD.Units.Quantity(self.form.inputTubeAxisX.text())),
                                  float(FreeCAD.Units.Quantity(self.form.inputTubeAxisY.text())),
                                  float(FreeCAD.Units.Quantity(self.form.inputTubeAxisZ.text()))]
            self.p['TubeSpacing'] = float(FreeCAD.Units.Quantity(self.form.inputTubeSpacing.text()).getValueAs('m'))
            self.p['SpacingDirection'] = \
                [float(FreeCAD.Units.Quantity(self.form.inputBundleLayerNormalX.text())),
                 float(FreeCAD.Units.Quantity(self.form.inputBundleLayerNormalY.text())),
                 float(FreeCAD.Units.Quantity(self.form.inputBundleLayerNormalZ.text()))]
            self.p['AspectRatio'] = float(FreeCAD.Units.Quantity(self.form.inputAspectRatio.text()))
            self.p['VelocityEstimate'] = \
                float(FreeCAD.Units.Quantity(self.form.inputVelocityEstimate.text()).getValueAs('m/s'))
        except ValueError:
            FreeCAD.Console.PrintError("Unrecognised value entered\n")
            return
        self.obj.porousZoneProperties = self.p
        self.obj.partNameList = self.partNameList
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()

    def reject(self):
        self.obj.shapeList = self.shapeListOrig
        FreeCADGui.doCommand("App.activeDocument().recompute()")
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()
