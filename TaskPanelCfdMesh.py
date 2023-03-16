# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2016 - Bernd Hahnebach <bernd@bimstatik.org>            *
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
#
# LinuxGuy123@gmail.com's notes:
#
#
#
# TODOs, in addition to TODOs in the code itself
#
# - check that the appropriate controls are enabled for the host.  Most specifically,
# Edit case shouldn't be enabled for remote hosts.  Paraview doesn't work on remote hosts either.
# Also check mesh, etc.
#
# - right now there is no way to edit the case on a remote host.  This could be enabled by
# copying back the case to the local machine, allowing the user to edit the files in a temp dir
# and then copying them back to the remote host
#
# - the host name was passed into the meshing routines via the global variable.   Really the hostname
# should be passed into the meshing routines via the mesh object
#
#- add use filename extension to the output path.  For both local and remote useRemoteProcessing
#
#- copy the mesh back to the local computer for Paraview, Load surface mesh and Check Mesh.




from __future__ import print_function
import FreeCAD
import os
import os.path
from CfdOF.Mesh import CfdMesh
import time
from datetime import timedelta
from CfdOF import CfdTools
from CfdOF.CfdTools import setQuantity, getQuantity, storeIfChanged
from CfdOF.Mesh import CfdMeshTools
from CfdOF.CfdConsoleProcess import CfdConsoleProcess
if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore
    from PySide import QtCore
    from PySide import QtGui
    from PySide.QtCore import Qt
    from PySide.QtGui import QApplication


class TaskPanelCfdMesh:
    """ The TaskPanel for editing References property of CfdMesh objects and creation of new CFD mesh """
    def __init__(self, obj):
        self.mesh_obj = obj
        self.analysis_obj = CfdTools.getParentAnalysisObject(self.mesh_obj)
        self.form = FreeCADGui.PySideUic.loadUi(os.path.join(CfdTools.getModulePath(), 'Gui', "TaskPanelCfdMesh.ui"))

        self.console_message_cart = ''
        self.error_message = ''
        self.mesh_obj.Proxy.cart_mesh = CfdMeshTools.CfdMeshTools(self.mesh_obj)
        self.paraviewScriptName = ""

        self.mesh_obj.Proxy.mesh_process = CfdConsoleProcess(finished_hook=self.meshFinished,
                                                             stdout_hook=self.gotOutputLines,
                                                             stderr_hook=self.gotErrorLines)

        #set the prefs and host prefs locations
        self.prefs_location = CfdTools.getPreferencesLocation()
        self.host_prefs_location = self.prefs_location + "/Hosts"
        self.useRemoteProcessing = FreeCAD.ParamGet(self.prefs_location).GetBool('UseRemoteProcessing', 0)

        #setting these here so they get created as globals
        #they also get initiated in loadProfile()
        # self.use_remote_processing = False <- this is set above before the control is loaded

        self.profile_name = ""
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

        #add a local host to cb_profile
        self.form.cb_profile.addItem("local")

        # if using remote processing, add the host profiles as well
        if self.useRemoteProcessing:
            self.loadProfileNames()
        else:
            #disable cb_profile so that users aren't trying to change the host
            self.form.cb_profile.setEnabled(False)

        # load the local profile
        self.loadProfile("local")

        self.Timer = QtCore.QTimer()
        self.Timer.setInterval(1000)
        self.Timer.timeout.connect(self.update_timer_text)

        # set up the profiles combo box connection
        self.form.cb_profile.currentIndexChanged.connect(self.profileChanged)

        self.form.cb_utility.activated.connect(self.choose_utility)

        self.form.pb_write_mesh.clicked.connect(self.writeMesh)

        self.form.pb_edit_mesh.clicked.connect(self.editMesh)

        self.form.pb_run_mesh.clicked.connect(self.runMesh)

        self.form.pb_stop_mesh.clicked.connect(self.killMeshProcess)
        self.form.pb_paraview.clicked.connect(self.openParaview)
        self.form.pb_load_mesh.clicked.connect(self.pbLoadMeshClicked)
        self.form.pb_clear_mesh.clicked.connect(self.pbClearMeshClicked)
        self.form.pb_searchPointInMesh.clicked.connect(self.searchPointInMesh)
        self.form.pb_check_mesh.clicked.connect(self.checkMeshClicked)

        self.radioGroup = QtGui.QButtonGroup()
        self.radioGroup.addButton(self.form.radio_explicit_edge_detection)
        self.radioGroup.addButton(self.form.radio_implicit_edge_detection)

        self.form.snappySpecificProperties.setVisible(False)
        self.form.pb_stop_mesh.setEnabled(False)
        self.form.pb_paraview.setEnabled(False)

        self.form.cb_utility.addItems(CfdMesh.MESHER_DESCRIPTIONS)

        self.form.if_max.setToolTip("Enter 0 to use default value")
        self.form.pb_searchPointInMesh.setToolTip("Specify below a point vector inside of the mesh or press 'Search' "
                                                  "to try to automatically find a point")
        self.form.if_cellsbetweenlevels.setToolTip("Number of cells between each of level of refinement")
        self.form.if_edgerefine.setToolTip("Number of refinement levels for all edges")
        self.form.radio_explicit_edge_detection.setToolTip("Find surface edges using explicit (eMesh) detection")
        self.form.radio_implicit_edge_detection.setToolTip("Find surface edges using implicit detection")

        self.load()
        self.updateUI()

        self.Start = time.time()
        self.Timer.start()

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
             print("Error: no host profile selected")
             return

         # set the vars to the local parameters
         if profile_name == "local":
              self.hostname = "local"
              # the local code doesn't use these vars, so don't set them
              # dangerous.
              """
              self.username = ""
              self.mesh_processes = 0
              self.mesh_threads = 0
              self.foam_processes = 0
              self.foam_threads = 0
              self.foam_dir = FreeCAD.ParamGet(hostPrefs).GetString("FoamDir", "")
              self.output_path = FreeCAD.ParamGet(hostPrefs).GetString("OutputPath","")
              self.output_path = ""
              self.add_filename_to_output = False
              """
         else:
              #set the vars to the remote host parameters
              # most of these aren't used, at least not in this page
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

              #now set the control values
              self.mesh_obj.NumberOfProcesses = self.mesh_processes
              self.mesh_obj.NumberOfThreads = self.mesh_threads

              #TODO: fix these, if we need to.
              #self.form.le_mesh_processes.setText(str(self.mesh_processes))
              #self.form.le_mesh_threads.setText(str(self.mesh_threads))

              #self.form.le_hostname.setText(self.hostname)
              #self.form.le_username.setText(self.username)

              #self.form.le_foam_processes.setText(str(self.foam_processes))
              #self.form.le_foam_threads.setText(str(self.foam_threads))
              #self.form.le_foam_dir.setText(self.foam_dir)
              #self.form.le_output_path.setText(self.output_path)
              #self.form.cb_add_filename_to_output.setChecked(self.add_filename_to_output)


    # this gets called when the user changes the profile
    def profileChanged(self):
        print("The profile was changed")
        # change the global profile name
        self.profile_name = self.form.cb_profile.currentText()
        #load the values for the new profile
        print ("New profile is ", self.profile_name)
        self.loadProfile(self.profile_name)
        # TODO enable and disable the appropriate controls here
        # Remote hosts can't edit the case nor Paraview, check mesh, etc.
        # Nor load surface mesh nor clear surface mesh.


    # test routine to run a mesh without
    # a proxy. The real routine is runMesh way below
    def runRemoteMesh(self):
        # run remote meshing directly, without a proxy
        #profile_prefs = CfdTools.getPreferencesLocation() + '/Hosts/' + self.profile_name
        remote_user = self.username
        remote_hostname = self.hostname

        # create the ssh connection command
        ssh_prefix = 'ssh -tt ' + remote_user + '@' + remote_hostname + ' '

        # Get the working directory for the mesh
        working_dir = self.output_path
        #TODO: add filename to the path if selected

        # create the command to do the actual work
        command = 'EOT \n'
        command += 'cd ' + working_dir + '/meshCase \n'
        command += './Allmesh \n'
        command += 'exit \n'
        command += 'EOT'
        command = ssh_prefix + ' << '  + command

        self.consoleMessage("Starting remote meshing...")
        try:
            CfdTools.runFoamCommand(command)
            print("Remote meshing is complete.")
            self.consoleMessage("Remote meshing is complete.")
        except Exception as error:
             self.consoleMessage("Error meshing on remote host: " + str(error))

    def getStandardButtons(self):
        return int(QtGui.QDialogButtonBox.Close)
        # def reject() is called on close button

    def reject(self):
        FreeCADGui.ActiveDocument.resetEdit()
        return True

    def closed(self):
        # We call this from unsetEdit to ensure cleanup
        self.store()
        self.mesh_obj.Proxy.mesh_process.terminate()
        self.mesh_obj.Proxy.mesh_process.waitForFinished()
        self.Timer.stop()
        FreeCAD.ActiveDocument.recompute()

    def load(self):
        """ Fills the widgets """
        setQuantity(self.form.if_max, self.mesh_obj.CharacteristicLengthMax)
        point_in_mesh = self.mesh_obj.PointInMesh.copy()
        setQuantity(self.form.if_pointInMeshX, point_in_mesh.get('x'))
        setQuantity(self.form.if_pointInMeshY, point_in_mesh.get('y'))
        setQuantity(self.form.if_pointInMeshZ, point_in_mesh.get('z'))

        self.form.if_cellsbetweenlevels.setValue(self.mesh_obj.CellsBetweenLevels)
        self.form.if_edgerefine.setValue(self.mesh_obj.EdgeRefinement)
        self.form.radio_implicit_edge_detection.setChecked(self.mesh_obj.ImplicitEdgeDetection)
        self.form.radio_explicit_edge_detection.setChecked(not self.mesh_obj.ImplicitEdgeDetection)

        index_utility = CfdTools.indexOrDefault(list(zip(
                CfdMesh.MESHERS, CfdMesh.DIMENSION, CfdMesh.DUAL_CONVERSION)), 
                (self.mesh_obj.MeshUtility, self.mesh_obj.ElementDimension, self.mesh_obj.ConvertToDualMesh), 0)
        self.form.cb_utility.setCurrentIndex(index_utility)

    def updateUI(self):
        case_path = self.mesh_obj.Proxy.cart_mesh.meshCaseDir
        self.form.pb_edit_mesh.setEnabled(os.path.exists(case_path))
        self.form.pb_run_mesh.setEnabled(os.path.exists(os.path.join(case_path, "Allmesh")))
        self.form.pb_paraview.setEnabled(os.path.exists(os.path.join(case_path, "pv.foam")))
        self.form.pb_load_mesh.setEnabled(os.path.exists(os.path.join(case_path, "mesh_outside.stl")))
        self.form.pb_check_mesh.setEnabled(os.path.exists(os.path.join(case_path, "mesh_outside.stl")))
        
        utility = CfdMesh.MESHERS[self.form.cb_utility.currentIndex()]
        if utility == "snappyHexMesh":
            self.form.snappySpecificProperties.setVisible(True)
        else:
            self.form.snappySpecificProperties.setVisible(False)

    def store(self):
        mesher_idx = self.form.cb_utility.currentIndex()
        storeIfChanged(self.mesh_obj, 'CharacteristicLengthMax', getQuantity(self.form.if_max))
        storeIfChanged(self.mesh_obj, 'MeshUtility', CfdMesh.MESHERS[mesher_idx])
        storeIfChanged(self.mesh_obj, 'ElementDimension', CfdMesh.DIMENSION[mesher_idx])
        storeIfChanged(self.mesh_obj, 'CellsBetweenLevels', self.form.if_cellsbetweenlevels.value())
        storeIfChanged(self.mesh_obj, 'EdgeRefinement', self.form.if_edgerefine.value())
        storeIfChanged(self.mesh_obj, 'ConvertToDualMesh', CfdMesh.DUAL_CONVERSION[mesher_idx])
        storeIfChanged(self.mesh_obj, 'ImplicitEdgeDetection', self.form.radio_implicit_edge_detection.isChecked())

        point_in_mesh = {'x': getQuantity(self.form.if_pointInMeshX),
                         'y': getQuantity(self.form.if_pointInMeshY),
                         'z': getQuantity(self.form.if_pointInMeshZ)}

        if self.mesh_obj.MeshUtility == 'snappyHexMesh':
            storeIfChanged(self.mesh_obj, 'PointInMesh', point_in_mesh)

        self.mesh_obj.Proxy.cart_mesh = CfdMeshTools.CfdMeshTools(self.mesh_obj)

    def consoleMessage(self, message="", colour_type=None, timed=True):
        if timed:
            self.console_message_cart += \
                '<font color="{}">{:4.1f}:</font> '.format(CfdTools.getColour('Logging'), time.time() - self.Start)
        if colour_type:
            self.console_message_cart += \
                '<font color="{}">{}</font><br>'.format(CfdTools.getColour(colour_type), message)
        else:
            self.console_message_cart += message + '<br>'
        self.form.te_output.setText(self.console_message_cart)
        self.form.te_output.moveCursor(QtGui.QTextCursor.End)
        if FreeCAD.GuiUp:
            FreeCAD.Gui.updateGui()

    def update_timer_text(self):
        if self.mesh_obj.Proxy.mesh_process.state() == QtCore.QProcess.ProcessState.Running:
            self.form.l_time.setText('Time: ' + CfdTools.formatTimer(time.time() - self.Start))

    def choose_utility(self, index):
        if index < 0:
            return
        utility = CfdMesh.MESHERS[self.form.cb_utility.currentIndex()]
        if utility == "snappyHexMesh":
            self.form.snappySpecificProperties.setVisible(True)
        else:
            self.form.snappySpecificProperties.setVisible(False)

    def writeMesh(self):
        import importlib
        importlib.reload(CfdMeshTools)
        self.console_message_cart = ''
        self.Start = time.time()
        # Re-initialise CfdMeshTools with new parameters
        self.store()

        #get the host name we are writing the mesh case for
        host_profile = self.profile_name
        print ("Writing mesh for host profile " + host_profile + ".")

        FreeCADGui.doCommand("from CfdOF.Mesh import CfdMeshTools")
        FreeCADGui.doCommand("from CfdOF import CfdTools")
        FreeCADGui.doCommand("cart_mesh = "
                             "CfdMeshTools.CfdMeshTools(FreeCAD.ActiveDocument." + self.mesh_obj.Name + ")")
        FreeCADGui.doCommand("FreeCAD.ActiveDocument." + self.mesh_obj.Name + ".Proxy.cart_mesh = cart_mesh")
        cart_mesh = self.mesh_obj.Proxy.cart_mesh
        cart_mesh.progressCallback = self.progressCallback

        # Start writing the mesh files
        if host_profile == "local":
            self.consoleMessage("Preparing local mesh ...")
        else:
            self.consoleMessage("Preparing remote mesh for " + host_profile + "...")
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            setQuantity(self.form.if_max, str(cart_mesh.getClmax()))
            # Re-update the data in case ClMax was auto-set to avoid spurious update detection on next write
            self.store()
            print('Part to mesh:\n  Name: '
                  + cart_mesh.part_obj.Name + ', Label: '
                  + cart_mesh.part_obj.Label + ', ShapeType: '
                  + cart_mesh.part_obj.Shape.ShapeType)
            print('  CharacteristicLengthMax: ' + str(cart_mesh.clmax))

            if host_profile == "local":
                FreeCADGui.doCommand("cart_mesh.writeMesh('local')")
            else:
                FreeCADGui.doCommand("cart_mesh.writeMesh('"+ host_profile +"')")

        except Exception as ex:
            self.consoleMessage("Error " + type(ex).__name__ + ": " + str(ex), 'Error')
            raise
        else:
            self.analysis_obj.NeedsMeshRerun = True
        finally:
            QApplication.restoreOverrideCursor()

        # Update the UI
        self.updateUI()


    def progressCallback(self, message):
        self.consoleMessage(message)

    def checkMeshClicked(self):
        if CfdTools.getFoamRuntime() == "PosixDocker":
            CfdTools.startDocker()
        self.Start = time.time()
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            FreeCADGui.doCommand("from CfdOF import CfdTools")
            FreeCADGui.doCommand("from CfdOF.Mesh import CfdMeshTools")
            FreeCADGui.doCommand("from CfdOF import CfdConsoleProcess")
            FreeCADGui.doCommand("cart_mesh = "
                                 "CfdMeshTools.CfdMeshTools(FreeCAD.ActiveDocument." + self.mesh_obj.Name + ")")
            FreeCADGui.doCommand("proxy = FreeCAD.ActiveDocument." + self.mesh_obj.Name + ".Proxy")
            FreeCADGui.doCommand("proxy.cart_mesh = cart_mesh")
            FreeCADGui.doCommand("cart_mesh.error = False")
            FreeCADGui.doCommand("cmd = CfdTools.makeRunCommand('checkMesh -meshQuality', cart_mesh.meshCaseDir)")
            FreeCADGui.doCommand("env_vars = CfdTools.getRunEnvironment()")
            FreeCADGui.doCommand("proxy.running_from_macro = True")
            self.mesh_obj.Proxy.running_from_macro = False
            FreeCADGui.doCommand("if proxy.running_from_macro:\n" +
                                 "  mesh_process = CfdConsoleProcess.CfdConsoleProcess()\n" +
                                 "  mesh_process.start(cmd, env_vars=env_vars)\n" +
                                 "  mesh_process.waitForFinished()\n" +
                                 "else:\n" +
                                 "  proxy.mesh_process.start(cmd, env_vars=env_vars)")
            if self.mesh_obj.Proxy.mesh_process.waitForStarted():
                self.form.pb_check_mesh.setEnabled(False)   # Prevent user running a second instance
                self.form.pb_run_mesh.setEnabled(False)
                self.form.pb_write_mesh.setEnabled(False)
                #self.form.pb_write_remote_mesh.setEnabled(False)
                self.form.pb_stop_mesh.setEnabled(False)
                self.form.pb_paraview.setEnabled(False)
                self.form.pb_load_mesh.setEnabled(False)
                self.consoleMessage("Mesh check started ...")
            else:
                self.consoleMessage("Error starting mesh check process", 'Error')
                self.mesh_obj.Proxy.cart_mesh.error = True

        except Exception as ex:
            self.consoleMessage("Error " + type(ex).__name__ + ": " + str(ex), 'Error')
        finally:
            QApplication.restoreOverrideCursor()


    def editMesh(self):
        case_path = self.mesh_obj.Proxy.cart_mesh.meshCaseDir
        self.consoleMessage("Please edit the case input files externally at: {}\n".format(case_path))
        CfdTools.openFileManager(case_path)


    #TODO: won't run remotely with a proxy yet.  Fix this.
    # Presently running without a proxy in runRemoteMesh way above.
    def runMesh(self):
        if CfdTools.getFoamRuntime() == "PosixDocker":
            CfdTools.startDocker()

        self.Start = time.time()

        # Check for changes that require mesh re-write
        self.store()
        if self.analysis_obj.NeedsMeshRewrite:
            if FreeCAD.GuiUp:
                if QtGui.QMessageBox.question(
                    None,
                    "CfdOF Workbench",
                    "The case setup for the mesher may need to be re-written based on changes you have made to the "
                    "model.\n\nWrite mesh case first?", defaultButton=QtGui.QMessageBox.Yes
                ) == QtGui.QMessageBox.Yes:
                    self.Start = time.time()
                    self.writeMesh()
                else:
                    self.Start = time.time()

        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)

            self.consoleMessage("Initializing {} ...".format(self.mesh_obj.MeshUtility))
            FreeCADGui.doCommand("from CfdOF.Mesh import CfdMeshTools")
            FreeCADGui.doCommand("from CfdOF import CfdTools")
            FreeCADGui.doCommand("from CfdOF import CfdConsoleProcess")
            FreeCADGui.doCommand("from FreeCAD import ParamGet")
            
            FreeCADGui.doCommand("cart_mesh = " +
                                 "CfdMeshTools.CfdMeshTools(FreeCAD.ActiveDocument." + self.mesh_obj.Name + ")")
            
            FreeCADGui.doCommand("proxy = FreeCAD.ActiveDocument." + self.mesh_obj.Name + ".Proxy")
            FreeCADGui.doCommand("proxy.cart_mesh = cart_mesh")
            FreeCADGui.doCommand("cart_mesh.error = False")

            # run locally
            if self.profile_name == "local":
                FreeCADGui.doCommand("cmd = CfdTools.makeRunCommand('./Allmesh', cart_mesh.meshCaseDir, source_env=False)")
                FreeCADGui.doCommand("env_vars = CfdTools.getRunEnvironment()")

                FreeCADGui.doCommand("print('cmd:')")
                FreeCADGui.doCommand("print(cmd)")
                #FreeCADGui.doCommand("print('env_vars:' + env_vars)")

                FreeCADGui.doCommand("proxy.running_from_macro = True")
                self.mesh_obj.Proxy.running_from_macro = False

                FreeCADGui.doCommand("if proxy.running_from_macro:\n" +
                                      "  mesh_process = CfdConsoleProcess.CfdConsoleProcess()\n" +
                                      "  mesh_process.start(cmd, env_vars=env_vars)\n" +
                                      "  mesh_process.waitForFinished()\n" +
                                      "else:\n" +
                                      "  proxy.mesh_process.start(cmd, env_vars=env_vars)")

            # run on remote host
            else:
                 #self.runRemoteMesh()  #For testing the non proxy function above

                 # Get the username and hostname for the remote host
                 prefsCmd = "profile_prefs = CfdTools.getPreferencesLocation() + " + '"/Hosts/' + self.profile_name + '"'
                 #print("prefsCmd:" + prefsCmd)
                 FreeCADGui.doCommand(prefsCmd)
                 FreeCADGui.doCommand("print('profile_prefs:' + profile_prefs)")

                 FreeCADGui.doCommand("remote_user = FreeCAD.ParamGet(profile_prefs).GetString('Username', '')")
                 FreeCADGui.doCommand("remote_hostname =FreeCAD.ParamGet(profile_prefs).GetString('Hostname', '')")

                 #FreeCADGui.doCommand("print('username:' + remote_user)")
                 #FreeCADGui.doCommand("print('hostname:' + remote_hostname)")

                 # create the ssh connection command
                 FreeCADGui.doCommand("ssh_prefix = 'ssh -tt ' + remote_user + '@' + remote_hostname + ' '")

                 # Get the working directory for the mesh
                 FreeCADGui.doCommand("working_dir = FreeCAD.ParamGet(profile_prefs).GetString('OutputPath', '')")
                 #FreeCADGui.doCommand("print('working directory:' + working_dir)")


                 # create the command to do the actual work
                 FreeCADGui.doCommand("command = 'EOT \\n' \n" +
                                      "command += 'cd ' + working_dir + '/meshCase \\n' \n" +
                                      "command += './Allmesh \\n' \n" +
                                      "command += 'exit \\n' \n" +
                                      "command += 'EOT' \n")
                 FreeCADGui.doCommand("command = ssh_prefix + ' << '  + command + '\\n'")

                 #FreeCADGui.doCommand("print(command)")

                 FreeCADGui.doCommand("runCommand = CfdTools.makeRunCommand(command, None)")

                 FreeCADGui.doCommand("proxy.running_from_macro = True")
                 self.mesh_obj.Proxy.running_from_macro = False

                 FreeCADGui.doCommand("if proxy.running_from_macro:\n" +
                                      "  mesh_process = CfdConsoleProcess.CfdConsoleProcess()\n" +
                                      "  mesh_process.start(runCommand)\n" +
                                      "  mesh_process.waitForFinished()\n" +
                                      "else:\n" +
                                      "  proxy.mesh_process.start(runCommand)")

            time.sleep(2)
            if self.mesh_obj.Proxy.mesh_process.waitForStarted():
                # enable/disable the correct buttons
                """
                if self.profile_name == "local":
                    self.form.pb_stop_mesh.setEnabled(True)

                    self.form.pb_run_mesh.setEnabled(False)
                    #self.form.pb_run_remote_mesh.setEnabled(False)
                    self.form.pb_write_mesh.setEnabled(False)
                    #self.form.pb_write_remote_mesh.setEnabled(False)
                    self.form.pb_edit_mesh.setEnabled(False)
                    #self.form.pb_edit_remote_mesh.setEnabled(False)

                    self.form.pb_check_mesh.setEnabled(False)
                    self.form.pb_paraview.setEnabled(False)
                    self.form.pb_load_mesh.setEnabled(False)
                else:
                    if self.useRemoteProcessing:
                        #self.form.pb_stop_remote_mesh.setEnabled(True)

                        self.form.pb_run_mesh.setEnabled(False)
                        #self.form.pb_run_remote_mesh.setEnabled(False)
                        self.form.pb_write_mesh.setEnabled(False)
                        self.form.pb_write_remote_mesh.setEnabled(False)
                        self.form.pb_edit_mesh.setEnabled(False)
                        self.form.pb_edit_remote_mesh.setEnabled(False)

                        self.form.pb_check_mesh.setEnabled(False)
                        self.form.pb_paraview.setEnabled(False)
                        self.form.pb_load_mesh.setEnabled(False)
                """
                self.consoleMessage("Mesher started ...")
            else:
                self.consoleMessage("Error starting meshing process", 'Error')
                self.mesh_obj.Proxy.cart_mesh.error = True
        except Exception as ex:
            self.consoleMessage("Error " + type(ex).__name__ + ": " + str(ex), 'Error')
            raise
        finally:
            QApplication.restoreOverrideCursor()


    def killMeshProcess(self):
        self.consoleMessage("Meshing manually stopped")
        self.error_message = 'Meshing interrupted'
        self.mesh_obj.Proxy.mesh_process.terminate()
        # Note: meshFinished will still be called

    def gotOutputLines(self, lines):
        pass

    def gotErrorLines(self, lines):
        print_err = self.mesh_obj.Proxy.mesh_process.processErrorOutput(lines)
        if print_err is not None:
            self.consoleMessage(print_err, 'Error')

    def meshFinished(self, exit_code):
        if exit_code == 0:
            self.consoleMessage('Meshing completed')
            self.analysis_obj.NeedsMeshRerun = False
            self.form.pb_run_mesh.setEnabled(True)
            self.form.pb_stop_mesh.setEnabled(False)
            self.form.pb_paraview.setEnabled(True)
            self.form.pb_write_mesh.setEnabled(True)
            self.form.pb_check_mesh.setEnabled(True)
            self.form.pb_load_mesh.setEnabled(True)

            if self.useRemoteProcessing:
                pass
                #self.form.pb_run_remote_mesh.setEnabled(True)
                #self.form.pb_stop_remote_mesh.setEnabled(False)
                #self.form.pb_write_remote_mesh.setEnabled(True)

        else:
            self.consoleMessage("Meshing exited with error", 'Error')
            self.form.pb_run_mesh.setEnabled(True)
            self.form.pb_stop_mesh.setEnabled(False)
            self.form.pb_write_mesh.setEnabled(True)
            self.form.pb_check_mesh.setEnabled(False)
            self.form.pb_paraview.setEnabled(False)

            if self.useRemoteProcessing:
                pass
                #self.form.pb_run_remote_mesh.setEnabled(True)
                #self.form.pb_stop_remote_mesh.setEnabled(False)
                #self.form.pb_write_remote_mesh.setEnabled(True)

        self.error_message = ''
        # Get rid of any existing loaded mesh
        self.pbClearMeshClicked()
        self.updateUI()

    def openParaview(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        case_path = os.path.abspath(self.mesh_obj.Proxy.cart_mesh.meshCaseDir)
        script_name = "pvScriptMesh.py"
        try:
            CfdTools.startParaview(case_path, script_name, self.consoleMessage)
        finally:
            QApplication.restoreOverrideCursor()

    def pbLoadMeshClicked(self):
        self.consoleMessage("Reading mesh ...", timed=False)
        prev_write_mesh = self.analysis_obj.NeedsMeshRewrite
        self.mesh_obj.Proxy.cart_mesh.loadSurfMesh()
        self.analysis_obj.NeedsMeshRewrite = prev_write_mesh
        self.consoleMessage('Triangulated representation of the surface mesh is shown - ', timed=False)
        self.consoleMessage("Please view in Paraview for accurate display.\n", timed=False)

    def pbClearMeshClicked(self):
        prev_write_mesh = self.analysis_obj.NeedsMeshRewrite
        for m in self.mesh_obj.Group:
            if m.isDerivedFrom("Fem::FemMeshObject"):
                FreeCAD.ActiveDocument.removeObject(m.Name)
        self.analysis_obj.NeedsMeshRewrite = prev_write_mesh
        FreeCAD.ActiveDocument.recompute()

    def searchPointInMesh(self):
        print ("Searching for an internal vector point ...")
        # Apply latest mesh size
        self.store()
        pointCheck = self.mesh_obj.Proxy.cart_mesh.automaticInsidePointDetect()
        if pointCheck is not None:
            iMPx, iMPy, iMPz = pointCheck
            setQuantity(self.form.if_pointInMeshX, str(iMPx) + "mm")
            setQuantity(self.form.if_pointInMeshY, str(iMPy) + "mm")
            setQuantity(self.form.if_pointInMeshZ, str(iMPz) + "mm")
