# A computional fluid dynamics (CFD) module for FreeCAD

by Qingfeng Xia

## LGPL license as FreeCAD

Use only with FreeCAD version > 0.17
Currently, only OpenFOAM (official 3.0 +) solver is implemented, tested on Ubuntu 16.04

This module aims to accelerate CFD case build up. Limited by the long solving time and mesh quality sensitivity of CFD problem, this module will not as good as FEM module. For engineering application, please seek support from other commercial CFD software.


## Features and limitation

![FreeCAD CFDworkbench screenshot](https://github.com/qingfengxia/qingfengxia.github.io/blob/master/images/FreeCAD_CFDworkbench_screenshot.png)

### Highlight for this initial commit:

1. Python code to run a basic laminar flow simulation is added into CfdWorkbench
2. An independent python module, FoamCaseBuilder (LGPL), can work with and without FreeCAD to build up case for OpenFOAM
3. A general FemSolverControlTaskPanel is proposed for any FemSolver.

### Limitation:

1. only laminar flow with dedicate solver and boundary setup can converge, and I suspect the the current meshing tool, netgen is not ideal for CFD, which needs very thin layer near wall. Please download my 2 test file to evaluate for this stage.
2. result can only be viewed in paraview. but possible to export result to VTK format then load back to FreeCAD. (it is implemented in Oct 2016)


### Platform support status
- install on Linux:
        Ubuntu 16.04 as a baseline implementation

- install on Windows 10 with Bash on Windows support:
        Official OpenFOAM  (Ubuntu deb) can be installed and run on windows via Bash on Windows,
        but it is tricky to run windows python script to call the command with python via subprocess module

- install on MAC (not tested):
        As a POSIX system, it is possible to run OpenFOAM and this moduel, assuming openfoam/etc/bashrc has been sourced for bash
      
=============================================
  
## Installation guide

### Prerequisites OpenFOAM related software

- OpenFOAM (3.0+)  `sudo apt-get install openfoam` once repo is added/imported

> see more OpenFOAM official installation guide

- PyFoam (0.6.6+) `sudo pip install PyFoam`

- gnuplot.py/gnuplot-py
 
optional;

- paraFoam (paraview for Openfoam, usually installed with OpenFoam)
- salome for mesihng

Debian/Ubuntu: see more details of Prerequisites installation in *Readme.md* in *FoamCaseBuilder* folder

RHEL/SL/Centos/Fedora: Installation tutorial/guide is welcomed from testers

### install freecad-daily
After Oct 2016, Cfd boundary condition C++ code (FemConstraintFluidBoundary) has been merged into official master
        
### install Cfd workbemch
from github using
`git clone https://github.com/qingfengxia/Cfd.git`
        
symbolic link or copy the folder into `<freecad installation folder>/Mod`, 
e.g, on POSIX system: 

`sudo ln -s (path_to_CFD)  (path_to_freecad)/Mod`
        

ALTERNATIVELY, use FreeCAD-Addon-Installer macro from <https://github.com/FreeCAD/FreeCAD-addons>

========================================

## testing

to-be-update later
[test procedure on freecad forum](http://forum.freecadweb.org/viewtopic.php?f=18&t=17322)


========================================

## Roadmap

### see external [Roadmap.md](./Roadmap.md)


=======================================

## How to contribute this module

You can fork this module to add new CFD solver or fix bugs for this OpenFOAM solver.

There is a ebook "Module developer's guide on FreeCAD source code", there are two chapters describing how Fem and Cfd modules are designed and implemented.

<https://github.com/qingfengxia/FreeCAD_Mod_Dev_Guide.git> where updated PDF could be found on this git repo

This is an outdated version for early preview:
<https://www.iesensor.com/download/FreeCAD_Mod_Dev_Guide__20160920.pdf>

## Collaboration strategy

Cfd is still under testing and dev, it will not be ready to be included into official in the next 6 m.

Currently route I can imagine:
CFD workbench new developers fork official FreeCAD and my Cfd githttps://github.com/qingfengxia/Cfd.git.

Cfd workbench depends on Fem for meshing and boundary(FemConstraint) and post-processing, most of them are coded in C++ so it is hard to split from Fem. If you need add feature on above, you branch FreeCAD official, not mime (but do let me know, pull request will only accepted if it is fully discussed on forum and reviewed by other dev like Bernd, me). see my ebook on how to pull request. Any other cfd python code, do pull request me (my Cfd.git) e.g. I developed vtk mesh and result import and export feature, git directly to official Fem workbench.

User can install freecad-daily, and git update/install Cfd.git so all got updated code without pain for installation.


