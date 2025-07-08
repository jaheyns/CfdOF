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
    & mpiexec -affinity -affinity_layout spr:P:L -np $NumProcs $cmd -parallel $args 2>&1 | tee log.$sol
    $err = $LASTEXITCODE
    if( ! $LASTEXITCODE -eq 0 )
    {
        exit $err
    }
}

# Set piping to file to ascii
$PSDefaultParameterValues['Out-File:Encoding'] = 'ascii'

$GMSH_EXE = "/home/oliver/software/gmsh-4.13.1-Linux64/bin/gmsh"
#$NTHREADS = (Get-CimInstance Win32_ComputerSystem).NumberOfLogicalProcessors
# Currently default to 1 thread as the current release version of gmsh 4.13.1,
# appears to suffer from a race condition
$NTHREADS = 1
runCommand "$GMSH_EXE" -nt $NTHREADS - "gmsh/Pad_Geometry.geo"

runCommand gmshToFoam "gmsh/Pad_Geometry.msh"

# polyDualMesh doesn't seem to convert cell zones
rm -ErrorAction SilentlyContinue constant/polyMesh/cellZones
# Convert to polyhedra
runCommand polyDualMesh 10 -concaveMultiCells -overwrite

runCommand transformPoints -scale "(0.001 0.001 0.001)"


# Extract surface mesh and convert to mm for visualisation in FreeCAD
runCommand foamToSurface -scale 1000 -tri surfaceMesh.vtk
