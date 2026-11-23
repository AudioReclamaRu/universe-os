# Phase 10 — whole-atlas comparison of dimensionless relations

## Purpose

Phase 09 derives one or more complete bases of dimensionless monomials from a declared physical-variable set. Phase 10 searches those bases for bounded integer-power combinations that numerically match the machine-readable numerical reference subset of the Canonical Mathematical Pattern Atlas.

The comparator examines products, quotients, powers and inverse powers of dimensionless groups rather than only each group in isolation.

## Files

- atlas_relation_comparator.py — standard-library comparator.
- test_atlas_relation_comparator.py — unit tests.
- phase09_source_variables.json — synthetic input to Phase 09.
- example_input.json — Phase 09 JSON output consumed by this phase.
- example_match_summary.json — compact summary of the synthetic Phase 10 result.

The script imports the numeric reference registry from the sibling Phase 08 module. Keep Phase 08, Phase 09 and Phase 10 as sibling directories in the research tree.

Run:

    python -m unittest -v
    python atlas_relation_comparator.py example_input.json --output atlas_comparison.json

Optional search controls:

    --tolerance 0.0001
    --max-terms 3
    --exponent-bound 2
    --max-candidates 20000

## Relation search

For a selected basis \(B=(\Pi_1,\ldots,\Pi_n)\), the engine enumerates

\[
R_{\mathbf k}=\prod_{i=1}^{n}\Pi_i^{k_i},
\qquad k_i\in\mathbb Z,
\]

with at most max-terms nonzero exponents and each exponent bounded by the selected exponent limit, excluding zero on selected coordinates.

All bounded integer-power vectors are retained, including non-primitive vectors. A power such as \(\Pi^2\) may match a canonical constant even when \(\Pi\) itself does not.

The number of candidates before the cap, for \(n\) groups, maximum \(k\) nonzero terms and exponent bound \(b\), is

\[
N(n,k,b)=\sum_{j=1}^{k}\binom{n}{j}(2b)^j.
\]

The cap prevents accidental combinatorial explosion. Cross-basis products are never generated.

## Alternative bases must remain separate

The null-space basis from Phase 09 is not unique. Its canonical basis and every reported alternative basis are separate complete coordinate descriptions of the same rational dimensionless-exponent subspace.

Phase 10 loads each basis as a separate BasisSet, enumerates candidate monomials within that basis only and emits a separate result section. It never combines a group from one basis with a group from another.

The same abstract relation may have different exponent vectors or formulas in different bases. A stable Atlas match across alternative bases is a basis-robustness check, not multiple independent discoveries.

If any group lacks a numeric value, it is listed as omitted and the search is labelled partial_numeric_projection. A basis with no numeric values remains listed with no candidates; the search does not silently delete it.

## Atlas matching

Phase 10 imports Phase 08's machine-readable numerical subset, currently including \(\varphi,\pi,e,\sqrt2,\sqrt3\), silver and plastic constants, Feigenbaum's period-doubling constant, Sierpiński/Cantor/gasket spectral dimensions and selected integer identities.

This is not the full structural atlas. Mandelbrot/Julia generators, graph spectra, symmetry groups, topology, substitution systems, automata, recurrence operators and differential systems require separate structural comparators; they must not be reduced to a list of decimals.

A numeric match is a candidate correspondence, not an exact symbolic identity, empirical law, common origin or causal mechanism. The screen is uncorrected for multiple comparisons; the report records tolerance and candidate count and supplies no significance claim.

## Numerical and evidence safeguards

- Candidate values are evaluated in the logarithmic domain to avoid intermediate overflow.
- Negative dimensionless groups are supported with integer-power sign rules.
- A zero group with a positive exponent evaluates to zero; a zero group with a negative exponent is retained as undefined rather than silently dropped.
- Candidates outside finite floating-point range are retained symbolically with numeric value null.
- Inputs may carry units, sources and evidence statuses from Phase 09.
- Uncertainty is not yet propagated through Phase 09 basis transformations and this monomial search. Missing uncertainty is not zero.
- The search uses a finite exponent and term window; it does not enumerate every rational, real, algebraic or transcendental exponent.

## Synthetic example

The example is deliberately artificial. Phase 09 receives two dimensionless variables:

\[
A=2,\qquad B=\frac{\varphi}{2}.
\]

It produces a canonical basis and four alternative bases. Phase 10 searches each independently. In the canonical basis, \(AB=\varphi\). In alternative bases, the same numerical reference is represented by different group coordinates.

The included match summary shows the five basis representations. This demonstrates software behaviour only; it is not a measurement or discovery about a physical system.

## Validation

Twelve standard-library unit tests pass locally. They cover product matching, basis separation, retention of non-primitive powers, power-to-constant matches, floating-point overflow, signed integer powers, zero denominators, fully non-numeric and partially numeric bases, tolerance validation, candidate caps and paired integer keys.

The Phase 09 → Phase 10 synthetic pipeline ran successfully in a repository-shaped test directory. This is local module-level verification, not a full-repository CI or fresh-checkout claim.

## Next increments

1. Propagate covariance matrices and interval uncertainty through Π groups and monomial relations.
2. Compare relations under equivalent rational basis transformations and identify basis-invariant content.
3. Add exact symbolic algebraic-number representations; floating-point matching remains a discovery screen.
4. Add multiple-comparison-aware null models without deleting candidate relations.
5. Add structural comparators for recurrence matrices, graph spectra, fractal generators, symmetry representations, topology and nonlinear dynamics.
6. Add measured-data adapters with calibration, source, units, coordinate frame, observation window and resolution provenance.
