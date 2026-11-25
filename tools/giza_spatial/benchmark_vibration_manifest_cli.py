#!/usr/bin/env python3
"""Reproducible synthetic benchmark for the GIZA vibration-manifest CLI.

The benchmark measures manifest validation and optional byte-level file
verification. It does not inspect waveform samples or use field observations.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
import platform
import psutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = REPOSITORY_ROOT / "tools" / "giza_spatial" / "validate_vibration_manifest.py"
SCHEMA = REPOSITORY_ROOT / "schemas" / "giza_ambient_vibration_manifest.schema.json"
HASH_SEEDS = ("1", "73", "987654321", "314159", "42", "2026", "1618", "2718")
WRITE_BLOCK = bytes(range(256)) * 4096


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_synthetic_file(path: Path, size_bytes: int) -> str:
    """Write deterministic bytes without allocating the full file in memory."""
    path.parent.mkdir(parents=True, exist_ok=True)
    remaining = size_bytes
    with path.open("wb") as handle:
        while remaining:
            chunk = WRITE_BLOCK[: min(len(WRITE_BLOCK), remaining)]
            handle.write(chunk)
            remaining -= len(chunk)
    return sha256_file(path)


def build_manifest(
    datasets: int,
    hashes: list[str],
    file_sizes: list[int],
) -> dict[str, Any]:
    if datasets < 1 or datasets > 10_000:
        raise ValueError("datasets must be between 1 and 10000")
    if len(hashes) != datasets or len(file_sizes) != datasets:
        raise ValueError("hashes and file_sizes must contain one value per dataset")

    records: list[dict[str, Any]] = []
    for index in range(datasets):
        number = index + 1
        records.append(
            {
                "dataset_id": f"BENCH-{number:06d}",
                "title": f"Synthetic benchmark dataset {number:06d}",
                "source": {
                    "origin": "user_supplied",
                    "title": "Generated benchmark fixture",
                    "source_uris": [],
                },
                "station": {
                    "station_id": f"ST-BENCH-{number:06d}",
                    "location": {
                        "x": float(index),
                        "y": float(index * 2),
                        "z": 0.0,
                        "coordinate_system": "SYNTHETIC-LOCAL",
                        "horizontal_unit": "m",
                        "vertical_datum": "synthetic-benchmark",
                    },
                },
                "instrument": {
                    "sensor_type": "seismometer",
                    "manufacturer": "Synthetic",
                    "model": "BENCH-3C",
                },
                "acquisition": {
                    "start_time": "2026-01-01T00:00:00Z",
                    "end_time": "2026-01-01T00:01:00Z",
                    "time_standard": "UTC",
                    "sample_rate_hz": 100.0,
                    "sample_count": 6000,
                },
                "channels": [
                    {"channel_id": "Z", "component": "vertical", "unit": "m/s"},
                    {"channel_id": "N", "component": "north", "unit": "m/s"},
                    {"channel_id": "E", "component": "east", "unit": "m/s"},
                ],
                "require_three_components": True,
                "files": [
                    {
                        "file_id": f"RAW-BENCH-{number:06d}",
                        "role": "raw",
                        "path": f"raw/benchmark-{number:06d}.mseed",
                        "file_format": "mseed",
                        "sha256": hashes[index],
                        "size_bytes": file_sizes[index],
                    }
                ],
                "quality": {
                    "status": "received_unchecked",
                    "calibration_status": "documented",
                    "orientation_status": "documented",
                    "timing_status": "documented",
                    "coordinate_status": "documented",
                },
            }
        )
    return {
        "schema_version": "1.0",
        "project": {
            "id": "GIZA-PRIME-BENCHMARK",
            "title": "Synthetic GIZA PRIME CLI benchmark",
        },
        "datasets": records,
    }


def _version(distribution: str) -> str:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return "not-installed"


def _run_one(
    manifest_path: Path,
    verify_files: bool,
    seed: str,
    timeout_seconds: int,
    memory_sample_interval_ms: int,
) -> dict[str, Any]:
    command = [sys.executable, str(VALIDATOR), "--manifest", str(manifest_path)]
    if verify_files:
        command.append("--verify-files")

    environment = os.environ.copy()
    environment["PYTHONHASHSEED"] = seed
    started = time.perf_counter()
    process = subprocess.Popen(
        command,
        cwd=REPOSITORY_ROOT,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    monitored_process = psutil.Process(process.pid)
    rss_samples: list[int] = []
    sample_interval = memory_sample_interval_ms / 1000.0

    try:
        while True:
            try:
                rss_samples.append(int(monitored_process.memory_info().rss))
            except psutil.NoSuchProcess:
                pass

            if process.poll() is not None:
                break

            elapsed = time.perf_counter() - started
            if elapsed >= timeout_seconds:
                process.kill()
                stdout, stderr = process.communicate()
                raise subprocess.TimeoutExpired(
                    command,
                    timeout_seconds,
                    output=stdout,
                    stderr=stderr,
                )
            time.sleep(min(sample_interval, max(0.001, timeout_seconds - elapsed)))
        stdout, stderr = process.communicate()
    except BaseException:
        if process.poll() is None:
            process.kill()
        process.communicate()
        raise

    elapsed = time.perf_counter() - started
    return {
        "hash_seed": seed,
        "elapsed_seconds": elapsed,
        "return_code": process.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "stdout_sha256": sha256_bytes(stdout),
        "stderr_sha256": sha256_bytes(stderr),
        "rss_peak_sampled_bytes": max(rss_samples) if rss_samples else None,
        "rss_first_sample_bytes": rss_samples[0] if rss_samples else None,
        "rss_sample_count": len(rss_samples),
    }


def _run_batch(
    manifest_path: Path,
    verify_files: bool,
    concurrency: int,
    iteration: int,
    timeout_seconds: int,
    memory_sample_interval_ms: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    seeds = [HASH_SEEDS[(iteration * concurrency + offset) % len(HASH_SEEDS)] for offset in range(concurrency)]
    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        results = list(
            executor.map(
                lambda seed: _run_one(
                    manifest_path,
                    verify_files,
                    seed,
                    timeout_seconds,
                    memory_sample_interval_ms,
                ),
                seeds,
            )
        )
    batch_elapsed = time.perf_counter() - started

    signatures = {
        (result["return_code"], result["stdout"], result["stderr"])
        for result in results
    }
    if len(signatures) != 1:
        raise RuntimeError(f"parallel CLI outputs differ in iteration {iteration}")

    return {
        "iteration": iteration,
        "batch_wall_seconds": batch_elapsed,
        "outputs_identical": True,
        "processes": [
            {
                "hash_seed": result["hash_seed"],
                "elapsed_seconds": result["elapsed_seconds"],
                "return_code": result["return_code"],
                "stdout_sha256": result["stdout_sha256"],
                "stderr_sha256": result["stderr_sha256"],
            }
            for result in results
        ],
    }, results


def _validate_results(
    results: list[dict[str, Any]],
    expected_datasets: int,
) -> tuple[int, bytes, bytes]:
    reference = results[0]
    for result in results:
        if result["return_code"] != 0:
            detail = result["stderr"].decode("utf-8", errors="replace")
            raise RuntimeError(f"validator returned {result['return_code']}: {detail[:2000]}")
        if result["stderr"]:
            detail = result["stderr"].decode("utf-8", errors="replace")
            raise RuntimeError(f"validator wrote to stderr: {detail[:2000]}")
        expected = f"VALID: {expected_datasets} dataset(s)".encode("ascii")
        if expected not in result["stdout"]:
            detail = result["stdout"].decode("utf-8", errors="replace")
            raise RuntimeError(f"expected validation result not found: {detail[:2000]}")
        if (
            result["return_code"] != reference["return_code"]
            or result["stdout"] != reference["stdout"]
            or result["stderr"] != reference["stderr"]
        ):
            raise RuntimeError("CLI output changed between benchmark executions")
    return reference["return_code"], reference["stdout"], reference["stderr"]


def run_benchmark(args: argparse.Namespace) -> dict[str, Any]:
    benchmark_started_at = datetime.now(timezone.utc).isoformat()
    benchmark_started = time.perf_counter()
    if args.datasets < 1 or args.datasets > 10_000:
        raise ValueError("--datasets must be between 1 and 10000")
    if args.file_size_bytes < 0 or args.file_size_bytes > 1024 * 1024 * 1024:
        raise ValueError("--file-size-bytes must be between 0 and 1073741824")
    if args.file_size_bytes > 0 and not args.verify_files:
        raise ValueError("--file-size-bytes greater than zero requires --verify-files")
    if args.verify_files and args.datasets != 1:
        raise ValueError("--verify-files requires --datasets 1 to keep file-I/O and manifest-size dimensions separate")
    if args.concurrency not in {1, 2, 4, 8}:
        raise ValueError("--concurrency must be one of 1, 2, 4, or 8")
    if args.repeat < 1 or args.repeat > 100:
        raise ValueError("--repeat must be between 1 and 100")
    if args.warmup < 0 or args.warmup > 10:
        raise ValueError("--warmup must be between 0 and 10")
    if args.timeout_seconds < 1 or args.timeout_seconds > 3600:
        raise ValueError("--timeout-seconds must be between 1 and 3600")
    if args.memory_sample_interval_ms < 1 or args.memory_sample_interval_ms > 1000:
        raise ValueError("--memory-sample-interval-ms must be between 1 and 1000")
    if not VALIDATOR.is_file() or not SCHEMA.is_file():
        raise FileNotFoundError("validator or default JSON Schema is missing from this repository checkout")

    with tempfile.TemporaryDirectory(prefix="giza-cli-benchmark-") as temporary_directory:
        root = Path(temporary_directory)
        raw_directory = root / "raw"
        raw_directory.mkdir()
        hashes: list[str] = []
        sizes: list[int] = []
        raw_paths: list[Path] = []

        for index in range(args.datasets):
            raw_path = raw_directory / f"benchmark-{index + 1:06d}.mseed"
            size = args.file_size_bytes if args.verify_files else 0
            hashes.append(write_synthetic_file(raw_path, size))
            sizes.append(size)
            raw_paths.append(raw_path)

        payload = build_manifest(args.datasets, hashes, sizes)
        manifest_path = root / "manifest.json"
        manifest_bytes = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        manifest_path.write_bytes(manifest_bytes)

        tracked_paths = [manifest_path, *raw_paths]
        hashes_before = {path: sha256_file(path) for path in tracked_paths}
        manifest_hash = hashes_before[manifest_path]
        schema_hash = sha256_file(SCHEMA)
        validator_hash = sha256_file(VALIDATOR)

        for warmup_index in range(args.warmup):
            _, results = _run_batch(
                manifest_path,
                args.verify_files,
                args.concurrency,
                warmup_index,
                args.timeout_seconds,
                args.memory_sample_interval_ms,
            )
            _validate_results(results, args.datasets)

        measurements: list[dict[str, Any]] = []
        process_times: list[float] = []
        batch_times: list[float] = []
        baseline: tuple[int, bytes, bytes] | None = None
        for iteration in range(args.repeat):
            batch, results = _run_batch(
                manifest_path,
                args.verify_files,
                args.concurrency,
                iteration + args.warmup,
                args.timeout_seconds,
                args.memory_sample_interval_ms,
            )
            validated = _validate_results(results, args.datasets)
            if baseline is None:
                baseline = validated
            elif validated != baseline:
                raise RuntimeError("CLI output changed between measured iterations")
            measurements.append(batch)
            batch_times.append(batch["batch_wall_seconds"])
            process_times.extend(item["elapsed_seconds"] for item in batch["processes"])

        hashes_after = {path: sha256_file(path) for path in tracked_paths}
        if hashes_after != hashes_before:
            changed = [path.name for path in tracked_paths if hashes_after[path] != hashes_before[path]]
            raise RuntimeError(f"benchmark inputs changed during execution: {changed}")

        rss_peaks = [
            item["rss_peak_sampled_bytes"]
            for batch in measurements
            for item in batch["processes"]
            if item["rss_peak_sampled_bytes"] is not None
        ]
        total_raw_bytes = sum(sizes)
        report = {
            "benchmark_format": "giza-prime-cli-benchmark-1.0",
            "started_at_utc": benchmark_started_at,
            "benchmark_wall_seconds": time.perf_counter() - benchmark_started,
            "runtime": {
                "os": platform.system(),
                "platform": platform.platform(),
                "python": platform.python_version(),
                "numpy": _version("numpy"),
                "jsonschema": _version("jsonschema"),
                "revision": os.environ.get("GITHUB_SHA"),
            },
            "memory_measurement": {
                "metric": "RSS bytes",
                "source": "psutil.Process.memory_info().rss",
                "sampling_interval_ms": args.memory_sample_interval_ms,
                "peak_definition": "maximum sampled RSS for each CLI process; a peak between samples may be missed",
                "shared_memory_note": "RSS includes shared memory mapped by the process; per-process peaks must not be summed as unique physical memory",
            },
            "artifacts": {
                "validator_sha256": validator_hash,
                "schema_sha256": schema_hash,
                "requirements_file": "requirements-giza-signal.txt",
            },
            "configuration": {
                "datasets": args.datasets,
                "manifest_bytes": len(manifest_bytes),
                "manifest_sha256": manifest_hash,
                "file_size_bytes_per_dataset": args.file_size_bytes if args.verify_files else 0,
                "raw_files_count": len(raw_paths),
                "raw_total_bytes": total_raw_bytes,
                "raw_sha256_unique": sorted(set(hashes)),
                "verify_files": args.verify_files,
                "concurrency": args.concurrency,
                "warmup_batches": args.warmup,
                "measured_batches": args.repeat,
                "timeout_seconds_per_process": args.timeout_seconds,
                "memory_sample_interval_ms": args.memory_sample_interval_ms,
                "hash_seed_cycle": list(HASH_SEEDS),
            },
            "integrity": {
                "manifest_unchanged": True,
                "raw_inputs_unchanged": True,
                "cli_outputs_identical_across_processes_and_iterations": True,
            },
            "summary": {
                "process_runs": len(process_times),
                "process_elapsed_seconds_min": min(process_times),
                "process_elapsed_seconds_median": statistics.median(process_times),
                "process_elapsed_seconds_max": max(process_times),
                "batch_wall_seconds_min": min(batch_times),
                "batch_wall_seconds_median": statistics.median(batch_times),
                "batch_wall_seconds_max": max(batch_times),
"max_rss_sampled_bytes_across_processes": max(rss_peaks) if rss_peaks else None,
                "rss_samples_total": sum(
                    item["rss_sample_count"]
                    for batch in measurements
                    for item in batch["processes"]
                ),
                "validated_stdout_sha256": sha256_bytes(baseline[1]) if baseline else None,
                "validated_stderr_sha256": sha256_bytes(baseline[2]) if baseline else None,
            },
            "measurements": measurements,
            "limitations": [
                "All inputs are synthetic and do not represent Giza field measurements.",
                "Elapsed times include Python process startup, imports, schema loading and validation.",
                "The process timing is an end-to-end CLI measurement, not an isolated function benchmark.",
                "RSS is sampled, not captured as an OS-maintained lifetime peak; peaks between samples may be missed.",
                "Per-process RSS includes shared pages and must not be summed as unique physical memory.",
                "Storage-device cache state is not measured by this tool.",
                "The results do not establish an upper capacity limit or a production performance target.",
            ],
        }
        return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--datasets", type=int, default=1, help="Number of synthetic datasets (1..10000)")
    parser.add_argument("--file-size-bytes", type=int, default=0, help="Raw file size; requires --verify-files and one dataset")
    parser.add_argument("--verify-files", action="store_true", help="Include actual file-size and SHA-256 verification")
    parser.add_argument("--concurrency", type=int, default=1, help="Concurrent CLI processes: 1, 2, 4, or 8")
    parser.add_argument("--repeat", type=int, default=3, help="Measured batches (1..100)")
    parser.add_argument("--warmup", type=int, default=1, help="Unrecorded warm-up batches (0..10)")
    parser.add_argument("--timeout-seconds", type=int, default=120, help="Timeout for each CLI process (1..3600)")
    parser.add_argument("--memory-sample-interval-ms", type=int, default=10, help="RSS polling interval in milliseconds (1..1000)")
    parser.add_argument("--output", type=Path, default=None, help="Optional path for a JSON report copy")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        report = run_benchmark(args)
        rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if args.output is not None:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        sys.stdout.write(rendered)
        return 0
    except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as exc:
        print(f"ERROR: benchmark failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
