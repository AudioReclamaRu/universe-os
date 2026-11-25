import copy
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "giza_spatial"))
from validate_vibration_manifest import validate_manifest_payload


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


if __name__ == "__main__":
    unittest.main()
