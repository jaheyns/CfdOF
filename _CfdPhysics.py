
__title__ = "CFDPhysicsModel"
__author__ = ""
__url__ = "http://www.freecadweb.org"



class _CfdPhysicsModel:
    "The CFD Physics Model"
    def __init__(self, obj):
        obj.addProperty("App::PropertyPythonObject","PhysicsModel")
        # Default settings
        obj.PhysicsModel = {"Time": "Steady",
                            "Flow": "Incompressible",
                            "Turbulence": "Laminar",  # Inviscid, Laminar, RANS
                            "Thermal": None,
                            "TurbulenceModel": None}
        obj.Proxy = self
        self.Type = "PhysicsModel"

    def execute(self, obj):
        return
