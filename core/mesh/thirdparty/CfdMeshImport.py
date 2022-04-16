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
from pivy import coin
from CfdTools import addObjectProperty
import os
from core.mesh.thirdparty import TaskPanelCfdMeshImport


def makeCfdMeshImport(base_mesh, name="CFDMeshImport"):
    obj = FreeCAD.ActiveDocument.addObject("App::DocumentObjectGroupPython", name)
    _CfdMeshImport(obj)
    if FreeCAD.GuiUp:
        _ViewProviderCfdMeshImport(obj.ViewObject)
    # base_mesh.addObject(obj)
    return obj


class _CommandCfdMeshFromImport:

    def __init__(self):
        pass

    def GetResources(self):
        icon_path = os.path.join(CfdTools.get_module_path(), "Gui", "Resources", "icons", "mesh_import.svg")
        return {'Pixmap': icon_path,
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Cfd_MeshFromImport", "CFD mesh import"),
                'Accel': "M, I",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Cfd_MeshFromImport", "Import an existing CFD mesh")}

    def IsActive(self):
        analysis_obj = CfdTools.getActiveAnalysis()
        mesh_obj = CfdTools.getMesh(analysis_obj)

        # No import is mesh already exists
        if mesh_obj is not None:
            return False
        else:
            sel = FreeCADGui.Selection.getSelection()
            return sel and len(sel) == 1 and hasattr(sel[0], "Proxy") #and isinstance(sel[0].Proxy, _CfdMesh)

    def Activated(self):
        is_present = False
        members = CfdTools.getMesh(CfdTools.getActiveAnalysis()).Group
        for i in members:
            if isinstance(i.Proxy, _CfdMeshImport):
                FreeCADGui.activeDocument().setEdit(i.Name)
                is_present = True

        if not is_present:
            sel = FreeCADGui.Selection.getSelection()
            if len(sel) == 1:
                sobj = sel[0]
                if len(sel) == 1 and hasattr(sobj, "Proxy") and isinstance(sobj.Proxy, _CfdMesh):
                    FreeCAD.ActiveDocument.openTransaction("Create MeshImport")
                    FreeCADGui.doCommand("")
                    FreeCADGui.addModule("core.mesh.thirdparty.CfdMeshImport as CfdMeshImport")
                    FreeCADGui.doCommand(
                        "CfdMeshImport.makeCfdMeshImport(App.ActiveDocument.{})".format(sobj.Name))
                    FreeCADGui.ActiveDocument.setEdit(FreeCAD.ActiveDocument.ActiveObject.Name)

        FreeCADGui.Selection.clearSelection()


class _CfdMeshImport:
    """ CFD mesh import properties """

    # they will be used from the task panel too, thus they need to be outside of the __init__
    known_mesh_types = ['.msh', '.cgns']

    def __init__(self, obj):
        obj.Proxy = self
        self.Type = "CfdMeshImport"
        self.initProperties(obj)

    def initProperties(self, obj):
        addObjectProperty(obj, 'CaseName', "meshCase", "App::PropertyString", "",
                          "Name of directory in which the mesh is created")

        if addObjectProperty(obj, "MeshImportTypes", _CfdMeshImport.known_mesh_types, "App::PropertyEnumeration",
                             "Mesh Parameters", "Meshing utilities"):
            obj.MeshImportTypes = '.msh'

        addObjectProperty(obj, 'ImportFilename', "importFilename", "App::PropertyString", "Import Parameters",
                          "Filename of the mesh to import")

    def onDocumentRestored(self, obj):
        self.initProperties(obj)


class _ViewProviderCfdMeshImport:
    """ A View Provider for the CfdMeshImport object """
    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        icon_path = os.path.join(CfdTools.get_module_path(), "Gui", "Resources", "icons", "mesh_import.svg")
        return icon_path

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object
        self.standard = coin.SoGroup()
        vobj.addDisplayMode(self.standard, "Standard")

    def getDisplayModes(self, obj):
        modes = []
        return modes

    def getDefaultDisplayMode(self):
        return "Shaded"

    def setDisplayMode(self, mode):
        return mode

    def updateData(self, obj, prop):
        return

    def onChanged(self, vobj, prop):
        return

    def setEdit(self, vobj, mode):
        import importlib
        importlib.reload(TaskPanelCfdMeshImport)
        taskd = TaskPanelCfdMeshImport.TaskPanelCfdMeshImport(self.Object)
        taskd.obj = vobj.Object
        FreeCADGui.Control.showDialog(taskd)
        return True

    def unsetEdit(self, vobj, mode=0):
        FreeCADGui.Control.closeDialog()
        return

    def doubleClicked(self, vobj):
        gui_doc = FreeCADGui.getDocument(vobj.Object.Document)
        if not gui_doc.getInEdit():
            gui_doc.setEdit(vobj.Object.Name)
        else:
            FreeCAD.Console.PrintError('Task dialog already open\n')
        return True

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None
