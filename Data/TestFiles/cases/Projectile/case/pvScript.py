#### import the simple module from the paraview
from paraview.simple import *
#### disable automatic camera reset on 'Show'
paraview.simple._DisableFirstRenderCameraReset()

# create a new OpenFOAMReader
pfoam = OpenFOAMReader(FileName=r'pv.foam')
pfoam.CaseType = 'Decomposed Case'
pfoam.Decomposepolyhedra = 0

# get active view
renderView1 = GetActiveViewOrCreate('RenderView')

# reset view to fit data
renderView1.ResetCamera()

# create a new 'Clean to Grid'
cleantoGrid1 = CleantoGrid(Input=pfoam)

# show data in view
cleantoGrid1Display = Show(cleantoGrid1, renderView1)

# hide data in view
Hide(pfoam, renderView1)

# get color transfer function/color map for 'U'
ULUT = GetColorTransferFunction('U')

# trace defaults for the display properties.
cleantoGrid1Display.ColorArrayName = ['POINTS', 'U']
cleantoGrid1Display.LookupTable = ULUT
cleantoGrid1Display.EdgeColor = [0.0, 0.0, 0.5]
cleantoGrid1Display.ScalarOpacityUnitDistance = 0.05

# get animation scene
animationScene1 = GetAnimationScene()

# update animation scene based on data timesteps
animationScene1.UpdateAnimationUsingDataTimeSteps()

# go to the final timestep of the simulation
timesteps = pfoam.TimestepValues
finalTime =  timesteps[-1]
animationScene1.AnimationTime = finalTime

# rescale color and/or opacity maps used to exactly fit the current data range
cleantoGrid1Display.RescaleTransferFunctionToDataRange(False, True)

# update the view to ensure updated data information
renderView1.Update()

# reset view to fit data
renderView1.ResetCamera(False)

