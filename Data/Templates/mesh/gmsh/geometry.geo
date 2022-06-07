%{%(MeshUtility%)
%:gmsh
%{%(Name%)
// geo file created by FreeCAD for meshing with GMSH meshing software

// Open brep geometry
Merge "%(0%)_Geometry.brep";

// Characteristic Length
%{%(GmshSettings/HasLengthMap%)
%:True
%{%(GmshSettings/LengthMap%)
// %(0%)
Characteristic Length { %(GmshSettings/NodeMap/%(0%)%) } = %(GmshSettings/LengthMap/%(0%)%);
%}
%}

// min, max Characteristic Length
Mesh.CharacteristicLengthMax = %(GmshSettings/ClMax%);
Mesh.CharacteristicLengthMin = %(GmshSettings/ClMin%);

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
Physical Volume ("Internal") = {%(GmshSettings/Solids%)};

// Boundaries
%{%(GmshSettings/BoundaryFaceMap%)
Physical Surface ("%(0%)") = {%(GmshSettings/BoundaryFaceMap/%(0%)%)};
%}

// Meshing
Mesh 3;

// Save
Mesh.Format = 10; // Auto according to extension
Mesh.MshFileVersion = 2.2;

// Ignore Physical definitions and save all elements
Mesh.SaveAll = 0;

// Save in msh for OpenFOAM as its unv converter is outdated
Save "%(0%)_Geometry.msh";
%} gmsh/%(0%)_Geometry.geo
%}