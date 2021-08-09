This is the FreeCAD fluid material library. It's intended to gather
the most common fluid properties.

(c) 2016 CSIR, South Africa
(c) 2021 Oliver Oxtoby

Please verify the fluid material properties before use. It aims to
serve as a convenience and does not aim to be a comprehensive
reference.

Each material has a Type keyword identifying the kind of modelling
it is compatible with. Only those compatible with the physics model
selected will we shown in the GUI:
- Isothermal: Denotes properties at fixed temperature and pressure,
for use in incompressible, isothermal solvers
- Incompressible: Properties modelled as dependent on temperature but
not pressure, useful for using very nearly incompressible fluids with
the low-Mach compressible solver.
- Compressible: Properties dependent on both temperature and pressure.

Current values are taken from FM White (2011) Fluid Mechanics.
