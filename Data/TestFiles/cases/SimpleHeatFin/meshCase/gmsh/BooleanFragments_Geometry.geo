// geo file created by FreeCAD for meshing with GMSH meshing software

// Open brep geometry
Merge "BooleanFragments_Geometry.brep";

// Characteristic Length

// min, max Characteristic Length
Mesh.CharacteristicLengthMax = 3.0;
Mesh.CharacteristicLengthMin = 0.0;

// Other mesh options
Mesh.RecombineAll = 0;

// GMSH tetra optimizer
Mesh.Optimize = 1;
// Netgen optimizer in GMSH
Mesh.OptimizeNetgen = 0;
Mesh.HighOrderOptimize = 0;

// Mesh order
Mesh.ElementOrder = 1;

// 2D mesh algorithm (1=MeshAdapt, 2=Automatic, 5=Delaunay, 6=Frontal, 7=BAMG, 8=DelQuad)
Mesh.Algorithm = 2;
// 3D mesh algorithm (1=Delaunay, 2=New Delaunay, 4=Frontal, 5=Frontal Delaunay, 6=Frontal Hex, 7=MMG3D, 9=R-tree, 10=hxtDelaunay)
Mesh.Algorithm3D = 10;

// Internal mesh
Physical Volume ("heatsink") = {2};
Physical Volume ("FluidProperties") = {1};

// Boundaries
Physical Surface ("patch_0_0") = {6, 7, 8, 9, 11};
Physical Surface ("patch_1_0") = {1, 3, 4, 10};
Physical Surface ("patch_2_0") = {12};
Physical Surface ("patch_3_0") = {2};
Physical Surface ("patch_4_0") = {5};

// Meshing
Mesh 3;

// Save
Mesh.Format = 10; // Auto according to extension
Mesh.MshFileVersion = 2.2;

// Ignore Physical definitions and save all elements
Mesh.SaveAll = 0;

// Save in msh for OpenFOAM as its unv converter is outdated
Save "BooleanFragments_Geometry.msh";
