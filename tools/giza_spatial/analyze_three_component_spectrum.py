#!/usr/bin/env python3
"""Reproducible Welch PSD/ASD analysis for calibrated three-component CSV data.

Required CSV columns: vertical, north, east.
Optional column: time_s, measured in seconds from the start of the record.

Input values must already be calibrated physical quantities. Counts are rejected.
The script does not correct instrument response, rotate sensor axes, remove gaps,
classify structural modes, or interpret H/V peaks.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np

REQUIRED_CHANNELS = ("vertical", "north", "east")
ALLOWED_UNITS = {"m/s", "m/s2", "m"}
TIME_COLUMN = "time_s"


class SpectrumError(ValueError):
    """Raised when input data or spectral parameters are invalid."""


@dataclass(frozen=True)
class Waveform:
    vertical: np.ndarray
    north: np.ndarray
    east: np.ndarray
    time_s: np.ndarray | None
    sample_rate_hz: float
    unit: str


@dataclass(frozen=True)
class Spectrum:
    frequency_hz: np.ndarray
    psd_vertical: np.ndarray
    psd_north: np.ndarray
    psd_east: np.ndarray
    asd_vertical: np.ndarray
    asd_north: np.ndarray
    asd_east: np.ndarray
    hv_rms: np.ndarray
    hv_geometric: np.ndarray
    segment_count: int
    frequency_resolution_hz: float


def _finite_positive(value: float, name: str) -> float:
    if isinstance(value, bool) or not math.isfinite(float(value)) or float(value) <= 0:
        raise SpectrumError(f"{name} must be a finite positive number")
    return float(value)


def read_waveform_csv(
    path: Path,
    sample_rate_hz: float,
    unit: str,
    time_column: str = TIME_COLUMN,
    time_tolerance_fraction: float = 1e-4,
) -> Waveform:
    if not path.is_file():
        raise SpectrumError(f"Input CSV does not exist: {path}")
    if unit not in ALLOWED_UNITS:
        raise SpectrumError(
            f"unit must be one of {sorted(ALLOWED_UNITS)}; counts require calibration first"
        )
    sample_rate = _finite_positive(sample_rate_hz, "sample_rate_hz")

    columns: dict[str, list[float]] = {name: [] for name in REQUIRED_CHANNELS}
    times: list[float] = []
    has_time = False

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        missing = [name for name in REQUIRED_CHANNELS if name not in headers]
        if missing:
            raise SpectrumError("Missing CSV columns: " + ", ".join(missing))
        has_time = time_column in headers

        for row_number, row in enumerate(reader, start=2):
            for name in REQUIRED_CHANNELS:
                raw = row.get(name)
                try:
                    value = float(raw)
                except (TypeError, ValueError) as exc:
                    raise SpectrumError(
                        f"Row {row_number}: {name} is not numeric: {raw!r}"
                    ) from exc
                if not math.isfinite(value):
                    raise SpectrumError(f"Row {row_number}: {name} must be finite")
                columns[name].append(value)

            if has_time:
                raw_time = row.get(time_column)
                try:
                    t = float(raw_time)
                except (TypeError, ValueError) as exc:
                    raise SpectrumError(
                        f"Row {row_number}: {time_column} is not numeric"
                    ) from exc
                if not math.isfinite(t):
                    raise SpectrumError(f"Row {row_number}: {time_column} must be finite")
                times.append(t)

    if not columns["vertical"]:
        raise SpectrumError("CSV contains no waveform samples")

    arrays = {name: np.asarray(values, dtype=np.float64) for name, values in columns.items()}
    if len({array.size for array in arrays.values()}) != 1:
        raise SpectrumError("Three components have different sample counts")

    time_array: np.ndarray | None = None
    if has_time:
        time_array = np.asarray(times, dtype=np.float64)
        if time_array.size != arrays["vertical"].size:
            raise SpectrumError("time_s and waveform components have different sample counts")
        differences = np.diff(time_array)
        if differences.size == 0 or np.any(differences <= 0):
            raise SpectrumError("time_s must be strictly increasing")
        expected_dt = 1.0 / sample_rate
        tolerance = max(1e-10, expected_dt * time_tolerance_fraction)
        if np.any(np.abs(differences - expected_dt) > tolerance):
            max_error = float(np.max(np.abs(differences - expected_dt)))
            raise SpectrumError(
                f"time_s is not uniform at the declared sample rate; max dt error={max_error:.6g}s"
            )

    return Waveform(
        vertical=arrays["vertical"],
        north=arrays["north"],
        east=arrays["east"],
        time_s=time_array,
        sample_rate_hz=sample_rate,
        unit=unit,
    )


def welch_psd(
    signal: np.ndarray,
    sample_rate_hz: float,
    nperseg: int,
    overlap: float = 0.5,
) -> tuple[np.ndarray, np.ndarray, int, float]:
    """One-sided PSD using mean removal, symmetric Hann window and segment averaging."""
    fs = _finite_positive(sample_rate_hz, "sample_rate_hz")
    if not isinstance(nperseg, int) or isinstance(nperseg, bool) or nperseg < 16:
        raise SpectrumError("nperseg must be an integer >= 16")
    if not math.isfinite(overlap) or overlap < 0 or overlap >= 1:
        raise SpectrumError("overlap must be in [0, 1)")
    x = np.asarray(signal, dtype=np.float64)
    if x.ndim != 1 or not np.all(np.isfinite(x)):
        raise SpectrumError("signal must be a finite one-dimensional array")
    if nperseg > x.size:
        raise SpectrumError("nperseg exceeds the number of waveform samples")

    noverlap = int(round(nperseg * overlap))
    step = nperseg - noverlap
    if step < 1:
        raise SpectrumError("overlap leaves no forward progress between segments")
    starts = list(range(0, x.size - nperseg + 1, step))
    if len(starts) < 2:
        raise SpectrumError("At least two complete segments are required for averaging")

    window = np.hanning(nperseg).astype(np.float64)
    window_energy = float(np.sum(window * window))
    if window_energy <= 0:
        raise SpectrumError("Window energy is zero")

    psd_sum: np.ndarray | None = None
    for start in starts:
        segment = x[start:start+nperseg].copy()
        segment -= np.mean(segment)
        transformed = np.fft.rfft(segment * window)
        periodogram = (np.abs(transformed) ** 2) / (fs * window_energy)

        if nperseg % 2 == 0:
            if periodogram.size > 2:
                periodogram[1:-1] *= 2.0
        elif periodogram.size > 1:
            periodogram[1:] *= 2.0

        if psd_sum is None:
            psd_sum = periodogram
        else:
            psd_sum += periodogram

    assert psd_sum is not None
    psd = psd_sum / len(starts)
    frequency = np.fft.rfftfreq(nperseg, d=1.0/fs)
    resolution = fs / nperseg
    return frequency, psd, len(starts), resolution


def analyze_waveform(
    waveform: Waveform,
    nperseg: int,
    overlap: float = 0.5,
) -> Spectrum:
    results = {}
    segment_counts = set()
    resolutions = set()
    frequency_reference: np.ndarray | None = None

    for name in REQUIRED_CHANNELS:
        frequency, psd, count, resolution = welch_psd(
            getattr(waveform, name),
            waveform.sample_rate_hz,
            nperseg,
            overlap,
        )
        if frequency_reference is None:
            frequency_reference = frequency
        elif not np.array_equal(frequency_reference, frequency):
            raise SpectrumError("Frequency grids differ between components")
        results[name] = psd
        segment_counts.add(count)
        resolutions.add(resolution)

    if len(segment_counts) != 1 or len(resolutions) != 1:
        raise SpectrumError("Three components produced inconsistent spectral settings")
    assert frequency_reference is not None

    psd_z = results["vertical"]
    psd_n = results["north"]
    psd_e = results["east"]
    asd_z = np.sqrt(psd_z)
    asd_n = np.sqrt(psd_n)
    asd_e = np.sqrt(psd_e)

    horizontal_rms_asd = np.sqrt((psd_n + psd_e) / 2.0)
    hv_rms = np.full(asd_z.shape, np.nan, dtype=np.float64)
    np.divide(horizontal_rms_asd, asd_z, out=hv_rms, where=asd_z > 0)

    horizontal_geometric_asd = np.sqrt(asd_n * asd_e)
    hv_geometric = np.full(asd_z.shape, np.nan, dtype=np.float64)
    np.divide(horizontal_geometric_asd, asd_z, out=hv_geometric, where=asd_z > 0)

    return Spectrum(
        frequency_hz=frequency_reference,
        psd_vertical=psd_z,
        psd_north=psd_n,
        psd_east=psd_e,
        asd_vertical=asd_z,
        asd_north=asd_n,
        asd_east=asd_e,
        hv_rms=hv_rms,
        hv_geometric=hv_geometric,
        segment_count=next(iter(segment_counts)),
        frequency_resolution_hz=next(iter(resolutions)),
    )


def write_outputs(
    input_path: Path,
    output_dir: Path,
    waveform: Waveform,
    spectrum: Spectrum,
    nperseg: int,
    overlap: float,
    dataset_id: str,
) -> tuple[Path, Path]:
    if output_dir.exists():
        raise SpectrumError(
            f"Output directory already exists; choose a new run directory: {output_dir}"
        )
    output_dir.mkdir(parents=True, exist_ok=False)

    input_hash = hashlib.sha256(input_path.read_bytes()).hexdigest()
    spectra_path = output_dir / "spectra.csv"
    metadata_path = output_dir / "processing.json"

    with spectra_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "frequency_hz",
            "psd_vertical_unit2_per_hz",
            "psd_north_unit2_per_hz",
            "psd_east_unit2_per_hz",
            "asd_vertical_unit_per_sqrt_hz",
            "asd_north_unit_per_sqrt_hz",
            "asd_east_unit_per_sqrt_hz",
            "hv_rms_power_mean",
            "hv_geometric_asd",
        ])
        for values in zip(
            spectrum.frequency_hz,
            spectrum.psd_vertical,
            spectrum.psd_north,
            spectrum.psd_east,
            spectrum.asd_vertical,
            spectrum.asd_north,
            spectrum.asd_east,
            spectrum.hv_rms,
            spectrum.hv_geometric,
        ):
            writer.writerow([
                f"{float(v):.17g}" if math.isfinite(float(v)) else "NaN"
                for v in values
            ])

    metadata = {
        "schema_version": "1.0",
        "status": "DERIVED_SPECTRAL_ESTIMATE_NOT_PHYSICAL_MODE_IDENTIFICATION",
        "dataset_id": dataset_id,
        "input_csv": str(input_path),
        "input_sha256": input_hash,
        "sample_rate_hz": waveform.sample_rate_hz,
        "sample_count": int(waveform.vertical.size),
        "unit": waveform.unit,
        "time_column_checked": waveform.time_s is not None,
        "nperseg": nperseg,
        "overlap_fraction": overlap,
        "window": "symmetric Hann",
        "detrend": "remove segment mean",
        "segment_count": spectrum.segment_count,
        "frequency_resolution_hz": spectrum.frequency_resolution_hz,
        "psd_method": (
            "One-sided modified periodograms; |rFFT(x*w)|^2 / "
            "(sample_rate * sum(w^2)); double positive interior bins; "
            "arithmetic mean over overlapping segments."
        ),
        "hv_rms_power_mean": "sqrt((PSD_N + PSD_E)/2) / ASD_Z",
        "hv_geometric_asd": "sqrt(ASD_N * ASD_E) / ASD_Z",
        "limitations": [
            "Input must already be calibrated to physical units.",
            "No instrument response correction is performed.",
            "No axis rotation or orientation correction is performed.",
            "No automatic transient-window rejection is performed.",
            "H/V ratios are diagnostic spectral estimates, not structural-mode identification.",
            "This processing does not establish historical use or function.",
        ],
        "software": {
            "python": sys.version.split()[0],
            "numpy": np.__version__,
        },
        "outputs": {
            "spectra_csv": spectra_path.name,
        },
    }
    metadata_path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return spectra_path, metadata_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Calibrated 3C CSV")
    parser.add_argument("--output-dir", type=Path, required=True, help="New output directory")
    parser.add_argument("--sample-rate", type=float, required=True, help="Sample rate in Hz")
    parser.add_argument("--unit", choices=sorted(ALLOWED_UNITS), required=True, help="Calibrated physical unit")
    parser.add_argument("--dataset-id", required=True, help="Dataset ID from the intake manifest")
    parser.add_argument("--nperseg", type=int, default=4096, help="Samples per Welch segment")
    parser.add_argument("--overlap", type=float, default=0.5, help="Segment overlap fraction")
    parser.add_argument("--time-column", default=TIME_COLUMN, help="Optional uniform time column name")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        waveform = read_waveform_csv(
            args.input,
            sample_rate_hz=args.sample_rate,
            unit=args.unit,
            time_column=args.time_column,
        )
        spectrum = analyze_waveform(waveform, args.nperseg, args.overlap)
        spectra_path, metadata_path = write_outputs(
            args.input, args.output_dir, waveform, spectrum,
            args.nperseg, args.overlap, args.dataset_id,
        )
        print(f"Spectra: {spectra_path}")
        print(f"Processing metadata: {metadata_path}")
        print(f"Samples: {waveform.vertical.size}; segments: {spectrum.segment_count}")
        print(f"Frequency resolution: {spectrum.frequency_resolution_hz:.9g} Hz")
        print("Status: derived spectral estimate; no physical-mode interpretation performed")
        return 0
    except (SpectrumError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
