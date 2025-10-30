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

# Less verbose error reporting
$ErrorView = 'ConciseView'

# Pick up number of parallel processes
$NPROC = foamDictionary -entry numberOfSubdomains -value system/decomposeParDict

runCommand blockMesh

# Extract feature edges
if ( Get-Command -ErrorAction SilentlyContinue surfaceFeatures )
{
    runCommand surfaceFeatures
}
else
{
    runCommand surfaceFeatureExtract
}

runCommand decomposePar -force
runParallel $NPROC snappyHexMesh -overwrite
if ( $Env:WM_PROJECT_VERSION[0] -eq "v" -or 11 -gt $Env:WM_PROJECT_VERSION )
{
    runCommand reconstructParMesh -constant
}
else
{
    runCommand reconstructPar -constant
}


# Extract surface mesh and convert to mm for visualisation in FreeCAD
runCommand foamToSurface -scale 1000 -tri surfaceMesh.vtk
