==================
#FoamCaseBuilder
==================

Qingfeng Xia
Jan 24, 2016
updated: August 17, 2016


### Introduction

FoamCaseBuilder aims to setup OpenFOAM case from python script, based on PyFoam. 

Merging FEM and CFD into a single processing pipeline (solver -> analysis -> AnalysisControlTaskPanel) is given up. 
CFD case setup code should be independent from Fem CalculiX code, to reduce work to merge with master each time. 

### OpenFoam is designed for POSIX, but possible on windows

OpenFOAM for windows is available now: http://www.openfoam.com/products/openfoam-windows.php
docker container in VirtualBox, also  ubuntu on windows 10 may run OpenFOAM directly in the future

Possible routes:

- OpenFoam+cygwin (not recommended, since you need to compile OpenFOAM from source)
- docker as the OpenFoam official done (launched in 2015); 
see [windows support in Docker](http://www.openfoam.com/download/install-windows.php).
I have not tried to call a command in docker Linux Image from windows. 
- bash on ubuntu on windows 10 (Windows's linux subsystem), test passed
see <http://www.iesensor.com/blog/2016/09/04/evaluation-of-openfoam-on-bash-on-ubuntu-on-windows-10/>

make Cygwin's windows disk mount point as as as Bash on windows: 
`/cygwin/c -> /mnt/c`
Set the cygdrive prefix to /mnt in /etc/fstab
`none /mnt cygdrive binary 0 0`

### Software prerequisits for Testing (Linux ONLY as in year 2016!!!)

- both python 3.4+ and python 2.7 are supported
- FreeCAD 0.17+: with all FEM features, netgen for meshing, 
before merge of this this fork, you need to build my forK
`git clone --branch foambuilder1 https://github.com/qingfengxia/FreeCAD.git  --single-branch`
If you install freecad-daily version 20160921 from PPA, CFD module can be tested with FreeCAD master

- OpenFOAM: 3.0+ will be supported for simplified setting dict; 2.x should works but not tested
  This module can work with FreeCAD/python interpreter start with lancher, need NOT to start in shell like gnome-terminal
- paraFoam: paraview 5 goes with OpenFOAM 4
- Salome: optional, recommended for comprehensive meshing capability
- PyFoam:  0.66, released in July 2016, can support some dict files for Openfoam 3.0+
- curl: optional, to download the example mesh file


### Test only on ubuntu 16.04

OpenFoam 4.0 can be installed from third party repo, which will also install the correct Paraview 5.0.  default location /opt/openfoam4/, as if the FoamCaseBuilder default to 4.0 version if it can not detect the OpenFoam version.

Also install PyFoam (0.66 as since July 2016), which can be done via "pip install PyFoam". On linux 16.04, python 2.7 is not default need installation, as is python-pip. PyFoam is globally accessible from FreeCAD. It is GPL software, it can not be copied with FreeCAD source. 

see [installation guide](http://www.openfoam.com/download/install-binary.php) If it is not for your linux ver, just try your package manager
see [OpenFoam quick startup guide](http://www.openfoam.org/)
see [tutorials](http://cfd.direct/openfoam/user-guide/) 

Basically, I need several programs on PATH and some env var exported, like icoFoam, paraview, paraFoam. This be easily done by source a bash script: `source /opt/openfoam4/etc/bashrc.sh` in your ~/.bashrc. Notably, this script can not been sourced to system wide, like /etc/profile;  user can not log into desktop once source this. 

`runFoamCommand('paraFoam')` is translates into `Popen("bash -c -i 'paraFoam'", shell=True)`:

https://www.iesensor.com/download/TestCase.unv and must be put into Mod/Fem/FoamCaseBuilder/
Test FoamCaseBuilder module without FreeCAD: "python pathto/FoamCaseBuilder/TestBulderer.py"

Test with FreeCAD by download: https://www.iesensor.com/download/TestFoam.fcstd


### FoamCaseBuilder as an independent python module

FoamCaseBuilder  is designed as working without any GUI, seen "TestBuilder.py"

Please run the "TestBuilde.py" from the FoamCaseBuilder folder, as all data file (template.zip and mesh) are relative from this folder/file

trimmed case is copied from a zipped template file "simpleFoam_v3.zip", then FoamCaseBuilder script will modify the case folder accordingly. 

### Test FoamCaseBuilder in FreeCAD

As the boundary condition/constraint GUI is finished , it is possible to test in GUI. 

I have a CfdExample.py in Mod/Fem folder,  paste the first half into FreeCAD console, it can make the example shown in my figure above.

However, the mesh can not be re-generated from the macro/script, it needs to click Mesh Taskpanel GUI to generate mesh.

Material taskpanel is not needed in CFD mode as it is default to water. Change the viscosity in OpenFoam case setup please

### see ./Roadmap.md for feature completion adn future plan

Huge work is needed to make a GUI for case setup for CFD, I may just focus on making it work in script mode first. 

### Acknowldgement

Thanks for my wife, Ms Jia Wang's ultimate support by freeing me from housework to code

########################################################################################################################

## previous pre-release

### Test only on ubuntu 14.04 (for the fork foambuilder_pre2)
tested: April 17, 2016
outdated: since Aug 2016
`git clone --branch foambuilder_pre2 https://github.com/qingfengxia/FreeCAD.git  --single-branch`

OpenFoam 2.x/3.0 can be installed from repo, which will also install the correct Paraview.  Please install OpenFoam 3.0 to default location /opt/, as if the FoamCaseBuilder default to 3.0 version if it can not detect the OpenFoam version.

Also install PyFoam, which can be done via "pip install PyFoam", on linux, FreeCAD reuses the system python 2.7, so PyFoam is accessible from FreeCAD. It is GPL software? can not be copy to FreeCAD source. 

see [installation guide](http://www.openfoam.com/download/install-binary.php) If it is not for your linux ver, just try your package manager
see [OpenFoam quick startup guide](http://www.openfoam.org/)
see [tutorials](http://cfd.direct/openfoam/user-guide/) 

Basically, I need several programs on PATH and some env var exported, like icoFoam, paraview, paraFoam. This be easily done by source a bash script(/opt/openfoam30/etc/bashrc.sh) in your ~/.bashrc, but there is a serious issue,  this script can not been sourced to system wide, like /etc/profile,  user can not log into desktop once source this. Nevertheless, I failed to run Popen(cmd, Terminal=True) , which I wish it can simulate run a program in a new terminal (which will source ~/.bashrc).

default to openfoam installation path: "/opt/openfoam30/" , as in Ubuntu 14.04
runFoamCommand():
bash -c 'source /opt/openfoam30/etc/bashrc.sh & paraFoam'
