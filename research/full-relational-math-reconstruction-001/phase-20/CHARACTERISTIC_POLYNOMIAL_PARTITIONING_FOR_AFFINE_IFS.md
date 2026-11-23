# Phase 20 — exact characteristic-polynomial partitions for affine IFS matching

## Purpose

Phase 18 can solve an underdetermined affine conjugacy family exactly, but it still enumerates map permutations. Phase 20 reduces that search before constructing the full affine system.

For any invertible affine coordinate change \(H(x)=Px+t\), the linear parts of a paired map must satisfy

\[
PA_i=C_{\pi(i)}P,\qquad \det P\ne0.
\]

Therefore \(A_i\) and \(C_{\pi(i)}\) are similar matrices and must have the same exact characteristic polynomial. This is a necessary invariant, not a sufficient proof of conjugacy.

Phase 20 uses this fact to build a bipartite candidate graph and searches only its perfect matchings.

## A. Exact characteristic-polynomial invariant

For dimensions one through three, the comparator calculates the descending coefficients of

\[
\chi_A(\lambda)=\det(\lambda I-A)
\]

using exact rational and quadratic-surd field arithmetic.

For a three-dimensional matrix, the coefficients are

\[
\chi_A(\lambda)=
\lambda^3-\operatorname{tr}(A)\lambda^2
+\frac{(\operatorname{tr}A)^2-\operatorname{tr}(A^2)}{2}\lambda
-\det(A).
\]

All comparisons are exact. No eigenvalue approximation, tolerance or rounded spectrum is used.

If two characteristic polynomials differ, those linear parts cannot be similar, so that map pairing is impossible under an invertible affine conjugacy. If they match, the pair is only a candidate: matrices with the same characteristic polynomial need not be similar.

## B. Bipartite candidate graph

Create a bipartite graph:

- left vertices: source affine maps;
- right vertices: target affine maps;
- edge \(i\to j\): exact characteristic polynomials of \(A_i\) and \(C_j\) are equal.

A perfect matching is necessary for a bijection between the map families. If no perfect matching exists, the comparator can reject affine conjugacy without solving any full affine systems.

Candidate perfect matchings are enumerated with a minimum-remaining-values ordering and exact residual matching checks. This avoids testing permutations that violate the necessary linear-part invariant.

For each complete candidate matching, Phase 20 reuses the Phase 18 exact linear equations. It parameterizes the solution family, tests the determinant polynomial, constructs an invertible witness when one exists, and verifies every original map equation.

## C. Demonstration: 4 candidates instead of 24 unrestricted permutations

The synthetic one-dimensional control has four source maps with four distinct slopes. The target maps have the same four exact linear-part signatures, expressed in a translated coordinate frame.

The unrestricted map-order search contains \(4!=24\) permutations. The exact characteristic-polynomial graph contains only four edges and one perfect matching. The comparator solves one affine system, recovers \(P=1\) and \(t=3\), and verifies all four affine map equations.

This demonstrates invariant-based reduction when linear-part signatures distinguish the maps. It is a software control, not an empirical physical finding.

## D. When the filter helps — and when it does not

The filter can dramatically reduce matching search when the map family has diverse linear parts and their characteristic polynomials are distinctive.

It offers little or no pruning when all maps share the same linear part. The Menger sponge IFS is an example: its 20 maps use the same one-third scalar contraction in three dimensions. Its candidate graph is therefore complete. The Phase 17 fixed-point-frame method remains the preferred route for that family.

Phase 20 must not claim that characteristic-polynomial equality establishes map equivalence. Every candidate matching must still satisfy one common affine coordinate transformation.

## E. Search and result semantics

- **affine_conjugacy_verified** — one candidate matching produced an exact invertible affine witness, and all map equations passed exact verification.
- **no_affine_conjugacy_found** — either the necessary-invariant graph has no perfect matching, or all candidate perfect matchings were exhausted without an invertible witness.
- **candidate_matching_search_limit_reached** — the candidate matching cap was reached; the result is unresolved, not negative.
- dimension, field and map-count mismatch statuses — inputs are not comparable within this implementation.

A complete negative result applies only to the supplied finite affine map families and declared coefficient field. It does not exclude nonlinear conjugacy, omitted maps, a different number field, or a physical process outside the model class.

## F. Scope and limitations

- Dimensions 1–3.
- Exact rational / real-quadratic field arithmetic.
- Characteristic polynomials are necessary invariants, not complete similarity invariants.
- Candidate matchings are searched under a configurable cap.
- Families with repeated characteristic polynomials can still have factorially many candidate matchings.
- The implementation reuses Phase 18's exact determinant-family witness construction.
- Nonlinear conjugacies, higher-degree number fields, mixed-field composita and physical causal inference remain outside scope.

## G. Validation

Six standard-library tests are included. They cover an exact three-dimensional characteristic polynomial, a four-map reduction from 24 unrestricted permutations to four candidate edges, a coincident-fixed-point affine witness, an invariant-based negative result, a capped ambiguous matching graph, and empty-payload validation.

All six Phase 20 tests passed in the clean GitHub Actions pull-request checkout, workflow run [45243433007](https://github.com/AudioReclamaRu/universe-os/actions/runs/45243433007), using Python 3.12. The workflow is limited to the affine IFS phases 16–21 and does not establish repository-wide CI.

## H. Relation to the Canonical Mathematical Pattern Atlas

Phase 20 adds an exact similarity invariant to the structural-comparison layer. It uses the invariant as a necessary filter, then retains the complete affine-operator equations, coordinate transformation, invertibility test and independent verification as the decisive criteria.

The result is mathematical structural correspondence only. It does not establish a shared physical origin, source/receiver path, energy transfer, causal coupling or natural implementation.



Phase 19 now calls this exact partition as its fallback when fixed-point-frame assumptions are inapplicable. The 20-map Menger control remains on the Phase 17 route because all its maps share the same scalar linear part and the characteristic-polynomial filter would not reduce its candidate graph. See [the adaptive Phase 19 pipeline](../phase-19/ADAPTIVE_AFFINE_IFS_CONJUGACY_PIPELINE.md).


Phase 19 now applies Phase 21 joint pairwise trace profiles before this characteristic-polynomial filter. The Menger control remains on the Phase 17 fast path because the uniform-contraction generator does not gain useful pruning from either fallback invariant. See [Phase 21](../phase-21/JOINT_TRACE_PROFILES_FOR_AFFINE_IFS.md) and [the adaptive Phase 19 pipeline](../phase-19/ADAPTIVE_AFFINE_IFS_CONJUGACY_PIPELINE.md).



Phase 22 combines this necessary individual spectral invariant with Phase 21's relational profiles as vertex colours in one directed, edge-labelled graph. It checks all ordered pair labels under a single map bijection before solving the full affine equations. See [Phase 22](../phase-22/RELATIONAL_GRAPH_ISOMORPHISM_FOR_AFFINE_IFS.md).

## I. Next increments

1. Add stronger exact similarity invariants for dimensions two and three, while retaining full affine-equation verification.
2. Preserve the incidence of relational traces across the full operator family, as implemented by the Phase 22 directed relational graph.
3. Add operator- and graph-level partitions for substitution tilings, cellular automata, L-systems and other Atlas generators.
4. Connect candidate relations to measured geometries and dynamical datasets, with uncertainty and falsifiers.
