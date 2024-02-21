# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2017 Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>          *
# *   Copyright (c) 2017 Johan Heyns (CSIR) <jheyns@csir.co.za>             *
# *   Copyright (c) 2017 Alfred Bogaers (CSIR) <abogaers@csir.co.za>        *
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
                with process.stdin:
                    # The CTRL+BREAK puts (some versions of?) PowerShell into Debug mode - exit that
                    process.stdin.write('q\n')
                    process.stdin.write('Y\n')


def processStdout():
    with process.stdout:
        try:
            for output in iter(process.stdout.readline, ''):
                sys.stdout.write(output)
                sys.stdout.flush()
        except UnicodeDecodeError:
            # Avoid falling over is some weird character is emitted
            pass


def processStderr():
    with process.stderr:
        try:
            for output in iter(process.stderr.readline, ''):
                sys.stderr.write(output)
                sys.stderr.flush()
        except UnicodeDecodeError:
            # Avoid falling over is some weird character is emitted
            pass


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
