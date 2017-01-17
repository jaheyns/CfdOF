
__title__ = "Classes to initialise internal flow field"
__author__ = ""
__url__ = "http://www.freecadweb.org"

import os.path

import FreeCAD
if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore, QtGui

import _CfdInitialVariables

def makeCfdInitialFlowField(name="InitializeInternalVariables"):
    obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython", name)
    _CfdInitialVariables._CfdInitialVariables(obj)


    if FreeCAD.GuiUp:
        from _ViewProviderCfdInitialseInternalFlowField import _ViewProviderCfdInitialseInternalFlowField
        _ViewProviderCfdInitialseInternalFlowField(obj.ViewObject)
    return obj

