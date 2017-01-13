
__title__ = "Classes for New CFD Physics model selection"
__author__ = ""
__url__ = "http://www.freecadweb.org"

import os.path

import FreeCAD
if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore, QtGui

import _CfdPhysics

def makeCfdPhysicsSelection(name="PhysicsModel"):
    obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython", name)
    #obj = FreeCAD.ActiveDocument.addObject("App::MaterialObjectPython", name)
    _CfdPhysics._CfdPhysicsModel(obj)

    if FreeCAD.GuiUp:
        from _ViewProviderPhysicsSelection import _ViewProviderPhysicsSelection
        _ViewProviderPhysicsSelection(obj.ViewObject)
    return obj

