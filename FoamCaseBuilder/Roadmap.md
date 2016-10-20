
## Foam CaseBuilder for FreeCAD Roadmap

### Phase I demonstration (Finished 2016-01-20)

2D mesh, GGI and dynamic mesh will not be supported here

branch: foambuilder_pre1
- CaeAnalysis: class should operate on diff category of solvers
- CaseSolver: extending Fem::FemSolverObject, factory pattern, create solver from name
- FoamCaseWriter: OpenFOAM case writer, the key part is meshing and case setup
- Fixed material as air or water
- 3D UNV meshing writing function, FreeCAD mesh export does not write boundary elements
- Use fem::constraint Constraint mapping: 
    Force->Velocity (Displacement is missing), 
    Pressure->Pressure, Symmetry is missing (Pulley), 
    PressureOutlet (Gear), VelocityOutlet(Bearing),

### Phase II general demonstration (Finished 2016-04-17)

branch: foambuilder_pre2
`git clone --branch foambuilder_pre2 https://github.com/qingfengxia/FreeCAD.git  --single-branch`

- FemMaterial:  A domo for general Materail model for any FEM
   not yet fully functional, to discuss with community for standardizing Material model, 
   also design for other CAE analysis EletroMagnetics
   
- CFD boundary conditions are catogeried into 5 types: inlet, outlet, wall, interface, freestream
    GUI menu and toolbar added
    
- Run the OpenFoam sovler in external terminal

- Use exteranal result viewer paraview
    CFD is cell base solution, while FEM is node base. It is not easy to reuse ResultObject 
    volPointInterpolation - interpolate volume field to point field;

### Phase III general usability (2016-09-05)

`foambuilder_pre2` has be refactored to keep update with latest FemWorkbench as branch: `foambuilder1`

- cpp code FemConstraintFluidBoundary merged (Aug 2016)
- TaskPanelFemSolverControl:  a general FemSolver control TaskPanel
- python codes CfdCaseWriterFoam and module FoamCaseBuilder etc. (Sep 2016)
- basic RAS turbulent model and heat transfering case support (Oct 2016)

### Phase IV: a new module "Cfd"

- branch `foambuilder1` is moved into a new module "Cfd" (Oct 2016)
- VTK mesh import and export for both Fem and Cfd modules (Oct 2016)
- CfdResult import and render pressure on FemMesh (Oct 2016)

todo:

- CfdExample.py for Cfd module
- improve FreeCAD meshing quality for CFD, boundary layer inflation and mesh importing
    CFD mesh with viscous layer and hex meshcell supported,
    The best way to do that will be meshing externally like Salome, and importing back to FreeCAD
    Currently, the bad mesh quality make turbulence case hard to converge

- FemMaterial: a general materail object serve all kinds of CAE Analysis
   
- Feature request from FreeCADGui or FemMesh
   NamedSelection (Collection of mesh face) for boundary:
          for identifying mesh boundary imported from mesh file
   Part section: build3DFromCavity buildEnclosureBox
          for example, there a pipe section, how to extract void space in pipe for CFD

### Phase V  FSI (year 2017?)

todo:
- More CFD Analysis Type supported, transient, heat transfer and LES model setup

- multiphase case setup

- AnalysisCoupler.py

list of FemAnalysis instances,  add_analysis()  add_time()
timeStep, currentTime,  adaptiveTimeStep=False
historicalTimes chain up all historical case data file. 
static multiple solvers are also possible





