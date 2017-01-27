# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2017 - Johan Heyns <jheyns@csir.co.za>                  *
# *   Copyright (c) 2017 - Oliver Oxtoby <ooxtoby@csir.co.za>               *
# *   Copyright (c) 2017 - Alfred Bogaers <abogaers@csir.co.za>             *
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

import CfdAnalysis
import CfdSolverFoam
import CfdPhysicsSelection
import CfdInitialiseFlowField
import CfdFluidMaterial

# import csv
import tempfile
import unittest

__title__ = "CFD unit test"
__author__ = "AB, JH, OO"
__url__ = "http://www.freecadweb.org"



''' Unit tests for the CFD WB

To run the test execute the following in the FreeCAD console:

import unittest
suite = unittest.TestSuite()
suite.addTest(unittest.defaultTestLoader.loadTestsFromName("TestCfd"))
r = unittest.TextTestRunner()
r.run(suite)

'''

mesh_name = 'Mesh'

home_path = FreeCAD.getHomePath()
temp_dir = tempfile.gettempdir()
# test_file_dir = home_path + 'Mod/Fem/test_files/ccx'


def fcc_print(message):
    FreeCAD.Console.PrintMessage('{} \n'.format(message))


class CfdTest(unittest.TestCase):

    def setUp(self):
        try:
            FreeCAD.setActiveDocument("CfdTest")
        except:
            FreeCAD.newDocument("CfdTest")
        finally:
            FreeCAD.setActiveDocument("CfdTest")
        self.active_doc = FreeCAD.ActiveDocument
        self.box = self.active_doc.addObject("Part::Box", "Box")
        self.active_doc.recompute()

    def create_new_analysis(self):
        self.analysis = CfdAnalysis.makeCfdAnalysis('CfdAnalysis')
        self.active_doc.recompute()

    def create_new_solver(self):
        self.solver_object = CfdSolverFoam.makeCfdSolverFoam()
        self.solver_object.EndTime = 100
        self.solver_object.ConvergenceCriteria = 0.001
        self.solver_object.Parallel = False
        # print ('Installation directory: {}'.format(self.solver_object.InstallationPath))
        self.active_doc.recompute()

    def create_new_physics(self):
        self.physics_object = CfdPhysicsSelection.makeCfdPhysicsSelection()
        self.active_doc.recompute()

    def create_new_initialise(self):
        self.initialise_object = CfdInitialiseFlowField.makeCfdInitialFlowField()
        self.active_doc.recompute()

    def create_new_fluid_property(self):
        self.property_object = CfdFluidMaterial.makeCfdFluidMaterial('CfdFluidProperties')
        self.active_doc.recompute()


    def test_new_analysis(self):
        fcc_print('--------------- Start of CFD tests ---------------')
        fcc_print('Checking CFD new analysis...')
        self.create_new_analysis()
        self.assertTrue(self.analysis, "CfdTest of new analysis failed")

        fcc_print('Checking CFD new solver...')
        self.create_new_solver()
        self.assertTrue(self.solver_object, "CfdTest of new solver failed")
        self.analysis.Member = self.analysis.Member + [self.solver_object]

        fcc_print('Checking CFD new physics object...')
        self.create_new_physics()
        self.assertTrue(self.physics_object, "CfdTest of new physics object failed")
        self.analysis.Member = self.analysis.Member + [self.physics_object]

        fcc_print('Checking CFD new initialise...')
        self.create_new_initialise()
        self.assertTrue(self.initialise_object, "CfdTest of new initialise failed")
        self.analysis.Member = self.analysis.Member + [self.initialise_object]

        fcc_print('Checking CFD new fluid property...')
        self.create_new_fluid_property()
        self.assertTrue(self.property_object, "CfdTest of new fluid property failed")
        self.analysis.Member = self.analysis.Member + [self.property_object]

