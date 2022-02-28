# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2013-2015 - Juergen Riegel <FreeCAD@juergen-riegel.net> *
# *   Copyright (c) 2016 - Qingfeng Xia <qingfeng.xia()eng.ox.ac.uk>        *
# *   Copyright (c) 2017 Alfred Bogaers (CSIR) <abogaers@csir.co.za>        *
# *   Copyright (c) 2017 Johan Heyns (CSIR) <jheyns@csir.co.za>             *
# *   Copyright (c) 2017 Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>          *
# *   Copyright (c) 2019-2022 Oliver Oxtoby <oliveroxtoby@gmail.com>        *
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
import CfdTools
import os
import os.path
import time
from CfdConsoleProcess import CfdConsoleProcess
if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore
    from PySide import QtGui
    from PySide.QtCore import Qt
    from PySide.QtGui import QApplication


class _TaskPanelCfdSolverControl:
    def __init__(self, solver_runner_obj):
        ui_path = os.path.join(os.path.dirname(__file__), "TaskPanelCfdSolverControl.ui")
        self.form = FreeCADGui.PySideUic.loadUi(ui_path)

        self.analysis_object = CfdTools.getActiveAnalysis()

        self.solver_runner = solver_runner_obj
        self.solver_object = solver_runner_obj.solver

        # update UI
        self.console_message = ''

        self.solver_object.Proxy.solver_process = CfdConsoleProcess(finishedHook=self.solverFinished,
                                                                    stdoutHook=self.gotOutputLines,
                                                                    stderrHook=self.gotErrorLines)
        self.Timer = QtCore.QTimer()
        self.Timer.setInterval(1000)
        self.Timer.timeout.connect(self.updateText)

        self.form.terminateSolver.clicked.connect(self.killSolverProcess)
        self.form.terminateSolver.setEnabled(False)

        self.open_paraview = QtCore.QProcess()

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

    def consoleMessage(self, message="", color="#000000"):
        self.console_message = self.console_message + \
                               '<font color="#0000FF">{0:4.1f}:</font> <font color="{1}">{2}</font><br>'.\
                               format(time.time() - self.Start, color, message)
        self.form.textEdit_Output.setText(self.console_message)
        self.form.textEdit_Output.moveCursor(QtGui.QTextCursor.End)

    def updateText(self):
        if self.solver_object.Proxy.solver_process.state() == QtCore.QProcess.ProcessState.Running:
            self.form.l_time.setText('Time: ' + CfdTools.formatTimer(time.time() - self.Start))

    def getStandardButtons(self):
        return int(QtGui.QDialogButtonBox.Close)

    def reject(self):
        FreeCADGui.ActiveDocument.resetEdit()

    def closed(self):
        # We call this from unsetEdit to ensure cleanup
        self.solver_object.Proxy.solver_process.terminate()
        self.solver_object.Proxy.solver_process.waitForFinished()
        self.open_paraview.terminate()
        self.Timer.stop()

    def write_input_file_handler(self):
        self.Start = time.time()
        import CfdCaseWriterFoam
        import importlib
        importlib.reload(CfdCaseWriterFoam)
        if self.check_prerequisites_helper():
            self.consoleMessage("Case writer called")
            self.form.pb_paraview.setEnabled(False)
            self.form.pb_edit_inp.setEnabled(False)
            self.form.pb_run_solver.setEnabled(False)
            QApplication.setOverrideCursor(Qt.WaitCursor)
            try:
                FreeCADGui.addModule("CfdCaseWriterFoam")
                FreeCADGui.doCommand("FreeCAD.ActiveDocument." + self.solver_object.Name + ".Proxy.case_writer = "
                                     "CfdCaseWriterFoam.CfdCaseWriterFoam(FreeCAD.ActiveDocument." +
                                     self.solver_runner.analysis.Name + ")")
                FreeCADGui.doCommand("writer = FreeCAD.ActiveDocument." +
                                     self.solver_object.Name + ".Proxy.case_writer")
                writer = self.solver_object.Proxy.case_writer
                writer.progressCallback = self.consoleMessage
                FreeCADGui.doCommand("writer.writeCase()")
            except Exception as e:
                self.consoleMessage("Error writing case:", "#FF0000")
                self.consoleMessage(type(e).__name__ + ": " + str(e), "#FF0000")
                self.consoleMessage("Write case setup file failed", "#FF0000")
                raise
            finally:
                QApplication.restoreOverrideCursor()
            self.updateUI()
            self.form.pb_run_solver.setEnabled(True)
        else:
            self.consoleMessage("Case check failed", "#FF0000")

    def check_prerequisites_helper(self):
        self.consoleMessage("Checking dependencies...")

        message = self.solver_runner.check_prerequisites()
        if message != "":
            self.consoleMessage(message, "#FF0000")
            return False
        return True

    def editSolverInputFile(self):
        case_path = os.path.join(self.working_dir, self.solver_object.InputCaseName)
        self.consoleMessage("Please edit the case input files externally at: {}\n".format(case_path))
        CfdTools.openFileManager(case_path)

    def runSolverProcess(self):
        self.Start = time.time()
        QApplication.setOverrideCursor(Qt.WaitCursor)
        FreeCADGui.addModule("CfdTools")
        FreeCADGui.addModule("CfdConsoleProcess")
        FreeCADGui.doCommand("analysis_object = FreeCAD.ActiveDocument."+self.analysis_object.Name)
        FreeCADGui.doCommand("solver_object = FreeCAD.ActiveDocument."+self.solver_object.Name)
        FreeCADGui.doCommand("working_dir = CfdTools.getOutputPath(analysis_object)")
        FreeCADGui.doCommand("case_name = solver_object.InputCaseName")
        FreeCADGui.doCommand("solver_directory = os.path.abspath(os.path.join(working_dir, case_name))")
        self.solver_object.Proxy.solver_runner = self.solver_runner
        FreeCADGui.doCommand("proxy = FreeCAD.ActiveDocument." + self.solver_object.Name + ".Proxy")
        FreeCADGui.doCommand("proxy.running_from_macro = True")
        self.solver_object.Proxy.running_from_macro = False
        FreeCADGui.doCommand("if proxy.running_from_macro:\n" +
                             "  import CfdRunnableFoam\n" +
                             "  solver_runner = CfdRunnableFoam.CfdRunnableFoam(analysis_object, solver_object)\n" +
                             "else:\n" +
                             "  solver_runner = proxy.solver_runner")
        FreeCADGui.doCommand("cmd = solver_runner.get_solver_cmd(solver_directory)")
        FreeCADGui.doCommand("FreeCAD.Console.PrintMessage(' '.join(cmd)+'\\n')")
        FreeCADGui.doCommand("env_vars = solver_runner.getRunEnvironment()")
        FreeCADGui.doCommand(
            "if proxy.running_from_macro:\n" +
            "  solver_process = CfdConsoleProcess.CfdConsoleProcess(stdoutHook=solver_runner.process_output)\n" +
            "  solver_process.start(cmd, env_vars=env_vars)\n" +
            "  solver_process.waitForFinished()\n" +
            "else:\n" +
            "  proxy.solver_process.start(cmd, env_vars=env_vars)")
        if self.solver_object.Proxy.solver_process.waitForStarted():
            # Setting solve button to inactive to ensure that two instances of the same simulation aren't started
            # simultaneously
            self.form.pb_write_inp.setEnabled(False)
            self.form.pb_run_solver.setEnabled(False)
            self.form.terminateSolver.setEnabled(True)
            self.form.pb_paraview.setEnabled(True)
            self.consoleMessage("Solver started")
        else:
            self.consoleMessage("Error starting solver")
        QApplication.restoreOverrideCursor()

    def killSolverProcess(self):
        self.consoleMessage("Solver manually stopped")
        self.solver_object.Proxy.solver_process.terminate()
        # Note: solverFinished will still be called

    def solverFinished(self, exit_code):
        if exit_code == 0:
            self.consoleMessage("Simulation finished successfully")
        else:
            self.consoleMessage("Simulation exited with error", "#FF0000")
        self.form.pb_write_inp.setEnabled(True)
        self.form.pb_run_solver.setEnabled(True)
        self.form.terminateSolver.setEnabled(False)

    def gotOutputLines(self, lines):
        self.solver_runner.process_output(lines)

    def gotErrorLines(self, lines):
        print_err = self.solver_object.Proxy.solver_process.processErrorOutput(lines)
        if print_err is not None:
            self.consoleMessage(print_err, "#FF0000")

    def openParaview(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        case_path = os.path.abspath(os.path.join(self.working_dir, self.solver_object.InputCaseName))
        script_name = "pvScript.py"
        try:
            self.open_paraview = CfdTools.startParaview(case_path, script_name, self.consoleMessage)
        finally:
            QApplication.restoreOverrideCursor()
