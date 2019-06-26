# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2013-2015 - Juergen Riegel <FreeCAD@juergen-riegel.net> *
# *   Copyright (c) 2017 Alfred Bogaers (CSIR) <abogaers@csir.co.za>        *
# *   Copyright (c) 2017 Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>          *
# *   Copyright (c) 2017 Johan Heyns (CSIR) <jheyns@csir.co.za>             *
# *   Copyright (c) 2019 Oliver Oxtoby <oliveroxtoby@gmail.com>             *
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
from CfdTools import getQuantity, setQuantity, indexOrDefault
import numpy
import CfdZone
import CfdFaceSelectWidget
if FreeCAD.GuiUp:
    import FreeCADGui


class _TaskPanelCfdZone:
    """ Task panel for zone objects """
    def __init__(self, obj):
        FreeCADGui.Selection.clearSelection()
        self.sel_server = None
        self.obj = obj

        self.ReferencesOrig = list(self.obj.References)

        self.form = FreeCADGui.PySideUic.loadUi(os.path.join(os.path.dirname(__file__), "TaskPanelCfdZone.ui"))

        self.form.framePorousZone.setVisible(False)
        self.form.frameInitialisationZone.setVisible(False)

        self.alphas = {}

        if self.obj.Name.startswith('PorousZone'):
            self.form.framePorousZone.setVisible(True)

            self.form.comboBoxCorrelation.currentIndexChanged.connect(self.updateUI)

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

            self.form.comboBoxCorrelation.addItems(CfdZone.POROUS_CORRELATION_NAMES)
            self.form.comboAspectRatio.addItems(CfdZone.ASPECT_RATIO_NAMES)

        elif self.obj.Name.startswith('InitialisationZone'):
            self.form.frameInitialisationZone.setVisible(True)

            self.form.comboFluid.currentIndexChanged.connect(self.comboFluidChanged)
            self.form.checkAlpha.stateChanged.connect(self.updateUI)
            self.form.checkVelocity.stateChanged.connect(self.updateUI)
            self.form.checkPressure.stateChanged.connect(self.updateUI)
            self.form.inputVolumeFraction.valueChanged.connect(self.inputVolumeFractionChanged)

            material_objs = CfdTools.getMaterials(CfdTools.getParentAnalysisObject(obj))
            self.form.frameVolumeFraction.setVisible(len(material_objs) > 1)
            if len(material_objs) > 1:
                fluid_names = [m.Label for m in material_objs]
                self.form.comboFluid.addItems(fluid_names[:-1])

        self.load()
        self.comboFluidChanged()
        self.updateUI()

        # Face list selection panel - modifies obj.References passed to it
        self.faceSelector = CfdFaceSelectWidget.CfdFaceSelectWidget(self.form.faceSelectWidget,
                                                                    self.obj, False, True)

    def load(self):
        if self.obj.Name.startswith('PorousZone'):
            ci = indexOrDefault(CfdZone.POROUS_CORRELATIONS, self.obj.PorousCorrelation, 0)
            self.form.comboBoxCorrelation.setCurrentIndex(ci)
            setQuantity(self.form.dx, self.obj.D1)
            setQuantity(self.form.dy, self.obj.D2)
            setQuantity(self.form.dz, self.obj.D3)
            setQuantity(self.form.fx, self.obj.F1)
            setQuantity(self.form.fy, self.obj.F2)
            setQuantity(self.form.fz, self.obj.F3)
            e1 = self.obj.e1
            setQuantity(self.form.e1x, str(e1[0]))
            setQuantity(self.form.e1y, str(e1[1]))
            setQuantity(self.form.e1z, str(e1[2]))
            e2 = self.obj.e2
            setQuantity(self.form.e2x, str(e2[0]))
            setQuantity(self.form.e2y, str(e2[1]))
            setQuantity(self.form.e2z, str(e2[2]))
            e3 = self.obj.e3
            setQuantity(self.form.e3x, str(e3[0]))
            setQuantity(self.form.e3y, str(e3[1]))
            setQuantity(self.form.e3z, str(e3[2]))
            setQuantity(self.form.inputOuterDiameter, self.obj.OuterDiameter)
            tubeAxis = self.obj.TubeAxis
            setQuantity(self.form.inputTubeAxisX, str(tubeAxis[0]))
            setQuantity(self.form.inputTubeAxisY, str(tubeAxis[1]))
            setQuantity(self.form.inputTubeAxisZ, str(tubeAxis[2]))
            setQuantity(self.form.inputTubeSpacing, self.obj.TubeSpacing)
            normalAxis = self.obj.SpacingDirection
            setQuantity(self.form.inputBundleLayerNormalX, str(normalAxis[0]))
            setQuantity(self.form.inputBundleLayerNormalY, str(normalAxis[1]))
            setQuantity(self.form.inputBundleLayerNormalZ, str(normalAxis[2]))
            setQuantity(self.form.inputAspectRatio, self.obj.AspectRatio)
            setQuantity(self.form.inputVelocityEstimate, self.obj.VelocityEstimate)

        elif self.obj.Name.startswith('InitialisationZone'):
            self.form.checkVelocity.setChecked(self.obj.VelocitySpecified)
            setQuantity(self.form.inputUx, self.obj.Ux)
            setQuantity(self.form.inputUy, self.obj.Uy)
            setQuantity(self.form.inputUz, self.obj.Uz)
            self.form.checkPressure.setChecked(self.obj.PressureSpecified)
            setQuantity(self.form.inputPressure, self.obj.Pressure)
            self.form.checkAlpha.setChecked(self.obj.VolumeFractionSpecified)
            self.alphas = self.obj.VolumeFractions

    def updateUI(self):
        method = self.form.comboBoxCorrelation.currentIndex()
        self.form.frameDarcyForchheimer.setVisible(CfdZone.POROUS_CORRELATIONS[method] == 'DarcyForchheimer')
        self.form.frameJakob.setVisible(CfdZone.POROUS_CORRELATIONS[method] == 'Jakob')
        self.form.comboBoxCorrelation.setToolTip(CfdZone.POROUS_CORRELATION_TIPS[method])

        velo_checked = self.form.checkVelocity.isChecked()
        self.form.inputUx.setEnabled(velo_checked)
        self.form.inputUy.setEnabled(velo_checked)
        self.form.inputUz.setEnabled(velo_checked)
        self.form.inputPressure.setEnabled(self.form.checkPressure.isChecked())
        self.form.inputVolumeFraction.setEnabled(self.form.checkAlpha.isChecked())
        self.form.comboFluid.setEnabled(self.form.checkAlpha.isChecked())

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
        if indexplus == prevIndex:  # indexminus must be the one changed longest ago
            e[indexminus] = numpy.cross(e[index], e[indexplus])
            e[indexplus] = numpy.cross(e[indexminus], e[index])
        else:
            e[indexplus] = numpy.cross(e[indexminus], e[index])
            e[indexminus] = numpy.cross(e[index], e[indexplus])
        e[indexplus] = CfdTools.normalise(e[indexplus])
        e[indexminus] = CfdTools.normalise(e[indexminus])

        setQuantity(self.form.e1x, str(e[0][0]))
        setQuantity(self.form.e1y, str(e[0][1]))
        setQuantity(self.form.e1z, str(e[0][2]))
        setQuantity(self.form.e2x, str(e[1][0]))
        setQuantity(self.form.e2y, str(e[1][1]))
        setQuantity(self.form.e2z, str(e[1][2]))
        setQuantity(self.form.e3x, str(e[2][0]))
        setQuantity(self.form.e3y, str(e[2][1]))
        setQuantity(self.form.e3z, str(e[2][2]))

    def comboAspectRatioChanged(self):
        i = self.form.comboAspectRatio.currentIndex()
        setQuantity(self.form.inputAspectRatio, CfdZone.ASPECT_RATIOS[i])
        self.form.comboAspectRatio.setToolTip(CfdZone.ASPECT_RATIO_TIPS[i])

    def comboFluidChanged(self):
        alphaName = self.form.comboFluid.currentText()
        if alphaName in self.alphas:
            setQuantity(self.form.inputVolumeFraction, self.alphas.get(alphaName, 0.0))

    def inputVolumeFractionChanged(self, text):
        alphaName = self.form.comboFluid.currentText()
        self.alphas[alphaName] = getQuantity(self.form.inputVolumeFraction)

    def accept(self):
        if self.obj.Name.startswith('PorousZone'):
            FreeCADGui.doCommand("p = FreeCAD.ActiveDocument.{}".format(self.obj.Name))
            FreeCADGui.doCommand("p.PorousCorrelation = '{}'".format(
                CfdZone.POROUS_CORRELATIONS[self.form.comboBoxCorrelation.currentIndex()]))
            FreeCADGui.doCommand("p.D1 = '{}'".format(getQuantity(self.form.dx)))
            FreeCADGui.doCommand("p.D2 = '{}'".format(getQuantity(self.form.dy)))
            FreeCADGui.doCommand("p.D3 = '{}'".format(getQuantity(self.form.dz)))
            FreeCADGui.doCommand("p.F1 = '{}'".format(getQuantity(self.form.fx)))
            FreeCADGui.doCommand("p.F2 = '{}'".format(getQuantity(self.form.fy)))
            FreeCADGui.doCommand("p.F3 = '{}'".format(getQuantity(self.form.fz)))
            FreeCADGui.doCommand("p.e1 = ({}, {}, {})".format(
                self.form.e1x.property('quantity').getValueAs("1").Value,
                self.form.e1y.property('quantity').getValueAs("1").Value,
                self.form.e1z.property('quantity').getValueAs("1").Value))
            FreeCADGui.doCommand("p.e2 = ({}, {}, {})".format(
                self.form.e2x.property('quantity').getValueAs("1").Value,
                self.form.e2y.property('quantity').getValueAs("1").Value,
                self.form.e2z.property('quantity').getValueAs("1").Value))
            FreeCADGui.doCommand("p.e3 = ({}, {}, {})".format(
                self.form.e3x.property('quantity').getValueAs("1").Value,
                self.form.e3y.property('quantity').getValueAs("1").Value,
                self.form.e3z.property('quantity').getValueAs("1").Value))
            FreeCADGui.doCommand("p.OuterDiameter = '{}'".format(getQuantity(self.form.inputOuterDiameter)))
            FreeCADGui.doCommand("p.TubeAxis = ({}, {}, {} )".format(
                self.form.inputTubeAxisX.property('quantity').getValueAs("1").Value,
                self.form.inputTubeAxisY.property('quantity').getValueAs("1").Value,
                self.form.inputTubeAxisZ.property('quantity').getValueAs("1").Value))
            FreeCADGui.doCommand("p.TubeSpacing = '{}'".format(getQuantity(self.form.inputTubeSpacing)))
            FreeCADGui.doCommand("p.SpacingDirection = ({}, {}, {})".format(
                self.form.inputBundleLayerNormalX.property('quantity').getValueAs("1").Value,
                self.form.inputBundleLayerNormalY.property('quantity').getValueAs("1").Value,
                self.form.inputBundleLayerNormalZ.property('quantity').getValueAs("1").Value))
            FreeCADGui.doCommand("p.AspectRatio = '{}'".format(getQuantity(self.form.inputAspectRatio)))
            FreeCADGui.doCommand("p.VelocityEstimate = '{}'".format(getQuantity(self.form.inputVelocityEstimate)))

        elif self.obj.Name.startswith('InitialisationZone'):
            FreeCADGui.doCommand("p = FreeCAD.ActiveDocument.{}".format(self.obj.Name))
            FreeCADGui.doCommand("p.VelocitySpecified = {}".format(self.form.checkVelocity.isChecked()))
            FreeCADGui.doCommand("p.Ux = '{}'".format(getQuantity(self.form.inputUx)))
            FreeCADGui.doCommand("p.Uy = '{}'".format(getQuantity(self.form.inputUy)))
            FreeCADGui.doCommand("p.Uz = '{}'".format(getQuantity(self.form.inputUz)))
            FreeCADGui.doCommand("p.PressureSpecified = {}".format(self.form.checkPressure.isChecked()))
            FreeCADGui.doCommand("p.Pressure = '{}'".format(getQuantity(self.form.inputPressure)))
            FreeCADGui.doCommand("p.VolumeFractionSpecified = {}".format(self.form.checkAlpha.isChecked()))
            FreeCADGui.doCommand("p.VolumeFractions = {}".format(self.alphas))

        FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.References = {}".format(self.obj.Name, self.obj.References))

        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()

    def reject(self):
        self.obj.References = self.ReferencesOrig
        FreeCADGui.doCommand("App.activeDocument().recompute()")
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()
