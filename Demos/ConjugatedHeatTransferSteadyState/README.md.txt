# Steady-State Conjugate Heat Transfer Examples

This directory contains CfdOF examples for steady-state conjugate heat
transfer (CHT) using OpenFOAM's `chtMultiRegionSimpleFoam` solver. CHT solves
heat conduction in one or more solid regions together with heat transfer and
fluid flow in the surrounding fluid region.

CHT uses a separate mesh for each fluid and solid region. A single combined
mesh with regions inferred from compound or Boolean Fragments children is not
supported.

snappyHexMesh support for NCC CHT is deferred to a later PR. Use Gmsh for
NCC region meshes; ordinary single-region snappyHexMesh cases are unaffected.

## External Solid Boundaries

Select an external face on a solid region and choose **Solid boundary** from
the CfdOF toolbar or menu. The thermal options are fixed temperature,
adiabatic (the default), heat flux, total power, and heat transfer coefficient.
Solid boundaries do not require fluid velocity or pressure settings.

For a PCB resting on the room floor, select the underside of the generated
PCB region. Keep the exposed room floor assigned to a fluid wall. Faces
already assigned to a region-coupled interface cannot also be external solid
boundaries. After changing face assignments, regenerate the affected meshes
and rewrite the solver case.

For a prescribed-temperature fluid-solid contact, set that face pair's thermal
type to `fixedValue` in the Region-coupled interface table and enter its
temperature. Both sides become stationary walls with the specified temperature,
not thermally coupled patches. Other face pairs retain their coupling. Do not
also assign a separate Solid boundary to the same face.

## Microchip Cooling

Folder: `microchip_cooling`

This example represents a more involved electronics-cooling problem. It
contains four solid regions for the heat sink, printed circuit board,
microchip, and polymer component. Heat passes between contacting solids and
from their surfaces into the surrounding air. The microchip uses a
volumetric heat source. A mean-velocity-force cell zone drives the air
flow and acts as a simplified fan model.

![Microchip cooling result](microchip_cooling/microchip_cooling_result_paraview.png)
