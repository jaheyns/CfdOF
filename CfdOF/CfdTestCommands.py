# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2024 Oliver Oxtoby <oliveroxtoby@gmail.com>             *
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

import os

import FreeCAD
import FreeCADGui
from CfdOF import CfdTools
from PySide import QtCore
import TestCfdOF
from TestCfdOF import runCfdUnitTests, updateReferenceFiles, cleanCfdUnitTests

from PySide.QtCore import QT_TRANSLATE_NOOP


class CommandCfdRunTests:

    def __init__(self):
        pass

    def GetResources(self):
        return {'MenuText': QT_TRANSLATE_NOOP("CfdOF_RunTests",
                                                     "Run CfdOF tests"),
                'ToolTip': QT_TRANSLATE_NOOP("CfdOF_RunTests",
                                                    "Run CfdOF tests")}

    def IsActive(self):
        return True

    def Activated(self):
        runCfdUnitTests()


class CommandCfdUpdateTestData:

    def __init__(self):
        pass

    def GetResources(self):
        return {'MenuText': QT_TRANSLATE_NOOP("CfdOF_UpdateTestData",
                                                     "Update test reference data"),
                'ToolTip': QT_TRANSLATE_NOOP("CfdOF_UpdateTestData",
                                                    "Use latest test run as new reference data for tests")}

    def IsActive(self):
        return True

    def Activated(self):
        updateReferenceFiles()


class CommandCfdCleanTests:

    def __init__(self):
        pass

    def GetResources(self):
        return {'MenuText': QT_TRANSLATE_NOOP("CfdOF_CleanTests",
                                                     "Clean CfdOF tests"),
                'ToolTip': QT_TRANSLATE_NOOP("CfdOF_CleanTests",
                                                    "Clean up temporary data created by CfdOF unit tests")}

    def IsActive(self):
        return True

    def Activated(self):
        cleanCfdUnitTests()
