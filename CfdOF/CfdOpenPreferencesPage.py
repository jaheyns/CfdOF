# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileNotice: Part of the CfdOF addon.

################################################################################
#                                                                              #
#   Copyright (c) 2024 hasecilu <hasecilu@tuta.io>                             #
#                                                                              #
#   This program is free software; you can redistribute it and/or              #
#   modify it under the terms of the GNU Lesser General Public                 #
#   License as published by the Free Software Foundation; either               #
#   version 3 of the License, or (at your option) any later version.           #
#                                                                              #
#   This program is distributed in the hope that it will be useful,            #
#   but WITHOUT ANY WARRANTY; without even the implied warranty of             #
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.                       #
#                                                                              #
#   See the GNU Lesser General Public License for more details.                #
#                                                                              #
#   You should have received a copy of the GNU Lesser General Public License   #
#   along with this program; if not, write to the Free Software Foundation,    #
#   Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.        #
#                                                                              #
################################################################################

import FreeCADGui

from PySide.QtCore import QT_TRANSLATE_NOOP


class CommandCfdOpenPreferencesPage:

    def __init__(self):
        pass

    def GetResources(self):
        return {'MenuText': QT_TRANSLATE_NOOP("CfdOF_OpenPreferences",
                                                "Open preferences"),
                'ToolTip': QT_TRANSLATE_NOOP("CfdOF_OpenPreferences",
                                                "Opens the CfdOF preferences page")}
    def IsActive(self):
        return True

    def Activated(self):
        FreeCADGui.showPreferences("CfdOF")
