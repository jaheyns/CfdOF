#***************************************************************************
#*   (c) Bernd Hahnebach (bernd@bimstatik.org) 2014                        *
#*   (c) Qingfeng Xia @ iesensor.com 2016                                  *
#*   (c) CSIR, South Africa 2017                                           *
#*                                                                         *
#*   This file is part of the FreeCAD CAx development system.              *
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   FreeCAD is distributed in the hope that it will be useful,            *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Lesser General Public License for more details.                   *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with FreeCAD; if not, write to the Free Software        *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************/

import FreeCAD
import os
import sys
import os.path
import Units

if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore
    from PySide import QtCore
    from PySide import QtGui
    from PySide.QtCore import Qt
    from PySide.QtGui import QApplication
    import FemGui


class TaskPanelCfdFluidProperties:
    '''The editmode TaskPanel for FluidMaterial objects'''
    def __init__(self, obj):
        self.obj = obj
        self.material = self.obj.Material

        # Initial version of the flow solver only support single region analysis and therefore selection_mode_solid
        # is not included.

        self.form = FreeCADGui.PySideUic.loadUi(os.path.join(os.path.dirname(__file__),
                                                             "TaskPanelCfdFluidProperties.ui"))

        # In most cases, unlike FEM, fluid flow properties are defined by the user. A small number of reference
        # values are stored in the fcmat database for fluids to serve as a starting point for the user. The properties
        # are therefore always initialised to "None" with the previous quantities reloaded in the input fields,
        # instead of trying match to a database entry as in FEM.

        self.import_materials()
        index = self.form.PredefinedMaterialLibraryComboBox.findText('None')
        self.form.PredefinedMaterialLibraryComboBox.setCurrentIndex(index)

        self.form.PredefinedMaterialLibraryComboBox.currentIndexChanged.connect(self.selectPredefine)

        self.form.fDens.valueChanged.connect(self.densityChanged)
        self.form.fViscosity.valueChanged.connect(self.viscosityChanged)

        self.setTextFields(self.material)

    def selectPredefine(self):
        index = self.form.PredefinedMaterialLibraryComboBox.currentIndex()

        mat_file_path = self.form.PredefinedMaterialLibraryComboBox.itemData(index) 
        self.form.fluidDescriptor.setText(self.materials[mat_file_path]["Description"])
        self.setTextFields(self.materials[mat_file_path])

    def setTextFields(self,matmap):
        if 'Density' in matmap:
            self.form.fDens.setProperty('quantityString', matmap['Density'])
        if "DynamicViscosity" in matmap:
            self.form.fViscosity.setProperty('quantityString', matmap['DynamicViscosity'])

    def densityChanged(self, quantity):
        self.material['Density'] = str(quantity)

    def viscosityChanged(self, quantity):
        self.material['DynamicViscosity'] = str(quantity)

    def accept(self):
        self.obj.Material = self.material
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()
        doc.Document.recompute()

        # Unlike the other dictionaries, 'Material' still stores values along with their units as str due to
        # the structure of the database
        FreeCADGui.doCommand("\nmat = FreeCAD.ActiveDocument." + self.obj.Name + ".Material")
        FreeCADGui.doCommand("mat['Density'] = '{}'".format(self.material['Density']))
        FreeCADGui.doCommand("mat['DynamicViscosity'] = '{}'".format(self.material['DynamicViscosity']))
        FreeCADGui.doCommand("FreeCAD.ActiveDocument." + self.obj.Name + ".Material = mat")

    def reject(self):
        #self.remove_active_sel_server()
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()

    def add_mat_dir(self, mat_dir, icon):
        import glob
        import os
        import Material
        mat_file_extension = ".FCMat"
        ext_len = len(mat_file_extension)
        dir_path_list = glob.glob(mat_dir + '/*' + mat_file_extension)
        self.pathList = self.pathList + dir_path_list
        material_name_list = []
        for a_path in dir_path_list:
            material_name = os.path.basename(a_path[:-ext_len])
            self.materials[a_path] = Material.importFCMat(a_path)
            material_name_list.append([material_name, a_path])
        material_name_list.sort()

        for mat in material_name_list:
            self.form.PredefinedMaterialLibraryComboBox.addItem(QtGui.QIcon(icon), mat[0], mat[1])

    def import_materials(self):
        import CfdTools

        self.materials = {}
        self.pathList = []
        self.form.PredefinedMaterialLibraryComboBox.clear()

        ''' Until module is integrated, store the defaults inside the module directory rather than the resource dir '''
        # system_mat_dir = FreeCAD.getResourceDir() + "/Mod/Material/FluidMaterialProperties"
        system_mat_dir = os.path.join(CfdTools.get_module_path(), "data/CfdFluidMaterialProperties")
        self.add_mat_dir(system_mat_dir, ":/icons/freecad.svg")

