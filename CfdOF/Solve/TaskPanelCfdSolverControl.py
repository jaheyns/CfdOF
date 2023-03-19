# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2016 - Qingfeng Xia <qingfeng.xia()eng.ox.ac.uk>        *
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

import FreeCAD
from CfdOF import CfdTools
import os
import os.path
import time
from CfdOF.CfdConsoleProcess import CfdConsoleProcess
if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore
    from PySide import QtGui
    from PySide.QtCore import Qt
    from PySide.QtGui import QApplication

# ********************************************************************************************************
# LinuxGuy123's Notes
#
# TODOs (there are some in the code as well)
#
# -add filename to the output path.  (addFilenameToOutput) For both local and remote useRemoteProcessing.
# It is already saved in prefs, for both local and remote hosts. You can get it with
# FreeCAD.ParamGet(prefs).GetBool("AddFilenameToOutput",0)
#
# -check on the number of cores that are being asked for and used by OpenFOAM
#
# -makeRunCommand is using the local OF bash command to build the remote run command.  It works but it isn't correct.
# The remote run is not calling the source command to set up OF usage.  It is relying on the bash shell  on the remote host
# to do that, through bashrc and OF working directly from the command line.
#
# -enable and disable buttons appropriately when running and when done
#
# global vars are used for stuff that should be passed via the solver object.
#
# -edit case doesn't copy the case back to the server after the edit is done.
#
# -remote solving has not been tested in macros
#
#- presently does not set the number of threads that the solver uses properly.  Must be done manually.

class TaskPanelCfdSolverControl:
    def __init__(self, solver_runner_obj):
        ui_path = os.path.join(CfdTools.getModulePath(), 'Gui', "TaskPanelCfdSolverControl.ui")
        self.form = FreeCADGui.PySideUic.loadUi(ui_path)

        self.analysis_object = CfdTools.getActiveAnalysis()

        self.solver_runner = solver_runner_obj
        self.solver_object = solver_runner_obj.solver

        # update UI
        self.console_message = ''

        self.solver_object.Proxy.solver_process = CfdConsoleProcess(finished_hook=self.solverFinished,
                                                                    stdout_hook=self.gotOutputLines,
                                                                    stderr_hook=self.gotErrorLines)
        self.Timer = QtCore.QTimer()
        self.Timer.setInterval(1000)
        self.Timer.timeout.connect(self.updateText)

        self.form.terminateSolver.clicked.connect(self.killSolverProcess)
        self.form.terminateSolver.setEnabled(False)

        self.working_dir = CfdTools.getOutputPath(self.analysis_object)

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
        #self.mesh_processes = 0
        #self.mesh_threads = 0
        #self.foam_processes = 0
        #self.foam_threads = 0
        self.foam_dir = ""
        self.output_path = ""
        #self.gmsh_path = ""
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

        self.updateUI()

        # Connect Signals and Slots
        # set up the profiles combo box connection
        self.form.cb_profile.currentIndexChanged.connect(self.profileChanged)
        self.form.pb_write_inp.clicked.connect(self.write_input_file_handler)
        self.form.pb_edit_inp.clicked.connect(self.editSolverInputFile)
        self.form.pb_run_solver.clicked.connect(self.runSolverProcess)
        self.form.pb_paraview.clicked.connect(self.openParaview)

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
                  # set the vars to the remote host parameters
                  # most of these aren't used, at least not in this page
                  hostPrefs = self.host_prefs_location
                  self.hostname = FreeCAD.ParamGet(hostPrefs).GetString("Hostname", "")
                  self.username = FreeCAD.ParamGet(hostPrefs).GetString("Username", "")
                  #self.mesh_processes = FreeCAD.ParamGet(hostPrefs).GetInt("MeshProcesses")
                  #self.mesh_threads = FreeCAD.ParamGet(hostPrefs).GetInt("MeshThreads")
                  #self.foam_processes = FreeCAD.ParamGet(hostPrefs).GetInt("FoamProcesses")
                  #self.foam_threads = FreeCAD.ParamGet(hostPrefs).GetInt("FoamThreads")
                  self.foam_dir = FreeCAD.ParamGet(hostPrefs).GetString("FoamDir", "")
                  self.output_path = FreeCAD.ParamGet(hostPrefs).GetString("OutputPath","")

                  # these are used
                  self.add_filename_to_output = FreeCAD.ParamGet(hostPrefs).GetBool("AddFilenameToOutput")
                  self.copy_back = FreeCAD.ParamGet(hostPrefs).GetBool("CopyBack")
                  self.delete_remote_results = FreeCAD.ParamGet(hostPrefs).GetBool("DeleteRemoteResults")


                  # now set the control values
                  # leaving these in in case we pass parameters like these to the solver
                  # object some day.

                  #self.mesh_obj.NumberOfProcesses = self.mesh_processes
                  #self.mesh_obj.NumberOfThreads = self.mesh_threads

                  #TODO: fix these, if we need to.
                  # Leaving these in in case we add controls to set these someday
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
            if self.profile_name == 'local':
                self.form.pb_write_inp.enabled = True
            else:
                pass

    def updateUI(self):
        solverDirectory = os.path.join(self.working_dir, self.solver_object.InputCaseName)

        if self.profile_name == 'local':
            self.form.pb_edit_inp.setEnabled(os.path.exists(solverDirectory))

        # TODO: enable local editing of the solver case
        else:
            self.form.pb_edit_inp.setEnabled(False)

        # TODO: Paraview is enabled even though the solver hasn't been run yet.  Fix this ?
        self.form.pb_paraview.setEnabled(os.path.exists(os.path.join(solverDirectory, "pv.foam")))
        self.form.pb_run_solver.setEnabled(os.path.exists(os.path.join(solverDirectory, "Allrun")))

    def consoleMessage(self, message="", colour_type=None):
        self.console_message += \
            '<font color="{}">{:4.1f}:</font> '.format(CfdTools.getColour('Logging'), time.time() - self.Start)
        if colour_type:
            self.console_message += '<font color="{}">{}</font><br>'.format(CfdTools.getColour(colour_type), message)
        else:
            self.console_message += message + '<br>'
        self.form.textEdit_Output.setText(self.console_message)
        self.form.textEdit_Output.moveCursor(QtGui.QTextCursor.End)

    def updateText(self):
        if self.solver_object.Proxy.solver_process.state() == QtCore.QProcess.ProcessState.Running:
            self.form.l_time.setText('Time: ' + CfdTools.formatTimer(time.time() - self.Start))

    def getStandardButtons(self):
        return int(QtGui.QDialogButtonBox.Close)

    def reject(self):
        FreeCADGui.ActiveDocument.resetEdit()

    def closing(self):
        # We call this from unsetEdit to ensure cleanup
        self.solver_object.Proxy.solver_process.terminate()
        self.solver_object.Proxy.solver_process.waitForFinished()
        self.Timer.stop()

    def write_input_file_handler(self):
        self.Start = time.time()
        FreeCADGui.doCommand("from CfdOF.Solve import CfdCaseWriterFoam")
        from CfdOF.Solve import CfdCaseWriterFoam
        import importlib
        importlib.reload(CfdCaseWriterFoam)
        if self.check_prerequisites_helper():
            self.consoleMessage("Case writer called")
            self.form.pb_paraview.setEnabled(False)
            self.form.pb_edit_inp.setEnabled(False)
            self.form.pb_run_solver.setEnabled(False)            
            QApplication.setOverrideCursor(Qt.WaitCursor)
            try:
               FreeCADGui.doCommand("FreeCAD.ActiveDocument." + self.solver_object.Name + ".Proxy.case_writer = "
                                     "CfdCaseWriterFoam.CfdCaseWriterFoam(FreeCAD.ActiveDocument." +
                                     self.solver_runner.analysis.Name + ")")
               FreeCADGui.doCommand("writer = FreeCAD.ActiveDocument." +
                                     self.solver_object.Name + ".Proxy.case_writer")
               writer = self.solver_object.Proxy.case_writer
               writer.progressCallback = self.consoleMessage
               FreeCADGui.doCommand("writer.writeCase('" + self.profile_name +"')")

            except Exception as e:
               self.consoleMessage("Error writing case:", 'Error')
               self.consoleMessage(type(e).__name__ + ": " + str(e), 'Error')
               self.consoleMessage("Write case setup file failed", 'Error')
               raise
            else:
                    self.analysis_object.NeedsCaseRewrite = False
            finally:
                    QApplication.restoreOverrideCursor()
            self.updateUI()
            self.form.pb_run_solver.setEnabled(True)

        else:
            self.consoleMessage("Case check failed", 'Error')



    def check_prerequisites_helper(self):
        self.consoleMessage("Checking dependencies...")

        message = self.solver_runner.check_prerequisites()
        if message != "":
            self.consoleMessage(message, 'Error')
            return False
        return True

    def editSolverInputFile(self):
        case_path = os.path.join(self.working_dir, self.solver_object.InputCaseName)
        self.consoleMessage("Please edit the case input files externally at: {}\n".format(case_path))
        CfdTools.openFileManager(case_path)

    def runSolverProcess(self, profileName):
        self.Start = time.time()

        # Check for changes that require remesh
        # TODO: This will not run the mesher on a remote host.  Fix this ?
        if FreeCAD.GuiUp and (
                self.analysis_object.NeedsMeshRewrite or 
                self.analysis_object.NeedsCaseRewrite or 
                self.analysis_object.NeedsMeshRerun):
            
            if self.analysis_object.NeedsCaseRewrite:
                if self.analysis_object.NeedsMeshRewrite or self.analysis_object.NeedsMeshRerun:
                    text = "The case may need to be re-meshed and the case setup re-written based on changes " + \
                           "you have made to the model.\n\nRe-mesh and re-write case setup first?"
                else:
                    text = "The case setup may need to be re-written based on changes " + \
                           "you have made to the model.\n\nRe-write case setup first?"
            else:
                if self.analysis_object.NeedsMeshRewrite or self.analysis_object.NeedsMeshRerun:
                    text = "The case may need to be re-meshed based on changes " + \
                           "you have made to the model.\n\nRe-mesh case first?"
                
            if QtGui.QMessageBox.question(
                    None, "CfdOF Workbench", text, defaultButton=QtGui.QMessageBox.Yes) == QtGui.QMessageBox.Yes:
                self.Start = time.time()
                
                if self.analysis_object.NeedsMeshRewrite or self.analysis_object.NeedsMeshRerun:
                    from CfdOF.Mesh import CfdMeshTools
                    mesh_obj = CfdTools.getMeshObject(self.analysis_object)  #TODO: This won't work with remote hosts.  Need to pass the host name into the mesh object
                    cart_mesh = CfdMeshTools.CfdMeshTools(mesh_obj)
                    cart_mesh.progressCallback = self.consoleMessage
                    if self.analysis_object.NeedsMeshRewrite:
                        #Write mesh
                        cart_mesh.writeMesh()
                        self.analysis_object.NeedsMeshRewrite = False
                        self.analysis_object.NeedsMeshRerun = True

                if self.analysis_object.NeedsCaseRewrite:
                    self.write_input_file_handler()

                if self.analysis_object.NeedsMeshRerun:
                    # Run mesher
                    self.solver_object.Proxy.solver_process = CfdConsoleProcess(
                        finished_hook=self.mesherFinished,
                        stdout_hook=self.gotOutputLines,
                        stderr_hook=self.gotErrorLines)

                    cart_mesh.error = False
                    cmd = CfdTools.makeRunCommand('./Allmesh', cart_mesh.meshCaseDir, source_env=False)
                    env_vars = CfdTools.getRunEnvironment()

                    # run locally
                    if profileName == 'local':
                        self.solver_object.Proxy.solver_process.start(cmd, env_vars=env_vars)
                        if self.solver_object.Proxy.solver_process.waitForStarted():
                            # Setting solve button to inactive to ensure that two instances of the same simulation aren't started
                            # simultaneously
                            self.form.pb_write_inp.setEnabled(False)
                            self.form.pb_run_solver.setEnabled(False)
                            self.form.terminateSolver.setEnabled(True)
                            self.consoleMessage("Mesher started ...")
                            return

                    # run remotely
                    # not implemented
                    else:
                        self.consoleMessage("Meshing from within the solver is not implemented for remote hosts.")
                        self.consoleMessage("Generate the mesh from the mesh object instead.")
                        return
                        """
                        remote_user = self.username
                        remote_hostname = self.hostname

                        # create the ssh connection command
                        # use ssh -t, not ssh -tt
                        ssh_prefix = 'ssh -t' + remote_user + '@' + remote_hostname + ' '

                        # Get the working directory for the mesh
                        working_dir = self.output_path
                        #TODO: add filename to the path if selected

                        # create the command to do the actual work
                        command = 'EOT \n'
                        command += 'cd ' + working_dir + '/meshCase \n'
                        command += './Allrun \n'
                        command += 'exit \n'
                        command += 'EOT \n'
                        command = ssh_prefix + ' << '  + command

                        cmd = CfdTools.makeRunCommand(command,None)
                    """

            #Mesh is ready to solve, so run it.
            else:
                self.Start = time.time()

        QApplication.setOverrideCursor(Qt.WaitCursor)
        FreeCADGui.doCommand("from CfdOF import CfdTools")
        FreeCADGui.doCommand("from CfdOF import CfdConsoleProcess")
        self.solver_object.Proxy.solver_runner = self.solver_runner
        FreeCADGui.doCommand("proxy = FreeCAD.ActiveDocument." + self.solver_object.Name + ".Proxy")
        # This is a workaround to emit code into macro without actually running it
        FreeCADGui.doCommand("proxy.running_from_macro = True")
        self.solver_object.Proxy.running_from_macro = False

        # if running on local host
        if self.profile_name == "local":
            # This must be kept in one doCommand because of the if statement
            FreeCADGui.doCommand(
                "if proxy.running_from_macro:\n" +
                "  analysis_object = FreeCAD.ActiveDocument." + self.analysis_object.Name + "\n" +
                "  solver_object = FreeCAD.ActiveDocument." + self.solver_object.Name + "\n" +
                "  working_dir = CfdTools.getOutputPath(analysis_object)\n" +
                "  case_name = solver_object.InputCaseName\n" +
                "  solver_directory = os.path.abspath(os.path.join(working_dir, case_name))\n" +
                "  from CfdOF.Solve.CfdRunnableFoam import CfdRunnableFoam\n" +
                "  solver_runner = CfdRunnableFoam.CfdRunnableFoam(analysis_object, solver_object)\n" +
                "  cmd = solver_runner.get_solver_cmd(solver_directory)\n" +
                "  env_vars = solver_runner.getRunEnvironment()\n" +
                "  solver_process = CfdConsoleProcess.CfdConsoleProcess(stdout_hook=solver_runner.process_output)\n" +
                "  solver_process.start(cmd,env_vars= env_vars)\n" +
                "  solver_process.waitForFinished()")

            working_dir = CfdTools.getOutputPath(self.analysis_object)
            case_name = self.solver_object.InputCaseName
            solver_directory = os.path.abspath(os.path.join(working_dir, case_name))
            cmd = self.solver_runner.get_solver_cmd(solver_directory)
            env_vars = self.solver_runner.getRunEnvironment()
            self.solver_object.Proxy.solver_process = CfdConsoleProcess(finished_hook=self.solverFinished,
                                                                           stdout_hook=self.gotOutputLines,
                                                                           stderr_hook=self.gotErrorLines)
            self.solver_object.Proxy.solver_process.start(cmd, env_vars=env_vars)

        # running remotely
        else:            

            # This must be kept in one doCommand because of the if statement
            # The only difference between this command and the local command is "  cmd = CfdTools.makeRunCommand('" + command + "',None)"
            # TODO: Test the macro code.
            FreeCADGui.doCommand(
                "if proxy.running_from_macro:\n" +
                "  analysis_object = FreeCAD.ActiveDocument." + self.analysis_object.Name + "\n" +
                "  solver_object = FreeCAD.ActiveDocument." + self.solver_object.Name + "\n" +
                "  working_dir = CfdTools.getOutputPath(analysis_object)\n" +
                "  case_name = solver_object.InputCaseName\n" +
                "  solver_directory = os.path.abspath(os.path.join(working_dir, case_name))\n" +
                "  from CfdOF.Solve.CfdRunnableFoam import CfdRunnableFoam\n" +
                "  solver_runner = CfdRunnableFoam.CfdRunnableFoam(analysis_object, solver_object)\n" +

                #  create the command to do the actual work
                #  was ssh -tt but then the shell wouldn't exit
                "  ssh_prefix = 'ssh -t ' + '" + self.username + "'+ '@' +'" + self.hostname + "'\n" +
                "  #command = 'EOT \\n' \n" +
                "  command = 'cd ' + '" + self.working_dir + "' + '/case \\n' \n" +
                "  command += './Allrun \\n' \n" +
                "  command += 'exit \\n' \n" +
                "  command += 'EOT' \n" +
                "  command = ssh_prefix + ' << '  + command + '\\n' \n" +
                "  print('doCommand command:' + command) \n" +
                "  cmd = CfdTools.makeRunCommand(command,None)\n" +           # was "  cmd = solver_runner.get_solver_cmd(solver_directory)\n" +
                "  print('doCommand cmd:')\n" +
                "  print(cmd)\n" +
                "  env_vars = solver_runner.getRunEnvironment()\n" +
                "  solver_process = CfdConsoleProcess.CfdConsoleProcess(stdout_hook=solver_runner.process_output)\n" +
                "  solver_process.start(cmd,env_vars= env_vars)\n" +
                "  solver_process.waitForFinished()")


            """
            # This was used for testing
            # create the command to do the actual work
            ssh_prefix = 'ssh -tt ' + self.username + '@' + self.hostname
            command = 'EOT \n'
            command += 'cd ' + self.working_dir + '/case \n'
            command += './Allrun \n'
            command += 'exit \n '
            command += 'EOT \n'
            command = ssh_prefix + ' << '  + command + ' \n'
            print("Code command:" + command)
            cmd = CfdTools.makeRunCommand(command,None)           # was cmd = solver_runner.get_solver_cmd(solver_directory)\n" +
            print("Code cmd:")
            print(cmd)
            """

            # create the command to do the actual work
            command = 'ssh -t ' + self.username + '@' + self.hostname   # was -tt
            command += '<< EOT \n'
            command += ' cd ' + self.working_dir + '/case \n'
            command += './Allrun \n'
            command += 'exit \n '
            command += 'EOT \n'
            print("Code command:" + command)

            #cmd = ['bash', '-c', command]
            #print("Code cmd:")
            #print(cmd)

            cmd = CfdTools.makeRunCommand(command,None)

            working_dir = CfdTools.getOutputPath(self.analysis_object)
            case_name = self.solver_object.InputCaseName
            solver_directory = os.path.abspath(os.path.join(working_dir, case_name))


            #cmd = self.solver_runner.get_solver_cmd(solver_directory)
            env_vars = self.solver_runner.getRunEnvironment()
            self.solver_object.Proxy.solver_process = CfdConsoleProcess(finished_hook=self.solverFinished,
                                                                               stdout_hook=self.gotOutputLines,
                                                                               stderr_hook=self.gotErrorLines)
            self.solver_object.Proxy.solver_process.start(cmd, env_vars=env_vars)

        if self.solver_object.Proxy.solver_process.waitForStarted():
            # Setting solve button to inactive to ensure that two instances of the same simulation aren't started
            # simultaneously
            self.form.pb_write_inp.setEnabled(False)
            self.form.pb_run_solver.setEnabled(False)
            self.form.terminateSolver.setEnabled(True)
            self.form.pb_paraview.setEnabled(True)
            self.consoleMessage("Solver started")
        else:
            self.consoleMessage("Error starting solver", 'Error')
        QApplication.restoreOverrideCursor()


    def killSolverProcess(self):
        self.consoleMessage("Solver manually stopped")
        self.solver_object.Proxy.solver_process.terminate()
        # TODO: kill the process on the server if we are running locally
        # Note: solverFinished will still be called

    def solverFinished(self, exit_code):
        if exit_code == 0:
            self.consoleMessage("Simulation finished")

            #check if there is work to do on the remote host
            if self.profile_name != 'local':
                # copy the solver case back to the workstation?
                # this code is also used in TaskPanelCfdMesh.py for copying the mesh case to the workstation
                if self.copy_back:
                    local_prefs = CfdTools.getPreferencesLocation()
                    profile_prefs = local_prefs +"/Hosts/" + self.profile_name

                    remote_user = FreeCAD.ParamGet(profile_prefs).GetString("Username", "")
                    remote_hostname = FreeCAD.ParamGet(profile_prefs).GetString("Hostname", "")
                    remote_output_path = FreeCAD.ParamGet(profile_prefs).GetString("OutputPath","")
                    local_output_path = FreeCAD.ParamGet(profile_prefs).GetString("OutputPath","")

                    # if we are deleting the solver and mesh case on the server
                    # if we delete the mesh case we'll need to remesh before running the solver

                    if self.delete_remote_results:
                        deleteStr = "--remove-source-files "
                    else:
                        deleteStr = ""

                    # rsync the solver case result on the server to the workstation's output directory
                    # Typical useage: rsync -r  --delete --remove-source-files me@david/tmp/case /tmp
                    # --remove-source-files removes the files that get transfered
                    # --delete removes files from the destination that didn't get transfered

                    try:
                        CfdTools.runFoamCommand("rsync -r --delete " + deleteStr +  remote_user + "@" + remote_hostname + ":" + remote_output_path + "/case " +  \
                                    local_output_path)
                    except Exception as e:
                        CfdTools.cfdMessage("Could not copy solver case back to local computer: " + str(e))
                        self.consoleMessage("Could not copy solver case back to local computer: " + str(e))

                    else:
                        CfdTools.cfdMessage("Copied solver case to " + local_output_path + "\n" )
                        self.consoleMessage("Copied solver case to " + local_output_path + "\n" )

                # the mesh case is still on the server
                # delete the mesh case result on the server ?
                # for now we'll leave it there
                if self.delete_remote_results:
                    pass

        else:
            self.consoleMessage("Simulation exited with error", 'Error')
        self.solver_runner.solverFinished()
        self.form.pb_write_inp.setEnabled(True)
        self.form.pb_run_solver.setEnabled(True)
        self.form.terminateSolver.setEnabled(False)

    def mesherFinished(self, exit_code):
        self.form.pb_write_inp.setEnabled(True)
        self.form.pb_run_solver.setEnabled(True)
        self.form.terminateSolver.setEnabled(False)
        if exit_code == 0:
            self.consoleMessage("Mesher finished successfully")
            self.analysis_object.NeedsMeshRerun = False
            self.runSolverProcess()
        else:
            self.consoleMessage("Mesher exited with error", 'Error')

    def gotOutputLines(self, lines):
        self.solver_runner.process_output(lines)

    def gotErrorLines(self, lines):
        print_err = self.solver_object.Proxy.solver_process.processErrorOutput(lines)
        if print_err is not None:
            self.consoleMessage(print_err, 'Error')

    def openParaview(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        case_path = os.path.abspath(os.path.join(self.working_dir, self.solver_object.InputCaseName))
        script_name = "pvScript.py"
        try:
            CfdTools.startParaview(case_path, script_name, self.consoleMessage)
        finally:
            QApplication.restoreOverrideCursor()
