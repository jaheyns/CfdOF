# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2017 - Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>        *
# *   Copyright (c) 2017 - Johan Heyns (CSIR) <jheyns@csir.co.za>           *
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

from __future__ import print_function
import platform
import os
from PySide import QtCore
import FreeCAD


class CfdConsoleProcess:
    """ Class to run a console process asynchronously, printing output and
    errors to the FreeCAD console and allowing clean termination in Linux
    and Windows """
    def __init__(self, finishedHook=None, stdoutHook=None, stderrHook=None):
        self.process = QtCore.QProcess()
        self.finishedHook = finishedHook
        self.stdoutHook = stdoutHook
        self.stderrHook = stderrHook
        self.process.finished.connect(self.finished)
        self.process.readyReadStandardOutput.connect(self.readStdout)
        self.process.readyReadStandardError.connect(self.readStderr)

    def __del__(self):
        self.terminate()

    def start(self, cmd, env_vars=None, working_dir=None):
        """ Start process and return immediately """
        env = QtCore.QProcessEnvironment.systemEnvironment()
        if env_vars:
            for key in env_vars:
                env.insert(key, env_vars[key])
        self.process.setProcessEnvironment(env)
        if working_dir:
            self.process.setWorkingDirectory(working_dir)
        if platform.system() == "Windows":
            # Run through a wrapper process to allow clean termination
            cmd = [os.path.join(FreeCAD.getHomePath(), "bin", "python.exe"),
                   '-u',  # Prevent python from buffering stdout
                   os.path.join(os.path.dirname(__file__), "WindowsRunWrapper.py")] + cmd
        print("Raw command: ", cmd)
        self.process.start(cmd[0], cmd[1:])

    def terminate(self):
        if platform.system() == "Windows":
            # terminate() doesn't operate and kill() doesnt allow cleanup and leaves mpi processes running
            # Instead, instruct wrapper program to kill child process and itself cleanly with ctrl-break signal
            self.process.write("terminate\n")
            self.process.waitForBytesWritten()  # 'flush'
        else:
            self.process.terminate()
        self.process.waitForFinished()

    def finished(self, exit_code):
        if self.finishedHook:
            self.finishedHook(exit_code)

    def readStdout(self):
        # Ensure only complete lines are passed on
        text = ""
        while self.process.canReadLine():
            text += str(self.process.readLine())
        print(text, end='')  # Avoid displaying on FreeCAD status bar
        if self.stdoutHook:
            self.stdoutHook(text)

    def readStderr(self):
        # Ensure only complete lines are passed on
        # Print any error output to console
        self.process.setReadChannel(QtCore.QProcess.StandardError)
        text = ""
        while self.process.canReadLine():
            text += str(self.process.readLine())
        if self.stderrHook:
            self.stderrHook(text)
        FreeCAD.Console.PrintError(text)
        self.process.setReadChannel(QtCore.QProcess.StandardOutput)

    def state(self):
        return self.process.state()

    def waitForStarted(self):
        return self.process.waitForStarted()

    def waitForFinished(self):
        return self.process.waitForFinished(-1)

    def exitCode(self):
        return self.process.exitCode()
