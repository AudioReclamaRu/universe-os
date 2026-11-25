import copy
import hashlib
import io
import json
import sys
from contextlib import redirect_stderr, redirect_stdout
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "giza_spatial"))
from validate_vibration_manifest import (
    DEFAULT_SCHEMA_PATH,
    main,
    validate_json_schema_payload,
    validate_manifest_payload,
)


def make_manifest(raw_hash: str) -> dict:
    return {
        "schema_version": "1.0",
        "project": {"id": "GIZA-PRIME-TEST", "title": "Synthetic test"},
        "datasets": [{
            "dataset_id": "VIB-TEST-001",
            "title": "Synthetic three-component station",
            "source": {
                "origin": "user_supplied",
                "title": "Synthetic unit-test record",
                "source_uris": []
            },
            "station": {
                "station_id": "ST-001",
                "location": {
                    "x": 100.0,
                    "y": 200.0,
                    "z": 10.0,
                    "coordinate_system": "SYNTHETIC-LOCAL",
                    "horizontal_unit": "m",
                    "vertical_datum": "local-test"
                }
            },
            "instrument": {
                "sensor_type": "seismometer",
                "manufacturer": "Synthetic",
                "model": "TEST-3C"
            },
            "acquisition": {
                "start_time": "2026-01-01T00:00:00Z",
                "end_time": "2026-01-01T00:01:00Z",
                "time_standard": "UTC",
                "sample_rate_hz": 100.0,
                "sample_count": 6000
            },
            "channels": [
                {"channel_id": "Z", "component": "vertical", "unit": "m/s"},
                {"channel_id": "N", "component": "north", "unit": "m/s"},
                {"channel_id": "E", "component": "east", "unit": "m/s"}
            ],
            "require_three_components": True,
            "files": [{
                "file_id": "RAW-001",
                "role": "raw",
                "path": "raw/station01.mseed",
                "file_format": "mseed",
                "sha256": raw_hash
            }],
            "quality": {
                "status": "received_unchecked",
                "calibration_status": "documented",
                "orientation_status": "documented",
                "timing_status": "documented",
                "coordinate_status": "documented"
            }
        }]
    }


class VibrationManifestTests(unittest.TestCase):
    def test_empty_template_is_valid_with_warning(self):
        payload = {
            "schema_version": "1.0",
            "project": {"id": "EMPTY", "title": "Empty template"},
            "datasets": []
        }
        errors, warnings = validate_manifest_payload(payload)
        self.assertEqual(errors, [])
        self.assertTrue(any("no datasets" in warning for warning in warnings))

    def test_valid_three_component_manifest_and_file_hash(self):
        raw_bytes = b"synthetic waveform bytes, not a real field record"
        digest = hashlib.sha256(raw_bytes).hexdigest()
        payload = make_manifest(digest)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw_dir = root / "raw"
            raw_dir.mkdir()
            (raw_dir / "station01.mseed").write_bytes(raw_bytes)
            errors, warnings = validate_manifest_payload(payload, root=root, verify_files=True)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_rejects_missing_horizontal_component(self):
        payload = make_manifest("a" * 64)
        payload["datasets"][0]["channels"] = payload["datasets"][0]["channels"][:2]
        errors, _ = validate_manifest_payload(payload)
        self.assertTrue(any("three-component dataset is missing" in error for error in errors))

    def test_rejects_naive_datetime(self):
        payload = make_manifest("a" * 64)
        payload["datasets"][0]["acquisition"]["start_time"] = "2026-01-01T00:00:00"
        errors, _ = validate_manifest_payload(payload)
        self.assertTrue(any("timezone offset is required" in error for error in errors))

    def test_rejects_duplicate_dataset_id(self):
        payload = make_manifest("a" * 64)
        payload["datasets"].append(copy.deepcopy(payload["datasets"][0]))
        errors, _ = validate_manifest_payload(payload)
        self.assertTrue(any("duplicate dataset_id" in error for error in errors))

    def test_rejects_path_traversal(self):
        payload = make_manifest("a" * 64)
        payload["datasets"][0]["files"][0]["path"] = "../outside.mseed"
        errors, _ = validate_manifest_payload(payload)
        self.assertTrue(any("path escapes" in error for error in errors))

    def test_rejects_sha256_mismatch(self):
        payload = make_manifest("0" * 64)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw_dir = root / "raw"
            raw_dir.mkdir()
            (raw_dir / "station01.mseed").write_bytes(b"different bytes")
            errors, _ = validate_manifest_payload(payload, root=root, verify_files=True)
        self.assertTrue(any("SHA-256 mismatch" in error for error in errors))

    def test_rejects_nonpositive_sample_rate(self):
        payload = make_manifest("a" * 64)
        payload["datasets"][0]["acquisition"]["sample_rate_hz"] = 0
        errors, _ = validate_manifest_payload(payload)
        self.assertTrue(any("sample_rate_hz must be" in error for error in errors))

    def test_rejects_negative_sample_rate_without_crashing(self):
        payload = make_manifest("a" * 64)
        payload["datasets"][0]["acquisition"]["sample_rate_hz"] = -20
        errors, _ = validate_manifest_payload(payload)
        self.assertTrue(any("sample_rate_hz must be" in error for error in errors))


    def test_rejects_unsupported_file_format(self):
        payload = make_manifest("a" * 64)
        payload["datasets"][0]["files"][0]["file_format"] = "invented"
        errors, _ = validate_manifest_payload(payload)
        self.assertTrue(any("unsupported file_format" in error for error in errors))

    def test_rejects_derived_reference_to_missing_file(self):
        payload = make_manifest("a" * 64)
        payload["datasets"][0]["files"][0]["derived_from_file_ids"] = ["MISSING-RAW"]
        errors, _ = validate_manifest_payload(payload)
        self.assertTrue(any("does not exist in this dataset" in error for error in errors))

    def test_warns_on_sample_duration_mismatch(self):
        payload = make_manifest("a" * 64)
        payload["datasets"][0]["acquisition"]["end_time"] = "2026-01-01T00:02:00Z"
        errors, warnings = validate_manifest_payload(payload)
        self.assertEqual(errors, [])
        self.assertTrue(any("timestamp duration" in warning for warning in warnings))

    def test_rejects_invalid_quality_status(self):
        payload = make_manifest("a" * 64)
        payload["datasets"][0]["quality"]["status"] = "looks-good"
        errors, _ = validate_manifest_payload(payload)
        self.assertTrue(any("unsupported quality.status" in error for error in errors))

    def test_rejects_declared_file_size_mismatch(self):
        raw_bytes = b"synthetic waveform bytes, not a real field record"
        digest = hashlib.sha256(raw_bytes).hexdigest()
        payload = make_manifest(digest)
        payload["datasets"][0]["files"][0]["size_bytes"] = 1
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw_dir = root / "raw"
            raw_dir.mkdir()
            (raw_dir / "station01.mseed").write_bytes(raw_bytes)
            errors, _ = validate_manifest_payload(payload, root=root, verify_files=True)
        self.assertTrue(any("size_bytes mismatch" in error for error in errors))


    def test_draft_2020_12_schema_accepts_empty_template(self):
        template_path = (
            Path(__file__).resolve().parents[2]
            / "examples"
            / "giza_spatial"
            / "ambient_vibration_manifest.template.json"
        )
        payload = json.loads(template_path.read_text(encoding="utf-8"))
        self.assertEqual(validate_json_schema_payload(payload, DEFAULT_SCHEMA_PATH), [])

    def test_draft_2020_12_schema_accepts_synthetic_three_component_manifest(self):
        payload = make_manifest("a" * 64)
        self.assertEqual(validate_json_schema_payload(payload, DEFAULT_SCHEMA_PATH), [])

    def test_schema_format_checker_rejects_invalid_datetime(self):
        payload = make_manifest("a" * 64)
        payload["datasets"][0]["acquisition"]["start_time"] = "2026-02-30T00:00:00Z"
        errors = validate_json_schema_payload(payload, DEFAULT_SCHEMA_PATH)
        self.assertTrue(any("start_time" in error for error in errors))

    def test_schema_requires_all_quality_status_fields(self):
        payload = make_manifest("a" * 64)
        payload["datasets"][0]["quality"].pop("coordinate_status")
        errors = validate_json_schema_payload(payload, DEFAULT_SCHEMA_PATH)
        self.assertTrue(any("quality" in error for error in errors))

    def test_schema_requires_nonempty_instrument_model(self):
        payload = make_manifest("a" * 64)
        payload["datasets"][0]["instrument"]["model"] = ""
        errors = validate_json_schema_payload(payload, DEFAULT_SCHEMA_PATH)
        self.assertTrue(any("instrument.model" in error for error in errors))

    def test_schema_format_checker_rejects_non_uri_source(self):
        payload = make_manifest("a" * 64)
        payload["datasets"][0]["source"]["source_uris"] = ["not a uri"]
        errors = validate_json_schema_payload(payload, DEFAULT_SCHEMA_PATH)
        self.assertTrue(any("source.source_uris" in error for error in errors))

    def test_cli_enforces_schema_unknown_property_rule(self):
        payload = {
            "schema_version": "1.0",
            "project": {"id": "CLI-TEST", "title": "Schema CLI test"},
            "datasets": [],
            "unexpected": "not allowed by the schema"
        }
        with tempfile.TemporaryDirectory() as tmp:
            manifest_path = Path(tmp) / "manifest.json"
            manifest_path.write_text(json.dumps(payload), encoding="utf-8")
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                exit_code = main(["--manifest", str(manifest_path)])
        self.assertEqual(exit_code, 2)
        self.assertIn("JSON Schema $", stderr.getvalue())


    def test_rejects_duplicate_channel_ids_and_primary_components(self):
        payload = make_manifest("a" * 64)
        duplicate = copy.deepcopy(payload["datasets"][0]["channels"][0])
        payload["datasets"][0]["channels"].append(duplicate)
        errors, _ = validate_manifest_payload(payload)
        self.assertTrue(any("duplicate channel_id" in error for error in errors))
        self.assertTrue(any("duplicate component" in error for error in errors))

    def test_rejects_channel_axis_and_sensitivity_bounds(self):
        payload = make_manifest("a" * 64)
        channel = payload["datasets"][0]["channels"][0]
        channel["azimuth_deg"] = 361
        channel["dip_deg"] = -91
        channel["sensitivity"] = 0
        errors, _ = validate_manifest_payload(payload)
        self.assertTrue(any("azimuth_deg" in error for error in errors))
        self.assertTrue(any("dip_deg" in error for error in errors))
        self.assertTrue(any("sensitivity must be positive" in error for error in errors))

    def test_rejects_duplicate_file_ids_and_paths(self):
        payload = make_manifest("a" * 64)
        duplicate = copy.deepcopy(payload["datasets"][0]["files"][0])
        payload["datasets"][0]["files"].append(duplicate)
        errors, _ = validate_manifest_payload(payload)
        self.assertTrue(any("duplicate file_id" in error for error in errors))
        self.assertTrue(any("duplicate path" in error for error in errors))

    def test_rejects_end_time_equal_to_or_before_start_time(self):
        for end_time in ("2026-01-01T00:00:00Z", "2025-12-31T23:59:59Z"):
            with self.subTest(end_time=end_time):
                payload = make_manifest("a" * 64)
                payload["datasets"][0]["acquisition"]["end_time"] = end_time
                errors, _ = validate_manifest_payload(payload)
                self.assertTrue(any("end_time must be later" in error for error in errors))

    def test_rejects_symlink_escape_during_file_verification(self):
        raw_bytes = b"outside file reached through a symlink"
        digest = hashlib.sha256(raw_bytes).hexdigest()
        payload = make_manifest(digest)
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "data"
            raw_dir = root / "raw"
            raw_dir.mkdir(parents=True)
            outside = base / "outside.mseed"
            outside.write_bytes(raw_bytes)
            link = raw_dir / "escape.mseed"
            try:
                link.symlink_to(outside)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"symlinks unavailable in this environment: {exc}")
            payload["datasets"][0]["files"][0]["path"] = "raw/escape.mseed"
            errors, _ = validate_manifest_payload(payload, root=root, verify_files=True)
        self.assertTrue(any("path escapes" in error for error in errors))

    def test_warns_for_unknown_and_partial_quality_states(self):
        payload = make_manifest("a" * 64)
        quality = payload["datasets"][0]["quality"]
        quality["calibration_status"] = "unknown"
        quality["orientation_status"] = "partial"
        quality["timing_status"] = "unknown"
        quality["coordinate_status"] = "partial"
        errors, warnings = validate_manifest_payload(payload)
        self.assertEqual(errors, [])
        self.assertEqual(len(warnings), 4)

    def test_cli_reports_missing_and_invalid_schema_files(self):
        payload = {
            "schema_version": "1.0",
            "project": {"id": "CLI-SCHEMA", "title": "Schema failure test"},
            "datasets": []
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(payload), encoding="utf-8")
            schema_path = root / "missing-schema.json"
            for schema_content in (None, "{ invalid json"):
                with self.subTest(schema_content=schema_content):
                    if schema_content is not None:
                        schema_path.write_text(schema_content, encoding="utf-8")
                    stderr = io.StringIO()
                    with redirect_stderr(stderr):
                        exit_code = main([
                            "--manifest", str(manifest_path),
                            "--schema", str(schema_path)
                        ])
                    self.assertEqual(exit_code, 2)
                    self.assertIn("JSON Schema validation could not run", stderr.getvalue())
                    if schema_content is None and schema_path.exists():
                        schema_path.unlink()

    def test_cli_verifies_complete_manifest_and_actual_file_hash(self):
        raw_bytes = b"synthetic file used for end-to-end CLI verification"
        digest = hashlib.sha256(raw_bytes).hexdigest()
        payload = make_manifest(digest)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw_dir = root / "raw"
            raw_dir.mkdir()
            (raw_dir / "station01.mseed").write_bytes(raw_bytes)
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(payload), encoding="utf-8")
            stdout = io.StringIO()
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                with redirect_stdout(stdout):
                    exit_code = main([
                        "--manifest", str(manifest_path),
                        "--root", str(root),
                        "--verify-files"
                    ])
        self.assertEqual(exit_code, 0, stderr.getvalue())
        self.assertIn("VALID: 1 dataset(s)", stdout.getvalue())

    def test_semantic_validator_handles_unhashable_enum_values(self):
        payload = make_manifest("a" * 64)
        dataset = payload["datasets"][0]
        dataset["source"]["origin"] = ["user_supplied"]
        dataset["instrument"]["sensor_type"] = ["seismometer"]
        dataset["acquisition"]["time_standard"] = ["UTC"]
        dataset["channels"][0]["component"] = ["vertical"]
        dataset["channels"][0]["unit"] = ["m/s"]
        dataset["files"][0]["role"] = ["raw"]
        dataset["files"][0]["file_format"] = ["mseed"]
        dataset["quality"]["status"] = ["received_unchecked"]

        errors, _ = validate_manifest_payload(payload)
        self.assertGreaterEqual(len(errors), 8)
        self.assertTrue(any("unsupported component" in error for error in errors))
        self.assertTrue(any("unsupported quality.status" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
