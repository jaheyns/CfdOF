function runCommand([string]$cmd)
{
    $sol = (Split-Path -Leaf $cmd)
    & $cmd $args 2>&1 | tee log.$sol
    $err = $LASTEXITCODE
    if( ! $LASTEXITCODE -eq 0 )
    {
        exit $err
    }
}

function runParallel([int]$NumProcs, [string]$cmd)
{
    $sol = (Split-Path -Leaf $cmd)
%{%(hostFileRequired%)
%:False
    & mpiexec %(MPIOptionsMSMPI%) -np $NumProcs $cmd -parallel $args 2>&1 | tee log.$sol
%:True
    & mpiexec %(MPIOptionsMSMPI%) --hostfile %(hostFileName%) -np $NumProcs $cmd -parallel $args 2>&1 | tee log.$sol
%}
    $err = $LASTEXITCODE
    if( ! $LASTEXITCODE -eq 0 )
    {
        exit $err
    }
}

# Set piping to file to ascii
$PSDefaultParameterValues['Out-File:Encoding'] = 'ascii'

%{%(MeshUtility%)
%:gmsh
$GMSH_EXE = "%(GmshSettings/Executable%)"
%{%(NumberOfThreads%)
%:0
#$NTHREADS = (Get-CimInstance Win32_ComputerSystem).NumberOfLogicalProcessors
# Currently default to 1 thread as the current release version of gmsh 4.13.1,
# appears to suffer from a race condition
$NTHREADS = 1
%:default
$NTHREADS = %(NumberOfThreads%)
%}
runCommand "$GMSH_EXE" -nt $NTHREADS - "gmsh/%(Name%)_Geometry.geo"

%}
%{%(ParallelMesh%)
%:True
# Pick up number of parallel processes
$NPROC = foamDictionary -entry numberOfSubdomains -value system/decomposeParDict

%}
%{%(MeshUtility%)
%:cfMesh
# Extract feature edges
runCommand surfaceFeatureEdges -angle 60 "constant/triSurface/%(Name%)_Geometry.stl" "%(Name%)_Geometry.fms"

%{%(ParallelMesh%)
%:True
%{%(NumberOfThreads%)
%:0
$Env:OMP_NUM_THREADS = 1
%:default
$Env:OMP_NUM_THREADS = %(NumberOfThreads%)
%}
runCommand preparePar
$Env:MPI_BUFFER_SIZE = 200000000
runParallel $NPROC cartesianMesh
runCommand reconstructParMesh -constant -fullMatch
%:False
%{%(NumberOfThreads%)
%:0
%:default
$Env:OMP_NUM_THREADS = %(NumberOfThreads%)
%}
runCommand cartesianMesh
%}
%:snappyHexMesh
runCommand blockMesh

# Extract feature edges
runCommand surfaceFeatureExtract

%{%(ParallelMesh%)
%:True
runCommand decomposePar
runParallel $NPROC snappyHexMesh -overwrite
runCommand reconstructParMesh -constant
%:False
runCommand snappyHexMesh -overwrite
%}
%:gmsh
runCommand gmshToFoam "gmsh/%(Name%)_Geometry.msh"

%{%(ConvertToDualMesh%)
%:True
# polyDualMesh doesn't seem to convert cell zones
rm -ErrorAction SilentlyContinue constant/polyMesh/cellZones
# Convert to polyhedra
runCommand polyDualMesh 10 -concaveMultiCells -overwrite

%}
runCommand transformPoints -scale "(0.001 0.001 0.001)"
%}

%{%(ExtrusionSettings/ExtrusionsPresent%)
%:True
%{%(ExtrusionSettings/Extrude2DPlanar%)
%:True
# Slight abuse of flattenMesh to make patch flat before extrusion
# Change patch type to empty first
%{%(ExtrusionSettings/Extrusions%)
%{%(ExtrusionSettings/Extrusions/%(0%)/ExtrusionType%)
%:2DPlanar
cp system/changeDictionaryDict.%(0%) system/changeDictionaryDict
runCommand changeDictionary
rm system/changeDictionaryDict
%}
%}
runCommand flattenMesh
%}
%{%(ExtrusionSettings/Extrusions%)
cp system/extrudeMeshDict.%(0%) system/extrudeMeshDict
%{%(ExtrusionSettings/Extrusions/%(0%)/KeepExistingMesh%)
%:False
# Refinement history is not processed by extrudeMesh
rm -ErrorAction SilentlyContinue constant/polyMesh/cellLevel
rm -ErrorAction SilentlyContinue constant/polyMesh/pointLevel
rm -ErrorAction SilentlyContinue constant/polyMesh/level0Edge
rm -ErrorAction SilentlyContinue constant/polyMesh/refinementHistory
%}
runCommand extrudeMesh
mv log.extrudeMesh log.extrudeMesh.%(0%)
rm system/extrudeMeshDict
%}

%}

# Extract surface mesh and convert to mm for visualisation in FreeCAD
runCommand foamToSurface -scale 1000 -tri surfaceMesh.vtk
