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
    ALLOWED_COMPONENTS,
    ALLOWED_FILE_FORMATS,
    ALLOWED_FILE_ROLES,
    ALLOWED_QUALITY_VALUES,
    ALLOWED_SENSOR_TYPES,
    ALLOWED_SOURCE_ORIGINS,
    ALLOWED_TIME_STANDARDS,
    ALLOWED_UNITS,
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

    def test_python_enum_contracts_match_json_schema(self):
        schema = json.loads(DEFAULT_SCHEMA_PATH.read_text(encoding="utf-8"))
        defs = schema["$defs"]

        enum_bindings = {
            "source.origin": (defs["source"]["properties"]["origin"]["enum"], ALLOWED_SOURCE_ORIGINS),
            "instrument.sensor_type": (defs["instrument"]["properties"]["sensor_type"]["enum"], ALLOWED_SENSOR_TYPES),
            "channel.component": (defs["channel"]["properties"]["component"]["enum"], ALLOWED_COMPONENTS),
            "channel.unit": (defs["channel"]["properties"]["unit"]["enum"], ALLOWED_UNITS),
            "acquisition.time_standard": (defs["acquisition"]["properties"]["time_standard"]["enum"], ALLOWED_TIME_STANDARDS),
            "file.role": (defs["file"]["properties"]["role"]["enum"], ALLOWED_FILE_ROLES),
            "file.file_format": (defs["file"]["properties"]["file_format"]["enum"], ALLOWED_FILE_FORMATS),
        }
        for field, (schema_values, python_values) in enum_bindings.items():
            with self.subTest(field=field):
                self.assertEqual(set(schema_values), python_values)

        for field, python_values in ALLOWED_QUALITY_VALUES.items():
            with self.subTest(field=f"quality.{field}"):
                schema_values = defs["quality"]["properties"][field]["enum"]
                self.assertEqual(set(schema_values), python_values)

    def test_required_schema_fields_are_declared_at_each_level(self):
        schema = json.loads(DEFAULT_SCHEMA_PATH.read_text(encoding="utf-8"))
        required_contracts = {
            "root": (schema, {"schema_version", "project", "datasets"}),
            "project": (schema["properties"]["project"], {"id", "title"}),
            "source": (schema["$defs"]["source"], {"origin", "title"}),
            "coordinates": (schema["$defs"]["coordinates"], {"x", "y", "coordinate_system"}),
            "station": (schema["$defs"]["station"], {"station_id", "location"}),
            "instrument": (schema["$defs"]["instrument"], {"sensor_type", "manufacturer", "model"}),
            "acquisition": (
                schema["$defs"]["acquisition"],
                {"start_time", "end_time", "time_standard", "sample_rate_hz", "sample_count"},
            ),
            "channel": (schema["$defs"]["channel"], {"channel_id", "component", "unit"}),
            "file": (schema["$defs"]["file"], {"file_id", "role", "path", "file_format", "sha256"}),
            "quality": (
                schema["$defs"]["quality"],
                {"status", "calibration_status", "orientation_status", "timing_status", "coordinate_status"},
            ),
            "dataset": (
                schema["$defs"]["dataset"],
                {"dataset_id", "title", "source", "station", "instrument", "acquisition", "channels", "files", "quality"},
            ),
        }
        for name, (definition, expected) in required_contracts.items():
            with self.subTest(definition=name):
                self.assertEqual(set(definition.get("required", [])), expected)

    def test_three_component_default_is_explicitly_applied_by_semantic_validator(self):
        schema = json.loads(DEFAULT_SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertIs(
            schema["$defs"]["dataset"]["properties"]["require_three_components"]["default"],
            True,
        )

        payload = make_manifest("a" * 64)
        dataset = payload["datasets"][0]
        dataset.pop("require_three_components")
        dataset["channels"] = dataset["channels"][:2]

        self.assertEqual(validate_json_schema_payload(payload, DEFAULT_SCHEMA_PATH), [])
        self.assertNotIn("require_three_components", dataset)
        errors, _ = validate_manifest_payload(payload)
        self.assertTrue(any("three-component dataset is missing" in error for error in errors))

        dataset["require_three_components"] = False
        errors, _ = validate_manifest_payload(payload)
        self.assertFalse(any("three-component dataset is missing" in error for error in errors))

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

    def test_cli_rejects_missing_required_nested_properties(self):
        mutations = {
            "dataset.title": lambda dataset: dataset.pop("title"),
            "instrument.manufacturer": lambda dataset: dataset["instrument"].pop("manufacturer"),
            "station.location.coordinate_system": lambda dataset: dataset["station"]["location"].pop("coordinate_system"),
            "acquisition.sample_count": lambda dataset: dataset["acquisition"].pop("sample_count"),
            "channels[0].unit": lambda dataset: dataset["channels"][0].pop("unit"),
            "files[0].sha256": lambda dataset: dataset["files"][0].pop("sha256"),
            "quality.coordinate_status": lambda dataset: dataset["quality"].pop("coordinate_status"),
        }
        for field, mutate in mutations.items():
            with self.subTest(field=field), tempfile.TemporaryDirectory() as tmp:
                payload = make_manifest("a" * 64)
                mutate(payload["datasets"][0])
                manifest_path = Path(tmp) / "manifest.json"
                manifest_path.write_text(json.dumps(payload), encoding="utf-8")
                stderr = io.StringIO()
                with redirect_stderr(stderr):
                    exit_code = main(["--manifest", str(manifest_path)])
                self.assertEqual(exit_code, 2)
                self.assertIn("JSON Schema", stderr.getvalue())

    def test_cli_rejects_unknown_nested_channel_property(self):
        payload = make_manifest("a" * 64)
        payload["datasets"][0]["channels"][0]["unregistered_gain"] = 42
        with tempfile.TemporaryDirectory() as tmp:
            manifest_path = Path(tmp) / "manifest.json"
            manifest_path.write_text(json.dumps(payload), encoding="utf-8")
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                exit_code = main(["--manifest", str(manifest_path)])
        self.assertEqual(exit_code, 2)
        self.assertIn("JSON Schema", stderr.getvalue())
        self.assertIn("unregistered_gain", stderr.getvalue())

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

    def test_cli_rejects_nonstandard_numeric_constants(self):
        for constant in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(constant=constant), tempfile.TemporaryDirectory() as tmp:
                raw = (
                    '{"schema_version":"1.0","project":{"id":"STRICT","title":"Strict JSON"},'
                    f'"datasets":[],"extra":{constant}' + "}"
                )
                manifest_path = Path(tmp) / "manifest.json"
                manifest_path.write_text(raw, encoding="utf-8")
                stderr = io.StringIO()
                with redirect_stderr(stderr):
                    exit_code = main(["--manifest", str(manifest_path)])
                self.assertEqual(exit_code, 2)
                self.assertIn("non-standard JSON numeric constant", stderr.getvalue())

    def test_cli_rejects_duplicate_json_object_keys(self):
        cases = {
            "root": (
                '{"schema_version":"1.0","schema_version":"1.0",'
                '"project":{"id":"STRICT","title":"Strict JSON"},"datasets":[]}'
            ),
            "nested": (
                '{"schema_version":"1.0","project":{"id":"STRICT","id":"OVERRIDE",'
                '"title":"Strict JSON"},"datasets":[]}'
            ),
        }
        for name, raw in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                manifest_path = Path(tmp) / "manifest.json"
                manifest_path.write_text(raw, encoding="utf-8")
                stderr = io.StringIO()
                with redirect_stderr(stderr):
                    exit_code = main(["--manifest", str(manifest_path)])
                self.assertEqual(exit_code, 2)
                self.assertIn("duplicate JSON object key", stderr.getvalue())

    def test_integral_float_sample_count_matches_json_schema_integer(self):
        payload = make_manifest("a" * 64)
        payload["datasets"][0]["acquisition"]["sample_count"] = 6000.0
        self.assertEqual(validate_json_schema_payload(payload, DEFAULT_SCHEMA_PATH), [])
        errors, warnings = validate_manifest_payload(payload)
        self.assertFalse(any("sample_count must be" in error for error in errors))
        self.assertFalse(any("timestamp duration" in warning for warning in warnings))

    def test_integral_float_size_bytes_matches_json_schema_integer(self):
        raw_bytes = b"integral float size metadata"
        digest = hashlib.sha256(raw_bytes).hexdigest()
        payload = make_manifest(digest)
        payload["datasets"][0]["files"][0]["size_bytes"] = float(len(raw_bytes))
        self.assertEqual(validate_json_schema_payload(payload, DEFAULT_SCHEMA_PATH), [])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw_dir = root / "raw"
            raw_dir.mkdir()
            (raw_dir / "station01.mseed").write_bytes(raw_bytes)
            errors, _ = validate_manifest_payload(payload, root=root, verify_files=True)
        self.assertEqual(errors, [])

    def test_rejects_distinct_paths_that_resolve_to_same_file(self):
        payload = make_manifest("a" * 64)
        duplicate = copy.deepcopy(payload["datasets"][0]["files"][0])
        duplicate["file_id"] = "DERIVED-ALIAS"
        duplicate["role"] = "derived"
        duplicate["path"] = "raw/./station01.mseed"
        payload["datasets"][0]["files"].append(duplicate)
        errors, _ = validate_manifest_payload(payload)
        self.assertTrue(any("multiple file records resolve to the same path" in error for error in errors))

    def test_rejects_windows_absolute_paths_on_posix(self):
        for raw_path in (r"C:\data\station.mseed", r"\\server\share\station.mseed"):
            with self.subTest(path=raw_path):
                payload = make_manifest("a" * 64)
                payload["datasets"][0]["files"][0]["path"] = raw_path
                errors, _ = validate_manifest_payload(payload)
                self.assertTrue(any("absolute paths are not allowed" in error for error in errors))

    def test_cli_rejects_invalid_top_level_manifest_shapes(self):
        cases = {
            "root_array": "[]",
            "project_array": '{"schema_version":"1.0","project":[],"datasets":[]}',
            "datasets_object": '{"schema_version":"1.0","project":{"id":"P","title":"T"},"datasets":{}}',
        }
        for name, raw in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                manifest_path = Path(tmp) / "manifest.json"
                manifest_path.write_text(raw, encoding="utf-8")
                stderr = io.StringIO()
                with redirect_stderr(stderr):
                    exit_code = main(["--manifest", str(manifest_path)])
                self.assertEqual(exit_code, 2)
                self.assertTrue(
                    "JSON Schema" in stderr.getvalue() or "ERROR:" in stderr.getvalue(),
                    stderr.getvalue(),
                )

    def test_schema_reference_in_const_is_treated_as_literal_data(self):
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "payload": {
                    "const": {"$ref": "https://example.invalid/this-is-data-not-a-schema-ref"}
                }
            },
        }
        payload = {"payload": {"$ref": "https://example.invalid/this-is-data-not-a-schema-ref"}}
        with tempfile.TemporaryDirectory() as tmp:
            schema_path = Path(tmp) / "schema.json"
            schema_path.write_text(json.dumps(schema), encoding="utf-8")
            self.assertEqual(validate_json_schema_payload(payload, schema_path), [])

    def test_cli_rejects_schema_that_is_invalid_under_draft_2020_12(self):
        payload = make_manifest("a" * 64)
        invalid_schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "not-a-valid-schema-type",
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest_path = root / "manifest.json"
            schema_path = root / "schema.json"
            manifest_path.write_text(json.dumps(payload), encoding="utf-8")
            schema_path.write_text(json.dumps(invalid_schema), encoding="utf-8")
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                exit_code = main([
                    "--manifest", str(manifest_path),
                    "--schema", str(schema_path)
                ])
        self.assertEqual(exit_code, 2)
        self.assertIn("JSON Schema validation could not run", stderr.getvalue())

    def test_cli_rejects_external_and_unresolved_schema_references(self):
        schemas = {
            "external": {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$ref": "https://example.invalid/external-schema.json",
            },
            "unresolved_local": {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$ref": "#/$defs/not_present",
                "$defs": {},
            },
        }
        payload = make_manifest("a" * 64)
        for name, schema in schemas.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                manifest_path = root / "manifest.json"
                schema_path = root / "schema.json"
                manifest_path.write_text(json.dumps(payload), encoding="utf-8")
                schema_path.write_text(json.dumps(schema), encoding="utf-8")
                stderr = io.StringIO()
                with redirect_stderr(stderr):
                    exit_code = main([
                        "--manifest", str(manifest_path),
                        "--schema", str(schema_path)
                    ])
                self.assertEqual(exit_code, 2)
                self.assertIn("JSON Schema validation could not run", stderr.getvalue())
                expected = "external schema references are not allowed" if name == "external" else "unresolved local JSON Pointer"
                self.assertIn(expected, stderr.getvalue())

    def test_cli_rejects_duplicate_keys_inside_schema(self):
        payload = {
            "schema_version": "1.0",
            "project": {"id": "SCHEMA-DUP", "title": "Duplicate schema key"},
            "datasets": []
        }
        duplicate_schema = (
            '{"$schema":"https://json-schema.org/draft/2020-12/schema",'
            '"$schema":"https://json-schema.org/draft/2020-12/schema","type":"object"}'
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest_path = root / "manifest.json"
            schema_path = root / "schema.json"
            manifest_path.write_text(json.dumps(payload), encoding="utf-8")
            schema_path.write_text(duplicate_schema, encoding="utf-8")
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                exit_code = main([
                    "--manifest", str(manifest_path),
                    "--schema", str(schema_path)
                ])
        self.assertEqual(exit_code, 2)
        self.assertIn("JSON Schema validation could not run", stderr.getvalue())
        self.assertIn("duplicate JSON object key", stderr.getvalue())

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
