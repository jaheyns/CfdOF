#### import the simple module from the paraview
from paraview.simple import *
#### disable automatic camera reset on 'Show'
paraview.simple._DisableFirstRenderCameraReset()

# create a new OpenFOAMReader
pfoam = OpenFOAMReader(FileName=r'%(system/CasePath%)/pv.foam')
%{%(solver/Parallel%)
%:True
pfoam.CaseType = 'Decomposed Case'
%:False
pfoam.CaseType = 'Reconstructed Case'
%}
pfoam.Decomposepolyhedra = 0

# get active view
renderView1 = GetActiveViewOrCreate('RenderView')

# get color transfer function/color map for 'p'
pLUT = GetColorTransferFunction('p')

# show data in view
pfoamDisplay = Show(pfoam, renderView1)
# trace defaults for the display properties.
pfoamDisplay.ColorArrayName = ['CELLS', 'p']
pfoamDisplay.LookupTable = pLUT
pfoamDisplay.EdgeColor = [0.0, 0.0, 0.5]
pfoamDisplay.ScalarOpacityUnitDistance = 0.05

# reset view to fit data
renderView1.ResetCamera()
