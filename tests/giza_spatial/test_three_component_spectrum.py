import csv
import hashlib
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "giza_spatial"))
from analyze_three_component_spectrum import (
    SpectrumError,
    analyze_waveform,
    read_waveform_csv,
    welch_psd,
    write_outputs,
)


def sine(frequency_hz: float, amplitude: float, sample_rate_hz: float, count: int) -> np.ndarray:
    t = np.arange(count, dtype=np.float64) / sample_rate_hz
    return amplitude * np.sin(2.0 * np.pi * frequency_hz * t)


def write_3c_csv(path: Path, vertical: np.ndarray, north: np.ndarray, east: np.ndarray,
                 sample_rate_hz: float, with_time: bool = True) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        fields = ["vertical", "north", "east"]
        if with_time:
            fields.insert(0, "time_s")
        writer = csv.writer(handle)
        writer.writerow(fields)
        for i, values in enumerate(zip(vertical, north, east)):
            row = ([i / sample_rate_hz] if with_time else []) + list(values)
            writer.writerow(row)


class ThreeComponentSpectrumTests(unittest.TestCase):
    def test_welch_peak_matches_known_sinusoid(self):
        fs = 128.0
        x = sine(7.0, 1.0, fs, 8192)
        frequency, psd, count, resolution = welch_psd(x, fs, 1024, 0.5)
        peak = float(frequency[int(np.argmax(psd))])
        self.assertAlmostEqual(peak, 7.0, delta=resolution)
        self.assertGreaterEqual(count, 2)

    def test_hv_rms_and_geometric_ratios_match_known_amplitudes(self):
        fs = 128.0
        n = 8192
        z = sine(4.0, 1.0, fs, n)
        north = sine(4.0, 2.0, fs, n)
        east = sine(4.0, 2.0, fs, n)
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "waveform.csv"
            write_3c_csv(csv_path, z, north, east, fs)
            waveform = read_waveform_csv(csv_path, fs, "m/s")
            result = analyze_waveform(waveform, 1024, 0.5)
        index = int(np.argmin(np.abs(result.frequency_hz - 4.0)))
        self.assertAlmostEqual(float(result.hv_rms[index]), 2.0, delta=0.05)
        self.assertAlmostEqual(float(result.hv_geometric[index]), 2.0, delta=0.05)

    def test_psd_scales_with_amplitude_squared(self):
        fs = 100.0
        x = sine(5.0, 1.0, fs, 8000)
        y = 2.0 * x
        frequency, p1, _, _ = welch_psd(x, fs, 1000, 0.5)
        _, p2, _, _ = welch_psd(y, fs, 1000, 0.5)
        index = int(np.argmin(np.abs(frequency - 5.0)))
        self.assertAlmostEqual(float(p2[index] / p1[index]), 4.0, delta=1e-8)

    def test_rejects_counts_without_calibration(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "wave.csv"
            x = sine(5.0, 1.0, 100.0, 4000)
            write_3c_csv(path, x, x, x, 100.0)
            with self.assertRaises(SpectrumError):
                read_waveform_csv(path, 100.0, "counts")

    def test_rejects_nonuniform_time_column(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "wave.csv"
            fs = 100.0
            x = sine(5.0, 1.0, fs, 4000)
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(["time_s", "vertical", "north", "east"])
                for i, v in enumerate(x):
                    t = i/fs + (0.001 if i == 200 else 0.0)
                    writer.writerow([t, v, v, v])
            with self.assertRaises(SpectrumError):
                read_waveform_csv(path, fs, "m/s")

    def test_rejects_nan_samples(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "wave.csv"
            x = sine(5.0, 1.0, 100.0, 4000)
            x[100] = float("nan")
            write_3c_csv(path, x, x, x, 100.0, with_time=False)
            with self.assertRaises(SpectrumError):
                read_waveform_csv(path, 100.0, "m/s")

    def test_rejects_less_than_two_segments(self):
        x = np.ones(200, dtype=np.float64)
        with self.assertRaises(SpectrumError):
            welch_psd(x, 100.0, 150, 0.5)

    def test_outputs_are_provenance_preserving(self):
        fs = 100.0
        x = sine(5.0, 1.0, fs, 8000)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = root / "waveform.csv"
            write_3c_csv(input_path, x, 2*x, 2*x, fs)
            waveform = read_waveform_csv(input_path, fs, "m/s")
            result = analyze_waveform(waveform, 1000, 0.5)
            output_dir = root / "run_001"
            spectra_path, metadata_path = write_outputs(
                input_path, output_dir, waveform, result, 1000, 0.5, "SYNTHETIC-001"
            )
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            self.assertEqual(
                metadata["input_sha256"],
                hashlib.sha256(input_path.read_bytes()).hexdigest()
            )
            self.assertEqual(metadata["status"], "DERIVED_SPECTRAL_ESTIMATE_NOT_PHYSICAL_MODE_IDENTIFICATION")
            self.assertTrue(spectra_path.is_file())
            self.assertTrue(metadata_path.is_file())
            with self.assertRaises(SpectrumError):
                write_outputs(input_path, output_dir, waveform, result, 1000, 0.5, "SYNTHETIC-001")


if __name__ == "__main__":
    unittest.main()
