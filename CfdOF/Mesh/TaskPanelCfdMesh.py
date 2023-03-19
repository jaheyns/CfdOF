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
# TODOs, in addition to TODOs in the code itself
#
# -This code uses (dangerous) global vars to access things like profile_name, hostname, output dir, etc.
# The profile_name, hostname, output dir should be attached to the mesh object and used from it.
#
# -the ParaView button gets enabled as soon as the mesh case is written before the results are
# available.   This should be fixed.  See updateUI.
#
# -the Clear Surface mesh button is enabled even when the surface isn't loaded.  This should be fixed in
# updateUI.
#
# -the UI doesn't know where a meshCase is available to run.  You can write a mesh case to the local, then
# change to a host and Run Mesh will be available to use. But there is no meshCase on that host yet.  Ideally
# the mesh object would retain the host that the mesh case is on so that it could properly enable various actions.  Luckily
# run mesh fails gracefully if no mesh case is found.
#
# -delete_remote_results removes the meshCase after a successful solve.  Actually, I disabled this.  Thus you (would) have to rewrite
# the mesh case and rerun it on the server after every successful solve, if delete_remote_results is selected.
#
# -edit mesh should copy the edited mesh to the server after the edit is done. Right now it doesn't.
#
# -remote meshing has not been tested in macros.
#
# -cfMesh runs only 1 mesh process on the remote machine if 1,0 is selected for processes, threads.  If you run 8 threads (1,8) for example, it
# doesn't ever finish the meshing process stack on the remote host is this.  Looks legit, but never finishes.
#
# $ ps aux | grep Mesh
#me        134162  0.0  0.0 174292 17336 ?        Sl   21:58   0:00 mpiexec -np 8 /home/me/OpenFOAM/me-2206/platforms/linux64GccDPInt32Opt/bin/cartesianMesh -parallel
#me        134163  0.0  0.0 221328   944 ?        S    21:58   0:00 tee -a log.cartesianMesh
#me        134164  0.0  0.0 221328   892 ?        S    21:58   0:00 tee -a log.cartesianMesh
#me        134168  102  0.3 4034732 237604 ?      Rl   21:58   5:22 /home/me/OpenFOAM/me-2206/platforms/linux64GccDPInt32Opt/bin/cartesianMesh -parallel
#me        134169  102  0.3 4038380 231280 ?      Rl   21:58   5:22 /home/me/OpenFOAM/me-2206/platforms/linux64GccDPInt32Opt/bin/cartesianMesh -parallel
#me        134170  102  0.3 4029584 221532 ?      Rl   21:58   5:22 /home/me/OpenFOAM/me-2206/platforms/linux64GccDPInt32Opt/bin/cartesianMesh -parallel
#me        134171  102  0.3 4063928 258864 ?      Rl   21:58   5:22 /home/me/OpenFOAM/me-2206/platforms/linux64GccDPInt32Opt/bin/cartesianMesh -parallel
#me        134172  102  0.3 4035376 234968 ?      Rl   21:58   5:22 /home/me/OpenFOAM/me-2206/platforms/linux64GccDPInt32Opt/bin/cartesianMesh -parallel
#me        134173  102  0.3 4032120 233276 ?      Rl   21:58   5:22 /home/me/OpenFOAM/me-2206/platforms/linux64GccDPInt32Opt/bin/cartesianMesh -parallel
#me        134174  102  0.3 4030184 221800 ?      Rl   21:58   5:22 /home/me/OpenFOAM/me-2206/platforms/linux64GccDPInt32Opt/bin/cartesianMesh -parallel
#me        134175  102  0.3 4066644 257484 ?      Rl   21:58   5:22 /home/me/OpenFOAM/me-2206/platforms/linux64GccDPInt32Opt/bin/cartesianMesh -parallel



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
        self.copy_back = False
        self.delete_remote_results = False

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
        self.form.pb_copy_to_host.clicked.connect(self.copyMeshcaseToHost)
        self.form.pb_delete_mesh.clicked.connect(self.deleteMeshcase)

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
              # enable controls for the local host
              self.form.pb_edit_mesh.setEnabled(True)
              self.form.pb_paraview.setEnabled(True)
              self.form.pb_check_mesh.setEnabled(True)
              self.form.pb_load_mesh.setEnabled(True)
              self.form.pb_clear_mesh.setEnabled(True)

              # the local code doesn't use these vars, setting them to be safe
              self.username = ""
              self.mesh_processes = 0
              self.mesh_threads = 0
              self.foam_processes = 0
              self.foam_threads = 0
              #self.foam_dir = FreeCAD.ParamGet(Prefs).GetString("FoamDir", "")
              #self.output_path = FreeCAD.ParamGet(Prefs).GetString("OutputPath","")
              self.output_path = ""
              self.add_filename_to_output = False
              # Not sure if this causes a side effect or not.
              case_path = self.mesh_obj.Proxy.cart_mesh.meshCaseDir
              self.form.pb_delete_mesh.setEnabled(os.path.exists(os.path.join(case_path, "Allmesh")))

         else:
              # set the vars to the remote host parameters
              # most of these aren't used, at least not in this page
              hostPrefs = self.host_prefs_location
              self.hostname = FreeCAD.ParamGet(hostPrefs).GetString("Hostname", "")
              self.username = FreeCAD.ParamGet(hostPrefs).GetString("Username", "")
              self.mesh_processes = FreeCAD.ParamGet(hostPrefs).GetInt("MeshProcesses")
              self.mesh_threads = FreeCAD.ParamGet(hostPrefs).GetInt("MeshThreads")
              self.foam_processes = FreeCAD.ParamGet(hostPrefs).GetInt("FoamProcesses")
              self.foam_threads = FreeCAD.ParamGet(hostPrefs).GetInt("FoamThreads")
              self.foam_dir = FreeCAD.ParamGet(hostPrefs).GetString("FoamDir", "")

              #self.output_path = FreeCAD.ParamGet(hostPrefs).GetString("OutputPath","")
              self.output_path = CfdTools.getDefaultOutputPath(self.profile_name)
              self.add_filename_to_output = FreeCAD.ParamGet(hostPrefs).GetBool("AddFilenameToOutput")
              self.copy_back = FreeCAD.ParamGet(hostPrefs).GetBool("CopyBack")
              self.delete_remote_results = FreeCAD.ParamGet(hostPrefs).GetBool("DeleteRemoteResults")

              #now set the control values
              self.mesh_obj.NumberOfProcesses = self.mesh_processes
              self.mesh_obj.NumberOfThreads = self.mesh_threads

              # disable if using a remote host
              self.form.pb_edit_mesh.setEnabled(False)
              self.form.pb_paraview.setEnabled(False)
              self.form.pb_check_mesh.setEnabled(False)
              self.form.pb_load_mesh.setEnabled(False)
              self.form.pb_clear_mesh.setEnabled(False)

              # enable if using a remote host
              case_path = self.mesh_obj.Proxy.cart_mesh.meshCaseDir
              self.form.pb_copy_to_host.setEnabled(os.path.exists(os.path.join(case_path, "Allmesh")))
              # TODO should check if there is a mesh case on the remote host and set accordingly
              self.form.pb_delete_mesh.setEnabled(True)

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

        # enable and disable the appropriate controls
        self.updateUI

    # test routine to run a mesh without a proxy
    # The real routine is runMesh down below
    def runRemoteMesh(self):
        # run remote meshing directly, without a proxy
        #profile_prefs = CfdTools.getPreferencesLocation() + '/Hosts/' + self.profile_name
        remote_user = self.username
        remote_hostname = self.hostname

        # create the ssh connection command
        # was ssh -tt
        ssh_prefix = 'ssh -t ' + remote_user + '@' + remote_hostname + ' '

        # Get the working directory for the mesh
        working_dir = self.output_path
        #TODO: add filename to the path if selected

        # create the command to do the actual work
        #command = 'EOT \n'
        command = 'cd ' + working_dir + '/meshCase \n'
        command += './Allmesh \n'
        command += 'exit \n'
        command += 'EOT \n'
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

    #TODO: this should be changed to reflect if the host is local or remote
    def updateUI(self):

        case_path = self.mesh_obj.Proxy.cart_mesh.meshCaseDir
        utility = CfdMesh.MESHERS[self.form.cb_utility.currentIndex()]
        if utility == "snappyHexMesh":
            self.form.snappySpecificProperties.setVisible(True)
        else:
            self.form.snappySpecificProperties.setVisible(False)

        # enable the appropriate controls
        # this is always an appropriate action
        self.form.pb_write_mesh.setEnabled(True)

        #enable these if the mesh is available locally
        if self.profile_name == 'local' or self.copy_back :
            self.form.pb_copy_to_host.setEnabled(False)
            self.form.pb_delete_mesh.setEnabled(os.path.exists(os.path.join(case_path, "Allmesh")))
            self.form.pb_edit_mesh.setEnabled(os.path.exists(case_path))
            # TODO have to enable this for the case that there is no local meshcase but
            # we have written one to a remote host  We should be checking if the case is available on
            # the remote host, not the local host
            #self.form.pb_run_mesh.setEnabled(os.path.exists(os.path.join(case_path, "Allmesh")))
            self.form.pb_run_mesh.setEnabled(True)

            # TODO This enables as soon as the mesh case is written.  It shouldn't.
            self.form.pb_paraview.setEnabled(os.path.exists(os.path.join(case_path, "pv.foam")))
            self.form.pb_load_mesh.setEnabled(os.path.exists(os.path.join(case_path, "mesh_outside.stl")))
            self.form.pb_check_mesh.setEnabled(os.path.exists(os.path.join(case_path, "mesh_outside.stl")))
            # TODO Should check that the mesh is loaded before enabling this. Not working right the way it is
            self.form.pb_clear_mesh.setEnabled(True)      

        # remote host is being used without copy_back
        # no local results to work on so disable these controls
        else:
            #self.form.pb_copy_to_host.setEnabled(os.path.exists(os.path.join(case_path, "Allmesh")))
            local_dir = CfdTools.getDefaultOutputPath('local')
            self.form.pb_copy_to_host.setEnabled(os.path.exists(os.path.join(local_dir, "meshCase")))
            #TODO should check if the mesh is present on the remote host
            self.form.pb_delete_mesh.setEnabled(True)
            # remote hosts don't support these functions yet
            self.form.pb_run_mesh.setEnabled(True)
            self.form.pb_paraview.setEnabled(False)
            self.form.pb_check_mesh.setEnabled(False)
            self.form.pb_load_mesh.setEnabled(False)
            self.form.pb_clear_mesh.setEnabled(False)

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
            FreeCADGui.doCommand("from CfdOF.CfdConsoleProcess import CfdConsoleProcess")
            FreeCADGui.doCommand("cart_mesh = "
                                 "    CfdMeshTools.CfdMeshTools(FreeCAD.ActiveDocument." + self.mesh_obj.Name + ")")
            FreeCADGui.doCommand("proxy = FreeCAD.ActiveDocument." + self.mesh_obj.Name + ".Proxy")
            FreeCADGui.doCommand("proxy.cart_mesh = cart_mesh")
            FreeCADGui.doCommand("cart_mesh.error = False")
            FreeCADGui.doCommand("cmd = CfdTools.makeRunCommand('checkMesh -meshQuality', cart_mesh.meshCaseDir)")
            FreeCADGui.doCommand("env_vars = CfdTools.getRunEnvironment()")
            self.check_mesh_error = False
            FreeCADGui.doCommand("proxy.running_from_macro = True")
            self.mesh_obj.Proxy.running_from_macro = False
            self.mesh_obj.Proxy.check_mesh_process = CfdConsoleProcess(
                stdout_hook=self.gotOutputLines, stderr_hook=self.gotErrorLines)
            FreeCADGui.doCommand("if proxy.running_from_macro:\n" +
                                 "  mesh_process = CfdConsoleProcess.CfdConsoleProcess()\n" +
                                 "  mesh_process.start(cmd, env_vars=env_vars)\n" +
                                 "  mesh_process.waitForFinished()\n" +
                                 "  proxy.check_mesh_process = CfdConsoleProcess()\n" +
                                 "  proxy.check_mesh_process.start(cmd, env_vars=env_vars)\n" +
                                 "  proxy.check_mesh_process.waitForFinished()\n" +
                                 "else:\n" +
                                 #"  proxy.mesh_process.start(cmd, env_vars=env_vars)"+
                                 "  proxy.check_mesh_process.start(cmd, env_vars=env_vars)")

            if self.mesh_obj.Proxy.mesh_process.waitForStarted():
                self.form.pb_check_mesh.setEnabled(False)   # Prevent user running a second instance
                self.form.pb_run_mesh.setEnabled(False)
                self.form.pb_write_mesh.setEnabled(False)
                self.form.pb_stop_mesh.setEnabled(False)
                self.form.pb_paraview.setEnabled(False)
                self.form.pb_load_mesh.setEnabled(False)


            if self.mesh_obj.Proxy.check_mesh_process.waitForStarted():
                self.consoleMessage("Mesh check started ...")
            else:
                self.consoleMessage("Error starting mesh check process", 'Error')
            if self.mesh_obj.Proxy.check_mesh_process.waitForFinished():
                if self.check_mesh_error:
                    self.consoleMessage("Detected error(s) in mesh", 'Error')
                else:
                    self.consoleMessage("Mesh check OK")
            else:
                self.consoleMessage("Mesh check process failed")

        except Exception as ex:
            self.consoleMessage("Error " + type(ex).__name__ + ": " + str(ex), 'Error')
        finally:
            QApplication.restoreOverrideCursor()


    def editMesh(self):
        case_path = self.mesh_obj.Proxy.cart_mesh.meshCaseDir
        self.consoleMessage("Please edit the case input files externally at: {}\n".format(case_path))
        CfdTools.openFileManager(case_path)

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
            

            FreeCADGui.doCommand("cart_mesh = "
                                 "    CfdMeshTools.CfdMeshTools(FreeCAD.ActiveDocument." + self.mesh_obj.Name + ")")

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
                 # was ssh -tt
                 FreeCADGui.doCommand("ssh_prefix = 'ssh -t ' + remote_user + '@' + remote_hostname + ' '")

                 # Get the working directory for the mesh
                 #FreeCADGui.doCommand("working_dir = FreeCAD.ParamGet(profile_prefs).GetString('OutputPath', '')")
                 FreeCADGui.doCommand("working_dir = CfdTools.getDefaultOutputPath('" + self.profile_name + "' )")
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

            if self.mesh_obj.Proxy.mesh_process.waitForStarted():
                # enable/disable the correct buttons
                self.form.pb_stop_mesh.setEnabled(True)
                self.form.pb_run_mesh.setEnabled(False)
                self.form.pb_write_mesh.setEnabled(False)
                self.form.pb_edit_mesh.setEnabled(False)
                self.form.pb_check_mesh.setEnabled(False)
                self.form.pb_paraview.setEnabled(False)
                self.form.pb_load_mesh.setEnabled(False)
                self.form.pb_clear_mesh.setEnabled(False)
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
        for l in lines.split('\n'):
            if l.endswith("faces in error to set meshQualityFaces"):
                self.check_mesh_error = True

    def gotErrorLines(self, lines):
        print_err = self.mesh_obj.Proxy.mesh_process.processErrorOutput(lines)
        if print_err is not None:
            self.consoleMessage(print_err, 'Error')

    def meshFinished(self, exit_code):
        if self.form.cb_notify.isChecked():
            #print("Beeping now")
            QApplication.beep()
        if exit_code == 0:
            self.consoleMessage('Meshing completed')
            self.analysis_obj.NeedsMeshRerun = False

            #check if there is work to do on the remote host
            if self.profile_name != 'local':
                # copy the meshcase back to the workstation?
                # this code is also used in reverse in CfdMeshTools.py for copying the mesh case to the server
                if self.copy_back:
                    local_prefs = CfdTools.getPreferencesLocation()
                    profile_prefs = local_prefs +"/Hosts/" + self.profile_name

                    remote_user = FreeCAD.ParamGet(profile_prefs).GetString("Username", "")
                    remote_hostname = FreeCAD.ParamGet(profile_prefs).GetString("Hostname", "")
                    remote_output_path = CfdTools.getDefaultOutputPath(self.profile_name)
                    local_output_path = CfdTools.getDefaultOutputPath('local')

                    #case_path = os.path.abspath(self.mesh_obj.Proxy.cart_mesh.meshCaseDir)
                    # If this ^ is used as the destination dir, it will put the remote meshCase dir in the
                    # local meshCase directory, which is wrong (/tmp/CfdOF/meshCase/meshCase, for example

                    # if we are deleting the mesh case on the server
                    # don't delete the mesh case.  In most cases we need it for the solver to run later
                    # it will be deleted after the solve if we elect to remove results

                    """
                    if self.delete_remote_results:
                        deleteStr = "--remove-source-files "
                    else:
                        deleteStr = ""
                    """
                    deleteStr = ""

                    # rsync the meshCase result on the server to the workstation's output directory
                    # Typical useage: rsync -r  --delete --remove-source-files me@david/tmp/meshCase /tmp
                    # --remove-source-files removes the files that get transfered
                    # --delete removes files from the destination that didn't get transfered

                    try:
                        CfdTools.runFoamCommand("rsync -r --delete " + deleteStr +  remote_user + "@" + remote_hostname + ":" + remote_output_path + "/meshCase " +  \
                                    local_output_path)
                    except Exception as e:
                        CfdTools.cfdMessage("Could not copy mesh to local computer: " + str(e))
                        if self.progressCallback:
                            self.progressCallback("Could not copy mesh to local computer: " + str(e))
                    else:
                        CfdTools.cfdMessage("Copied mesh case to " + local_output_path + " on local computer\n" )
                        if self.progressCallback:
                            self.progressCallback("Copied mesh case to " + local_output_path  + "on local computer\n")
                if self.progressCallback:
                        self.progressCallback("Mesh case copy back process is complete.")

                # delete the result on the server ?
                # if this got deleted then we'd have to remesh every run
                # or copy a mesh from the local machine to the server
                # not implemented for this reason
                if self.delete_remote_results:
                    pass

        else:
            self.consoleMessage("Meshing exited with error", 'Error')

        # update the controls
        self.error_message = ''
        # Get rid of any existing loaded mesh
        self.pbClearMeshClicked()
        self.updateUI()


    # Delete the mesh case on the current host, including the local host if it is the current host
    # TODO: Add a warning for the user so they can cancel if desired
    def deleteMeshcase(self):
        # local host
        if self.hostname == 'local':
            #TODO Check if the meshCase exists
            local_output_path = CfdTools.getDefaultOutputPath('local')
            print("Local output path:" + local_output_path)

            # create the command to do the actual work
            # TODO  This won't work on a Windows or Mac machine Fix it
            command = "rm -rf " + local_output_path + "/meshCase"

            try:
                CfdTools.runFoamCommand(command, "./")

            except Exception as e:
                    CfdTools.cfdMessage("Could not delete the local mesh case:"  + str(e))
                    self.consoleMessage("Could not delete the local mesh case:" + str(e))
            else:
                    CfdTools.cfdMessage("Deleted the mesh case in " + local_output_path + "\n" )
                    self.consoleMessage("Deleted the mesh case in " + local_output_path + "\n" )
                    # now update the UI
                    self.updateUI

        # remote host
        # TODO uses a combination of looked up parameters and local vars !  Very dangerous.  Fix this
        # TODO check if mesh case exists
        else:
            local_prefs = CfdTools.getPreferencesLocation()
            profile_prefs = local_prefs +"/Hosts/" + self.profile_name
            #remote_user = FreeCAD.ParamGet(profile_prefs).GetString("Username", "")
            remote_hostname = FreeCAD.ParamGet(profile_prefs).GetString("Hostname", "")
            #remote_output_path = FreeCAD.ParamGet(profile_prefs).GetString("OutputPath","")
            remote_output_path = CfdTools.getDefaultOutputPath(self.profile_name)

            # create the command to do the actual work
            command = 'ssh -tt ' + self.username + '@' + self.hostname + " "   # was -tt
            command += ' << EOT \n'
            command += 'cd ' + remote_output_path + '\n'
            command += 'rm -rf meshCase ' + '\n'
            command += 'exit \n '
            command += 'EOT \n'
            #print("Code command:" + command)

            try:
                CfdTools.runFoamCommand(command)

            except Exception as e:
                    CfdTools.cfdMessage("Could not delete mesh case on remote host:"  + str(e))
                    self.consoleMessage("Could not delete mesh case on remote host:" + str(e))
            else:
                    CfdTools.cfdMessage("Deleted mesh case in " + remote_hostname + ":" + remote_output_path + "\n" )
                    self.consoleMessage("Deleted mesh case in " + remote_hostname + ":" + remote_output_path + "\n" )
                    # now update the UI
                    self.updateUI



    def copyMeshcaseToHost(self):
        #check that a host is selected
        if self.profile_name == 'local':
           self.consoleMessage("Select a host to copy the mesh case to.")
        else:
            # copy the meshcase back to the workstation
            # this code is also used in reverse in CfdMeshTools.py for copying the mesh case to the server
            local_prefs = CfdTools.getPreferencesLocation()
            profile_prefs = local_prefs +"/Hosts/" + self.profile_name

            remote_user = FreeCAD.ParamGet(profile_prefs).GetString("Username", "")
            remote_hostname = FreeCAD.ParamGet(profile_prefs).GetString("Hostname", "")

            #remote_output_path = FreeCAD.ParamGet(profile_prefs).GetString("OutputPath","")
            #local_output_path = FreeCAD.ParamGet(local_prefs).GetString("DefaultOutputPath","")

            remote_output_path = CfdTools.getDefaultOutputPath(self.profile_name)
            local_output_path = CfdTools.getDefaultOutputPath('local')


            #case_path = os.path.abspath(self.mesh_obj.Proxy.cart_mesh.meshCaseDir)
            # If this ^ is used as the destination dir, it will put the remote meshCase dir in the
            # local meshCase directory, which is wrong (/tmp/CfdOF/meshCase/meshCase, for example

            # rsync the meshCase result on the server to the workstation's output directory
            # Typical useage: rsync -r  --delete --remove-source-files me@david/tmp/meshCase /tmp
            # --remove-source-files removes the files that get transfered
            # --delete removes files from the destination that didn't get transfered

            try:
                CfdTools.runFoamCommand("rsync -r --delete " + local_output_path + "/meshCase " + remote_user + "@" + remote_hostname + ":" \
                + remote_output_path)

            except Exception as e:
                    CfdTools.cfdMessage("Could not copy mesh case to host: " + str(e))
                    self.consoleMessage("Could not copy mesh case to host: " + str(e))
            else:
                    CfdTools.cfdMessage("Copied mesh case to " + remote_hostname + ":" + remote_output_path + "\n" )
                    self.consoleMessage("Copied mesh case to " + remote_hostname + ":" + remote_output_path + "\n" )


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
