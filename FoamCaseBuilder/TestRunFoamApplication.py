#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2016 - Qingfeng Xia <qingfeng.xia()eng.ox.ac.uk> *
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   This program is distributed in the hope that it will be useful,       *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Library General Public License for more details.                  *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with this program; if not, write to the Free Software   *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************


from __future__ import print_function
import platform
import subprocess
import os
import os.path

from utility import *
from utility import _fromWindowsPath, _toWindowsPath
from utility import _FOAM_SETTINGS, _detectFoamDir, _detectFoamVersion

def test_bash_QProcess():
    from PyQt4 import QtCore
    process = QtCore.QProcess()
    process.setProcessChannelMode(QtCore.QProcess.MergedChannels)
    #process.finished.connect()
    #QProcess works wtih `bash -l -c` but not `bash -i -c`
    #process.start('bash', ['-l', '-c', 'echo $WM_PROJECT_DIR'])  # work if start in gnome-terminal
    #~/.bashrc is not recognized, need a full path to the etc file
    process.start('bash', ['-c', '"source ~/.bashrc && echo $WM_PROJECT_DIR"'])  #
    print('Test in QProcess')
    if process.waitForFinished():
        print(process.readAll())
    print('End of Test in QProcess')


def runFoamCommand(cmd):
    """ run OpenFOAM command via bash with OpenFOAM setup sourced into ~/.bashrc
    wait until finish, caller is not interested on output but whether succeeded
    source foam_dir/etc/bashrc before run foam related program
    `shell=True` does not work if freeCAD is not started in shell terminal
    Bash on Ubuntu on Windows, may need case path translation done in Builder
    """

    if isinstance(cmd, list):
        _cmd = _translateFoamCasePath(cmd)  # do not modify input parameter, it may be used outside somewhere
        #cmd = ' '.join(cmd)
    else:
        print("Warning: runFoamCommand() command and options must be specified in a list")

    cmdline = ' '.join(_cmd)
    print("Run command: ", cmdline)

    # this is the method works for both started in terminal and GUI launcher
    env_setup_script = "source {}/etc/bashrc".format(getFoamDir())
    #env_setup_script = "source ~/.bashrc"
    cmdline_1 = ['bash', '-c', ' '.join([env_setup_script, '&&'] + _cmd)]
    #cmdline = """bash -i -c  '{} && {}' """.format(env_setup_script, ' '.join(_cmd))
    #cmdline_1 = """bash -c ' {} && {}'""".format(env_setup_script, cmdline)
    print("Run command_1: ", cmdline_1)  # get correct command line, correct in terminal, but error in python
    out = subprocess.check_output(cmdline_1, stderr=subprocess.PIPE)

    # bug:  FreeCAD exit due to runFoamCommand() is called immediately after another  runFoamCommand() using `bash -i`
    # '-l' means '--login' works in terminal, while  '-i' means '--interactive' works from unity GUI launcher
    #out = subprocess.check_output(['bash', '-l', '-c', cmdline], stderr=subprocess.PIPE)
    if _debug: print(out)

    """
    # method3: error even at the first runFoamCommand(), running from terminal
    process = subprocess.Popen(['bash', '-i', '-c', cmdline], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    stdout, stderr = process.communicate()
    exitCode = process.returncode

    if _debug:
        print(stdout)

    if (exitCode != 0):
        if _debug:
            print(stderr)
        #else:  # should allow runFoamCommand to fail
            #raise SystemError("Error in foamRunCommand:".format(cmdline), exitCode)
    return exitCode
    """

'''
source foam_dir/etc/bashrc before run foam related program
`shell=True` does not work if freeCAD is not started in shell terminal
    
>python3  subprocess.check_output"
b'/opt/openfoam4\n'
>Exit code: 1
>python2  subprocess.check_output"
/opt/openfoam4
'''

def test_runBashCommand(cmd):
    #leading and trailing space in case path quote " path " will cause error
    #cmd = ["icoFoam", '-help']
    #cmdline = """bash -i -c '{}' """.format(' '.join(cmd))
    cmdline = ' '.join(cmd)
    print(cmdline)
    out = subprocess.check_output(['bash', '-i', '-c', cmdline], stderr=subprocess.PIPE)
    print(out)

#test_runCommand1() #fine in freecad without in console
#foam_dir = subprocess.check_output(['bash', '--rcfile', '~/.bashrc' '-c', ' echo $WM_PROJECT_DIR'], stderr=subprocess.PIPE)

print("test on platform", platform.system())
print("Foam dir and version detectoin")
print(_FOAM_SETTINGS)

if  platform.system() == 'Windows':  # ubuntu on windows 10
    #cmdline = ['bash', '-i', '-c', 'source ~/.bashrc && echo $WM_PROJECT_DIR']
    #print(cmdline)
    #foam_dir = subprocess.check_output('bash -c "source ~/.bashrc && echo test $WM_PROJECT_DIR"', stderr=subprocess.PIPE)  # error
    case = 'D:\\'
    output_file = case + os.path.sep + "output.txt"
    output_file_wsl = _fromWindowsPath(output_file)
    print("test of path translation")
    print("original win path:", output_file)
    print("to WSL path:", _fromWindowsPath(output_file))
    print("translated back to win path:", _toWindowsPath(output_file_wsl))
    
    cmdline = 'transformPoints -case "D:\TestCase" -scale "(1 1 1)"'
    print("translation of cmdline:", cmdline)

    if True:
        #cmd = 'echo $HOME'  # working, but user export var is not working like WM_PROJECT_DIR
        cmd = 'export WM_PROJECT_DIR=/opt/openfoam4 && echo $WM_PROJECT_DIR'  # not working
        #ret = subprocess.call('bash -c "source ~/.bashrc && {} > {}"'.format(cmd, output_file_wsl))  # no error,  no output
        
        # by `bash script.sh`, export is supported, but "source bashrc is still not working"
        cmd = 'source "$HOME/.bashrc" && echo $WM_PROJECT_DIR'  # not working
        foam_script_file = case + os.path.sep + "temp_foam_script.sh"
        with open(foam_script_file, 'w') as wf:  # existent file will be erased
            wf.write('{} > "{}"'.format(cmd, output_file_wsl))  # single line to avoid end of line error
        ret = subprocess.call('bash "{}"'.format(_fromWindowsPath(foam_script_file)))  # no error,  no output
        #bash --init-file ~/.bashrc -c declare -x WM_PROJECT_DIR=/opt/openfoam4 && echo $WM_PROJECT_DIR
        #cmd: bash -i  -c "source /home/qingfeng/.bashrc && echo test$WM_PROJECT_DIR"

        #print("type of return value", type(ret))
        with open(output_file) as f:
            result = f.read().strip()
        #assert 'test' == result
        print("`{}` exit with code: {}, and result is `{}`".format(cmd, ret, result))
    else:
        cmd = ['echo', "$HOME"]  # $WM_PROJECT_DIR
        print('runFoamCommandOnWSL()')
        foam_dir = runFoamCommandOnWSL(None, cmd, output_file)
        print(foam_dir)
else:
    test_bash_QProcess()
    #`bash -l -c` will not work with python subprocess.check_output
    foam_dir = subprocess.check_output(['bash', '-i', '-c', 'echo $WM_PROJECT_DIR'], stderr=subprocess.PIPE)
    print(foam_dir)
    #print(stderr)

    case_path = '/home/qingfeng/Documents/TestCase'
    if os.path.exists(case_path):
        cmd = ['transformPoints','-case', '"' + case_path + '"', '-scale', '"(1 1 1)"']
        #test_runBashCommand(cmd) # error
        cmd1 = ['transformPoints', '-scale', '"(1 1 1)"']
        runFoamApplication(case_path, cmd1)
    runFoamApplication(None, 'simpleFoam -help')

