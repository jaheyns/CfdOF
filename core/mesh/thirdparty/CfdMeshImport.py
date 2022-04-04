# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2022 - Jonathan Bergh <bergh.jonathan@gmail.com>        *
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

from __future__ import print_function

import FreeCAD
import FreeCADGui
from PySide import QtCore, QtGui
import CfdTools
from CfdMesh import _CfdMesh
from CfdTools import addObjectProperty
import os


def makeCfdMeshImport(base_mesh, name="CFDMeshImport"):
    obj = FreeCAD.ActiveDocument.addObject("App::DocumentObjectGroupPython", name)
    _CfdMeshImport(obj)
    if FreeCAD.GuiUp:
        _ViewProviderCfdMeshImport(obj.ViewObject)
    base_mesh.addObject(obj)
    return obj


class _CommandCfdMeshFromImport:
    def GetResources(self):
        icon_path = os.path.join(CfdTools.get_module_path(), "Gui", "Resources", "icons", "meshimport.png")
        return {'Pixmap': icon_path,
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Cfd_MeshFromImport",
                                                     "CFD mesh import"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Cfd_MeshFromImport",
                                                    "Import an existing CFD mesh")}

    def IsActive(self):
        sel = FreeCADGui.Selection.getSelection()
        return sel and len(sel) == 1 and hasattr(sel[0], "Proxy") and isinstance(sel[0].Proxy, _CfdMesh)

    def Activated(self):
        sel = FreeCADGui.Selection.getSelection()
        analysis_obj = CfdTools.getActiveAnalysis()
        if analysis_obj:
            if len(sel) == 1:
                sobj = sel[0]
                if len(sel) == 1 and hasattr(sobj, "Proxy") and isinstance(sobj.Proxy, _CfdMesh):
                    FreeCAD.ActiveDocument.openTransaction("Create MeshImport")
                    FreeCADGui.doCommand("")
                    FreeCADGui.addModule("core.mesh.thirdparty.CfdMeshImport as CfdMeshImport")
                    FreeCADGui.doCommand(
                        "CfdMeshImport.makeCfdMeshImport(App.ActiveDocument.{})".format(sobj.Name))
                    FreeCADGui.ActiveDocument.setEdit(FreeCAD.ActiveDocument.ActiveObject.Name)
        else:
            print("ERROR: You cannot have more than one mesh object")

        FreeCADGui.Selection.clearSelection()


class _CfdMeshImport:
    """ CFD mesh import properties """

    # they will be used from the task panel too, thus they need to be outside of the __init__
    known_mesh_types = ['.msh', '.cgns']

    def __init__(self, obj):
        self.Type = "CfdMeshImport"
        self.Object = obj
        obj.Proxy = self
        self.initProperties(obj)

    def initProperties(self, obj):
        addObjectProperty(obj, 'CaseName', "meshCase", "App::PropertyString", "",
                          "Name of directory in which the mesh is created")

        # addObjectProperty(obj, "Part", None, "App::PropertyLink", "Mesh Parameters", "Part object to mesh")

        if addObjectProperty(obj, "MeshImportTypes", _CfdMeshImport.known_mesh_types, "App::PropertyEnumeration",
                             "Mesh Parameters", "Meshing utilities"):
            obj.MeshImportTypes = '.msh'

        addObjectProperty(obj, 'ImportFilename', "importFilename", "App::PropertyString", "Import Parameters",
                          "Filename of the mesh to import")

    def onDocumentRestored(self, obj):
        self.initProperties(obj)

    def execute(self, obj):
        pass

    def __getstate__(self):
        return self.Type

    def __setstate__(self, state):
        if state:
            self.Type = state


class _ViewProviderCfdMeshImport:
    """ A View Provider for the CfdMeshImport object """
    def __init__(self, vobj):
        vobj.Proxy = self
        self.taskd = None

    def getIcon(self):
        icon_path = os.path.join(CfdTools.get_module_path(), "Gui", "Resources", "icons", "meshimport.png")
        return icon_path

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object

    def updateData(self, obj, prop):
        return

    def onChanged(self, vobj, prop):
        CfdTools.setCompSolid(vobj)
        return

    def setEdit(self, vobj, mode):
        for obj in FreeCAD.ActiveDocument.Objects:
            if hasattr(obj, 'Proxy') and isinstance(obj.Proxy, _CfdMeshImport):
                obj.ViewObject.show()
        from core.mesh.thirdparty import _TaskPanelCfdMeshImport
        self.taskd = _TaskPanelCfdMeshImport._TaskPanelCfdMeshImport(self.Object)
        self.taskd.obj = vobj.Object
        FreeCADGui.Control.showDialog(self.taskd)
        return True

    def unsetEdit(self, vobj, mode):
        if self.taskd:
            self.taskd.closed()
            self.taskd = None
        FreeCADGui.Control.closeDialog()

    def doubleClicked(self, vobj):
        if FreeCADGui.activeWorkbench().name() != 'CfdOFWorkbench':
            FreeCADGui.activateWorkbench("CfdOFWorkbench")
        gui_doc = FreeCADGui.getDocument(vobj.Object.Document)
        # if not gui_doc.getInEdit():
        gui_doc.setEdit(vobj.Object.Name)
        # else:
        #     FreeCAD.Console.PrintError('Task dialog already open\n') # TODO Jonathan, check mes
        return True

    def onDelete(self, feature, subelements):
        try:
            for obj in self.Object.Group:
                obj.ViewObject.show()
        except Exception as err:
            FreeCAD.Console.PrintError("Error in onDelete: " + str(err))
        return True

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None
