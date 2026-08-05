# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileNotice: Part of the CfdOF addon.

import os

import FreeCAD
from CfdOF import CfdTools
from CfdOF.CfdTools import addObjectProperty

if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore, QtGui

QT_TRANSLATE_NOOP = FreeCAD.Qt.QT_TRANSLATE_NOOP

GENERATED_BY = "CfdOF_InterfaceNccRegions"
REGION_ROLE_FLUID = "Fluid"
REGION_ROLE_SOLID = "Solid"
REGION_ROLES = (REGION_ROLE_FLUID, REGION_ROLE_SOLID)


def _safe_name(label):
    safe = ''.join(c if c.isalnum() else '_' for c in str(label)).strip('_')
    return safe or "Region"


def _normalise_link_sub_reference(reference):
    if isinstance(reference, (tuple, list)) and len(reference) == 2:
        ref_obj, subnames = reference
    else:
        ref_obj, subnames = reference, ()
    if isinstance(subnames, str):
        subnames = (subnames,)
    else:
        subnames = tuple(subnames or ())
    return ref_obj, subnames


def _copy_subshape(ref_obj, subname):
    try:
        return ref_obj.Shape.getElement(subname).copy()
    except Exception:
        try:
            return ref_obj.getSubObject(subname).copy()
        except Exception:
            return None


def _snapshot_generated_region_references(doc, keep_interface=None):
    """Capture user references before generated region objects are replaced."""
    generated_objects = {
        obj.Name: obj for obj in doc.Objects
        if getattr(obj, 'GeneratedBy', '') == GENERATED_BY
    }
    if not generated_objects:
        return {'part_links': [], 'shape_refs': []}

    source_names = {
        obj_name: getattr(getattr(obj, 'SourceObject', None), 'Name', '')
        for obj_name, obj in generated_objects.items()
    }
    part_links = []
    shape_refs = []
    for obj in list(doc.Objects):
        if obj.Name in generated_objects or obj is keep_interface:
            continue

        part = getattr(obj, 'Part', None)
        if part is not None and part.Name in generated_objects:
            part_links.append((obj.Name, source_names.get(part.Name, '')))

        if 'ShapeRefs' not in getattr(obj, 'PropertiesList', []):
            continue
        entries = []
        has_generated_reference = False
        for reference in list(getattr(obj, 'ShapeRefs', [])):
            ref_obj, subnames = _normalise_link_sub_reference(reference)
            if ref_obj is None:
                continue
            if ref_obj.Name not in generated_objects:
                entries.append({
                    'kind': 'existing',
                    'object_name': ref_obj.Name,
                    'subnames': subnames,
                })
                continue
            has_generated_reference = True
            entries.append({
                'kind': 'generated',
                'source_name': source_names.get(ref_obj.Name, ''),
                'elements': [
                    (subname, _copy_subshape(ref_obj, subname)) for subname in subnames
                ],
            })
        if has_generated_reference:
            shape_refs.append((obj.Name, entries))
    return {'part_links': part_links, 'shape_refs': shape_refs}


def _candidate_subshapes(shape, subname):
    if subname.startswith('Face'):
        return 'Area', list(getattr(shape, 'Faces', []))
    if subname.startswith('Solid'):
        return 'Volume', list(getattr(shape, 'Solids', []))
    if subname.startswith('Edge'):
        return 'Length', list(getattr(shape, 'Edges', []))
    if subname.startswith('Vertex'):
        return None, list(getattr(shape, 'Vertexes', []))
    return None, []


def _matching_subshape_names(old_subshape, subname, new_region, tolerance=1e-5):
    if old_subshape is None:
        return []
    measure_name, candidates = _candidate_subshapes(new_region.Shape, subname)
    prefix = ''.join(c for c in subname if not c.isdigit())
    exact_matches = []
    for index, candidate in enumerate(candidates, 1):
        try:
            if old_subshape.isSame(candidate):
                exact_matches.append("{}{}".format(prefix, index))
        except Exception:
            pass
    if exact_matches:
        return exact_matches

    if measure_name is None:
        for index, candidate in enumerate(candidates, 1):
            try:
                if old_subshape.distToShape(candidate)[0] <= tolerance:
                    return ["{}{}".format(prefix, index)]
            except Exception:
                continue
        return []

    old_measure = abs(getattr(old_subshape, measure_name, 0.0))
    if old_measure <= 0:
        return []
    overlap_matches = []
    covered_measure = 0.0
    for index, candidate in enumerate(candidates, 1):
        try:
            if old_subshape.distToShape(candidate)[0] > tolerance:
                continue
            common = old_subshape.common(candidate)
            overlap = abs(getattr(common, measure_name, 0.0))
        except Exception:
            continue
        if overlap <= max(old_measure * 1e-8, tolerance ** 3):
            continue
        overlap_matches.append("{}{}".format(prefix, index))
        covered_measure += overlap
    if covered_measure >= old_measure * 0.99:
        return overlap_matches
    return []


def _restore_generated_region_references(doc, snapshot, source_to_region_obj):
    new_regions = {source_obj.Name: region_obj for source_obj, region_obj in source_to_region_obj.items()}
    for obj_name, source_name in snapshot['part_links']:
        obj = doc.getObject(obj_name)
        region_obj = new_regions.get(source_name)
        if obj is not None and region_obj is not None:
            obj.Part = region_obj

    for obj_name, entries in snapshot['shape_refs']:
        obj = doc.getObject(obj_name)
        if obj is None:
            continue
        restored_refs = []
        for entry in entries:
            if entry['kind'] == 'existing':
                ref_obj = doc.getObject(entry['object_name'])
                subnames = entry['subnames']
            else:
                ref_obj = new_regions.get(entry['source_name'])
                subnames = []
                if ref_obj is not None:
                    for old_subname, old_subshape in entry['elements']:
                        subnames.extend(_matching_subshape_names(
                            old_subshape, old_subname, ref_obj
                        ))
                subnames = tuple(dict.fromkeys(subnames))
                if ref_obj is not None and entry['elements'] and not subnames:
                    FreeCAD.Console.PrintWarning(
                        "Could not restore {} references on {} after regenerating interface region {}\n".format(
                            ', '.join(subname for subname, _shape in entry['elements']),
                            obj.Label,
                            ref_obj.Label,
                        )
                    )
            if ref_obj is not None and subnames:
                restored_refs.append((ref_obj, tuple(subnames)))
        obj.ShapeRefs = restored_refs


def _clear_generated_objects(doc, keep_interface=None):
    for obj in list(doc.Objects):
        if getattr(obj, 'GeneratedBy', '') == GENERATED_BY:
            doc.removeObject(obj.Name)
    old_group = doc.getObject("InterfaceRegions")
    if old_group is not None and not getattr(old_group, 'Group', []):
        doc.removeObject(old_group.Name)
    old_interface = doc.getObject("InterfaceRegionCoupledInterface")
    if old_interface is not None and old_interface is not keep_interface and \
            getattr(getattr(old_interface, 'Proxy', None), 'Type', '') == \
            'CfdRegionCoupledInterface':
        doc.removeObject(old_interface.Name)


def _add_generated_marker(obj):
    addObjectProperty(
        obj,
        "GeneratedBy",
        GENERATED_BY,
        "App::PropertyString",
        "Interface NCC",
        QT_TRANSLATE_NOOP("App::Property", "Generator marker for CfdOF interface NCC regions"),
    )


def _add_generated_properties(obj, source_obj, region_role=REGION_ROLE_SOLID):
    _add_generated_marker(obj)
    addObjectProperty(
        obj,
        "IsFinalInterfaceRegion",
        False,
        "App::PropertyBool",
        "Interface NCC",
        QT_TRANSLATE_NOOP("App::Property", "Whether this is the final generated region for its source object"),
    )
    addObjectProperty(
        obj,
        "SourceObject",
        source_obj,
        "App::PropertyLinkGlobal",
        "Interface NCC",
        QT_TRANSLATE_NOOP("App::Property", "Original source object for this interface region"),
    )
    addObjectProperty(
        obj,
        "RegionRole",
        region_role,
        "App::PropertyString",
        "Interface NCC",
        QT_TRANSLATE_NOOP("App::Property", "Region role used to choose interface Cut ownership"),
    )


def _clone_source_object(doc, source_obj):
    clone = doc.addObject("Part::Feature", "NccSourceClone_{}".format(_safe_name(source_obj.Name)))
    clone.Label = "{}_clone".format(source_obj.Label)
    clone.Shape = source_obj.Shape.copy()
    _add_generated_marker(clone)
    doc.recompute()
    if getattr(clone, 'ViewObject', None):
        clone.ViewObject.Visibility = False
    return clone


def _make_slice_feature(doc, base_obj, tool_obj, name, label, source_obj,
                        region_role=REGION_ROLE_SOLID):
    from BOPTools import SplitFeatures

    slice_obj = SplitFeatures.makeSlice(name=name)
    slice_obj.Label = label
    slice_obj.Base = base_obj
    slice_obj.Tools = [tool_obj]
    slice_obj.Mode = "Split"
    _add_generated_properties(slice_obj, source_obj, region_role)
    doc.recompute()
    return slice_obj


def _make_cut_feature(doc, base_obj, tool_obj, name, label, source_obj,
                      region_role=REGION_ROLE_SOLID):
    cut_obj = doc.addObject("Part::Cut", name)
    cut_obj.Label = label
    cut_obj.Base = base_obj
    cut_obj.Tool = tool_obj
    cut_obj.Refine = False
    _add_generated_properties(cut_obj, source_obj, region_role)
    doc.recompute()
    return cut_obj


def _shapes_touch_or_overlap(shape_a, shape_b, tolerance=1e-5):
    if _overlap_volume(shape_a, shape_b) > tolerance:
        return True
    try:
        return shape_a.distToShape(shape_b)[0] <= tolerance
    except Exception:
        return False


def _shape_volume(shape):
    try:
        solids = getattr(shape, 'Solids', [])
        if solids:
            return sum(abs(solid.Volume) for solid in solids)
        return abs(shape.Volume)
    except Exception:
        return 0.0


def _overlap_volume(shape_a, shape_b):
    try:
        common = shape_a.common(shape_b)
        return _shape_volume(common)
    except Exception:
        return 0.0


def _should_cut_source_by_tool(source_shape, tool_shape, tolerance=1e-5):
    source_volume = _shape_volume(source_shape)
    tool_volume = _shape_volume(tool_shape)
    if source_volume <= tolerance or tool_volume <= tolerance:
        return False
    overlap_volume = _overlap_volume(source_shape, tool_shape)
    if overlap_volume <= tolerance:
        return False

    source_overlap_fraction = overlap_volume / source_volume
    tool_overlap_fraction = overlap_volume / tool_volume

    # If the source is contained by the tool, keep the source as its own region.
    # The containing partner will be cut by this source when its turn is processed.
    if source_overlap_fraction > 0.999 and tool_volume > source_volume:
        return False

    # Cut the larger/containing side so the generated region owns a cavity face
    # that can be paired with the contained/overlapping partner.
    return tool_overlap_fraction > 0.999 or source_volume >= tool_volume


def _should_cut_source_by_role(source_role, tool_role):
    if source_role == REGION_ROLE_FLUID and tool_role == REGION_ROLE_SOLID:
        return True
    if source_role == REGION_ROLE_SOLID and tool_role == REGION_ROLE_FLUID:
        return False
    return None


def _has_volume_overlap(shape_a, shape_b, tolerance=1e-5):
    return _overlap_volume(shape_a, shape_b) > tolerance


def _face_overlap_fraction(face_a, face_b):
    area_a = abs(getattr(face_a, 'Area', 0.0))
    area_b = abs(getattr(face_b, 'Area', 0.0))
    if area_a <= 0 or area_b <= 0:
        return 0.0
    try:
        return abs(face_a.common(face_b).Area) / min(area_a, area_b)
    except Exception:
        return 0.0


def _faces_are_paired(face_a, face_b, tolerance=1e-5, overlap_threshold=0.5):
    try:
        if face_a.distToShape(face_b)[0] > tolerance:
            return False
    except Exception:
        return False
    return _face_overlap_fraction(face_a, face_b) > overlap_threshold


def findTouchingShapePairs(source_objects, tolerance=1e-5):
    """Return selected-object pairs that touch or overlap, preserving selection order."""
    pairs = []
    for i, obj_a in enumerate(source_objects):
        for obj_b in source_objects[i + 1:]:
            if _shapes_touch_or_overlap(obj_a.Shape, obj_b.Shape, tolerance):
                pairs.append((obj_a, obj_b))
    return pairs


def touchingPartnersForSource(source_obj, touching_pairs, object_map=None):
    """Return ordered touching partners for one source from a touching-pair list."""
    partners = []
    for obj_a, obj_b in touching_pairs:
        if obj_a is source_obj:
            partners.append(object_map.get(obj_b, obj_b) if object_map else obj_b)
        elif obj_b is source_obj:
            partners.append(object_map.get(obj_a, obj_a) if object_map else obj_a)
    return partners


def _default_region_roles(source_objects):
    roles = {}
    for index, source_obj in enumerate(source_objects):
        roles[source_obj.Name] = REGION_ROLE_FLUID if index == 0 else REGION_ROLE_SOLID
    return roles


def _normalise_region_role(role):
    role_text = str(role or '').strip().lower()
    if role_text == REGION_ROLE_FLUID.lower():
        return REGION_ROLE_FLUID
    return REGION_ROLE_SOLID


def _normalise_region_roles(source_objects, region_roles=None):
    roles = _default_region_roles(source_objects)
    if region_roles is None:
        return roles
    if isinstance(region_roles, dict):
        for source_obj in source_objects:
            value = None
            if source_obj in region_roles:
                value = region_roles[source_obj]
            elif source_obj.Name in region_roles:
                value = region_roles[source_obj.Name]
            elif source_obj.Label in region_roles:
                value = region_roles[source_obj.Label]
            if value is not None:
                roles[source_obj.Name] = _normalise_region_role(value)
        return roles
    for source_obj, role in zip(source_objects, region_roles):
        roles[source_obj.Name] = _normalise_region_role(role)
    return roles


def _create_interface_region_from_pairs(doc, source_obj, base_obj, touching_pairs, clone_map,
                                        clone_source_names, region_roles):
    source_role = region_roles.get(source_obj.Name, REGION_ROLE_SOLID)
    current_obj = base_obj
    operation_steps = []
    tools = touchingPartnersForSource(source_obj, touching_pairs, clone_map)
    for tool_index, tool_obj in enumerate(tools):
        tool_role = region_roles.get(clone_source_names.get(tool_obj.Name, ''), REGION_ROLE_SOLID)
        if not _shapes_touch_or_overlap(current_obj.Shape, tool_obj.Shape):
            continue
        is_final_tool = tool_index == len(tools) - 1
        operation_name = "{}_slice".format(_safe_name(source_obj.Name)) if is_final_tool \
            else "NccSlice_{}_by_{}".format(_safe_name(source_obj.Name), _safe_name(tool_obj.Name))
        operation_label = "{}_slice".format(source_obj.Label) if is_final_tool \
            else "{}_slice".format(tool_obj.Label)

        volume_overlap = _has_volume_overlap(current_obj.Shape, tool_obj.Shape)
        role_cut_decision = _should_cut_source_by_role(source_role, tool_role)
        if volume_overlap and (role_cut_decision is True or (
                role_cut_decision is None and _should_cut_source_by_tool(current_obj.Shape, tool_obj.Shape))):
            next_obj = _make_cut_feature(
                doc, current_obj, tool_obj, operation_name, operation_label, source_obj, source_role)
        elif volume_overlap:
            continue
        else:
            next_obj = _make_slice_feature(
                doc, current_obj, tool_obj, operation_name, operation_label, source_obj, source_role)

        if not next_obj.Shape.Solids:
            doc.removeObject(next_obj.Name)
            continue
        if getattr(current_obj, 'GeneratedBy', '') == GENERATED_BY and getattr(current_obj, 'ViewObject', None):
            current_obj.ViewObject.Visibility = False
        current_obj = next_obj
        operation_steps.append(next_obj)

    if not operation_steps:
        slice_obj = doc.addObject("Part::Feature", "{}_slice".format(_safe_name(source_obj.Name)))
        slice_obj.Label = "{}_slice".format(source_obj.Label)
        slice_obj.Shape = base_obj.Shape.copy()
        _add_generated_properties(slice_obj, source_obj, source_role)
        slice_obj.IsFinalInterfaceRegion = True
        return slice_obj

    final_obj = operation_steps[-1]
    final_obj.IsFinalInterfaceRegion = True
    final_name = "{}_slice".format(_safe_name(source_obj.Name))
    if final_obj.Name != final_name:
        final_obj.Label = "{}_slice".format(source_obj.Label)
    if getattr(final_obj, 'ViewObject', None):
        final_obj.ViewObject.Visibility = True
    return final_obj


def _face_touches_other_region(face, region_obj, region_objects, tolerance=1e-5):
    for other_obj in region_objects:
        if other_obj is region_obj:
            continue
        try:
            if face.distToShape(other_obj.Shape)[0] <= tolerance:
                return True
        except Exception:
            continue
    return False


def generateInterfaceFaceRefs(region_objects, tolerance=1e-5):
    """Return per-region face references created by interfacing/slicing."""
    refs = []
    for region_obj in region_objects:
        face_names = []
        for face_id, face in enumerate(region_obj.Shape.Faces, 1):
            if _face_touches_other_region(face, region_obj, region_objects, tolerance):
                face_names.append("Face{}".format(face_id))
        if face_names:
            refs.append((region_obj, tuple(face_names)))
    if not refs:
        raise ValueError("No interface faces were found between generated regions")
    return refs


def createInterfaceNccRegions(source_objects=None, analysis_obj=None, region_roles=None, interface_obj=None):
    """Create root-level per-region interface shapes.

    The selected/source objects remain unchanged. For each source object, CfdOF
    retains that source as the base and applies each touching or overlapping
    selected source in sequence. Touching-only partners use Slice Apart. Partners
    with real shared volume use Boolean Cut on the containing/larger side so
    fluid regions around immersed solids get cavity faces for NCC coupling.
    If region_roles is not provided, the first selected/source object defaults
    to Fluid and the remaining objects default to Solid.
    """
    doc = FreeCAD.ActiveDocument
    if doc is None:
        raise RuntimeError("No active FreeCAD document")
    if analysis_obj is None:
        analysis_obj = CfdTools.getActiveAnalysis()
    if analysis_obj is None:
        raise RuntimeError("No active CfdAnalysis")
    if source_objects is None:
        if not FreeCAD.GuiUp:
            raise RuntimeError("source_objects must be provided when GUI selection is unavailable")
        source_objects = FreeCADGui.Selection.getSelection()
    source_objects = [obj for obj in source_objects if hasattr(obj, 'Shape') and not obj.Shape.isNull()]
    if len(source_objects) < 2:
        raise RuntimeError("Select at least two valid region source objects")
    region_roles = _normalise_region_roles(source_objects, region_roles)

    dependent_references = _snapshot_generated_region_references(doc, keep_interface=interface_obj)
    _clear_generated_objects(doc, keep_interface=interface_obj)
    touching_pairs = findTouchingShapePairs(source_objects)
    if not touching_pairs:
        raise RuntimeError("No touching or overlapping shape pairs were found")
    clone_map = {source_obj: _clone_source_object(doc, source_obj) for source_obj in source_objects}
    clone_source_names = {clone_obj.Name: source_obj.Name for source_obj, clone_obj in clone_map.items()}

    slice_objects = []
    source_to_region_obj = {}
    for source_obj in source_objects:
        slice_obj = _create_interface_region_from_pairs(
            doc, source_obj, clone_map[source_obj], touching_pairs, clone_map, clone_source_names, region_roles)
        slice_objects.append(slice_obj)
        source_to_region_obj[source_obj] = slice_obj
        if getattr(slice_obj, 'ViewObject', None):
            slice_obj.ViewObject.Visibility = True

    _restore_generated_region_references(doc, dependent_references, source_to_region_obj)

    analysis_obj.NeedsMeshRewrite = True
    analysis_obj.NeedsMeshRerun = True
    analysis_obj.NeedsCaseRewrite = True

    doc.recompute()
    return None, slice_objects, None


class CommandCfdInterfaceNccRegions:
    def GetResources(self):
        return {
            'Pixmap': os.path.join(CfdTools.getModulePath(), "Gui", "Icons",
                                   "interface_ncc_regions.svg"),
            'MenuText': QT_TRANSLATE_NOOP("CfdOF_InterfaceNccRegions",
                                          "Create interface NCC regions"),
            'ToolTip': QT_TRANSLATE_NOOP(
                "CfdOF_InterfaceNccRegions",
                "Create root-level interface region shapes using Slice Apart for touching regions and Cut for overlapping regions"),
        }

    def IsActive(self):
        if CfdTools.getActiveAnalysis() is None:
            return False
        return len(FreeCADGui.Selection.getSelection()) >= 2

    def Activated(self):
        source_objects = [
            obj for obj in FreeCADGui.Selection.getSelection()
            if hasattr(obj, 'Shape') and not obj.Shape.isNull()
        ]
        if len(source_objects) < 2:
            QtGui.QMessageBox.warning(None, "Create interface NCC regions",
                                      "Select at least two valid region source objects.")
            return
        FreeCAD.ActiveDocument.openTransaction("Create interface NCC regions")
        try:
            createInterfaceNccRegions(source_objects)
            FreeCAD.ActiveDocument.commitTransaction()
        except Exception:
            FreeCAD.ActiveDocument.abortTransaction()
            raise


if FreeCAD.GuiUp and hasattr(FreeCADGui, 'addCommand'):
    FreeCADGui.addCommand('CfdOF_InterfaceNccRegions', CommandCfdInterfaceNccRegions())
