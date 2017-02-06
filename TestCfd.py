# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2017 - Johan Heyns (CSIR) <jheyns@csir.co.za>           *
# *   Copyright (c) 2017 - Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>        *
# *   Copyright (c) 2017 - Alfred Bogaers (CSIR) <abogaers@csir.co.za>      *
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

import CfdAnalysis
import CfdSolverFoam
import CfdPhysicsSelection
import CfdInitialiseFlowField
import CfdFluidMaterial
import CfdMeshGmsh
import CfdFluidBoundary
import CfdTools

# import csv
import tempfile
import unittest

__title__ = "CFD unit test"
__author__ = "AB, JH, OO"
__url__ = "http://www.freecadweb.org"

""" Unit tests for the CFD WB
Until included in Test Framework run the test in FreeCAD console

import unittest
suite = unittest.TestSuite()
suite.addTest(unittest.defaultTestLoader.loadTestsFromName("TestCfd"))
r = unittest.TextTestRunner()
r.run(suite)

NOTE: Running the unit test in FreeCADCmd gives PySideUic errors.
"""

home_path = FreeCAD.getHomePath()
temp_dir = tempfile.gettempdir()
test_file_dir = home_path + 'Mod/Cfd/test_files/'


def fccPrint(message):
    FreeCAD.Console.PrintMessage('{} \n'.format(message))


class BlockTest(unittest.TestCase):
    __doc_name = 'block'
    __part_name = 'Box'

    def setUp(self):
        """ Load document with part. """
        part_file = test_file_dir + 'parts/' + self.__class__.__doc_name + '.fcstd'
        FreeCAD.open(part_file)
        FreeCAD.setActiveDocument(self.__class__.__doc_name)
        self.active_doc = FreeCAD.ActiveDocument
        self.active_doc.recompute()

    def createNewAnalysis(self):
        self.analysis = CfdAnalysis.makeCfdAnalysis('CfdAnalysis')
        self.active_doc.recompute()

    def createNewSolver(self):
        self.solver_object = CfdSolverFoam.makeCfdSolverFoam()
        self.solver_object.EndTime = 100
        self.solver_object.ConvergenceCriteria = 0.001
        self.solver_object.Parallel = False
        self.active_doc.recompute()

    def createNewPhysics(self):
        self.physics_object = CfdPhysicsSelection.makeCfdPhysicsSelection()
        phys = self.physics_object.PhysicsModel
        phys['Time'] = 'Steady'
        phys['Flow'] = 'Incompressible'
        phys['Turbulence'] = 'Laminar'
        self.active_doc.recompute()

    def createNewInitialise(self):
        self.initialise_object = CfdInitialiseFlowField.makeCfdInitialFlowField()
        init_var = self.initialise_object.InitialVariables
        init_var['PotentialFoam'] = True
        self.active_doc.recompute()

    def createNewFluidProperty(self):
        self.material_object = CfdFluidMaterial.makeCfdFluidMaterial('CfdFluidProperties')
        mat = self.material_object.Material
        mat['Name'] = 'None'
        mat['Density'] = '1.20 kg/m^3'
        mat['DynamicViscosity'] = '0.000018 kg/m/s'
        self.active_doc.recompute()

    def createNewMesh(self, mesh_name):
        self.mesh_object = CfdMeshGmsh.makeCfdMeshGmsh(mesh_name)
        doc = FreeCAD.getDocument(self.__class__.__doc_name)
        obj = doc.getObject(mesh_name)
        vobj = obj.ViewObject
        obj.Part = doc.getObject(self.__class__.__part_name)
        CfdTools.setPartVisibility(vobj, False, False, True, True)
        obj.CharacteristicLengthMax = "80 mm"
        obj.ElementOrder = "1st"
        import _TaskPanelCfdMeshGmsh
        taskd = _TaskPanelCfdMeshGmsh._TaskPanelCfdMeshGmsh(obj)  # Error when ran in FreeCADCmd
        taskd.obj = vobj.Object
        taskd.run_gmsh()

    def createInletBoundary(self):
        self.inlet_boundary = CfdFluidBoundary.makeCfdFluidBoundary('inlet')
        bc_set = self.inlet_boundary.BoundarySettings
        bc_set['BoundaryType'] = 'inlet'
        bc_set['BoundarySubtype'] = 'uniformVelocity'
        bc_set['Ux'] = '1 m/s'
        bc_set['Uy'] = '0 m/s'
        bc_set['Uz'] = '0 m/s'

        # Test addSelection and rebuild_list_references
        doc = FreeCAD.getDocument(self.__class__.__doc_name)
        obj = doc.getObject('inlet')
        vobj = obj.ViewObject
        import _TaskPanelCfdFluidBoundary
        taskd = _TaskPanelCfdFluidBoundary.TaskPanelCfdFluidBoundary(obj)
        CfdTools.setPartVisibility(vobj, True, False, False, True)
        taskd.obj = vobj.Object
        taskd.selecting_references = True
        taskd.addSelection(doc.Name, doc.getObject(self.__class__.__part_name).Name, 'Face1')
        taskd.accept()

    def createOutletBoundary(self):
        self.outlet_boundary = CfdFluidBoundary.makeCfdFluidBoundary('outlet')
        bc_set = self.outlet_boundary.BoundarySettings
        bc_set['BoundaryType'] = 'outlet'
        bc_set['BoundarySubtype'] = 'staticPressure'
        bc_set['Pressure'] = '0.0 m*kg/s^2'
        self.outlet_boundary.References = [('Box', 'Face4')]
        FreeCADGui.doCommand("FreeCAD.getDocument('"+self.__class__.__doc_name+"').recompute()")

    def createWallBoundary(self):
        self.wall_boundary = CfdFluidBoundary.makeCfdFluidBoundary('wall')
        bc_set = self.wall_boundary.BoundarySettings
        bc_set['BoundaryType'] = 'wall'
        bc_set['BoundarySubtype'] = 'fixed'
        self.wall_boundary.References = [('Box', 'Face2'), ('Box', 'Face3')]
        FreeCADGui.doCommand("FreeCAD.getDocument('"+self.__class__.__doc_name+"').recompute()")

    def createSlipBoundary(self):
        self.slip_boundary = CfdFluidBoundary.makeCfdFluidBoundary('slip')
        bc_set = self.slip_boundary.BoundarySettings
        bc_set['BoundaryType'] = 'wall'
        bc_set['BoundarySubtype'] = 'slip'
        self.slip_boundary.References = [('Box', 'Face5'), ('Box', 'Face6')]
        FreeCADGui.doCommand("FreeCAD.getDocument('"+self.__class__.__doc_name+"').recompute()")

    def writeInputFiles(self):
        print ('Write input files ...')
        doc = FreeCAD.getDocument(self.__class__.__doc_name)

    def test_new_analysis(self):
        fccPrint('--------------- Start of CFD tests ---------------')
        fccPrint('Checking CFD new analysis...')
        self.createNewAnalysis()
        self.assertTrue(self.analysis, "CfdTest of new analysis failed")

        fccPrint('Checking CFD new solver...')
        self.createNewSolver()
        self.assertTrue(self.solver_object, self.__class__.__doc_name + " of new solver failed")
        self.analysis.Member += [self.solver_object]

        fccPrint('Checking CFD new physics object...')
        self.createNewPhysics()
        self.assertTrue(self.physics_object, "CfdTest of new physics object failed")
        self.analysis.Member += [self.physics_object]

        fccPrint('Checking CFD new initialise...')
        self.createNewInitialise()
        self.assertTrue(self.initialise_object, "CfdTest of new initialise failed")
        self.analysis.Member += [self.initialise_object]

        fccPrint('Checking CFD new fluid property...')
        self.createNewFluidProperty()
        self.assertTrue(self.material_object, "CfdTest of new fluid property failed")
        self.analysis.Member += [self.material_object]

        fccPrint('Checking CFD new mesh...')
        self.createNewMesh('mesh')
        self.assertTrue(self.mesh_object, "CfdTest of new mesh failed")
        self.analysis.Member += [self.mesh_object]

        fccPrint('Checking Cfd new velocity inlet boundary...')
        self.createInletBoundary()
        self.assertTrue(self.inlet_boundary, "CfdTest of new inlet boundary failed")
        self.analysis.Member += [self.inlet_boundary]

        fccPrint('Checking Cfd new velocity outlet boundary...')
        self.createOutletBoundary()
        self.assertTrue(self.outlet_boundary, "CfdTest of new outlet boundary failed")
        self.analysis.Member += [self.outlet_boundary]

        fccPrint('Checking Cfd new wall boundary...')
        self.createWallBoundary()
        self.assertTrue(self.wall_boundary, "CfdTest of new wall boundary failed")
        self.analysis.Member += [self.wall_boundary]

        fccPrint('Checking Cfd new slip boundary...')
        self.createSlipBoundary()
        self.assertTrue(self.slip_boundary, "CfdTest of new slip boundary failed")
        # self.analysis.Member = self.analysis.Member + [self.slip_boundary]
        self.analysis.Member += [self.slip_boundary]

        fccPrint('Write Cfd input files...')
        self.writeInputFiles()

        fccPrint('--------------- End of CFD tests ---------------')

    def tearDown(self):
        FreeCAD.closeDocument(self.__class__.__doc_name)
        pass

