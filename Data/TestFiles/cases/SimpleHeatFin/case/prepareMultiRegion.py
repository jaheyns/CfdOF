#!/usr/bin/env python3

import glob
import os
import re
import shutil
import subprocess
import sys


PARALLEL = False
PARALLEL = True

REGION_MESHES = [
    ("", "None"),
]

COUPLES = [
    ("None",
     "None",
     "None",
     "None"),
]


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


def copy_region_meshes():
    for region, mesh_dir in REGION_MESHES:
        source = os.path.join(mesh_dir, "constant", "polyMesh")
        destination = os.path.join("constant", region, "polyMesh")
        if not os.path.isdir(source):
            raise RuntimeError(
                "Mesh for region '{}' was not found at '{}'. Run that region's Allmesh first.".format(
                    region, source
                )
            )
        if os.path.isdir(destination):
            shutil.rmtree(destination)
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        shutil.copytree(source, destination)

        global_gravity = os.path.join("constant", "g")
        if os.path.isfile(global_gravity):
            with open(global_gravity) as fid:
                gravity = fid.read()
            gravity = re.sub(
                r'location\s+"constant"\s*;',
                'location    "constant/' + region + '";',
                gravity,
            )
            with open(os.path.join("constant", region, "g"), "w") as fid:
                fid.write(gravity)


def create_patch_blocks(contents):
    patches_match = re.search(r"\npatches\s*\(", contents)
    if not patches_match:
        return []
    blocks = []
    index = patches_match.end()
    depth = 0
    start = None
    while index < len(contents):
        character = contents[index]
        if character == "{":
            if depth == 0:
                start = index
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0 and start is not None:
                blocks.append(contents[start:index + 1])
                start = None
        elif character == ")" and depth == 0:
            break
        index += 1
    return blocks


def block_matches_patches(block, names):
    match = re.search(r"\n\s*patches\s*\((.*?)\)\s*;", block, re.S)
    if not match:
        return False
    patterns = re.findall(r'"([^"]+)"|([A-Za-z0-9_.*+-]+)', match.group(1))
    return any(
        re.fullmatch(quoted or unquoted, name)
        for quoted, unquoted in patterns
        for name in names
    )


def write_region_create_patch_dict(region):
    global_dict = os.path.join("system", "createPatchDict")
    with open(global_dict) as fid:
        contents = fid.read()
    with open(boundary_file(region)) as fid:
        boundary = fid.read()
    names = set(re.findall(r"\n\s*([A-Za-z_][A-Za-z0-9_]*)\s*\n\s*\{", boundary))
    patches_match = re.search(r"\npatches\s*\(", contents)
    if not patches_match:
        raise RuntimeError("No patches list found in '{}'".format(global_dict))
    blocks = [
        block for block in create_patch_blocks(contents)
        if block_matches_patches(block, names)
    ]
    system_dir = os.path.join("system", region)
    os.makedirs(system_dir, exist_ok=True)
    region_dict = os.path.join(system_dir, "createPatchDict")
    with open(region_dict, "w") as fid:
        fid.write(contents[:patches_match.start()])
        fid.write("\npatches\n(\n")
        for block in blocks:
            fid.write(block + "\n")
        fid.write(");\n\n// ************************************************************************* //\n")
    return os.path.abspath(region_dict)


def create_region_patches():
    for region, _mesh_dir in REGION_MESHES:
        region_dict = write_region_create_patch_dict(region)
        subprocess.check_call([
            "createPatch", "-region", region, "-dict", region_dict, "-overwrite"
        ])


def replace_patch_block(contents, patch, neighbour_region, neighbour_patch):
    sample_mode = os.environ.get("CFDOF_MAPPED_WALL_SAMPLE_MODE", "nearestPatchFaceAMI")
    pattern = re.compile(
        r"(\n\s*" + re.escape(patch) + r"\s*\n\s*\{)(.*?)(\n\s*\})",
        re.S,
    )
    match = pattern.search(contents)
    if not match:
        raise RuntimeError("Patch '{}' was not found in boundary file".format(patch))
    body = match.group(2)
    for keyword in ("type", "sampleMode", "sampleRegion", "samplePatch"):
        body = re.sub(r"\n\s*" + keyword + r"\s+\w+\s*;", "", body)
    body = (
        "\n        type            mappedWall;"
        "\n        sampleMode      " + sample_mode + ";"
        "\n        sampleRegion    " + neighbour_region + ";"
        "\n        samplePatch     " + neighbour_patch + ";" + body
    )
    return contents[:match.start()] + match.group(1) + body + match.group(3) + contents[match.end():]


def couple_region_patches():
    if not COUPLES:
        raise RuntimeError("Multi-mesh CHT requires at least one region-coupled wall pair")
    for master_region, master_patch, slave_region, slave_patch in COUPLES:
        for region, patch, neighbour_region, neighbour_patch in (
            (master_region, master_patch, slave_region, slave_patch),
            (slave_region, slave_patch, master_region, master_patch),
        ):
            path = boundary_file(region)
            with open(path) as fid:
                contents = fid.read()
            contents = replace_patch_block(contents, patch, neighbour_region, neighbour_patch)
            with open(path, "w") as fid:
                fid.write(contents)


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
    if len(sys.argv) > 1:
        if sys.argv[1] != "meshes":
            raise ValueError("Unknown preparation stage '{}'".format(sys.argv[1]))
        copy_region_meshes()
        create_region_patches()
        couple_region_patches()
        return

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
