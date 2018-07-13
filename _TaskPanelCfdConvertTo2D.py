# ***************************************************************************
# *   (c) Bernd Hahnebach (bernd@bimstatik.org) 2014                        *
# *   (c) Qingfeng Xia @ iesensor.com 2016                                  *
# *   Copyright (c) 2018 - Alfred Bogaers <abogaers@csir.co.za>             *
# *   Copyright (c) 2018 - Johan Heyns <jheyns@csir.co.za>                  *
# *   Copyright (c) 2018 - Oliver Oxtoby <ooxtoby@csir.co.za>               *
# *                                                                         *
# *   This file is part of the FreeCAD CAx development system.              *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   FreeCAD is distributed in the hope that it will be useful,            *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Lesser General Public License for more details.                   *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with FreeCAD; if not, write to the Free Software        *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************

from __future__ import print_function
import FreeCAD
import os
import sys
import os.path
import Units
from CfdTools import setInputFieldQuantity
from CfdTools import getParentAnalysisObject
import time

import CfdTools
import math
import Part

if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore
    from PySide import QtCore
    from PySide import QtGui
    from PySide.QtCore import Qt
    from PySide.QtGui import QApplication
    import FemGui


class TaskPanelCfdConvertTo2D:
    '''The editmode TaskPanel for FluidMaterial objects'''
    def __init__(self, obj):
        self.obj = obj

        self.Timer = QtCore.QTimer()
        self.conversion_process = QtCore.QProcess()
        self.conversion_process.finished.connect(self.mesh_finished)
        self.conversion_process.readyReadStandardOutput.connect(self.read_output)
        self.conversion_process.readyReadStandardError.connect(self.read_output)

        self.console_message_cart = ''
        self.form = FreeCADGui.PySideUic.loadUi(os.path.join(os.path.dirname(__file__),
                                                             "TaskPanelCfdConvertTo2D.ui"))

        descriptionText = "Convert 3D mesh to 2D (single element through the thickness)."

        usageDescriptor = ("1.) Create 3D mesh. \n" \
            "2.) Create boundary conditions for front and back faces \n"\
            "3.) Select corresponding boundary conditions \n"\
            "4.) Selected boundaries will automitically be changed to Type='Empty'.")

        self.form.labelDescription.setText(descriptionText)
        self.form.labelUsageDescription.setText(usageDescriptor)

        self.form.paraviewButton.setEnabled(False)
        self.form.paraviewButton.clicked.connect(self.openParaview)
        self.open_paraview = QtCore.QProcess()

        self.listOfBoundaryLabels = []
        self.listOfBoundaryNames = []
        doc_name = str(self.obj.Document.Name)
        doc = FreeCAD.getDocument(doc_name)
        for doc_objs in doc.Objects:
            if "CfdFluidBoundary" in doc_objs.Name:
                self.listOfBoundaryLabels.append(doc_objs.Label)
                self.listOfBoundaryNames.append(doc_objs.Name)

        self.form.comboBoxFront.addItems(self.listOfBoundaryLabels)
        self.form.comboBoxBack.addItems(self.listOfBoundaryLabels)

        self.form.convertButton.clicked.connect(self.convertClicked)

        self.initialiseUponReload()

    def convertClicked(self):
        fFObjName = self.listOfBoundaryNames[self.form.comboBoxFront.currentIndex()]
        bFObjName = self.listOfBoundaryNames[self.form.comboBoxBack.currentIndex()]
        if fFObjName == bFObjName:
            CfdTools.cfdError("Front and back faces cannot be the same.")
        else:
            doc_name = str(self.obj.Document.Name)
            frontObj = FreeCAD.getDocument(doc_name).getObject(fFObjName)
            backObj = FreeCAD.getDocument(doc_name).getObject(bFObjName)
            fShape = frontObj.Shape
            bShape = backObj.Shape
            if len(fShape.Faces) == 0 or len(bShape.Faces) == 0:
                CfdTools.cfdError("Either the front or back face is empty.")
            else:
                allFFacesPlanar = True
                allBFacesPlanar = True
                for faces in fShape.Faces:
                    if not isinstance(faces.Surface, Part.Plane):
                        allFFacesPlanar = False
                        break
                for faces in bShape.Faces:
                    if not isinstance(faces.Surface, Part.Plane):
                        allBFacesPlanar = False
                        break
                if allFFacesPlanar and allBFacesPlanar:
                    A1 = fShape.Faces[0].Surface.Axis
                    A2 = bShape.Faces[0].Surface.Axis
                    if self.norm(A1-A2) <=1e-6 or self.norm(A1+A2):
                        if len(frontObj.Shape.Vertexes) == len(backObj.Shape.Vertexes) and \
                           len(frontObj.Shape.Vertexes) > 0 and \
                           abs(frontObj.Shape.Area - backObj.Shape.Area) < 1e-6:
                            self.distance = fShape.distToShape(bShape)[0]
                            self.convertMesh()
                        else:
                            CfdTools.cfdError("Front and back faces do not match up.")
                    else:
                        CfdTools.cfdError("Front and back faces are not aligned.")
                else:
                    CfdTools.cfdError("Front and back faces need to be flat surfaces.")

    def openParaview(self):
        self.Start = time.time()
        QApplication.setOverrideCursor(Qt.WaitCursor)

        paraview_cmd = "paraview"
        # If using blueCFD, use paraview supplied
        if CfdTools.getFoamRuntime() == 'BlueCFD':
            paraview_cmd = '{}\\..\\AddOns\\ParaView\\bin\\paraview.exe'.format(CfdTools.getFoamDir())
        # Otherwise, the command 'paraview' must be in the path. Possibly make path user-settable.
        # Test to see if it exists, as the exception thrown is cryptic on Windows if it doesn't
        import distutils.spawn
        if distutils.spawn.find_executable(paraview_cmd) is None:
            raise IOError("Paraview executable " + paraview_cmd + " not found in path.")

        self.paraviewScriptName = os.path.join(self.meshCaseDir, 'pvScriptMesh.py')
        arg = '--script={}'.format(self.paraviewScriptName)

        self.console_log("Running " + paraview_cmd + " " +arg)
        self.open_paraview.start(paraview_cmd, [arg])
        QApplication.restoreOverrideCursor()

    def norm(self, first):
        if isinstance(first, FreeCAD.Vector):
            return math.sqrt(first.x*first.x + first.y*first.y + first.z*first.z)

    def convertMesh(self):
        import tempfile
        import CfdCaseWriterFoam
        import CfdCartTools
        import TemplateBuilder
        import os

        if not self.meshConverted:
            self.Start = time.time()
            self.Timer.start()
            self.console_log("Starting 3D to 2D mesh conversion ...")

            self.frontFaceName = self.form.comboBoxFront.currentText()
            self.backFaceName = self.form.comboBoxBack.currentText()

            tmpdir = tempfile.gettempdir()
            analysis_obj = FemGui.getActiveAnalysis()

            tmpdir = tempfile.gettempdir()
            self.meshCaseDir = os.path.join(tmpdir, "meshCase")

            self.meshObj = CfdTools.getMesh(analysis_obj)
            solver_obj = CfdTools.getSolver(analysis_obj)
            gmshMesh = False
            if self.meshObj.Proxy.Type == "Fem::FemMeshGmsh":  # GMSH
                # Convert GMSH created UNV file to OpenFoam
                print("Writing GMSH UNV mesh to be converted to 2D mesh")
                unvMeshFile = self.meshCaseDir + os.path.sep + solver_obj.InputCaseName + u".unv"
                #try:
                if not os.path.exists(self.meshCaseDir):
                    os.makedirs(self.meshCaseDir)

                bc_group = CfdTools.getCfdBoundaryGroup(analysis_obj)
                self.mesh_generated = CfdTools.write_unv_mesh(self.meshObj, bc_group, unvMeshFile)
                gmshMesh = True
                frontFaceList = self.frontFaceName
                backFaceList = [self.backFaceName]

            else:
                case = CfdCaseWriterFoam.CfdCaseWriterFoam(analysis_obj)
                case.settings = {}
                case.settings['createPatchesFromSnappyBaffles'] = False
                case.setupPatchNames()
                keys = case.settings['createPatches'].keys()
                frontPatchIndex = keys.index(self.frontFaceName)
                frontFaceList = case.settings['createPatches'][keys[frontPatchIndex]]['PatchNamesList']

                backPatchIndex = keys.index(self.backFaceName)
                backFaceList = case.settings['createPatches'][keys[backPatchIndex]]['PatchNamesList']

            template_path = os.path.join(CfdTools.get_module_path(), "data", "defaultsMesh")
            settings = {
                'ConvertTo2D': True,
                'gmshMesh': gmshMesh,
                'unvFileName': solver_obj.InputCaseName + u".unv",
                'FrontFaceList': frontFaceList,
                'BackFaceList': backFaceList[0],
                'Distance': self.distance/1000.0,
                'TranslatedFoamPath': CfdTools.translatePath(CfdTools.getFoamDir()),
                'MeshPath': self.meshCaseDir
                }

            TemplateBuilder.TemplateBuilder(self.meshCaseDir, template_path, settings)

            cmd = CfdTools.makeRunCommand('./ConvertMeshTo2D', self.meshCaseDir, source_env=False)

            #will fail silently in Windows
            fname = os.path.join(self.meshCaseDir, "ConvertMeshTo2D")
            import stat
            s = os.stat(fname)
            os.chmod(fname, s.st_mode | stat.S_IEXEC)

            FreeCAD.Console.PrintMessage("Executing: " + ' '.join(cmd) + "\n")
            env = QtCore.QProcessEnvironment.systemEnvironment()
            env_vars = CfdTools.getRunEnvironment()
            for key in env_vars:
                env.insert(key, env_vars[key])

            self.conversion_process.setProcessEnvironment(env)
            self.conversion_process.start(cmd[0], cmd[1:])

            if self.conversion_process.waitForStarted():
                self.form.convertButton.setEnabled(False)  # Prevent user running a second instance
                self.form.paraviewButton.setEnabled(False)
            else:
                self.console_log("Error starting meshing process", "#FF0000")
        else:
            CfdTools.cfdError("Mesh has already been converted!")

    def console_log(self, message="", color="#000000"):
        self.console_message_cart = self.console_message_cart \
                                    + '<font color="#0000FF">{0:4.1f}:</font> <font color="{1}">{2}</font><br>'.\
                                    format(time.time()
                                    - self.Start, color, message.encode('utf-8', 'replace'))
        self.form.console_output.setText(self.console_message_cart)
        self.form.console_output.moveCursor(QtGui.QTextCursor.End)

    def read_output(self):
        while self.conversion_process.canReadLine():
            print(str(self.conversion_process.readLine()), end="") # Avoid displaying on FreeCAD status bar

        # Print any error output to console
        self.conversion_process.setReadChannel(QtCore.QProcess.StandardError)
        while self.conversion_process.canReadLine():
            err = str(self.conversion_process.readLine())
            self.console_log(err, "#FF0000")
            FreeCAD.Console.PrintError(err)
        self.conversion_process.setReadChannel(QtCore.QProcess.StandardOutput)

    def mesh_finished(self, exit_code):
        self.read_output()
        print("exit code", exit_code)
        if exit_code == 0:
            self.console_log("Reading mesh")
            # Reading stl created by OpenFOAM to display representation of mesh
            import Mesh
            import Fem
            self.meshConverted = True
            stl = os.path.join(self.meshCaseDir, 'mesh_outside.stl')
            ast = os.path.join(self.meshCaseDir, 'mesh_outside.ast')
            mesh = Mesh.Mesh(stl)
            mesh.write(ast)
            os.remove(stl)
            os.rename(ast, stl)
            fem_mesh = Fem.read(stl)
            self.meshObj.FemMesh = fem_mesh
            self.console_log('2D Meshing completed')
            self.console_log('The mesh should now contain only a single element through the thickness.')
            self.console_log('Warning: Tetrahedral representation of the mesh is a only a representation.')
            self.console_log("Please use Paraview to view the new mesh correctly.\n")
            self.form.paraviewButton.setEnabled(True)
            self.form.convertButton.setEnabled(True)
            self.saveInfo()
            self.form.conversionStatusText.setText("Mesh converted successfully.")
            self.form.conversionStatusText.setStyleSheet('color: green')
        else:
            print("Meshing error")
            self.meshConverted = False
            self.console_log("Meshing exited with error", "#FF0000")
            self.form.paraviewButton.setEnabled(False)
            self.form.convertButton.setEnabled(True)

        self.form.convertButton.setEnabled(True)
        self.Timer.stop()
        self.error_message = ''

    def initialiseUponReload(self):
        self.meshConverted = self.obj.Converter2D["TwoDMeshCreated"]
        self.frontFaceName = self.obj.Converter2D["FrontFace"]
        self.backFaceName = self.obj.Converter2D["BackFace"]
        if self.frontFaceName:
            try:
                indexFront = self.listOfBoundaryLabels.index(self.frontFaceName)
                indexBack = self.listOfBoundaryLabels.index(self.backFaceName)
                self.form.comboBoxFront.setCurrentIndex(indexFront)
                self.form.comboBoxBack.setCurrentIndex(indexBack)
            except ValueError:
                CfdTools.cfdError("NOTE: Either the boundary with the name " + str(self.frontFaceName) + " or " +
                                  str(self.backFaceName) + " no longer exists.")
        if self.meshConverted:
            self.form.conversionStatusText.setText("Mesh has already been converted.")
            self.form.conversionStatusText.setStyleSheet('color: green')
            self.form.paraviewButton.setEnabled(True)
        else:
            self.form.conversionStatusText.setText("Not yet converted.")
            self.form.conversionStatusText.setStyleSheet('color: red')

    def saveInfo(self):
        Converter2D = {"TwoDMeshCreated":self.meshConverted,
                   "FrontFace": self.frontFaceName,
                   "BackFace":  self.backFaceName}
        FreeCADGui.doCommand("FreeCAD.ActiveDocument.{}.Converter2D "
                     "= {}".format(self.obj.Name, Converter2D))

    def accept(self):
        self.saveInfo()
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()

    def reject(self):
        doc = FreeCADGui.getDocument(self.obj.Document)
        doc.resetEdit()

