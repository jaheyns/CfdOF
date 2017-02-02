#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2015 - FreeCAD Developers                               *
#*   Author (c) 2016 - Qingfeng Xia <qingfeng xia eng.ox.ac.uk>                    *
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   This program is distributed in the hope that it will be useful,       *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Library General Public License for more details.                  *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with this program; if not, write to the Free Software   *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************

import FreeCAD
import CfdTools
import os

if FreeCAD.GuiUp:
    import FreeCADGui
    import FemGui


class _ViewProviderCfdAnalysis:
    """A View Provider for the CfdAnalysis container object
    double click to bring up CFD workbench, instead of FemWorkbench
    """

    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        # return ":/icons/fem-cfd-analysis.svg"
        icon_path = os.path.join(CfdTools.get_module_path(), "Gui", "Resources", "icons", "cfd_analysis.png")
        return icon_path

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object
        self.bubbles = None

    def updateData(self, obj, prop):
        return

    def onChanged(self, vobj, prop):
        return

    def doubleClicked(self, vobj):
        self.makePartTransparent(vobj)
        if not FemGui.getActiveAnalysis() == self.Object:
            if FreeCADGui.activeWorkbench().name() != 'CfdWorkbench':
                FreeCADGui.activateWorkbench("CfdWorkbench")
            FemGui.setActiveAnalysis(self.Object)
            return True
        return True

    def makePartTransparent (self, vobj):
        ''' Make parts transparent so that the boundary conditions and cell zones are clearly visible.'''
        docName = str(vobj.Object.Document.Name)
        doc = FreeCAD.getDocument(docName)
        for obj in doc.Objects:
            if obj.isDerivedFrom("Part::Feature") and not("CfdFluidBoundary" in obj.Name):
                FreeCAD.getDocument(docName).getObject(obj.Name).ViewObject.Transparency = 70
                FreeCAD.getDocument(docName).getObject(obj.Name).ViewObject.LineWidth = 1
                FreeCAD.getDocument(docName).getObject(obj.Name).ViewObject.LineColor = (0.5,0.5,0.5)
                FreeCAD.getDocument(docName).getObject(obj.Name).ViewObject.PointColor = (0.5,0.5,0.5)
            if obj.isDerivedFrom("Part::Feature") and ("Compound" in obj.Name):
                FreeCAD.getDocument(docName).getObject(obj.Name).ViewObject.Visibility = False

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None