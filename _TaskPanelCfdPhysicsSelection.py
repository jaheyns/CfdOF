
__title__ = "_TaskPanelPhysicsSelection"
__author__ = ""
__url__ = "http://www.freecadweb.org"


import FreeCAD
import FreeCADGui
from PySide import QtGui
from PySide import QtCore
#import Units



class _TaskPanelCfdPhysicsSelection:
    '''The editmode TaskPanel for FemMaterial objects'''
    def __init__(self, obj):
        FreeCADGui.Selection.clearSelection()
        self.sel_server = None
        self.obj = obj
        self.physicsModel = self.obj.PhysicsModel.copy()

        self.form = FreeCADGui.PySideUic.loadUi(FreeCAD.getHomePath() + "Mod/Cfd/TaskPanelPhysics.ui")

        self.form.TimeFrame.setVisible(True)
        self.form.FlowFrame.setVisible(True)
        self.form.turbulenceFrame.setVisible(True)
        self.form.thermalFrame.setVisible(True)
        
        self.form.turbulenceChoiceFrame.setVisible(False)
        self.form.turbulenceModelFrame.setVisible(False)
        self.form.thermalSelectionFrame.setVisible(False)

        self.form.radioButtonSteady.toggled.connect(self.timeStateChanged)
        self.form.radioButtonTransient.toggled.connect(self.timeStateChanged)

        self.form.radioButtonIncompressible.toggled.connect(self.flowChoiceChanged)
        self.form.radioButtonCompressible.toggled.connect(self.flowChoiceChanged)

        self.form.turbulenceCheckBox.stateChanged.connect(self.turbulanceStateChanged)
        self.form.radioButtonRANS.toggled.connect(self.RANSChosen)
        #self.form.radioButtonLES_DES.toggled.connect(self.LESChosen)
        self.form.radioButtonLaminar.toggled.connect(self.hideTurbulenceModel)

        self.form.thermalCheckBox.stateChanged.connect(self.thermalStateChanged)
        self.form.radioButtonEnergy.toggled.connect(self.selectThermal)
        self.form.radioButtonBuoyancy.toggled.connect(self.selectThermal)

        #temporarily disabling features whihc are not yet supported
        #self.form.radioButtonRANS.setEnabled(False)
        #self.form.radioButtonTransient.setEnabled(False)
        #self.form.radioButtonCompressible.setEnabled(False)
        #self.form.radioButtonEnergy.setEnabled(False)
        #self.form.radioButtonBuoyancy.setEnabled(False)
        
        self.initialiseUponReload()


    def initialiseUponReload(self):
        if self.physicsModel['Time'] == 'Steady':
            self.form.radioButtonSteady.toggle()
        elif self.physicsModel['Time'] == 'Transient':
            self.form.radioButtonTransient.toggle()

        if self.physicsModel['Flow'] == 'Incompressible':
            self.form.radioButtonIncompressible.toggle()
        elif self.physicsModel['Flow'] == 'Compressible':
            self.form.radioButtonCompressible.toggle()

        if self.physicsModel['Turbulence'] == 'Laminar':
            self.form.turbulenceCheckBox.toggle()
            self.form.radioButtonLaminar.toggle()
        elif self.physicsModel['Turbulence'] == 'RANS':
            self.form.turbulenceCheckBox.toggle()
            self.form.radioButtonRANS.toggle()

        if self.physicsModel['Thermal'] == "Energy":
            self.form.thermalCheckBox.toggle()
            self.form.radioButtonEnergy.toggle()
        elif self.physicsModel['Thermal'] == "Buoyancy":
            self.form.thermalCheckBox.toggle()
            self.form.radioButtonBuoyancy.toggle()

    def timeStateChanged(self):
        self.form.FlowFrame.setVisible(True)

        if self.form.radioButtonSteady.isChecked():
            self.physicsModel['Time'] = 'Steady'
        else:
            self.physicsModel['Time'] = 'Transient'

    def selectThermal(self):
        if self.form.radioButtonEnergy.isChecked():
            self.physicsModel['Thermal'] = "Energy"
        elif self.form.radioButtonBuoyancy.isChecked():
            self.physicsModel['Thermal'] = "Buoyancy"

    def flowChoiceChanged(self):
        #self.form.turbulenceFrame.setVisible(True)
        #self.form.turbulenceChoiceFrame.setVisible(False)
        #self.form.turbulenceModelFrame.setVisible(False)
        #if self.form.turbulenceCheckBox.isChecked():
            #self.form.turbulenceCheckBox.toggle()

        #self.form.thermalFrame.setVisible(True)
        #self.form.thermalSelectionFrame.setVisible(False)
        #if self.form.thermalCheckBox.isChecked():
            #self.form.thermalCheckBox.toggle()
    

        if self.form.radioButtonIncompressible.isChecked():
            self.physicsModel["Flow"] = 'Incompressible'
        else:
            self.physicsModel["Flow"] = 'Compressible'

    def turbulanceStateChanged(self):
        if self.form.turbulenceCheckBox.isChecked():
            self.form.turbulenceChoiceFrame.setVisible(True)
            self.form.radioButtonLaminar.toggle()
        else:
            self.form.turbulenceChoiceFrame.setVisible(False)
            self.form.turbulenceModelFrame.setVisible(False)
            self.physicsModel["Turbulence"] = "None"

    def thermalStateChanged(self):
        if self.form.thermalCheckBox.isChecked():
            self.form.thermalSelectionFrame.setVisible(True)
            self.form.radioButtonEnergy.toggle()
        else:
            self.form.thermalSelectionFrame.setVisible(False)
            self.physicsModel["Thermal"] = "None"

    def RANSChosen(self):
        self.form.turbulenceModelFrame.setVisible(True)
        #NOTE: strictly there might be differences between incompressible and compressible!
        #see http://cfd.direct/openfoam/user-guide/turbulence/ for more openfoam supported models
        Choices = ["SpalartAllmaras","kEpsilon","SSG","RNGkEpsilon","kOmega","kOmegaSSTSAS"]
        self.form.turbulenceComboBox.clear()
        self.form.turbulenceComboBox.addItems(Choices)
        self.physicsModel["Turbulence"] = "RANS"


    #def LESChosen(self):
        #self.form.turbulenceModelFrame.setVisible(True)
        ##NOTE: strictly there might be differences between incompressible and compressible!
        ##see http://cfd.direct/openfoam/user-guide/turbulence/ for more openfoam supported models
        #Choices = ["Smagorinsky","kEqn","dynamicKEqn"]
        #self.form.turbulenceComboBox.clear()
        #self.form.turbulenceComboBox.addItems(Choices)


    def hideTurbulenceModel(self):
        self.form.turbulenceModelFrame.setVisible(False)
        self.physicsModel["Turbulence"] = "Laminar"


    def accept(self):
        self.obj.PhysicsModel = self.physicsModel
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()

        #return

        # print(self.material)
        #self.remove_active_sel_server()
        #if self.has_equal_references_shape_types():
            #self.obj.Material = self.material
            #self.obj.References = self.references
            #doc = FreeCADGui.getDocument(self.obj.Document)
            #doc.resetEdit()
            #doc.Document.recompute()

    def reject(self):
        #return
        ##self.remove_active_sel_server()
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()
