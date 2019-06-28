# CfdOF: A Computational fluid dynamics (CFD) workbench for FreeCAD

This workbench aims to help users set up and run CFD analyses within the [FreeCAD](https://freecadweb.org)
modeller. It guides the user in selecting the relevant physics, 
specifying the material properties, generating a mesh, assigning boundary conditions and setting the solver settings
before running the simulation. Best practices are chosen to maximise the stability of the solvers.

![screenshot](https://forum.freecadweb.org/download/file.php?id=35618)

The workbench serves as a front-end to the popular OpenFOAM® CFD toolkit (www.openfoam.org, www.openfoam.com).

Disclaimer:
This offering is not approved or endorsed by OpenCFD Limited, producer and distributor of the OpenFOAM software via www.openfoam.com, and owner of the OPENFOAM® and OpenCFD® trade marks

## Features

### Current:

* Incompressible, laminar flow (simpleFoam, pimpleFoam)
* Incompressible free-surface flow (interFoam, multiphaseInterFoam)
* High-speed compressible flow ([HiSA](https://hisa.gitlab.io))
* Basic material database
* Flow initialisation with a potential solver
* Cut-cell Cartesian meshing with boundary layers (cfMesh)
* Cut-cell Cartesian meshing with porous media (snappyHexMesh)
* Tetrahedral meshing using GMSH
* Postprocessing using paraview
* Porous regions and porous baffles
* Runs on Windows 7-10 and Linux
* Unit testing
* Extension to turbulent flow using RANS (k-w SST)
* New case builder using an extensible template structure
* Macro scripting

### Planned:

* Conjugate heat transfer.

### Platforms supported

#### Linux

Any system on which FreeCAD and the prerequisites listed below can be installed.

#### Windows

Windows 7-10; 64-bit version is required.

#### MacOSX

Not widely tested, but possible. 
      
## Getting started

### Prerequisites

The CfdOF workbench depends on the following external software, some of
which can be automatically installed (see below for instructions).

- [Latest release version of FreeCAD (0.18)](https://www.freecadweb.org/downloads.php)
 or [latest development version (0.19 prerelease)](https://github.com/FreeCAD/FreeCAD/releases)  
- OpenFOAM [Foundation version 4.0 or later](http://openfoam.org/download/) or [ESI version 1706 or later](http://openfoam.com/download)  
- [Paraview](http://www.paraview.org/)  
- [FreeCAD plot workbench](https://github.com/FreeCAD/freecad.plot.git)
- [cfMesh (customised version updated to compile with latest OpenFOAM versions)](https://sourceforge.net/projects/cfmesh-cfdof/)
- [HiSA (High Speed Aerodynamic Solver)](https://hisa.gitlab.io)
- [GMSH (version 2.13 or later)](http://gmsh.info/) - optional, for generating tetrahedral meshes

### Setting up the CfdOF workbench

#### Windows

The latest 
[release](https://www.freecadweb.org/downloads.php) 
or [development](https://github.com/FreeCAD/FreeCAD/releases)
FreeCAD build can be obtained (64 bit version) and the latest
CfdOF workbench can be installed into it using the Addon manager:

* After running the installer or extracting the .7z archive to a directory <FreeCAD-directory>,
run FreeCAD in place (<FreeCAD-directory\bin\FreeCAD.exe). 
* Select Tools | Addon manager ...
* Select CfdOF in the list of workbenches, and click "Install/update"
* Restart FreeCAD
* For installation of dependencies, see below.

Note: The CFD workbench can be updated at any time through the Addon manager.

##### Dependency installation

Dependencies can be checked and installed
conveniently from the CFD Preferences panel in FreeCAD.
In the FreeCAD window, select Edit | Preferences ... and
choose "CFD". 

The OpenFOAM installation is via the [blueCFD-Core](http://bluecfd.github.io/Core/Downloads/) package (version 2017-2),
with which Paraview comes bundled. This can be installed
manually using the above link, or by clicking the relevant
button in the Preferences panel described above.

Please note that User Access Control in Windows 10 can restrict write
access to the Program Files directory, which interferes with
the installation of cfMesh and HiSA in blueCFD-Core. **It is therefore recommended
that blueCFD-Core be installed outside the Program Files folder.**

Set the OpenFOAM install directory in the preferences
panel to \<blueCFD install directory\>\OpenFOAM-5.x
 (It will be automatically detected in the default install
location.)

Likewise, cfMesh and HiSA can be installed from the 
Preferences panel. They are automatically built from source 
inside the OpenFOAM environment if installed from the 
Preferences panel. Note that this is a lengthy process.

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
[OpenFOAM](http://openfoam.org/download/),
[Paraview](http://www.paraview.org/) and
[GMSH](http://gmsh.info/) (optional). They should be
installed using your distribution's package manager
or the links above. 

Set the OpenFOAM install directory in the preferences
panel - typical install locations are /opt/openfoam6 
or /home/user/OpenFOAM/OpenFOAM-6.x (It will be automatically 
detected in common default install
locations.)

cfMesh and HiSA can be installed using the Preferences panel described above,
and can be downloaded and built from the source
code inside your OpenFOAM installation if you have
not already done so yourself. Note that this is a lengthy process.

Choosing the "Check dependencies" option will verify that all 
prerequisites have been successfully installed.


## Feedback

### Reporting Bugs

Please discuss issues on the [CfdOF dedicated FreeCAD forum](https://forum.freecadweb.org/viewforum.php?f=37).
Bugs can be reported on the [github project site](https://github.com/jaheyns/cfdof). 

Please first read the [guidelines for reporting bugs](https://forum.freecadweb.org/viewtopic.php?f=37&t=33492#p280359) 
in order to provide sufficient information.

## Development

It is asked that developers should only add functionality or code that is working and can be tested. Dead code, even
portions included for possible future functionality, reduces function clarity and increases the maintenance overhead. 
Our philosophy is 'Do the basics well' and therefore robust operation takes precedence over extended functionality.

### Testing

Unit testing is currently under development. Where possible, it is asked that all new functionality should be included
in the unit test framework.


### Style guide

For consistency please follow [PEP8](https://www.python.org/dev/peps/pep-0008/)
1. Use 4 spaces per indentation level (spaces are preferred over tabs).
2. Limit all lines to a maximum of 120 characters.
3. Break lines before binary operators.
4. Blank lines 
    
    - Surround top-level function and class definitions with two lines.

    - Definitions inside a class are surrounded by a single line.
    
5. Imports should usually be on separate lines.
6. Comments
    - Docstrings always use """triple double-quotes"""
    
    - Block comment starts with a # and a single space and are indented to the same level as that code
    
    - Use inline comments sparingly. They are on the same line as a statement and should be separated by at least two
 spaces from the statement. 

7. Avoid trailing whitespaces
8. Naming convention

    - ClassNames (Camel)
    - variable_names_without_capitals (Underscore)
    - CONSTANTS_USE_CAPITALS (Uppercase)
    - functions_without_capitals (underscore, preferred as it follows PEP8)
    - functionsWithoutCapitals (Camel instead of underscore is accepted as it is widely used within FreeCAD)
    - __class_attribute (Double leading underscore)


## Acknowledgements

### Funding
This development was made possible through funding from [Eskom Holdings SOC Ltd](http://www.eskom.co.za)
and the [Council for Scientific and Industrial Research](https://www.csir.co.za) (South Africa).

### Lead developers
The code is maintained by
* Oliver Oxtoby (CSIR, 2016-2018; private 2019-) <oliveroxtoby@gmail.com>  
* Johan Heyns (CSIR, 2016-2018) <jaheyns@gmail.com>  
* Alfred Bogaers (CSIR, 2016-2018) <alfredbogaers@gmail.com>    

### Contributors

We acknowledge significant contributions from
* Qingfeng Xia (2015) - Original framework
* Michael Hindley (2016) - Initial concept
* Klaus Sembritzki (2017) - Multiphase extension
* Thomas Schrader (2017-2018) <info@schraderundschrader.de> - Testing and user assistance
