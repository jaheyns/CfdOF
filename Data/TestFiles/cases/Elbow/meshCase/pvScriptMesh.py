#### import the simple module from the paraview
from paraview.simple import *
#### disable automatic camera reset on 'Show'
paraview.simple._DisableFirstRenderCameraReset()

# create a new OpenFOAMReader
pfoam = OpenFOAMReader(FileName=r'pv.foam')
pfoam.CaseType = 'Reconstructed Case'
pfoam.Decomposepolyhedra = 0

# get active view
renderView1 = GetActiveViewOrCreate('RenderView')

# reset view to fit data
renderView1.ResetCamera()

# show data in view
pfoamDisplay = Show(pfoam, renderView1)
# trace defaults for the display properties.
pfoamDisplay.ColorArrayName = [None, '']
#pfoamDisplay.LookupTable = pLUT
pfoamDisplay.EdgeColor = [0.0, 0.0, 0.5]

# change representation type
pfoamDisplay.SetRepresentationType('Surface With Edges')

# Properties modified on pfoamDisplay
#pfoamDisplay.Opacity = 0.5

# create a new 'Extract Cells By Region'
extractCellsByRegion1 = ExtractCellsByRegion(Input=pfoam)
extractCellsByRegion1.IntersectWith.Normal = [1.0, 1.0, 1.0]

# show data in view
extractCellsByRegion1Display = Show(extractCellsByRegion1, renderView1)
# trace defaults for the display properties.
extractCellsByRegion1Display.ColorArrayName = [None, '']
extractCellsByRegion1Display.EdgeColor = [0.0, 0.0, 0.5]

# Properties modified on extractCellsByRegion1
extractCellsByRegion1.Extractonlyintersected = 1
extractCellsByRegion1.Extractintersected = 1

# change representation type
extractCellsByRegion1Display.SetRepresentationType('Surface With Edges')

SetActiveSource(pfoam)

# reset view to fit data
renderView1.ResetCamera()
