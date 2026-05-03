# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: © 2025 muez abdalla <muezabdalla777@gmail.com>
# SPDX-FileNotice: Part of the CfdOF addon.

################################################################################
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

from pivy import coin

def initPrevPoint(node, move_node, rad, r, g, b, x=0, y=0, z=0):
    col = coin.SoBaseColor()
    col.rgb = (r, g, b)
    sphere = coin.SoSphere()
    sphere.radius = rad
    move_node.translation.setValue([x, y, z])
    node.addChild(col)
    node.addChild(move_node)
    node.addChild(sphere)
    FreeCADGui.ActiveDocument.ActiveView.getSceneGraph().addChild(node)

