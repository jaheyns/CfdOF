# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: © 2015 Przemo Firszt <przemo@firszt.eu>
# SPDX-FileCopyrightText: © 2017 Johan Heyns (CSIR) <jheyns@csir.co.za>
# SPDX-FileCopyrightText: © 2017 Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>
# SPDX-FileCopyrightText: © 2017 Alfred Bogaers (CSIR) <abogaers@csir.co.za>
# SPDX-FileCopyrightText: © 2021 Oliver Oxtoby <oliveroxtoby@gmail.com>
# SPDX-FileCopyrightText: © 2022 Jonathan Bergh <bergh.jonathan@gmail.com>
# SPDX-FileNotice: Part of the CfdOF addon.

################################################################################
#                                                                              #
#   This program is free software; you can redistribute it and/or              #
#   modify it under the terms of the GNU Lesser General Public                 #
#   License as published by the Free Software Foundation; either               #
#   version 3 of the License, or (at your option) any later version.           #
#                                                                              #
#   This program is distributed in the hope that it will be useful,            #
#   but WITHOUT ANY WARRANTY; without even the implied warranty of             #
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.                       #
#                                                                              #
#   See the GNU Lesser General Public License for more details.                #
#                                                                              #
#   You should have received a copy of the GNU Lesser General Public License   #
#   along with this program; if not, write to the Free Software Foundation,    #
#   Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.        #
#                                                                              #
################################################################################

import FreeCAD
import FreeCADGui

from CfdOF import CfdAnalysis as CfdAnalysis
from CfdOF.Solve import CfdSolverFoam
from CfdOF.Solve import CfdPhysicsSelection
from CfdOF.Solve import CfdInitialiseFlowField
from CfdOF.Solve import CfdFluidMaterial
from CfdOF.Mesh import CfdMesh
from CfdOF.Solve import CfdFluidBoundary
from CfdOF.Solve import CfdRegionCoupledInterface
from CfdOF import CfdTools
from CfdOF.Solve import CfdCaseWriterFoam
from CfdOF.Mesh import CfdMeshTools
from CfdOF.Solve import CfdRunnableFoam

import tempfile
import unittest
import os
import re
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
temp_dir = CfdTools.getDefaultOutputPath()
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

    def test_fluid_boundary_has_no_region_override(self):
        boundary = CfdFluidBoundary.makeCfdFluidBoundary('boundary')
        self.assertNotIn('RegionName', boundary.PropertiesList)

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
        self.assertNotIn('RegionName', bc_set.PropertiesList)
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

    def runTest(self, dir_name, macro_names, case_name=None):
        if case_name is None:
            case_name = dir_name

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
        CfdTools.getSolver(analysis).InputCaseName = "case" + case_name
        CfdTools.getMeshObject(analysis).CaseName = "meshCase" + case_name
        self.writeCaseFiles()
        self.child_instance.assertTrue(self.writer, "CfdTest of writer failed")

        mesh_ref_dir = os.path.join(test_file_dir, "cases", case_name, "meshCase")
        mesh_case_dir = self.meshwriter.mesh_case_dir
        comparePaths(mesh_ref_dir, mesh_case_dir, self.child_instance)

        ref_dir = os.path.join(test_file_dir, "cases", case_name, "case")
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
    __macros = ['01-partDesign.FCMacro', '02-firstAnalysis.FCMacro', '03-refineMesh.FCMacro',  '04-forces.FCMacro']

    def __init__(self, var):
        super().__init__(var)
        MacroTest.child_instance = self

    def test_run(self):
        self.runTest(self.__class__.__dir_name, self.__class__.__macros)

    def tearDown(self):
        self.closeDoc()


class BatteryCoolingTest(unittest.TestCase, MacroTest):
    __dir_name = 'BatteryCooling'
    __macros = ['BatteryCooling.FCMacro']

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
    __macros = ['01-geom.FCMacro', '02-analysis.FCMacro', '03-mesh.FCMacro', '04-adaptiveMesh.FCMacro', '05-boundaries.FCMacro', '06-waterZone.FCMacro', '07-probes.FCMacro']

    def __init__(self, var):
        super().__init__(var)
        MacroTest.child_instance = self

    def test_run(self):
        self.runTest(self.__class__.__dir_name, self.__class__.__macros)

    def tearDown(self):
        self.closeDoc()


class PropellerTest(unittest.TestCase, MacroTest):
    __dir_name = 'Propeller'
    __macros = ['01-geom.FCMacro', '02-mesh.FCMacro', '03-MovingMeshRegion.FCMacro']

    def __init__(self, var):
        super().__init__(var)
        MacroTest.child_instance = self

    def test_run(self):
        self.runTest(self.__class__.__dir_name, self.__class__.__macros)

    def tearDown(self):
        self.closeDoc()


class PeriodicBoundaryAndMeanVelocityForceTest(unittest.TestCase, MacroTest):
    __dir_name = 'PeriodicBoundaryAndMeanVelocityForce'
    __case_name = 'PeriodicBoundaryAndMeanVelocityForce'
    __macros = ['01-geom.FCMacro', '02-analysis.FCMacro', '03-mesh.FCMacro', '04-boundaryConditions.FCMacro', '05-meanVelocityForce.FCMacro']

    def __init__(self, var):
        super().__init__(var)
        MacroTest.child_instance = self

    def test_run(self):
        self.runTest(self.__class__.__dir_name, self.__class__.__macros)

    def tearDown(self):
        self.closeDoc()


class MeanVelocityForceCellZoneTest(unittest.TestCase, MacroTest):
    __dir_name = 'MeanVelocityForceCellZone'
    __case_name = 'MeanVelocityForceCellZone'
    __macros = ['01-geom.FCMacro', '02-analysis.FCMacro', '03-mesh.FCMacro', '04-boundaryConditions.FCMacro',  '05-meanVelocityForce.FCMacro']

    def __init__(self, var):
        super().__init__(var)
        MacroTest.child_instance = self

    def test_run(self):
        prefs = CfdTools.getPreferencesLocation()
        original_append_setting = FreeCAD.ParamGet(prefs).GetBool("AppendDocNameToOutputPath", 0)
        FreeCAD.ParamGet(prefs).SetBool("AppendDocNameToOutputPath", 0)

        fccPrint('--------------- Start of CFD tests ---------------')
        dir_name = self.__class__.__dir_name
        case_name = self.__class__.__case_name
        for m in self.__class__.__macros:
            macro_name = os.path.join(home_path, "Demos", dir_name, m)
            fccPrint('Running {} macro {} ...'.format(dir_name, macro_name))
            CfdTools.executeMacro(macro_name)

        fccPrint('Writing {} case files ...'.format(dir_name))
        analysis = CfdTools.getActiveAnalysis()
        if analysis is None:
            # Proxy may not be fully restored when running without GUI; find by property
            for obj in FreeCAD.ActiveDocument.Objects:
                if hasattr(obj, 'IsActiveAnalysis') and hasattr(obj, 'OutputPath'):
                    analysis = obj
                    break
        analysis.OutputPath = temp_dir
        CfdTools.getSolver(analysis).InputCaseName = "case" + case_name
        self.writer = CfdCaseWriterFoam.CfdCaseWriterFoam(analysis)
        self.writer.writeCase()
        self.assertTrue(self.writer, "CfdTest of writer failed")

        ref_dir = os.path.join(test_file_dir, "cases", case_name, "case")
        case_dir = self.writer.case_folder
        comparePaths(ref_dir, case_dir, self)

        fccPrint('--------------- End of CFD tests ---------------')

        FreeCAD.ParamGet(prefs).SetBool("AppendDocNameToOutputPath", original_append_setting)

    def tearDown(self):
        self.closeDoc()

class WaterPouringTest(unittest.TestCase, MacroTest):
    __dir_name = 'WaterPouring'
    __macros = ['01-geom.FCMacro', '02-analysis.FCMacro', '03-boundaryConditions.FCMacro', '04-initializeWaterZone.FCMacro', '05-mesh.FCMacro', '06-movingMeshRegion.FCMacro', '07-meshRefinement.FCMacro']

    def __init__(self, var):
        super().__init__(var)
        MacroTest.child_instance = self

    def test_run(self):
        self.runTest(self.__class__.__dir_name, self.__class__.__macros)

    def tearDown(self):
        self.closeDoc()


class SimpleHeatFinTest(unittest.TestCase, MacroTest):
    __dir_name = os.path.join('ConjugatedHeatTransferSteadyState', 'simple_heat_fin')
    __case_name = 'SimpleHeatFin'
    __macros = ['01-geometry.FCMacro', '02-analysis.FCMacro', '03-mesh.FCMacro', '04-boundaries.FCMacro',
                '05-solidMaterial.FCMacro']

    def __init__(self, var):
        super().__init__(var)
        MacroTest.child_instance = self

    def test_run(self):
        self.runTest(self.__class__.__dir_name, self.__class__.__macros, self.__class__.__case_name)
        pressure_file = os.path.join(self.writer.case_folder, '0', 'FluidProperties', 'p')
        with open(pressure_file) as fid:
            pressure = fid.read()
        self.assertIsNone(re.search(r'boundaryField\s*\{\s*\{', pressure))
        for patch in ('wall001', 'inlet', 'outlet'):
            self.assertRegex(pressure, r'\n\s*' + patch + r'\s*\n\s*\{')

    def tearDown(self):
        self.closeDoc()


class MicrochipCoolingNccMacroWorkflowTest(unittest.TestCase):
    __dir_name = os.path.join('ConjugatedHeatTransferSteadyState', 'microchip_cooling_ncc')
    __case_name = 'MicrochipCoolingNccMacroWorkflow'
    __macros = ['01-geometry.FCMacro', '02-analysis.FCMacro', '03-meshes.FCMacro', '04-boundaries.FCMacro',
                '05-solidMaterials.FCMacro', '06-meanVelocityForce.FCMacro']

    def test_run(self):
        prefs = CfdTools.getPreferencesLocation()
        original_append_setting = FreeCAD.ParamGet(prefs).GetBool("AppendDocNameToOutputPath", 0)
        FreeCAD.ParamGet(prefs).SetBool("AppendDocNameToOutputPath", 0)
        original_warning = CfdTools.cfdWarning
        original_case_message = CfdCaseWriterFoam.cfdMessage
        warnings = []
        case_messages = []

        def capture_warning(message):
            warnings.append(str(message))
            original_warning(message)

        def capture_case_message(message):
            case_messages.append(str(message))
            original_case_message(message)

        CfdTools.cfdWarning = capture_warning
        CfdCaseWriterFoam.cfdMessage = capture_case_message
        try:
            fccPrint('--------------- Start of CFD tests ---------------')
            for macro in self.__class__.__macros:
                macro_name = os.path.join(home_path, "Demos", self.__class__.__dir_name, macro)
                fccPrint('Running {} macro {} ...'.format(self.__class__.__dir_name, macro_name))
                CfdTools.executeMacro(macro_name)

            analysis = CfdTools.getActiveAnalysis()
            self.assertIsNotNone(analysis)
            analysis.OutputPath = temp_dir
            meshes = CfdTools.getMeshObjects(analysis)
            self.assertEqual(len(meshes), 5)
            self.assertEqual(
                {CfdTools.getRegionName(mesh): getattr(mesh, 'RegionType', '') for mesh in meshes},
                {
                    "room": "fluid", "PCB": "solid", "microchip": "solid",
                    "fan_case": "solid", "heat_sink": "solid",
                },
            )
            self.assertEqual(
                {mesh.Part.Name for mesh in meshes},
                {"Box_slice", "Box001_slice", "Box002_slice", "Body_slice", "Fusion_slice"},
            )
            for mesh in meshes:
                self.assertNotEqual(mesh.Part.Name, "BooleanFragments")
                self.assertEqual(getattr(mesh.Part, 'GeneratedBy', ''), "CfdOF_InterfaceNccRegions")
                self.assertTrue(mesh.Part.Shape.Solids)

            interfaces = CfdTools.getRegionCoupledInterfaceGroup(analysis)
            self.assertEqual(len(interfaces), 1)
            self.assertTrue(interfaces[0].ShapeRefs)
            self.assertTrue(interfaces[0].InterfacePairs)

            solver = CfdTools.getSolver(analysis)
            solver.InputCaseName = "case" + self.__class__.__case_name
            for mesh in meshes:
                CfdMeshTools.CfdMeshTools(mesh).writeMesh()

            writer = CfdCaseWriterFoam.CfdCaseWriterFoam(analysis)
            writer.writeCase()
            create_patch_dict = os.path.join(writer.case_folder, "system", "createPatchDict")
            self.assertTrue(os.path.exists(create_patch_dict))
            with open(create_patch_dict, 'r') as patch_file:
                create_patch_text = patch_file.read()
            for patch_name in (
                    "RegionCoupledInterface001_PCB_to_microchip",
                    "RegionCoupledInterface001_microchip_to_PCB"):
                self.assertIn(patch_name, create_patch_text)

            region_properties = os.path.join(writer.case_folder, "constant", "regionProperties")
            self.assertTrue(os.path.exists(region_properties))
            with open(region_properties, 'r') as region_file:
                region_text = region_file.read()
            for region_name in ("room", "PCB", "microchip", "fan_case", "heat_sink"):
                self.assertIn(region_name, region_text)

            conflict_warnings = [
                warning for warning in warnings
                if "also assigned as boundary" in warning or
                "ignoring duplicate" in warning or
                "No part of the boundary" in warning
            ]
            self.assertEqual(conflict_warnings, [])
            self.assertEqual([
                message for message in case_messages
                if "appears to be enclosed inside fluid body" in message
            ], [])
            fccPrint('--------------- End of CFD tests ---------------')
        finally:
            CfdTools.cfdWarning = original_warning
            CfdCaseWriterFoam.cfdMessage = original_case_message
            FreeCAD.ParamGet(prefs).SetBool("AppendDocNameToOutputPath", original_append_setting)

    def tearDown(self):
        if FreeCAD.ActiveDocument is not None:
            FreeCAD.closeDocument(FreeCAD.ActiveDocument.Name)


class InterfaceNccRegionsWorkflowTest(unittest.TestCase):
    __dir_name = os.path.join('ConjugatedHeatTransferSteadyState', 'simple_heat_fin_ncc')
    __macros = ['01-geometry.FCMacro', '02-analysis.FCMacro']

    def test_create_interface_regions(self):
        fccPrint('--------------- Start of CFD tests ---------------')
        for m in self.__class__.__macros:
            macro_name = os.path.join(home_path, "Demos", self.__class__.__dir_name, m)
            fccPrint('Running {} macro {} ...'.format(self.__class__.__dir_name, macro_name))
            CfdTools.executeMacro(macro_name)

        from CfdOF.Solve import CfdInterfaceNccRegions

        source_objects = [
            FreeCAD.ActiveDocument.FluidRegion,
            FreeCAD.ActiveDocument.SolidRegion,
        ]
        group, region_objects, interface = CfdInterfaceNccRegions.createInterfaceNccRegions(source_objects)
        analysis = CfdTools.getActiveAnalysis()

        self.assertIsNone(group)
        self.assertEqual(len(region_objects), 2)
        self.assertEqual(len(interface.RegionObjects), 2)
        self.assertTrue(interface.ShapeRefs)
        self.assertTrue(interface.InterfacePairs)
        self.assertIn(interface, analysis.Group)
        self.assertTrue(all("RegionName" not in region.PropertiesList for region in region_objects))
        for source_obj, region_obj in zip(source_objects, region_objects):
            self.assertEqual(region_obj.Name, "{}_slice".format(source_obj.Name))
            self.assertNotIn(region_obj, analysis.Group)
            self.assertTrue(region_obj.Shape.Solids)
            self.assertEqual(getattr(region_obj, 'GeneratedBy', ''), CfdInterfaceNccRegions.GENERATED_BY)
            self.assertTrue(getattr(region_obj, 'IsFinalInterfaceRegion', False))
            self.assertEqual(region_obj.SourceObject, source_obj)
            self.assertEqual(getattr(region_obj.Proxy, 'Type', ''), "FeatureSlice")
            self.assertIsNotNone(region_obj.Base)
            self.assertTrue(region_obj.Tools)
            self.assertNotEqual(region_obj.Base, source_obj)

        from CfdOF.Solve import CfdRegionCoupledInterface
        self.assertEqual(
            [CfdRegionCoupledInterface.getRegionName(region) for region in region_objects],
            ["FluidRegion", "SolidRegion"],
        )
        self.assertEqual(
            [CfdRegionCoupledInterface.getInterfaceRegionForSource(obj) for obj in source_objects],
            region_objects,
        )
        shape_refs, interface_pairs = CfdRegionCoupledInterface.generatePairedTouchingFaceData(
            [CfdRegionCoupledInterface.getInterfaceRegionForSource(obj) for obj in source_objects]
        )
        self.assertTrue(shape_refs)
        self.assertTrue(interface_pairs)
        self.assertEqual({ref_obj.Name for ref_obj, _subnames in shape_refs},
                         {region_obj.Name for region_obj in region_objects})
        decoded_pairs = CfdRegionCoupledInterface._decode_interface_pairs(interface)
        self.assertTrue(decoded_pairs)
        self.assertEqual(
            {pair['thermal_type'] for pair in decoded_pairs},
            {"zeroGradient"},
        )
        for pair_index in range(len(decoded_pairs)):
            self.assertTrue(CfdRegionCoupledInterface.updateInterfacePairThermalType(
                interface,
                pair_index,
                "fixedValue",
            ))
        self.assertEqual(
            {pair['thermal_value'] for pair in CfdRegionCoupledInterface._decode_interface_pairs(interface)},
            {str(interface.Temperature)},
        )
        generated_boundaries = interface.Proxy.makeBoundaryObjects(interface)
        self.assertEqual(
            {boundary.ThermalBoundaryType for boundary in generated_boundaries},
            {"fixedValue"},
        )
        self.assertEqual(
            {str(boundary.Temperature) for boundary in generated_boundaries},
            {str(interface.Temperature)},
        )
        self.assertEqual(len(generated_boundaries), 2 * len(decoded_pairs))
        self.assertTrue(CfdRegionCoupledInterface.updateInterfacePairThermalType(
            interface,
            0,
            "fixedGradient",
        ))
        self.assertIn(
            "W/m^2",
            CfdRegionCoupledInterface._decode_interface_pairs(interface)[0]['thermal_value'],
        )

        if FreeCAD.GuiUp:
            interface.RegionObjects = region_objects
            interface.RegionNames = [CfdRegionCoupledInterface.getRegionName(region_obj) for region_obj in region_objects]
            interface.ShapeRefs = CfdInterfaceNccRegions.generateInterfaceFaceRefs(region_objects)
            interface.InterfacePairs = interface_pairs
            from CfdOF.Solve import TaskPanelCfdRegionCoupledInterface
            task_panel = TaskPanelCfdRegionCoupledInterface.TaskPanelCfdRegionCoupledInterface(interface)
            self.assertEqual(task_panel.faceTable.columnCount(), 4)
            self.assertEqual(
                task_panel.faceTable.cellWidget(0, 2).currentText(),
                "zeroGradient",
            )
            self.assertEqual(task_panel.faceTable.item(0, 3).text(), "")
            task_panel.faceTable.cellWidget(0, 2).setCurrentIndex(
                task_panel.faceTable.cellWidget(0, 2).findText("fixedValue")
            )
            self.assertEqual(
                CfdRegionCoupledInterface._decode_interface_pairs(interface)[0]['thermal_type'],
                "fixedValue",
            )
            self.assertEqual(
                task_panel.faceTable.item(0, 3).text(),
                str(interface.Temperature),
            )
            task_panel.faceTable.item(0, 3).setText("350 K")
            self.assertEqual(
                CfdRegionCoupledInterface._decode_interface_pairs(interface)[0]['thermal_value'],
                "350 K",
            )
            self.assertEqual(task_panel.selectFaceButton.text(), "Select face")
            self.assertEqual(task_panel.removeFaceButton.text(), "Remove face")
            self.assertEqual(task_panel.addPairButton.text(), "Add pair")
            self.assertEqual(task_panel.removePairButton.text(), "Remove pair")
            initial_pair_count = task_panel.faceTable.rowCount()
            task_panel.addInterfacePair()
            self.assertEqual(task_panel.faceTable.rowCount(), initial_pair_count + 1)
            added_row = task_panel.faceTable.rowCount() - 1
            self.assertTrue(task_panel._setInterfacePairFace(
                added_row,
                0,
                region_objects[0],
                interface.ShapeRefs[0][1][0],
            ))
            self.assertTrue(
                CfdRegionCoupledInterface._decode_interface_pairs(interface)[added_row]['face_a']
            )
            task_panel.faceTable.setCurrentCell(added_row, 0)
            task_panel.removeSelectedInterfaceFaceCell()
            self.assertEqual(
                CfdRegionCoupledInterface._decode_interface_pairs(interface)[added_row]['face_a'],
                '',
            )
            task_panel.faceTable.selectRow(added_row)
            task_panel.removeSelectedInterfacePairs()
            self.assertEqual(task_panel.faceTable.rowCount(), initial_pair_count)
            self.assertEqual({(ref_obj.Name, subname) for ref_obj, subnames in interface.ShapeRefs
                              for subname in subnames},
                             {(pair_obj.Name, face_name)
                              for pair_entry in CfdRegionCoupledInterface._decode_interface_pairs(interface)
                              for pair_obj, face_name in (
                                  (interface.Document.getObject(pair_entry['object_a']), pair_entry['face_a']),
                                  (interface.Document.getObject(pair_entry['object_b']), pair_entry['face_b']),
                              )})
            task_panel.form.close()

            interface.RegionObjects = source_objects
            interface.RegionNames = [source_obj.Label for source_obj in source_objects]
            interface.ShapeRefs = [(source_objects[0], ("Face1",))]
            interface.InterfacePairs = []
            task_panel = TaskPanelCfdRegionCoupledInterface.TaskPanelCfdRegionCoupledInterface(interface)
            self.assertEqual(list(interface.RegionObjects), region_objects)
            self.assertEqual({ref_obj.Name for ref_obj, _subnames in interface.ShapeRefs},
                             {region_obj.Name for region_obj in region_objects})
            self.assertTrue(interface.InterfacePairs)
            task_panel.form.close()

        fccPrint('--------------- End of CFD tests ---------------')

    def test_regeneration_preserves_region_references(self):
        fccPrint('--------------- Start of CFD tests ---------------')
        for m in self.__class__.__macros:
            macro_name = os.path.join(home_path, "Demos", self.__class__.__dir_name, m)
            fccPrint('Running {} macro {} ...'.format(self.__class__.__dir_name, macro_name))
            CfdTools.executeMacro(macro_name)

        from CfdOF.Mesh import CfdMesh
        from CfdOF.Solve import CfdFluidBoundary
        from CfdOF.Solve import CfdInterfaceNccRegions
        from CfdOF.Solve import CfdSolidMaterial

        doc = FreeCAD.ActiveDocument
        analysis = CfdTools.getActiveAnalysis()
        source_objects = [doc.FluidRegion, doc.SolidRegion]
        _group, region_objects, interface = CfdInterfaceNccRegions.createInterfaceNccRegions(source_objects)
        regions = {region.SourceObject.Name: region for region in region_objects}
        fluid_region = regions[doc.FluidRegion.Name]
        solid_region = regions[doc.SolidRegion.Name]

        mesh = CfdMesh.makeCfdMesh("RegenerationMesh")
        analysis.addObject(mesh)
        mesh.Part = fluid_region

        solid_material = CfdSolidMaterial.makeCfdSolidMaterial("RegenerationSolid")
        analysis.addObject(solid_material)
        solid_material.ShapeRefs = [(solid_region, ("Solid1",))]
        self.assertNotIn("RegionName", solid_material.PropertiesList)

        interface_faces = {
            subname for ref_obj, subnames in interface.ShapeRefs
            if ref_obj is fluid_region for subname in subnames
        }
        boundary_face_name = next(
            "Face{}".format(face_index)
            for face_index in range(1, len(fluid_region.Shape.Faces) + 1)
            if "Face{}".format(face_index) not in interface_faces
        )
        old_boundary_face = fluid_region.Shape.getElement(boundary_face_name).copy()
        boundary = CfdFluidBoundary.makeCfdFluidBoundary("RegenerationBoundary")
        analysis.addObject(boundary)
        boundary.ShapeRefs = [(fluid_region, (boundary_face_name,))]

        analysis.NeedsMeshRewrite = False
        analysis.NeedsMeshRerun = False
        analysis.NeedsCaseRewrite = False
        _group, new_region_objects, regenerated_interface = \
            CfdInterfaceNccRegions.createInterfaceNccRegions(
                source_objects,
                interface_obj=interface,
            )
        new_regions = {region.SourceObject.Name: region for region in new_region_objects}

        self.assertIs(regenerated_interface, interface)
        self.assertIs(mesh.Part, new_regions[doc.FluidRegion.Name])
        self.assertEqual(len(solid_material.ShapeRefs), 1)
        self.assertIs(solid_material.ShapeRefs[0][0], new_regions[doc.SolidRegion.Name])
        self.assertEqual(tuple(solid_material.ShapeRefs[0][1]), ("Solid1",))
        self.assertEqual(len(boundary.ShapeRefs), 1)
        self.assertIs(boundary.ShapeRefs[0][0], new_regions[doc.FluidRegion.Name])
        restored_faces = [
            new_regions[doc.FluidRegion.Name].Shape.getElement(subname)
            for subname in boundary.ShapeRefs[0][1]
        ]
        restored_area = sum(abs(old_boundary_face.common(face).Area) for face in restored_faces)
        self.assertAlmostEqual(restored_area, old_boundary_face.Area, places=6)
        self.assertTrue(analysis.NeedsMeshRewrite)
        self.assertTrue(analysis.NeedsMeshRerun)
        self.assertTrue(analysis.NeedsCaseRewrite)

        fccPrint('--------------- End of CFD tests ---------------')

    def test_touching_pair_order_drives_slice_chain(self):
        fccPrint('--------------- Start of CFD tests ---------------')
        for m in self.__class__.__macros:
            macro_name = os.path.join(home_path, "Demos", self.__class__.__dir_name, m)
            fccPrint('Running {} macro {} ...'.format(self.__class__.__dir_name, macro_name))
            CfdTools.executeMacro(macro_name)

        from CfdOF.Solve import CfdInterfaceNccRegions
        import Part

        doc = FreeCAD.ActiveDocument
        cube = doc.addObject("Part::Feature", "TouchCube")
        cube.Shape = Part.makeBox(10, 10, 10)
        cylinder = doc.addObject("Part::Feature", "TouchCylinder")
        cylinder.Shape = Part.makeCylinder(5, 10, FreeCAD.Vector(10, 5, 0), FreeCAD.Vector(1, 0, 0))
        cone = doc.addObject("Part::Feature", "TouchCone")
        cone.Shape = Part.makeCone(5, 0, 10, FreeCAD.Vector(20, 5, 0), FreeCAD.Vector(1, 0, 0))
        doc.recompute()

        source_objects = [cube, cylinder, cone]
        touching_pairs = CfdInterfaceNccRegions.findTouchingShapePairs(source_objects)
        self.assertEqual(
            [(a.Name, b.Name) for a, b in touching_pairs],
            [("TouchCube", "TouchCylinder"), ("TouchCylinder", "TouchCone")],
        )

        _group, region_objects, _interface = CfdInterfaceNccRegions.createInterfaceNccRegions(source_objects)
        regions = {region.SourceObject.Name: region for region in region_objects}
        self.assertTrue(_interface.InterfacePairs)

        def generated_slice_depth(obj):
            depth = 0
            while getattr(getattr(obj, 'Proxy', None), 'Type', '') == "FeatureSlice":
                depth += 1
                obj = obj.Base
            return depth

        self.assertEqual(generated_slice_depth(regions["TouchCube"]), 1)
        self.assertEqual(generated_slice_depth(regions["TouchCylinder"]), 2)
        self.assertEqual(generated_slice_depth(regions["TouchCone"]), 1)
        self.assertFalse(any(
            getattr(obj, 'GeneratedBy', '') == CfdInterfaceNccRegions.GENERATED_BY
            and getattr(obj, 'TypeId', '') == 'App::Link'
            for obj in doc.Objects
        ))
        generated_clones = [
            obj for obj in doc.Objects
            if getattr(obj, 'GeneratedBy', '') == CfdInterfaceNccRegions.GENERATED_BY
            and obj.Name.startswith("NccSourceClone_")
        ]
        self.assertEqual(len(generated_clones), 3)
        for source_obj in source_objects:
            self.assertIsNotNone(doc.getObject("NccSourceClone_{}".format(source_obj.Name)))

        from CfdOF.Solve import CfdRegionCoupledInterface
        shape_refs, interface_pairs = CfdRegionCoupledInterface.generatePairedTouchingFaceData(region_objects)
        self.assertTrue(shape_refs)
        self.assertTrue(interface_pairs)
        self.assertNotIn("BooleanFragments", [ref_obj.Name for ref_obj, _subnames in shape_refs])

        fccPrint('--------------- End of CFD tests ---------------')

    def test_overlapping_region_uses_cut_for_containing_side(self):
        fccPrint('--------------- Start of CFD tests ---------------')
        for m in self.__class__.__macros:
            macro_name = os.path.join(home_path, "Demos", self.__class__.__dir_name, m)
            fccPrint('Running {} macro {} ...'.format(self.__class__.__dir_name, macro_name))
            CfdTools.executeMacro(macro_name)

        from CfdOF.Solve import CfdInterfaceNccRegions
        from CfdOF.Solve import CfdRegionCoupledInterface
        import Part

        doc = FreeCAD.ActiveDocument
        fluid = doc.addObject("Part::Feature", "ContainingFluid")
        fluid.Shape = Part.makeBox(20, 20, 20)
        solid = doc.addObject("Part::Feature", "InternalSolid")
        solid.Shape = Part.makeBox(8, 8, 8, FreeCAD.Vector(6, 6, 6))
        doc.recompute()

        _group, region_objects, interface = CfdInterfaceNccRegions.createInterfaceNccRegions([fluid, solid])
        regions = {region.SourceObject.Name: region for region in region_objects}

        self.assertEqual(getattr(regions["ContainingFluid"], "TypeId", ""), "Part::Cut")
        self.assertEqual(regions["ContainingFluid"].SourceObject, fluid)
        self.assertEqual(getattr(regions["ContainingFluid"].Base, "GeneratedBy", ""),
                         CfdInterfaceNccRegions.GENERATED_BY)
        self.assertEqual(getattr(regions["ContainingFluid"].Tool, "GeneratedBy", ""),
                         CfdInterfaceNccRegions.GENERATED_BY)
        self.assertNotEqual(getattr(regions["InternalSolid"], "TypeId", ""), "Part::Cut")
        self.assertTrue(interface.InterfacePairs)

        paired_regions = {
            tuple(sorted((pair['region_a'], pair['region_b'])))
            for pair in CfdRegionCoupledInterface._decode_interface_pairs(interface)
        }
        self.assertEqual(paired_regions, {tuple(sorted((
            CfdRegionCoupledInterface.getRegionName(regions["ContainingFluid"]),
            CfdRegionCoupledInterface.getRegionName(regions["InternalSolid"]),
        )))})

        fccPrint('--------------- End of CFD tests ---------------')

    def test_overlapping_region_roles_choose_cut_owner(self):
        fccPrint('--------------- Start of CFD tests ---------------')
        for m in self.__class__.__macros:
            macro_name = os.path.join(home_path, "Demos", self.__class__.__dir_name, m)
            fccPrint('Running {} macro {} ...'.format(self.__class__.__dir_name, macro_name))
            CfdTools.executeMacro(macro_name)

        from CfdOF.Solve import CfdInterfaceNccRegions
        import Part

        doc = FreeCAD.ActiveDocument
        solid = doc.addObject("Part::Feature", "RoleSolid")
        solid.Shape = Part.makeBox(8, 8, 8, FreeCAD.Vector(6, 6, 6))
        fluid = doc.addObject("Part::Feature", "RoleFluid")
        fluid.Shape = Part.makeBox(20, 20, 20)
        doc.recompute()

        _group, region_objects, _interface = CfdInterfaceNccRegions.createInterfaceNccRegions(
            [solid, fluid],
            region_roles={
                solid.Name: CfdInterfaceNccRegions.REGION_ROLE_SOLID,
                fluid.Name: CfdInterfaceNccRegions.REGION_ROLE_FLUID,
            },
        )
        regions = {region.SourceObject.Name: region for region in region_objects}

        self.assertNotEqual(getattr(regions["RoleSolid"], "TypeId", ""), "Part::Cut")
        self.assertEqual(getattr(regions["RoleSolid"], "RegionRole", ""),
                         CfdInterfaceNccRegions.REGION_ROLE_SOLID)
        self.assertEqual(getattr(regions["RoleFluid"], "TypeId", ""), "Part::Cut")
        self.assertEqual(getattr(regions["RoleFluid"], "RegionRole", ""),
                         CfdInterfaceNccRegions.REGION_ROLE_FLUID)

        fccPrint('--------------- End of CFD tests ---------------')

    def test_final_region_lookup_does_not_depend_on_operation_name(self):
        fccPrint('--------------- Start of CFD tests ---------------')
        for m in self.__class__.__macros:
            macro_name = os.path.join(home_path, "Demos", self.__class__.__dir_name, m)
            fccPrint('Running {} macro {} ...'.format(self.__class__.__dir_name, macro_name))
            CfdTools.executeMacro(macro_name)

        from CfdOF.Solve import CfdInterfaceNccRegions
        from CfdOF.Solve import CfdRegionCoupledInterface
        import Part

        doc = FreeCAD.ActiveDocument
        solid = doc.addObject("Part::Feature", "MarkedSolid")
        solid.Shape = Part.makeBox(10, 10, 10)
        touching_solid = doc.addObject("Part::Feature", "TouchingSolid")
        touching_solid.Shape = Part.makeBox(10, 10, 10, FreeCAD.Vector(10, 0, 0))
        fluid = doc.addObject("Part::Feature", "ContainingFluid")
        fluid.Shape = Part.makeBox(40, 30, 30, FreeCAD.Vector(-10, -10, -10))
        doc.recompute()

        roles = {
            solid.Name: CfdInterfaceNccRegions.REGION_ROLE_SOLID,
            touching_solid.Name: CfdInterfaceNccRegions.REGION_ROLE_SOLID,
            fluid.Name: CfdInterfaceNccRegions.REGION_ROLE_FLUID,
        }
        _group, region_objects, _interface = CfdInterfaceNccRegions.createInterfaceNccRegions(
            [solid, touching_solid, fluid],
            region_roles=roles,
        )
        regions = {region.SourceObject.Name: region for region in region_objects}
        final_solid = regions[solid.Name]

        self.assertTrue(final_solid.Name.startswith("NccSlice_"))
        self.assertTrue(final_solid.IsFinalInterfaceRegion)
        self.assertTrue(CfdRegionCoupledInterface.isFinalInterfaceRegionObject(final_solid))
        self.assertEqual(CfdRegionCoupledInterface.getInterfaceRegionForSource(solid), final_solid)

        fccPrint('--------------- End of CFD tests ---------------')

    def test_fluid_cut_includes_separated_contained_solids(self):
        fccPrint('--------------- Start of CFD tests ---------------')
        for m in self.__class__.__macros:
            macro_name = os.path.join(home_path, "Demos", self.__class__.__dir_name, m)
            fccPrint('Running {} macro {} ...'.format(self.__class__.__dir_name, macro_name))
            CfdTools.executeMacro(macro_name)

        from CfdOF.Solve import CfdInterfaceNccRegions
        from CfdOF.Solve import CfdRegionCoupledInterface
        import Part

        doc = FreeCAD.ActiveDocument
        solid_a = doc.addObject("Part::Feature", "ContainedSolidA")
        solid_a.Shape = Part.makeBox(5, 5, 5, FreeCAD.Vector(5, 5, 5))
        solid_b = doc.addObject("Part::Feature", "ContainedSolidB")
        solid_b.Shape = Part.makeBox(5, 5, 5, FreeCAD.Vector(20, 20, 20))
        fluid = doc.addObject("Part::Feature", "SeparatedSolidFluid")
        fluid.Shape = Part.makeBox(30, 30, 30)
        doc.recompute()

        roles = {
            solid_a.Name: CfdInterfaceNccRegions.REGION_ROLE_SOLID,
            solid_b.Name: CfdInterfaceNccRegions.REGION_ROLE_SOLID,
            fluid.Name: CfdInterfaceNccRegions.REGION_ROLE_FLUID,
        }
        _group, region_objects, interface = CfdInterfaceNccRegions.createInterfaceNccRegions(
            [solid_a, solid_b, fluid],
            region_roles=roles,
        )
        regions = {region.SourceObject.Name: region for region in region_objects}
        fluid_region = regions[fluid.Name]

        expected_volume = fluid.Shape.Volume - solid_a.Shape.Volume - solid_b.Shape.Volume
        self.assertAlmostEqual(fluid_region.Shape.Volume, expected_volume, places=7)
        paired_regions = {
            tuple(sorted((pair['region_a'], pair['region_b'])))
            for pair in CfdRegionCoupledInterface._decode_interface_pairs(interface)
        }
        self.assertIn(tuple(sorted((solid_a.Label, fluid.Label))), paired_regions)
        self.assertIn(tuple(sorted((solid_b.Label, fluid.Label))), paired_regions)

        fccPrint('--------------- End of CFD tests ---------------')

    def test_fluid_cut_preserves_partner_face_partitions(self):
        fccPrint('--------------- Start of CFD tests ---------------')
        for m in self.__class__.__macros:
            macro_name = os.path.join(home_path, "Demos", self.__class__.__dir_name, m)
            fccPrint('Running {} macro {} ...'.format(self.__class__.__dir_name, macro_name))
            CfdTools.executeMacro(macro_name)

        from CfdOF.Solve import CfdInterfaceNccRegions
        from CfdOF.Solve import CfdRegionCoupledInterface
        import Part

        doc = FreeCAD.ActiveDocument
        solid_a = doc.addObject("Part::Feature", "PartitionSolidA")
        solid_a.Shape = Part.makeBox(5, 5, 5, FreeCAD.Vector(5, 5, 5))
        solid_b = doc.addObject("Part::Feature", "PartitionSolidB")
        solid_b.Shape = Part.makeBox(5, 5, 5, FreeCAD.Vector(10, 5, 5))
        fluid = doc.addObject("Part::Feature", "PartitionFluid")
        fluid.Shape = Part.makeBox(25, 20, 20)
        doc.recompute()

        roles = {
            solid_a.Name: CfdInterfaceNccRegions.REGION_ROLE_SOLID,
            solid_b.Name: CfdInterfaceNccRegions.REGION_ROLE_SOLID,
            fluid.Name: CfdInterfaceNccRegions.REGION_ROLE_FLUID,
        }
        _group, region_objects, interface = CfdInterfaceNccRegions.createInterfaceNccRegions(
            [solid_a, solid_b, fluid],
            region_roles=roles,
        )
        regions = {region.SourceObject.Name: region for region in region_objects}
        fluid_region = regions[fluid.Name]

        current_obj = fluid_region
        while getattr(current_obj, 'TypeId', '') == 'Part::Cut':
            self.assertFalse(current_obj.Refine)
            current_obj = current_obj.Base

        partners_by_fluid_face = {}
        for pair in CfdRegionCoupledInterface._decode_interface_pairs(interface):
            if pair['region_a'] == fluid.Label:
                partners_by_fluid_face.setdefault(pair['face_a'], set()).add(pair['region_b'])
            elif pair['region_b'] == fluid.Label:
                partners_by_fluid_face.setdefault(pair['face_b'], set()).add(pair['region_a'])
        self.assertTrue(partners_by_fluid_face)
        self.assertTrue(all(len(partners) == 1 for partners in partners_by_fluid_face.values()))
        self.assertTrue(interface.Proxy.makeBoundaryObjects(interface))

        fccPrint('--------------- End of CFD tests ---------------')

    def tearDown(self):
        if FreeCAD.ActiveDocument is not None:
            FreeCAD.closeDocument(FreeCAD.ActiveDocument.Name)


class SolidMaterialCardsTest(unittest.TestCase):
    def test_solid_material_cards_are_complete(self):
        expected_names = {
            "AcrylicSolid", "AluminiumSolid", "BrassSolid", "BrickSolid",
            "CopperSolid", "FiberglassSolid", "GlassSolid", "Inconel601Solid",
            "IronSolid", "PolypropyleneSolid", "SandSolid", "SilverSolid",
            "StainlessSteel316Solid", "StyrofoamSolid", "TitaniumSolid",
        }
        materials, name_path_list = CfdTools.importMaterials()
        paths_by_name = {name: path for name, path in name_path_list}

        self.assertTrue(expected_names.issubset(paths_by_name))
        for name in expected_names:
            material = materials[paths_by_name[name]]
            self.assertEqual(material.get("Type"), "Solid")
            for property_name in ("Density", "ThermalConductivity", "SpecificHeat"):
                self.assertTrue(material.get(property_name), "{} lacks {}".format(name, property_name))


def compareInpFiles(file_name1, file_name2):
    file1 = open(file_name1, 'r')
    f1 = file1.readlines()
    file1.close()
    lf1 = [l for l in f1 if not l.startswith("FOAMDIR=") and not l.startswith("GMSH_EXE=")
           and not l.startswith("set FOAMDIR") and not l.startswith("set FOAMVER") and not l.startswith("$GMSH_EXE")]
    lf1 = forceUnixLineEnds(lf1)
    file2 = open(file_name2, 'r')
    f2 = file2.readlines()
    file2.close()
    lf2 = [l for l in f2 if not l.startswith("FOAMDIR=") and not l.startswith("GMSH_EXE=")
           and not l.startswith("set FOAMDIR") and not l.startswith("set FOAMVER") and not l.startswith("$GMSH_EXE")]
    lf2 = forceUnixLineEnds(lf2)
    while lf1 and not lf1[-1].strip():
        lf1.pop()
    while lf2 and not lf2[-1].strip():
        lf2.pop()
    if file_name1.endswith('.brep') and file_name2.endswith('.brep'):
        lf1 = [line.rstrip() + '\n' for line in lf1]
        lf2 = [line.rstrip() + '\n' for line in lf2]
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
