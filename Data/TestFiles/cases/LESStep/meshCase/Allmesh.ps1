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
    & mpiexec -np $NumProcs $cmd -parallel $args 2>&1 | tee log.$sol
    $err = $LASTEXITCODE
    if( ! $LASTEXITCODE -eq 0 )
    {
        exit $err
    }
}

# Set piping to file to ascii
$PSDefaultParameterValues['Out-File:Encoding'] = 'ascii'

$GMSH_EXE = "/usr/local/bin/gmsh"
$NTHREADS = (Get-CimInstance Win32_ComputerSystem).NumberOfLogicalProcessors
runCommand "$GMSH_EXE" -nt $NTHREADS - "gmsh/Pad_Geometry.geo"

runCommand gmshToFoam "gmsh/Pad_Geometry.msh"

# Convert to polyhedra
runCommand polyDualMesh 10 -concaveMultiCells -overwrite

runCommand transformPoints -scale "(0.001 0.001 0.001)"


# Extract surface mesh and convert to mm for visualisation in FreeCAD
runCommand foamToSurface -scale 1000 -tri surfaceMesh.vtk
