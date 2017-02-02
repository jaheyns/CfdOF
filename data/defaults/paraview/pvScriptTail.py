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
