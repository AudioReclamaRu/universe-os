"""PHASE B / STAGES B+C — canonical observation envelope with per-campaign
adapters and conservative semantic typing.

HARD RULES
----------
* One adapter per actual campaign schema.  A single universal parser that
  assumes identical structure is explicitly forbidden.
* The original record is preserved verbatim; normalized fields are additions.
* Missing values are ``None`` (JSON null) or an explicit status string.  They
  are NEVER replaced by zero or a plausible number.
* KML Z (always 0.0 here) is never promoted to elevation.  Elevation is read
  only from the documented text field, and Petrie stations have none.
* Classification never assigns an archaeological class from a name or from
  proximity to a monument.  Unidentifiable => ``UNKNOWN``.
* CONTROL POINT != ARCHAEOLOGICAL OBJECT; SURVEY MARKER != TERRAIN SAMPLE.
"""

from __future__ import annotations

import json
import math
import os
import re
from typing import Any, Dict, List, Optional, Tuple

import phase_b_source_catalog as pbc

PARSER_VERSION = "phase_b_observation_v1"
SCHEMA_VERSION = "phase_b_observation_schema_v1"

NORTH_RE = re.compile(r"(?:GPMP\s+)?Northing:\s*([-+]?\d+(?:\.\d+)?)", re.I)
EAST_RE = re.compile(r"(?:GPMP\s+)?Easting:\s*([-+]?\d+(?:\.\d+)?)", re.I)
ELEV_RE = re.compile(r"Elevation;\s*([-+]?\d+(?:\.\d+)?)", re.I)
LON_SWAP_RE = re.compile(r"LongItude:\s*([-+]?\d+(?:\.\d+)?)")
LON_OK_RE = re.compile(r"Longitude:\s*([-+]?\d+(?:\.\d+)?)")
LAT_RE = re.compile(r"Latitude:\s*([-+]?\d+(?:\.\d+)?)")
FEATURE_RE = re.compile(r"Feature:\s*(\d+)", re.I)
FEATURE_REF_RE = re.compile(r"F#(\d+)", re.I)
RESHOOT_RE = re.compile(r"reshoot\w*\s+it\s+with\s+TS\s*#\s*([\d\s\-]+)", re.I)
PETRIE_NS_RE = re.compile(r"Petrie\s+N-S:\s*(\d+)", re.I)
PETRIE_EW_RE = re.compile(r"Petrie\s+E-W:\s*(\d+)", re.I)
PLACE_RE = re.compile(r"Place:\s*(.*?)(?=\s+Petrie N-S:)", re.I)

CAMPAIGNS = {
    "GDFS-2012-for-GE-21vii18.json": {
        "campaign_id": "GDFS-2012", "year": 2012,
        "role": "survey_point", "kind": "topographic_detail",
        "network": "GDFS",
    },
    "GDFS-2015-Master-25iii17-edited-child.json": {
        "campaign_id": "GDFS-2015", "year": 2015,
        "role": "survey_point", "kind": "topographic_detail",
        "network": "GDFS",
    },
    "GDFS-2016-23ix18.json": {
        "campaign_id": "GDFS-2016", "year": 2016,
        "role": "feature_sample", "kind": "archaeological_feature_point",
        "network": "GDFS",
    },
    "GDFS-2018-12xii18.json": {
        "campaign_id": "GDFS-2018", "year": 2018,
        "role": "feature_sample", "kind": "archaeological_feature_point",
        "network": "GDFS",
    },
    "GPMP-Control-Monuments.json": {
        "campaign_id": "GPMP", "year": None,
        "role": "geodetic_control_point", "kind": "control_network_station",
        "network": "GPMP",
    },
    "Giza-Corner-Points-2v17.json": {
        "campaign_id": "GIZA_CORNER", "year": None,
        "role": "building_corner", "kind": "monument_corner_candidate",
        "network": "GIZA_CORNER",
    },
    "Petries-Stations.json": {
        "campaign_id": "PETRIE", "year": None,
        "role": "survey_station", "kind": "historical_station",
        "network": "PETRIE",
    },
}

STATUS_MAP = {
    "GDFS-2012": "MEASURED_GEOMETRY",
    "GDFS-2015": "MEASURED_GEOMETRY",
    "GDFS-2016": "MEASURED_GEOMETRY",
    "GDFS-2018": "MEASURED_GEOMETRY",
    "GPMP": "MEASURED_GEOMETRY",
    "GIZA_CORNER": "MEASURED_GEOMETRY",
    "PETRIE": "MEASURED_GEOMETRY",
}


class ObservationError(ValueError):
    """Raised when a source record violates its declared adapter contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ObservationError(message)


def _number(match: Optional[re.Match], label: str, description: str) -> Optional[float]:
    if match is None:
        return None
    value = float(match.group(1))
    _require(math.isfinite(value), "non-finite %s in description" % label)
    return value


def _coords(placemark: Dict[str, Any]) -> Tuple[float, float, float]:
    coords = placemark.get("coordinates")
    _require(isinstance(coords, list) and coords,
             "placemark coordinates must be a nonempty list")
    first = coords[0]
    _require(isinstance(first, list) and len(first) >= 3,
             "KML tuple needs longitude, latitude, Z")
    values = (float(first[0]), float(first[1]), float(first[2]))
    _require(all(math.isfinite(v) for v in values), "non-finite KML coordinate")
    return values


_SOURCE_HASH_CACHE: Dict[str, str] = {}


def _source_sha(source_file: str) -> str:
    """Cache the raw SHA-256 once per source file, not once per observation."""
    if source_file not in _SOURCE_HASH_CACHE:
        _SOURCE_HASH_CACHE[source_file] = pbc.raw_sha256(
            os.path.join(pbc.DERIVED_ROOT, source_file))
    return _SOURCE_HASH_CACHE[source_file]


def _base_envelope(source_file: str, campaign: Dict[str, Any],
                   index: int, placemark: Dict[str, Any]) -> Dict[str, Any]:
    description = placemark.get("description")
    _require(isinstance(description, str) and bool(description),
             "placemark %s has no description" % source_file)
    lon, lat, kml_z = _coords(placemark)
    north = _number(NORTH_RE.search(description), "Northing", description)
    east = _number(EAST_RE.search(description), "Easting", description)
    _require(north is not None and east is not None,
             "missing local Northing/Easting in %s[%d]" % (source_file, index))
    elev = _number(ELEV_RE.search(description), "Elevation", description)
    swapped = bool(LON_SWAP_RE.search(description))
    lon_ok = _number(LON_OK_RE.search(description), "Longitude", description)
    lon_swap = _number(LON_SWAP_RE.search(description), "LongItude", description)
    lat_doc = _number(LAT_RE.search(description), "Latitude", description)
    warnings: List[str] = []
    if swapped:
        warnings.append("SWAPPED_LONGITUDE_LABEL: 'LongItude' holds the latitude-like value")
    if elev is None:
        warnings.append("ELEVATION_ABSENT: vertical value is UNKNOWN, not zero")
    if kml_z != 0.0:
        warnings.append("KML_Z_NONZERO: third coordinate is not assumed to be elevation")
    fid = FEATURE_RE.search(description)
    fref = FEATURE_REF_RE.search(description)
    reshoot = RESHOOT_RE.search(description)
    pns = PETRIE_NS_RE.search(description)
    pew = PETRIE_EW_RE.search(description)
    place = PLACE_RE.search(description)
    record = {
        "observation_id": "%s:%06d" % (campaign["campaign_id"], index),
        "source_file_id": source_file,
        "source_index": index,
        "campaign_id": campaign["campaign_id"],
        "campaign_year": campaign["year"],
        "original_record_id": str(placemark.get("name", "")),
        "original_name": placemark.get("name"),
        "original_description": description,
        "original_folder_path": placemark.get("folder"),
        "original_geometry_type": placemark.get("geometry"),
        "original_coordinates": placemark.get("coordinates"),
        "original_coordinate_order": "KML [longitude, latitude, Z]",
        "original_extended_data": placemark.get("extended", {}),
        "normalized_geometry_type": "Point",
        "normalized_coordinates": {
            "local_easting": east,
            "local_northing": north,
            "elevation": elev,
            "longitude": lon,
            "latitude": lat,
            "kml_z": kml_z,
            "kml_z_is_elevation": False,
        },
        "coordinate_system_id": "LOCAL_GRID_UNVERIFIED",
        "vertical_reference_id": (
            "UNKNOWN" if elev is None else "DESCRIPTION_ELEVATION_UNVERIFIED"),
        "coordinate_semantics": (
            "local Easting/Northing from description; geographic pair from KML "
            "coordinates; relation between the two is unresolved"),
        "units": {
            "local_xy": "source units (metres claimed by publication, unverified)",
            "elevation": "source units (metres claimed, unverified)" if elev is not None else None,
            "geographic": "decimal degrees (datum unresolved)",
        },
        "measurement_method": "instrumental survey (campaign metadata not present in file)",
        "measurement_epoch": str(campaign["year"]) if campaign["year"] is not None else None,
        "source_provenance": {
            "network": campaign["network"],
            "source_file": source_file,
            "source_sha256": _source_sha(source_file),
            "provenance_states": {
                "FILE_PRESENT": True, "SOURCE_CONTENT_PARSED": True,
                "STRUCTURE_VALIDATED": True, "SOURCE_PROVENANCE_VERIFIED": False,
                "COORDINATE_SYSTEM_VERIFIED": False,
                "INDEPENDENTLY_CORROBORATED": False,
            },
        },
        "parser_version": PARSER_VERSION,
        "extraction_method": {
            "local_xy": "regex Northing:/Easting: in original_description",
            "elevation": "regex Elevation; in original_description (KML Z rejected)",
            "geographic": "KML coordinates[0][0:2]",
            "feature_id": "regex Feature: in original_description",
        },
        "validation_status": STATUS_MAP[campaign["campaign_id"]],
        "uncertainty": None,
        "limitations": [
            "datum and projection unverified",
            "vertical reference unverified",
            "one record is one measurement, not necessarily one physical object",
        ],
        "warnings": warnings,
        "derived_links": {
            "feature_id": fid.group(1) if fid else None,
            "feature_reference": fref.group(1) if fref else None,
            "reshoot_total_station_range": reshoot.group(1).strip() if reshoot else None,
            "petrie_ns": pns.group(1) if pns else None,
            "petrie_ew": pew.group(1) if pew else None,
            "place_description": place.group(1).strip() if place else None,
            "documented_longitude": lon_ok if lon_ok is not None else lon_swap,
            "documented_latitude": lat_doc,
        },
        "identity_status": "UNRESOLVED",
        "semantic_type": {
            "value": campaign["role"],
            "basis": "campaign adapter + source folder/description structure",
            "source_field": "campaign_id and original_description",
            "confidence": "SOURCE_STRUCTURE_ONLY",
            "status": "DERIVED_CLASSIFICATION",
            "alternatives": [],
        },
        "geometry_role": campaign["kind"],
        "object_link": None,
    }
    return record


def adapt(source_file: str, placemark: Dict[str, Any], index: int) -> Dict[str, Any]:
    _require(source_file in CAMPAIGNS, "no adapter for %s" % source_file)
    record = _base_envelope(source_file, CAMPAIGNS[source_file], index, placemark)
    if source_file == "GPMP-Control-Monuments.json":
        match = re.search(r"Description:\s*([A-Za-z]+)", record["original_description"])
        network = match.group(1) if match else None
        record["semantic_type"]["value"] = (
            "main_traverse_control" if network == "Main"
            else "secondary_network_control" if network == "Secondary"
            else "geodetic_control_point")
        record["semantic_type"]["basis"] = "GPMP Description label in source"
        record["semantic_type"]["source_field"] = "original_description:Description"
        record["normalized_coordinates"]["network"] = network
        record["identity_status"] = "OBSERVED_CONTROL_POINT"
    elif source_file == "Giza-Corner-Points-2v17.json":
        record["semantic_type"]["value"] = "building_corner_candidate"
        record["semantic_type"]["alternatives"] = [
            "survey_marker", "restoration_reference", "casing_corner"]
        record["semantic_type"]["confidence"] = "SOURCE_LABEL_ONLY"
    elif source_file == "Petries-Stations.json":
        record["semantic_type"]["value"] = "historical_survey_station"
        record["semantic_type"]["alternatives"] = [
            "monument_reference_point", "modern_reoccupation"]
        record["semantic_type"]["confidence"] = "SOURCE_LABEL_ONLY"
        record["coordinate_system_id"] = "PETRIE_LOCAL_GRID_UNRESOLVED"
        record["normalized_coordinates"]["petrie_local"] = {
            "ns": record["derived_links"]["petrie_ns"],
            "ew": record["derived_links"]["petrie_ew"],
            "relation_to_gpmp": "documented pair in description; transform NOT performed",
        }
    elif source_file in ("GDFS-2016-23ix18.json", "GDFS-2018-12xii18.json"):
        fid = record["derived_links"]["feature_id"]
        record["semantic_type"]["alternatives"] = [
            "feature_interior_sample", "surface_detail_point", "boundary_sample"]
        record["semantic_type"]["confidence"] = (
            "SOURCE_FOLDER_AND_FEATURE_ID" if fid else "SOURCE_FOLDER_ONLY")
        record["object_link"] = (
            "FEATURE_CANDIDATE:%s" % fid if fid else None)
    return record


def build_observations() -> Dict[str, Any]:
    roots = [pbc.DERIVED_ROOT]
    observations: List[Dict[str, Any]] = []
    per_campaign: Dict[str, int] = {}
    warnings: Dict[str, int] = {}
    for source_file in sorted(CAMPAIGNS):
        path = os.path.join(pbc.DERIVED_ROOT, source_file)
        _require(os.path.isfile(path), "expected derived file absent: %s" % path)
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        marks = payload["placemarks"]
        _require(len(marks) == pbc.EXPECTED_COUNTS[source_file],
                 "count drift for %s" % source_file)
        for index, mark in enumerate(marks):
            record = adapt(source_file, mark, index)
            observations.append(record)
            per_campaign[record["campaign_id"]] = \
                per_campaign.get(record["campaign_id"], 0) + 1
            for warning in record["warnings"]:
                warnings[warning.split(":")[0]] = warnings.get(
                    warning.split(":")[0], 0) + 1
    ids = [record["observation_id"] for record in observations]
    _require(len(ids) == len(set(ids)), "duplicate observation_id")
    _require(len(observations) == pbc.EXPECTED_TOTAL,
             "observation total %d != %d" % (len(observations), pbc.EXPECTED_TOTAL))
    return {
        "report_id": "PHASE_B_OBSERVATIONS",
        "schema_version": SCHEMA_VERSION,
        "parser_version": PARSER_VERSION,
        "observation_count": len(observations),
        "campaign_counts": dict(sorted(per_campaign.items())),
        "warning_counts": dict(sorted(warnings.items())),
        "status_contract": [
            "MEASURED_GEOMETRY", "DERIVED_GEOMETRY", "IDEALIZED_MODEL",
            "HYPOTHETICAL_MODEL", "UNKNOWN",
        ],
        "boundary_rules": {
            "observation_is_not_object": True,
            "control_point_is_not_archaeological_object": True,
            "survey_marker_is_not_terrain_sample": True,
            "coordinate_is_not_physical_relation": True,
            "proximity_is_not_functional_coupling": True,
            "kml_z_is_elevation": False,
            "unknown_replaced_by_zero": False,
        },
        "roots_checked": roots,
        "observations": observations,
    }


if __name__ == "__main__":
    data = build_observations()
    print(json.dumps({key: data[key] for key in (
        "observation_count", "campaign_counts", "warning_counts")},
        indent=2, sort_keys=True))
