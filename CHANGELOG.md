# CfdOF Release notes

## v1.17.0
* Significant performance improvement when writing triangulated surfaces
* Internal directory structure reorganisation
* Added regression tests covering multiphase, dynamic mesh, and force reporting functions

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

### v1.13.0
* Added support for k-omega SST Langtry Menter turbulence model
* Option to use implicit as well as explicit edge / feature detection in SnappyHexMesh
* Added OpenFOAM Check Mesh capability
* Added ability to convert meshes to dual meshes (only for use with gmsh tetrahedral mesher)
* Added to Paraview python script to open to latest time step for solved models.  

### v1.12.0
* Added support for k-epsilon and Spalart Allmaras turbulence models
