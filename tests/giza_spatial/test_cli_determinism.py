"""Cross-process reproducibility checks for the GIZA vibration-manifest CLI."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_validate_vibration_manifest import make_manifest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = REPOSITORY_ROOT / "tools" / "giza_spatial" / "validate_vibration_manifest.py"
HASH_SEEDS = ("1", "73", "987654321")


def write_json(path: Path, value: object) -> bytes:
    raw = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    path.write_bytes(raw)
    return raw


def run_cli_across_hash_seeds(
    manifest_path: Path,
    schema_path: Path | None = None,
    *,
    verify_files: bool = False,
    protected_paths: tuple[Path, ...] = (),
) -> tuple[int, bytes, bytes]:
    command = [sys.executable, str(VALIDATOR), "--manifest", str(manifest_path)]
    if schema_path is not None:
        command.extend(["--schema", str(schema_path)])
    if verify_files:
        command.append("--verify-files")

    tracked_paths = [manifest_path, *protected_paths]
    if schema_path is not None:
        tracked_paths.append(schema_path)
    hashes_before = {
        path: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in tracked_paths
    }
    results: list[tuple[int, bytes, bytes]] = []

    for seed in HASH_SEEDS:
        environment = os.environ.copy()
        environment["PYTHONHASHSEED"] = seed
        completed = subprocess.run(
            command,
            cwd=REPOSITORY_ROOT,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        results.append((completed.returncode, completed.stdout, completed.stderr))

    for path in tracked_paths:
        digest_after = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest_after != hashes_before[path]:
            raise AssertionError(f"CLI changed input bytes during validation: {path.name}")

    if not all(result == results[0] for result in results[1:]):
        details = [
            {
                "seed": seed,
                "returncode": result[0],
                "stdout": result[1].decode("utf-8", errors="replace"),
                "stderr": result[2].decode("utf-8", errors="replace"),
            }
            for seed, result in zip(HASH_SEEDS, results)
        ]
        raise AssertionError(f"CLI output differs across hash seeds: {details!r}")

    return results[0]


class CliDeterminismTests(unittest.TestCase):
    def test_valid_unchanged_passport_has_byte_stable_output(self):
        manifest = {
            "schema_version": "1.0",
            "project": {"id": "CLI-STABILITY", "title": "Deterministic CLI test"},
            "datasets": [],
        }

        with tempfile.TemporaryDirectory() as temporary_directory:
            manifest_path = Path(temporary_directory) / "manifest.json"
            write_json(manifest_path, manifest)

            returncode, stdout, stderr = run_cli_across_hash_seeds(manifest_path)

        self.assertEqual(returncode, 0)
        self.assertIn(b"WARNING: manifest contains no datasets", stdout)
        self.assertIn(b"VALID: 0 dataset(s)", stdout)
        self.assertEqual(stderr, b"")

    def test_schema_failure_order_has_byte_stable_cli_diagnostics(self):
        manifest = {
            "schema_version": "1.0",
            "project": {"id": "CLI-STABILITY", "title": "Deterministic CLI test"},
            "datasets": [],
        }
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "$defs": {
                "first_definition": {
                    "$ref": "https://example.invalid/first-definition.json"
                }
            },
            "properties": {
                "payload": {
                    "$ref": "https://example.invalid/later-property.json"
                }
            },
        }

        with tempfile.TemporaryDirectory() as temporary_directory:
            manifest_path = Path(temporary_directory) / "manifest.json"
            schema_path = Path(temporary_directory) / "schema.json"
            write_json(manifest_path, manifest)
            write_json(schema_path, schema)

            returncode, stdout, stderr = run_cli_across_hash_seeds(
                manifest_path,
                schema_path,
            )

        self.assertEqual(returncode, 2)
        self.assertEqual(stdout, b"")
        self.assertIn(b"JSON Schema validation could not run", stderr)
        self.assertIn(b"$.$defs.first_definition.$ref", stderr)
        self.assertIn(b"external schema references are not allowed", stderr)

    def test_strict_json_rejections_are_byte_stable_across_hash_seeds(self):
        cases = {
            "duplicate_key": (
                b'{"schema_version":"1.0","schema_version":"1.0",'
                b'"project":{"id":"STRICT","title":"Strict"},"datasets":[]}',
                b"duplicate JSON object key",
            ),
            "nan": (
                b'{"schema_version":"1.0","project":{"id":"STRICT","title":"Strict"},'
                b'"datasets":[],"extra":NaN}',
                b"non-standard JSON numeric constant",
            ),
            "float_overflow": (
                b'{"schema_version":"1.0","project":{"id":"STRICT","title":"Strict"},'
                b'"datasets":[],"extra":1e999}',
                b"exceeds supported finite range",
            ),
            "float_underflow": (
                b'{"schema_version":"1.0","project":{"id":"STRICT","title":"Strict"},'
                b'"datasets":[],"extra":1e-999}',
                b"underflows supported numeric precision",
            ),
        }

        for name, (raw, expected_message) in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary_directory:
                manifest_path = Path(temporary_directory) / "manifest.json"
                manifest_path.write_bytes(raw)

                returncode, stdout, stderr = run_cli_across_hash_seeds(manifest_path)

            self.assertEqual(returncode, 2)
            self.assertEqual(stdout, b"")
            self.assertIn(b"ERROR: cannot read manifest", stderr)
            self.assertIn(expected_message, stderr)

    def test_semantic_errors_and_warnings_are_byte_stable(self):
        payload = make_manifest("a" * 64)
        dataset = payload["datasets"][0]
        dataset["quality"]["calibration_status"] = "unknown"
        dataset["quality"]["orientation_status"] = "partial"
        payload["datasets"].append(copy.deepcopy(dataset))

        with tempfile.TemporaryDirectory() as temporary_directory:
            manifest_path = Path(temporary_directory) / "manifest.json"
            write_json(manifest_path, payload)
            returncode, stdout, stderr = run_cli_across_hash_seeds(manifest_path)

        self.assertEqual(returncode, 2)
        self.assertIn(b"quality.calibration_status is unknown", stdout)
        self.assertIn(b"quality.orientation_status is partial", stdout)
        self.assertIn(b"duplicate dataset_id", stderr)

    def test_verify_files_success_is_byte_stable_and_inputs_remain_unchanged(self):
        raw_bytes = b"synthetic file for deterministic CLI verification"
        payload = make_manifest(hashlib.sha256(raw_bytes).hexdigest())

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            raw_directory = root / "raw"
            raw_directory.mkdir()
            raw_path = raw_directory / "station01.mseed"
            raw_path.write_bytes(raw_bytes)
            manifest_path = root / "manifest.json"
            write_json(manifest_path, payload)

            returncode, stdout, stderr = run_cli_across_hash_seeds(
                manifest_path,
                verify_files=True,
                protected_paths=(raw_path,),
            )

        self.assertEqual(returncode, 0)
        self.assertIn(b"VALID: 1 dataset(s)", stdout)
        self.assertEqual(stderr, b"")


if __name__ == "__main__":
    unittest.main()
