#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2015 - Qingfeng Xia @iesensor.com                 *
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   This program is distributed in the hope that it will be useful,       *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Library General Public License for more details.                  *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with this program; if not, write to the Free Software   *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************

App.newDocument("Unnamed")
App.setActiveDocument("Unnamed")
App.ActiveDocument=App.getDocument("Unnamed")
Gui.ActiveDocument=Gui.getDocument("Unnamed")
#
Gui.activateWorkbench("PartWorkbench")
App.ActiveDocument.addObject("Part::Cylinder","Cylinder")
App.ActiveDocument.ActiveObject.Label = "Cylinder"
App.ActiveDocument.getObject("Cylinder").Radius = '5 mm'
App.ActiveDocument.getObject("Cylinder").Height = '20 mm'
App.ActiveDocument.recompute()
Gui.SendMsgToActiveView("ViewFit")
Gui.activateWorkbench("FemWorkbench")
#
mesh_obj = App.activeDocument().addObject('Fem::FemMeshShapeNetgenObject', 'Cylinder_Mesh')
App.activeDocument().ActiveObject.Shape = App.activeDocument().Cylinder
Gui.activeDocument().setEdit(App.ActiveDocument.ActiveObject.Name)
Gui.activeDocument().resetEdit()
#
import FemGui
import CaeAnalysis
analysis_obj = CaeAnalysis._CreateCaeAnalysis('OpenFOAM', 'OpenFOAMAnalysis')
analysis_obj.Member = analysis_obj.Member  + [mesh_obj]
Gui.getDocument("Unnamed").getObject("Cylinder_Mesh").Visibility=False
Gui.getDocument("Unnamed").getObject("Cylinder").Visibility=True
#copy and paste the code above, nesh must be generated in TaskPanel
# uncheck the "second order" checkbox to gen mesh, also use the very fine mesh
#################################################
import FemMaterial
FemMaterial.makeFemMaterial('Fluid')
App.activeDocument().OpenFOAMAnalysis.Member = App.activeDocument().OpenFOAMAnalysis.Member + [App.ActiveDocument.ActiveObject]
Gui.activeDocument().setEdit(App.ActiveDocument.ActiveObject.Name)
###############################################
Gui.getDocument("Unnamed").getObject("Cylinder").Visibility=True
Gui.getDocument("Unnamed").getObject("OpenFOAM").WorkingDir = "/tmp/"
#
App.activeDocument().addObject("Fem::FluidBoundary","FluidBoundary")
App.activeDocument().OpenFOAMAnalysis.Member = App.activeDocument().OpenFOAMAnalysis.Member + [App.activeDocument().FluidBoundary]
App.ActiveDocument.recompute()
Gui.activeDocument().setEdit('FluidBoundary')
App.ActiveDocument.FluidBoundary.BoundaryType = 'outlet'
App.ActiveDocument.FluidBoundary.Subtype = 'totalPressure'
App.ActiveDocument.FluidBoundary.BoundaryValue = 0.000000
App.ActiveDocument.FluidBoundary.Direction = None
App.ActiveDocument.FluidBoundary.ThermalBoundaryType = 'zeroGradient'
App.ActiveDocument.FluidBoundary.TemperatureValue = 0.000000
App.ActiveDocument.FluidBoundary.HeatFluxValue = 0.000000
App.ActiveDocument.FluidBoundary.HTCoeffValue = 0.000000
App.ActiveDocument.FluidBoundary.References = [(App.ActiveDocument.Cylinder,"Face2")]
App.ActiveDocument.recompute()
Gui.activeDocument().resetEdit()
#
App.activeDocument().addObject("Fem::FluidBoundary","FluidBoundary001")
App.activeDocument().OpenFOAMAnalysis.Member = App.activeDocument().OpenFOAMAnalysis.Member + [App.activeDocument().FluidBoundary001]
App.ActiveDocument.recompute()
Gui.activeDocument().setEdit('FluidBoundary001')
App.ActiveDocument.FluidBoundary001.BoundaryType = 'inlet'
App.ActiveDocument.FluidBoundary001.Subtype = 'uniformVelocity'
App.ActiveDocument.FluidBoundary001.BoundaryValue = 1.000000
App.ActiveDocument.FluidBoundary001.Direction = None
App.ActiveDocument.FluidBoundary001.ThermalBoundaryType = 'zeroGradient'
App.ActiveDocument.FluidBoundary001.TemperatureValue = 0.000000
App.ActiveDocument.FluidBoundary001.HeatFluxValue = 0.000000
App.ActiveDocument.FluidBoundary001.HTCoeffValue = 0.000000
App.ActiveDocument.FluidBoundary001.References = [(App.ActiveDocument.Cylinder,"Face3")]
App.ActiveDocument.recompute()
Gui.activeDocument().resetEdit()
#
App.activeDocument().addObject("Fem::FluidBoundary","FluidBoundary002")
App.activeDocument().OpenFOAMAnalysis.Member = App.activeDocument().OpenFOAMAnalysis.Member + [App.activeDocument().FluidBoundary002]
App.ActiveDocument.recompute()
Gui.activeDocument().setEdit('FluidBoundary002')
App.ActiveDocument.FluidBoundary002.BoundaryType = 'wall'
App.ActiveDocument.FluidBoundary002.Subtype = 'fixed'
App.ActiveDocument.FluidBoundary002.BoundaryValue = 0.000000
App.ActiveDocument.FluidBoundary002.Direction = None
App.ActiveDocument.FluidBoundary002.ThermalBoundaryType = 'zeroGradient'
App.ActiveDocument.FluidBoundary002.TemperatureValue = 0.000000
App.ActiveDocument.FluidBoundary002.HeatFluxValue = 0.000000
App.ActiveDocument.FluidBoundary002.HTCoeffValue = 0.000000
App.ActiveDocument.FluidBoundary002.References = [(App.ActiveDocument.Cylinder,"Face1")]
App.ActiveDocument.recompute()
Gui.activeDocument().resetEdit()
#
############################################################
#
# must generate mesh in GUI dialog, or the mesh_obj is empty without cells
# CFD mesh must NOT second-order, or optimized, so untick those checkboxes in GUI
#
import FoamCaseWriter
writer = FoamCaseWriter.FoamCaseWriter(App.activeDocument().OpenFOAMAnalysis)
writer.write_case()