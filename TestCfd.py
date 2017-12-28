# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2015 - Przemo Firszt <przemo@firszt.eu>                 *
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
import CfdCaseWriterFoam

import tempfile
import unittest
import os
import shutil

__title__ = "CFD unit test"
__author__ = "AB, JH, OO"
__url__ = "http://www.freecadweb.org"

# ***************************************************************************
#                                                                           *
# CFD WB unit tests                                                         *
#                                                                           *
# Until included in Test Framework run the test in FreeCAD console:         *
#                                                                           *
#   >>> import TestCfd                                                      *
#   >>> TestCfd.runCfdUnitTests()                                           *
#                                                                           *
# Current tests:                                                            *
#                                                                           *
#   * block     -   steady, incompressible flow                             *
#                                                                           *
# ***************************************************************************


home_path = CfdTools.get_module_path()
temp_dir = tempfile.gettempdir()
test_file_dir = os.path.join(home_path, 'testFiles')
working_dir = ''
if os.path.exists('/tmp/'):
    working_dir = '/tmp/'  # Must exist for POSIX system.
elif tempfile.tempdir:
    working_dir = tempfile.tempdir


def fccPrint(message):
    FreeCAD.Console.PrintMessage('{} \n'.format(message))


class BlockTest(unittest.TestCase):
    __doc_name = 'block'
    __part_name = 'Box'
    __file_comparison = [["0", "p"],
                         ["0", "U"],
                         ["constant", "polyMesh", "boundary"],
                         ["constant", "transportProperties"],
                         ["constant", "turbulenceProperties"],
                         ["system", "controlDict"],
                         ["system", "fvSchemes"],
                         ["system", "fvSolution"]]

    def setUp(self):
        """ Load document with part. """
        print (test_file_dir)
        part_file = os.path.join(test_file_dir, 'parts', self.__class__.__doc_name + '.fcstd')
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
        self.solver_object.WorkingDir = working_dir
        self.solver_object.InputCaseName = self.__class__.__doc_name
        self.active_doc.recompute()

    def createNewPhysics(self):
        self.physics_object = CfdPhysicsSelection.makeCfdPhysicsSelection()
        phys = self.physics_object.PhysicsModel
        phys['Time'] = 'Steady'
        phys['Flow'] = 'Incompressible'
        phys['TurbulenceModel'] = 'Laminar'
        self.active_doc.recompute()

    def createNewInitialise(self):
        self.initialise_object = CfdInitialiseFlowField.makeCfdInitialFlowField()
        init_var = self.initialise_object.InitialVariables
        init_var['PotentialFoam'] = True
        self.active_doc.recompute()

    def createNewFluidProperty(self):
        self.material_object = CfdFluidMaterial.makeCfdFluidMaterial('FluidProperties')
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
        if obj.isDerivedFrom("Fem::FemMeshObject"):
            obj.ViewObject.show()
        obj.CharacteristicLengthMax = "80 mm"
        obj.ElementOrder = "1st"
        import _TaskPanelCfdMeshGmsh
        taskd = _TaskPanelCfdMeshGmsh._TaskPanelCfdMeshGmsh(obj)  # Error when ran in FreeCADCmd
        taskd.obj = vobj.Object
        taskd.runMeshProcess()
        taskd.mesh_process.waitForFinished()

    def createInletBoundary(self):
        self.inlet_boundary = CfdFluidBoundary.makeCfdFluidBoundary('inlet')
        bc_set = self.inlet_boundary.BoundarySettings
        bc_set['BoundaryType'] = 'inlet'
        bc_set['BoundarySubtype'] = 'uniformVelocity'
        bc_set['Ux'] = 1
        bc_set['Uy'] = 0
        bc_set['Uz'] = 0

        # Test addSelection and rebuild_list_references
        doc = FreeCAD.getDocument(self.__class__.__doc_name)
        obj = doc.getObject('inlet')
        vobj = obj.ViewObject
        import _TaskPanelCfdFluidBoundary
        physics_model, is_present = CfdTools.getPhysicsModel(self.analysis)
        material_objs = CfdTools.getMaterials(self.analysis)
        taskd = _TaskPanelCfdFluidBoundary.TaskPanelCfdFluidBoundary(obj, physics_model, material_objs)
        taskd.obj = vobj.Object
        taskd.selecting_references = True
        taskd.faceSelector.addSelection(doc.Name, doc.getObject(self.__class__.__part_name).Name, 'Face1')
        taskd.accept()

    def createOutletBoundary(self):
        self.outlet_boundary = CfdFluidBoundary.makeCfdFluidBoundary('outlet')
        bc_set = self.outlet_boundary.BoundarySettings
        bc_set['BoundaryType'] = 'outlet'
        bc_set['BoundarySubtype'] = 'staticPressure'
        bc_set['Pressure'] = 0.0
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

    def writeCaseFiles(self):
        print ('Write case files ...')
        self.writer = CfdCaseWriterFoam.CfdCaseWriterFoam(self.analysis)
        self.writer.write_case()

    def test_new_analysis(self):
        fccPrint('--------------- Start of CFD tests ---------------')
        fccPrint('Checking CFD {} analysis ...'.format(self.__class__.__doc_name))
        self.createNewAnalysis()
        self.assertTrue(self.analysis, "CfdTest of analysis failed")

        fccPrint('Checking CFD {} solver ...'.format(self.__class__.__doc_name))
        self.createNewSolver()
        self.assertTrue(self.solver_object, self.__class__.__doc_name + " of solver failed")
        self.analysis.addObject(self.solver_object)

        fccPrint('Checking CFD {} physics object ...'.format(self.__class__.__doc_name))
        self.createNewPhysics()
        self.assertTrue(self.physics_object, "CfdTest of physics object failed")
        self.analysis.addObject(self.physics_object)

        fccPrint('Checking CFD {} initialise ...'.format(self.__class__.__doc_name))
        self.createNewInitialise()
        self.assertTrue(self.initialise_object, "CfdTest of initialise failed")
        self.analysis.addObject(self.initialise_object)

        fccPrint('Checking CFD {} fluid property ...'.format(self.__class__.__doc_name))
        self.createNewFluidProperty()
        self.assertTrue(self.material_object, "CfdTest of fluid property failed")
        self.analysis.addObject(self.material_object)

        fccPrint('Checking CFD {} mesh ...'.format(self.__class__.__doc_name))
        self.createNewMesh('mesh')
        self.assertTrue(self.mesh_object, "CfdTest of mesh failed")
        self.analysis.addObject(self.mesh_object)

        fccPrint('Checking Cfd {} velocity inlet boundary ...'.format(self.__class__.__doc_name))
        self.createInletBoundary()
        self.assertTrue(self.inlet_boundary, "CfdTest of inlet boundary failed")
        self.analysis.addObject(self.inlet_boundary)

        fccPrint('Checking Cfd {} velocity outlet boundary ...'.format(self.__class__.__doc_name))
        self.createOutletBoundary()
        self.assertTrue(self.outlet_boundary, "CfdTest of outlet boundary failed")
        self.analysis.addObject(self.outlet_boundary)

        fccPrint('Checking Cfd {} wall boundary ...'.format(self.__class__.__doc_name))
        self.createWallBoundary()
        self.assertTrue(self.wall_boundary, "CfdTest of wall boundary failed")
        self.analysis.addObject(self.wall_boundary)

        fccPrint('Checking Cfd {} slip boundary ...'.format(self.__class__.__doc_name))
        self.createSlipBoundary()
        self.assertTrue(self.slip_boundary, "CfdTest of slip boundary failed")
        self.analysis.addObject(self.slip_boundary)

        fccPrint('Writing {} case files ...'.format(self.__class__.__doc_name))
        self.writeCaseFiles()
        self.assertTrue(self.writer, "CfdTest of writer failed")

        # ref_dir = os.path.join(test_file_dir, "cases", self.__class__.__doc_name)
        # case_dir = os.path.join(self.solver_object.WorkingDir, self.solver_object.InputCaseName)
        #
        # for file_ext in self.__class__.__file_comparison:
        #     extension = ""
        #     for entry in file_ext:
        #         extension += "/" + entry
        #     ref_file = ref_dir + extension
        #     case_file = case_dir + extension
        #
        #     fccPrint('Comparing {} to {}'.format(ref_file, case_file))
        #     ret = compareInpFiles(ref_file, case_file)
        #     self.assertFalse(ret, "File \'{}\' test failed.\n{}".format(extension, ret))
        #
        # case_dir = os.path.join(self.solver_object.WorkingDir, self.solver_object.InputCaseName)
        # shutil.rmtree(case_dir)

        fccPrint('--------------- End of CFD tests ---------------')

    def tearDown(self):
        FreeCAD.closeDocument(self.__class__.__doc_name)
        pass


def compareInpFiles(file_name1, file_name2):
    file1 = open(file_name1, 'r')
    f1 = file1.readlines()
    file1.close()
    lf1 = [l for l in f1 if not (l.startswith('**   written ') or l.startswith('**   file '))]
    lf1 = forceUnixLineEnds(lf1)
    file2 = open(file_name2, 'r')
    f2 = file2.readlines()
    file2.close()
    lf2 = [l for l in f2 if not (l.startswith('**   written ') or l.startswith('**   file '))]
    lf2 = forceUnixLineEnds(lf2)
    import difflib
    diff = difflib.unified_diff(lf1, lf2, n=0)
    result = ''
    for l in diff:
        result += l
    if result:
        result = "Comparing {} to {} failed!\n".format(file_name1, file_name2) + result
    return result


def forceUnixLineEnds(line_list):
    new_line_list = []
    for l in line_list:
        if l.endswith("\r\n"):
            l = l[:-2] + '\n'
        new_line_list.append(l)
    return new_line_list


def runCfdUnitTests():
    suite = unittest.TestSuite()
    suite.addTest(unittest.defaultTestLoader.loadTestsFromName("TestCfd"))
    r = unittest.TextTestRunner()
    r.run(suite)
