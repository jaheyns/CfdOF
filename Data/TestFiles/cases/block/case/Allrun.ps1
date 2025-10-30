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
$ErrorView = 'CategoryView'

# Copy mesh from mesh case dir if available
$MESHDIR = "../meshCaseblock"
if( Test-Path -PathType Leaf $MESHDIR/constant/polyMesh/faces )
{
    rm -ErrorAction SilentlyContinue -Recurse -Force constant/polyMesh
    cp -Recurse $MESHDIR/constant/polyMesh constant/polyMesh
}
elseif( !(Test-Path -PathType Leaf constant/polyMesh/faces) )
{
    Write-Error "Fatal error: Unable to find mesh in directory $MESHDIR"
    exit 1
}

# Set turbulence lib
if ( $Env:WM_PROJECT_VERSION[0] -eq "v" -or 10 -gt $Env:WM_PROJECT_VERSION )
{
    echo '"libturbulenceModels"' > system/turbulenceLib
}
else
{
    echo '"libmomentumTransportModels"' > system/turbulenceLib
}

# Set interface compression
echo "div(phi,alpha) Gauss vanLeer;" > system/alphaDivScheme
echo "cAlpha 1;" > system/cAlpha

# Update patch name and type
runCommand createPatch -overwrite

$PNAME = "p"

# Mesh renumbering
runCommand renumberMesh -overwrite

# Initialise flow
runCommand potentialFoam -initialiseUBCs -pName $PNAME -writep

# Run application
# Detect new foamRun in Foundation versions >= 11 and translate solver
if( (Get-Command foamRun) )
{
    runCommand foamRun -solver incompressibleFluid
}
else
{
    runCommand simpleFoam
}
