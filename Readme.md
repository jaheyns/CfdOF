# Computional fluid dynamics (CFD) workbench for FreeCAD

This workbench aims to help users set up and run CFD analysis. It guides the user in selecting the relevant physics, 
specifying the material properties, generating a mesh, assigning boundary conditions and setting the solver settings
before running the simulation. Where possible best practices are included to improve the stability of the solvers.

![screenshot](https://forum.freecadweb.org/download/file.php?id=35618)

## Features

### Current:

* Incompressible, laminar flow (simpleFoam, pimpleFoam).
* Basic multiphase capability (interFoam, multiphaseInterFoam)
* Basic material data base.
* Flow initialisation with a potential solver.
* Tetrahedral meshing using GMSH including multiple region meshing using FEM workbench functionality.
* Post processing using paraview.
* Porous regions and porous baffles.
* Runs on Windows 7-10
* Unit testing
* Cut-cell Cartesian meshing with boundary layers.
* Extension to turbulent using RANS (k-w SST).
* New case builder using a modular template structure

### Future (2017):

* Conjugate heat transfer.

### Platforms supported

#### Linux: 

Any system on which FreeCAD and the prerequisites listed below can be installed. The following have been tested:
* Ubuntu 16.04 
* Fedora 24

#### Windows:

* Windows 7 (tested)
* Windows 8 (not yet tested)
* Windows 10 (tested)

#### MacOSX:

Not tested, but a POSIX system. Possible to install and run OpenFOAM. 
      
=============================================
  
## Getting started

### Prerequisites

The CFD workbench depends on the following external software, some of
which can be automatically installed (see below for instructions).

- [Latest development version of FreeCAD (0.17 prerelease; git commit 11209 or later)](https://www.freecadweb.org/wiki/Download)  
- [OpenFOAM (version 4.0 or later)](http://openfoam.org/download/)  
- [Gnuplot.py (version 1.8)](http://gnuplot-py.sourceforge.net/)  
- [Gnuplot](http://www.gnuplot.info/)  
- [Paraview](http://www.paraview.org/)  
- [GMSH (version 2.13 or later)](http://gmsh.info/)  
- [cfMesh (version 1.1.2)](https://sourceforge.net/projects/cfmesh/files/)

### Setting up CFD workbench

#### Windows

##### Option 1: Packaged version
In Windows, it is suggested to download a pre-packaged version from 
https://opensimsa.github.io/download.html
and consult the included README file. 
This package comes with the latest stable release of the CFD workbench and most dependencies
already installed. For installation of additional dependencies, see below.

##### Option 2: Installation into FreeCAD
Alternatively, a recent FreeCAD build can be obtained from
https://github.com/FreeCAD/FreeCAD/releases and the latest
CFD workbench downloaded from 
https://github.com/jaheyns/CfdFoam\.
After extracting the FreeCAD archive to a directory <FreeCAD-directory>, the CFD workbench can be extracted
to the folder <FreeCAD-directory>\Mod\CfdFoam or to 
\<Application Data\>\FreeCAD\Mod\CfdFoam. 

##### Dependency installation

Whichever option is used, dependencies can be checked and installed
conveniently from the CFD Preferences panel in FreeCAD.
In the FreeCAD window, select Edit | Preferences ... and
choose "CFD". 

The OpenFOAM installation is via the [blueCFD-Core](http://bluecfd.github.io/Core/Downloads/) package (version 2016-1),
with which Gnuplot and Paraview come bundled. This can be installed
manually using the above link, or by clicking the relevant
button in the Preferences panel described above.

Set the OpenFOAM install directory in the preferences
panel to \<blueCFD install directory\>\OpenFOAM-4.x
 (It will be automatically detected in the default install
location.)

Likewise the Gnuplot-py module can be installed from the Preferences
panel (not necessary if using Option 1), as well as cfMesh.
cfMesh is automatically built from source inside the OpenFOAM
environment if installed from the Preferences panel. Note
that this is a lengthy process.

Choosing the "Check dependencies" option will verify that all 
prerequisites have been successfully installed.

#### Linux

The latest development version of FreeCAD can be obtained from 
the [Ubuntu daily build](https://www.freecadweb.org/wiki/Download#Ubuntu_Daily_PPA_Packages)
packages. Alternatively, it can be built from the source code
at 
https://github.com/FreeCAD/FreeCAD\.

As the CFD workbench is fully developed in Python the user is not required to 
compile any libraries in order to use it, and can directly 
copy the folder to <FreeCAD-directory>/Mod/CfdFoam or to ~/.FreeCAD/Mod/CfdFoam

As an example, from the command line, use git to clone the CFD workbench
    
    $ git clone https://github.com/jaheyns/CfdFoam.git
        
and create a symbolic link to the local FreeCAD instalation directory. 
    
    $ ln -s <path/to/CfdFoam>  <path/to/FreeCAD>/Mod/CfdFoam
        
This workbench is unfortunately not yet available under the  FreeCAD-Addon-Installer.

##### Dependency installation

Dependencies can be checked and some of them installed
conveniently from the CFD Preferences panel in FreeCAD.
In the FreeCAD window, select Edit | Preferences ... and
choose "CFD". 
Manual installation is however required for 
[OpenFOAM](http://openfoam.org/download/),
[Gnuplot](http://www.gnuplot.info/),
[Paraview](http://www.paraview.org/) and
[GMSH](http://gmsh.info/), which should be
installed using your distribution's package manager
or the links above.

Set the OpenFOAM install directory in the preferences
panel - typical install locations are /home/user/OpenFOAM/OpenFOAM-4.x
or /opt/openfoam4 (It will be automatically detected in common default install
locations.)

The Gnuplot-py package can be installed into Python
using the Preferences panel described above, as well
as cfMesh which will be downloaded and built from the source
code inside your OpenFOAM installation if you have
not already done so yourself. Note that this is a lengthy process.

Choosing the "Check dependencies" option will verify that all 
prerequisites have been successfully installed.


## Feedback

### Submitting Bugs

Please discuss issues on the [CFDFoam dedicated FreeCAD forum thread](https://forum.freecadweb.org/viewtopic.php?f=18&t=21576).

## Developement

It is asked that developers should only add functionality or code that is working and can be tested. Dead code, even
portions included for possible future functionality, reduces function clarity and increases the maintenance overhead.

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
    - functionsWithoutCapitals (Camel instead of underscore to ensure consistency with FreeCAD)
    - __class_attribute (Double leading underscore)


## Developers

Oliver Oxtoby (CSIR, 2016-2017) <ooxtoby@csir.co.za>  
Johan Heyns (CSIR, 2016-2017) <jheyns@csir.co.za>  
Alfred Bogaers (CSIR, 2016-2017) <abogaers@csir.co.za>    
Qingfeng Xia (2015)
Klaus Sembritzki (2017)
