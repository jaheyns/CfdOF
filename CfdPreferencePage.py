# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2013-2015 - Juergen Riegel <FreeCAD@juergen-riegel.net> *
# *   Copyright (c) 2017-2018 - Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>   *
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
import platform
import urlparse
import urllib

import FreeCAD
import CfdTools
import TemplateBuilder

if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore
    from PySide import QtGui
    from PySide.QtCore import Qt, QRunnable, QObject, QThread
    from PySide.QtGui import QApplication, QDialog

BLUECFD_URL = \
    "https://github.com/blueCFD/Core/releases/download/blueCFD-Core-2017-2/blueCFD-Core-2017-2-win64-setup.exe"
CFMESH_URL = \
    "https://sourceforge.net/projects/cfmesh-cfdof/files/cfmesh-cfdof.zip/download"
CFMESH_FILE_BASE = "cfmesh-cfdof"
CFMESH_FILE_EXT = ".zip"

# Tasks for the worker thread
DOWNLOAD_BLUECFD = 1
DOWNLOAD_CFMESH = 2


class CfdPreferencePage:
    def __init__(self):
        ui_path = os.path.join(os.path.dirname(__file__), "CfdPreferencePage.ui")
        self.form = FreeCADGui.PySideUic.loadUi(ui_path)

        self.form.tb_choose_foam_dir.clicked.connect(self.chooseFoamDir)
        self.form.le_foam_dir.textChanged.connect(self.foamDirChanged)
        self.form.pb_run_dependency_checker.clicked.connect(self.runDependencyChecker)
        self.form.pb_download_install_blueCFD.clicked.connect(self.downloadInstallBlueCFD)
        self.form.tb_pick_bluecfd_file.clicked.connect(self.pickBlueCFDFile)
        self.form.pb_download_install_cfMesh.clicked.connect(self.downloadInstallCfMesh)
        self.form.tb_pick_cfmesh_file.clicked.connect(self.pickCfMeshFile)

        self.form.le_bluecfd_url.setText(BLUECFD_URL)
        self.form.le_cfmesh_url.setText(CFMESH_URL)

        self.thread = None
        self.install_process = None

        self.console_message = ""
        self.foam_dir = ""
        self.initial_foam_dir = ""

        self.form.gb_bluecfd.setVisible(platform.system() == 'Windows')

    def __del__(self):
        if self.thread and self.thread.isRunning():
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
        self.initial_foam_dir = str(self.foam_dir)
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
        # Temporarily apply the foam dir selection
        CfdTools.setFoamDir(self.foam_dir)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.consoleMessage("Checking dependencies...")
        msg = CfdTools.checkCfdDependencies()
        if not msg:
            self.consoleMessage("No missing dependencies detected")
        else:
            self.consoleMessage(msg)
        CfdTools.setFoamDir(self.initial_foam_dir)
        QApplication.restoreOverrideCursor()

    def downloadInstallBlueCFD(self):
        if self.createThread():
            self.thread.task = DOWNLOAD_BLUECFD
            self.thread.bluecfd_url = self.form.le_bluecfd_url.text()
            self.thread.start()

    def pickBlueCFDFile(self):
        f, filter = QtGui.QFileDialog().getOpenFileName(title='Choose BlueCFD install file', filter="*.exe")
        if f and os.access(f, os.W_OK):
            self.form.le_bluecfd_url.setText(urlparse.urljoin('file:', urllib.pathname2url(f)))

    def downloadInstallCfMesh(self):
        if self.createThread():
            self.thread.task = DOWNLOAD_CFMESH
            # We are forced to apply the foam dir selection - reset when the task finishes
            CfdTools.setFoamDir(self.foam_dir)
            self.thread.cfmesh_url = self.form.le_cfmesh_url.text()
            self.thread.start()

    def pickCfMeshFile(self):
        f, filter = QtGui.QFileDialog().getOpenFileName(title='Choose cfMesh archive', filter="*.zip")
        if f and os.access(f, os.W_OK):
            self.form.le_cfmesh_url.setText(urlparse.urljoin('file:', urllib.pathname2url(f)))

    def createThread(self):
        if self.thread and self.thread.isRunning():
            self.consoleMessage("Busy - please wait...", '#FF0000')
            return False
        else:
            self.thread = CfdPreferencePageThread()
            self.thread.signals.error.connect(self.threadError)
            self.thread.signals.finished.connect(self.threadFinished)
            self.thread.signals.status.connect(self.threadStatus)
            self.thread.signals.downloadProgress.connect(self.downloadProgress)
            return True

    def threadStatus(self, msg):
        self.consoleMessage(msg)

    def threadError(self, msg):
        self.consoleMessage(msg, '#FF0000')

    def threadFinished(self, status):
        if self.thread.task == DOWNLOAD_CFMESH:
            if status:
                self.consoleMessage("Download completed")
                user_dir = self.thread.user_dir
                self.consoleMessage("Building cfMesh. Lengthy process - please wait...")
                if CfdTools.getFoamRuntime() == "BlueCFD":
                    script_name = "buildCfMeshOnBlueCFD.sh"
                    self.consoleMessage("Log file: {}\\log.{}".format(user_dir, script_name))
                    TemplateBuilder.TemplateBuilder(user_dir,
                                                    os.path.join(CfdTools.get_module_path(), 'data', 'foamUserDir'),
                                                    {'cfMeshDirectory': CFMESH_FILE_BASE})
                    self.install_process = CfdTools.startFoamApplication(
                        "./"+script_name, "$WM_PROJECT_USER_DIR", self.installFinished)
                else:
                    self.consoleMessage("Log file: {}/{}/log.Allwmake".format(user_dir, CFMESH_FILE_BASE))
                    self.install_process = CfdTools.startFoamApplication(
                        "./Allwmake", "$WM_PROJECT_USER_DIR/"+CFMESH_FILE_BASE, self.installFinished)
                # Reset foam dir for now in case the user presses 'Cancel'
                CfdTools.setFoamDir(self.initial_foam_dir)
            else:
                self.consoleMessage("Download unsuccessful")
        self.thread = None

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
        self.bluecfd_url = None
        self.cfmesh_url = None

    def run(self):
        try:
            if self.task == DOWNLOAD_BLUECFD:
                self.downloadBlueCFD()
            elif self.task == DOWNLOAD_CFMESH:
                self.downloadCfMesh()
        except Exception as e:
            self.signals.error.emit(str(e))
            self.signals.finished.emit(False)
            raise
        self.signals.finished.emit(True)

    def downloadBlueCFD(self):
        self.signals.status.emit("Downloading blueCFD-Core, please wait...")
        try:
            import urllib
            (filename, headers) = urllib.urlretrieve(self.bluecfd_url, reporthook=self.downloadStatus)
        except Exception as ex:
            raise Exception("Error downloading blueCFD-Core: {}".format(str(ex)))
        self.signals.status.emit("blueCFD-Core downloaded to {}".format(filename))

        if QtCore.QProcess().startDetached(filename):
            self.signals.status.emit("blueCFD-Core installer launched - please complete the installation")
        else:
            raise Exception("Failed to launch blueCFD-Core installer")

    def downloadCfMesh(self):
        self.signals.status.emit("Downloading cfMesh, please wait...")

        self.user_dir = CfdTools.runFoamCommand("echo $WM_PROJECT_USER_DIR").rstrip().split('\n')[-1]
        self.user_dir = CfdTools.reverseTranslatePath(self.user_dir)

        try:
            import urllib
            # Work around for certificate issues
            import ssl
            urllib._urlopener = urllib.FancyURLopener(context=ssl._create_unverified_context())
            # Download
            (filename, header) = urllib.urlretrieve(self.cfmesh_url,
                                                    reporthook=self.downloadStatus)
        except Exception as ex:
            raise Exception("Error downloading cfMesh: {}".format(str(ex)))

        self.signals.status.emit("Extracting cfMesh...")
        CfdTools.runFoamCommand(
            '{{ mkdir -p "$WM_PROJECT_USER_DIR" && cd "$WM_PROJECT_USER_DIR" && unzip -o "{}"; }}'.
            format(CfdTools.translatePath(filename)))

    def downloadStatus(self, blocks, block_size, total_size):
        self.signals.downloadProgress.emit(blocks*block_size, total_size)
