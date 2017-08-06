# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2017 - Alfred Bogaers (CSIR) <abogaers@csir.co.za>      *
# *   Copyright (c) 2017 - Johan Heyns (CSIR) <jheyns@csir.co.za>           *
# *   Copyright (c) 2017 - Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>        *
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
import FreeCADGui
import CfdTools
import os

# import pivy
# from pivy import coin

__title__ = "_ViewProviderCfdPorousZone"
__author__ = ""
__url__ = "http://www.freecadweb.org"


class _ViewProviderCfdPorousZone:
    """ A View Provider for the Porous Zone object. """
    def __init__(self, vobj):
        """ Set this object to the proxy object of the actual view provider """
        vobj.Proxy = self

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object
        self.ViewObject.ShapeColor = (0.5,0.0,1.0)
        self.ViewObject.Transparency = 70
        # Setup the scene sub-graph of the view provider, this method is mandatory
        return

    def updateData(self, fp, prop):
        """ If a property of the handled feature has changed we have the chance to handle this here """
        return

    def getDisplayModes(self, obj):
        """ Return a list of display modes. """
        modes=[]
        return modes

    def getDefaultDisplayMode(self):
        """ Return the name of the default display mode. It must be defined in getDisplayModes. """
        return "Shaded"

    def setDisplayMode(self,mode):
        """ Map the display mode defined in attach with those defined in getDisplayModes. Since they have the same
        names nothing needs to be done. This method is optinal.
        """
        return mode

    def onChanged(self, vp, prop):
        return

    def getIcon(self):
        if "PorousZone" in self.Object.Name:
            icon_path = os.path.join(CfdTools.get_module_path(), "Gui", "Resources", "icons", "porous.png")
        else:
            icon_path = os.path.join(CfdTools.get_module_path(), "Gui", "Resources", "icons", "alpha.png")
        return icon_path

    def setEdit(self, vobj, mode):
        import _TaskPanelCfdPorousZone
        taskd = _TaskPanelCfdPorousZone._TaskPanelCfdPorousZone(self.Object)
        taskd.obj = vobj.Object
        FreeCADGui.Control.showDialog(taskd)
        return True

    def unsetEdit(self, vobj, mode):
        FreeCADGui.Control.closeDialog()
        return

    def doubleClicked(self, vobj):
        doc = FreeCADGui.getDocument(vobj.Object.Document)
        # Overwrite the doubleClicked to make sure no other Material taskd (and thus no selection observer) is still
        # active
        if not doc.getInEdit():
            doc.setEdit(vobj.Object.Name)
        else:
            FreeCAD.Console.PrintError('Active Task Dialog found! Please close this one first!\n')
        return True

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None
