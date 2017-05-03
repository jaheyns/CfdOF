
__title__ = "CFDInitialVariables"
__author__ = ""
__url__ = "http://www.freecadweb.org"



class _CfdInitialVariables:
    """ The field initialisation object """
    def __init__(self, obj):
        obj.addProperty("App::PropertyPythonObject", "InitialVariables")
        # Default settings
        obj.InitialVariables = {"PotentialFoam": True,
                                "Ux": 0,
                                "Uy": 0,
                                "Uz": 0,
                                "P": 0,
                                "UseInletTurbulenceValues": False,
                                "Inlet": "",
                                "k": 0.01,
                                "omega": 1}
        obj.Proxy = self
        self.Type = "InitialVariables"

    def execute(self, obj):
        return
