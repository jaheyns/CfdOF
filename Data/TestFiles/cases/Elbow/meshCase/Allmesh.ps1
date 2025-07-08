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
runCommand surfaceFeatureEdges -angle 60 "constant/triSurface/Pad_Geometry.stl" "Pad_Geometry.fms"

runCommand cartesianMesh

# Slight abuse of flattenMesh to make patch flat before extrusion
# Change patch type to empty first
cp system/changeDictionaryDict.0 system/changeDictionaryDict
runCommand changeDictionary
rm system/changeDictionaryDict
runCommand flattenMesh
cp system/extrudeMeshDict.0 system/extrudeMeshDict
# Refinement history is not processed by extrudeMesh
rm -ErrorAction SilentlyContinue constant/polyMesh/cellLevel
rm -ErrorAction SilentlyContinue constant/polyMesh/pointLevel
rm -ErrorAction SilentlyContinue constant/polyMesh/level0Edge
rm -ErrorAction SilentlyContinue constant/polyMesh/refinementHistory
runCommand extrudeMesh
mv log.extrudeMesh log.extrudeMesh.0
rm system/extrudeMeshDict


# Extract surface mesh and convert to mm for visualisation in FreeCAD
runCommand foamToSurface -scale 1000 -tri surfaceMesh.vtk
