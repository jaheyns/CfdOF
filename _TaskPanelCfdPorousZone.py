
__title__ = "_TaskPanelCfdPorousZone"
__author__ = ""
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

        self.form = FreeCADGui.PySideUic.loadUi(os.path.join(os.path.dirname(__file__), "TaskPanelPorousZone.ui"))

        self.setInitialValues()
        self.form.selectReference.clicked.connect(self.selectReference)
        self.form.listWidget.itemClicked.connect(self.setSelection)
        self.form.pushButtonDelete.clicked.connect(self.deleteFeature)
        self.form.helpButton.clicked.connect(self.requestHelp)
        self.form.checkPoint.clicked.connect(self.checkPoint)
        self.form.automaticSelect.clicked.connect(self.autoDefinePoint)

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

        self.form.dx.setText("{} {}".format(self.p["dx"], "m^-2"))
        self.form.dy.setText("{} {}".format(self.p["dy"], "m^-2"))
        self.form.dz.setText("{} {}".format(self.p["dz"], "m^-2"))
        self.form.fx.setText("{} {}".format(self.p["fx"], "m^-1"))
        self.form.fy.setText("{} {}".format(self.p["fy"], "m^-1"))
        self.form.fz.setText("{} {}".format(self.p["fz"], "m^-1"))
        self.form.e1x.setText("{}".format(CfdTools.getOrDefault(self.p, 'e1x', 1)))
        self.form.e1y.setText("{}".format(CfdTools.getOrDefault(self.p, 'e1y', 0)))
        self.form.e1z.setText("{}".format(CfdTools.getOrDefault(self.p, 'e1z', 0)))
        self.form.e2x.setText("{}".format(CfdTools.getOrDefault(self.p, 'e2x', 0)))
        self.form.e2y.setText("{}".format(CfdTools.getOrDefault(self.p, 'e2y', 1)))
        self.form.e2z.setText("{}".format(CfdTools.getOrDefault(self.p, 'e2z', 0)))
        self.form.e3x.setText("{}".format(CfdTools.getOrDefault(self.p, 'e3x', 0)))
        self.form.e3y.setText("{}".format(CfdTools.getOrDefault(self.p, 'e3y', 0)))
        self.form.e3z.setText("{}".format(CfdTools.getOrDefault(self.p, 'e3z', 1)))
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

    # One of the e vector edit boxes loses focus or user presses enter
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

        self.form.e1x.setText(str(e[0][0]))
        self.form.e1y.setText(str(e[0][1]))
        self.form.e1z.setText(str(e[0][2]))
        self.form.e2x.setText(str(e[1][0]))
        self.form.e2y.setText(str(e[1][1]))
        self.form.e2z.setText(str(e[1][2]))
        self.form.e3x.setText(str(e[2][0]))
        self.form.e3y.setText(str(e[2][1]))
        self.form.e3z.setText(str(e[2][2]))

    def accept(self):
        self.p["dx"] = float(FreeCAD.Units.Quantity(self.form.dx.text()).getValueAs("m^-2"))
        self.p["dy"] = float(FreeCAD.Units.Quantity(self.form.dy.text()).getValueAs("m^-2"))
        self.p["dz"] = float(FreeCAD.Units.Quantity(self.form.dz.text()).getValueAs("m^-2"))
        self.p["fx"] = float(FreeCAD.Units.Quantity(self.form.fx.text()).getValueAs("m^-1"))
        self.p["fy"] = float(FreeCAD.Units.Quantity(self.form.fy.text()).getValueAs("m^-1"))
        self.p["fz"] = float(FreeCAD.Units.Quantity(self.form.fz.text()).getValueAs("m^-1"))
        self.p["e1x"] = float(FreeCAD.Units.Quantity(self.form.e1x.text()))
        self.p["e1y"] = float(FreeCAD.Units.Quantity(self.form.e1y.text()))
        self.p["e1z"] = float(FreeCAD.Units.Quantity(self.form.e1z.text()))
        self.p["e2x"] = float(FreeCAD.Units.Quantity(self.form.e2x.text()))
        self.p["e2y"] = float(FreeCAD.Units.Quantity(self.form.e2y.text()))
        self.p["e2z"] = float(FreeCAD.Units.Quantity(self.form.e2z.text()))
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
