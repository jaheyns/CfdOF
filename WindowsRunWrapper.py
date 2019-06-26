# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2017 Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>          *
# *   Copyright (c) 2017 Johan Heyns (CSIR) <jheyns@csir.co.za>             *
# *   Copyright (c) 2017 Alfred Bogaers (CSIR) <abogaers@csir.co.za>        *
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
import sys
import threading
import signal
import subprocess


def processStdin():
    with sys.stdin:
        for line in iter(sys.stdin.readline, ''):
            if line.rstrip() == "terminate":
                print("Wrapper process received terminate command")
                process.send_signal(signal.CTRL_BREAK_EVENT)


def processStdout():
    with process.stdout:
        for output in iter(process.stdout.readline, ''):
            sys.stdout.write(output)
            sys.stdout.flush()


def processStderr():
    with process.stderr:
        for output in iter(process.stderr.readline, ''):
            sys.stderr.write(output)
            sys.stdout.flush()


# Run program, return its exit code, while awaiting quit instruction on stdin pipe
argv = sys.argv
process = subprocess.Popen(argv[1:],
                           # Although we don't access stdin of subprocess, without stdin=PIPE,
                           # delivery to our (the parent's) stdin from outside seems very unreliable
                           stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                           universal_newlines=True)
# Start threads to await input/output.
t1 = threading.Thread(target=processStdin)
t1.daemon = True
t1.start()
t2 = threading.Thread(target=processStdout)
t2.daemon = True
t2.start()
t3 = threading.Thread(target=processStderr)
t3.daemon = True
t3.start()
process.wait()
sys.exit(process.returncode)
