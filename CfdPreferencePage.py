# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2013-2015 - Juergen Riegel <FreeCAD@juergen-riegel.net> *
# *   Copyright (c) 2017 - Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>        *
# *   Copyright (c) 2017 - Johan Heyns (CSIR) <jheyns@csir.co.za>           *
# *   Copyright (c) 2017 - Alfred Bogaers (CSIR) <abogaers@csir.co.za>      *
# *   Copyright (c) 2016 - Qingfeng Xia <qingfeng.xia()eng.ox.ac.uk>        *
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

__title__ = "CFD preference page"
__author__ = "OO, JH, AB"
__url__ = "http://www.freecadweb.org"

import os
import os.path
import shutil
import platform
import zipfile
import tempfile

import FreeCAD
import CfdTools
import CfdConsoleProcess

if FreeCAD.GuiUp:
    import FreeCADGui
    import FemGui
    from PySide import QtCore
    from PySide import QtGui
    from PySide.QtCore import Qt, QRunnable, QObject, QThread
    from PySide.QtGui import QApplication, QDialog

BLUECFD_URL = \
    "https://github.com/blueCFD/Core/releases/download/blueCFD-Core-2016-2/blueCFD-Core-2016-2-win64-setup.exe"
GNUPLOTPY_URL = "https://sourceforge.net/projects/gnuplot-py/files/Gnuplot-py/1.8/gnuplot-py-1.8.zip/download"
GNUPLOTPY_FILE_BASE = "gnuplot-py-1.8"
CFMESH_URL = "https://sourceforge.net/projects/cfmesh/files/v1.1.2/cfMesh-v1.1.2.tgz/download"
CFMESH_FILE_BASE = "cfMesh-v1.1.2"
CFMESH_FILE_EXT = ".tar.gz"

# Tasks for the worker thread
DEPENDENCY_CHECK = 1
DOWNLOAD_BLUECFD = 2
DOWNLOAD_GNUPLOTPY = 3
DOWNLOAD_CFMESH = 4


class CfdPreferencePage:
    def __init__(self):
        ui_path = os.path.join(os.path.dirname(__file__), "CfdPreferencePage.ui")
        self.form = FreeCADGui.PySideUic.loadUi(ui_path)

        self.form.tb_choose_foam_dir.clicked.connect(self.chooseFoamDir)
        self.form.le_foam_dir.textChanged.connect(self.foamDirChanged)
        self.form.pb_run_dependency_checker.clicked.connect(self.runDependencyChecker)
        self.form.pb_download_install_blueCFD.clicked.connect(self.downloadInstallBlueCFD)
        self.form.pb_download_install_Gnuplotpy.clicked.connect(self.downloadInstallGnuplotpy)
        self.form.pb_download_install_cfMesh.clicked.connect(self.downloadInstallCfMesh)

        self.thread = CfdPreferencePageThread()
        self.thread.signals.error.connect(self.threadError)
        self.thread.signals.finished.connect(self.threadFinished)
        self.thread.signals.status.connect(self.threadStatus)
        self.thread.signals.downloadProgress.connect(self.downloadProgress)

        self.install_process = None

        self.console_message = ""
        self.foam_dir = ""

        self.form.pb_download_install_blueCFD.setVisible(platform.system() == 'Windows')

    def __del__(self):
        if self.thread.isRunning():
            FreeCAD.Console.PrintMessage("Terminating a pending install task")
            self.thread.terminate()
        if self.install_process and self.install_process.state() == QtCore.QProcess.Running:
            FreeCAD.Console.PrintMessage("Terminating a pending install task")
            self.install_process.terminate()
        QApplication.restoreOverrideCursor()

    def saveSettings(self):
        CfdTools.setFoamDir(self.foam_dir)

    def loadSettings(self):
        # Don't set the autodetected location, since the user might want to allow that to vary according
        # to WM_PROJECT_DIR setting
        prefs = CfdTools.getPreferencesLocation()
        self.foam_dir = FreeCAD.ParamGet(prefs).GetString("InstallationPath", "")
        self.form.le_foam_dir.setText(self.foam_dir)

    def consoleMessage(self, message="", color="#000000"):
        message = message.replace('\n', '<br>')
        self.console_message = self.console_message + \
            '<font color="{0}">{1}</font><br>'.format(color, message.encode('utf-8', 'replace'))
        self.form.textEdit_Output.setText(self.console_message)
        self.form.textEdit_Output.moveCursor(QtGui.QTextCursor.End)

    def foamDirChanged(self, text):
        self.foam_dir = text

    def chooseFoamDir(self):
        d = QtGui.QFileDialog().getExistingDirectory(None, 'Choose OpenFOAM directory', self.foam_dir)
        if d and os.access(d, os.W_OK):
            self.foam_dir = d
        self.form.le_foam_dir.setText(self.foam_dir)

    def runDependencyChecker(self):
        self.thread.task = DEPENDENCY_CHECK
        self.startThread()
        QApplication.setOverrideCursor(Qt.WaitCursor)

    def downloadInstallBlueCFD(self):
        self.thread.task = DOWNLOAD_BLUECFD
        self.startThread()

    def downloadInstallGnuplotpy(self):
        self.thread.task = DOWNLOAD_GNUPLOTPY
        self.startThread()

    def downloadInstallCfMesh(self):
        self.thread.task = DOWNLOAD_CFMESH
        self.startThread()

    def startThread(self):
        if self.thread.isRunning():
            self.consoleMessage("Process already running...", '#FF0000')
        else:
            self.thread.start()

    def threadStatus(self, msg):
        self.consoleMessage(msg)

    def threadError(self, msg):
        self.consoleMessage(msg, '#FF0000')

    def threadFinished(self, status):
        if self.thread.task == DEPENDENCY_CHECK:
            QApplication.restoreOverrideCursor()

        elif self.thread.task == DOWNLOAD_GNUPLOTPY:
            self.consoleMessage("Attempting to install Gnuplot-py package:")

            if platform.system() == 'Windows':
                python_exe = os.path.join(FreeCAD.getHomePath(), 'bin', 'python.exe')
            else:
                python_exe = 'python'
            cmd = [python_exe, '-u', 'setup.py', 'install']

            working_dir = os.path.join(tempfile.gettempdir(), GNUPLOTPY_FILE_BASE)
            self.install_process = CfdConsoleProcess.CfdConsoleProcess(finishedHook=self.installFinished)
            print("Running {} in {}".format(' '.join(cmd), working_dir))

            self.install_process.start(cmd, working_dir=working_dir)
            if not self.install_process.waitForStarted():
                self.consoleMessage("Unable to run command " + ' '.join(cmd), '#FF0000')

        elif self.thread.task == DOWNLOAD_CFMESH:
            if status:
                self.consoleMessage("Download completed")
                user_dir = self.thread.user_dir
                self.consoleMessage("Building cfMesh. Lengthy process - please wait...")
                if CfdTools.getFoamRuntime() == "BlueCFD":
                    script_name = "buildCfMeshOnBlueCFD.sh"
                    self.consoleMessage("Log file: {}\\log.{}".format(user_dir, script_name))
                    shutil.copy(os.path.join(CfdTools.get_module_path(), 'data', script_name),
                                os.path.join(user_dir, script_name))
                    self.install_process = CfdTools.startFoamApplication(
                        "./"+script_name, "$WM_PROJECT_USER_DIR", self.installFinished)
                else:
                    self.consoleMessage("Log file: {}/{}/log.Allwmake".format(user_dir, CFMESH_FILE_BASE))
                    self.install_process = CfdTools.startFoamApplication(
                        "./Allwmake", "$WM_PROJECT_USER_DIR/"+CFMESH_FILE_BASE, self.installFinished)
            else:
                self.consoleMessage("Download unsuccessful")

    def installFinished(self, exit_code):
        if exit_code:
            self.consoleMessage("Install finished with error {}".format(exit_code))
        else:
            self.consoleMessage("Install completed")

    def downloadProgress(self, bytes_done, bytes_total):
        mb_done = float(bytes_done)/(1024*1024)
        msg = "Downloaded {:.2f} MB".format(mb_done)
        if bytes_total > 0:
            msg += " of {:.2f} MB".format(int(bytes_total/(1024*1024)))
        self.form.labelDownloadProgress.setText(msg)


class CfdPreferencePageSignals(QObject):
    error = QtCore.Signal(str)  # Signal in PySide, pyqtSignal in PyQt
    finished = QtCore.Signal(bool)
    status = QtCore.Signal(str)
    downloadProgress = QtCore.Signal(int, int)


class CfdPreferencePageThread(QThread):
    """ Worker thread to complete tasks in preference page """
    def __init__(self):
        super(CfdPreferencePageThread, self).__init__()
        self.signals = CfdPreferencePageSignals()
        self.user_dir = None
        self.task = None

    def run(self):
        try:
            if self.task == DEPENDENCY_CHECK:
                self.dependencyCheck()
            elif self.task == DOWNLOAD_BLUECFD:
                self.downloadBlueCFD()
            elif self.task == DOWNLOAD_GNUPLOTPY:
                self.downloadGnuplotpy()
            elif self.task == DOWNLOAD_CFMESH:
                self.downloadCfMesh()
        except Exception as e:
            self.signals.error.emit(str(e))
            self.signals.finished.emit(False)
            raise
        self.signals.finished.emit(True)

    def dependencyCheck(self):
        self.signals.status.emit("Checking dependencies...")
        msg = CfdTools.checkCfdDependencies()
        if not msg:
            self.signals.status.emit("No missing dependencies detected")
        else:
            self.signals.status.emit(msg)

    def downloadBlueCFD(self):
        self.signals.status.emit("Downloading blueCFD-Core, please wait...")
        try:
            import urllib
            (filename, headers) = urllib.urlretrieve(BLUECFD_URL, reporthook=self.downloadStatus)
        except Exception as ex:
            raise Exception("Error downloading blueCFD-Core: {}".format(str(ex)))
        self.signals.status.emit("blueCFD-Core downloaded to {}".format(filename))

        if QtCore.QProcess().startDetached(filename):
            self.signals.status.emit("blueCFD-Core installer launched - please complete the installation")
        else:
            raise Exception("Failed to launch blueCFD-Core installer")

    def downloadGnuplotpy(self):
        self.signals.status.emit("Downloading Gnuplot-py, please wait...")
        try:
            import urllib
            (filename, headers) = urllib.urlretrieve(GNUPLOTPY_URL, reporthook=self.downloadStatus)
        except Exception as ex:
            raise Exception("Error downloading Gnuplot-py: {}".format(str(ex)))

        self.signals.status.emit("Extracting {} in {}".format(filename, tempfile.gettempdir()))
        with zipfile.ZipFile(filename, 'r') as z:
            z.extractall(tempfile.gettempdir())

    def downloadCfMesh(self):
        self.signals.status.emit("Downloading cfMesh, please wait...")

        self.user_dir = CfdTools.runFoamCommand("echo $WM_PROJECT_USER_DIR").rstrip().split('\n')[-1]
        self.user_dir = CfdTools.reverseTranslatePath(self.user_dir)

        try:
            import urllib
            (filename, header) = urllib.urlretrieve(CFMESH_URL,
                                                    reporthook=self.downloadStatus)
        except Exception as ex:
            raise Exception("Error downloading cfMesh: {}".format(str(ex)))

        self.signals.status.emit("Extracting cfMesh...")
        CfdTools.runFoamCommand(
            '{{ mkdir -p "$WM_PROJECT_USER_DIR"; cd "$WM_PROJECT_USER_DIR"; tar -xzf "{}"; }}'.
            format(CfdTools.translatePath(filename)))

    def downloadStatus(self, blocks, block_size, total_size):
        self.signals.downloadProgress.emit(blocks*block_size, total_size)
