%{
// Created by CfdOF for surface triangulation using GMSH

// Open brep geometry
Merge "%(Name%).brep";

// Mesh order
Mesh.ElementOrder = 1;

// 2D mesh algorithm (1=MeshAdapt, 2=Automatic, 5=Delaunay, 6=Frontal, 7=BAMG, 8=DelQuad)
Mesh.Algorithm = 2;

// Number of elements from 2*pi radians
// Used when remeshing
Mesh.MeshSizeFromCurvature = %(AngularMeshDensity%);

// Meshing
Mesh 2;

// Save
Mesh.Format = 10; // Auto according to extension

// Ignore Physical definitions and save all elements
Mesh.SaveAll = 1;

Mesh.ScalingFactor = %(ScalingFactor%);

Save "%(OutputFileName%)";
%} %(Name%).geo
