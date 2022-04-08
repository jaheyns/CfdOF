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

# get color transfer function/color map for 'p'
ULUT = GetColorTransferFunction('U')

# show data in view
pfoamDisplay = Show(pfoam, renderView1)
# trace defaults for the display properties.
pfoamDisplay.ColorArrayName = ['POINTS', 'U']
pfoamDisplay.LookupTable = ULUT
pfoamDisplay.EdgeColor = [0.0, 0.0, 0.5]
pfoamDisplay.ScalarOpacityUnitDistance = 0.05

# reset view to fit data
renderView1.ResetCamera()

# get animation scene
animationScene1 = GetAnimationScene()

# update animation scene based on data timesteps
animationScene1.UpdateAnimationUsingDataTimeSteps()

# go to the final timestep of the simulation
timesteps = pfoam.TimestepValues
finalTime =  timesteps[-1]
animationScene1.AnimationTime = finalTime

# rescale color and/or opacity maps used to exactly fit the current data range
pfoamDisplay.RescaleTransferFunctionToDataRange(False, True)

# update the view to ensure updated data information
renderView1.Update()