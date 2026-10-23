%{%(multiRegionEnabled%)
%:True
#!/usr/bin/env python3

import glob
import os
import re


PARALLEL = False
%{%(solver/Parallel%)
%:True
PARALLEL = True
%}


def read_regions():
    with open(os.path.join("constant", "regionProperties")) as fid:
        contents = fid.read()
    fluid_match = re.search(r"fluid\s*\(\s*([^)]*?)\s*\)", contents)
    solid_match = re.search(r"solid\s*\(\s*([^)]*?)\s*\)", contents)
    fluid_regions = fluid_match.group(1).split() if fluid_match else []
    solid_regions = solid_match.group(1).split() if solid_match else []
    return fluid_regions, solid_regions


def boundary_file(region):
    return os.path.join("constant", region, "polyMesh", "boundary")


def update_sample_mode(path):
    sample_mode = os.environ.get("CFDOF_MAPPED_WALL_SAMPLE_MODE", "nearestPatchFaceAMI")
    with open(path) as fid:
        contents = fid.read()
    contents = re.sub(r"sampleMode\s+\w+\s*;", "sampleMode      " + sample_mode + ";", contents)
    with open(path, "w") as fid:
        fid.write(contents)


def patch_names(path, mapped):
    with open(path) as fid:
        contents = fid.read()
    all_patches = re.findall(r"\n\s+([A-Za-z_][A-Za-z0-9_]*)\s*\n\s*\{", contents)
    mapped_patches = set(re.findall(
        r"\n\s+([A-Za-z_][A-Za-z0-9_]*)\s*\n\s*\{[^}]*type\s+mappedWall",
        contents,
    ))
    if mapped:
        return [name for name in all_patches if name in mapped_patches]
    return [name for name in all_patches if name not in mapped_patches]


def has_patch(contents, patch):
    return bool(re.search(r"\n\s+" + re.escape(patch) + r"\s*\n\s*\{", contents))


def add_patch_entry(path, patch, lines):
    with open(path) as fid:
        contents = fid.read()
    if has_patch(contents, patch):
        return

    entry = "\n    " + patch + "\n    {\n"
    entry += "".join("        " + line + "\n" for line in lines)
    entry += "    }\n"
    closing_braces = list(re.finditer(r"\n}", contents))
    if not closing_braces:
        raise RuntimeError("No boundaryField closing brace found in '{}'".format(path))
    position = closing_braces[-1].start() + 1
    contents = contents[:position] + entry + contents[position:]
    with open(path, "w") as fid:
        fid.write(contents)


def add_interface_fields(region, patches, is_fluid):
    field_dir = os.path.join("0", region)
    if not os.path.isdir(field_dir):
        return
    for patch in patches:
        for path in glob.glob(os.path.join(field_dir, "*")):
            field = os.path.basename(path)
            if field == "T":
                kappa = "fluidThermo" if is_fluid else "solidThermo"
                add_patch_entry(path, patch, [
                    "type            compressible::turbulentTemperatureCoupledBaffleMixed;",
                    "value           $internalField;",
                    "Tnbr            T;",
                    "kappaMethod     " + kappa + ";",
                ])
            elif field == "U" and is_fluid:
                add_patch_entry(path, patch, ["type            noSlip;"])
            elif field == "p_rgh" and is_fluid:
                add_patch_entry(path, patch, [
                    "type            fixedFluxPressure;",
                    "value           $internalField;",
                ])
            elif field == "p":
                add_patch_entry(path, patch, [
                    "type            calculated;",
                    "value           $internalField;",
                ])
            elif field == "nut" and is_fluid:
                add_patch_entry(path, patch, [
                    "type            nutkWallFunction;",
                    "value           $internalField;",
                ])
            elif field in ("k", "epsilon", "omega", "nuTilda", "alphat") and is_fluid:
                add_patch_entry(path, patch, ["type            zeroGradient;"])


def add_default_solid_fields(region, patches):
    field_dir = os.path.join("0", region)
    if not os.path.isdir(field_dir):
        return
    for patch in patches:
        for path in glob.glob(os.path.join(field_dir, "*")):
            field = os.path.basename(path)
            if field == "T":
                add_patch_entry(path, patch, ["type            zeroGradient;"])
            elif field == "p":
                add_patch_entry(path, patch, [
                    "type            calculated;",
                    "value           $internalField;",
                ])


def main():
    fluid_regions, solid_regions = read_regions()
    for region in fluid_regions + solid_regions:
        path = boundary_file(region)
        if PARALLEL and os.path.isfile(path):
            update_sample_mode(path)

    for region in fluid_regions:
        path = boundary_file(region)
        if os.path.isfile(path):
            add_interface_fields(region, patch_names(path, mapped=True), is_fluid=True)
    for region in solid_regions:
        path = boundary_file(region)
        if not os.path.isfile(path):
            continue
        add_interface_fields(region, patch_names(path, mapped=True), is_fluid=False)
        add_default_solid_fields(region, patch_names(path, mapped=False))


if __name__ == "__main__":
    main()
%}
