"""Tests for the reproducible synthetic CLI benchmark harness."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
BENCHMARK = REPOSITORY_ROOT / "tools" / "giza_spatial" / "benchmark_vibration_manifest_cli.py"


class CliBenchmarkTests(unittest.TestCase):
    def run_benchmark(self, *arguments: str) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            [sys.executable, str(BENCHMARK), *arguments],
            cwd=REPOSITORY_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=180,
        )

    def test_small_manifest_benchmark_emits_machine_readable_report(self):
        completed = self.run_benchmark(
            "--datasets", "2",
            "--concurrency", "2",
            "--repeat", "1",
            "--warmup", "0",
        )

        self.assertEqual(completed.returncode, 0, completed.stderr.decode("utf-8", errors="replace"))
        self.assertEqual(completed.stderr, b"")
        report = json.loads(completed.stdout)
        self.assertEqual(report["benchmark_format"], "giza-prime-cli-benchmark-1.0")
        self.assertEqual(report["configuration"]["datasets"], 2)
        self.assertEqual(report["configuration"]["concurrency"], 2)
        self.assertEqual(report["summary"]["process_runs"], 2)
        self.assertGreater(report["benchmark_wall_seconds"], 0)
        self.assertTrue(report["started_at_utc"].endswith("+00:00"))
        self.assertTrue(report["integrity"]["manifest_unchanged"])
        self.assertTrue(report["integrity"]["raw_inputs_unchanged"])
        self.assertGreater(report["measurements"][0]["processes"][0]["rss_peak_sampled_bytes"], 0)
        self.assertTrue(report["integrity"]["cli_outputs_identical_across_processes_and_iterations"])
        self.assertEqual(report["runtime"]["psutil"], "7.2.2")
        self.assertEqual(report["memory_measurement"]["source"], "psutil.Process.memory_info().rss")
        self.assertEqual(report["memory_measurement"]["sampling_interval_ms"], 10)
        self.assertGreater(report["summary"]["max_rss_sampled_bytes_across_processes"], 0)
        self.assertEqual(len(report["measurements"]), 1)
        self.assertEqual(len(report["measurements"][0]["processes"]), 2)
        for process in report["measurements"][0]["processes"]:
            self.assertGreater(process["rss_peak_sampled_bytes"], 0)
            self.assertGreater(process["rss_sample_count"], 0)
        self.assertTrue(report["measurements"][0]["outputs_identical"])

    def test_file_verification_benchmark_records_bytes_and_digest(self):
        completed = self.run_benchmark(
            "--datasets", "1",
            "--file-size-bytes", "4096",
            "--verify-files",
            "--concurrency", "1",
            "--repeat", "1",
            "--warmup", "0",
        )

        self.assertEqual(completed.returncode, 0, completed.stderr.decode("utf-8", errors="replace"))
        report = json.loads(completed.stdout)
        self.assertTrue(report["configuration"]["verify_files"])
        self.assertEqual(report["configuration"]["file_size_bytes_per_dataset"], 4096)
        self.assertEqual(report["configuration"]["raw_total_bytes"], 4096)
        self.assertEqual(len(report["configuration"]["raw_sha256_unique"]), 1)
        self.assertEqual(report["summary"]["process_runs"], 1)
        self.assertTrue(report["integrity"]["raw_inputs_unchanged"])

    def test_file_verification_rejects_multiple_datasets(self):
        completed = self.run_benchmark(
            "--datasets", "2",
            "--verify-files",
            "--repeat", "1",
            "--warmup", "0",
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn(
            b"--verify-files requires --datasets 1",
            completed.stderr,
        )

    def test_output_copy_is_written_without_changing_stdout_report(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_path = Path(temporary_directory) / "nested" / "benchmark.json"
            completed = self.run_benchmark(
                "--datasets", "1",
                "--concurrency", "1",
                "--repeat", "1",
                "--warmup", "0",
                "--output", str(output_path),
            )
            self.assertEqual(
                completed.returncode,
                0,
                completed.stderr.decode("utf-8", errors="replace"),
            )
            self.assertTrue(output_path.is_file())
            self.assertEqual(json.loads(output_path.read_bytes()), json.loads(completed.stdout))


if __name__ == "__main__":
    unittest.main()
