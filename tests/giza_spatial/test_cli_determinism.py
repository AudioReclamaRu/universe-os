"""Cross-process reproducibility checks for the GIZA vibration-manifest CLI."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

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
) -> tuple[int, bytes, bytes]:
    command = [sys.executable, str(VALIDATOR), "--manifest", str(manifest_path)]
    if schema_path is not None:
        command.extend(["--schema", str(schema_path)])

    manifest_before = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    schema_before = (
        hashlib.sha256(schema_path.read_bytes()).hexdigest()
        if schema_path is not None
        else None
    )
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

    if hashlib.sha256(manifest_path.read_bytes()).hexdigest() != manifest_before:
        raise AssertionError("CLI changed the manifest bytes during validation")
    if schema_path is not None:
        if hashlib.sha256(schema_path.read_bytes()).hexdigest() != schema_before:
            raise AssertionError("CLI changed the schema bytes during validation")

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
        self.assertIn(b"#.$defs.first_definition.$ref", stderr)
        self.assertIn(b"external schema references are not allowed", stderr)


if __name__ == "__main__":
    unittest.main()
