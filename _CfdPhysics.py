
__title__ = "CFDPhysicsModel"
__author__ = ""
__url__ = "http://www.freecadweb.org"



class _CfdPhysicsModel:
    "The CFD Physics Model"
    def __init__(self, obj):
        obj.addProperty("App::PropertyPythonObject","PhysicsModel")
        #Defualt settings
        #obj.PhysicsModel = {"Time": "None","Flow":"None","Turbulence":"None","Thermal":"None","TurbulenceModel":"None"}
        obj.PhysicsModel = {"Time": "Steady","Flow":"Incompressible","Turbulence":"Laminar","Thermal":None,"TurbulenceModel":None}
        obj.Proxy = self
        self.Type = "PhysicsModel"

    def execute(self, obj):
        return
