

# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2017-2018 Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>     *
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
#
# LinuxGuy123@gmail.com's notes.
#
# This file started out as a simple clone of the CfdPreferencesPage to handle a remote host instead
# of the local host. But with the changes needed to handle multiple host profiles, it changed a lot.
#
# The first iteration of this code was to change it to use a single remote host.
#
# The current iteration of this code now handles multiple remote hosts via host profiles.  This resulted in
# the working parts getting almost complelely rewritten.  This code presently only works with Linux remote hosts
# or at least it has only been tested with Linux remote hosts. I left in many pieces of the old code in case they are
# needed to add Docker, Windows, etc. on the remote host.
#
# How this page works...
# If Use Remote Processing is enabled, the controls are enabled. If not, they aren't.
# The page then loads the profile names from the parameters file.
#
# Then it loads the parameters for the first profile listed in the profile drop down box.
# With these parameters it initializes the controls and the local vars.
# When the users changes a parameter in the gui it is immediately written to the parameter file and
# the local var is updated.
# When the profile is changed the new parameters for the profile are loaded and the local vars
# are updated as are the controls.
#
# This page ignores the OK, Apply and Cancel buttons.   There is a routine to save the current
# profile (saveProfile) on OK, change profile and Apply, but are those buttons are ignored in CfdOF.
# As they were in the previous version. Instead, every field is saved to the local var and the parameter file
# when it is entered.
#
# The remotePreferences GUI file (CfdRemotePreferencePage.ui) file still has many controls that are not used.  See
# enableControls() for a list of what is or isn't used.
# They are set to disabled and not visible so they don't appear in the running GUI. They were left in in case
# they would be needed in the future. But generally the disabled controls don't make sense on a remote host -
# Paraview, for example.  At some point, once the page has been deemed to operate in an acceptable manner, they
# should be removed entirely.
#
# In the initial code I wrote the variables that were used with remote operation had _remote_ in their name. I removed
# them because the var names were pretty long. Now all the vars in this code are assumed to be referring to a remote host.
# The only names that have remote in them are procedures that replaced non remote procedures.  For example runRemoteDependencyCheck.
# I left the code for runDependencyCheck in the file because parts of it may be used if/when Windows or Docker is added for remote hosts.
#
# The reason I'm telling you this is to justify how messy the code is right now. It would be very easy to remove all the unused
# code and clean things up.  But right now the unused code is present in case they are needed in the near future.
#
# This application doesn't install OpenFOAM on the remote host.  It also doesn't install gmsh.  It does install cfmesh
# if OpenFOAM (and OpenFOAM-devel) is installed.
#
# I did not use worker threads to install cfMesh.  I just ran the processes from the ssh command line.
#
# TODO:

# - fix downloadInstallCFMesh   Its broken due to using profiles.  Doesn't stop installing if a step fails.
#   Also requires the working directory folder to be present.  Fails if it isn't.
# - get About Remote Processing document window working - put User's Guide in it
# - put the remote host computer fields in a container like Docker, OpenFOAM, etc.
# - get tooltips working
# - OpenFOAM doesn't need the number of threads and processes like the meshers do.  Remove one.

# Done: get cfMesh URL control working
# Done: implement host profiles so that multiple remote hosts can be used
# Done: store and load the use remote processing boolean
# Done: enable and disable all the controls with the cb_use_remote_processing checkbox result
# Done: store and load the host name and username fields
# Done: get ping host working
# Done: get test ssh working
# Nope: move ping and ssh to CfdOFTools ?
# Done: get remote foam dir storing and loading
# Done: remote gmsh path storing and loading
# Done: remote work dir storing and loading
# Done: get download and install cfMesh working

#********************************************************************************

import os
import os.path
import platform
import sys
if sys.version_info >= (3,):  # Python 3
    import urllib.request as urlrequest
    import urllib.parse as urlparse
else:
    import urllib as urlrequest
    import urlparse

 #import traceback  #This as used during debugging

import ssl
import ctypes
import FreeCAD
from CfdOF import CfdTools
import tempfile
from contextlib import closing
from xml.sax.saxutils import escape

if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore
    from PySide import QtGui
    from PySide.QtCore import Qt, QObject, QThread
    from PySide.QtGui import QApplication


# Constants
OPENFOAM_URL = \
    "https://sourceforge.net/projects/openfoam/files/v2206/OpenFOAM-v2206-windows-mingw.exe/download"
OPENFOAM_FILE_EXT = ".exe"
PARAVIEW_URL = \
    "https://www.paraview.org/paraview-downloads/download.php?submit=Download&version=v5.10&type=binary&os=Windows&downloadFile=ParaView-5.10.1-Windows-Python3.9-msvc2017-AMD64.exe"
PARAVIEW_FILE_EXT = ".exe"
CFMESH_URL = \
    "https://sourceforge.net/projects/cfmesh-cfdof/files/cfmesh-cfdof.zip/download"
CFMESH_URL_MINGW = \
    "https://sourceforge.net/projects/cfmesh-cfdof/files/cfmesh-cfdof-binaries-{}.zip/download"
CFMESH_FILE_BASE = "cfmesh-cfdof"
CFMESH_FILE_EXT = ".zip"
HISA_URL = \
    "https://sourceforge.net/projects/hisa/files/hisa-master.zip/download"
HISA_URL_MINGW = \
    "https://sourceforge.net/projects/hisa/files/hisa-master-binaries-{}.zip/download"
HISA_FILE_BASE = "hisa-master"
HISA_FILE_EXT = ".zip"
DOCKER_URL = \
    "docker.io/mmcker/cfdof-openfoam"

OPENFOAM_DIR = "/usr/lib/openfoam/openfoam2206"


# Tasks for the worker thread
# Not used anymore
DOWNLOAD_OPENFOAM = 1
DOWNLOAD_PARAVIEW = 2
DOWNLOAD_CFMESH = 3
DOWNLOAD_HISA = 4
DOWNLOAD_DOCKER = 5


class CloseDetector(QObject):
    def __init__(self, obj, callback):
        super().__init__(obj)
        self.callback = callback

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.ChildRemoved:
            self.callback()
        return False


#*************************************************************************

class CfdRemotePreferencePage:
    def __init__(self):

        # load the page
        ui_path = os.path.join(CfdTools.getModulePath(), 'Gui', "CfdRemotePreferencePage.ui")
        self.form = FreeCADGui.PySideUic.loadUi(ui_path)

        # set the preferences parameters location
        self.prefs_location = CfdTools.getPreferencesLocation()

        # get the use remote processing parameter and set the use RP control
        self.use_remote_processing = FreeCAD.ParamGet(self.prefs_location).GetBool("UseRemoteProcessing")
        self.form.cb_use_remote_processing.setChecked(self.use_remote_processing)

        #enable controls appropriately
        self.enableControls(self.use_remote_processing)

        # connect the handler for remote_processing.clicked
        self.form.cb_use_remote_processing.clicked.connect(self.useRemoteProcessingChanged)

        #TODOself.form.cb_use_remote_processing.setToolTip("Remote processing is
        # the use of a remote computer to run meshing and OpenFOAM operations")

        # set up the profiles combo box        
        self.form.cb_profile.currentIndexChanged.connect(self.profileChanged)

        # connect the hostname and username controls
        self.form.le_hostname.textChanged.connect(self.hostnameChanged)
        self.form.le_username.textChanged.connect(self.usernameChanged)

        #connect the ping and ssh test push buttons
        self.form.pb_ping_host.clicked.connect(self.pingHost)
        self.form.pb_test_ssh.clicked.connect(self.testSSH)

        #connect the mesh and foam processes and threads controls
        self.form.le_mesh_threads.textChanged.connect(self.meshThreadsChanged)
        self.form.le_mesh_processes.textChanged.connect(self.meshProcessesChanged)
        self.form.le_foam_threads.textChanged.connect(self.foamThreadsChanged)
        self.form.le_foam_processes.textChanged.connect(self.foamProcessesChanged)

        # connect the foam_dir changed control
        #self.form.tb_choose_remote_foam_dir.clicked.connect(self.chooseFoamDir)
        self.form.le_foam_dir.textChanged.connect(self.foamDirChanged)

        #connect the add filename to output control
        self.form.cb_add_filename_to_output.clicked.connect(self.addFilenameToOutputChanged)

        self.form.cb_copy_back.clicked.connect(self.copyBackChanged)
        self.form.cb_delete_remote_results.clicked.connect(self.deleteRemoteResultsChanged)



        # connect handlers for various control events
        # note: some of these aren't actually used.  Code left in tact anyway
        self.form.tb_choose_paraview_path.clicked.connect(self.chooseParaviewPath)
        self.form.le_paraview_path.textChanged.connect(self.paraviewPathChanged)

        self.form.tb_choose_remote_gmsh_path.clicked.connect(self.chooseGmshPath)
        self.form.le_gmsh_path.textChanged.connect(self.gmshPathChanged)

        self.form.pb_run_dependency_checker.clicked.connect(self.runRemoteDependencyChecker)
        self.form.pb_download_install_openfoam.clicked.connect(self.downloadInstallOpenFoam)
        self.form.tb_pick_openfoam_file.clicked.connect(self.pickOpenFoamFile)
        self.form.pb_download_install_paraview.clicked.connect(self.downloadInstallParaview)
        self.form.tb_pick_paraview_file.clicked.connect(self.pickParaviewFile)

        self.form.pb_download_install_cfMesh.clicked.connect(self.remoteDownloadInstallCfMesh)
        self.form.tb_pick_cfmesh_file.clicked.connect(self.pickCfMeshFile)
        self.form.pb_download_install_hisa.clicked.connect(self.downloadInstallHisa)
        self.form.tb_pick_hisa_file.clicked.connect(self.pickHisaFile)

        self.form.pb_add_profile.clicked.connect(self.addProfile)
        self.form.pb_delete_profile.clicked.connect(self.deleteProfile)

        # initialize general things with defaults
        # this gets done from loadProfile() now.
        # self.form.le_openfoam_url.setText(OPENFOAM_URL)
        # self.form.le_paraview_url.setText(PARAVIEW_URL)

        self.form.tb_choose_remote_output_dir.clicked.connect(self.chooseOutputDir)
        self.form.le_output_path.textChanged.connect(self.outputPathChanged)

        self.form.cb_docker_sel.clicked.connect(self.dockerCheckboxClicked)
        self.form.pb_download_install_docker.clicked.connect(self.downloadInstallDocker)

        self.dockerCheckboxClicked()

        self.ev_filter = CloseDetector(self.form, self.cleanUp)
        self.form.installEventFilter(self.ev_filter)

        # set global vars
        self.thread = None
        self.install_process = None

        self.console_message = ""

        #setting these here so they get created as globals
        #they also get initiated in loadProfile()
        # self.use_remote_processing = False <- this is set above before the control is loaded

        self.profile_name = ""
        self.host_prefs_location = ""
        self.hostname = ""
        self.username = ""
        self.mesh_processes = 0
        self.mesh_threads = 0
        self.foam_processes = 0
        self.foam_threads = 0
        self.foam_dir = ""
        self.output_path = ""
        self.gmsh_path = ""
        self.add_filename_to_output = False
        self.delete_remote_results = False
        self.copy_back = False

        # TODO:fix these references
        # if they are still used. Most are not.
        #self.initial_remote_foam_dir = ""
        #self.paraview_path = ""
        #self.initial_paraview_path = ""
        #self.initial_remote_gmsh_path = ""
        #self.remote_output_dir = ""

        # not sure what this is for
        self.form.gb_openfoam.setVisible(platform.system() == 'Windows')
        self.form.gb_paraview.setVisible(platform.system() == 'Windows')

        # now load the profiles into the combo box
        self.loadProfileNames()

        #now load the top profile
        self.loadProfile(self.form.cb_profile.currentText())


    # enable/disable the controls on this page
    def enableControls(self,value):

        self.form.cb_profile.setEnabled(value)
        self.form.pb_add_profile.setEnabled(value)
        self.form.pb_delete_profile.setEnabled(value)

        self.form.le_hostname.setEnabled(value)
        self.form.le_username.setEnabled(value)
        self.form.pb_ping_host.setEnabled(value)
        self.form.pb_test_ssh.setEnabled(value)

        self.form.le_mesh_processes.setEnabled(value)
        self.form.le_mesh_threads.setEnabled(value)
        self.form.le_foam_processes.setEnabled(value)
        self.form.le_foam_threads.setEnabled(value)

        self.form.le_foam_dir.setEnabled(value)
        self.form.le_output_path.setEnabled(value)
        self.form.cb_add_filename_to_output.setEnabled(value)

        self.form.pb_run_dependency_checker.setEnabled(value)

        self.form.pb_download_install_cfMesh.setEnabled(value)
        self.form.le_cfmesh_url.setEnabled(value)
        self.form.le_cfmesh_url.setText(CFMESH_URL)

        self.form.cb_copy_back.setEnabled(value)
        self.form.cb_delete_remote_results.setEnabled(value)
        self.form.cb_add_filename_to_output.setEnabled(value)


        # Controls below here are not yet operational regardless of if remote processing
        # is enabled or not.  So they are disabled.  Change this as new functionality
        # is added to the page
        value = False


        self.form.pb_about_remote_processing.setEnabled(value)

        # disable the foam path chooser
        self.form.tb_choose_remote_foam_dir.setEnabled(value)
        self.form.tb_choose_remote_foam_dir.setVisible(value)

        # disable paraview stuff and make it invisible because we
        # don't run paraview on the remote computer
        # This makes it disappear from the page but allows us to
        # leave the controls and code in place
        self.form.le_paraview_path.setEnabled(value)
        self.form.le_paraview_path.setVisible(False)
        self.form.lbl_remote_paraview_path.setVisible(False)
        self.form.tb_choose_paraview_path.setEnabled(value)
        self.form.tb_choose_paraview_path.setVisible(False)

        # disable the gmsh path
        # we don't need to know gmsh's path in Linux.  Either it is installed or not
        # we just call it from the shell,  This might change if the remote host is running
        # a different OS.
        self.form.lbl_gmsh_path.setVisible(False)
        self.form.le_gmsh_path.setEnabled(value)
        self.form.le_gmsh_path.setVisible(False)
        self.form.tb_choose_remote_gmsh_path.setEnabled(value)
        self.form.tb_choose_remote_gmsh_path.setVisible(value)

        #disable the output path chooser
        self.form.tb_choose_remote_output_dir.setEnabled(value)
        self.form.tb_choose_remote_output_dir.setVisible(False)


        # disable docker stuff.  Setting it to invisible does not
        # make it disappear.
        self.form.gb_docker.setEnabled(False)
        self.form.gb_docker.setVisible(False)

        self.form.pb_download_install_openfoam.setEnabled(value)
        self.form.tb_pick_openfoam_file.setEnabled(value)

        self.form.pb_download_install_paraview.setEnabled(value)
        self.form.tb_pick_paraview_file.setEnabled(value)

        self.form.cb_docker_sel.setEnabled(value)
        self.form.le_docker_url.setEnabled(value)
        self.form.pb_download_install_docker.setEnabled(value)

        self.form.tb_pick_cfmesh_file.setEnabled(value)
        #self.form.pb_download_install_cfMesh.setEnabled(value)

        self.form.pb_download_install_hisa.setEnabled(value)
        self.form.tb_pick_hisa_file.setEnabled(value)
        self.form.le_hisa_url.setEnabled(value)
        self.form.pb_download_install_hisa.setEnabled(value)

        self.form.le_openfoam_url.setEnabled(value)

    # loads the profiles names into the profile combo box
    def loadProfileNames(self):
        profileDir = self.prefs_location + "/Hosts"
        profiles = FreeCAD.ParamGet(profileDir)
        profileList = profiles.GetGroups()
        for item in profileList:
            self.form.cb_profile.addItem(item)

    # load profile parameters into the controls and local vars
    def loadProfile(self, profile_name):

        #set the global profile name
        self.profile_name = profile_name

        #set the global host prefs location
        self.host_prefs_location = self.prefs_location + "/Hosts/" + profile_name

        #set the other global vars
        if profile_name == "":
            self.username = ""
            self.hostname = ""
            self.mesh_processes = 0
            self.mesh_threads = 0
            self.foam_processes = 0
            self.foam_threads = 0
            self.foam_dir = ""
            self.output_path = ""
            self.add_filename_to_output = False
            self.copy_back = False
            self.delete_remote_results = False

        else:
            hostPrefs = self.host_prefs_location
            self.hostname = FreeCAD.ParamGet(hostPrefs).GetString("Hostname", "")
            self.username = FreeCAD.ParamGet(hostPrefs).GetString("Username", "")
            self.mesh_processes = FreeCAD.ParamGet(hostPrefs).GetInt("MeshProcesses")
            self.mesh_threads = FreeCAD.ParamGet(hostPrefs).GetInt("MeshThreads")
            self.foam_processes = FreeCAD.ParamGet(hostPrefs).GetInt("FoamProcesses")
            self.foam_threads = FreeCAD.ParamGet(hostPrefs).GetInt("FoamThreads")
            self.foam_dir = FreeCAD.ParamGet(hostPrefs).GetString("FoamDir", "")
            self.output_path = FreeCAD.ParamGet(hostPrefs).GetString("OutputPath","")
            self.add_filename_to_output = FreeCAD.ParamGet(hostPrefs).GetBool("AddFilenameToOutput")
            self.copy_back = FreeCAD.ParamGet(hostPrefs).GetBool("CopyBack")
            self.delete_remote_results = FreeCAD.ParamGet(hostPrefs).GetBool("DeleteRemoteResults")


        #now set the UI controls
        self.form.le_hostname.setText(self.hostname)
        self.form.le_username.setText(self.username)
        self.form.le_mesh_processes.setText(str(self.mesh_processes))
        self.form.le_mesh_threads.setText(str(self.mesh_threads))
        self.form.le_foam_processes.setText(str(self.foam_processes))
        self.form.le_foam_threads.setText(str(self.foam_threads))
        self.form.le_foam_dir.setText(self.foam_dir)
        self.form.le_output_path.setText(self.output_path)
        self.form.cb_add_filename_to_output.setChecked(self.add_filename_to_output)
        self.form.cb_copy_back.setChecked(self.copy_back)
        self.form.cb_delete_remote_results.setChecked(self.delete_remote_results)


    # create a new profile and add it to the cb_profile control
    # and create its entry in the CfdOF parameters
    def addProfile(self):
        # get the new profile name
        #https://wiki.freecad.org/PySide_Beginner_Examples/en
        profile_name, ok = QtGui.QInputDialog.getText(None,"Profile Name", "Enter the name of the profile you'd like to add.\n It cannot contain spaces or slashes")
        if ok and profile_name:
            print("Adding: " + profile_name)
            #TODO: test for spaces or slashes here.

            # add the profile name to profile combo list
            self.form.cb_profile.addItem(profile_name)
            # move to the item just added
            # TODO: check if text isn't found, ie index = -1
            index = self.form.cb_profile.findText(profile_name)
            self.form.cb_profile.setCurrentIndex(index)

            # update the global profile_name var
            self.profile_name = profile_name

            # update the global host_prefs_location
            self.host_prefs_location = self.prefs_location + "/Hosts/" + profile_name

            # add the default setting for a profile into parameters
            hostPrefs = self.host_prefs_location
            FreeCAD.ParamGet(hostPrefs).SetString("Hostname", "")
            FreeCAD.ParamGet(hostPrefs).SetString("Username", "")
            FreeCAD.ParamGet(hostPrefs).SetInt("MeshProcesses", 0)
            FreeCAD.ParamGet(hostPrefs).SetInt("MeshThreads", 0)
            FreeCAD.ParamGet(hostPrefs).SetInt("FoamProcesses", 0)
            FreeCAD.ParamGet(hostPrefs).SetInt("FoamThreads", 0)
            FreeCAD.ParamGet(hostPrefs).SetString("FoamDir", OPENFOAM_DIR)
            FreeCAD.ParamGet(hostPrefs).SetString("OutputPath","/tmp")
            FreeCAD.ParamGet(hostPrefs).SetBool("AddFilenameToOutput", False)
            FreeCAD.ParamGet(hostPrefs).SetBool("CopyBack", False)
            FreeCAD.ParamGet(hostPrefs).SetBool("DeleteRemoteResults", False)

            # now load the controls and local vars from the profile parameters
            self.loadProfile(profile_name)

    # delete the current profile in the cb_profile and in parameters
    # this will trigger a profile change which will update the controls and
    # vars with the values from the new profile
    def deleteProfile(self):
        #check if there is a profile in the profile combo box to delete
        if self.form.cb_profile.currentText() == "":
            return

        # ask the user if they really want to delete the profile
        #https://wiki.freecad.org/PySide_Beginner_Examples/en
        deleteProfile = self.form.cb_profile.currentText()
        deleteIndex = self.form.cb_profile.currentIndex()
        deleteQuestion = "Delete profile " + deleteProfile + "?\n" + "This cannot be undone."

        reply = QtGui.QMessageBox.question(None, "Delete profile ?", deleteQuestion,
                 QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)

        if reply == QtGui.QMessageBox.Yes:
            #delete it from the control
            self.form.cb_profile.removeItem(deleteIndex)
            # delete it from the parameters list
            profileDir = self.prefs_location + "/Hosts"
            FreeCAD.ParamGet(profileDir).RemGroup(deleteProfile)

        if reply == QtGui.QMessageBox.No:
                 # this is where the code relevant to a 'No' answer goes
                 pass

    # this gets called when the user changes the profile
    # Note: doesn't save the last profile before changing to the new profile
    def profileChanged(self):
         print("The profile was changed")
         # change the global profile name
         self.profile_name = self.form.cb_profile.currentText()
         #load the values for the new profile
         print ("New profile is ", self.profile_name)
         self.loadProfile(self.profile_name)


    # save the current profile by writing its the parameters
    # not currently used.
    def saveProfile(self):
        print("saveProfile has fired")
        if self.profile_name != "":
            hostPrefs = self.host_prefs_location
            FreeCAD.ParamGet(hostPrefs).SetString("Hostname", self.hostname)
            FreeCAD.ParamGet(hostPrefs).SetString("Username", self.username)
            FreeCAD.ParamGet(hostPrefs).SetInt("MeshProcesses", self.mesh_processes)
            FreeCAD.ParamGet(hostPrefs).SetInt("MeshThreads", self.mesh_threads)
            FreeCAD.ParamGet(hostPrefs).SetInt("FoamProcesses",self.foam_processes)
            FreeCAD.ParamGet(hostPrefs).SetInt("FoamThreads",self.foam_threads)
            FreeCAD.ParamGet(hostPrefs).SetString("FoamDir", self.foam_dir)
            FreeCAD.ParamGet(hostPrefs).SetString("OutputPath",self.output_path)
            FreeCAD.ParamGet(hostPrefs).SetBool("AddFilenameToOutput", self.add_filename_to_output)
            FreeCAD.ParamGet(hostPrefs).SetBool("DeleteRemoteResults", self.delete_remote_results)
            FreeCAD.ParamGet(hostPrefs).SetBool("CopyBack", self.copy_back)
            self.profileChanged = False

    def meshThreadsChanged(self):
        if self.profile_name == "":
            return
        if self.form.le_mesh_threads.text() == "":
           return
        #else
        #update the global var
        self.mesh_threads = int(self.form.le_mesh_threads.text())
        #write the new ValueError to the host profile
        FreeCAD.ParamGet(self.host_prefs_location).SetInt("MeshThreads", self.mesh_threads)

    def meshProcessesChanged(self):
        if self.profile_name == "":
            return
        if self.form.le_mesh_processes.text() == "":
           return
        #else
        #update the global var
        self.mesh_processes = int(self.form.le_mesh_processes.text())
        #write the new ValueError to the host profile
        FreeCAD.ParamGet(self.host_prefs_location).SetInt("MeshProcesses", self.mesh_processes)

    def foamThreadsChanged(self):
        if self.profile_name == "":
            return
        if self.form.le_foam_threads.text() == "":
           return
        #else
        #update the global var
        self.foam_threads = int(self.form.le_foam_threads.text())
        #write the new ValueError to the host profile
        FreeCAD.ParamGet(self.host_prefs_location).SetInt("FoamThreads", self.foam_threads)

    def foamProcessesChanged(self):
        #print("foamProcessesChanged has fired")
        #traceback.print_stack()
        if self.profile_name == "":
            return
        if self.form.le_foam_processes.text() == "":
           return
        #else
        #update the global var
        self.foam_processes = int(self.form.le_foam_processes.text())
        #write the new ValueError to the host profile
        FreeCAD.ParamGet(self.host_prefs_location).SetInt("FoamProcesses", self.foam_processes)

    def useRemoteProcessingChanged(self):
        if (self.form.cb_use_remote_processing.isChecked() == True):
            self.enableControls(True)
            FreeCAD.ParamGet(self.prefs_location).SetBool("UseRemoteProcessing", True)
        else:
            self.enableControls(False)
            FreeCAD.ParamGet(self.prefs_location).SetBool("UseRemoteProcessing", False)

    def hostnameChanged(self):
        if self.profile_name == "":
            return
        # update the global variables
        self.hostname = self.form.le_hostname.text()
        FreeCAD.ParamGet(self.host_prefs_location).SetString("Hostname", self.hostname )
        self.profile_changed = True

    def usernameChanged(self):
        if self.profile_name == "":
            return
        # update the global variables
        self.username = self.form.le_username.text()
        FreeCAD.ParamGet(self.host_prefs_location).SetString("Username", self.username )
        self.profile_changed = True

    def foamDirChanged(self):
        #TODO: check that the path doesn't end with "/"
        if self.profile_name == "":
            return
        # update the global variables
        self.foam_dir = self.form.le_foam_dir.text()
        FreeCAD.ParamGet(self.host_prefs_location).SetString("FoamDir", self.foam_dir )
        self.profile_changed = True
        """
        self.foam_dir = text
        if self.foam_dir and os.access(self.foam_dir, os.R_OK):
           #TODO: change this?
           #self.setDownloadURLs()
        """
    def gmshPathChanged(self):
        #TODO: check that the path doesn't end in "/"
        if self.profile_name == "":
            return
        self.gmsh_path = self.form.le_gmsh_path.text()
        FreeCAD.ParamGet(self.host_prefs_location).SetString("GmshDir", self.foam_dir )
        self.profile_changed = True

    def outputPathChanged(self, text):
        #TODO: check that the path doesn't end in "/"
        if self.profile_name == "":
            return
        self.output_path = self.form.le_output_path.text()
        FreeCAD.ParamGet(self.host_prefs_location).SetString("OutputPath", self.output_path )
        self.profile_changed = True

    def addFilenameToOutputChanged(self):
        #TODO: check that the filename doesn't have a space in it
        if self.profile_name == "":
            return
        self.add_filename_to_output = self.form.cb_add_filename_to_output.isChecked()
        FreeCAD.ParamGet(self.host_prefs_location).SetBool("AddFilenameToOutput", self.add_filename_to_output)
        self.profile_changed = True

    def copyBackChanged(self):
        if self.profile_name == "":
            return
        self.copy_back = self.form.cb_copy_back.isChecked()
        FreeCAD.ParamGet(self.host_prefs_location).SetBool("CopyBack", self.copy_back)
        self.profile_changed = True

    def deleteRemoteResultsChanged(self):
        if self.profile_name == "":
            return
        self.delete_remote_results = self.form.cb_delete_remote_results.isChecked()
        FreeCAD.ParamGet(self.host_prefs_location).SetBool("DeleteRemoteResults", self.delete_remote_results)
        self.profile_changed = True

    #TODO: Move this to CfdTools
    def pingHost(self):
        self.consoleMessage("Performing ping test...")
        if self.hostname == "":
            self.consoleMessage("Error: missing hostname or IP address.")
            return
        result = CfdTools.runCommand("ping",["-c8", self.hostname])
        #result = runCommand("ssh", ["me@192.168.2.159", "ls", "-al"])
        #result = runCommand("ssh", ["me@192.168.2.159", "ping", "-c8","www.google.com"])
        #result = runCommand("ssh", ["me@192.168.2.159", "uname", "-a"])
        if result == 0:
            self.consoleMessage("Successfully pinged " + self.hostname + ".")        #+ remote_hostname +".")
        else:
            self.consoleMessage("Could not ping the remote host. Check network configure and test manually.")

    #TODO: Move this to CfdTools
    def testSSH(self):
        self.consoleMessage("Performing ssh test...")
        if self.hostname == "":
            self.consoleMessage("Error: missing hostname or IP address.")
            return
        if self.username =="":
            self.consoleMessage("Error: missing username.")
            return

        connectString = self.form.le_username.text() + "@" + self.hostname
        #print("ssh connectString:", connectString);
        result = CfdTools.runCommand("ssh",[connectString,"ls -al"])
        if result == 0:
           self.consoleMessage("Successfully ran an ssh session on " + self.hostname + ".")
        else:
            self.consoleMessage("Failed to establish an ssh session with the remote host. Manually verify ssh operation with the remote host.")


    def __del__(self):
        self.cleanUp()


    def cleanUp(self):
        if self.thread and self.thread.isRunning():
            FreeCAD.Console.PrintError("Terminating a pending install task\n")
            self.thread.quit = True
        if self.install_process and self.install_process.state() == QtCore.QProcess.Running:
            FreeCAD.Console.PrintError("Terminating a pending install task\n")
            self.install_process.terminate()
        QApplication.restoreOverrideCursor()

    # This gets called from outside the page
    def saveSettings(self):
        pass
        #self.saveProfile() <- this is called in _init_  Doesn't need to be called here.
        """
        print("Error: saveSettings has been depreciated.")
        CfdTools.setRemoteFoamDir(self.foam_dir)
        CfdTools.setParaviewPath(self.paraview_path)
        prefs = self.prefs_location
        FreeCAD.ParamGet(prefs).SetString("RemoteOutputPath", self.remote_output_dir)
        FreeCAD.ParamGet(prefs).SetBool("UseDocker",self.form.cb_docker_sel.isChecked())
        FreeCAD.ParamGet(prefs).SetString("DockerURL",self.form.le_docker_url.text())
        """

    # This gets called form outside the page
    def loadSettings(self):
        pass
        #self.loadProfile(self.profile_name)
        """
        print("Error: loadSettings has been depreciated.")
        # Don't set the autodetected location, since the user might want to allow that to vary according
        # to WM_PROJECT_DIR setting
        prefs = self.prefs_location
        self.foam_dir = FreeCAD.ParamGet(prefs).GetString("RemoteInstallationPath", "")
        self.initial_remote_foam_dir = str(self.foam_dir)
        self.form.le_foam_dir.setText(self.foam_dir)

        # Added by me
        self.remote_output_dir = FreeCAD.ParamGet(prefs).GetString("RemoteOutputPath", "")
        self.initial_remote_output_dir = str(self.remote_output_dir)
        self.form.le_output_path.setText(self.remote_output_dir)

        self.paraview_path = CfdTools.getParaviewPath()
        self.initial_paraview_path = str(self.paraview_path)
        self.form.le_paraview_path.setText(self.paraview_path)

        self.gmsh_path = CfdTools.getRemoteGmshPath()
        self.initial_remote_gmsh_path = str(self.gmsh_path)
        self.form.le_gmsh_path.setText(self.gmsh_path)

        self.output_dir = CfdTools.getDefaultRemoteOutputPath()
        self.form.le_output_path.setText(self.remote_output_dir)

        # Load the use_remote_processing parameter
        if FreeCAD.ParamGet(prefs).GetBool("UseRemoteProcessing", 0):
            self.form.cb_use_remote_processing.setCheckState(Qt.Checked)
            self.enableControls(True)
        else:
            self.enableControls(False)

        #load the hostname
        self.form.le_hostname.setText(FreeCAD.ParamGet(prefs).GetString("RemoteHostname",""))
        self.form.le_username.setText(FreeCAD.ParamGet(prefs).GetString("RemoteUsername",""))

        if FreeCAD.ParamGet(prefs).GetBool("UseDocker", 0):
            self.form.cb_docker_sel.setCheckState(Qt.Checked)
        
        # Set usedocker and enable/disable download buttons 
        self.dockerCheckboxClicked()

        self.form.le_docker_url.setText(FreeCAD.ParamGet(prefs).GetString("DockerURL", DOCKER_URL))

        self.setDownloadURLs()
        """


    def consoleMessage(self, message="", colour_type=None):
        message = escape(message)
        message = message.replace('\n', '<br>')
        if colour_type:
            self.console_message += '<font color="{0}">{1}</font><br>'.format(CfdTools.getColour(colour_type), message)
        else:
            self.console_message += message+'<br>'
        self.form.textEdit_Output.setText(self.console_message)
        self.form.textEdit_Output.moveCursor(QtGui.QTextCursor.End)


    # Not used anymore
    def testGetRuntime(self, disable_exception=True):
        print("Error:testGetRuntime has been depreciated.")
        """ Set the foam dir temporarily and see if we can detect the runtime """
        CfdTools.setFoamDir(self.foam_dir)
        try:
            runtime = CfdTools.getFoamRuntime()
        except IOError as e:
            runtime = None
            if not disable_exception:
                raise
        CfdTools.setFoamDir(self.initial_remote_foam_dir)
        return runtime


    def setDownloadURLs(self):
        print("Error:setDownloadURLs has been depreciated.")
        if self.testGetRuntime() == "MinGW":
            # Temporarily apply the foam dir selection
            CfdTools.setFoamDir(self.foam_dir)
            foam_ver = os.path.split(CfdTools.getFoamDir())[-1]
            self.form.le_cfmesh_url.setText(CFMESH_URL_MINGW.format(foam_ver))
            self.form.le_hisa_url.setText(HISA_URL_MINGW.format(foam_ver))
            CfdTools.setFoamDir(self.initial_remote_foam_dir)
        else:
            self.form.le_cfmesh_url.setText(CFMESH_URL)
            self.form.le_hisa_url.setText(HISA_URL)

    def paraviewPathChanged(self, text):
        print("Error:paraviewPathChanged has been depreciated.")
        self.paraview_path = text

    def chooseFoamDir(self):
        d = QtGui.QFileDialog().getExistingDirectory(None, 'Choose OpenFOAM directory', self.foam_dir)
        if d and os.access(d, os.R_OK):
            self.foam_dir = d
        self.form.le_foam_dir.setText(self.foam_dir)

    def chooseParaviewPath(self):
        p, filter = QtGui.QFileDialog().getOpenFileName(None, 'Choose ParaView executable', self.paraview_path,
                                                        filter="*.exe"  if platform.system() == 'Windows' else None)
        if p and os.access(p, os.R_OK):
            self.paraview_path = p
        self.form.le_paraview_path.setText(self.paraview_path)

    def chooseGmshPath(self):
        p, filter = QtGui.QFileDialog().getOpenFileName(None, 'Choose gmsh executable', self.gmsh_path,
                                                        filter="*.exe"  if platform.system() == 'Windows' else None)
        if p and os.access(p, os.R_OK):
            self.gmsh_path = p
        self.form.le_gmsh_path.setText(self.gmsh_path)

    def chooseOutputDir(self):
        d = QtGui.QFileDialog().getExistingDirectory(None, 'Choose output directory', self.output_dir)
        if d and os.access(d, os.W_OK):
            self.output_dir = os.path.abspath(d)
        self.form.le_output_path.setText(self.output_dir)


    #*******************************************************************************************
    # This function assumes the remote computer is running Linux or a derivative and a vanilla
    # OpenFOAM installation.  It does not handle a Windows remote computer or Docker at this time.
    # It also does simple checks of the provided paths.  It does not attempt to find executables the
    # way the non remote dependency checker does
    # It does not attempt to find ParaView on the remote computer because ParaView is not used as a server in
    # FreeCAD.  Though it could be, some day.

    def checkRemoteCfdDependencies(self):

           CF_MAJOR_VER_REQUIRED = 1
           CF_MINOR_VER_REQUIRED = 16

           HISA_MAJOR_VER_REQUIRED = 1
           HISA_MINOR_VER_REQUIRED = 6
           HISA_PATCH_VER_REQUIRED = 4

           return_message = ""
           FreeCAD.Console.PrintMessage("Checking remote host CFD dependencies on " + self.hostname + "...\n")

           remote_user = self.username
           remote_hostname = self.hostname
           ssh_prefix = "ssh " + remote_user + "@" + remote_hostname + " "

           # check that the remote host is running Linux
           # right now Linux is the only OS supported on the remote host
           print("Checking the operating system on the remote host...\n")

           try:
               os_string = CfdTools.runFoamCommand(ssh_prefix + "uname -o")[0]
           except:
                return_message += "Could not determine the OS on " + self.hostname + ".\n"
           else:
                if os_string.find("Linux") != 0:
                    return_message += "Remote host OS is " + os_string[:-1] + ".\n"

                else:
                    return_message += "The remote host OS is not Linux.\n"
                    return_message += "CfdOF requires that the remote host be running Linux.\n"

           # check that the open foam directory exists on the remote host
           print("Checking the OpenFOAM directory...")
           remote_foam_dir = self.foam_dir
           foam_ls_command = ssh_prefix + " ls " + remote_foam_dir
           #print("OpenFOAM dir testCommand:", foam_ls_command)

           try:
               CfdTools.runFoamCommand(foam_ls_command)
           except:
               return_message += "Failed to find the OpenFOAM directory: "+ remote_foam_dir + " on " + self.hostname +".\n"
               # print the message on the console
           else:
                return_message += "Found OpenFOAM directory " + remote_foam_dir + " on " + self.hostname + ".\n"


           """
           try:
               foam_dir = getRemoteFoamDir()
               sys_msg = "System: {}\nRuntime: {}\nOpenFOAM directory: {}".format(
                   platform.system(), getFoamRuntime(), foam_dir if len(foam_dir) else "(system installation)")
               print(sys_msg)
               message += sys_msg + '\n'
           except IOError as e:
               ofmsg = "Could not find OpenFOAM installation: " + str(e)
               print(ofmsg)
               message += ofmsg + '\n'
           else:
               if foam_dir is None:
                   ofmsg = "OpenFOAM installation path not set and OpenFOAM environment neither pre-loaded before " + \
                           "running FreeCAD nor detected in standard locations"
                   print(ofmsg)
                   message += ofmsg + '\n'
               else:
                   if getFoamRuntime() == "PosixDocker":
                       startDocker()
                   try:
                       if getFoamRuntime() == "MinGW":
                           foam_ver = runFoamCommand("echo $FOAM_API")[0]
                       else:
                       foam_ver = runFoamCommand("echo $WM_PROJECT_VERSION")[0]
          """

           # Check if OpenFOAM will run and what its version is
           FreeCAD.Console.PrintMessage("Checking OpenFOAM operation and version... ")

           try:
                 # TODO: figure out why foamVersion won't run properly in an ssh statement
                 # need sleep in the command so that the OpenFOAM source script gets run in the shell before foamVersion does
                 # help_string = runFoamCommand(ssh_prefix +"sleep 4s ; foamVersion")[0]

                 help_string = CfdTools.runFoamCommand(ssh_prefix + "simpleFoam -help")[0]
           except Exception as e:
                 runmsg = "Unable to run OpenFOAM: " + str(e)
                 return_message += runmsg + '\n'
                 print(runmsg)
                 #raise
           else:
                 # TODO: this should be put in a try to go with the except below in case
                 # there is an issue with parsing out the OF version
                 # The command $foamVersion will give the version as well
                 version_start = help_string.find("OpenFOAM-") + 9
                 version_string = help_string[version_start:version_start+4]
                 print(version_string)
                 return_message += "Successfully ran OpenFOAM version " + version_string + " on " + self.hostname + ".\n"
                 foam_version = int(version_string)

                 """
                 foam_ver = foam_ver.rstrip()
                 if foam_ver:
                      foam_ver = foam_ver.split()[-1]
                 if foam_ver and foam_ver != 'dev' and foam_ver != 'plus':
                      try:
                          # Isolate major version number
                          foam_ver = foam_ver.lstrip('v')
                          foam_ver = int(foam_ver.split('.')[0])
                          if getFoamRuntime() == "MinGW":
                              if foam_ver < 2012 or foam_ver > 2206:
                                       vermsg = "OpenFOAM version " + str(foam_ver) + \
                                                " is not currently supported with MinGW installation"
                                       message += vermsg + "\n"
                                       print(vermsg)
                 """
                 if foam_version >= 1000:  # Plus version
                                if foam_version < 1706:
                                       vermsg = "OpenFOAM version " + str(foam_version) + " is outdated:\n" + \
                                                "Minimum version 1706 or 5 required"
                                       return_message += vermsg + "\n"
                                       print(vermsg)
                 if foam_version > 2206:
                                       vermsg = "OpenFOAM version " + str(foam_version) + " is not yet supported:\n" + \
                                                "Last tested version is 2206"
                                       return_message += vermsg + "\n"
                                       print(vermsg)
                 """
                 This code does not support foundation version numbers at this time.
                 TODO: handle foundation version numbers
                 else:  # Foundation version
                                   if foam_ver < 5:
                                       vermsg = "OpenFOAM version " + str(foam_ver) + " is outdated:\n" + \
                                                "Minimum version 5 or 1706 required"
                                       message += vermsg + "\n"
                                       print(vermsg)
                 if foam_ver > 9:
                                       vermsg = "OpenFOAM version " + str(foam_ver) + " is not yet supported:\n" + \
                                                "Last tested version is 9"
                                       message += vermsg + "\n"
                                       print(vermsg)
                 except ValueError:
                               vermsg = "Error parsing OpenFOAM version string " + foam_ver
                               message += vermsg + "\n"
                               print(vermsg)

                 # Check for wmake
                 # if getFoamRuntime() != "MinGW" and getFoamRuntime() != "PosixDocker":
                """

                 try:
                      # changed this from -help to -version
                      wmake_reply = CfdTools.runFoamCommand(ssh_prefix + "wmake -version")[0]

                 except Exception as e:
                       #print(e)
                       wmakemsg = "Cannot run 'wmake' on remote host. \n"
                       wmakemsg += "Installation of cfMesh and HiSA is not be possible without 'wmake'.\n"
                       wmakemsg += "'wmake' is installed with most OpenFOAM development packages.\n"
                       wmakemsg += "You may want to install the OpenFOAM development package on the remote host to provide 'wmake'.\n"
                       return_message += wmakemsg
                       print(wmakemsg)

                 else:
                     print(wmake_reply)
                     return_message += "'wmake' is installed on " + self.hostname + ".\n"

                 # Check for cfMesh
                 try:
                     cfmesh_ver = CfdTools.runFoamCommand(ssh_prefix + "cartesianMesh -version")[0]
                     version_line = cfmesh_ver.splitlines()[-1]
                     vermsg = version_line[:-1] + " found on " + self.hostname + "."
                     cfmesh_ver = cfmesh_ver.rstrip().split()[-1]
                     cfmesh_ver = cfmesh_ver.split('.')
                     if (not cfmesh_ver or len(cfmesh_ver) != 2 or
                         int(cfmesh_ver[0]) < CF_MAJOR_VER_REQUIRED or
                         (int(cfmesh_ver[0]) == CF_MAJOR_VER_REQUIRED and
                          int(cfmesh_ver[1]) < CF_MINOR_VER_REQUIRED)):
                          vermsg += "cfMesh-CfdOF version {}.{} required".format(CF_MAJOR_VER_REQUIRED, CF_MINOR_VER_REQUIRED)

                 except Exception as e: #subprocess.CalledProcessError:
                           vermsg = "cfMesh (CfdOF version) not found on " + self.hostname + "."
                 return_message += vermsg + '\n'
                 print(vermsg)


                 # Check for HiSA
                 try:
                           hisa_ver = CfdTools.runFoamCommand(ssh_prefix + "hisa -version")[0]
                           hisa_ver = hisa_ver.rstrip().split()[-1]
                           hisa_ver = hisa_ver.split('.')
                           if (not hisa_ver or len(hisa_ver) != 3 or
                               int(hisa_ver[0]) < HISA_MAJOR_VER_REQUIRED or
                               (int(hisa_ver[0]) == HISA_MAJOR_VER_REQUIRED and
                                (int(hisa_ver[1]) < HISA_MINOR_VER_REQUIRED or
                                 (int(hisa_ver[1]) == HISA_MINOR_VER_REQUIRED and
                                  int(hisa_ver[2]) < HISA_PATCH_VER_REQUIRED)))):
                               vermsg = "HiSA version {}.{}.{} required".format(HISA_MAJOR_VER_REQUIRED,
                                                                                HISA_MINOR_VER_REQUIRED,
                                                                                HISA_PATCH_VER_REQUIRED)
                               return_message += vermsg + "\n"
                               print(vermsg)
                 except Exception as e:  #subprocess.CalledProcessError:
                           hisa_msg = "HiSA not found on " + self.hostname + "."
                           return_message += hisa_msg + '\n'
                           print(hisa_msg)


           print("Checking for gmsh:")
           # check that gmsh version 2.13 or greater is installed
           # Note: ssh runs things in a shell.   As long as the environment vars for that shell
           # are set up properly on the remote computer, one doesn't need to know the gmsh path.
           # You just call it and the shell $PATH takes care of the rest.

           try:
                gmsh_reply = CfdTools.runFoamCommand(ssh_prefix + "gmsh -version")[0]

           except Exception as e:
                 #print(e)
                 gmsh_msg = "Cannot run 'gmsh' on " + self.hostname + ". \n"
                 gmsh_msg += "Please install gmsh on the remote host.\n"
                 return_message += gmsh_msg
                 print(gmsh_msg)

           else:
               # print(gmsh_reply)
               # print(type(gmsh_reply))
               return_message += "gmsh version " + gmsh_reply[:-1]  + " is installed on " + self.hostname + ".\n"
               versionlist = gmsh_reply.split(".")
               if int(versionlist[0]) < 2 or (int(versionlist[0]) == 2 and int(versionlist[1]) < 13):
                   gmsh_ver_msg = "The installed gmsh version is older than minimum required (2.13).\n"
                   gmsh_ver_msg += "Please update gmsh on the remote host."
                   return_message += gmsh_ver_msg + '\n'
                   print(gmsh_ver_msg)

           """
           gmshversion = ""
           gmsh_exe = getRemoteGmshExecutable()
           if gmsh_exe is None:
               gmsh_msg = "gmsh not found (optional)"
               return_message += gmsh_msg + '\n'
               print(gmsh_msg)
           else:
               gmsh_msg = "gmsh executable: " + gmsh_exe
               return_message += gmsh_msg + '\n'
               print(gmsh_msg)
               try:
                   # Needs to be runnable from OpenFOAM environment
                   gmshversion = runFoamCommand("'" + gmsh_exe + "'" + " -version")[2]
               except (OSError, subprocess.CalledProcessError):
                   gmsh_msg = "gmsh could not be run from OpenFOAM environment"
                   return_message += gmsh_msg + '\n'
                   print(gmsh_msg)
               if len(gmshversion) > 1:
                   # Only the last line contains gmsh version number
                   gmshversion = gmshversion.rstrip().split()
                   gmshversion = gmshversion[-1]
                   versionlist = gmshversion.split(".")
                   if int(versionlist[0]) < 2 or (int(versionlist[0]) == 2 and int(versionlist[1]) < 13):
                       gmsh_ver_msg = "gmsh version is older than minimum required (2.13)"
                       return_message += gmsh_ver_msg + '\n'
                       print(gmsh_ver_msg)
            """

           print("Completed CFD remote dependency check.")
           return_message += "Completed remote host dependency check on " + self.hostname + ".\n"
           return return_message


    # This dependency checker runs on the remote host
    def runRemoteDependencyChecker(self):

       if self.profile_name == "":
            self.consoleMessage("Error: empty profile")
            return

       if self.hostname == "":
            self.consoleMessage("Error: missing hostname or IP address")
            return

       if self.username == "":
            self.consoleMessage("Error: missing username")
            return

       remote_hostname = self.hostname

       # Temporarily apply the foam dir selection and paraview path selection
       #CfdTools.setRemoteFoamDir(self.foam_dir)
       #CfdTools.setParaviewPath(self.paraview_path)
       #CfdTools.setRemoteGmshPath(self.gmsh_path)
       #QApplication.setOverrideCursor(Qt.WaitCursor)

       self.consoleMessage("Checking dependencies on " + remote_hostname + "...")
       msg = self.checkRemoteCfdDependencies()
       self.consoleMessage(msg)
       #CfdTools.setRemoteFoamDir(self.initial_remote_foam_dir)
       #CfdTools.setParaviewPath(self.initial_paraview_path)
       #CfdTools.setRemoteGmshPath(self.initial_remote_gmsh_path)
       QApplication.restoreOverrideCursor()


    # Not used anymore.  Kept for reference sake
    # Some of the vars may have been changed to their remote versions
    """
    def runDependencyChecker(self):
        # Temporarily apply the foam dir selection and paraview path selection
        CfdTools.setFoamDir(self.foam_dir)
        CfdTools.setParaviewPath(self.paraview_path)
        CfdTools.setGmshPath(self.gmsh_path)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.consoleMessage("Checking dependencies...")
        msg = CfdTools.checkCfdDependencies()
        self.consoleMessage(msg)
        CfdTools.setFoamDir(self.initial_foam_dir)
        CfdTools.setParaviewPath(self.initial_paraview_path)
        CfdTools.setGmshPath(self.initial_gmsh_path)
        QApplication.restoreOverrideCursor()
    """


    def showAdministratorWarningMessage(self):
        if platform.system() == "Windows":
            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
            if not is_admin:
                button = QtGui.QMessageBox.question(
                    None,
                    "CfdOF Workbench",
                    "Before installing this software, it is advised to run FreeCAD in administrator mode (hold down "
                    " the 'Shift' key, right-click on the FreeCAD launcher, and choose 'Run as administrator').\n\n"
                    "If this is not possible, please make sure OpenFOAM is installed in a location to which you have "
                    "full read/write access rights.\n\n"
                    "You are not currently running as administrator - do you wish to continue anyway?")
                return button == QtGui.QMessageBox.StandardButton.Yes
        return True

    def downloadInstallOpenFoam(self):
        if not self.showAdministratorWarningMessage():
            return
        if self.createThread():
            self.thread.task = DOWNLOAD_OPENFOAM
            self.thread.openfoam_url = self.form.le_openfoam_url.text()
            self.thread.start()

    def pickOpenFoamFile(self):
        f, filter = QtGui.QFileDialog().getOpenFileName(None, 'Choose OpenFOAM install file', filter="*.exe")
        if f and os.access(f, os.R_OK):
            self.form.le_openfoam_url.setText(urlparse.urljoin('file:', urlrequest.pathname2url(f)))

    def downloadInstallParaview(self):
        if self.createThread():
            self.thread.task = DOWNLOAD_PARAVIEW
            self.thread.paraview_url = self.form.le_paraview_url.text()
            self.thread.start()

    def pickParaviewFile(self):
        f, filter = QtGui.QFileDialog().getOpenFileName(None, 'Choose ParaView install file', filter="*.exe")
        if f and os.access(f, os.R_OK):
            self.form.le_paraview_url.setText(urlparse.urljoin('file:', urlrequest.pathname2url(f)))


    #**********************************************************************************************
    # TODO: Update to use profiles
    def remoteDownloadInstallCfMesh(self):

        #TODO: this routine doesn't clean up after itself if it fails
        # Nor does it check for a full or partial build
        # If the user reruns the build after fully or partially building previously
        # this routine will fail.

        # TODO this routine assumes the output dir exists.  Will fail if it doesn't.  Fix this.

        # Get the username and hostname for the remote host
        remote_user = self.username
        remote_hostname = self.hostname
        ssh_prefix = "ssh -tt " + remote_user + "@" + remote_hostname + " "
        working_dir = self.output_path

        self.consoleMessage("Installing cfMesh on " + self.hostname + "...")

        # create a dir to download the CfMesh source files to
        # cfMesh is installed in the user's home directory, not the output directory

        command = "EOT\n"
        command += "cd " + working_dir + "\n"
        command += "mkdir cfMesh" + "\n"
        command += "exit \n"
        command += "EOT"

        try:
            command_result = CfdTools.runFoamCommand(ssh_prefix + "<< " + command)[0]
            working_dir += "/cfMesh"

            print("Created cfMesh install dir: " + working_dir)
            self.consoleMessage("Created cfMesh install directory " + working_dir)
        except:
             self.consoleMessage("Could not create an install directory on " + self.hostname + ".")
             return

        # download the cfMesh source files
        command = "EOT\n"
        command += "cd " + working_dir + "\n"
        command += "wget "  + self.form.le_cfmesh_url.text() + "\n"
        command += "exit \n"
        command += "EOT"

        try:
             command_result = CfdTools.runFoamCommand(ssh_prefix + " << " + command)[0]
             self.consoleMessage("Downloaded the cfMesh source files")
        except:
             self.consoleMessage("Could not download the cfMesh source files.")
             return

        # unzip the downloaded file
        # TODO: this assumes the downloaded archive is called "download".  Which might not always be the case.
        # Get name of the downloaded file from the URL and use that filename in this command
        command = "EOT\n"
        command += "cd " + working_dir + "\n"
        command += "unzip download \n"
        command += "exit \n"
        command += "EOT"

        try:
             command_result = CfdTools.runFoamCommand(ssh_prefix + " << " + command)[0]
             self.consoleMessage("Unzipped cfMesh source files")
        except:
             self.consoleMessage("Could not unzip cfMesh source files.")
             return

        # run the wmake process
        # TODO: add the number of processes to use on the build with export WM_NCOMPPROCS=`nproc`;
        # TODO: add logging wiht ./Allwmake  ->  log.Allwmake
        # TODO: delete the previous log before starting the new build
        # Executing: { rm -f log.Allwmake; export WM_NCOMPPROCS=`nproc`; ./Allwmake 1> >(tee -a log.Allwmake) 2> >(tee -a log.Allwmake >&2); } in $WM_PROJECT_USER_DIR/cfmesh-cfdof

        command = "EOT\n"
        command += "cd " + working_dir + "/cfmesh-cfdof \n"
        command += "./Allwmake \n"
        command += "exit \n"
        command += "EOT"

        self.consoleMessage("Starting cfMesh build on " + self.hostname + ".")
        self.consoleMessage("This takes a bit of time.  Please wait.")
        try:
             command_result = CfdTools.runFoamCommand(ssh_prefix + " << " + command)[0]
             self.consoleMessage("Successfully built and installed cfMesh.")
        except:
             self.consoleMessage("Could not build cfMesh: " + command_result)
             return





    # old version, not used anymore.  Doesn't handle remote install
    def downloadInstallCfMesh(self):
        print("Error:downloadInstallCFMesh has been depreciated.")
        return

        if not self.showAdministratorWarningMessage():
            return

        runtime = self.testGetRuntime(False)
        if runtime == "MinGW" and self.form.le_cfmesh_url.text() == CFMESH_URL:
            # Openfoam might have just been installed and the URL would not have had a chance to update
            self.setDownloadURLs()

        if self.createThread():
            self.thread.task = DOWNLOAD_CFMESH
            # We are forced to apply the foam dir selection - reset when the task finishes
            CfdTools.setFoamDir(self.foam_dir)
            self.thread.cfmesh_url = self.form.le_cfmesh_url.text()
            self.thread.start()

    def pickCfMeshFile(self):
        f, filter = QtGui.QFileDialog().getOpenFileName(None, 'Choose cfMesh archive', filter="*.zip")
        if f and os.access(f, os.R_OK):
            self.form.le_cfmesh_url.setText(urlparse.urljoin('file:', urlrequest.pathname2url(f)))

    def downloadInstallHisa(self):
        if not self.showAdministratorWarningMessage():
            return

        runtime = self.testGetRuntime(False)
        if runtime == "MinGW" and self.form.le_hisa_url.text() == HISA_URL:
            # Openfoam might have just been installed and the URL would not have had a chance to update
            self.setDownloadURLs()

        if self.createThread():
            self.thread.task = DOWNLOAD_HISA
            # We are forced to apply the foam dir selection - reset when the task finishes
            CfdTools.setFoamDir(self.foam_dir)
            self.thread.hisa_url = self.form.le_hisa_url.text()
            self.thread.start()

    def pickHisaFile(self):
        f, filter = QtGui.QFileDialog().getOpenFileName(None, 'Choose HiSA archive', filter="*.zip")
        if f and os.access(f, os.R_OK):
            self.form.le_hisa_url.setText(urlparse.urljoin('file:', urlrequest.pathname2url(f)))


    def createThread(self):
        if self.thread and self.thread.isRunning():
            self.consoleMessage("Busy - please wait...", 'Error')
            return False
        else:
            self.thread = CfdRemotePreferencePageThread()
            self.thread.signals.error.connect(self.threadError)
            self.thread.signals.finished.connect(self.threadFinished)
            self.thread.signals.status.connect(self.threadStatus)
            self.thread.signals.downloadProgress.connect(self.downloadProgress)
            return True

    def threadStatus(self, msg):
        self.consoleMessage(msg)

    def threadError(self, msg):
        self.consoleMessage(msg, 'Error')
        self.consoleMessage("Download unsuccessful")

    def threadFinished(self, status):
        if self.thread.task == DOWNLOAD_CFMESH:
            if status:
                if CfdTools.getFoamRuntime() != "MinGW":
                    self.consoleMessage("Download completed")
                    user_dir = self.thread.user_dir
                    self.consoleMessage("Building cfMesh. Lengthy process - please wait...")
                    self.consoleMessage("Log file: {}/{}/log.Allwmake".format(user_dir, CFMESH_FILE_BASE))
                    if CfdTools.getFoamRuntime() == 'WindowsDocker':
                        # There seem to be issues when using multi processors to build in docker
                        self.install_process = CfdTools.startFoamApplication(
                            "export WM_NCOMPPROCS=1; ./Allwmake",
                            "$WM_PROJECT_USER_DIR/"+CFMESH_FILE_BASE,
                            'log.Allwmake', self.installFinished, stderr_hook=self.stderrFilter)
                    else:
                        self.install_process = CfdTools.startFoamApplication(
                            "export WM_NCOMPPROCS=`nproc`; ./Allwmake", 
                            "$WM_PROJECT_USER_DIR/"+CFMESH_FILE_BASE,
                            'log.Allwmake', self.installFinished, stderr_hook=self.stderrFilter)
                else:
                    self.consoleMessage("Install completed")
            # Reset foam dir for now in case the user presses 'Cancel'
            CfdTools.setFoamDir(self.initial_remote_foam_dir)
        elif self.thread.task == DOWNLOAD_HISA:
            if status:
                if CfdTools.getFoamRuntime() != "MinGW":
                    self.consoleMessage("Download completed")
                    user_dir = self.thread.user_dir
                    self.consoleMessage("Building HiSA. Please wait...")
                    self.consoleMessage("Log file: {}/{}/log.Allwmake".format(user_dir, HISA_FILE_BASE))
                    if CfdTools.getFoamRuntime() == 'WindowsDocker':
                        # There seem to be issues when using multi processors to build in docker
                        self.install_process = CfdTools.startFoamApplication(
                            "export WM_NCOMPPROCS=1; ./Allwmake",
                            "$WM_PROJECT_USER_DIR/"+HISA_FILE_BASE,
                            'log.Allwmake', self.installFinished, stderr_hook=self.stderrFilter)
                    else:
                        self.install_process = CfdTools.startFoamApplication(
                            "export WM_NCOMPPROCS=`nproc`; ./Allwmake", 
                            "$WM_PROJECT_USER_DIR/"+HISA_FILE_BASE,
                            'log.Allwmake', self.installFinished, stderr_hook=self.stderrFilter)
                else:
                    self.consoleMessage("Install completed")
            # Reset foam dir for now in case the user presses 'Cancel'
            CfdTools.setFoamDir(self.initial_remote_foam_dir)
        elif self.thread.task == DOWNLOAD_DOCKER:
            if status:
                self.consoleMessage("Download completed")            
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
            msg += " of {:.2f} MB".format(float(bytes_total)/(1024*1024))
        self.form.labelDownloadProgress.setText(msg)

    def stderrFilter(self, text):
        # Print to stdout rather than stderr so as not to alarm the user
        # with the spurious wmkdep errors on stderr
        print(text, end='')
        return ''

    def dockerCheckboxClicked(self):
        if CfdTools.docker_container==None:
            CfdTools.docker_container = CfdTools.DockerContainer()
        CfdTools.docker_container.usedocker = self.form.cb_docker_sel.isChecked()
        self.form.pb_download_install_docker.setEnabled(CfdTools.docker_container.usedocker)
        self.form.pb_download_install_openfoam.setEnabled(not CfdTools.docker_container.usedocker)
        #self.form.pb_download_install_hisa.setEnabled((not CfdTools.docker_container.usedocker ))
        #self.form.pb_download_install_cfMesh.setEnabled((not CfdTools.docker_container.usedocker))
        self.form.gb_docker.setVisible(CfdTools.docker_container.docker_cmd!=None or CfdTools.docker_container.usedocker)

    def downloadInstallDocker(self):
        # Set foam dir and output dir in preparation for using docker
        CfdTools.setFoamDir(self.form.le_foam_dir.text())
        self.saveSettings()
        if self.createThread():
            self.thread.task = DOWNLOAD_DOCKER
            self.thread.docker_url = self.form.le_docker_url.text() 
            self.thread.start()

class CfdRemotePreferencePageSignals(QObject):
    error = QtCore.Signal(str)  # Signal in PySide, pyqtSignal in PyQt
    finished = QtCore.Signal(bool)
    status = QtCore.Signal(str)
    downloadProgress = QtCore.Signal(int, int)


class CfdRemotePreferencePageThread(QThread):
    """ Worker thread to complete tasks in preference page """
    def __init__(self):
        super(CfdRemotePreferencePageThread, self).__init__()
        self.signals = CfdRemotePreferencePageSignals()
        self.quit = False
        self.user_dir = None
        self.task = None
        self.openfoam_url = None
        self.paraview_url = None
        self.cfmesh_url = None
        self.hisa_url = None
        self.docker_url = None

    def run(self):
        self.quit = False

        try:
            if self.task == DOWNLOAD_OPENFOAM:
                self.downloadOpenFoam()
            elif self.task == DOWNLOAD_PARAVIEW:
                self.downloadParaview()
            elif self.task == DOWNLOAD_CFMESH:
                self.downloadCfMesh()
            elif self.task == DOWNLOAD_HISA:
                self.downloadHisa()
            elif self.task == DOWNLOAD_DOCKER:
                self.downloadDocker()
        except Exception as e:
            if self.quit:
                self.signals.finished.emit(False)  # Exit quietly since UI already destroyed
                return
            else:
                self.signals.error.emit(str(e))
                self.signals.finished.emit(False)
                return
        self.signals.finished.emit(True)

    def downloadFile(self, url, **kwargs):
        block_size = kwargs.get('block_size', 10*1024)
        context = kwargs.get('context', None)
        reporthook = kwargs.get('reporthook', None)
        suffix = kwargs.get('suffix', '')
        with closing(urlrequest.urlopen(url, context=context)) as response:  # For Python < 3.3 backward compatibility
            download_len = int(response.info().get('Content-Length', 0))
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_file:
                i = 0
                while True:
                    data = response.read(block_size)
                    if not data:
                        break
                    if self.quit:
                        raise RuntimeError("Premature termination received")
                    tmp_file.write(data)
                    i += 1
                    if reporthook:
                        reporthook(i, block_size, download_len)
                filename = tmp_file.name
                return filename, response.info()

    def download(self, url, suffix, name):
        self.signals.status.emit("Downloading {}, please wait...".format(name))
        try:
            if hasattr(ssl, 'create_default_context'):
                context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            else:
                context = None
            # Download
            (filename, header) = self.downloadFile(
                url, suffix=suffix, reporthook=self.downloadStatus, context=context)
        except Exception as ex:
            raise Exception("Error downloading {}: {}".format(name, str(ex)))

        self.signals.status.emit("{} downloaded to {}".format(name, filename))
        return filename

    def downloadOpenFoam(self):
        filename = self.download(self.openfoam_url, OPENFOAM_FILE_EXT, "OpenFOAM")
        if QtCore.QProcess().startDetached(filename):
            self.signals.status.emit("OpenFOAM installer launched - please complete the installation")
        else:
            raise Exception("Failed to launch OpenFOAM installer")

    def downloadParaview(self):
        filename = self.download(self.paraview_url, PARAVIEW_FILE_EXT, "ParaView")
        if QtCore.QProcess().startDetached(filename):
            self.signals.status.emit("ParaView installer launched - please complete the installation")
        else:
            raise Exception("Failed to launch ParaView installer")

    def downloadCfMesh(self):
        filename = self.download(self.cfmesh_url, CFMESH_FILE_EXT, "cfMesh")

        if CfdTools.getFoamRuntime() == "MinGW":
            self.user_dir = None
            self.signals.status.emit("Installing cfMesh...")
            CfdTools.runFoamCommand(
                '{{ mkdir -p "$FOAM_APPBIN" && cd "$FOAM_APPBIN" && unzip -o "{}"; }}'.
                    format(CfdTools.translatePath(filename)))
        else:
            self.user_dir = CfdTools.runFoamCommand("echo $WM_PROJECT_USER_DIR")[0].rstrip().split('\n')[-1]
            # We can't reverse-translate the path for docker since it sits inside the container. Just report it as such.
            if CfdTools.getFoamRuntime() != 'WindowsDocker':
                self.user_dir = CfdTools.reverseTranslatePath(self.user_dir)

            self.signals.status.emit("Extracting cfMesh...")
            if CfdTools.getFoamRuntime() == 'WindowsDocker':
                from zipfile import ZipFile
                with ZipFile(filename, 'r') as zip:
                    with tempfile.TemporaryDirectory() as tempdir:
                        zip.extractall(path=tempdir)
                        CfdTools.runFoamCommand(
                            '{{ mkdir -p "$WM_PROJECT_USER_DIR" && cp -r "{}" "$WM_PROJECT_USER_DIR/"; }}'
                                .format(CfdTools.translatePath(os.path.join(tempdir, CFMESH_FILE_BASE))))
            else:
                CfdTools.runFoamCommand(
                    '{{ mkdir -p "$WM_PROJECT_USER_DIR" && cd "$WM_PROJECT_USER_DIR" && ( rm -r {}; unzip -o "{}"; ); }}'.
                    format(CFMESH_FILE_BASE, CfdTools.translatePath(filename)))

    def downloadHisa(self):
        filename = self.download(self.hisa_url, HISA_FILE_EXT, "HiSA")

        if CfdTools.getFoamRuntime() == "MinGW":
            self.user_dir = None
            self.signals.status.emit("Installing HiSA...")
            CfdTools.runFoamCommand(
                '{{ mkdir -p "$FOAM_APPBIN" && cd "$FOAM_APPBIN" && unzip -o "{}"; }}'.
                    format(CfdTools.translatePath(filename)))
        else:
            self.user_dir = CfdTools.runFoamCommand("echo $WM_PROJECT_USER_DIR")[0].rstrip().split('\n')[-1]
            # We can't reverse-translate the path for docker since it sits inside the container. Just report it as such.
            if CfdTools.getFoamRuntime() != 'WindowsDocker':
                self.user_dir = CfdTools.reverseTranslatePath(self.user_dir)

            self.signals.status.emit("Extracting HiSA...")
            if CfdTools.getFoamRuntime() == 'WindowsDocker':
                from zipfile import ZipFile
                with ZipFile(filename, 'r') as zip:
                    with tempfile.TemporaryDirectory() as tempdir:
                        zip.extractall(path=tempdir)
                        CfdTools.runFoamCommand(
                            '{{ mkdir -p "$WM_PROJECT_USER_DIR" && cp -r "{}" "$WM_PROJECT_USER_DIR/"; }}'
                                .format(CfdTools.translatePath(os.path.join(tempdir, HISA_FILE_BASE))))
            else:
                CfdTools.runFoamCommand(
                    '{{ mkdir -p "$WM_PROJECT_USER_DIR" && cd "$WM_PROJECT_USER_DIR" && ( rm -r {}; unzip -o "{}"; );  }}'.
                    format(HISA_FILE_BASE, CfdTools.translatePath(filename)))

    def downloadDocker(self):
        self.signals.status.emit("Downloading Docker image, please wait until 'Download completed' message shown below")
        if CfdTools.docker_container.container_id!=None:
            CfdTools.docker_container.stop_container()
        cmd = '{} pull {}'.format(CfdTools.docker_container.docker_cmd, self.docker_url)
        if 'docker'in CfdTools.docker_container.docker_cmd:
            cmd = cmd.replace('docker.io/','')

        CfdTools.runFoamCommand(cmd)
    
    def downloadStatus(self, blocks, block_size, total_size):
        self.signals.downloadProgress.emit(blocks*block_size, total_size)
