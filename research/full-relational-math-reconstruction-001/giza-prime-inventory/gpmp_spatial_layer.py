"""GPMP Control Monuments -> provenance-tagged spatial point layer.

HARD RULES
----------
* Every value is read from ``source_samples/GPMP-Control-Monuments.json``.
* KML ``coordinates[2] == 0.0`` is NOT an elevation.  Elevation is parsed only
  from the ``description`` field after ``Elevation;``.
* No Helmert <-> WGS84 / EPSG conversion is attempted; datum status stays
  ``unverified``.  Longitude/latitude are stored as separate scalar fields and
  are never silently equated with the local Northing/Easting system.
* The 41/11/30 counts are control values for THIS file, not universal laws.
* A malformed value raises; it is never replaced by zero or a plausible guess.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
from typing import Any, Dict, List, Optional, Sequence, Tuple

import spatial_geometry as sg

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SOURCE = os.path.join(HERE, "source_samples", "GPMP-Control-Monuments.json")

# Control values for this committed source file only.
CONTROL_TOTAL = 41
CONTROL_NETWORKS = {"main_traverse": 11, "secondary_network": 30}

NORTHING_RE = re.compile(r"Northing:\s*([-+]?\d+(?:\.\d+)?)")
EASTING_RE = re.compile(r"Easting:\s*([-+]?\d+(?:\.\d+)?)")
ELEVATION_RE = re.compile(r"Elevation;\s*([-+]?\d+(?:\.\d+)?)")
NETWORK_RE = re.compile(r"Description:\s*([A-Za-z]+)")

NETWORK_LABELS = {
    "Main": "main_traverse",
    "Secondary": "secondary_network",
}

REQUIRED_TOP_LEVEL = (
    "source_file", "sha256", "kml_entry", "kml_bytes", "folders",
    "placemark_count", "placemarks",
)


class SpatialValidationError(ValueError):
    """Raised when the GPMP source violates its declared structure."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SpatialValidationError(message)


def _sha256_of(path: str) -> str:
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def _number(match: Optional[re.Match], label: str, raw: str) -> float:
    _require(match is not None, "%s not found in description" % label)
    value = float(match.group(1))  # type: ignore[union-attr]
    _require(math.isfinite(value), "%s is not finite" % label)
    _require(label in raw, "%s missing from raw description" % label)
    return value


def load_source(path: Optional[str] = None) -> Dict[str, Any]:
    target = DEFAULT_SOURCE if path is None else path
    _require(os.path.isfile(target), "GPMP source file is absent: %s" % target)
    with open(target, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    for key in REQUIRED_TOP_LEVEL:
        _require(key in payload, "GPMP source missing %r" % key)
    return payload


def parse_northing(description: str) -> float:
    return _number(NORTHING_RE.search(description), "Northing", description)


def parse_easting(description: str) -> float:
    return _number(EASTING_RE.search(description), "Easting", description)


def parse_elevation(description: str) -> float:
    """Elevation is after ``Elevation;`` in the description, never KML Z."""
    return _number(ELEVATION_RE.search(description), "Elevation", description)


def parse_longitude_latitude(placemark: Dict[str, Any]) -> Tuple[float, float, float]:
    coords = placemark.get("coordinates")
    _require(isinstance(coords, list) and len(coords) >= 1,
             "placemark coordinates must be a nonempty list")
    first = coords[0]
    _require(isinstance(first, list) and len(first) >= 3,
             "KML coordinate tuple needs longitude, latitude and Z")
    values = tuple(float(v) for v in first[:3])
    _require(all(math.isfinite(v) for v in values), "KML coordinate is not finite")
    return values  # type: ignore[return-value]


def classify_network(description: str) -> str:
    match = NETWORK_RE.search(description)
    _require(match is not None, "network label not found in description")
    label = match.group(1)  # type: ignore[union-attr]
    _require(label in NETWORK_LABELS, "unknown network label %r" % label)
    return NETWORK_LABELS[label]


def validate_control_point(record: Dict[str, Any]) -> bool:
    _require(bool(record.get("point_id")), "control point has no point_id")
    _require(record.get("geometry") == "Point", "control point geometry must be Point")
    local = record.get("local_coordinates", {})
    for key in ("easting", "northing", "elevation"):
        _require(key in local, "control point missing local %s" % key)
        _require(math.isfinite(float(local[key])), "local %s is not finite" % key)
    geo = record.get("longitude_latitude", {})
    for key in ("longitude", "latitude", "kml_z"):
        _require(key in geo, "control point missing %s" % key)
        _require(math.isfinite(float(geo[key])), "%s is not finite" % key)
    _require(geo.get("kml_z_is_elevation") is False,
             "KML Z must never be promoted to elevation")
    _require(record.get("network") in CONTROL_NETWORKS,
             "control point has unexpected network label")
    _require(isinstance(record.get("description"), str) and bool(record["description"]),
             "raw description must be preserved")
    _require(record.get("datum_status") == "unverified",
             "datum status may not be asserted as verified")
    return True


def _build_point(placemark: Dict[str, Any]) -> Dict[str, Any]:
    _require("name" in placemark and bool(placemark["name"]), "placemark has no name")
    description = placemark.get("description")
    _require(isinstance(description, str) and bool(description), "placemark has no description")
    northing = parse_northing(description)
    easting = parse_easting(description)
    elevation = parse_elevation(description)
    lon, lat, kml_z = parse_longitude_latitude(placemark)
    network = classify_network(description)
    name = str(placemark["name"])
    record = {
        "point_id": "GPMP:" + name,
        "name": name,
        "network": network,
        "geometry": "Point",
        "local_coordinates": {
            "easting": easting,
            "northing": northing,
            "elevation": elevation,
            "axis_order": "X=Easting, Y=Northing, Z=Elevation",
            "units": "source units (metres claimed by publication; unverified here)",
            "coordinate_system": "GPMP local Northing/Easting + Elevation",
            "datum_status": "unverified",
            "source_field": "description",
        },
        "longitude_latitude": {
            "longitude": lon,
            "latitude": lat,
            "kml_z": kml_z,
            "kml_z_is_elevation": False,
            "datum_status": "unverified",
            "relation_to_local_system": "unresolved",
            "source_field": "KML coordinates[0][:3]",
        },
        "description": description,
        "extraction": {
            "northing": "regex Northing: in description",
            "easting": "regex Easting: in description",
            "elevation": "regex Elevation; in description (KML Z rejected)",
            "longitude_latitude": "KML coordinates[0][0:2]",
            "network": "regex Description: in description",
        },
        "datum_status": "unverified",
        "object_link": "UNRESOLVED",
    }
    validate_control_point(record)
    return record


def _range(points: Sequence[Dict[str, Any]], path: Sequence[str]) -> Dict[str, float]:
    values = []
    for point in points:
        node: Any = point
        for key in path:
            node = node[key]
        values.append(float(node))
    return {"min": min(values), "max": max(values)}


def build_spatial_snapshot(path: Optional[str] = None) -> Dict[str, Any]:
    """Parse, validate and project the GPMP source into a spatial snapshot."""
    target = DEFAULT_SOURCE if path is None else path
    payload = load_source(target)
    placemarks = payload["placemarks"]
    _require(isinstance(placemarks, list), "placemarks must be a list")
    _require(payload["placemark_count"] == len(placemarks),
             "declared placemark_count does not match the array")
    _require(len(placemarks) == CONTROL_TOTAL,
             "unexpected placemark count: %d (control for this file is %d)"
             % (len(placemarks), CONTROL_TOTAL))

    points = [_build_point(pm) for pm in placemarks]
    ids = [point["point_id"] for point in points]
    _require(len(ids) == len(set(ids)), "duplicate GPMP point_id")
    names = [point["name"] for point in points]
    _require(len(names) == len(set(names)), "duplicate GPMP name")

    counts = {name: sum(1 for p in points if p["network"] == name)
              for name in CONTROL_NETWORKS}
    for name, expected in CONTROL_NETWORKS.items():
        _require(counts[name] == expected,
                 "%s count %d != control %d" % (name, counts[name], expected))

    control_ranges = {
        "northing": _range(points, ("local_coordinates", "northing")),
        "easting": _range(points, ("local_coordinates", "easting")),
        "elevation": _range(points, ("local_coordinates", "elevation")),
        "longitude": _range(points, ("longitude_latitude", "longitude")),
        "latitude": _range(points, ("longitude_latitude", "latitude")),
    }
    for key, expected in (
        ("northing", (98399.708, 100154.421)),
        ("easting", (498718.109, 500634.775)),
        ("elevation", (19.570, 197.555)),
        ("longitude", (31.1209192, 31.14077838)),
        ("latitude", (29.96474083, 29.98056996)),
    ):
        got = control_ranges[key]
        for side, want in zip(("min", "max"), expected):
            _require(abs(got[side] - want) < 0.001,
                     "%s %s drifted from control" % (key, side))

    centered = sg.center_points(
        [(p["local_coordinates"]["easting"],
          p["local_coordinates"]["northing"],
          p["local_coordinates"]["elevation"]) for p in points])
    plane = sg.fit_plane_least_squares(centered["points"])

    return {
        "layer_id": "GIZA_PRIME_SPATIAL_3D_SKELETON",
        "marking": "SOURCE POINTS / NOT A TERRAIN MODEL",
        "scientific_status": "control_network_only_no_monument_geometry",
        "source": {
            "source_file": payload["source_file"],
            "sha256_of_kml": payload["sha256"],
            "sha256_of_committed_json": _sha256_of(target),
            "kml_entry": payload["kml_entry"],
            "kml_bytes": payload["kml_bytes"],
            "folders": list(payload["folders"]),
            "declared_placemark_count": payload["placemark_count"],
        },
        "provenance_states": {
            "SOURCE_FILE_PRESENT": True,
            "SOURCE_CONTENT_PARSED": True,
            "STRUCTURE_VALIDATED": True,
            "SOURCE_PROVENANCE_VERIFIED": False,
            "INDEPENDENTLY_CORROBORATED": False,
        },
        "coordinate_system": {
            "name": "GPMP local Northing/Easting + Elevation",
            "datum_status": "unverified",
            "units": "source units (metres claimed by publication; unverified here)",
            "conversion_to_epsg_wgs84": "not_performed",
            "helmert_spheroid_of_reference_transform": "not_performed",
            "kml_z_is_elevation": False,
        },
        "counts": {
            "total": len(points),
            "main_traverse": counts["main_traverse"],
            "secondary_network": counts["secondary_network"],
            "real_objects": 0,
            "relations": 0,
        },
        "control_values_for_this_file": {
            "total": CONTROL_TOTAL,
            "networks": dict(CONTROL_NETWORKS),
        },
        "control_ranges": control_ranges,
        "points": points,
        "derived_geometry": {
            "centering_origin": {
                "easting": centered["origin"][0],
                "northing": centered["origin"][1],
                "elevation": centered["origin"][2],
            },
            "least_squares_plane": plane,
            "status": sg.DERIVED_GEOMETRY,
            "not_terrain": True,
        },
        "separation": {
            "gpmp_and_arce_sphinx_grid": "separate",
            "gpmp_to_arce_transform": "not_performed",
            "object_link": "UNRESOLVED",
            "control_points_are_not_archaeological_objects": True,
        },
        "render_rules": {
            "terrain_mesh": False,
            "fabricated_lines": False,
            "kml_z_as_elevation": False,
            "vertical_exaggeration_default": 1.0,
            "grid_is_graphic_support_only": True,
        },
        "model_contract": {
            "statuses": list(sg.MODEL_STATUSES),
            "required_model_fields": list(sg.MODEL_RECORD_FIELDS),
            "instantiated_models_in_this_commit": 0,
            "reason": "insufficient constraints for a validated idealized surface",
        },
    }


__all__ = [name for name in dir() if not name.startswith("_")]
