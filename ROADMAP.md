# CfdOF: A Computational fluid dynamics (CFD) workbench for FreeCAD

The workbench serves as a front-end (GUI) for the popular OpenFOAM® CFD toolkit (www.openfoam.org, www.openfoam.com).

Disclaimer:
This offering is not approved or endorsed by OpenCFD Limited, producer and distributor of the OpenFOAM software via 
www.openfoam.com, and owner of the OPENFOAM® and OpenCFD® trademarks.

## Roadmap

The following are items for discussion or items for which existing merges / PR's have been done.

## New features
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

