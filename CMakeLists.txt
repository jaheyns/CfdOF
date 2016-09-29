
fc_copy_to_mod_path("Cfd" 

)

INSTALL(
    FILES
        # changes on the file list here needs to be made in App/CMakeLists.txt as well
        Init.py
        InitGui.py
        # OpenFOAM solver related
        CfdAnalysis.py
        CfdSolver.py
        CfdSolverFoam.py
        CfdTools.py
        CfdCaseWriterFoam.py
        CfdRunnableFoam.py
	CfdResult.py

        TaskPanelCfdSolverControl.ui
        _TaskPanelCfdSolverControl.py
        _ViewProviderCfdSolverFoam.py
        TaskPanelCfdResult.ui
        _TaskPanelCfdResult.py
        _ViewProviderCfdResult.py

        _CommandCfdAnalysis.py
        _CommandCfdSolverFoam.py
        _CommandCfdSolverControl.py
	_CommandCfdResult.py

        FoamCaseBuilder/BasicBuilder.py
        FoamCaseBuilder/__init__.py
        FoamCaseBuilder/utility.py
        FoamCaseBuilder/ThermalBuilder.py
        FoamCaseBuilder/FoamTemplateString.py
        FoamCaseBuilder/TestBuilder.py
        FoamCaseBuilder/Readme.md
        FoamCaseBuilder/Roadmap.md

    DESTINATION
        Mod/Cfd
)
