# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2013-2015 - Juergen Riegel <FreeCAD@juergen-riegel.net> *
# *   Copyright (c) 2016 - Qingfeng Xia <qingfeng.xia()eng.ox.ac.uk>        *
# *   Copyright (c) 2017 - Alfred Bogaers (CSIR) <abogaers@csir.co.za>      *
# *   Copyright (c) 2017 - Johan Heyns (CSIR) <jheyns@csir.co.za>           *
# *   Copyright (c) 2017 - Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>        *
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

__title__ = "Job Control Task Panel"
__author__ = "Juergen Riegel, Qingfeng Xia"
__url__ = "http://www.freecadweb.org"

import os
import sys
import os.path
import time
import subprocess
from CfdConsoleProcess import CfdConsoleProcess

import FreeCAD
import CfdTools

if FreeCAD.GuiUp:
    import FreeCADGui
    import FemGui
    from PySide import QtCore
    from PySide import QtGui
    from PySide.QtCore import Qt
    from PySide.QtGui import QApplication


class _TaskPanelCfdSolverControl:
    def __init__(self, solver_runner_obj):
        ui_path = os.path.join(os.path.dirname(__file__), "TaskPanelCfdSolverControl.ui")
        self.form = FreeCADGui.PySideUic.loadUi(ui_path)

        self.analysis_object = FemGui.getActiveAnalysis()

        self.solver_runner = solver_runner_obj
        self.solver_object = solver_runner_obj.solver

        # update UI
        self.console_message = ''

        self.solver_run_process = CfdConsoleProcess(finishedHook=self.solverFinished,
                                                    stdoutHook=self.gotOutputLines,
                                                    stderrHook=self.gotErrorLines)
        self.Timer = QtCore.QTimer()
        self.Timer.start(100)

        self.form.terminateSolver.clicked.connect(self.killSolverProcess)
        self.form.terminateSolver.setEnabled(False)

        self.open_paraview = QtCore.QProcess()

        self.working_dir = CfdTools.getOutputPath(self.analysis_object)

        self.updateUI()

        # Connect Signals and Slots
        QtCore.QObject.connect(self.form.pb_write_inp, QtCore.SIGNAL("clicked()"), self.write_input_file_handler)
        QtCore.QObject.connect(self.form.pb_edit_inp, QtCore.SIGNAL("clicked()"), self.editSolverInputFile)
        QtCore.QObject.connect(self.form.pb_run_solver, QtCore.SIGNAL("clicked()"), self.runSolverProcess)
        # QtCore.QObject.connect(self.form.pb_show_result, QtCore.SIGNAL("clicked()"), self.showResult)
        QtCore.QObject.connect(self.form.pb_paraview, QtCore.SIGNAL("clicked()"), self.openParaview)
        # self.form.pb_show_result.setEnabled(False)

        QtCore.QObject.connect(self.Timer, QtCore.SIGNAL("timeout()"), self.updateText)
        self.Start = time.time()

    def updateUI(self):
        self.form.pb_edit_inp.setEnabled(os.path.exists(self.working_dir))
        solverDirectory = os.path.join(self.working_dir, self.solver_object.InputCaseName)
        self.form.pb_paraview.setEnabled(os.path.exists(os.path.join(solverDirectory, "pv.foam")))
        self.form.pb_run_solver.setEnabled(os.path.exists(os.path.join(solverDirectory, "Allrun")))

    def consoleMessage(self, message="", color="#000000"):
        self.console_message = self.console_message + \
                               '<font color="#0000FF">{0:4.1f}:</font> <font color="{1}">{2}</font><br>'.\
                               format(time.time() - self.Start, color, message)
        self.form.textEdit_Output.setText(self.console_message)
        self.form.textEdit_Output.moveCursor(QtGui.QTextCursor.End)

    def updateText(self):
        if self.solver_run_process.state() == QtCore.QProcess.ProcessState.Running:
            self.form.l_time.setText('Time: {0:4.1f}'.format(time.time() - self.Start))

    def getStandardButtons(self):
        return int(QtGui.QDialogButtonBox.Close)

    def accept(self):
        FreeCADGui.ActiveDocument.resetEdit()

    def reject(self):
        self.solver_run_process.terminate()
        self.solver_run_process.waitForFinished()
        import platform
        if platform.system() == "Windows":
            # Hard kill should not be necessary for a GUI application but there appears to be a bug in Windows or Qt
            self.open_paraview.kill()
        else:
            self.open_paraview.terminate()
        self.open_paraview.waitForFinished()
        FreeCADGui.ActiveDocument.resetEdit()

    def write_input_file_handler(self):
        self.Start = time.time()
        if self.check_prerequisites_helper():
            self.consoleMessage("{} case writer is called".format(self.solver_object.SolverName))
            self.form.pb_paraview.setEnabled(False)
            self.form.pb_edit_inp.setEnabled(False)
            self.form.pb_run_solver.setEnabled(False)
            QApplication.setOverrideCursor(Qt.WaitCursor)
            try:
                self.solver_runner.writer.writeCase()
            except Exception as e:
                self.consoleMessage("Error writing case:", "#FF0000")
                self.consoleMessage(str(e), "#FF0000")
                self.consoleMessage("Write case setup file failed", "#FF0000")
                raise
            finally:
                QApplication.restoreOverrideCursor()
            self.consoleMessage("Write {} case is completed".format(self.solver_object.SolverName))
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
        self.Start = time.time()
        solverDirectory = os.path.join(self.working_dir, self.solver_object.InputCaseName)
        self.consoleMessage("Please edit the case input files externally at: {}\n".format(solverDirectory))
        self.solver_runner.edit_case()

    def runSolverProcess(self):
        self.Start = time.time()

        solverDirectory = os.path.join(self.working_dir, self.solver_object.InputCaseName)
        solverDirectory = os.path.abspath(solverDirectory)
        cmd = self.solver_runner.get_solver_cmd(solverDirectory)
        FreeCAD.Console.PrintMessage(' '.join(cmd) + '\n')
        self.consoleMessage("Starting solver command:")
        self.consoleMessage(' '.join(cmd))
        envVars = self.solver_runner.getRunEnvironment()
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.solver_run_process.start(cmd, env_vars=envVars)
        if self.solver_run_process.waitForStarted():
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
        self.solver_run_process.terminate()
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
        print_err = self.solver_run_process.processErrorOutput(lines)
        if print_err is not None:
            self.consoleMessage(print_err, "#FF0000")

    def openParaview(self):
        self.Start = time.time()
        QApplication.setOverrideCursor(Qt.WaitCursor)

        script_name = os.path.abspath(os.path.join(self.working_dir,
                                                   self.solver_object.InputCaseName,
                                                   "pvScript.py"))

        paraview_cmd = "paraview"
        # If using blueCFD, use paraview supplied
        if CfdTools.getFoamRuntime() == 'BlueCFD':
            paraview_cmd = '{}\\..\\AddOns\\ParaView\\bin\\paraview.exe'.format(CfdTools.getFoamDir())
        # Otherwise, the command 'paraview' must be in the path. Possibly make path user-settable.
        # Test to see if it exists, as the exception thrown is cryptic on Windows if it doesn't
        import distutils.spawn
        if distutils.spawn.find_executable(paraview_cmd) is None:
            raise IOError("Paraview executable " + paraview_cmd + " not found in path.")

        arg = '--script={}'.format(script_name)

        self.consoleMessage("Running "+paraview_cmd+" "+arg)
        self.open_paraview.start(paraview_cmd, [arg])
        if self.open_paraview.waitForStarted():
            self.consoleMessage("Paraview started")
        else:
            self.consoleMessage("Error starting paraview")
        QApplication.restoreOverrideCursor()
