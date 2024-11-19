# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2015 - Przemo Firszt <przemo@firszt.eu>                 *
# *   Copyright (c) 2017 Johan Heyns (CSIR) <jheyns@csir.co.za>             *
# *   Copyright (c) 2017 Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>          *
# *   Copyright (c) 2017 Alfred Bogaers (CSIR) <abogaers@csir.co.za>        *
# *   Copyright (c) 2021-2024 Oliver Oxtoby <oliveroxtoby@gmail.com>        *
# *   Copyright (c) 2022 Jonathan Bergh <bergh.jonathan@gmail.com>          *
# *                                                                         *
# *   This program is free software: you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License as        *
# *   published by the Free Software Foundation, either version 3 of the    *
# *   License, or (at your option) any later version.                       *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Lesser General Public License for more details.                   *
# *                                                                         *
# *   You should have received a copy of the GNU Lesser General Public      *
# *   License along with this program.  If not,                             *
# *   see <https://www.gnu.org/licenses/>.                                  *
# *                                                                         *
# ***************************************************************************

import FreeCAD
import FreeCADGui

from CfdOF import CfdAnalysis as CfdAnalysis
from CfdOF.Solve import CfdSolverFoam
from CfdOF.Solve import CfdPhysicsSelection
from CfdOF.Solve import CfdInitialiseFlowField
from CfdOF.Solve import CfdFluidMaterial
from CfdOF.Mesh import CfdMesh
from CfdOF.Solve import CfdFluidBoundary
from CfdOF import CfdTools
from CfdOF.Solve import CfdCaseWriterFoam
from CfdOF.Mesh import CfdMeshTools
from CfdOF.Solve import CfdRunnableFoam

import tempfile
import unittest
import os
import shutil

# ***************************************************************************
#                                                                           *
# CFD WB unit tests                                                         *
#                                                                           *
# To run:                                                                   *
#   * From command line: FreeCAD -t TestCfdOF                               *
#   * From GUI: 'Test framework' Workbench -> Self-test -> 'TestCfdOF'      *
#                                                                           *
# ***************************************************************************


home_path = CfdTools.getModulePath()
temp_dir = tempfile.gettempdir()
test_file_dir = os.path.join(home_path, 'Data', 'TestFiles')


def fccPrint(message):
    FreeCAD.Console.PrintMessage('{} \n'.format(message))


class BlockTest(unittest.TestCase):
    __doc_name = 'block'
    __part_name = 'Box'

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
        CfdTools.setActiveAnalysis(self.analysis)
        self.active_doc.recompute()

    def createNewSolver(self):
        self.solver_object = CfdSolverFoam.makeCfdSolverFoam()
        self.analysis.addObject(self.solver_object)
        self.solver_object.EndTime = 100
        self.solver_object.ConvergenceTol = 0.001
        self.solver_object.Parallel = False
        self.active_doc.recompute()

    def createNewPhysics(self):
        self.physics_object = CfdPhysicsSelection.makeCfdPhysicsSelection()
        self.analysis.addObject(self.physics_object)
        phys = self.physics_object
        phys.Time = 'Steady'
        phys.Flow = 'Isothermal'
        phys.Turbulence = 'Laminar'
        self.active_doc.recompute()

    def createNewInitialise(self):
        self.initialise_object = CfdInitialiseFlowField.makeCfdInitialFlowField()
        self.analysis.addObject(self.initialise_object)
        init_var = self.initialise_object
        init_var.PotentialFlowP = True
        init_var.UseOutletPValue = False
        self.active_doc.recompute()

    def createNewFluidProperty(self):
        self.material_object = CfdFluidMaterial.makeCfdFluidMaterial('FluidProperties')
        self.analysis.addObject(self.material_object)
        mat = self.material_object.Material
        mat['Name'] = 'None'
        mat['Density'] = '1.20 kg/m^3'
        mat['DynamicViscosity'] = '0.000018 kg/m/s'
        self.active_doc.recompute()

    def createNewMesh(self, mesh_name):
        self.mesh_object = CfdMesh.makeCfdMesh(mesh_name)
        self.analysis.addObject(self.mesh_object)
        doc = FreeCAD.getDocument(self.__class__.__doc_name)
        obj = doc.getObject(mesh_name)
        obj.Part = doc.getObject(self.__class__.__part_name)
        if obj.isDerivedFrom("Fem::FemMeshObject"):
            obj.ViewObject.show()
        obj.CharacteristicLengthMax = "80 mm"
        obj.MeshUtility = "gmsh"
        obj.ElementDimension = "3D"

    def createInletBoundary(self):
        self.inlet_boundary = CfdFluidBoundary.makeCfdFluidBoundary('inlet')
        self.analysis.addObject(self.inlet_boundary)
        bc_set = self.inlet_boundary
        bc_set.BoundaryType = 'inlet'
        bc_set.BoundarySubType = 'uniformVelocityInlet'
        bc_set.Ux = 1
        bc_set.Uy = 0
        bc_set.Uz = 0

        # Test addSelection and rebuild_list_references
        doc = FreeCAD.getDocument(self.__class__.__doc_name)
        obj = doc.getObject('inlet')
        vobj = obj.ViewObject
        from CfdOF.Solve import TaskPanelCfdFluidBoundary
        physics_model = CfdTools.getPhysicsModel(self.analysis)
        material_objs = CfdTools.getMaterials(self.analysis)
        taskd = TaskPanelCfdFluidBoundary.TaskPanelCfdFluidBoundary(obj, physics_model, material_objs)
        taskd.selecting_references = True
        taskd.faceSelector.addSelection(doc.Name, self.__class__.__part_name, 'Face1')
        # Give scheduled recompute a chance to happen
        FreeCADGui.updateGui()
        taskd.accept()

    def createOutletBoundary(self):
        self.outlet_boundary = CfdFluidBoundary.makeCfdFluidBoundary('outlet')
        self.analysis.addObject(self.outlet_boundary)
        bc_set = self.outlet_boundary
        bc_set.BoundaryType = 'outlet'
        bc_set.BoundarySubType = 'staticPressureOutlet'
        bc_set.Pressure = 0.0
        doc = FreeCAD.getDocument(self.__class__.__doc_name)
        obj = doc.getObject('Box')
        self.outlet_boundary.ShapeRefs = [(obj, ('Face4'))]
        FreeCADGui.doCommand("FreeCAD.getDocument('"+self.__class__.__doc_name+"').recompute()")

    def createWallBoundary(self):
        self.wall_boundary = CfdFluidBoundary.makeCfdFluidBoundary('wall')
        self.analysis.addObject(self.wall_boundary)
        bc_set = self.wall_boundary
        bc_set.BoundaryType = 'wall'
        bc_set.BoundarySubType = 'fixedWall'
        doc = FreeCAD.getDocument(self.__class__.__doc_name)
        obj = doc.getObject('Box')
        self.wall_boundary.ShapeRefs = [(obj, ('Face2', 'Face3'))]
        FreeCADGui.doCommand("FreeCAD.getDocument('"+self.__class__.__doc_name+"').recompute()")

    def createSlipBoundary(self):
        self.slip_boundary = CfdFluidBoundary.makeCfdFluidBoundary('slip')
        self.analysis.addObject(self.slip_boundary)
        bc_set = self.slip_boundary
        bc_set.BoundaryType = 'wall'
        bc_set.BoundarySubType = 'slipWall'
        doc = FreeCAD.getDocument(self.__class__.__doc_name)
        obj = doc.getObject('Box')
        self.slip_boundary.ShapeRefs = [(obj, ('Face5', 'Face6'))]
        FreeCADGui.doCommand("FreeCAD.getDocument('"+self.__class__.__doc_name+"').recompute()")

    def writeCaseFiles(self):
        print ('Write mesh files ...')
        from CfdOF.Mesh import TaskPanelCfdMesh
        taskd = TaskPanelCfdMesh.TaskPanelCfdMesh(self.mesh_object)
        taskd.obj = self.mesh_object.ViewObject
        taskd.writeMesh()
        taskd.closed()

        print ('Write case files ...')
        from CfdOF.Solve import TaskPanelCfdSolverControl
        solver_runner = CfdRunnableFoam.CfdRunnableFoam(self.analysis, self.solver_object)
        taskd = TaskPanelCfdSolverControl.TaskPanelCfdSolverControl(solver_runner)
        taskd.obj = self.solver_object.ViewObject
        taskd.write_input_file_handler()
        taskd.closing()

    def test_new_analysis(self):
        # Unset the appending of the document name to the output path to get a predictable place where
        # files are stored
        prefs = CfdTools.getPreferencesLocation()
        original_append_setting = FreeCAD.ParamGet(prefs).GetBool("AppendDocNameToOutputPath", 0)
        FreeCAD.ParamGet(prefs).SetBool("AppendDocNameToOutputPath", 0)

        fccPrint('--------------- Start of CFD tests ---------------')
        fccPrint('Checking CFD {} analysis ...'.format(self.__class__.__doc_name))
        self.createNewAnalysis()
        self.assertTrue(self.analysis, "CfdTest of analysis failed")

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

        fccPrint('Checking CFD {} mesh ...'.format(self.__class__.__doc_name))
        self.createNewMesh('mesh')
        self.assertTrue(self.mesh_object, "CfdTest of mesh failed")
        self.analysis.addObject(self.mesh_object)

        fccPrint('Checking CFD {} solver ...'.format(self.__class__.__doc_name))
        self.createNewSolver()
        self.assertTrue(self.solver_object, self.__class__.__doc_name + " of solver failed")
        self.analysis.addObject(self.solver_object)

        fccPrint('Writing {} case files ...'.format(self.__class__.__doc_name))
        self.analysis.OutputPath = temp_dir
        self.solver_object.InputCaseName = "case" + self.__class__.__doc_name
        self.mesh_object.CaseName = "meshCase" + self.__class__.__doc_name
        self.writeCaseFiles()

        mesh_ref_dir = os.path.join(test_file_dir, "cases", self.__class__.__doc_name, "meshCase")
        mesh_case_dir = os.path.join(CfdTools.getOutputPath(self.analysis), self.mesh_object.CaseName)
        ref_dir = os.path.join(test_file_dir, "cases", self.__class__.__doc_name, "case")
        case_dir = os.path.join(CfdTools.getOutputPath(self.analysis), self.solver_object.InputCaseName)

        comparePaths(mesh_ref_dir, mesh_case_dir, self)
        comparePaths(ref_dir, case_dir, self)

        fccPrint('--------------- End of CFD tests ---------------')

        FreeCAD.ParamGet(prefs).SetBool("AppendDocNameToOutputPath", original_append_setting)

    def tearDown(self):
        FreeCAD.closeDocument(self.__class__.__doc_name)


class MacroTest:
    """ Base class for macro-based regression tests below """

    def __init__(self, var):
        self.child_instance = None

    def writeCaseFiles(self):
        analysis = CfdTools.getActiveAnalysis()
        self.meshwriter = CfdMeshTools.CfdMeshTools(CfdTools.getMeshObject(analysis))
        self.meshwriter.writeMesh()

        self.writer = CfdCaseWriterFoam.CfdCaseWriterFoam(FreeCAD.ActiveDocument.CfdAnalysis)
        self.writer.writeCase()

    def runTest(self, dir_name, macro_names):
        # Unset the appending of the document name to the output path to get a predictable place where
        # files are stored
        prefs = CfdTools.getPreferencesLocation()
        original_append_setting = FreeCAD.ParamGet(prefs).GetBool("AppendDocNameToOutputPath", 0)
        FreeCAD.ParamGet(prefs).SetBool("AppendDocNameToOutputPath", 0);

        fccPrint('--------------- Start of CFD tests ---------------')
        for m in macro_names:
            macro_name = os.path.join(home_path, "Demos", dir_name, m)
            fccPrint('Running {} macro {} ...'.format(dir_name, macro_name))
            CfdTools.executeMacro(macro_name)

        fccPrint('Writing {} case files ...'.format(dir_name))
        analysis = CfdTools.getActiveAnalysis()
        analysis.OutputPath = temp_dir
        CfdTools.getSolver(analysis).InputCaseName = "case" + dir_name
        CfdTools.getMeshObject(analysis).CaseName = "meshCase" + dir_name
        self.writeCaseFiles()
        self.child_instance.assertTrue(self.writer, "CfdTest of writer failed")

        mesh_ref_dir = os.path.join(test_file_dir, "cases", dir_name, "meshCase")
        mesh_case_dir = self.meshwriter.meshCaseDir
        comparePaths(mesh_ref_dir, mesh_case_dir, self.child_instance)

        ref_dir = os.path.join(test_file_dir, "cases", dir_name, "case")
        case_dir = self.writer.case_folder
        comparePaths(ref_dir, case_dir, self.child_instance)

        fccPrint('--------------- End of CFD tests ---------------')

        FreeCAD.ParamGet(prefs).SetBool("AppendDocNameToOutputPath", original_append_setting)

    def closeDoc(self):
        FreeCAD.closeDocument(FreeCAD.ActiveDocument.Name)


class ElbowTest(unittest.TestCase, MacroTest):
    __dir_name = 'Elbow'
    __macros = ['elbow.FCMacro']

    def __init__(self, var):
        super().__init__(var)
        MacroTest.child_instance = self

    def test_run(self):
        self.runTest(self.__class__.__dir_name, self.__class__.__macros)

    def tearDown(self):
        self.closeDoc()


class DuctTest(unittest.TestCase, MacroTest):
    __dir_name = 'Duct'
    __macros = ['01-geom.FCMacro', '02-mesh.FCMacro', '03-porous.FCMacro', '04-screen.FCMacro']

    def __init__(self, var):
        super().__init__(var)
        MacroTest.child_instance = self

    def test_run(self):
        self.runTest(self.__class__.__dir_name, self.__class__.__macros)

    def tearDown(self):
        self.closeDoc()


class ViscousTubeBundleTest(unittest.TestCase, MacroTest):
    __dir_name = 'ViscousTubeBundle'
    __macros = ['viscousTubeBundle.FCMacro']

    def __init__(self, var):
        super().__init__(var)
        MacroTest.child_instance = self

    def test_run(self):
        self.runTest(self.__class__.__dir_name, self.__class__.__macros)

    def tearDown(self):
        self.closeDoc()


class UAVTest(unittest.TestCase, MacroTest):
    __dir_name = 'UAV'
    __macros = ['01-partDesign.FCMacro', '02-firstAnalysis.FCMacro', '03-refineMesh.FCMacro']

    def __init__(self, var):
        super().__init__(var)
        MacroTest.child_instance = self

    def test_run(self):
        self.runTest(self.__class__.__dir_name, self.__class__.__macros)

    def tearDown(self):
        self.closeDoc()


class ProjectileTest(unittest.TestCase, MacroTest):
    __dir_name = 'Projectile'
    __macros = ['01-geometry.FCMacro', '02-mesh.FCMacro', '03-boundaries.FCMacro', '04-forceCoeffs.FCMacro']

    def __init__(self, var):
        super().__init__(var)
        MacroTest.child_instance = self

    def test_run(self):
        self.runTest(self.__class__.__dir_name, self.__class__.__macros)

    def tearDown(self):
        self.closeDoc()


class LESStepTest(unittest.TestCase, MacroTest):
    __dir_name = 'LESStep'
    __macros = ['backwardStep.FCMacro']

    def __init__(self, var):
        super().__init__(var)
        MacroTest.child_instance = self

    def test_run(self):
        self.runTest(self.__class__.__dir_name, self.__class__.__macros)

    def tearDown(self):
        self.closeDoc()


class DamBreak3DTest(unittest.TestCase, MacroTest):
    __dir_name = 'DamBreak3D'
    __macros = ['01-geom.FCMacro', '02-analysis.FCMacro', '03-probes.FCMacro','04-adaptiveMesh.FCMacro']

    def __init__(self, var):
        super().__init__(var)
        MacroTest.child_instance = self

    def test_run(self):
        self.runTest(self.__class__.__dir_name, self.__class__.__macros)

    def tearDown(self):
        self.closeDoc()


def compareInpFiles(file_name1, file_name2):
    file1 = open(file_name1, 'r')
    f1 = file1.readlines()
    file1.close()
    lf1 = [l for l in f1 if not l.startswith("FOAMDIR=") and not l.startswith("GMSH_EXE=")
           and not l.startswith("set FOAMDIR") and not l.startswith("call %FOAMDIR%") and not l.startswith("$GMSH_EXE")]
    lf1 = forceUnixLineEnds(lf1)
    file2 = open(file_name2, 'r')
    f2 = file2.readlines()
    file2.close()
    lf2 = [l for l in f2 if not l.startswith("FOAMDIR=") and not l.startswith("GMSH_EXE=")
           and not l.startswith("set FOAMDIR") and not l.startswith("call %FOAMDIR%") and not l.startswith("$GMSH_EXE")]
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


def comparePaths(ref_dir, case_dir, unit_test):
    """ Compares every file in ref_dir to corresponding one in case_dir """
    fccPrint("Comparing files in {} to those in {}".format(case_dir, ref_dir))
    unit_test.assertTrue(os.path.exists(ref_dir))
    for path, directories, files in os.walk(ref_dir):
        for file in files:
            ref_file = os.path.join(path, file)
            case_file = os.path.join(case_dir, os.path.relpath(path, ref_dir), file)
            fccPrint('Comparing {} to {}'.format(ref_file, case_file))
            ret = compareInpFiles(ref_file, case_file)
            unit_test.assertFalse(ret, "File \'{}\' test failed.\n{}".format(file, ret))


def updateReferenceDirectory(ref_dir, case_dir):
    """ For every file in ref_dir, copy the corresponding one in case_dir """
    """ over to ref_dir """
    fccPrint("Updating files in {} from those in {}".format(case_dir, ref_dir))
    for path, directories, files in os.walk(ref_dir):
        for file in files:
            ref_file = os.path.join(path, file)
            case_file = os.path.join(case_dir, os.path.relpath(path, ref_dir), file)
            #fccPrint('Copying {} to {}'.format(case_file, ref_file))
            shutil.copyfile(case_file, ref_file)


def runCfdUnitTests():
    suite = unittest.TestSuite()
    suite.addTest(unittest.defaultTestLoader.loadTestsFromName("TestCfdOF"))
    r = unittest.TextTestRunner()
    r.run(suite)


def updateReferenceFiles():
    """ Update all the reference files with those from runs just completed """

    for item in os.scandir(os.path.join(test_file_dir, "cases")):
        if item.is_dir():
            dir_name = item.name
            mesh_ref_dir = os.path.join(test_file_dir, "cases", dir_name, "meshCase")
            mesh_case_dir = os.path.join(temp_dir, "meshCase"+dir_name)
            if os.path.exists(mesh_case_dir):
                updateReferenceDirectory(mesh_ref_dir, mesh_case_dir)
            else:
                fccPrint("Test output data not found in {} - skipping".format(mesh_case_dir))

            ref_dir = os.path.join(test_file_dir, "cases", dir_name, "case")
            case_dir = os.path.join(temp_dir, "case"+dir_name)
            if os.path.exists(case_dir):
                updateReferenceDirectory(ref_dir, case_dir)
            else:
                fccPrint("Test output data not found in {} - skipping".format(case_dir))


def cleanCfdUnitTests():
    """ Clean up unit test data from temporary directory """

    for path, directories, files in os.walk(test_file_dir):
        for dir_name in directories:
            mesh_case_dir = os.path.join(temp_dir, "meshCase"+dir_name)
            if os.path.exists(mesh_case_dir):
                fccPrint("Cleaning directory {}".format(mesh_case_dir))
                shutil.rmtree(mesh_case_dir)

            case_dir = os.path.join(temp_dir, "case"+dir_name)
            if os.path.exists(case_dir):
                fccPrint("Cleaning directory {}".format(case_dir))
                shutil.rmtree(case_dir)
