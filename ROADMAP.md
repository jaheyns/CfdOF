# CfdOF: A Computational fluid dynamics (CFD) workbench for FreeCAD

The workbench serves as a front-end (GUI) for the popular OpenFOAM® CFD toolkit (www.openfoam.org, www.openfoam.com).

Disclaimer:
This offering is not approved or endorsed by OpenCFD Limited, producer and distributor of the OpenFOAM software via 
www.openfoam.com, and owner of the OPENFOAM® and OpenCFD® trademarks.

## Roadmap

The following are items for discussion or items for which existing merges / PR's have been done.

### General

* Add translations
    * See the guide here: https://wiki.freecadweb.org/Translating_an_external_workbench
    * Forum topic: https://forum.freecadweb.org/viewtopic.php?f=10&t=36413
* Visualisation of point locations. At various places a point is specified - e.g. an internal 
mesh point when snappyHexMesh is selected in the meshing task panel, as well as
when specifying the scalar transport sources in the scalar transport panel. These should be 
displayed as a point on the model so that the user has feedback on their location. 
* Logging - some of the more technical/diagnostic output that is printed to the report view 
could instead be directed to the log, so that the report view is cleaner and more readable 
for the user. Generally improve the logging and messages that are printed there.
(see FreeCAD.Console.PrintLog/PrintMessage/PrintWarning/PrintError.)
* Test and provide more elegant errors or fallbacks for invalid/unexpected/unusual sequences of actions,
e.g. (there are many more!):
    * Switching a case to/from incompressible and compressible and trying to write it without
    re-setting the material properties to a valid type
* Test and fix running under WSL on Windows
  
### Testing

* More 'demo' cases are needed, which are specified as macros and run during the testing runs
  * Multiphase case(s)
  * Cases with postprocessing
  * Buoyant case(s)
* Additional unit tests which also test the functionality of the task panels, are needed. Currently testing is only
  done based on macros. Somehow, interaction with the GUI itself needs to be simulated.

### Documentation

* Formal documentation should be added to FreeCAD Wiki.

### Future scheduled cleanup
* On release of FreeCAD v0.21, stop supporting FreeCAD <= 0.19
    * Remove metadata.txt
    * Remove legacy python 2 code and python2/3 switches
    * Switch repository in Addon manager to gitlab
    * Remove backward-compatible plot code in compat/
    * Update version requirement in package.xml and dependency checker
    

### Turbulence models / boundary conditions / physics (solvers)
* k-epsilon - DONE
* Spalart Allmaras - DONE
* Langtry's transition models for k-omega - DONE
* cyclic boundary conditions

### Mesh
* checkMesh capabilities - DONE
* Convert tetra mesh to polyhedra mesh using polyDualMesh - DONE
* ability to import meshes from other formats? (CGNS, .msh (fluent), others?) [TODO]
* adaptive mesh refinement [DONE]

### Cases
* ability to import / export existing OF cases / results [TODO]

### Internal
* Update src to use Python module hierarchy instead of flat package, will make reading / maintaining the code much easier [IN PROGRESS]
* Improve edge detection for meshing?
* Move parallel run option to GUI for ease of use [DISCUSS]
* Implement -parallel meshing for snappyHexMesh (and others if supported) [DONE]
