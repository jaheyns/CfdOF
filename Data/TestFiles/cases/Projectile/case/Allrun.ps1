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

# Copy mesh from mesh case dir if available
$MESHDIR = "../meshCaseProjectile"
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
echo "libturbulenceModels.so" > system/turbulenceLib

# Update patch name and type
runCommand createPatch -overwrite

# Parallel decomposition
if( !(Test-Path -PathType Container processor0) )
{
    runCommand decomposePar -force
}

# Pick up number of parallel processes
$NPROC = foamDictionary -entry "numberOfSubdomains" -value system/decomposeParDict

# Mesh renumbering
runParallel $NPROC renumberMesh -overwrite

# Run application in parallel
runParallel $NPROC hisa
