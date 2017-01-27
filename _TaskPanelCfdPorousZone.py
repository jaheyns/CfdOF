
__title__ = "_TaskPanelCfdPorousZone"
__author__ = ""
__url__ = "http://www.freecadweb.org"


import FreeCAD
import FreeCADGui
from PySide import QtGui
from PySide import QtCore
#import Units
import FemGui
import Part


class _TaskPanelCfdPorousZone:
    '''The editmode TaskPanel for InitialVariables objects'''
    def __init__(self, obj):
        FreeCADGui.Selection.clearSelection()
        self.sel_server = None
        #obj.addProperty("Part::PropertyPartShape","Shape","Something")
        self.obj = obj
        self.shapeListOrig = list(self.obj.shapeList)
        self.partNameList = list(self.obj.partNameList)
        
        self.form = FreeCADGui.PySideUic.loadUi(FreeCAD.getHomePath() + "Mod/Cfd/TaskPanelPorousZone.ui")
        
        self.setInitialValues()
        self.form.selectReference.clicked.connect(self.selectReference)
        self.form.listWidget.itemClicked.connect(self.setSelection)
        self.form.pushButtonDelete.clicked.connect(self.deleteFeature)
        
        self.form.pushButtonDelete.setEnabled(False)


    def setInitialValues(self):
	for i in range(len(self.obj.partNameList)):
	    self.form.listWidget.addItem(str(self.obj.partNameList[i]))
	
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
	
	return
    
    
    def setSelection(self,value):
	FreeCADGui.Selection.clearSelection()
	FreeCADGui.Selection.addSelection(self.obj.shapeList[self.form.listWidget.row(value)])
	self.form.pushButtonDelete.setEnabled(True)
	return
    
    def selectReference(self):
        selection = FreeCADGui.Selection.getSelectionEx()
        """
            NOTE: to access the subElement (eg face which was selected) it would be selection[i].Object.SubElementNames
            Access to the actual shapes such as solids, faces, edges etc s[i].Object.Shape.Faces/Edges/Solids
        """
        shapeList = list(self.obj.shapeList)
        for i in range(len(selection)):
                if len(selection[i].Object.Shape.Solids)>0:
                    if not(selection[i].Object.Name in self.partNameList):
                        self.form.listWidget.addItem(str(selection[i].Object.Name))
                        shapeList.append(selection[i].Object)
                        self.partNameList.append(selection[i].Object.Name)
                        
                        
        self.obj.shapeList = shapeList
        FreeCADGui.doCommand("App.activeDocument().recompute()")
        
    
    def accept(self):
        self.obj.partNameList = self.partNameList
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()

    def reject(self):
        self.obj.shapeList = self.shapeListOrig
        FreeCADGui.doCommand("App.activeDocument().recompute()")
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()
