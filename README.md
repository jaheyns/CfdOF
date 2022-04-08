# CfdOF: A Computational fluid dynamics (CFD) workbench for FreeCAD

This workbench aims to help users set up and run CFD analyses within the [FreeCAD](https://freecadweb.org)
modeller. It guides the user in selecting the relevant physics, 
specifying the material properties, generating a mesh, assigning boundary conditions and choosing the solver settings
before running the simulation. Best practices are specified to maximise the stability of the solvers.

![screenshot](https://forum.freecadweb.org/download/file.php?id=35618)

The workbench serves as a front-end (GUI) for the popular OpenFOAM® CFD toolkit (www.openfoam.org, www.openfoam.com).

Disclaimer:
This offering is not approved or endorsed by OpenCFD Limited, producer and distributor of the OpenFOAM software via www.openfoam.com, and owner of the OPENFOAM® and OpenCFD® trade marks

## Features

### Current:

* Incompressible, laminar flow (simpleFoam, pimpleFoam)
* Extension to RANS turbulent flow (k-omega SST (incl. transistion), k-epsilon, and Spalart-Allmaras models supported)
* Extension to LES turbulent flow (k-Equation, Smagorinsky and WALE (Wall bounded) models)
* Incompressible free-surface flow (interFoam, multiphaseInterFoam)
* Compressible buoyant flow (buoyantSimpleFoam, buoyantPimpleFoam)
* High-speed compressible flow ([HiSA](https://hisa.gitlab.io))
* Porous regions and porous baffles
* Basic material database
* Flow initialisation with a potential solver
* Cut-cell Cartesian meshing with boundary layers (cfMesh)
* Cut-cell Cartesian meshing with baffles (snappyHexMesh) and implicit / explicit snapping
* Tetrahedral meshing using Gmsh
* Conversion to poly dual mesh from existing meshes
* Post meshing check mesh
* Postprocessing using Paraview
* Runs on Windows 7-11 and Linux
* Unit/regression testing
* Case builder using an extensible template structure
* Macro scripting

### Platforms supported

#### Linux

Any system on which FreeCAD and the prerequisites listed below can be installed.

#### Windows

Windows 7-11; 64-bit version is required.

#### macOS

Not widely tested, but success has been reported. See 
[the following forum post](https://forum.freecadweb.org/viewtopic.php?f=37&t=63782&p=547611#p547578)
for instructions.

## Getting started

### Prerequisites

The CfdOF workbench depends on the following external software, some of
which can be automatically installed (see below for instructions).

- [Latest release version of FreeCAD (at least version 0.18.4 / git commit 16146)](https://www.freecadweb.org/downloads.php)
 or [latest development version (prerelease)](https://github.com/FreeCAD/FreeCAD/releases)  
- OpenFOAM [Foundation versions 5-9](http://openfoam.org/download/) or [ESI-OpenCFD versions 1706-2112](http://openfoam.com/download)  
- [Paraview](http://www.paraview.org/)  
- [FreeCAD plot workbench](https://github.com/FreeCAD/freecad.plot.git)
- [cfMesh (customised version updated to compile with latest OpenFOAM versions)](https://sourceforge.net/projects/cfmesh-cfdof/)
- [HiSA (High Speed Aerodynamic Solver)](https://hisa.gitlab.io)
- [Gmsh (version 2.13 or later)](http://gmsh.info/) - optional, for generating tetrahedral meshes

### Setting up the CfdOF workbench

#### Windows

The latest 
[release](https://www.freecadweb.org/downloads.php) 
or [development](https://github.com/FreeCAD/FreeCAD/releases)
FreeCAD build can be obtained (64 bit version) and installed
by respectively running the installer or extracting the .7z archive to a directory
\<FreeCAD-directory\>. In the latter case, FreeCAD can be run in place
(\<FreeCAD-directory\>\bin\FreeCAD.exe). 

Before installing CfdOF, the Plot workbench must first be 
installed into FreeCAD using the Addon manager:

* Run FreeCAD
* Select Tools | Addon manager ...
* Select Plot in the list of workbenches, and click "Install/update"
* Restart FreeCAD
* Repeat the above for the "CfdOF" workbench
* For installation of dependencies, see below

Note: The CfdOF workbench can be updated at any time through the Addon manager.

##### Dependency installation

Dependencies can be checked and installed
conveniently from the CfdOF Preferences panel in FreeCAD.
In the FreeCAD window, select Edit | Preferences ... and
choose "CfdOF". 

The OpenFOAM installation is via the [OpenCFD MinGW package](https://www.openfoam.com/download/install-binary-windows-mingw.php), and 
the [BlueCFD Core](https://bluecfd.github.io/Core/) port of OpenFOAM is also supported. 
The [OpenCFD docker package](https://www.openfoam.com/download/install-binary-windows.php) is also currently supported but has some issues.  

OpenFOAM can be installed manually using the above links, or by clicking the relevant
button in the Preferences panel described above. If you experience problems running OpenFOAM in CfdOF, please make
sure you have a working installation by following instructions on the relevant websites.

To interface correctly with the OpenFOAM installation, CfdOF needs to be able to write to its
install location.
Some users experience problems using a location inside C:\Program Files due to restrictions
imposed by Windows User Account Control. It is therefore suggested to install to an alternative 
location, preferably in your home directory.  

Set the OpenFOAM install directory in the preferences
panel to the install directory ending in the 'vXXXX' subfolder (where XXXX is the version number installed)
for the MinGW package, or the BlueCFD install directory.
 It will be automatically detected in the default install
locations.

Any version of [ParaView](https://www.paraview.org/download/) can be installed, 
by following the above link or clicking the relevant button in the Preferences panel.
Set the ParaView install path in the preferences panel to the 'paraview.exe' file in the 'bin' 
subfolder of the ParaView installation. Common defaults will be detected if it is left blank.

Likewise, cfMesh and HiSA can be installed from the 
Preferences panel. Do not close
it until the 'Install completed' message is received.
Note that the OpenFOAM installation must be in a writable location
for cfMesh and HiSA to be installed successfully.

Choosing the "Check dependencies" option will verify that all 
prerequisites have been successfully installed.

#### Linux

AppImages of the latest [release](https://www.freecadweb.org/downloads.php) 
or [development](https://github.com/FreeCAD/FreeCAD/releases) 
versions of FreeCAD can be downloaded and run directly
without installation. Note that you will
have to enable execution permission on the downloaded file to run it.
The [Ubuntu PPA daily build](https://www.freecadweb.org/wiki/Install_on_Unix)
packages are an alternative binary option. Otherwise, FreeCAD can be built 
from the source code at 
https://github.com/FreeCAD/FreeCAD . 

Note:
* Installations of FreeCAD via Linux package managers (including the PPA daily build above)
make use of your local python installation. Therefore you might need to install additional
python packages to get full functionality. The dependency checker (see below) can help to diagnose 
this. 
* Note that the 'Snap' container installed through some distributions' package managers
can be problematic as it does not allow access to system
directories, and therefore OpenFOAM has to be installed in the user's home directory
to be runnable from FreeCAD. 

For the reasons above we recommend the AppImage as the most robust installation
option on Linux.

Before installing CfdOF, the Plot workbench must first be 
installed into FreeCAD using the Addon manager:

* Run FreeCAD 
* Select Tools | Addon manager ...
* Select Plot in the list of workbenches, and click "Install/update"
* Restart FreeCAD
* Repeat the above for the "CfdOF" workbench
* For installation of dependencies, see below


##### Dependency installation

Dependencies can be checked and some of them installed
conveniently from the CFD Preferences panel in FreeCAD.
In the FreeCAD window, select Edit | Preferences ... and
choose "CFD".

However, in Linux, manual installation is required for 
OpenFOAM ([OpenCFD](https://openfoam.com/download) or [Foundation](https://openfoam.org/download/) versions),
[Paraview](http://www.paraview.org/) and
[Gmsh](http://gmsh.info/) (optional). They should be
installed using the links above or your distribution's package 
manager. Note, however, that the OpenFOAM packages bundled in 
some Linux distributions may be out of date or incomplete; for example,
the standard Debian and Ubuntu packages do not include the build command 'wmake' 
and therefore cannot be used with the optional components 'HiSA' and 'cfMesh'.
We therefore recommend installation of the packages supplied through
the official websites above.

Set the OpenFOAM install directory in the preferences
panel - examples of typical install locations are /opt/openfoam8 
or /home/user/OpenFOAM/OpenFOAM-8.x (It will be automatically 
detected in common default install
locations). Note that if you have loaded the desired OpenFOAM 
environment already, the install directory should be left blank.

cfMesh and HiSA can be installed using the Preferences panel described above,
and can be downloaded and built from their source
code inside your OpenFOAM installation if you have
not already done so yourself. Note that this is a lengthy process.

Choosing the "Check dependencies" option will verify that all 
prerequisites have been successfully installed.

## Documentation

At present there is no formal documentation for CfdOF apart from this README. 
However, demonstration cases
are provided inside the 'demos' folder of the 
[CfdOF workbench directory](https://gitlab.com/opensimproject/cfdof). These aim
to provide a basic overview of features and best practices. The examples are run
by loading and executing the macro files ending in '.FCMacro' in the various sub-directories
in the 'demos' directory. Where there are several numbered files, these should be run in order
and aim to demonstrate step-by-step how the case is set up.

Community assistance may be sought at the 
[CfdOF dedicated FreeCAD forum](https://forum.freecadweb.org/viewforum.php?f=37),
and a list of various third-party documentation is available in
[the following forum post](https://forum.freecadweb.org/viewtopic.php?f=37&t=33492#p280359).

### FAQ

Q: Do I have to create a watertight geometry?

A: This isn't necessary if using the cartesian mesh generators _snappyHexMesh_ and _cfMesh_.
You can make use of shells and compounds instead of creating solids, as long as the 
collection of shapes in the compound being meshed blocks off the volume desired. 
Gaps smaller than the mesh spacing are also allowed.

## Feedback

### Reporting Bugs

Please discuss issues on the [CfdOF FreeCAD forum](https://forum.freecadweb.org/viewforum.php?f=37) 
for community assistance.
Bugs can be reported on the [gitlab project site](https://gitlab.com/opensimproject/cfdof). 

Please first read the [guidelines for reporting bugs](https://forum.freecadweb.org/viewtopic.php?f=37&t=33492#p280359) 
in order to provide sufficient information.

## Development
[![Total alerts](https://img.shields.io/lgtm/alerts/g/jaheyns/CfdOF.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/jaheyns/CfdOF/alerts/)[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/jaheyns/CfdOF.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/jaheyns/CfdOF/context:python)

If you'd like to get involved in the development of CfdOF, please check out our [Contribution guidelines](CONTRIBUTING.md). 
   
## Acknowledgements

### Funding
This development was made possible through initial funding from [Eskom Holdings SOC Ltd](http://www.eskom.co.za)
and the [Council for Scientific and Industrial Research](https://www.csir.co.za) (South Africa).

### Lead developers
The code is primarily developed by
* Oliver Oxtoby (CSIR, 2016-2018; private 2019-) <oliveroxtoby@gmail.com>  
* Johan Heyns (CSIR, 2016-2018) <jaheyns@gmail.com>  
* Alfred Bogaers (CSIR, 2016-2018) <alfredbogaers@gmail.com>    

### Contributors

We acknowledge significant contributions from
* Qingfeng Xia (2015) - Original framework
* Michael Hindley (2016) - Initial concept
* Klaus Sembritzki (2017) - Multiphase extension
* Thomas Schrader (2017-) <info@schraderundschrader.de> - Testing and user assistance
* Jonathan Bergh (2022) - Additional turbulence models

### Dedication

CfdOF is dedicated to the memory of Michael Hindley. It is thanks to his irrepressible enthusiasm for 
FreeCAD and open source software that this workbench exists. Rest in peace.

_Last Updated 07/04/2022_