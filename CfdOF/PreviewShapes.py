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

import FreeCAD
import math
from pivy import coin

def directionVectorToAxisAngle(orig_dir, desired_dir):
    """ convert from a 3-float vector that represent a direction to a rotation angle (in radian) around an axis"""

    # if the desired_dir is 0,0,0 return the orig_dir with 0 rotation
    if desired_dir == FreeCAD.Vector(0, 0, 0):
        return coin.SbVec3f(orig_dir[0], orig_dir[1], orig_dir[2]), 0
    desired_dir.normalize()
    # Calculate Angle (using dot product)
    cos_angle = orig_dir.dot(desired_dir)
    # Clamp value to [-1, 1] to avoid math domain errors due to floating point noise
    cos_angle = max(-1.0, min(1.0, cos_angle))
    angle_rad = math.acos(cos_angle)

    # Calculate Axis (using cross product)
    axis = orig_dir.cross(desired_dir)

    # Handle edge case: vectors are parallel (axis will be 0,0,0)
    if axis.Length < 1e-9:
        if angle_rad < 1e-9:
            # No rotation needed
            axis = FreeCAD.Vector(0, 0, 1)
            angle_rad = 0
        else:
            # 180 degree rotation (vectors opposite), axis is arbitrary perpendicular
            # Choose a vector not parallel to ref
            axis = orig_dir.cross(FreeCAD.Vector(1, 0, 0))
            if axis.Length < 1e-9:
                axis = orig_dir.cross(FreeCAD.Vector(0, 1, 0))
            angle_rad = 3.141592653589793 # 180 degrees
    else:
        axis.normalize()

    # convert the axis to a SbVec3f
    axis_vec = coin.SbVec3f(axis[0], axis[1], axis[2])
    return (axis_vec, angle_rad)

def getPrevPointSize(shape):
    """ return the estimated size of the preview point based on the mesh object"""
    size = 0.02*math.sqrt(shape.BoundBox.XLength**2 + shape.BoundBox.YLength**2 + shape.BoundBox.ZLength**2)
    return size

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

def initPrevArrow(node, transform_node, r,g,b):
    """ create an arrow with the input node and transform_node. can change the size, direction and position by changing the transform_node"""
    col = coin.SoBaseColor()
    col.rgb = (r, g, b)

    tail = coin.SoCylinder()
    tail.radius = 1/2
    tail.hieght = 2
    move_tail = coin.SoTransform()
    move_tail.translation.setValue(0, 1, 0)
    move_tail.rotation.setValue(coin.SbVec3f(0, 0, 1), 0)
    node_tail = coin.SoSeparator()
    node_tail.addChild(col)
    node_tail.addChild(move_tail)
    node_tail.addChild(tail)

    head = coin.SoCone()
    head.bottomRadius = 1
    head.height = 2
    move_head = coin.SoTransform()
    move_head.translation.setValue(0, 3, 0)
    move_head.rotation.setValue(coin.SbVec3f(0, 0, 1), 0)
    node_head = coin.SoSeparator()
    node_head.addChild(col)
    node_head.addChild(move_head)
    node_head.addChild(head)

    node.addChild(transform_node)
    node.addChild(node_tail)
    node.addChild(node_head)
    FreeCADGui.ActiveDocument.ActiveView.getSceneGraph().addChild(node)
