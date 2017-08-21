# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2016 - Bernd Hahnebach <bernd@bimstatik.org>            *
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

__title__ = "_ViewProviderCfdMeshCart"
__author__ = "Bernd Hahnebach"
__url__ = "http://www.freecadweb.org"

import FreeCAD
import FreeCADGui
import FemGui
import CfdTools
import os

class _ViewProviderCfdMeshCart:
    """ A View Provider for the CfdMeshCart object """
    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        icon_path = os.path.join(CfdTools.get_module_path(), "Gui", "Resources", "icons", "mesh.png")
        return icon_path

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object
        self.ViewObject.ShapeColor = (0.4, 0.4, 0.4)
        # self.ViewObject.LineWidth = 2

    def updateData(self, obj, prop):
        return

    def onChanged(self, vobj, prop):
        CfdTools.setCompSolid(vobj)
        return

    def setEdit(self, vobj, mode):
        for obj in FreeCAD.ActiveDocument.Objects:
            if obj.isDerivedFrom("Part::Feature"):
                obj.ViewObject.hide()
            if obj.isDerivedFrom("Fem::FemMeshObject"):
                obj.ViewObject.show()
        import _TaskPanelCfdMeshCart
        taskd = _TaskPanelCfdMeshCart._TaskPanelCfdMeshCart(self.Object)
        taskd.obj = vobj.Object
        FreeCADGui.Control.showDialog(taskd)
        return True

    def unsetEdit(self, vobj, mode):
        FreeCADGui.Control.closeDialog()
        return

    def doubleClicked(self, vobj):
        if FreeCADGui.activeWorkbench().name() != 'CfdOFWorkbench':
            FreeCADGui.activateWorkbench("CfdOFWorkbench")
        # Group meshing is only active on active analysis, should confirm the analysis the mesh belongs too is active
        gui_doc = FreeCADGui.getDocument(vobj.Object.Document)
        if not gui_doc.getInEdit():
            if FemGui.getActiveAnalysis() is not None:
                if FemGui.getActiveAnalysis().Document is FreeCAD.ActiveDocument:
                    if self.Object in FemGui.getActiveAnalysis().Member:
                        if not gui_doc.getInEdit():
                            gui_doc.setEdit(vobj.Object.Name)
                        else:
                            FreeCAD.Console.PrintError('Activate the analysis this mesh belongs to!\n')
                    else:
                        print('Mesh does not belong to the active analysis.')
                        for o in gui_doc.Document.Objects:
                            if o.isDerivedFrom('Fem::FemAnalysisPython'):
                                for m in o.Member:
                                    if m == self.Object:
                                        FemGui.setActiveAnalysis(o)
                                        print('Analysis the Mesh belongs too was activated.')
                                        gui_doc.setEdit(vobj.Object.Name)
                                        break
                else:
                    FreeCAD.Console.PrintError('Active Analysis is not in active Document!\n')
            else:
                # No active analysis
                for o in gui_doc.Document.Objects:
                    if o.isDerivedFrom('Fem::FemAnalysisPython'):
                        for m in o.Member:
                            if m == self.Object:
                                FemGui.setActiveAnalysis(o)
                                print('Analysis the Mesh belongs too was activated.')
                                gui_doc.setEdit(vobj.Object.Name)
                                break
                else:
                    print('Mesh GMSH object does not belong to an analysis. Group meshing will is deactivated.')
                    gui_doc.setEdit(vobj.Object.Name)
        else:
            FreeCAD.Console.PrintError('Active Task Dialog found! Please close this one first!\n')
        return True

    def claimChildren(self):
        return (self.Object.MeshRegionList + self.Object.MeshGroupList)

    def onDelete(self, feature, subelements):
        try:
            for obj in self.claimChildren():
                obj.ViewObject.show()
        except Exception as err:
            FreeCAD.Console.PrintError("Error in onDelete: " + err.message)
        return True

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None
