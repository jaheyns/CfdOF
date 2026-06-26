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

if( (Get-Command -ErrorAction SilentlyContinue createNonConformalCouples) )
{
    echo "mode inside;" > system/MMR_Properties
}
else
{
    echo "faceType boundary;" > system/MMR_Properties
    echo "cellZoneInside inside;" >> system/MMR_Properties
}

runCommand snappyHexMesh -overwrite
if ( (Get-Command -ErrorAction SilentlyContinue createNonConformalCouples) )
{
	runCommand createBaffles -overwrite
	runCommand splitBaffles -overwrite
	runCommand createNonConformalCouples -overwrite MeshRefinement_M MeshRefinement_S
	mv log.createNonConformalCouples log.createNonConformalCouplesMeshRefinement
}
else
{
	runCommand createPatch -overwrite
}


# Extract surface mesh and convert to mm for visualisation in FreeCAD
runCommand foamToSurface -scale 1000 -tri surfaceMesh.vtk
