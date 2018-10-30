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
from CfdTools import inputCheckAndStore, setInputFieldQuantity, indexOrDefault

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


class _TaskPanelCfdZone:
    """ Task panel for zone objects """
    def __init__(self, obj):
        FreeCADGui.Selection.clearSelection()
        self.sel_server = None
        self.obj = obj
        self.shapeListOrig = list(self.obj.shapeList)
        self.partNameList = list(self.obj.partNameList)
        self.partNameListOrig = list(self.obj.partNameList)

        self.form = FreeCADGui.PySideUic.loadUi(os.path.join(os.path.dirname(__file__), "TaskPanelCfdZone.ui"))

        self.form.selectReference.clicked.connect(self.selectReference)
        self.form.listWidget.itemPressed.connect(self.setSelection)
        self.form.pushButtonDelete.clicked.connect(self.deleteFeature)

        if self.obj.Name.startswith('PorousZone'):
            self.p = dict(self.obj.porousZoneProperties)
            self.form.stackedWidgetZoneType.setCurrentIndex(0)

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

        elif self.obj.Name.startswith('InitialisationZone'):
            self.p = dict(self.obj.initialisationZoneProperties)
            self.form.stackedWidgetZoneType.setCurrentIndex(1)

            self.form.comboFluid.currentIndexChanged.connect(self.comboFluidChanged)
            self.form.checkAlpha.stateChanged.connect(self.checkAlphaChanged)
            self.form.checkVelocity.stateChanged.connect(self.checkVelocityChanged)
            self.form.checkPressure.stateChanged.connect(self.checkPressureChanged)
            self.form.inputVolumeFraction.valueChanged.connect(self.inputVolumeFractionChanged)
            self.form.inputUx.valueChanged.connect(self.inputUxChanged)
            self.form.inputUy.valueChanged.connect(self.inputUyChanged)
            self.form.inputUz.valueChanged.connect(self.inputUzChanged)
            self.form.inputPressure.valueChanged.connect(self.inputPressureChanged)

            material_objs = CfdTools.getMaterials(CfdTools.getParentAnalysisObject(obj))
            self.form.frameVolumeFraction.setVisible(len(material_objs) > 1)
            if len(material_objs) > 1:
                fluid_names = [m.Label for m in material_objs]
                self.form.comboFluid.addItems(fluid_names[:-1])

        self.setInitialValues()

    def setInitialValues(self):
        for i in range(len(self.obj.partNameList)):
            self.form.listWidget.addItem(str(self.obj.partNameList[i]))

        if self.obj.Name.startswith('PorousZone'):
            ci = indexOrDefault(POROUS_CORRELATIONS, self.p.get('PorousCorrelation'), 0)
            self.form.comboBoxCorrelation.setCurrentIndex(ci)
            d = self.p.get('D')
            setInputFieldQuantity(self.form.dx, "{} m^-2".format(d[0]))
            setInputFieldQuantity(self.form.dy, "{} m^-2".format(d[1]))
            setInputFieldQuantity(self.form.dz, "{} m^-2".format(d[2]))
            f = self.p.get('F')
            setInputFieldQuantity(self.form.fx, "{} m^-1".format(f[0]))
            setInputFieldQuantity(self.form.fy, "{} m^-1".format(f[1]))
            setInputFieldQuantity(self.form.fz, "{} m^-1".format(f[2]))
            e1 = self.p.get('e1')
            setInputFieldQuantity(self.form.e1x, str(e1[0]))
            setInputFieldQuantity(self.form.e1y, str(e1[1]))
            setInputFieldQuantity(self.form.e1z, str(e1[2]))
            e2 = self.p.get('e2')
            setInputFieldQuantity(self.form.e2x, str(e2[0]))
            setInputFieldQuantity(self.form.e2y, str(e2[1]))
            setInputFieldQuantity(self.form.e2z, str(e2[2]))
            e3 = self.p.get('e3')
            setInputFieldQuantity(self.form.e3x, str(e3[0]))
            setInputFieldQuantity(self.form.e3y, str(e3[1]))
            setInputFieldQuantity(self.form.e3z, str(e3[2]))
            setInputFieldQuantity(self.form.inputOuterDiameter, "{} m".format(self.p.get('OuterDiameter')))
            tubeAxis = self.p.get('TubeAxis')
            setInputFieldQuantity(self.form.inputTubeAxisX, str(tubeAxis[0]))
            setInputFieldQuantity(self.form.inputTubeAxisY, str(tubeAxis[1]))
            setInputFieldQuantity(self.form.inputTubeAxisZ, str(tubeAxis[2]))
            setInputFieldQuantity(self.form.inputTubeSpacing, "{} m".format(self.p.get('TubeSpacing')))
            normalAxis = self.p.get('SpacingDirection')
            setInputFieldQuantity(self.form.inputBundleLayerNormalX, str(normalAxis[0]))
            setInputFieldQuantity(self.form.inputBundleLayerNormalY, str(normalAxis[1]))
            setInputFieldQuantity(self.form.inputBundleLayerNormalZ, str(normalAxis[2]))
            setInputFieldQuantity(self.form.inputAspectRatio, str(self.p.get('AspectRatio')))
            setInputFieldQuantity(self.form.inputVelocityEstimate, "{} m/s".format(self.p.get('VelocityEstimate')))

        elif self.obj.Name.startswith('InitialisationZone'):
            if 'Ux' in self.p:
                setInputFieldQuantity(self.form.inputUx, "{} m/s".format(self.p.get('Ux')))
                setInputFieldQuantity(self.form.inputUy, "{} m/s".format(self.p.get('Uy')))
                setInputFieldQuantity(self.form.inputUz, "{} m/s".format(self.p.get('Uz')))
                self.form.checkVelocity.setChecked(True)
            if 'Pressure' in self.p:
                setInputFieldQuantity(self.form.inputPressure, "{} kg/m/s^2".format(self.p.get('Pressure')))
                self.form.checkPressure.setChecked(True)
            if 'alphas' in self.p:
                self.form.checkAlpha.setChecked(True)
            # Simulate initial signals to get into correct state
            self.checkVelocityChanged(self.form.checkVelocity.isChecked())
            self.checkPressureChanged(self.form.checkPressure.isChecked())
            self.checkAlphaChanged(self.form.checkAlpha.isChecked())

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
        #NOTE: to access the subElement (eg face which was selected) it would be selection[i].Object.SubElementNames
        #Access to the actual shapes such as solids, faces, edges etc s[i].Object.Shape.Faces/Edges/Solids
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
        e = [[self.form.e1x.property('quantity').getValueAs('1').Value,
              self.form.e1y.property('quantity').getValueAs('1').Value,
              self.form.e1z.property('quantity').getValueAs('1').Value],
             [self.form.e2x.property('quantity').getValueAs('1').Value,
              self.form.e2y.property('quantity').getValueAs('1').Value,
              self.form.e2z.property('quantity').getValueAs('1').Value],
             [self.form.e3x.property('quantity').getValueAs('1').Value,
              self.form.e3y.property('quantity').getValueAs('1').Value,
              self.form.e3z.property('quantity').getValueAs('1').Value]]
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

        setInputFieldQuantity(self.form.e1x, str(e[0][0]))
        setInputFieldQuantity(self.form.e1y, str(e[0][1]))
        setInputFieldQuantity(self.form.e1z, str(e[0][2]))
        setInputFieldQuantity(self.form.e2x, str(e[1][0]))
        setInputFieldQuantity(self.form.e2y, str(e[1][1]))
        setInputFieldQuantity(self.form.e2z, str(e[1][2]))
        setInputFieldQuantity(self.form.e3x, str(e[2][0]))
        setInputFieldQuantity(self.form.e3y, str(e[2][1]))
        setInputFieldQuantity(self.form.e3z, str(e[2][2]))

    def comboAspectRatioChanged(self):
        i = self.form.comboAspectRatio.currentIndex()
        setInputFieldQuantity(self.form.inputAspectRatio, ASPECT_RATIOS[i])
        self.form.comboAspectRatio.setToolTip(ASPECT_RATIO_TIPS[i])

    def checkAlphaChanged(self, checked):
        self.form.inputVolumeFraction.setEnabled(checked != 0)
        self.form.comboFluid.setEnabled(checked != 0)
        if not checked:
            self.p.pop('alphas', None)  # Delete if present
        else:
            if 'alphas' not in self.p:
                self.p['alphas'] = {}
            self.comboFluidChanged()

    def comboFluidChanged(self):
        alphaName = self.form.comboFluid.currentText()
        if 'alphas' in self.p:
            if alphaName in self.p['alphas']:
                setInputFieldQuantity(self.form.inputVolumeFraction, str(self.p['alphas'].get(alphaName, 0.0)))

    def checkVelocityChanged(self, checked):
        self.form.inputUx.setEnabled(checked != 0)
        self.form.inputUy.setEnabled(checked != 0)
        self.form.inputUz.setEnabled(checked != 0)
        if not checked:
            self.p.pop('Ux', None)
            self.p.pop('Uy', None)
            self.p.pop('Uz', None)
        else:
            # Store current text box values
            self.inputUxChanged(self.form.inputUx.text())
            self.inputUyChanged(self.form.inputUy.text())
            self.inputUzChanged(self.form.inputUz.text())

    def checkPressureChanged(self, checked):
        self.form.inputPressure.setEnabled(checked != 0)
        if not checked:
            self.p.pop('Pressure', None)
        else:
            # Store current text box value
            self.inputPressureChanged(self.form.inputPressure.text())

    def inputVolumeFractionChanged(self, text):
        alphaName = self.form.comboFluid.currentText()
        if 'alphas' in self.p:
            inputCheckAndStore(text, "m/m", self.p['alphas'], alphaName)

    def inputUxChanged(self, text):
        inputCheckAndStore(text, "m/s", self.p, 'Ux')

    def inputUyChanged(self, text):
        inputCheckAndStore(text, "m/s", self.p, 'Uy')

    def inputUzChanged(self, text):
        inputCheckAndStore(text, "m/s", self.p, 'Uz')

    def inputPressureChanged(self, text):
        inputCheckAndStore(text, "kg/m/s^2", self.p, 'Pressure')

    def accept(self):
        if self.obj.Name.startswith('PorousZone'):
            try:
                FreeCADGui.doCommand("p = FreeCAD.ActiveDocument.{}.porousZoneProperties".format(self.obj.Name))
                FreeCADGui.doCommand("p['PorousCorrelation'] = '{}'".format( POROUS_CORRELATIONS[self.form.comboBoxCorrelation.currentIndex()]))
                FreeCADGui.doCommand("p['D'] = [{},{},{}]".format( self.form.dx.property('quantity').getValueAs("m^-2").Value,
                                                                   self.form.dy.property('quantity').getValueAs("m^-2").Value,
                                                                   self.form.dz.property('quantity').getValueAs("m^-2").Value))
                FreeCADGui.doCommand("p['F'] = [{},{},{}]".format( self.form.fx.property('quantity').getValueAs("m^-1").Value,
                                                                   self.form.fy.property('quantity').getValueAs("m^-1").Value,
                                                                   self.form.fz.property('quantity').getValueAs("m^-1").Value))
                FreeCADGui.doCommand("p['e1'] = [{},{},{}]".format( self.form.e1x.property('quantity').getValueAs("1").Value,
                                                                    self.form.e1y.property('quantity').getValueAs("1").Value,
                                                                    self.form.e1z.property('quantity').getValueAs("1").Value))
                FreeCADGui.doCommand("p['e2'] = [{},{},{}]".format(self.form.e2x.property('quantity').getValueAs("1").Value,
                                                                    self.form.e2y.property('quantity').getValueAs("1").Value,
                                                                    self.form.e2z.property('quantity').getValueAs("1").Value))
                FreeCADGui.doCommand("p['e3'] = [{},{},{}]".format(self.form.e3x.property('quantity').getValueAs("1").Value,
                                                                    self.form.e3y.property('quantity').getValueAs("1").Value,
                                                                    self.form.e3z.property('quantity').getValueAs("1").Value))
                FreeCADGui.doCommand("p['OuterDiameter'] = {}".format(self.form.inputOuterDiameter.property('quantity').getValueAs('m').Value))
                FreeCADGui.doCommand("p['TubeAxis'] = [{},{},{}]".format(self.form.inputTubeAxisX.property('quantity').getValueAs("m/m").Value,
                                                                      self.form.inputTubeAxisY.property('quantity').getValueAs("m/m").Value,
                                                                      self.form.inputTubeAxisZ.property('quantity').getValueAs("m/m").Value))
                FreeCADGui.doCommand("p['TubeSpacing'] = {}".format(self.form.inputTubeSpacing.property('quantity').getValueAs('m').Value))
                FreeCADGui.doCommand("p['SpacingDirection'] = [{},{},{}]".format(self.form.inputBundleLayerNormalX.property('quantity').getValueAs("1").Value,
                                                                                     self.form.inputBundleLayerNormalY.property('quantity').getValueAs("1").Value,
                                                                                     self.form.inputBundleLayerNormalZ.property('quantity').getValueAs("1").Value))
                FreeCADGui.doCommand("p['AspectRatio'] = {}".format( self.form.inputAspectRatio.property('quantity').getValueAs("1").Value))
                FreeCADGui.doCommand("p['VelocityEstimate'] = {}".format(self.form.inputVelocityEstimate.property('quantity').getValueAs('m/s').Value))

            except ValueError:
                FreeCAD.Console.PrintError("Unrecognised value entered\n")
                return
            FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.porousZoneProperties = p".format(self.obj.Name))

        elif self.obj.Name.startswith('InitialisationZone'):
            FreeCADGui.doCommand("p = FreeCAD.ActiveDocument.{}.initialisationZoneProperties".format(self.obj.Name))
            FreeCADGui.doCommand("p = {}".format(self.p))
            FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.initialisationZoneProperties = p".format(self.obj.Name))
        FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.partNameList = {}".format(self.obj.Name, self.partNameList))
        FreeCADGui.doCommand("sl = []")
        for s in self.partNameList:
            FreeCADGui.doCommand("sl.append(FreeCAD.ActiveDocument.{})".format(s))
        FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.shapeList = sl".format(self.obj.Name))

        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()

    def reject(self):
        self.obj.shapeList = self.shapeListOrig
        self.obj.partNameList = self.partNameListOrig
        FreeCADGui.doCommand("App.activeDocument().recompute()")
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()
