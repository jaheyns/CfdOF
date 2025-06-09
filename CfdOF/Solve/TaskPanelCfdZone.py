# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2017 Alfred Bogaers (CSIR) <abogaers@csir.co.za>        *
# *   Copyright (c) 2017 Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>          *
# *   Copyright (c) 2017 Johan Heyns (CSIR) <jheyns@csir.co.za>             *
# *   Copyright (c) 2019-2024 Oliver Oxtoby <oliveroxtoby@gmail.com>        *
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

import os
import os.path
import numpy
import FreeCAD
if FreeCAD.GuiUp:
    import FreeCADGui
from CfdOF import CfdTools
from CfdOF.CfdTools import getQuantity, setQuantity, indexOrDefault, storeIfChanged
from CfdOF.Solve import CfdZone
from CfdOF import CfdFaceSelectWidget


class TaskPanelCfdZone:
    """ Task panel for zone objects """
    def __init__(self, obj):
        FreeCADGui.Selection.clearSelection()
        self.sel_server = None
        self.obj = obj
        self.analysis_obj = CfdTools.getParentAnalysisObject(obj)

        self.ShapeRefsOrig = list(self.obj.ShapeRefs)
        self.NeedsCaseRewriteOrig = self.analysis_obj.NeedsCaseRewrite

        self.form = FreeCADGui.PySideUic.loadUi(os.path.join(CfdTools.getModulePath(), 'Gui', "TaskPanelCfdZone.ui"))

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
            if hasattr(self.form.checkAlpha, "checkStateChanged"):
                self.form.checkAlpha.checkStateChanged.connect(self.updateUI)
                self.form.checkVelocity.checkStateChanged.connect(self.updateUI)
                self.form.checkPressure.checkStateChanged.connect(self.updateUI)
                self.form.checkTemperature.checkStateChanged.connect(self.updateUI)
            else:
                self.form.checkAlpha.stateChanged.connect(self.updateUI)
                self.form.checkVelocity.stateChanged.connect(self.updateUI)
                self.form.checkPressure.stateChanged.connect(self.updateUI)
                self.form.checkTemperature.stateChanged.connect(self.updateUI)
            self.form.inputVolumeFraction.valueChanged.connect(self.inputVolumeFractionChanged)

            material_objs = CfdTools.getMaterials(CfdTools.getParentAnalysisObject(obj))
            self.form.frameVolumeFraction.setVisible(len(material_objs) > 1)
            if len(material_objs) > 1:
                fluid_names = [m.Label for m in material_objs]
                self.form.comboFluid.addItems(fluid_names[:-1])

            physics_obj = CfdTools.getPhysicsModel(self.analysis_obj)
            self.form.frameTemperature.setVisible(physics_obj.Flow != 'Isothermal')

        self.load()
        self.comboFluidChanged()
        self.updateUI()

        # Face list selection panel - modifies obj.ShapeRefs passed to it
        self.faceSelector = CfdFaceSelectWidget.CfdFaceSelectWidget(self.form.faceSelectWidget,
                                                                    self.obj, False, False, True)

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
            self.form.checkTemperature.setChecked(self.obj.TemperatureSpecified)
            setQuantity(self.form.inputTemperature, self.obj.Temperature)
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
        self.form.inputTemperature.setEnabled(self.form.checkTemperature.isChecked())
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
        self.analysis_obj.NeedsCaseRewrite = self.NeedsCaseRewriteOrig

        if self.obj.Name.startswith('PorousZone'):
            storeIfChanged(self.obj, 'PorousCorrelation',
                CfdZone.POROUS_CORRELATIONS[self.form.comboBoxCorrelation.currentIndex()])
            storeIfChanged(self.obj, 'D1', getQuantity(self.form.dx))
            storeIfChanged(self.obj, 'D2', getQuantity(self.form.dy))
            storeIfChanged(self.obj, 'D3', getQuantity(self.form.dz))
            storeIfChanged(self.obj, 'F1', getQuantity(self.form.fx))
            storeIfChanged(self.obj, 'F2', getQuantity(self.form.fy))
            storeIfChanged(self.obj, 'F3', getQuantity(self.form.fz))
            e1 = FreeCAD.Vector(
                self.form.e1x.property('quantity').getValueAs("1").Value,
                self.form.e1y.property('quantity').getValueAs("1").Value,
                self.form.e1z.property('quantity').getValueAs("1").Value)
            e2 = FreeCAD.Vector(
                self.form.e2x.property('quantity').getValueAs("1").Value,
                self.form.e2y.property('quantity').getValueAs("1").Value,
                self.form.e2z.property('quantity').getValueAs("1").Value)
            e3 = FreeCAD.Vector(
                self.form.e3x.property('quantity').getValueAs("1").Value,
                self.form.e3y.property('quantity').getValueAs("1").Value,
                self.form.e3z.property('quantity').getValueAs("1").Value)
            storeIfChanged(self.obj, 'e1', e1)
            storeIfChanged(self.obj, 'e2', e2)
            storeIfChanged(self.obj, 'e3', e3)
            storeIfChanged(self.obj, 'OuterDiameter', getQuantity(self.form.inputOuterDiameter))
            tube_axis = FreeCAD.Vector(
                self.form.inputTubeAxisX.property('quantity').getValueAs("1").Value,
                self.form.inputTubeAxisY.property('quantity').getValueAs("1").Value,
                self.form.inputTubeAxisZ.property('quantity').getValueAs("1").Value)
            storeIfChanged(self.obj, 'TubeAxis', tube_axis)
            storeIfChanged(self.obj, 'TubeSpacing', getQuantity(self.form.inputTubeSpacing))
            spacing_direction = FreeCAD.Vector(
                self.form.inputBundleLayerNormalX.property('quantity').getValueAs("1").Value,
                self.form.inputBundleLayerNormalY.property('quantity').getValueAs("1").Value,
                self.form.inputBundleLayerNormalZ.property('quantity').getValueAs("1").Value)
            storeIfChanged(self.obj, 'SpacingDirection', spacing_direction)
            storeIfChanged(self.obj, 'AspectRatio', getQuantity(self.form.inputAspectRatio))
            storeIfChanged(self.obj, 'VelocityEstimate', getQuantity(self.form.inputVelocityEstimate))

        elif self.obj.Name.startswith('InitialisationZone'):
            storeIfChanged(self.obj, 'VelocitySpecified', self.form.checkVelocity.isChecked())
            storeIfChanged(self.obj, 'Ux', getQuantity(self.form.inputUx))
            storeIfChanged(self.obj, 'Uy', getQuantity(self.form.inputUy))
            storeIfChanged(self.obj, 'Uz', getQuantity(self.form.inputUz))
            storeIfChanged(self.obj, 'PressureSpecified', self.form.checkPressure.isChecked())
            storeIfChanged(self.obj, 'Pressure', getQuantity(self.form.inputPressure))
            storeIfChanged(self.obj, 'TemperatureSpecified', self.form.checkTemperature.isChecked())
            storeIfChanged(self.obj, 'Temperature', getQuantity(self.form.inputTemperature))
            storeIfChanged(self.obj, 'VolumeFractionSpecified', self.form.checkAlpha.isChecked())
            storeIfChanged(self.obj, 'VolumeFractions', self.alphas)

        if self.obj.ShapeRefs != self.ShapeRefsOrig:
            refstr = "FreeCAD.ActiveDocument.{}.ShapeRefs = [\n".format(self.obj.Name)
            refstr += ',\n'.join(
                "(FreeCAD.ActiveDocument.getObject('{}'), {})".format(ref[0].Name, ref[1]) for ref in self.obj.ShapeRefs)
            refstr += "]"
            FreeCADGui.doCommand(refstr)

        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()

    def reject(self):
        self.obj.ShapeRefs = self.ShapeRefsOrig
        FreeCADGui.doCommand("App.activeDocument().recompute()")
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()

    def closing(self):
        # We call this from unsetEdit to ensure cleanup
        self.faceSelector.closing()
