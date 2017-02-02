
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
        self.p = self.obj.porousZoneProperties

        self.form = FreeCADGui.PySideUic.loadUi(FreeCAD.getHomePath() + "Mod/Cfd/TaskPanelPorousZone.ui")

        self.setInitialValues()
        self.form.selectReference.clicked.connect(self.selectReference)
        self.form.listWidget.itemClicked.connect(self.setSelection)
        self.form.pushButtonDelete.clicked.connect(self.deleteFeature)
        self.form.helpButton.clicked.connect(self.requestHelp)
        self.form.checkPoint.clicked.connect(self.checkPoint)
        self.form.automaticSelect.clicked.connect(self.autoDefinePoint)

        self.form.pushButtonDelete.setEnabled(False)


    def extractMainShapeFromMesh(self):
        isPresent = False
        meshObjects = []
        members = FemGui.getActiveAnalysis().Member
        mainShape = False
        message = None
        for i in members:
            if "Mesh" in i.Name:
                meshObjects.append(i)
                isPresent = True
        if len(meshObjects)>1:
            message = "More than 1 mesh objects were found! Cannot proceed!"
            #QtGui.QMessageBox.critical(None, "More than 1 mesh objects", message)
            return mainShape,message
        if isPresent == False:
            message = "No mesh objects were found. Cannot proceed!"
            #QtGui.QMessageBox.critical(None, "0 mesh objects found", message)
            return mainShape,message
        if len(self.obj.shapeList) == 0:
            message = "No porous zone regions have been selected yet. Please select a porous region."
            #QtGui.QMessageBox.critical(None, "No porous zones", message)
            return mainShape,message
        try:
            #Netgen mesh object
            mainShape = meshObjects[0].Shape
        except:
            #Gmsh mesh object
            mainShape = meshObjects[0].Part
        return mainShape,message

    def checkPoint(self):
        import FemGui
        mainShape,message = self.extractMainShapeFromMesh()
        if not(mainShape):
            QtGui.QMessageBox.critical(None, "Error", message)
            return

        px = float((FreeCAD.Units.Quantity(self.form.OX.text())).getValueAs("mm"))
        py = float((FreeCAD.Units.Quantity(self.form.OY.text())).getValueAs("mm"))
        pz = float((FreeCAD.Units.Quantity(self.form.OZ.text())).getValueAs("mm"))
        point = FreeCAD.Vector(float(px),float(py),float(pz))

        Result = self.checkOnePoint(mainShape,self.obj.shapeList,point)
        if Result:
            message = "Valid"
        else:
            message = "Not Valid\n"

        QtGui.QMessageBox.information(None, "Point check", message)

    def autoDefinePoint(self):
        point = self.autoFindPoint()
        if point == "criticalError":
            return
        elif point:
            self.form.OX.setText("{}{}".format(str(point[0]) ,'mm'))
            self.form.OY.setText("{}{}".format(str(point[1]),'mm'))
            self.form.OZ.setText("{}{}".format(str(point[2]),'mm'))
        else:
            message = "No valid points were automatically found. Please ensure that the selected shapes are valid. If valid, please select a point manually"
            QtGui.QMessageBox.critical(None, "Error", message)

    def autoFindPoint(self):
        porousShapes = self.obj.shapeList

        mainShape,message = self.extractMainShapeFromMesh()
        if not(mainShape):
            QtGui.QMessageBox.critical(None, "Error", message)
            return "criticalError"

        """
            NOTE The automatic selection algorithm is not full proof.
            1.) First check each vertex of the main shape.
            2.) Check each vertex of the intersecting shapes between the main shape an the porous zones 
            2.b) Each interseting vertex is perturbed about the vertex in 6 directions
            The first valid point is popped out
        """

        mainVertices = mainShape.Shape.Vertexes
        for ii in range(len(mainVertices)):
            point = mainVertices[ii].Point
            Result = self.checkOnePoint(mainShape,porousShapes,point)
            if Result:
                return point

        for ii in range(len(porousShapes)):
            import Part
            common = mainShape.Shape.common(porousShapes[ii].Shape)
            combinedVertices = common.Vertexes
            for jj in range(len(combinedVertices)):
                point = combinedVertices[jj].Point
                change = [FreeCAD.Vector(-1,0.0,0.0),FreeCAD.Vector(1,0.0,0.0),FreeCAD.Vector(0,-1.0,0.0),FreeCAD.Vector(0,1.0,0.0),FreeCAD.Vector(0.0,0.0,-1.0),FreeCAD.Vector(0.0,0.0,1.0)]
                for kk in range(2):
                    pointC = point + change[kk]
                    Result = self.checkOnePoint(mainShape,porousShapes,pointC)
                    if Result:
                        return point



    def checkOnePoint(self,mainShape,porousShapes,point):
        Result = True
        for ii in range(len(porousShapes)):
            shape = porousShapes[ii].Shape
            result = shape.isInside(point,0.001,False)
            if result:
                Result = False
            #QtGui.QMessageBox.critical(None, "No porous zones", str(result))
        if Result:
            if not(mainShape.Shape.isInside(point,0.001,True)):
                Result = False
        return Result

    def setInitialValues(self):
	for i in range(len(self.obj.partNameList)):
	    self.form.listWidget.addItem(str(self.obj.partNameList[i]))

        self.form.dx.setText("{}".format(self.p["dx"]))
        self.form.dy.setText("{}".format(self.p["dy"]))
        self.form.dz.setText("{}".format(self.p["dz"]))
        self.form.fx.setText("{}".format(self.p["fx"]))
        self.form.fy.setText("{}".format(self.p["fy"]))
        self.form.fz.setText("{}".format(self.p["fz"]))
        self.form.e1x.setText("{}".format(self.p["e1x"]))
        self.form.e1y.setText("{}".format(self.p["e1y"]))
        self.form.e1z.setText("{}".format(self.p["e1z"]))
        self.form.e3x.setText("{}".format(self.p["e3x"]))
        self.form.e3y.setText("{}".format(self.p["e3y"]))
        self.form.e3z.setText("{}".format(self.p["e3z"]))
        self.form.OX.setText("{}{}".format(self.p["OX"],'m'))
        self.form.OY.setText("{}{}".format(self.p["OY"],'m'))
        self.form.OZ.setText("{}{}".format(self.p["OZ"],'m'))
        #self.form.dy.setText(self.p["dy"])
        #self.form.dz.setText(self.p["dz"])
	
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


    def requestHelp(self):
        message = "Outside point Help.\nPlease specify a point location (x,y,z) which falls outside the porous zone regions but is still within fluid flow domain to be analysed (contained within the meshed region).\n\nHelpers:\nClick Automatic: Automatically find a point\nClick Check: Checks whether a given point is valid."
        QtGui.QMessageBox.information(None, "Outside point", message)

    def accept(self):
        self.p["dx"] = float(FreeCAD.Units.Quantity(self.form.dx.text()))
        self.p["dy"] = float(FreeCAD.Units.Quantity(self.form.dy.text()))
        self.p["dz"] = float(FreeCAD.Units.Quantity(self.form.dz.text()))
        self.p["fx"] = float(FreeCAD.Units.Quantity(self.form.fx.text()))
        self.p["fy"] = float(FreeCAD.Units.Quantity(self.form.fy.text()))
        self.p["fz"] = float(FreeCAD.Units.Quantity(self.form.fz.text()))
        self.p["e1x"] = float(FreeCAD.Units.Quantity(self.form.e1x.text()))
        self.p["e1y"] = float(FreeCAD.Units.Quantity(self.form.e1y.text()))
        self.p["e1z"] = float(FreeCAD.Units.Quantity(self.form.e1z.text()))
        self.p["e3x"] = float(FreeCAD.Units.Quantity(self.form.e3x.text()))
        self.p["e3y"] = float(FreeCAD.Units.Quantity(self.form.e3y.text()))
        self.p["e3z"] = float(FreeCAD.Units.Quantity(self.form.e3z.text()))
        self.p["OX"] = float((FreeCAD.Units.Quantity(self.form.OX.text())).getValueAs("m"))
        self.p["OY"] = float((FreeCAD.Units.Quantity(self.form.OY.text())).getValueAs("m"))
        self.p["OZ"] = float((FreeCAD.Units.Quantity(self.form.OZ.text())).getValueAs("m"))
        self.obj.porousZoneProperties = self.p
        self.obj.partNameList = self.partNameList
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()

    def reject(self):
        self.obj.shapeList = self.shapeListOrig
        FreeCADGui.doCommand("App.activeDocument().recompute()")
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()
