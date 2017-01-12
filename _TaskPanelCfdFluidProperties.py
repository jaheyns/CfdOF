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

if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore
    from PySide import QtCore
    from PySide import QtGui
    from PySide.QtCore import Qt
    from PySide.QtGui import QApplication
    import FemGui


class TaskPanelFluidProperties:
    '''The editmode TaskPanel for FluidMaterial objects'''
    def __init__(self, obj):
        self.obj = obj
        self.material = self.obj.Material

        ''' Initial version of the flow solver only support single region analysis and therefore selection_mode_solid
            is not included.
        '''

        self.form = FreeCADGui.PySideUic.loadUi(os.path.dirname(__file__) + os.path.sep + "TaskPanelFluidProperties.ui")

        ''' In most cases, unlike FEM, fluid flow properties are defined by the user. A small number of reference
            values are store in the fcmat database for fluids to serve as a starting point for the user.  The properties
            are therefore always initialised to "None" with the previous quantities reloaded in the input fields,
            instead of trying match to a database entry as in FEM.
        '''
        self.import_materials()
        index = self.form.PredefinedMaterialLibraryComboBox.findText('None')
        self.form.PredefinedMaterialLibraryComboBox.setCurrentIndex(index)

        QtCore.QObject.connect(self.form.PredefinedMaterialLibraryComboBox, QtCore.SIGNAL("currentIndexChanged(int)"), self.selectPredefine)

        ''' NOTE Using different connect here because we would like access to the full text, where
            QtCore.QObject.connect, does not recognize textChanged signal.  We do so to allow the units to be pulled
            along with the values to ensure unit consistency, unlike FEM where units are assumed upon change/save.
        '''
        self.form.fDens.textChanged.connect(self.DensityChanged)
        self.form.fViscosity.textChanged.connect(self.ViscosityChanged)

        self.check_material_keys()
        self.setTextFields(self.material)

        FreeCAD.Console.PrintMessage("Task panel initialised \n")

    def selectPredefine(self):
        index = self.form.PredefinedMaterialLibraryComboBox.currentIndex()

        mat_file_path = self.form.PredefinedMaterialLibraryComboBox.itemData(index) 
        self.form.fluidDescriptor.setText(self.materials[mat_file_path]["Description"])
        self.setTextFields(self.materials[mat_file_path])

    def setTextFields(self,matmap):
        if 'Density' in matmap:
            density_new_unit = "kg/m^3"
            density = FreeCAD.Units.Quantity(matmap['Density'])
            density_with_new_unit = density.getValueAs(density_new_unit)
            self.form.fDens.setText("{} {}".format(density_with_new_unit, density_new_unit))

        if "DynamicViscosity" in matmap:
            new_unit = "kg/s/m"
            visc = FreeCAD.Units.Quantity(matmap['DynamicViscosity'])
            visc_with_new_unit = float(visc.getValueAs(new_unit))
            self.form.fViscosity.setText("{} {}".format(visc_with_new_unit,new_unit))



    def DensityChanged(self,value):
        import Units
        density = Units.Quantity(value).getValueAs("kg/m^3")
        self.material['Density'] = unicode(density) + "kg/m^3"

    def ViscosityChanged(self,value):
        import Units
        viscosity = Units.Quantity(value).getValueAs("kg/m/s")
        self.material['DynamicViscosity'] = unicode(viscosity) + "kg/m/s"

    def accept(self):
        self.obj.Material = self.material
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()
        doc.Document.recompute()

    def check_material_keys(self):
        if 'Density' not in self.material:
            self.material['Density'] = '0 kg/m^3'
        if 'DynamicViscosity' not in self.material:
            self.material['DynamicViscosity'] = '0 kg/m/s'

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

