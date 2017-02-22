# Computional fluid dynamics (CFD) workbench for FreeCAD

This workbench aims to help users set up and run CFD analysis. It guides the user in selecting the relevant physics, 
specifying the material properties, generating a mesh, assigning boundary conditions and setting the solver settings
before running the simulation. Where possible best practices are included to improve the stability of the solvers.

This software is a fork of the CFD workbench developed by [Qingfeng Xia](http://github.com/qingfengxia/Cfd), but
focuses on assisting new CFD users. It therefor places greater emphasis on usability and solver stability intead of
functionality.

## Features

### Current:

* Incompressible, laminar flow (simpleFoam and pimpleFoam).
* Basic material data base.
* Flow initialisation with a potential solver.
* Tetrahedral meshing using GMSH.
* Post processing using paraview.
* Porous regions and porous baffles.

### Under development:

* Multiple region meshing
* Unit testing
* Run on Windows 7-10

### Future (2017):

* Cut-cell Cartesian meshing with boundary layers.
* Extension to turbulent using RANS (k-w SST).
* Conjugate heat transfer.

### Platform supported

Linux: 

        Ubuntu 16.04 
        Fedora 24

Windows:

        Not yet supported. 

MAC 

        Not tested, but a POSIX system. Possible to install and run OpenFOAM. 
      
=============================================
  
## Getting started

### Prerequisites

- [OpenFOAM (3.0+)](http://openfoam.org/download/)

- [PyFoam (0.6.6+)](http://pypi.python.org/pypi/PyFoam)

- gnuplot.py or gnuplot-py

- [Paraview](http://www.paraview.org/)
 
- [GMSH (2.13+)](http://gmsh.info/)


### Setting up Cfd workbemch

As the CFD workbench is fully developed in Python the user is not required to compile any libraries and can directly 
copy the folder to <FreeCAD/Mod/Cfd>. 

From command line, clone the CFD workbench
    
    $ git clone https://github.com/jaheyns/Cfd.git`
        
and create a symbolic link the local FreeCAD instalation directory. 
    
    $ ln -s <path/to/Cfd)  <path/to/freecad>/Mod
        

This fork is unfortunately not available under the  FreeCAD-Addon-Installer.


##Developement

It is asked that developers should only add functionality or code that is working and can be tested. Dead code, even
portions included for possible future functionality, reduces function clarity and increases the maintenance overhead.

### Testing

Unit testing is currently under development. Where possible, it is asked that all new functionality should be included
in the unit test framework.


### Style guide

For consistency please follow [PEP8](https://www.python.org/dev/peps/pep-0008/)
1. Use 4 spaces per indentation level (Spaces are the preferred over tabs).
2. Limit all lines to a maximum of 120 characters.
3. Break lines before binary operators.
4. Blank lines 
    
    - Surround top-level function and class definitions with two lines.

    - Definitions inside a class are surrounded by a single line.
    
5. Imports should usually be on separate lines.
6. Comments

    - Docstrings always use """triple double quotes"""
    
    - Block comment starts with a # and a single space and are indented to the same level as that code
    
    - Use inline comments sparingly, they are on the same line as a statement and should be separated by at least two
 spaces from the statement. 

7. Avoid trailing whitespaces
8. Naming convention

    - ClassNames (Camel)
    - variable_names_without_capitals (Underscore)
    - CONSTANTS_USE_CAPITALS (Uppercase)
    - functionsWithoutCapitals (Camel instead of underscore to ensure consistency with FreeCAD)
    - __class_attribute (Double leading underscore)


## Developers

Qingfeng Xia, 2015 <iesensor.com/HTML5pptCV>
Johan Heyns (CSIR, 2016) <jheyns@csir.co.za>         
Oliver Oxtoby (CSIR, 2016) <ooxtoby@csir.co.za>      
Alfred Bogaers (CSIR, 2016) <abogaers@csir.co.za>    

