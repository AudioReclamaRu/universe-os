# Phase 19 — adaptive affine-IFS conjugacy pipeline

## Purpose

Phases 17 and 22 solve complementary cases. Phase 17 reconstructs an affine coordinate frame from unique map fixed points when the source fixed-point cloud spans the ambient space. Phase 22 represents the whole family as an exact directed, edge-labelled relational graph and searches for one common map bijection before solving the full affine equations.

Phase 19 is the deterministic controller. It uses the fast fixed-point route first; only when that method's assumptions do not hold does it invoke the Phase 22 relational graph and affine-witness pipeline.

## A. Routing policy

1. Run the exact Phase 17 fixed-point-frame comparator.
2. Accept a verified witness or a complete result under the frame method's assumptions.
3. If unique fixed points or full source affine span are unavailable, run Phase 22.
4. Phase 22 colours vertices by exact characteristic polynomial and relational profile, checks all directed pairwise word-trace labels under one common permutation, and then solves Phase 18's exact affine equations.
5. Dimension, field and map-count mismatches are terminal.
6. A Phase 17 frame-search cap remains unresolved and is not silently retried through another search.
7. Phase 22 graph-node and candidate-isomorphism caps are also unresolved, not negative.

The controller records every attempted method, the trigger for switching, the selected route and the final result.

## B. Why the routes are complementary

The Phase 17 route avoids factorial map-permutation enumeration when unique fixed points provide a full coordinate frame.

The Phase 22 fallback does not require such a frame. It first compares vertex colours and all directed pair labels in the matrix family. Only a complete relational graph isomorphism is allowed to proceed to exact affine-equation solving. Phase 22 uses Phase 21's six pairwise trace words and Phase 20's characteristic-polynomial invariant, but retains the full incidence relation between ordered pairs instead of relying only on separate per-map multisets.

The Menger control remains on the Phase 17 route. Its uniform scalar linear parts and symmetric relational graph do not offer useful pruning through the fallback.

## C. Demonstrations

- **20-map Menger IFS:** the full-rank fixed-point cloud routes to Phase 17, which recovers and verifies a witness after 23 of 116,280 ordered target frames.
- **Two-map coincident-fixed-point IFS:** Phase 17 reports that the source fixed points do not span the plane. Phase 22 then recovers an exact relationally consistent map bijection and an invertible affine witness.
- **Equal individual spectra with incompatible family relations:** Phase 22 rejects the directed relational graph before solving any affine system.

These are mathematical software controls, not physical measurements or evidence of common natural origin.

## D. Search-cap and negative-result discipline

A search cap is not a mathematical negative result.

- Phase 17 frame-cap result remains unresolved and is returned without automatic fallback.
- Phase 22 graph-node or candidate-isomorphism caps remain unresolved.
- A complete Phase 17 negative result is retained under the frame assumptions.
- A Phase 22 graph with no compatible vertex/edge-labelled bijection is a negative result for the supplied finite family and selected invariant set.
- If relational graph isomorphisms exist, Phase 22 checks every affine family under its configured budget; complete exhaustion is required for a negative affine-conjugacy result.

## E. Scope and limitations

- Exact affine IFS map families in dimensions 1–3.
- Common real quadratic coefficient field, using Phase 16 exact arithmetic.
- Phase 17 requires a unique fixed point for every map and full affine span of source fixed points.
- Phase 22 uses exact characteristic polynomials and directed edge-labelled pairwise traces; Phase 24 adaptively appends longer exact two-generator matrix-word traces when stable classes remain ambiguous. These are necessary, not complete invariants for simultaneous similarity.
- The exact affine equations and determinant feasibility remain decisive.
- Search is bounded by frame, graph-node and candidate-isomorphism limits. Adaptive matrix-word expansion has a separate matrix-product budget and a maximum word length.
- No nonlinear conjugacy, mixed-field composita, higher-degree number fields or physical causal interpretation is inferred.

## F. Validation

Nine standard-library routing tests are included. They cover the Menger fast path, the Phase 22 fallback, a frame-search cap, a complete Phase 17 negative result, an input mismatch, relational rejection of an incompatible family, a Phase 22 graph-search cap, Phase 24 budget propagation and empty-payload validation.

The Phase 19 package is checked in the dedicated Python 3.12 matrix alongside Phases 16–24. The latest clean-checkout totals are recorded in the root research README after the final CI run.

## G. Relation to the Canonical Mathematical Pattern Atlas

Phase 19 combines geometric coordinate recovery with exact structural relations across an entire finite operator family. It keeps the distinction between necessary invariants, a candidate relational isomorphism and a fully verified affine witness.

A verified match does not establish a shared natural origin, historical direction, energy transfer, source/receiver path or physical causal bridge.

## H. Phase 24 integration

The Phase 22 fallback now calls Phase 24 after the initial exact Phase 21
profiles and Phase 23 directed colour refinement. Phase 24 expands the
noncommutative trace-word family only for pairs touching unresolved colour
classes, then reruns Phase 23 jointly. A complete word tier is charged against
the explicit matrix-product budget and is either fully applied or skipped.
Phase 22 still performs complete directed graph search where its budget
allows; Phase 18's affine equations and determinant witness remain decisive.

The adaptive controller exposes max_matrix_products and max_word_length in
both direct calls and batch payloads. Frame-search, graph-search and word
budgets remain separate; a cap in one layer is not silently treated as a
negative result in another.

## I. Next increments

1. Add exact algebraic dependency detection between matrix words to avoid
   spending budget on trace expressions already implied by shorter words.
2. Explore higher-degree word invariants and mixed coefficient fields under
   explicit resource controls.
3. Connect verified structural candidates to measured systems with provenance,
   uncertainty, physical carrier paths and falsifiable mechanisms.

The Phase 22 fallback now applies Phase 23 joint directed colour refinement before its graph search. The initial exact colours still combine the Phase 20 characteristic polynomial and Phase 21 relational profile; Phase 23 then refines by incoming/outgoing edge labels against neighbour classes. The adaptive controller contract and cap semantics are unchanged. The integrated implementation is validated by the Phase 19 and Phase 22 jobs in the Phase 23-era workflow.
