
__title__ = "_ViewProviderCfdPorousZone"
__author__ = ""
__url__ = "http://www.freecadweb.org"

import FreeCAD
import FreeCADGui
import CfdTools
import os

import pivy
from pivy import coin

class _ViewProviderCfdPorousZone:
    "A View Provider for the InitialVariables object"
    def __init__(self, obj):
            ''' Set this object to the proxy object of the actual view provider '''
            obj.Proxy = self

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object
        self.ViewObject.ShapeColor = (0.0,0.0,1.0)
        #self.ViewObject.LineColor = (1.0,0.0,0.0)
        #self.ViewObject.PointColor = (1.0,0.0,0.0)
        #self.ViewObject.LineWidth = 5
        self.ViewObject.Transparency = 70
        #self.ViewObject.PointSize = 5
        ''' Setup the scene sub-graph of the view provider, this method is mandatory '''
        return

    def updateData(self, fp, prop):
            ''' If a property of the handled feature has changed we have the chance to handle this here '''
            return

    def getDisplayModes(self,obj):
            ''' Return a list of display modes. '''
            modes=[]
            return modes

    def getDefaultDisplayMode(self):
            ''' Return the name of the default display mode. It must be defined in getDisplayModes. '''
            return "Shaded"

    def setDisplayMode(self,mode):
            ''' Map the display mode defined in attach with those defined in getDisplayModes.
            Since they have the same names nothing needs to be done. This method is optinal.
            '''
            return mode

    def onChanged(self, vp, prop):
            ''' Print the name of the property that has changed '''
            FreeCAD.Console.PrintMessage("Change property: " + str(prop) + "\n")

    def getIcon(self):
            ''' Return the icon in XMP format which will appear in the tree view. This method is optional
            and if not defined a default icon is shown.
            '''
            return """
                    /* XPM */
                    static const char * ViewProviderBox_xpm[] = {
                    "16 16 6 1",
                    " 	c None",
                    ".	c #141010",
                    "+	c #615BD2",
                    "@	c #C39D55",
                    "#	c #000000",
                    "$	c #57C355",
                    "        ........",
                    "   ......++..+..",
                    "   .@@@@.++..++.",
                    "   .@@@@.++..++.",
                    "   .@@  .++++++.",
                    "  ..@@  .++..++.",
                    "###@@@@ .++..++.",
                    "##$.@@$#.++++++.",
                    "#$#$.$$$........",
                    "#$$#######      ",
                    "#$$#$$$$$#      ",
                    "#$$#$$$$$#      ",
                    "#$$#$$$$$#      ",
                    " #$#$$$$$#      ",
                    "  ##$$$$$#      ",
                    "   #######      "};
                    """

    def __getstate__(self):
            ''' When saving the document this object gets stored using Python's cPickle module.
            Since we have some un-pickable here -- the Coin stuff -- we must define this method
            to return a tuple of all pickable objects or None.
            '''
            return None

    def __setstate__(self,state):
            ''' When restoring the pickled object from document we have the chance to set some
            internals here. Since no data were pickled nothing needs to be done here.
            '''
            return None


    def makeSolidsVisible(self,makeVisible):
        for ShapeNameObj in FreeCAD.ActiveDocument.Objects:
                if ShapeNameObj.isDerivedFrom("Part::Feature") and  not("PorousZone" in ShapeNameObj.Name) :
                    #FreeCADGui.ActiveDocument.getObject(ShapeNameObj.Name).Visibility = True/False
                    FreeCADGui.ActiveDocument.getObject(ShapeNameObj.Name).Visibility = makeVisible

    def setEdit(self, vobj, mode):
        import _TaskPanelCfdPorousZone
        taskd = _TaskPanelCfdPorousZone._TaskPanelCfdPorousZone(self.Object)
        taskd.obj = vobj.Object
        self.makeSolidsVisible(True)
        FreeCADGui.Control.showDialog(taskd)
        return True
    

    def unsetEdit(self, vobj, mode):
        self.makeSolidsVisible(False)
        FreeCADGui.Control.closeDialog()
        return

    # overwrite the doubleClicked to make sure no other Material taskd (and thus no selection observer) is still active
    def doubleClicked(self, vobj):
        doc = FreeCADGui.getDocument(vobj.Object.Document)
        if not doc.getInEdit():
            doc.setEdit(vobj.Object.Name)
        else:
            FreeCAD.Console.PrintError('Active Task Dialog found! Please close this one first!\n')
        return True

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None
