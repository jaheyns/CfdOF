# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileNotice: Part of the CfdOF addon.

# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2023 Oliver Oxtoby <oliveroxtoby@gmail.com>             *
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

from PySide.QtCore import QT_TRANSLATE_NOOP

class CommandCfdReloadWorkbench:

    def __init__(self):
        pass

    def GetResources(self):
        return {'MenuText': QT_TRANSLATE_NOOP("CfdOF_ReloadWorkbench",
                                              "Reload CfdOF workbench"),
                'ToolTip': QT_TRANSLATE_NOOP("CfdOF_ReloadWorkbench",
                "Attempt to reload all CfdOF source files from disk. May break open documents!")}

    def IsActive(self):
        return True

    def Activated(self):
        CfdTools.reloadWorkbench()

