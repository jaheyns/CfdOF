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


class CommandCfdReloadWorkbench:

    def __init__(self):
        pass

    def GetResources(self):
        return {'MenuText': QtCore.QT_TRANSLATE_NOOP("Cfd_ReloadWorkbench",
                                                     "Reload CfdOF workbench"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Cfd_ReloadWorkbench",
                                                    "Reload source files from disk")}

    def IsActive(self):
        return True

    def Activated(self):
        CfdTools.reloadWorkbench()

