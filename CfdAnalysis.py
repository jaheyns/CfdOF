# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2013-2015 - Juergen Riegel <FreeCAD@juergen-riegel.net> *
# *   Copyright (c) 2017 - Oliver Oxtoby <ooxtoby@csir.co.za>               *
# *   Copyright (c) 2017 - Johan Heyns <jheyns@csir.co.za>                  *
# *   Copyright (c) 2017 - Alfred Bogaers <abogaers@csir.co.za>             *
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

import FreeCAD

__title__ = "CFD Analysis creation"
__author__ = "Qingfeng Xia"
__url__ = "http://www.freecadweb.org"


def makeCfdAnalysis(name):
    """ makeCfdAnalysis(name): makes a Cfd Analysis group object """
    obj = FreeCAD.ActiveDocument.addObject("Fem::FemAnalysisPython", name)
    if FreeCAD.GuiUp:
        from _ViewProviderCfdAnalysis import _ViewProviderCfdAnalysis
        _ViewProviderCfdAnalysis(obj.ViewObject)
    return obj
