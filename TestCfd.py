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
# import csv
import tempfile
import unittest

__title__ = "CFD unit test"
__author__ = "AB, JH, OO"
__url__ = "http://www.freecadweb.org"



''' Unit tests for the CFD WB

To run the test paste the following in the FreeCAD console:

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
        self.physics_object = CfdPhysicsSelection.makeCfdPhysicsSelection()
        self.initial_object = CfdInitialiseFlowField.makeCfdInitialFlowField()
        # self.solver_object.GeometricalNonlinearity = 'linear'
        # self.solver_object.ThermoMechSteadyState = False
        # self.solver_object.MatrixSolverType = 'default'
        # self.solver_object.IterationsControlParameterTimeUse = False
        # self.solver_object.EigenmodesCount = 10
        # self.solver_object.EigenmodeHighLimit = 1000000.0
        # self.solver_object.EigenmodeLowLimit = 0.0
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

