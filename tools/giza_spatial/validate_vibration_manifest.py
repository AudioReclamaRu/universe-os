#!/usr/bin/env python3
"""Validate GIZA PRIME ambient-vibration metadata and, optionally, raw files.

This utility checks manifest consistency and file provenance. It does not parse
MiniSEED/SAC waveform samples, calibrate instruments, compute spectra, or
interpret HVSR peaks. Those operations require format-aware processing and
separate scientific validation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path, PureWindowsPath
from typing import Any
from urllib.parse import unquote, urlsplit

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError

DEFAULT_SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "schemas"
    / "giza_ambient_vibration_manifest.schema.json"
)
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
REQUIRED_COMPONENTS = {"vertical", "north", "east"}
ALLOWED_SOURCE_ORIGINS = {
    "primary_fieldwork", "primary_archive", "official_publication",
    "secondary_publication", "user_supplied", "derived", "unknown"
}
ALLOWED_SENSOR_TYPES = {
    "seismometer", "geophone", "accelerometer", "velocity_sensor", "other", "unknown"
}
ALLOWED_COMPONENTS = {"vertical", "north", "east", "other", "unknown"}
ALLOWED_UNITS = {"counts", "m/s", "m/s2", "m", "unknown"}
ALLOWED_FILE_ROLES = {
    "raw", "calibrated", "oriented", "segmented", "processed",
    "derived", "metadata", "report", "field_photo"
}
ALLOWED_FILE_FORMATS = {"mseed", "sac", "csv", "ascii", "wav", "seg2", "other"}
ALLOWED_TIME_STANDARDS = {"UTC", "GPS", "local_with_offset", "unknown"}
ALLOWED_QUALITY_VALUES = {
    "status": {"received_unchecked", "metadata_checked", "integrity_checked", "processed", "validated", "quarantined"},
    "calibration_status": {"documented", "partial", "unknown", "not_applicable"},
    "orientation_status": {"documented", "partial", "unknown", "not_applicable"},
    "timing_status": {"documented", "partial", "unknown"},
    "coordinate_status": {"documented", "partial", "unknown"},
}
DATASET_ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9._:-]*$")


def _reject_nonstandard_json_constant(token: str) -> None:
    raise ValueError(f"non-standard JSON numeric constant is not allowed: {token}")


def _reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key is not allowed: {key!r}")
        result[key] = value
    return result


def _strict_json_float(token: str) -> float:
    try:
        value = float(token)
        exact = Decimal(token)
    except (ValueError, InvalidOperation, OverflowError) as exc:
        raise ValueError(f"invalid JSON number: {token}") from exc
    if not math.isfinite(value):
        raise ValueError(f"JSON number exceeds supported finite range: {token}")
    if value == 0.0 and not exact.is_zero():
        raise ValueError(f"JSON number underflows supported numeric precision: {token}")
    return value


def _strict_json_loads(raw: str) -> Any:
    """Parse standard JSON while rejecting duplicate keys and NaN/Infinity."""
    return json.loads(
        raw,
        object_pairs_hook=_reject_duplicate_json_keys,
        parse_constant=_reject_nonstandard_json_constant,
        parse_float=_strict_json_float,
    )


_SINGLE_SCHEMA_KEYWORDS = (
    "additionalItems",
    "additionalProperties",
    "unevaluatedItems",
    "unevaluatedProperties",
    "propertyNames",
    "contains",
    "items",
    "not",
    "if",
    "then",
    "else",
    "contentSchema",
)
_SCHEMA_ARRAY_KEYWORDS = ("allOf", "anyOf", "oneOf", "prefixItems")
_SCHEMA_MAP_KEYWORDS = (
    "$defs",
    "definitions",
    "properties",
    "patternProperties",
    "dependentSchemas",
)


def _iter_schema_references(schema: Any, path: str = "$"):
    """Walk only schema-bearing keywords, not literal const/default/example data."""
    if not isinstance(schema, dict):
        return

    for key in ("$ref", "$dynamicRef", "$recursiveRef"):
        if key in schema:
            yield f"{path}.{key}", schema[key]

    for key in _SINGLE_SCHEMA_KEYWORDS:
        child = schema.get(key)
        if isinstance(child, (dict, bool)):
            yield from _iter_schema_references(child, f"{path}.{key}")
        elif key == "items" and isinstance(child, list):
            for index, item in enumerate(child):
                yield from _iter_schema_references(item, f"{path}.{key}[{index}]")

    for key in _SCHEMA_ARRAY_KEYWORDS:
        children = schema.get(key)
        if isinstance(children, list):
            for index, child in enumerate(children):
                yield from _iter_schema_references(child, f"{path}.{key}[{index}]")

    for key in _SCHEMA_MAP_KEYWORDS:
        children = schema.get(key)
        if isinstance(children, dict):
            for name, child in children.items():
                yield from _iter_schema_references(child, f"{path}.{key}.{name}")


def _validate_local_schema_references(schema: Any) -> None:
    """Allow only resolvable local JSON Pointer references; never retrieve remote schemas."""
    for location, reference in _iter_schema_references(schema):
        if not isinstance(reference, str):
            raise ValueError(f"{location}: schema reference must be a string")
        parsed = urlsplit(reference)
        if parsed.scheme or parsed.netloc or parsed.path or parsed.query:
            raise ValueError(
                f"{location}: external schema references are not allowed: {reference!r}"
            )
        fragment = unquote(parsed.fragment)
        if not fragment:
            continue
        if not fragment.startswith("/"):
            raise ValueError(
                f"{location}: only local JSON Pointer references are supported: {reference!r}"
            )

        target = schema
        for encoded_token in fragment[1:].split("/"):
            if re.search(r"~(?![01])", encoded_token):
                raise ValueError(
                    f"{location}: invalid JSON Pointer escape in {reference!r}"
                )
            token = encoded_token.replace("~1", "/").replace("~0", "~")
            if isinstance(target, dict) and token in target:
                target = target[token]
            elif isinstance(target, list) and token.isdigit() and int(token) < len(target):
                target = target[int(token)]
            else:
                raise ValueError(
                    f"{location}: unresolved local JSON Pointer reference: {reference!r}"
                )


def _is_number(value: Any) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(float(value))
    except (OverflowError, ValueError):
        return False


def _is_allowed_string(value: Any, allowed: set[str]) -> bool:
    return isinstance(value, str) and value in allowed


def _is_integer(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, int):
        return True
    return isinstance(value, float) and math.isfinite(value) and value.is_integer()


def _parse_aware_datetime(value: Any, label: str, errors: list[str]) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{label}: missing ISO-8601 datetime")
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        result = datetime.fromisoformat(normalized)
    except ValueError:
        errors.append(f"{label}: invalid ISO-8601 datetime {value!r}")
        return None
    if result.tzinfo is None or result.utcoffset() is None:
        errors.append(f"{label}: timezone offset is required")
        return None
    return result


def _safe_relative_path(raw_path: Any, root: Path, label: str, errors: list[str]) -> Path | None:
    if not isinstance(raw_path, str) or not raw_path.strip():
        errors.append(f"{label}: path is empty")
        return None
    candidate = Path(raw_path)
    windows_candidate = PureWindowsPath(raw_path)
    if candidate.is_absolute() or windows_candidate.is_absolute() or windows_candidate.drive:
        errors.append(f"{label}: absolute paths are not allowed: {raw_path}")
        return None
    try:
        resolved_root = root.resolve()
        resolved = (resolved_root / candidate).resolve()
        resolved.relative_to(resolved_root)
    except (OSError, ValueError):
        errors.append(f"{label}: path escapes the declared data root: {raw_path}")
        return None
    return resolved


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_manifest_payload(
    payload: Any,
    root: Path | None = None,
    verify_files: bool = False,
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(payload, dict):
        return ["manifest root must be a JSON object"], warnings

    if payload.get("schema_version") != "1.0":
        errors.append("schema_version must be '1.0'")

    project = payload.get("project")
    if not isinstance(project, dict) or not project.get("id") or not project.get("title"):
        errors.append("project must contain non-empty id and title")

    datasets = payload.get("datasets")
    if not isinstance(datasets, list):
        errors.append("datasets must be an array")
        return errors, warnings

    if not datasets:
        warnings.append("manifest contains no datasets; this is valid as an empty intake template")

    root_path = root or Path.cwd()
    dataset_ids: set[str] = set()

    for index, dataset in enumerate(datasets):
        prefix = f"datasets[{index}]"
        if not isinstance(dataset, dict):
            errors.append(f"{prefix}: dataset must be an object")
            continue

        dataset_id = dataset.get("dataset_id")
        if not isinstance(dataset_id, str) or not dataset_id.strip():
            errors.append(f"{prefix}: dataset_id is required")
        elif not DATASET_ID_RE.fullmatch(dataset_id):
            errors.append(f"{prefix}: dataset_id contains unsupported characters")
        elif dataset_id in dataset_ids:
            errors.append(f"{prefix}: duplicate dataset_id {dataset_id!r}")
        else:
            dataset_ids.add(dataset_id)

        source = dataset.get("source")
        if not isinstance(source, dict) or not source.get("origin") or not source.get("title"):
            errors.append(f"{prefix}: source.origin and source.title are required")
        elif not _is_allowed_string(source.get("origin"), ALLOWED_SOURCE_ORIGINS):
            errors.append(f"{prefix}: unsupported source.origin {source.get('origin')!r}")

        station = dataset.get("station")
        if not isinstance(station, dict) or not station.get("station_id"):
            errors.append(f"{prefix}: station.station_id is required")
        else:
            location = station.get("location")
            if not isinstance(location, dict):
                errors.append(f"{prefix}: station.location is required")
            else:
                for axis in ("x", "y"):
                    if not _is_number(location.get(axis)):
                        errors.append(f"{prefix}: station.location.{axis} must be finite")
                if not isinstance(location.get("coordinate_system"), str) or not location.get("coordinate_system").strip():
                    errors.append(f"{prefix}: coordinate_system is required")

        instrument = dataset.get("instrument")
        if not isinstance(instrument, dict) or not instrument.get("sensor_type") or not instrument.get("model"):
            errors.append(f"{prefix}: instrument.sensor_type and instrument.model are required")
        elif not _is_allowed_string(instrument.get("sensor_type"), ALLOWED_SENSOR_TYPES):
            errors.append(f"{prefix}: unsupported instrument.sensor_type {instrument.get('sensor_type')!r}")

        acquisition = dataset.get("acquisition")
        if not isinstance(acquisition, dict):
            errors.append(f"{prefix}: acquisition is required")
            acquisition = {}
        start = _parse_aware_datetime(acquisition.get("start_time"), f"{prefix}.acquisition.start_time", errors)
        end = _parse_aware_datetime(acquisition.get("end_time"), f"{prefix}.acquisition.end_time", errors)
        if start is not None and end is not None and end <= start:
            errors.append(f"{prefix}: end_time must be later than start_time")

        sample_rate = acquisition.get("sample_rate_hz")
        if not _is_number(sample_rate) or float(sample_rate) <= 0:
            errors.append(f"{prefix}: sample_rate_hz must be a finite positive number")
        sample_count = acquisition.get("sample_count")
        if not _is_integer(sample_count) or sample_count < 1:
            errors.append(f"{prefix}: sample_count must be a positive integer")
        if not _is_allowed_string(acquisition.get("time_standard"), ALLOWED_TIME_STANDARDS):
            errors.append(f"{prefix}: unsupported time_standard {acquisition.get('time_standard')!r}")
        if acquisition.get("time_standard") == "unknown":
            warnings.append(f"{prefix}: time standard is unknown")
        nominal_duration = acquisition.get("nominal_duration_s")
        if nominal_duration is not None and (not _is_number(nominal_duration) or float(nominal_duration) <= 0):
            errors.append(f"{prefix}: nominal_duration_s must be positive when supplied")
        if (start is not None and end is not None and _is_number(sample_rate)
                and float(sample_rate) > 0 and _is_integer(sample_count) and sample_count > 0):
            elapsed = (end - start).total_seconds()
            try:
                expected = int(sample_count) / float(sample_rate)
            except OverflowError:
                errors.append(f"{prefix}: sample_count exceeds the supported duration calculation range")
            else:
                tolerance = max(2.0 / float(sample_rate), 0.005 * expected)
                if abs(elapsed - expected) > tolerance:
                    warnings.append(
                        f"{prefix}: timestamp duration ({elapsed:.6g}s) differs from "
                        f"sample_count/sample_rate ({expected:.6g}s); confirm whether end_time "
                        "marks the final sample or the end boundary"
                    )


        channels = dataset.get("channels")
        if not isinstance(channels, list) or not channels:
            errors.append(f"{prefix}: at least one channel is required")
            channels = []
        channel_ids: set[str] = set()
        components: set[str] = set()
        for channel_index, channel in enumerate(channels):
            channel_prefix = f"{prefix}.channels[{channel_index}]"
            if not isinstance(channel, dict):
                errors.append(f"{channel_prefix}: channel must be an object")
                continue
            channel_id = channel.get("channel_id")
            if not isinstance(channel_id, str) or not channel_id.strip():
                errors.append(f"{channel_prefix}: channel_id is required")
            elif channel_id in channel_ids:
                errors.append(f"{channel_prefix}: duplicate channel_id {channel_id!r}")
            else:
                channel_ids.add(channel_id)
            component = channel.get("component")
            if not _is_allowed_string(component, ALLOWED_COMPONENTS):
                errors.append(f"{channel_prefix}: unsupported component {component!r}")
            elif isinstance(component, str):
                if component in components and component in REQUIRED_COMPONENTS:
                    errors.append(f"{channel_prefix}: duplicate component {component!r}")
                components.add(component)
            unit = channel.get("unit")
            if not _is_allowed_string(unit, ALLOWED_UNITS):
                errors.append(f"{channel_prefix}: unsupported unit {unit!r}")
            azimuth = channel.get("azimuth_deg")
            if azimuth is not None and (not _is_number(azimuth) or not 0 <= float(azimuth) <= 360):
                errors.append(f"{channel_prefix}: azimuth_deg must be between 0 and 360")
            dip = channel.get("dip_deg")
            if dip is not None and (not _is_number(dip) or not -90 <= float(dip) <= 90):
                errors.append(f"{channel_prefix}: dip_deg must be between -90 and 90")
            if channel.get("unit") == "counts" and not _is_number(channel.get("sensitivity")):
                warnings.append(
                    f"{channel_prefix}: counts channel has no documented positive sensitivity; "
                    "physical-unit conversion is not established"
                )
            sensitivity = channel.get("sensitivity")
            if sensitivity is not None and (not _is_number(sensitivity) or float(sensitivity) <= 0):
                errors.append(f"{channel_prefix}: sensitivity must be positive when supplied")

        if dataset.get("require_three_components", True):
            missing = REQUIRED_COMPONENTS - components
            if missing:
                errors.append(
                    f"{prefix}: three-component dataset is missing: {', '.join(sorted(missing))}"
                )

        files = dataset.get("files")
        if not isinstance(files, list) or not files:
            errors.append(f"{prefix}: at least one file record is required")
            files = []
        file_ids: set[str] = set()
        roles: set[str] = set()
        file_paths: set[str] = set()
        resolved_paths: set[Path] = set()
        derived_refs: list[tuple[str, list[str]]] = []
        for file_index, file_record in enumerate(files):
            file_prefix = f"{prefix}.files[{file_index}]"
            if not isinstance(file_record, dict):
                errors.append(f"{file_prefix}: file record must be an object")
                continue

            file_id = file_record.get("file_id")
            if not isinstance(file_id, str) or not file_id.strip():
                errors.append(f"{file_prefix}: file_id is required")
            elif file_id in file_ids:
                errors.append(f"{file_prefix}: duplicate file_id {file_id!r}")
            else:
                file_ids.add(file_id)

            role = file_record.get("role")
            if not _is_allowed_string(role, ALLOWED_FILE_ROLES):
                errors.append(f"{file_prefix}: unsupported file role {role!r}")
            elif isinstance(role, str):
                roles.add(role)
            file_format = file_record.get("file_format")
            if not _is_allowed_string(file_format, ALLOWED_FILE_FORMATS):
                errors.append(f"{file_prefix}: unsupported file_format {file_format!r}")
            derived = file_record.get("derived_from_file_ids", [])
            if not isinstance(derived, list) or any(not isinstance(x, str) for x in derived):
                errors.append(f"{file_prefix}: derived_from_file_ids must be an array of strings")
            else:
                derived_refs.append((file_prefix, derived))
            raw_path = file_record.get("path")
            if isinstance(raw_path, str):
                if raw_path in file_paths:
                    errors.append(f"{file_prefix}: duplicate path {raw_path!r}")
                file_paths.add(raw_path)

            expected_hash = file_record.get("sha256")
            if not isinstance(expected_hash, str) or not SHA256_RE.fullmatch(expected_hash):
                errors.append(f"{file_prefix}: sha256 must contain exactly 64 hexadecimal characters")

            resolved = _safe_relative_path(raw_path, root_path, file_prefix, errors)
            if resolved is not None:
                if resolved in resolved_paths:
                    errors.append(
                        f"{file_prefix}: multiple file records resolve to the same path: {raw_path!r}"
                    )
                else:
                    resolved_paths.add(resolved)
            if verify_files and resolved is not None:
                if not resolved.is_file():
                    errors.append(f"{file_prefix}: file does not exist: {raw_path}")
                else:
                    declared_size = file_record.get("size_bytes")
                    if declared_size is not None and (
                        not _is_integer(declared_size) or declared_size < 0
                    ):
                        errors.append(f"{file_prefix}: size_bytes must be a non-negative integer")
                    elif _is_integer(declared_size) and resolved.stat().st_size != int(declared_size):
                        errors.append(
                            f"{file_prefix}: size_bytes mismatch for {raw_path}; "
                            f"manifest={int(declared_size)}, actual={resolved.stat().st_size}"
                        )
                    if isinstance(expected_hash, str) and SHA256_RE.fullmatch(expected_hash):
                        actual = _sha256(resolved)
                        if actual.lower() != expected_hash.lower():
                            errors.append(
                                f"{file_prefix}: SHA-256 mismatch for {raw_path}; expected "
                                f"{expected_hash.lower()}, got {actual}"
                            )

        for file_prefix, refs in derived_refs:
            for ref in refs:
                if ref not in file_ids:
                    errors.append(f"{file_prefix}: derived_from_file_id {ref!r} does not exist in this dataset")

        if "raw" not in roles:
            errors.append(f"{prefix}: at least one raw file record is required")

        quality = dataset.get("quality")
        if not isinstance(quality, dict):
            errors.append(f"{prefix}: quality object is required")
        else:
            allowed_quality = ALLOWED_QUALITY_VALUES
            for field, allowed in allowed_quality.items():
                if not _is_allowed_string(quality.get(field), allowed):
                    errors.append(f"{prefix}: unsupported quality.{field} value {quality.get(field)!r}")
            for field in ("calibration_status", "orientation_status", "timing_status", "coordinate_status"):
                if isinstance(quality.get(field), str) and quality.get(field) in {"unknown", "partial"}:
                    warnings.append(f"{prefix}: quality.{field} is {quality.get(field)}")

    return errors, warnings


def validate_json_schema_payload(payload: Any, schema_path: Path) -> list[str]:
    """Validate a manifest against its Draft 2020-12 JSON Schema."""
    schema_payload = _strict_json_loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema_payload)
    _validate_local_schema_references(schema_payload)
    validator = Draft202012Validator(
        schema_payload,
        format_checker=FormatChecker(),
    )
    validation_errors = sorted(
        validator.iter_errors(payload),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )

    messages: list[str] = []
    for error in validation_errors:
        location = "$"
        for part in error.absolute_path:
            location += f"[{part}]" if isinstance(part, int) else f".{part}"
        messages.append(f"JSON Schema {location}: {error.message}")
    return messages


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True, help="Ambient vibration manifest JSON")
    parser.add_argument(
        "--schema",
        type=Path,
        default=DEFAULT_SCHEMA_PATH,
        help="Draft 2020-12 JSON Schema; defaults to the repository schema",
    )
    parser.add_argument("--root", type=Path, default=None, help="Data root for relative file paths; defaults to manifest directory")
    parser.add_argument("--verify-files", action="store_true", help="Check file existence and SHA-256 against actual bytes")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.manifest.is_file():
        print(f"ERROR: manifest not found: {args.manifest}", file=sys.stderr)
        return 2

    try:
        payload = _strict_json_loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"ERROR: cannot read manifest: {exc}", file=sys.stderr)
        return 2

    try:
        schema_errors = validate_json_schema_payload(payload, args.schema)
    except (OSError, ValueError, SchemaError) as exc:
        print(f"ERROR: JSON Schema validation could not run: {exc}", file=sys.stderr)
        return 2

    root = args.root or args.manifest.parent
    try:
        errors, warnings = validate_manifest_payload(payload, root=root, verify_files=args.verify_files)
    except OSError as exc:
        print(f"ERROR: file verification failed: {exc}", file=sys.stderr)
        return 2

    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in schema_errors:
        print(f"ERROR: {error}", file=sys.stderr)
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)

    total_errors = len(schema_errors) + len(errors)
    if total_errors:
        print(f"FAILED: {total_errors} error(s), {len(warnings)} warning(s)", file=sys.stderr)
        return 2

    print(f"VALID: {len(payload.get('datasets', []))} dataset(s), {len(warnings)} warning(s)")
    if not args.verify_files:
        print("NOTE: file existence and content hashes were not checked; use --verify-files for byte-level validation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
