# Phase 19 — adaptive affine-IFS conjugacy pipeline

## Purpose

Phases 17–18 solve complementary cases. Phase 17 reconstructs an affine coordinate frame from unique map fixed points when the source fixed-point cloud spans the ambient space. Phase 18 solves the full affine operator equations and can recover an invertible coordinate change even when the fixed-point geometry is degenerate.

Phase 19 is the deterministic controller. It uses the fast fixed-point route first; only when that method's assumptions do not hold does it route through Phase 21 joint trace profiles, Phase 20 characteristic-polynomial partitions and the Phase 18 exact determinant-family solver.

## A. Routing policy

1. Run the exact Phase 17 fixed-point-frame comparator.
2. Accept a verified witness or a complete result under the frame method's assumptions.
3. If unique fixed points or full source affine span are unavailable, run the Phase 21 relational trace-profile filter. That passes only necessary candidate edges to Phase 20.
4. Phase 20 intersects those edges with exact individual characteristic-polynomial compatibility and solves the remaining candidate matchings with Phase 18.
5. Dimension, field and map-count mismatches are terminal.
6. A Phase 17 frame-search cap remains unresolved and is not silently retried through another search.
7. Every fallback result retains the status and limits of the method that produced it.

## B. Why the routes are complementary

The Phase 17 route avoids factorial map-permutation enumeration when unique fixed points provide a full coordinate frame.

The Phase 21 → Phase 20 → Phase 18 route does not require such a frame. It compares the relations between each linear operator and the rest of its family, then applies an individual spectral invariant, and finally tests the complete affine equations. The trace and characteristic-polynomial filters are necessary conditions only; the exact common affine transformation is still the decisive test.

The Menger control remains on the Phase 17 route. Its maps share the same scalar linear part and identical joint trace profiles, so the fallback filters would not reduce its candidate graph.

## C. Demonstrations

- **20-map Menger IFS:** the full-rank fixed-point cloud routes to Phase 17. The exact rational control finds a valid witness after 23 of 116,280 ordered target frames.
- **Two-map coincident-fixed-point IFS:** the source fixed points do not span the plane. Phase 21 preserves the two valid relational profiles, Phase 20 retains the two characteristic-compatible pairings, and Phase 18 recovers an invertible witness from a two-parameter affine solution family.
- **Equal individual spectra but incompatible family relations:** Phase 20 alone leaves four possible edges. Phase 21's joint trace profiles reduce these to zero, rejecting the supplied finite family without solving an affine system.

These are mathematical software controls, not physical measurements or evidence of common natural origin.

## D. Search-cap and negative-result discipline

A search cap is not a mathematical negative result.

- Phase 17 frame-cap result remains unresolved and is returned without automatic fallback.
- Phase 20 candidate-matching-cap result remains unresolved.
- A complete Phase 17 negative result is retained under the frame assumptions.
- A complete Phase 20 negative result is retained only after all candidate perfect matchings are examined and all consistent affine families fail the exact invertibility test.
- A zero-edge Phase 21 relational graph is a complete negative result only for the stated finite family and selected necessary-invariant family.

## E. Scope and limitations

- Exact affine IFS map families in dimensions 1–3.
- Common real quadratic coefficient field, using Phase 16 exact arithmetic.
- Phase 17 requires a unique fixed point for every map and full affine span of source fixed points.
- Phase 21 uses six selected pairwise trace words; these are necessary, not complete, simultaneous-similarity invariants.
- Phase 20 uses individual characteristic polynomials; these are also necessary, not sufficient, similarity invariants.
- Phase 18 solves the remaining affine equation families; its candidate matching search remains capped.
- A Phase 17 target-frame cap is not automatically retried.
- No nonlinear conjugacy, mixed-field composita, higher-degree number fields, or physical causal interpretation is inferred.

## F. Validation

Seven standard-library routing tests are included. They cover the Menger fast path, the Phase 21 → Phase 20 → Phase 18 fallback, a frame-search cap, a complete Phase 17 negative result, an input mismatch, relational rejection of equal-characteristic-polynomial but incompatible families, and empty-payload validation.

All seven Phase 19 routing tests passed in the clean GitHub Actions pull-request checkout, workflow run [45243433007](https://github.com/AudioReclamaRu/universe-os/actions/runs/45243433007), using Python 3.12. The matrix covers phases 16–21 only; it is not a repository-wide CI pass claim.

## G. Relation to the Canonical Mathematical Pattern Atlas

Phase 19 combines geometric coordinate recovery, relations among operators, individual spectral invariants and exact affine-family feasibility. This is a concrete adaptive search architecture for structural equivalence.

A verified match does not establish a shared natural origin, historical direction, energy transfer, source/receiver path, or physical causal bridge.

## H. Next increments

1. Expand the Phase 21 trace family adaptively with cyclic words of greater length under an explicit complexity budget.
2. Compare generated matrix-algebra invariants while retaining full affine-equation verification.
3. Add exact handling of compatible coefficient-field extensions and composita.
4. Extend the adaptive controller beyond affine IFS to substitution tilings, cellular automata, L-systems and nonlinear operators.
5. Connect the structural engine to measured geometries and dynamical datasets with coordinate provenance, uncertainty and physical falsifiers.
