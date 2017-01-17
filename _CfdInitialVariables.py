
__title__ = "CFDInitialVariables"
__author__ = ""
__url__ = "http://www.freecadweb.org"



class _CfdInitialVariables:
    "The CFD Physics Model"
    def __init__(self, obj):
        obj.addProperty("App::PropertyPythonObject","InitialVariables")
        #Defualt settings
        obj.InitialVariables = {"PotentialFoam":True,
                                "Ux": "0 m/s",
                                "Uy":"0 m/s",
                                "Uz":"0 m/s",
                                "P":"0 kg*m/s^2"}
        obj.Proxy = self
        self.Type = "InitialVariables"

    def execute(self, obj):
        return
