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
%{%(system/hostFileRequired%)
%:False
    & mpiexec %(system/MPIOptionsMSMPI%) -np $NumProcs $cmd -parallel $args 2>&1 | tee log.$sol
%:True
    & mpiexec %(system/MPIOptionsMSMPI%) --hostfile %(system/hostFileName%) -np $NumProcs $cmd -parallel $args 2>&1 | tee log.$sol
%}
    $err = $LASTEXITCODE
    if( ! $LASTEXITCODE -eq 0 )
    {
        exit $err
    }
}

# Set piping to file to ascii
$PSDefaultParameterValues['Out-File:Encoding'] = 'ascii'

# Copy mesh from mesh case dir if available
$MESHDIR = "%(meshDir%)"
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

%{%(dynamicMeshEnabled%)
%:True
# Set 'internal' patch type
mkdir 0/include
echo "type fixedValue;" > 0/include/helperPatchFieldType
echo "type patch;" > system/helperPatchType

%}
# Update patch name and type
runCommand createPatch -overwrite

%{%(zonesPresent%)
%:True
# Set cell zones contained inside the .stl surfaces
runCommand topoSet -dict system/topoSetZonesDict

%}
%{%(initialisationZonesPresent%)
%:True
# Set internal fields according to setFieldsDict
runCommand setFields

%}
%{%(bafflesPresent%)
%:True
%{%(createPatchesFromSnappyBaffles%)
%:False
# Combine mesh faceZones
runCommand topoSet -dict system/topoSetBafflesDict

# Creating baffles
runCommand createBaffles -overwrite

%}
%}
%{%(runChangeDictionary%)
%:True
# Update patch name and type
runCommand changeDictionary

%}
%{%(initialValues/PotentialFlow%)
%:True
%{%(solver/SolverName%)
%:buoyantSimpleFoam buoyantPimpleFoam interFoam multiphaseInterFoam
$PNAME = "p_rgh"
%:default
$PNAME = "p"
%}

%}
%{%(solver/Parallel%)
%:True
# Parallel decomposition
if( !(Test-Path -PathType Container processor0) )
{
    runCommand decomposePar -force
}

# Pick up number of parallel processes
$NPROC = foamDictionary -entry "numberOfSubdomains" -value system/decomposeParDict

%{%(dynamicMeshEnabled%)
%:False
# Mesh renumbering
runParallel $NPROC renumberMesh -overwrite
%:True
# Mesh renumbering does not work in Foundation with dynamic mesh
# runParallel $NPROC renumberMesh -overwrite
%}

%{%(initialValues/PotentialFlow%)
%:True
# Initialise flow
%{%(bafflesPresent%)
%:True
# Baffle BC does not work with potentialFoam; do not initialise p
runParallel $NPROC potentialFoam -initialiseUBCs -pName $PNAME
%:default
%{%(initialValues/PotentialFlowP%)
%:True
runParallel $NPROC potentialFoam -initialiseUBCs -pName $PNAME -writep
%:default
runParallel $NPROC potentialFoam -initialiseUBCs -pName $PNAME
%}
%}
%{%(solver/SolverName%)
%:buoyantSimpleFoam buoyantPimpleFoam interFoam multiphaseInterFoam
# Remove phi with wrong units
rm -ErrorAction SilentlyContinue processor*/0/phi
%}

%}
# Run application in parallel
runParallel $NPROC %(solver/SolverName%)
%:False
%{%(dynamicMeshEnabled%)
%:False
# Mesh renumbering
runCommand renumberMesh -overwrite
%:True
# Mesh renumbering does not currently work in Foundation with dynamic mesh
# runCommand renumberMesh -overwrite
%}

%{%(initialValues/PotentialFlow%)
%:True
# Initialise flow
%{%(bafflesPresent%)
%:True
# Baffle BC does not work with potentialFoam; do not initialise p
runCommand potentialFoam -initialiseUBCs -pName $PNAME
%:default
%{%(initialValues/PotentialFlowP%)
%:True
runCommand potentialFoam -initialiseUBCs -pName $PNAME -writep
%:default
runCommand potentialFoam -initialiseUBCs -pName $PNAME
%}
%}
%{%(solver/SolverName%)
%:buoyantSimpleFoam buoyantPimpleFoam interFoam multiphaseInterFoam
# Remove phi with wrong units
rm -ErrorAction SilentlyContinue 0/phi
%}

%}
# Run application
runCommand %(solver/SolverName%)
%}
