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

"""
Naming is not consistent in this file
solver specific setting is removed from ui
"""

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

        self.writer_thread = QtCore.QThreadPool()
        self.writer_thread.setMaxThreadCount(1)  # Only allow one concurrent case writer to be triggered
        self.solver_runner.writer.setAutoDelete(False)  # Don't delete object once writer is run
        self.solver_runner.writer.signals.error.connect(self.writerError)
        self.solver_runner.writer.signals.finished.connect(self.writerFinished)

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

        # Connect Signals and Slots
        QtCore.QObject.connect(self.form.tb_choose_working_dir, QtCore.SIGNAL("clicked()"), self.choose_working_dir)
        QtCore.QObject.connect(self.form.pb_write_inp, QtCore.SIGNAL("clicked()"), self.write_input_file_handler)
        QtCore.QObject.connect(self.form.pb_edit_inp, QtCore.SIGNAL("clicked()"), self.editSolverInputFile)
        QtCore.QObject.connect(self.form.pb_run_solver, QtCore.SIGNAL("clicked()"), self.runSolverProcess)
        # QtCore.QObject.connect(self.form.pb_show_result, QtCore.SIGNAL("clicked()"), self.showResult)
        QtCore.QObject.connect(self.form.pb_paraview, QtCore.SIGNAL("clicked()"), self.openParaview)
        # self.form.pb_show_result.setEnabled(False)

        QtCore.QObject.connect(self.Timer, QtCore.SIGNAL("timeout()"), self.updateText)
        self.Start = time.time()
        self.update()  # update UI from FemSolverObject, like WorkingDir

    def consoleMessage(self, message="", color="#000000"):
        self.console_message = self.console_message + \
                               '<font color="#0000FF">{0:4.1f}:</font> <font color="{1}">{2}</font><br>'.\
                               format(time.time() - self.Start, color, message.encode('utf-8', 'replace'))
        self.form.textEdit_Output.setText(self.console_message)
        self.form.textEdit_Output.moveCursor(QtGui.QTextCursor.End)

    def updateText(self):
        pass
        if self.solver_run_process.state() == QtCore.QProcess.ProcessState.Running or \
                self.writer_thread.activeThreadCount() > 0:
            self.form.l_time.setText('Time: {0:4.1f}'.format(time.time() - self.Start))

    def getStandardButtons(self):
        return int(QtGui.QDialogButtonBox.Close)

    def update(self):
        if CfdTools.checkWorkingDir(self.solver_object.WorkingDir):
            self.form.le_working_dir.setText(self.solver_object.WorkingDir)
        else:
            wd = CfdTools.getTempWorkingDir()
            self.solver_object.WorkingDir = wd
            self.form.le_working_dir.setText(wd)
        return

    def accept(self):
        FreeCADGui.ActiveDocument.resetEdit()

    def reject(self):
        self.solver_run_process.terminate()
        self.solver_run_process.waitForFinished()
        self.solver_runner.cleanUp()
        import platform
        if platform.system() == "Windows":
            # Hard kill should not be necessary for a GUI application but there appears to be a bug in Windows or Qt
            self.open_paraview.kill()
        else:
            self.open_paraview.terminate()
        self.open_paraview.waitForFinished()
        FreeCADGui.ActiveDocument.resetEdit()

    def choose_working_dir(self):
        current_wd = self.solver_object.WorkingDir
        wd = QtGui.QFileDialog.getExistingDirectory(None,
                                                    'Choose Solver working directory',
                                                    current_wd)
        info_obj = self.solver_object
        if wd and os.access(wd, os.W_OK):
            info_obj.WorkingDir = wd
        else:
            info_obj.WorkingDir = current_wd
        self.form.le_working_dir.setText(info_obj.WorkingDir)

    def write_input_file_handler(self):
        self.Start = time.time()
        if self.check_prerequisites_helper():
            self.consoleMessage("{} case writer is called".format(self.solver_object.SolverName))
            self.form.pb_paraview.setEnabled(False)
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.writer_thread.start(self.solver_runner.writer)
        else:
            self.consoleMessage("Case check failed", "#FF0000")

    def writerError(self, error_msg):
        self.consoleMessage("Error writing case:", "#FF0000")
        self.consoleMessage(str(error_msg), "#FF0000")

    def writerFinished(self, success):
        if success:
            self.consoleMessage("Write {} case is completed".format(self.solver_object.SolverName))
            self.form.pb_edit_inp.setEnabled(True)
            self.form.pb_run_solver.setEnabled(True)
        else:
            self.consoleMessage("Write case setup file failed", "#FF0000")
        QApplication.restoreOverrideCursor()

    def check_prerequisites_helper(self):
        self.consoleMessage("Checking dependencies...")

        message = self.solver_runner.check_prerequisites()
        if message != "":
            self.consoleMessage(message, "#FF0000")
            return False
        return True

    def editSolverInputFile(self):
        self.Start = time.time()
        solverDirectory = os.path.join(self.solver_object.WorkingDir, self.solver_object.InputCaseName)
        self.consoleMessage("Please edit the case input files externally at: {}\n".format(solverDirectory))
        self.solver_runner.edit_case()

    def runSolverProcess(self):
        self.Start = time.time()

        solverDirectory = os.path.join(self.solver_object.WorkingDir, self.solver_object.InputCaseName)
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
        print_err = self.solver_runner.processErrorOutput(lines)
        if print_err is not None:
            self.consoleMessage(print_err, "#FF0000")

    def openParaview(self):
        self.Start = time.time()
        QApplication.setOverrideCursor(Qt.WaitCursor)

        script_name = self.solver_runner.getParaviewScript()

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
