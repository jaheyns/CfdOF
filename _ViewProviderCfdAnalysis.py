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
        return ":/icons/fem-cfd-analysis.svg"

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object
        self.bubbles = None

    def updateData(self, obj, prop):
        return

    def onChanged(self, vobj, prop):
        return

    def doubleClicked(self, vobj):
        if not FemGui.getActiveAnalysis() == self.Object:
            if FreeCADGui.activeWorkbench().name() != 'CfdWorkbench':
                FreeCADGui.activateWorkbench("CfdWorkbench")
            FemGui.setActiveAnalysis(self.Object)
            return True
        return True

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None