# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2017 - Oliver Oxtoby (CSIR) <ooxtoby@csir.co.za>        *
# *   Copyright (c) 2017 - Alfred Bogaers (CSIR) <abogaers@csir.co.za>      *
# *   Copyright (c) 2017 - Johan Heyns (CSIR) <jheyns@csir.co.za>           *
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

__title__ = "Classes to create zones"
__author__ = ""
__url__ = "http://www.freecadweb.org"

import os.path

import FreeCAD
if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore, QtGui

import _CfdZone
import Part


def makeCfdPorousZone(name='PorousZone'):
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", name)
    _CfdZone._CfdZone(obj)

    if FreeCAD.GuiUp:
        from _ViewProviderCfdZone import _ViewProviderCfdZone
        _ViewProviderCfdZone(obj.ViewObject)
    
    return obj


def makeCfdInitialisationZone(name='InitialisationZone'):
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", name)
    _CfdZone._CfdZone(obj)

    if FreeCAD.GuiUp:
        from _ViewProviderCfdZone import _ViewProviderCfdZone
        _ViewProviderCfdZone(obj.ViewObject)

    return obj
