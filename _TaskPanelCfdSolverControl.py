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

import FreeCAD
from FemTools import FemTools
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
        self.fem_prefs = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Fem")

        self.analysis_object = FemGui.getActiveAnalysis()

        self.solver_runner = solver_runner_obj
        self.solver_object = solver_runner_obj.solver

        self.writer_thread = QtCore.QThreadPool()
        self.writer_thread.setMaxThreadCount(1)  # Only allow one concurrent case writer to be triggered
        self.solver_runner.writer.setAutoDelete(False)  # Don't delete object once writer is run
        self.solver_runner.writer.signals.error.connect(self.writerError)
        self.solver_runner.writer.signals.finished.connect(self.writerFinished)

        # update UI
        self.fem_console_message = ''

        self.solver_run_process = QtCore.QProcess()
        self.Timer = QtCore.QTimer()
        self.Timer.start(100)

        #self.solver_run_process.readyReadStandardOutput.connect(self.stdoutReady)
        QtCore.QObject.connect(self.solver_run_process, QtCore.SIGNAL("finished(int)"), self.solverFinished)
        QtCore.QObject.connect(self.solver_run_process, QtCore.SIGNAL("readyReadStandardOutput()"), self.plotResiduals)
        QtCore.QObject.connect(self.form.terminateSolver, QtCore.SIGNAL("clicked()"), self.killSolverProcess)
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

    def femConsoleMessage(self, message="", color="#000000"):
        self.fem_console_message = self.fem_console_message + '<font color="#0000FF">{0:4.1f}:</font> <font color="{1}">{2}</font><br>'.\
            format(time.time() - self.Start, color, message.encode('utf-8', 'replace'))
        self.form.textEdit_Output.setText(self.fem_console_message)
        self.form.textEdit_Output.moveCursor(QtGui.QTextCursor.End)

    def updateText(self):
        if self.solver_run_process.state() == QtCore.QProcess.ProcessState.Running or \
                self.writer_thread.activeThreadCount() > 0:
            self.form.l_time.setText('Time: {0:4.1f}'.format(time.time() - self.Start))

    def getStandardButtons(self):
        return int(QtGui.QDialogButtonBox.Close)

    def update(self):
        'fills the widgets with solver properties, and it must exist and writable'
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
        import platform
        if platform.system() == "Windows":
            # This should not be necessary for a GUI application but there appears to be a bug in Windows or Qt
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
            self.femConsoleMessage("{} case writer is called".format(self.solver_object.SolverName))
            self.form.pb_paraview.setEnabled(False)
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.writer_thread.start(self.solver_runner.writer)
        else:
            self.femConsoleMessage("Case check failed", "#FF0000")

    def writerError(self, error_msg):
        self.femConsoleMessage("Error writing case:")
        self.femConsoleMessage(str(error_msg))

    def writerFinished(self, success):
        if success:
            self.femConsoleMessage("Write {} case is completed".format(self.solver_object.SolverName))
            self.form.pb_edit_inp.setEnabled(True)
            self.form.pb_run_solver.setEnabled(True)
        else:
            self.femConsoleMessage("Write case setup file failed", "#FF0000")
        QApplication.restoreOverrideCursor()

    def check_prerequisites_helper(self):
        self.femConsoleMessage("Checking dependencies...")

        message = self.solver_runner.check_prerequisites()
        if message != "":
            self.femConsoleMessage(message, "#FF0000")
            return False
        return True

    def editSolverInputFile(self):
        self.femConsoleMessage("Edit case input file in FreeCAD is not implemented!")
        self.solver_runner.edit_case()

    def runSolverProcess(self):
        self.Start = time.time()
        #self.femConsoleMessage("Run {} at {} with command:".format(self.solver_object.SolverName, self.solver_object.WorkingDir))

        solverDirectory = os.path.join(self.solver_object.WorkingDir, self.solver_object.InputCaseName)
        solverDirectory = os.path.abspath(solverDirectory)
        cmd = self.solver_runner.get_solver_cmd(solverDirectory)
        FreeCAD.Console.PrintMessage(' '.join(cmd) + '\n')
        self.femConsoleMessage("Starting solver command:")
        self.femConsoleMessage(' '.join(cmd))
        self.solver_run_process.setWorkingDirectory(solverDirectory)
        env = QtCore.QProcessEnvironment.systemEnvironment()
        envVars = self.solver_runner.getRunEnvironment()
        for key in envVars:
            env.insert(key, envVars[key])
        self.solver_run_process.setProcessEnvironment(env)
        self.solver_run_process.start(cmd[0], cmd[1:])

        QApplication.setOverrideCursor(Qt.WaitCursor)
        if self.solver_run_process.waitForStarted():
            # Setting solve button to inactive to ensure that two instances of the same simulation aren't started
            # simultaneously
            self.form.pb_run_solver.setEnabled(False)
            self.form.terminateSolver.setEnabled(True)
            # self.form.pb_show_result.setEnabled(False)
            self.form.pb_paraview.setEnabled(True)
            self.femConsoleMessage("Solver started")
        else:
            self.femConsoleMessage("Error starting solver")
        QApplication.restoreOverrideCursor()

    def killSolverProcess(self):
        self.femConsoleMessage("Solver manually stopped")
        import platform
        if platform.system() == "Windows":
            self.solver_run_process.kill()  # Terminal processes don't respond to terminate() on Windows
        else:
            self.solver_run_process.terminate()  # Could use kill() here as well but terminate() is kinder
        self.form.pb_run_solver.setEnabled(True)
        self.form.terminateSolver.setEnabled(False)
        #FreeCAD.Console.PrintMessage("Killing OF solver instance")

    def solverFinished(self):
        #self.femConsoleMessage(self.solver_run_process.exitCode())
        self.femConsoleMessage("Simulation finished")
        self.form.pb_run_solver.setEnabled(True)
        self.form.terminateSolver.setEnabled(False)
    
    def plotResiduals(self):
        # Ensure only complete lines are passed on
        text = ""
        while self.solver_run_process.canReadLine():
            text += str(self.solver_run_process.readLine())
        #FreeCAD.Console.PrintMessage(text)
        print text,  # Avoid displaying on FreeCAD status bar
        self.solver_runner.process_output(text)

        # Print any error output to console
        err = ""
        self.solver_run_process.setReadChannel(QtCore.QProcess.StandardError)
        while self.solver_run_process.canReadLine():
            err += str(self.solver_run_process.readLine())
        FreeCAD.Console.PrintError(err)
        self.solver_run_process.setReadChannel(QtCore.QProcess.StandardOutput)

    def openParaview(self):
        self.Start = time.time()
        QApplication.setOverrideCursor(Qt.WaitCursor)

        script_name = self.solver_runner.create_paraview_script()

        paraview_cmd = "paraview"
        import FoamCaseBuilder
        # If using blueCFD, use paraview supplied
        if FoamCaseBuilder.utility.getFoamRuntime() == 'BlueCFD':
            paraview_cmd = '{}\\..\\AddOns\\ParaView\\bin\\paraview.exe'.format(FoamCaseBuilder.utility.getFoamDir())
        # Otherwise, the command 'paraview' must be in the path. Possibly make path user-settable.
        # Test to see if it exists, as the exception thrown is cryptic on Windows if it doesn't
        import distutils.spawn
        if distutils.spawn.find_executable(paraview_cmd) is None:
            raise IOError("Paraview executable " + paraview_cmd + " not found in path.")

        arg = '--script={}'.format(script_name)

        self.femConsoleMessage("Running "+paraview_cmd+" "+arg)
        self.open_paraview.start(paraview_cmd, [arg])
        QApplication.restoreOverrideCursor()
