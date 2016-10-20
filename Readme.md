#A computional fluid dynamics (CFD) module for FreeCAD

by Qingfeng Xia

## LGPL license as FreeCAD

Use only with FreeCAD version > 0.17
Currently, only OpenFOAM (official 3.0 +) solver is implemented, tested on Ubuntu 16.04

This module aims to accelerate CFD case build up. Limited by the long solving time and mesh quality sensitivity of CFD problem, this module will not as good as FEM module. For engineering application, please seek support from other commercial CFD software.

## FoamCaseBuilder

FoamCaseBuilder is an independent python module to build up case, working with and without FreeCAD. 

## Prerequisites OpenFOAM related software

- OpenFOAM (3.0+)  `sudo apt-get install openfoam` once repo is added/imported

> see more OpenFOAM official installation guide

- PyFoam (0.6.6+) `sudo pip install PyFoam`
 

Debian/Ubuntu: see more details of Prerequisites installation in *Readme.md* in *FoamCaseBuilder* folder

RHEL/SL/Centos/Fedora: Installation tutorial/guide is welcomed from testers

## Platform support status
- install on Linux:
        Ubuntu 16.04 as a baseline implementation

- install on Windows 10 with Bash on Windows support:
        Official OpenFOAM  (Ubuntu deb) can be installed and run on windows via Bash on Windows,
        but it is tricky to run windows python script to call the command with python via subprocess module

- install on MAC (not tested):
        As a POSIX system, it is possible to run OpenFOAM and this moduel, assuming openfoam/etc/bashrc has been sourced for bash
        
## Installation guide
        
### install from github
`git clone https://github.com/qingfengxia/Cfd.git`
        
symbolic link or copy the folder into `<freecad installation folder>/Mod`, 
e.g, on POSIX system: 

`sudo ln -s (path_to_CFD)  (path_to_freecad)/Mod`
        
### install from FreeCAD

ALTERNATIVELY, use FreeCAD-Addon-Installer macro from <https://github.com/FreeCAD/FreeCAD-addons>

## How to contribute this module

You can fork this module to add new CFD solver or fix bugs for this OpenFOAM solver.

There is a ebook "Module developer's guide on FreeCAD source code", there are two chapters describing how Fem and Cfd modules are designed and implemented.

<https://github.com/qingfengxia/FreeCAD_Mod_Dev_Guide.git> where updated PDF could be found on this git repo

This is an outdated version for early preview:
<https://www.iesensor.com/download/FreeCAD_Mod_Dev_Guide__20160920.pdf>


