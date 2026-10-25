<!-- SPDX-FileCopyrightText: © 2026 Kavin Teenakul <andythe_great@protonmail.com> -->

# Microchip Cooling NCC

Steady-state CHT setup with independently meshed room, PCB, microchip, heat sink
and fan-case regions. The microchip has a volumetric heat source, and a
mean-velocity-force zone drives the air flow.

## Workflow

Run `00-RunAll.FCMacro` in FreeCAD with CfdOF loaded, or run the numbered macros
in order:

1. `01-geometry.FCMacro`: create the five original region shapes. The heat sink
   is a fusion of its base and fins. No BooleanFragments object is created.
2. `02-analysis.FCMacro`: configure steady-state physics, air, initial fields
   and solver settings.
3. `03-meshes.FCMacro`: clone the source shapes through CfdOF's interface-region
   generation, retain the Slice/Cut history, and create five Gmsh mesh objects.
   The original source shapes are hidden for the final view, not modified.
4. `04-boundaries.FCMacro`: assign the room's external pressure opening and the
   adiabatic PCB underside where it touches the room floor.
5. `05-solidMaterials.FCMacro`: assign material properties to the generated solid
   regions and set the microchip heat source.
6. `06-meanVelocityForce.FCMacro`: configure the simplified fan forcing.

Select each region mesh and generate its mesh, then write and run the solver
case. Use a different mesh-case directory for each mesh, as configured by the
macros. Select the desired installed OpenFOAM environment in CfdOF preferences;
the macros do not select version-specific dictionary formats.

## Simulation Setup

The interface selection includes all five regions, with coupled fluid-solid and
solid-solid contacts. All six external room faces use a total-pressure opening
at 100 kPa and 293 K. The PCB rests on the room floor; its exposed underside has
a separate zero-gradient solid thermal boundary.

The PCB is acrylic, the microchip brass, the heat sink aluminium, and the fan
case polypropylene. The microchip heat generation is 300 MW/m^3 (270 W total).
A cylindrical fan zone of radius 12 mm and height 10 mm inside the fan case
targets a mean velocity of 0.5 m/s in the positive Z direction, with relaxation
0.2. Gravity acts in negative Z at 9.81 m/s^2.

All regions use Gmsh. Maximum element sizes are 3.9395 mm for the room, 0.4 mm for
the PCB and microchip, 0.8818 mm for the heat sink, and 0.8718 mm for the fan case.
Initial temperature is 293 K, with potential-flow initialization enabled. The
steady solver uses six processes, up to 2000 iterations, a convergence tolerance
of 0.001, and output every 100 iterations.

NCC snappyHexMesh support is deferred; this demo uses Gmsh. One-step smoke solves
validate startup, not convergence or the physical accuracy of a cooling result.

The reference setup has passed meshing and a one-iteration parallel solve with
OpenFOAM.com 2606. With Foundation 14, the same mesh settings currently fail the
default mapped-wall geometric matching tolerance on a room-to-heat-sink pair.
No tolerance override or mesh-size adjustment is included in the demo.
