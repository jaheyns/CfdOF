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

# Extract feature edges
runCommand surfaceFeatureEdges -angle 60 "constant/triSurface/Compound001_Geometry.stl" "Compound001_Geometry.fms"

runCommand cartesianMesh


# Extract surface mesh and convert to mm for visualisation in FreeCAD
runCommand foamToSurface -scale 1000 -tri surfaceMesh.vtk
