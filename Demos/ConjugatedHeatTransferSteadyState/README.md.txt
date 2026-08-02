# Steady-State Conjugate Heat Transfer Examples

This directory contains two CfdOF examples for steady-state conjugate heat
transfer (CHT) using OpenFOAM's `chtMultiRegionSimpleFoam` solver. CHT solves
heat conduction in one or more solid regions together with heat transfer and
fluid flow in the surrounding fluid region.

## Simple Heat Fin

Folder: `simple_heat_fin`

This example contains one aluminium solid region surrounded by
air. Heat conducts through the fin and is transferred to the air, producing a
steady temperature distribution and buoyancy-driven flow. The case uses a
laminar flow model and demonstrates:


![screenshot](simple_heat_fin/simple_heat_fin_result_paraview.png)

## Microchip Cooling

Folder: `microchip_cooling`

This example represents a more involved electronics-cooling problem. It
contains four solid regions for the heat sink, printed circuit board,
microchip, and polymer component. Heat passes between contacting solids and
from their surfaces into the surrounding air. The microchip uses a
volumetric heat source. A mean-velocity-force cell zone drives the air
flow and acts as a simplified fan model.

![Microchip cooling result](microchip_cooling/microchip_cooling_result_paraview.png)
