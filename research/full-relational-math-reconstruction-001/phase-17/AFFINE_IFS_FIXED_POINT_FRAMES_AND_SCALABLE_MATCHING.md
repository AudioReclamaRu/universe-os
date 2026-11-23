# Phase 17 — fixed-point affine frames and scalable IFS matching

## Purpose

Phase 16 established exact affine-conjugacy comparison for finite affine iterated-function systems (IFS), but its exhaustive search enumerated permutations of the complete map list. For a 20-map generator such as the Menger sponge, that map-order search grows as a factorial and becomes unusable even though the geometric transformation is low-dimensional.

Phase 17 changes the search object. Instead of guessing a complete map permutation, it uses the fixed points of the affine maps to identify an affine coordinate frame, then solves the remaining map correspondence as a bipartite perfect-matching problem.

## A. Fixed points carry the coordinate transformation

For each affine map

\[
F_i(x)=A_i x+b_i,
\]

its fixed point satisfies

\[
x_i^*=A_i x_i^*+b_i,
\qquad
(I-A_i)x_i^*=b_i.
\]

When \(I-A_i\) is nonsingular, the fixed point is computed exactly in the declared rational or real-quadratic field. This condition is checked per map; the algorithm does not silently assume that every affine map has a unique fixed point.

Suppose the source fixed-point cloud contains an affine frame in ambient dimension \(d\): \(d+1\) affinely independent points. Phase 17 selects one deterministic source frame. Any true invertible affine conjugacy

\[
H(x)=Px+t,\qquad \det P\ne0,
\]

must send those selected source points to an ordered target frame. Therefore the algorithm can enumerate ordered target frames, rather than all permutations of all IFS maps.

For source frame \(x_0,\ldots,x_d\) and a candidate target frame \(y_0,\ldots,y_d\), define the difference matrices whose columns are the differences from the first point:

\[
X=[x_1-x_0\;\cdots\;x_d-x_0],\qquad
Y=[y_1-y_0\;\cdots\;y_d-y_0].
\]

When both are nonsingular, the only affine map sending this ordered frame to the target frame is

\[
P=YX^{-1},\qquad t=y_0-Px_0.
\]

All arithmetic is exact; a floating-point near-match is not accepted.

## B. Map correspondence as a bipartite graph

For a candidate \((P,t)\), source map \(i\) may correspond to target map \(j\) only when both exact conditions hold:

\[
Px_i^*+t=y_j^*,
\]

\[
PA_i=C_jP.
\]

These tests create a bipartite graph between source-map indices and target-map indices. A perfect matching gives a one-to-one map correspondence without enumerating all \(m!\) map permutations. Duplicate fixed points are retained as separate vertices, so map multiplicity is not collapsed.

The resulting affine map and matching are then passed through an independent exact verification of every original affine identity:

\[
H\circ F_i=G_{\pi(i)}\circ H.
\]

The fixed-point and linear-part tests imply the corresponding translation identity when the fixed points are unique, but the implementation still performs the full equation check before returning a verified result.

## C. When the method is complete — and when it is not

The fixed-point-frame search is complete if all of the following hold:

1. Every source and target affine map has a unique fixed point in the declared exact field.
2. The source fixed-point cloud spans the full ambient affine space.
3. Every ordered target frame of \(d+1\) fixed points is examined.
4. Candidate maps are matched with a complete bipartite perfect-matching procedure.
5. Every proposed witness is checked against all affine map equations.

Under these conditions, if an affine conjugacy exists, it maps the selected source frame to one of the enumerated target frames. Exhausting all target frames without a verified witness is therefore a negative result for affine conjugacy in the declared field and coordinate dimension.

The implementation explicitly returns an inconclusive status when a map lacks a unique fixed point, when the source fixed-point cloud is not full-dimensional, or when the target-frame search cap is reached. A capped search is **unresolved, not negative**. It does not use a negative result to exclude nonlinear conjugacies, transformations over larger fields, or mechanisms outside the declared model class.

## D. Complexity and the Menger control

With \(m\) maps in dimension \(d\), the target-frame search contains at most

\[
m(m-1)\cdots(m-d)
\]

ordered frames. The default frame cap is 250,000. For the 20-map Menger IFS in three dimensions, there are 116,280 ordered target frames, while the Phase 16 map-permutation strategy would face \(20!\) possible map orderings.

The synthetic control constructs the standard 20-map Menger sponge IFS, applies an exact invertible affine coordinate change, reverses the target map list, and asks the comparator to recover a witness. The implementation returns the status **affine_conjugacy_verified**, maps all 20 source maps one-to-one, and verifies every affine identity exactly. It finds a witness after examining 23 target frames, out of 116,280 possible ordered frames. The returned coordinate transformation is a valid witness; because the Menger generator has internal symmetries, it need not be the same transformation that was used to construct the synthetic target.

This demonstrates the algorithmic improvement on a controlled mathematical example. It is not a physical measurement, evidence of a natural Menger-like process, or proof of a common historical origin.

## E. Status semantics

- **affine_conjugacy_verified** — an invertible affine map and a complete map matching were found and independently verified.
- **no_affine_conjugacy_found** — the full target-frame search was exhausted under the stated fixed-point and full-span assumptions.
- **target_frame_search_limit_reached** — the search cap was reached; the result is unresolved.
- **unique_fixed_point_method_not_applicable** — at least one map lacks a unique fixed point in the declared field.
- **source_fixed_points_do_not_span_ambient_space** — no source affine frame exists; the method is inconclusive.
- dimension, field and map-count mismatch statuses — the inputs do not describe comparable systems within this implementation.

## F. Scope and limitations

- Dimensions 1–3.
- A common real quadratic coefficient field \(\mathbb Q(\sqrt d)\), with positive squarefree nonsquare integer \(d\).
- Exact rational / quadratic-surd arithmetic.
- Unique fixed points and full affine span of the source fixed-point cloud are required for the frame method.
- Ordered target-frame enumeration is capped; no claim of unrestricted scalability is made.
- The map assignment uses exact candidate edges and deterministic augmenting-path matching; it does not enumerate factorial map permutations.
- General number fields, mixed-field composita, non-affine conjugacy, nonunique fixed-point families and underdetermined affine-frame recovery remain outside scope.

## G. Validation

Nine standard-library tests pass locally. They cover the Sierpiński gasket control, the 20-map Menger control with reversed map ordering, a complete negative result, a capped unresolved search, duplicate fixed-point multiplicity, dimension/map-count errors, and the two principal method-inapplicability cases.

The Phase 17 CLI example is stored in example_input.json and its reproducible output in example_summary.json. Phase 16's separate 17-test suite also passes locally. These are local phase-level checks; they are not a fresh-checkout validation or repository-wide CI claim.

## H. Relation to the Canonical Mathematical Pattern Atlas

This phase adds a structural relation that is invariant under invertible affine changes of coordinates: the conjugacy class of a finite affine-map family together with its fixed-point incidence and map correspondence. It complements the Phase 14 graph/recurrence comparators and Phase 15 generator descriptors. An exact match remains a mathematical structural equivalence; it does not establish a physical carrier, energy transfer, causal coupling or common origin.

## I. Next increments

1. Replace ordered target-frame enumeration with a more selective exact invariant-based frame candidate index for large map families.
2. Develop a principled treatment of underdetermined affine-frame families and map systems with nonunique fixed points.
3. Extend exact arithmetic to compatible higher-degree number fields and composita.
4. Generalize beyond affine IFS generators to substitution tilings, cellular automata, L-systems and nonlinear operators in the full Atlas.
5. Connect structural comparisons to measured geometries and dynamical datasets while preserving provenance, uncertainty, physical carrier and falsification requirements.
