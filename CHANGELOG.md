# CfdOF: A Computational fluid dynamics (CFD) workbench for FreeCAD
Brought to you by the developers of the CfdOF FreeCAD OpenFOAM integration workbench.

## Release notes
## v1.16.0
* Support added for passive scalar transport solution
* Added support for Detached Eddy Simulation (DES, DDES and IDDES)
* Auto-detection of changes requiring re-writing the case or re-meshing, and prompts to do so when necessary

## v1.15.0
* Added dynamic mesh adaptation functionality
* Added Reporting functions functionality
* Added Reporting probes functionality
* Support for backwards Plot module compatibility
* Update ResidualPlot to generalised TimePlot

## v1.14.0
* Added support for LES models (WALE, Smagorinsky, kEqn-based)
* Changed turbulence intensity inputs to percentages to make things more user friendly / intuitive
* Added support for parallel meshing in gmsh
* Shifted ui templates and some controllers to Python module structure (folders) for better code organisation
* Refactor variable names and method names to meet Contribution Guidelines
* Minor bug fixes, fix broken import, allow dynamic updating of enumerations so old projects are still loadable by updated versions

### v1.13.7
* Small Windows bug fixes for default paths
* Other formatting, and naming bug cleanups

### v1.13.6
* Bug fixes to Paraview to check for Python support before running
* Update Paraview script to open to latest time step for steady as well as transient cases

### v1.13.5
* Added support for k-epsilon, Spalart Allmaras and k-omega SST Langtry Menter turbulence models
* Option to use implicit as well as explicit edge / feature detection in SnappyHexMesh
* Various bug fixes to GUI to stop rerunning operations while meshing is in progress
* Added OpenFOAM Check Mesh capability
* Added ability to convert meshes to dual meshes (only for use with gmsh tetrahedral mesher)
* Added tooltips for some GUI components
* Added to Paraview python script to open to latest time step for solved models.  

_Last updated 06/04/2022_