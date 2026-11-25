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
from pathlib import Path
from typing import Any

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
DATASET_ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9._:-]*$")


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


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
    if candidate.is_absolute():
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
        elif source.get("origin") not in ALLOWED_SOURCE_ORIGINS:
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
        elif instrument.get("sensor_type") not in ALLOWED_SENSOR_TYPES:
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
        if not isinstance(sample_count, int) or isinstance(sample_count, bool) or sample_count < 1:
            errors.append(f"{prefix}: sample_count must be a positive integer")
        if acquisition.get("time_standard") not in {"UTC", "GPS", "local_with_offset", "unknown"}:
            errors.append(f"{prefix}: unsupported time_standard {acquisition.get('time_standard')!r}")
        if acquisition.get("time_standard") == "unknown":
            warnings.append(f"{prefix}: time standard is unknown")
        nominal_duration = acquisition.get("nominal_duration_s")
        if nominal_duration is not None and (not _is_number(nominal_duration) or float(nominal_duration) <= 0):
            errors.append(f"{prefix}: nominal_duration_s must be positive when supplied")
        if start is not None and end is not None and _is_number(sample_rate) and isinstance(sample_count, int) and sample_count > 0:
            elapsed = (end - start).total_seconds()
            expected = sample_count / float(sample_rate)
            tolerance = max(2.0 / float(sample_rate), 0.005 * expected)
            if abs(elapsed - expected) > tolerance:
                warnings.append(
                    f"{prefix}: timestamp duration ({elapsed:.6g}s) differs from "
                    f"sample_count/sample_rate ({expected:.6g}s); confirm whether end_time "
                    "marks the final sample or the end boundary"
                )
        if acquisition.get("time_standard") == "unknown":
            warnings.append(f"{prefix}: time standard is unknown")

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
            if component not in ALLOWED_COMPONENTS:
                errors.append(f"{channel_prefix}: unsupported component {component!r}")
            elif isinstance(component, str):
                if component in components and component in REQUIRED_COMPONENTS:
                    errors.append(f"{channel_prefix}: duplicate component {component!r}")
                components.add(component)
            unit = channel.get("unit")
            if unit not in ALLOWED_UNITS:
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
            if role not in ALLOWED_FILE_ROLES:
                errors.append(f"{file_prefix}: unsupported file role {role!r}")
            elif isinstance(role, str):
                roles.add(role)
            file_format = file_record.get("file_format")
            if file_format not in ALLOWED_FILE_FORMATS:
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
            if verify_files and resolved is not None:
                if not resolved.is_file():
                    errors.append(f"{file_prefix}: file does not exist: {raw_path}")
                else:
                    declared_size = file_record.get("size_bytes")
                    if declared_size is not None and (
                        not isinstance(declared_size, int) or isinstance(declared_size, bool)
                        or declared_size < 0
                    ):
                        errors.append(f"{file_prefix}: size_bytes must be a non-negative integer")
                    elif isinstance(declared_size, int) and resolved.stat().st_size != declared_size:
                        errors.append(
                            f"{file_prefix}: size_bytes mismatch for {raw_path}; "
                            f"manifest={declared_size}, actual={resolved.stat().st_size}"
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
            allowed_quality = {
                "status": {"received_unchecked", "metadata_checked", "integrity_checked", "processed", "validated", "quarantined"},
                "calibration_status": {"documented", "partial", "unknown", "not_applicable"},
                "orientation_status": {"documented", "partial", "unknown", "not_applicable"},
                "timing_status": {"documented", "partial", "unknown"},
                "coordinate_status": {"documented", "partial", "unknown"}
            }
            for field, allowed in allowed_quality.items():
                if quality.get(field) not in allowed:
                    errors.append(f"{prefix}: unsupported quality.{field} value {quality.get(field)!r}")
            for field in ("calibration_status", "orientation_status", "timing_status", "coordinate_status"):
                if quality.get(field) in {"unknown", "partial"}:
                    warnings.append(f"{prefix}: quality.{field} is {quality.get(field)}")

    return errors, warnings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True, help="Ambient vibration manifest JSON")
    parser.add_argument("--root", type=Path, default=None, help="Data root for relative file paths; defaults to manifest directory")
    parser.add_argument("--verify-files", action="store_true", help="Check file existence and SHA-256 against actual bytes")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.manifest.is_file():
        print(f"ERROR: manifest not found: {args.manifest}", file=sys.stderr)
        return 2

    try:
        payload = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read manifest: {exc}", file=sys.stderr)
        return 2

    root = args.root or args.manifest.parent
    try:
        errors, warnings = validate_manifest_payload(payload, root=root, verify_files=args.verify_files)
    except OSError as exc:
        print(f"ERROR: file verification failed: {exc}", file=sys.stderr)
        return 2

    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)

    if errors:
        print(f"FAILED: {len(errors)} error(s), {len(warnings)} warning(s)", file=sys.stderr)
        return 2

    print(f"VALID: {len(payload.get('datasets', []))} dataset(s), {len(warnings)} warning(s)")
    if not args.verify_files:
        print("NOTE: file existence and content hashes were not checked; use --verify-files for byte-level validation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
