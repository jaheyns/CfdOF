
__title__ = "_TaskPanelCfdInitialiseInternalFlowField"
__author__ = ""
__url__ = "http://www.freecadweb.org"


import FreeCAD
import FreeCADGui
from PySide import QtGui
from PySide import QtCore
#import Units
import FemGui



class _TaskPanelCfdInitialiseInternalFlowField:
    '''The editmode TaskPanel for InitialVariables objects'''
    def __init__(self, obj):
        FreeCADGui.Selection.clearSelection()
        self.sel_server = None
        self.obj = obj
        self.physicsModel = self.fetchPhysicsObject()
        self.InitialVariables = self.obj.InitialVariables.copy()

        self.form = FreeCADGui.PySideUic.loadUi(FreeCAD.getHomePath() + "Mod/Cfd/TaskPanelCfdInitialiseInternalField.ui")


        self.form.potentialFoamMessageframe.setVisible(False)
        self.form.basicPropertiesFrame.setVisible(False)


        self.form.potentialFoamCheckBox.stateChanged.connect(self.potentialFoamClicked)
        self.form.potentialFoamQuestion.clicked.connect(self.requestPotentialFoamHelp)

        self.form.Ux.textChanged.connect(self.UxChanged)
        self.form.Uy.textChanged.connect(self.UyChanged)
        self.form.Uz.textChanged.connect(self.UzChanged)
        self.form.pressure.textChanged.connect(self.PChanged)

        #self.form.potentialFoamCheckBox.toggle()

        self.populateUiBasedOnPhysics()







    def UxChanged(self,value):
        import Units
        value = Units.Quantity(value).getValueAs("m/s")
        self.InitialVariables['Ux'] = unicode(value) + "m/s"

    def UyChanged(self,value):
        import Units
        value = Units.Quantity(value).getValueAs("m/s")
        self.InitialVariables['Uy'] = unicode(value) + "m/s"

    def UzChanged(self,value):
        import Units
        value = Units.Quantity(value).getValueAs("m/s")
        self.InitialVariables['Uz'] = unicode(value) + "m/s"

    def PChanged(self,value):
        import Units
        value = Units.Quantity(value).getValueAs("kg*m/s^2")
        self.InitialVariables['P'] = unicode(value) + "kg*m/s^2"

    def fetchPhysicsObject(self):
        members = FemGui.getActiveAnalysis().Member
        isPresent = False
        for i in members:
            if "PhysicsModel" in i.Name:
                physicsModel = i.PhysicsModel
                isPresent = True
        if not(isPresent):
            message = "Missing physics model! \n\nIt appears that the physics model has been deleted. Please re-create."
            QtGui.QMessageBox.critical(None,'Missing physics model',message)
        return physicsModel

    def requestPotentialFoamHelp(self):
        message = "Initialise flow field using PotentialFoam: \n\nPotentialFoam  is useful for generating initial conditions for Ux, Uy, Uz and Pressure for complex problems/geometries and generally assists convergence rates for steady state problems."
        QtGui.QMessageBox.information(None, "Initialising flow with potentialFoam", message)


    def populateUiBasedOnPhysics(self):
        if self.InitialVariables['PotentialFoam']:
            self.form.potentialFoamCheckBox.toggle()
        else:
            self.form.potentialFoamMessageframe.setVisible(False)
            self.form.basicPropertiesFrame.setVisible(True)
            self.form.Ux.setText(self.InitialVariables["Ux"])
            self.form.Uy.setText(self.InitialVariables["Uy"])
            self.form.Uz.setText(self.InitialVariables["Uz"])
            self.form.pressure.setText(self.InitialVariables["P"])

        if self.physicsModel['Turbulence'] in ['Laminar','RANS']:
            if self.physicsModel['Turbulence'] == 'Laminar':
                self.form.laminarFrame.setVisible(True)
                self.form.kEpsilonFrame.setVisible(False)
                self.form.SpalartAlmerasFrame.setVisible(False)
            if self.physicsModel['Turbulence'] == 'RANS':
                self.form.laminarFrame.setVisible(False)
                self.form.kEpsilonFrame.setVisible(True)
                self.form.SpalartAlmerasFrame.setVisible(True)
        else:
            self.form.turbulencePropertiesFrame.setVisible(False)
        if self.physicsModel['Thermal'] == 'Energy':
            self.form.energyFrame.setVisible(True)
            self.form.bouyancyFrame.setVisible(False)
        elif self.physicsModel['Thermal'] == 'Buoyancy':
            self.form.energyFrame.setVisible(False)
            self.form.bouyancyFrame.setVisible(True)
        else:
            self.form.thermalPropertiesFrame.setVisible(False)

    def potentialFoamClicked(self):
        if self.form.potentialFoamCheckBox.isChecked():
            self.form.potentialFoamMessageframe.setVisible(True)
            self.form.basicPropertiesFrame.setVisible(False)
            self.InitialVariables['PotentialFoam'] = True
        else:
            self.form.basicPropertiesFrame.setVisible(True)
            self.form.potentialFoamMessageframe.setVisible(False)
            self.InitialVariables['PotentialFoam'] = False

    def accept(self):
        self.obj.InitialVariables = self.InitialVariables
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()

    def reject(self):
        #return
        ##self.remove_active_sel_server()
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()
