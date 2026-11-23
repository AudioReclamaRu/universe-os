# Phase 08 — Executable relation-discovery kernel

## Purpose

Phase 07 defined the relation-first framework. Phase 08 adds a small, executable reference kernel that turns supplied data into dimensionally admissible relation candidates and compares numerical results against a machine-readable subset of the Canonical Mathematical Pattern Atlas.

This is the first working instrument, not the final universal discovery engine. It clearly separates what is automated now from what still requires further mathematics.

## Files and use

- relation_discovery.py — standard-library implementation.
- test_relation_discovery.py — unit tests.
- example_input.json — synthetic demonstration input.
- example_report.json — generated demonstration output.

From this directory run:

    python -m unittest -v
    python relation_discovery.py example_input.json --output example_report.json

No third-party packages are required.

## Current capabilities

### Typed quantities and dimensional checks

Each quantity carries a unique name, a value in coherent SI units, seven SI base-dimension exponents (L, M, T, I, Theta, N, J), optional standard uncertainty, source/status labels and an optional coordinate-frame identifier.

Dimension exponents are rational. Pairwise ratios are generated only when numerator and denominator have identical dimensions. A length/time ratio is never silently treated as dimensionless.

### Relation generation

The kernel generates both orientations of every dimensionally compatible pairwise ratio. It can optionally generate cross-ratios for four coordinates only when all four share a declared coordinate frame. It also fits a power law y = A x^z from at least three strictly positive data pairs.

Pairwise ratio generation is quadratic in the number of quantities. Cross-ratio enumeration is quartic and is off by default; use it only on a selected, common-frame coordinate set.

The power-law fit is ordinary least squares in log space. It reports exponent, amplitude, residuals and R-squared. It does not yet calculate confidence intervals, compare alternative models, account for correlated errors or establish causality. A high R-squared is not proof of a scaling law.

### Atlas comparison

The initial numeric register contains symbolic/exact expressions and numerical screening values for φ, π, e, selected algebraic roots, silver and plastic constants, Feigenbaum's period-doubling constant, Sierpiński/Cantor/gasket spectral dimensions and selected integer identities.

For each candidate, the kernel computes relative numerical error against every registered numerical reference and retains matches within the explicit user-declared tolerance. Exact expressions are kept alongside numeric results.

This register is only a machine-readable subset of the wider Canonical Pattern Atlas. Structural families (Mandelbrot/Julia generators, graph spectra, symmetry groups, topology, substitution systems, automata and differential operators) need dedicated structural comparators and must not be flattened into decimal constants.

A match means only that a numerical candidate lies within the selected tolerance. It is not an exact symbolic identity, evidence of common origin or proof of a physical mechanism.

### Uncertainty and evidence

For ratios, uncertainty is propagated from independent input standard uncertainties using first-order relative-error propagation. If an input uncertainty is absent, the output uncertainty remains null rather than being silently treated as zero.

Every generated output is labelled as a derived candidate and carries an explicit guard against causal interpretation. Input provenance is represented in the input schema; full per-input provenance propagation into each report record is a planned schema increment.

Integer report keys use paired binary/ternary notation. Exact irrational references remain symbolic; floating-point values are secondary computational fields.

## Input schema

See example_input.json. Minimal quantity fields are name, value and dimension. Dimension keys are L, M, T, I, Theta, N and J. Values may be JSON numbers or rational/decimal strings. Convert all values to coherent SI units before analysis.

Cross-ratio inputs additionally require a shared nonempty coordinate_frame and include_cross_ratios=true. Like units alone do not imply a common coordinate line or projective reference frame.

## Deliberate current limitations

This kernel does not yet:
- solve general Buckingham-Π null-space systems for arbitrary variable sets;
- prove symbolic identities in algebraic number fields;
- enumerate products/powers over all variable subsets;
- compare graph spectra, symmetry groups, topology, fractal generators, substitution rules, automata or differential operators structurally;
- infer causal mechanisms, transfer paths, energy budgets or historical intent;
- ingest raw survey, sensor, image, field, spectral or time-series datasets directly;
- correct multiple-comparison bias or provide calibrated significance;
- discover every possible relation (an unbounded task).

## Validation

Nine standard-library tests cover paired numeral keys, dimensional arithmetic, rejection of incompatible dimensions, φ screening, cross-ratio frame constraints, uncertainty propagation, duplicate names, power-law recovery and positive-domain checks. All nine tests passed locally. The synthetic CLI example also ran.

This is local verification of the kernel and test module, not a fresh-checkout or CI claim for the full research repository.

## Next increments

1. Exact symbolic expression trees and algebraic simplification.
2. Buckingham-Π engine with dimension-matrix rank and alternative-basis audit.
3. Relation-of-relations generation with dimensional, depth and combinatorial controls.
4. Scaling-window, crossover, finite-size and discrete-scale-invariance analysis with uncertainty intervals.
5. Structural atlas comparators for recurrence operators, graph spectra, symmetry groups, topology, fractal generators and dynamical systems.
6. Surrogate/null models and multiple-comparison accounting, retaining candidates and negative results.
7. Dataset adapters and domain-specific validation packs. Giza, geological, seismic, acoustic, atmospheric and astronomical data remain separate evidence streams.

## Canonical interpretation

The engine generates and compares candidates; it does not decide what nature means. It preserves symbolic references, requires dimensional compatibility, exposes uncertainty and prevents numerical proximity from being promoted to a physical law without mechanism, evidence and falsifiable tests.
