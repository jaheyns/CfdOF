# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2017 Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>          *
# *   Copyright (c) 2017 Johan Heyns (CSIR) <jheyns@csir.co.za>             *
# *   Copyright (c) 2017 Alfred Bogaers (CSIR) <abogaers@csir.co.za>        *
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

from __future__ import print_function

import platform
import os
import sys
from PySide import QtCore
from PySide.QtCore import QProcess, QTextStream
import FreeCAD

from PySide.QtCore import QT_TRANSLATE_NOOP

class CfdConsoleProcess:
    """
    Class to run a console process asynchronously, printing output and
    errors to the FreeCAD console and allowing clean termination in Linux
    and Windows
    """
    def __init__(self, finished_hook=None, stdout_hook=None, stderr_hook=None):
        self.process = QProcess()
        self.finishedHook = finished_hook
        self.stdoutHook = stdout_hook
        self.stderrHook = stderr_hook
        self.process.finished.connect(self.finished)
        self.process.readyReadStandardOutput.connect(self.readStdout)
        self.process.readyReadStandardError.connect(self.readStderr)
        self.print_next_error_lines = 0
        self.print_next_error_file = False

    def __del__(self):
        self.terminate()

    def start(self, cmd, env_vars=None, working_dir=None):
        """ Start process and return immediately """
        self.print_next_error_lines = 0
        self.print_next_error_file = False
        env = QtCore.QProcessEnvironment.systemEnvironment()
        if env_vars:
            for key in env_vars:
                env.insert(key, env_vars[key])
        removeAppimageEnvironment(env)
        self.process.setProcessEnvironment(env)
        if working_dir:
            self.process.setWorkingDirectory(working_dir)
        if platform.system() == "Windows":
            # Run through a wrapper process to allow clean termination
            cmd = [os.path.join(FreeCAD.getHomePath(), "bin", "python.exe"),
                   '-u',  # Prevent python from buffering stdout
                   os.path.join(os.path.dirname(__file__), "WindowsRunWrapper.py")] + cmd
        FreeCAD.Console.PrintLog("CfdConsoleProcess running command: {}\n".format(cmd))
        self.process.setProgram(cmd[0])
        if platform.system() == "Windows":
            has_cmd = False
            for i, c in enumerate(cmd[1:]):
                f = os.path.basename(c).lower()
                if f == 'cmd' or f == 'cmd.exe':
                    has_cmd = True
                elif has_cmd and c.lower() == '/c':
                    self.process.setArguments(cmd[1:(i+1)])
                    # cmd.exe doesn't follow normal quoting rules for its /c argument, to this must be added unprocessed
                    # using setNativeArguments
                    s = '/S /C ' + '"' + ' '.join(cmd[(i+2):]).replace('\\', '\\\\') + '"'
                    self.process.setNativeArguments(s)
                    break
            if not has_cmd:
                self.process.setArguments(cmd[1:])
        else:
            self.process.setArguments(cmd[1:])
        self.process.start()

    def terminate(self):
        if self.process.state() != QProcess.NotRunning:
            if platform.system() == "Windows":
                # terminate() doesn't operate and kill() doesn't allow cleanup and leaves mpi processes running
                # Instead, instruct wrapper program to kill child process and itself cleanly with ctrl-break signal
                self.process.write(b"terminate\n")
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
            byte_arr = self.process.readLine()
            text += QTextStream(byte_arr).readAll()
        if text:
            if self.stdoutHook:
                new_text = self.stdoutHook(text)
                if new_text:
                    text = new_text
            if text:
                print(text, end='')  # Avoid displaying on FreeCAD status bar
                # Must be at the end as it can cause re-entrance
                if FreeCAD.GuiUp:
                    FreeCAD.Gui.updateGui()

    def readStderr(self):
        # Ensure only complete lines are passed on. Print any error output to console
        self.process.setReadChannel(QProcess.StandardError)
        text = ""
        while self.process.canReadLine():
            byte_arr = self.process.readLine()
            text += QTextStream(byte_arr).readAll()
        self.process.setReadChannel(QProcess.StandardOutput)
        if text:
            if self.stderrHook:
                new_text = self.stderrHook(text)
                if new_text is not None:
                    text = new_text
            if text:
                print(text, end='', file=sys.stderr)  # Avoid displaying on FreeCAD status bar
                # Must be at the end as it can cause re-entrance
                if FreeCAD.GuiUp:
                    FreeCAD.Gui.updateGui()

    def state(self):
        return self.process.state()

    def waitForStarted(self):
        return self.process.waitForStarted()

    def waitForFinished(self):
        # For some reason waitForFinished doesn't always return - so we resort to a failsafe timeout:
        while True:
            ret = self.process.waitForFinished(1000)
            if self.process.error() != QProcess.Timedout:
                self.readStdout()
                self.readStderr()
                return ret
            if self.process.state() == QProcess.NotRunning:
                self.readStdout()
                self.readStderr()
                return True

    def exitCode(self):
        return self.process.exitCode()

    def processErrorOutput(self, err):
        """
        Process standard error text output from OpenFOAM
        :param err: Standard error output, single or multiple lines
        :return: A message to be printed on console, or None
        """
        ret = ""
        err_lines = err.split('\n')
        for err_line in err_lines:
            if len(err_line) > 0:  # Ignore blanks
                if self.print_next_error_lines > 0:
                    ret += err_line + "\n"
                    self.print_next_error_lines -= 1
                if self.print_next_error_file and "file:" in err_line:
                    ret += err_line + "\n"
                    self.print_next_error_file = False
                words = err_line.split(' ', 1)  # Split off first field for parallel
                FATAL = "--> FOAM FATAL ERROR"
                FATAL_IO = "--> FOAM FATAL IO ERROR"
                if err_line.startswith(FATAL) or (len(words) > 1 and words[1].startswith(FATAL)):
                    self.print_next_error_lines = 1
                    ret += "OpenFOAM fatal error:\n"
                elif err_line.startswith(FATAL_IO) or (len(words) > 1 and words[1].startswith(FATAL_IO)):
                    self.print_next_error_lines = 1
                    self.print_next_error_file = True
                    ret += "OpenFOAM IO error:\n"
                elif err_line.startswith("Fatal error:"):
                    ret += err_line
        if len(ret) > 0:
            return ret
        else:
            return None


def removeAppimageEnvironment(env):
    """
    When running from an AppImage, the changes to the system environment can interfere with the running of
    external commands. This tries to remove them.
    """
    if env.contains("APPIMAGE"):
        # Strip any value starting with the appimage directory, to attempt to revert to the system environment
        appdir = env.value("APPDIR")
        keys = env.keys()
        for k in keys:
            vals = env.value(k).split(':')
            newvals = ''
            for val in vals:
                if not val.startswith(appdir):
                    newvals += val + ':'
            newvals = newvals.rstrip(':')
            if newvals:
                env.insert(k, newvals)
            else:
                env.remove(k)
