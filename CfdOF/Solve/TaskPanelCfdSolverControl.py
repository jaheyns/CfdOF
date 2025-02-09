# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2016 - Qingfeng Xia <qingfeng.xia()eng.ox.ac.uk>        *
# *   Copyright (c) 2017 Alfred Bogaers (CSIR) <abogaers@csir.co.za>        *
# *   Copyright (c) 2017 Johan Heyns (CSIR) <jheyns@csir.co.za>             *
# *   Copyright (c) 2017 Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>          *
# *   Copyright (c) 2019-2022 Oliver Oxtoby <oliveroxtoby@gmail.com>        *
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
from CfdOF import CfdTools
import os
import os.path
import time
from CfdOF.CfdConsoleProcess import CfdConsoleProcess
if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore
    from PySide import QtGui
    from PySide.QtCore import Qt
    from PySide.QtGui import QApplication

translate = FreeCAD.Qt.translate

class TaskPanelCfdSolverControl:
    def __init__(self, solver_runner_obj):
        ui_path = os.path.join(CfdTools.getModulePath(), 'Gui', "TaskPanelCfdSolverControl.ui")
        self.form = FreeCADGui.PySideUic.loadUi(ui_path)

        self.analysis_object = CfdTools.getActiveAnalysis()

        self.solver_runner = solver_runner_obj
        self.solver_object = solver_runner_obj.solver

        # update UI
        self.console_message = ''

        self.solver_object.Proxy.solver_process = CfdConsoleProcess(finished_hook=self.solverFinished,
                                                                    stdout_hook=self.gotOutputLines,
                                                                    stderr_hook=self.gotErrorLines)
        self.Timer = QtCore.QTimer()
        self.Timer.setInterval(1000)
        self.Timer.timeout.connect(self.updateText)

        self.form.terminateSolver.clicked.connect(self.killSolverProcess)
        self.form.terminateSolver.setEnabled(False)

        self.working_dir = CfdTools.getOutputPath(self.analysis_object)

        self.updateUI()

        # Connect Signals and Slots
        self.form.pb_write_inp.clicked.connect(self.write_input_file_handler)
        self.form.pb_edit_inp.clicked.connect(self.editSolverInputFile)
        self.form.pb_run_solver.clicked.connect(self.runSolverProcess)
        self.form.pb_paraview.clicked.connect(self.openParaview)

        self.Start = time.time()
        self.Timer.start()

    def updateUI(self):
        solverDirectory = os.path.join(self.working_dir, self.solver_object.InputCaseName)
        self.form.pb_edit_inp.setEnabled(os.path.exists(solverDirectory))
        self.form.pb_paraview.setEnabled(os.path.exists(os.path.join(solverDirectory, "pv.foam")))
        self.form.pb_run_solver.setEnabled(os.path.exists(os.path.join(solverDirectory, "Allrun")))

    def consoleMessage(self, message="", colour_type=None):
        self.console_message += \
            '<font color="{}">{:4.1f}:</font> '.format(CfdTools.getColour('Logging'), time.time() - self.Start)
        if colour_type:
            self.console_message += '<font color="{}">{}</font><br>'.format(CfdTools.getColour(colour_type), message)
        else:
            self.console_message += message + '<br>'
        self.form.textEdit_Output.setText(self.console_message)
        self.form.textEdit_Output.moveCursor(QtGui.QTextCursor.End)

    def updateText(self):
        if self.solver_object.Proxy.solver_process.state() == QtCore.QProcess.ProcessState.Running:
            self.form.l_time.setText('Time: ' + CfdTools.formatTimer(time.time() - self.Start))

    def getStandardButtons(self):
        return QtGui.QDialogButtonBox.Close

    def reject(self):
        FreeCADGui.ActiveDocument.resetEdit()

    def closing(self):
        # We call this from unsetEdit to ensure cleanup
        self.solver_object.Proxy.solver_process.terminate()
        self.solver_object.Proxy.solver_process.waitForFinished()
        self.Timer.stop()

    def write_input_file_handler(self):
        self.Start = time.time()
        FreeCADGui.doCommand("from CfdOF.Solve import CfdCaseWriterFoam")
        from CfdOF.Solve import CfdCaseWriterFoam
        import importlib
        importlib.reload(CfdCaseWriterFoam)
        self.consoleMessage("Case writer called")
        self.form.pb_paraview.setEnabled(False)
        self.form.pb_edit_inp.setEnabled(False)
        self.form.pb_run_solver.setEnabled(False)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            FreeCADGui.doCommand("FreeCAD.ActiveDocument." + self.solver_object.Name + ".Proxy.case_writer = "
                                    "CfdCaseWriterFoam.CfdCaseWriterFoam(FreeCAD.ActiveDocument." +
                                    self.solver_runner.analysis.Name + ")")
            FreeCADGui.doCommand("writer = FreeCAD.ActiveDocument." +
                                    self.solver_object.Name + ".Proxy.case_writer")
            writer = self.solver_object.Proxy.case_writer
            writer.progressCallback = self.consoleMessage
            FreeCADGui.doCommand("writer.writeCase()")
        except Exception as e:
            self.consoleMessage("Error writing case:", 'Error')
            self.consoleMessage(type(e).__name__ + ": " + str(e), 'Error')
            self.consoleMessage("Write case setup file failed", 'Error')
            raise
        else:
            self.analysis_object.NeedsCaseRewrite = False
        finally:
            QApplication.restoreOverrideCursor()
        self.updateUI()
        self.form.pb_run_solver.setEnabled(True)

    def editSolverInputFile(self):
        case_path = os.path.join(self.working_dir, self.solver_object.InputCaseName)
        self.consoleMessage("Please edit the case input files externally at: {}\n".format(case_path))
        CfdTools.openFileManager(case_path)

    def runSolverProcess(self):
        self.Start = time.time()

        # Check for changes that require remesh
        if FreeCAD.GuiUp and (
                self.analysis_object.NeedsMeshRewrite or 
                self.analysis_object.NeedsCaseRewrite or 
                self.analysis_object.NeedsMeshRerun):
            
            if self.analysis_object.NeedsCaseRewrite:
                if self.analysis_object.NeedsMeshRewrite or self.analysis_object.NeedsMeshRerun:
                    text = translate(
                        "Dialogs",
                        "The case may need to be re-meshed and the case setup re-written based on changes "
                        "you have made to the model.\n\nRe-mesh and re-write case setup first?"
                    )
                else:
                    text = translate(
                        "Dialogs",
                        "The case setup may need to be re-written based on changes " 
                        "you have made to the model.\n\nRe-write case setup first?"
                    )
            else:
                if self.analysis_object.NeedsMeshRewrite or self.analysis_object.NeedsMeshRerun:
                    text = translate(
                        "Dialogs",
                        "The case may need to be re-meshed based on changes " 
                        "you have made to the model.\n\nRe-mesh case first?"
                    )
                
            if QtGui.QMessageBox.question(
                    None, "CfdOF Workbench", text, defaultButton=QtGui.QMessageBox.Yes) == QtGui.QMessageBox.Yes:
                self.Start = time.time()
                
                if self.analysis_object.NeedsMeshRewrite or self.analysis_object.NeedsMeshRerun:
                    from CfdOF.Mesh import CfdMeshTools
                    mesh_obj = CfdTools.getMeshObject(self.analysis_object)
                    cart_mesh = CfdMeshTools.CfdMeshTools(mesh_obj)
                    cart_mesh.progressCallback = self.consoleMessage
                    if self.analysis_object.NeedsMeshRewrite:
                        #Write mesh
                        cart_mesh.writeMesh()
                        self.analysis_object.NeedsMeshRewrite = False
                        self.analysis_object.NeedsMeshRerun = True

                if self.analysis_object.NeedsCaseRewrite:
                    self.write_input_file_handler()

                if self.analysis_object.NeedsMeshRerun:
                    # Run mesher
                    self.solver_object.Proxy.solver_process = CfdConsoleProcess(
                        finished_hook=self.mesherFinished,
                        stdout_hook=self.gotOutputLines,
                        stderr_hook=self.gotErrorLines)

                    cart_mesh.error = False
                    if CfdTools.getFoamRuntime() == "MinGW":
                        cmd = CfdTools.makeRunCommand('Allmesh.bat', source_env=False)
                    else:
                        cmd = CfdTools.makeRunCommand('./Allmesh', cart_mesh.meshCaseDir, source_env=False)
                    env_vars = CfdTools.getRunEnvironment()
                    self.solver_object.Proxy.solver_process.start(cmd, working_dir=cart_mesh.meshCaseDir, env_vars=env_vars)
                    if self.solver_object.Proxy.solver_process.waitForStarted():
                        # Setting solve button to inactive to ensure that two instances of the same simulation aren't started
                        # simultaneously
                        self.form.pb_write_inp.setEnabled(False)
                        self.form.pb_run_solver.setEnabled(False)
                        self.form.terminateSolver.setEnabled(True)
                        self.consoleMessage("Mesher started ...")
                        return
            else:
                self.Start = time.time()

        QApplication.setOverrideCursor(Qt.WaitCursor)
        FreeCADGui.doCommand("from CfdOF import CfdTools")
        FreeCADGui.doCommand("from CfdOF import CfdConsoleProcess")
        self.solver_object.Proxy.solver_runner = self.solver_runner
        FreeCADGui.doCommand("proxy = FreeCAD.ActiveDocument." + self.solver_object.Name + ".Proxy")
        # This is a workaround to emit code into macro without actually running it
        FreeCADGui.doCommand("proxy.running_from_macro = True")
        self.solver_object.Proxy.running_from_macro = False
        FreeCADGui.doCommand(
            "if proxy.running_from_macro:\n" +
            "  analysis_object = FreeCAD.ActiveDocument." + self.analysis_object.Name + "\n" +
            "  solver_object = FreeCAD.ActiveDocument." + self.solver_object.Name + "\n" +
            "  working_dir = CfdTools.getOutputPath(analysis_object)\n" +
            "  case_name = solver_object.InputCaseName\n" +
            "  solver_directory = os.path.abspath(os.path.join(working_dir, case_name))\n" +
            "  from CfdOF.Solve import CfdRunnableFoam\n" +
            "  solver_runner = CfdRunnableFoam.CfdRunnableFoam(analysis_object, solver_object)\n" +
            "  cmd = solver_runner.getSolverCmd(solver_directory)\n" +
            "  if cmd is not None:\n" +
            "    env_vars = solver_runner.getRunEnvironment()\n" +
            "    solver_process = CfdConsoleProcess.CfdConsoleProcess(stdout_hook=solver_runner.processOutput)\n" +
            "    solver_process.start(cmd, env_vars=env_vars, working_dir=solver_directory)\n" +
            "    solver_process.waitForFinished()\n")
        working_dir = CfdTools.getOutputPath(self.analysis_object)
        case_name = self.solver_object.InputCaseName
        solver_directory = os.path.abspath(os.path.join(working_dir, case_name))
        cmd = self.solver_runner.getSolverCmd(solver_directory)
        if cmd is None:
            return
        env_vars = self.solver_runner.getRunEnvironment()
        self.solver_object.Proxy.solver_process = CfdConsoleProcess(finished_hook=self.solverFinished,
                                                                    stdout_hook=self.gotOutputLines,
                                                                    stderr_hook=self.gotErrorLines)
        self.solver_object.Proxy.solver_process.start(cmd, env_vars=env_vars, working_dir=solver_directory)
        if self.solver_object.Proxy.solver_process.waitForStarted():
            # Setting solve button to inactive to ensure that two instances of the same simulation aren't started
            # simultaneously
            self.form.pb_write_inp.setEnabled(False)
            self.form.pb_run_solver.setEnabled(False)
            self.form.terminateSolver.setEnabled(True)
            self.form.pb_paraview.setEnabled(True)
            self.consoleMessage("Solver started")
        else:
            self.consoleMessage("Error starting solver", 'Error')
        QApplication.restoreOverrideCursor()

    def killSolverProcess(self):
        if CfdTools.getFoamRuntime() == "PosixDocker":
            FreeCADGui.doCommand("from CfdOF import CfdConsoleProcess")
            FreeCADGui.doCommand("cmd = CfdTools.makeRunCommand('killall Allrun', None, source_env=False)")
            FreeCADGui.doCommand("env_vars = CfdTools.getRunEnvironment()")
            FreeCADGui.doCommand("kill_process = CfdConsoleProcess.CfdConsoleProcess()\n" +
                                 "kill_process.start(cmd, env_vars=env_vars)\n" +
                                 "kill_process.waitForFinished()\n" )
        self.consoleMessage("Solver manually stopped")
        self.solver_object.Proxy.solver_process.terminate()
        # Note: solverFinished will still be called

    def solverFinished(self, exit_code):
        if exit_code == 0:
            self.consoleMessage("Simulation finished successfully")
        else:
            self.consoleMessage("Simulation exited with error", 'Error')
        self.solver_runner.solverFinished()
        self.form.pb_write_inp.setEnabled(True)
        self.form.pb_run_solver.setEnabled(True)
        self.form.terminateSolver.setEnabled(False)

    def mesherFinished(self, exit_code):
        self.form.pb_write_inp.setEnabled(True)
        self.form.pb_run_solver.setEnabled(True)
        self.form.terminateSolver.setEnabled(False)
        if exit_code == 0:
            self.consoleMessage("Mesher finished successfully")
            self.analysis_object.NeedsMeshRerun = False
            self.runSolverProcess()
        else:
            self.consoleMessage("Mesher exited with error", 'Error')

    def gotOutputLines(self, lines):
        self.solver_runner.processOutput(lines)

    def gotErrorLines(self, lines):
        print_err = self.solver_object.Proxy.solver_process.processErrorOutput(lines)
        if print_err is not None:
            self.consoleMessage(print_err, 'Error')

    def openParaview(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        case_path = os.path.abspath(os.path.join(self.working_dir, self.solver_object.InputCaseName))
        script_name = "pvScript.py"
        try:
            CfdTools.startParaview(case_path, script_name, self.consoleMessage)
        finally:
            QApplication.restoreOverrideCursor()
