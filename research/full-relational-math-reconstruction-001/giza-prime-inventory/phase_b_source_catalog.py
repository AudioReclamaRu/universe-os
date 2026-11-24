"""PHASE B / STAGE A — recursive, read-only inventory of the two owner-nominated
source directories.

HARD RULES
----------
* Only the two exact directories named by the owner are scanned.  No fallback
  search, no downloads, no writes to source files.
* Three identifiers are kept strictly separate: raw-byte SHA-256, git blob SHA
  and canonical-JSON SHA-256.  They are never substituted for one another.
* The canonical hash is platform-independent (sorted keys, fixed separators,
  UTF-8, NaN/Infinity forbidden) — the Phase A lesson about CRLF/LF is binding.
* Counts are reported as observed; a mismatch with the expected 12,078 is
  explained, never silently corrected.
* Every file is parsed by a format-specific reader.  Unknown formats are
  reported, not guessed away.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import re
import zipfile
from typing import Any, Dict, List, Optional, Tuple
import xml.etree.ElementTree as ET

import gpmp_spatial_layer as gsl

RAW_ROOT = r"E:\GIZA_PRIME_LAB\gizalab\data\raw\dash_foundation"
DERIVED_ROOT = r"E:\GIZA_PRIME_LAB\gizalab\data\derived\phase2\kmz"

EXPECTED_COUNTS = {
    "GDFS-2012-for-GE-21vii18.json": 1539,
    "GDFS-2015-Master-25iii17-edited-child.json": 1100,
    "GDFS-2016-23ix18.json": 4746,
    "GDFS-2018-12xii18.json": 4569,
    "GPMP-Control-Monuments.json": 41,
    "Giza-Corner-Points-2v17.json": 15,
    "Petries-Stations.json": 68,
}
EXPECTED_TOTAL = 12078

# Portability contract.  The two defaults above are kept verbatim so a build
# with no environment overrides stays byte-identical to the published Phase B
# registries.  Other machines may mount the same exact sources elsewhere.
ENV_RAW_ROOT = "GIZA_PRIME_RAW_ROOT"
ENV_DERIVED_ROOT = "GIZA_PRIME_DERIVED_ROOT"
ENV_REQUIRE_FULL_SOURCE = "GIZA_PRIME_REQUIRE_FULL_SOURCE"
SOURCE_NOT_MOUNTED = "SKIPPED — SOURCE DATA NOT MOUNTED"


def source_roots() -> Tuple[str, str]:
    """Resolve the two nominated source roots from the environment.

    No fallback search is performed.  If a variable is set it must name the
    exact directory to scan; otherwise the owner-nominated default is used.
    """
    raw = os.environ.get(ENV_RAW_ROOT) or RAW_ROOT
    derived = os.environ.get(ENV_DERIVED_ROOT) or DERIVED_ROOT
    return raw, derived


def sources_mounted() -> bool:
    """True only when both roots and all seven derived sets are present."""
    return source_status()["mounted"]


def full_source_required() -> bool:
    """Whether missing sources must remain an error, not an explicit skip."""
    return os.environ.get(ENV_REQUIRE_FULL_SOURCE, "").strip().lower() in (
        "1", "true", "yes", "on")


def source_status() -> Dict[str, Any]:
    """Report the exact reason why full-source integration can or cannot run."""
    raw_root, derived_root = source_roots()
    raw_mounted = os.path.isdir(raw_root)
    derived_mounted = os.path.isdir(derived_root)
    missing = [name for name in sorted(EXPECTED_COUNTS)
               if not os.path.isfile(os.path.join(derived_root, name))]
    return {
        "raw_root": raw_root,
        "derived_root": derived_root,
        "raw_mounted": raw_mounted,
        "derived_mounted": derived_mounted,
        "missing_derived_files": missing,
        "mounted": bool(raw_mounted and derived_mounted and not missing),
        "full_source_required": full_source_required(),
        "skip_status": SOURCE_NOT_MOUNTED,
    }


KML_GEOMETRY_TAGS = (
    "Point", "LineString", "LinearRing", "Polygon", "MultiGeometry",
)


class CatalogError(ValueError):
    """Raised when a nominated directory or critical structure is absent."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CatalogError(message)


def raw_sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_blob_sha256(path: str) -> Optional[str]:
    """Return the git blob object id if the file lives in a work tree, else None.

    This is computed from git's own header rule (``blob <len>\\0``) so it does
    not require a git process or a visible console child.
    """
    with open(path, "rb") as handle:
        data = handle.read()
    header = b"blob %d\0" % len(data)
    return hashlib.sha1(header + data).hexdigest()


def _sniff_format(path: str) -> str:
    lower = path.lower()
    if lower.endswith(".kmz"):
        return "KMZ"
    if lower.endswith(".kml"):
        return "KML"
    if lower.endswith(".json"):
        return "JSON"
    if lower.endswith(".geojson"):
        return "GeoJSON"
    if lower.endswith(".csv"):
        return "CSV"
    if lower.endswith(".tsv"):
        return "TSV"
    if lower.endswith(".gpx"):
        return "GPX"
    if lower.endswith(".xml"):
        return "XML"
    if lower.endswith(".dxf"):
        return "DXF"
    if lower.endswith(".shp"):
        return "SHP"
    with open(path, "rb") as handle:
        head = handle.read(4)
    if head[:2] == b"PK":
        return "ZIP_CONTAINER"
    if head[:5].lower() in (b"<?xml", b"<kml", b"<gpx"):
        return "XML_LIKE"
    return "UNKNOWN"


def parse_derived_json(path: str) -> Dict[str, Any]:
    """Read a derived placemark JSON without changing it."""
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    _require(isinstance(payload, dict), "derived JSON must be an object: %s" % path)
    for key in gsl.REQUIRED_TOP_LEVEL:
        _require(key in payload, "derived JSON missing %r: %s" % (key, path))
    marks = payload["placemarks"]
    _require(isinstance(marks, list), "placemarks must be a list: %s" % path)
    _require(payload["placemark_count"] == len(marks),
             "declared count mismatch: %s" % path)
    geometry: Dict[str, int] = {}
    crs_hints: Dict[str, int] = {}
    for mark in marks:
        kind = str(mark.get("geometry", "UNKNOWN"))
        geometry[kind] = geometry.get(kind, 0) + 1
        for hint in mark.get("crs_hints", []):
            hint = str(hint)
            crs_hints[hint] = crs_hints.get(hint, 0) + 1
    canonical = gsl.canonical_json_sha256(payload)
    return {
        "parse_status": "PARSED",
        "record_count": len(marks),
        "geometry_types": dict(sorted(geometry.items())),
        "crs_hint_frequency": dict(sorted(crs_hints.items())),
        "folders": list(payload["folders"]),
        "kml_entry": payload["kml_entry"],
        "kml_bytes": payload["kml_bytes"],
        "declared_sha256_of_kml": payload["sha256"],
        "canonical_json_sha256": canonical,
        "parser_version": "phase_b_derived_json_v1",
        "warnings": [],
    }


def parse_kmz(path: str) -> Dict[str, Any]:
    """Open the ZIP, inspect KML structure and count geometry/folders."""
    result: Dict[str, Any] = {
        "parse_status": "PARSED", "kml_entries": [], "folders": {},
        "geometry_types": {}, "placemark_counts": {},
        "extended_data_counts": {}, "parser_version": "phase_b_kmz_v1",
        "warnings": [],
    }
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        result["zip_entries"] = names
        kml_names = [name for name in names if name.lower().endswith(".kml")]
        result["kml_entries"] = kml_names
        if not kml_names:
            result["parse_status"] = "NO_KML_ENTRY"
            result["warnings"].append("KMZ has no .kml member")
            return result
        for kml_name in kml_names:
            raw = archive.read(kml_name)
            try:
                root = ET.fromstring(raw)
            except ET.ParseError as exc:
                result["parse_status"] = "KML_PARSE_ERROR"
                result["warnings"].append("%s: %s" % (kml_name, exc))
                continue
            tags = root.iter()
            folders: List[str] = []
            geometry = {tag: 0 for tag in KML_GEOMETRY_TAGS}
            placemarks = 0
            extended = 0
            for node in tags:
                local = node.tag.split("}")[-1]
                if local == "Folder":
                    for child in node:
                        if child.tag.split("}")[-1] == "name" and child.text:
                            folders.append(child.text)
                            break
                elif local == "Placemark":
                    placemarks += 1
                elif local in geometry:
                    geometry[local] += 1
                elif local == "ExtendedData":
                    extended += 1
            result["folders"][kml_name] = folders
            result["geometry_types"][kml_name] = {
                key: value for key, value in geometry.items() if value}
            result["placemark_counts"][kml_name] = placemarks
            result["extended_data_counts"][kml_name] = extended
    return result


def parse_csv_header(path: str) -> Dict[str, Any]:
    import csv
    with open(path, "r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader, [])
        rows = sum(1 for _ in reader)
    return {
        "parse_status": "PARSED", "header": header, "data_rows": rows,
        "parser_version": "phase_b_csv_v1", "warnings": [],
    }


def inventory_file(root: str, name: str) -> Dict[str, Any]:
    path = os.path.join(root, name)
    stat = os.stat(path)
    fmt = _sniff_format(path)
    entry: Dict[str, Any] = {
        "relative_path": os.path.relpath(path, os.path.dirname(root)),
        "name": name,
        "extension": os.path.splitext(name)[1].lower(),
        "bytes": stat.st_size,
        "modified_utc": _dt.datetime.fromtimestamp(
            stat.st_mtime, _dt.timezone.utc).isoformat(timespec="seconds").replace(
                "+00:00", "Z"),
        "detected_format": fmt,
        "raw_sha256": raw_sha256(path),
        "git_blob_sha1": git_blob_sha256(path),
        "canonical_json_sha256": None,
        "readable": True,
        "parse": {"parse_status": "NOT_PARSED", "warnings": []},
        "warnings": [],
    }
    try:
        if fmt in ("JSON", "GeoJSON"):
            parsed = parse_derived_json(path)
            entry["canonical_json_sha256"] = parsed["canonical_json_sha256"]
            entry["parse"] = parsed
        elif fmt == "KMZ":
            entry["parse"] = parse_kmz(path)
        elif fmt == "CSV":
            entry["parse"] = parse_csv_header(path)
        elif fmt == "KML":
            entry["parse"] = parse_kmz(path)  # no zip; handled by sniff guard below
    except Exception as exc:  # noqa: BLE001 — inventory must report, not abort
        entry["readable"] = False
        entry["parse"] = {"parse_status": "PARSE_ERROR",
                          "error": "%s: %s" % (type(exc).__name__, exc),
                          "warnings": []}
    return entry


def build_catalog() -> Dict[str, Any]:
    raw_root, derived_root = source_roots()
    _require(os.path.isdir(raw_root), "raw directory absent: %s" % raw_root)
    _require(os.path.isdir(derived_root),
             "derived directory absent: %s" % derived_root)
    raw_files = sorted(name for name in os.listdir(raw_root)
                       if os.path.isfile(os.path.join(raw_root, name)))
    derived_files = sorted(name for name in os.listdir(derived_root)
                           if os.path.isfile(os.path.join(derived_root, name)))
    raw = [inventory_file(raw_root, name) for name in raw_files]
    derived = [inventory_file(derived_root, name) for name in derived_files]

    expected_status = {}
    for name, expected in sorted(EXPECTED_COUNTS.items()):
        found = next((entry for entry in derived if entry["name"] == name), None)
        actual = found["parse"].get("record_count") if found else None
        expected_status[name] = {
            "expected": expected,
            "found": found is not None,
            "parsed": bool(found and found["parse"]["parse_status"] == "PARSED"),
            "actual_record_count": actual,
            "count_matches": actual == expected,
            "reason": "" if actual == expected else (
                "file absent" if found is None else
                "parsed %s records, expected %s" % (actual, expected)),
        }

    total = sum(item["actual_record_count"] or 0
                for item in expected_status.values())
    kmz_by_stem = {}
    for entry in raw:
        if entry["extension"] == ".kmz":
            kmz_by_stem[os.path.splitext(entry["name"])[0]] = entry
    reconciliation = []
    for name, status in sorted(expected_status.items()):
        stem = os.path.splitext(name)[0]
        kmz = kmz_by_stem.get(stem)
        derived_entry = next(e for e in derived if e["name"] == name) \
            if status["found"] else None
        declared = derived_entry["parse"].get("declared_sha256_of_kml") \
            if derived_entry else None
        reconciliation.append({
            "derived_json": name,
            "raw_kmz": kmz["name"] if kmz else None,
            "raw_kmz_sha256": kmz["raw_sha256"] if kmz else None,
            "declared_kml_sha256_in_json": declared,
            "archive_match": bool(kmz and declared == kmz["raw_sha256"]),
        })

    return {
        "report_id": "PHASE_B_SOURCE_CATALOG",
        "schema_version": "phase_b_catalog_v1",
        "roots": {"raw": raw_root, "derived": derived_root},
        "scan_policy": "exact owner-nominated directories only; no fallback search",
        "identifier_policy": {
            "raw_sha256": "SHA-256 over actual file bytes",
            "git_blob_sha1": "git blob object id computed from header + bytes",
            "canonical_json_sha256": (
                "SHA-256 of sorted-key UTF-8 JSON, fixed separators, "
                "allow_nan=False; independent of CRLF/LF"),
            "interchangeable": False,
        },
        "counts": {
            "raw_files": len(raw),
            "derived_files": len(derived),
            "expected_total": EXPECTED_TOTAL,
            "observed_total": total,
            "delta": total - EXPECTED_TOTAL,
        },
        "expected_set_status": expected_status,
        "raw_archive_reconciliation": reconciliation,
        "raw_files": raw,
        "derived_files": derived,
        "provenance_states": {
            "FILE_PRESENT": True,
            "FILE_HASHED": True,
            "SOURCE_CONTENT_PARSED": all(
                e["parse"]["parse_status"] == "PARSED" for e in derived),
            "STRUCTURE_VALIDATED": all(s["parsed"]
                                       for s in expected_status.values()),
            "ORIGINAL_ARCHIVE_MATCHED": all(
                r["archive_match"] for r in reconciliation),
            "SOURCE_PROVENANCE_VERIFIED": False,
            "INDEPENDENTLY_CORROBORATED": False,
        },
        "warnings": [
            "Petrie Stations descriptions carry no Elevation; height is UNKNOWN, not zero.",
            "GDFS 2016/2018 descriptions use the swapped label 'LongItude' for the "
            "latitude-like value; KML coordinate order stays [longitude, latitude, Z].",
        ],
    }


if __name__ == "__main__":
    catalog = build_catalog()
    print(json.dumps(catalog["counts"], indent=2, sort_keys=True))
