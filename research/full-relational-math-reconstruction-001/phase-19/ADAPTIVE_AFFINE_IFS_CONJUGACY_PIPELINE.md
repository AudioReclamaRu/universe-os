# Phase 19 — adaptive affine-IFS conjugacy pipeline

## Purpose

Phases 17 and 18 solve complementary cases:

- Phase 17 is fast when every affine map has a unique fixed point and the source fixed-point cloud spans the ambient affine space. It reconstructs a coordinate transform from affine frames and assigns maps with a bipartite matching algorithm.
- Phase 18 handles consistent but underdetermined affine conjugacy systems, including coincident or lower-rank fixed-point clouds. It determines exactly whether the affine solution family contains an invertible coordinate transform.

Phase 19 combines these methods into one deterministic controller. It selects the fast frame route where applicable and falls back to the determinant-family route only when the frame assumptions fail.

## A. Routing policy

1. Run the exact Phase 17 fixed-point-frame comparator.
2. If it returns a verified conjugacy or a complete result under its applicability assumptions, accept that result.
3. If it reports **unique_fixed_point_method_not_applicable** or **source_fixed_points_do_not_span_ambient_space**, run the Phase 20 candidate partition followed by the Phase 18 exact affine-family method.
4. If Phase 17 reports a dimension, field or map-count mismatch, stop and report the mismatch.
5. If Phase 17 reaches its ordered-frame search cap, preserve the unresolved result. Do not silently start another expensive search and do not reinterpret a cap as a negative result.
6. If Phase 17 completes its frame search and finds no affine conjugacy, preserve that complete negative result under the Phase 17 assumptions.

The controller records every attempted method, the reason for switching, the final method and the final result.

## B. Why the routes are complementary

The Phase 17 route reduces the search to affine frames formed by exact fixed points. It avoids the factorial map-permutation search when those points provide a full coordinate frame.

The Phase 20 → Phase 18 fallback does not need a fixed-point frame. It first removes pairings whose linear-part characteristic polynomials differ, then solves only the surviving candidate matchings. It works directly from all operator and translation equations, parameterizes the entire affine solution family and tests the determinant polynomial for an invertible member. It is more general for degenerate fixed-point configurations but still enumerates finite map correspondences under a cap.

The controller does not treat these algorithms as interchangeable black boxes. It preserves the conditions under which each conclusion is valid.

## C. Demonstrations

The test controls exercise both routes:

- **20-map Menger IFS:** a full-rank unique-fixed-point cloud routes to Phase 17. An independent exact rational-arithmetic reproduction recovered a valid coordinate witness after 23 of 116,280 ordered target frames.
- **Two-map coincident-fixed-point IFS:** the source fixed points do not span the plane, so the controller records Phase 17's method-inapplicability status and routes to Phase 18. Phase 18 recovers an invertible witness from a two-parameter affine solution family.

The first example shows efficient frame recovery; the second shows that missing geometric frame information does not automatically mean that no affine relation exists.

## D. Search-cap and negative-result discipline

A search cap is not a mathematical negative result.

- Phase 17 frame-cap result remains unresolved and is returned without automatic fallback.
- Phase 18 permutation-cap result remains unresolved.
- A complete Phase 17 negative result is retained when the frame assumptions hold.
- A complete Phase 18 negative result is retained only after all finite map permutations are examined and every consistent affine family has an identically zero determinant polynomial.

This separation is essential for preserving the Canonical Research Principle: non-detection is interpreted relative to the exact search domain and limits.

## E. Scope and limitations

- Exact affine IFS map families in dimensions 1–3.
- Common real quadratic coefficient field, using Phase 16 exact arithmetic.
- Phase 17 requires a unique fixed point for every map and full affine span of the source fixed-point cloud.
- Phase 18 is the fallback when those fixed-point assumptions fail.
- Phase 20 reduces map correspondence using an exact characteristic-polynomial necessary invariant, but ambiguous matching families may still be factorial and capped.
- A Phase 17 target-frame cap is not automatically retried with Phase 18.
- No nonlinear conjugacy, mixed-field composita, higher-degree number fields, or physical causal interpretation is inferred.

## F. Validation

Eight standard-library routing tests are included. They cover the Menger fast path, the underdetermined fallback, a frame-search cap, a complete Phase 17 negative result, an input mismatch, a Phase 18 permutation cap and empty-payload validation.

The committed Phase 19 test module has not been executed from a clean checkout in this continuation. The routing logic has been inspected against the Phase 17 and 18 status contracts. This is not a repository-wide CI claim.

## G. Relation to the Canonical Mathematical Pattern Atlas

Phase 19 combines two complementary ways of identifying the same structural relation under coordinate change:

- geometric reconstruction from an affine frame of fixed points;
- algebraic reconstruction from a full operator-equation solution family.

This is a methodological integration inside the structural-equivalence layer. A verified match does not establish a shared natural origin, historical direction, energy transfer, or physical causal bridge.

## H. Next increments

1. **Partly advanced in Phase 20:** the Phase 18 fallback now has an exact characteristic-polynomial candidate partition and searches only compatible perfect matchings. Repeated linear-part signatures can still produce a factorial number of candidate matchings; see [Phase 20](../phase-20/CHARACTERISTIC_POLYNOMIAL_PARTITIONING_FOR_AFFINE_IFS.md).
2. Integrate the Phase 20 invariant partitions more tightly into the Phase 19 adaptive controller, while preserving its cap and negative-result policy.
3. Add exact handling of compatible coefficient-field extensions and composita.
4. Extend the adaptive controller beyond affine IFS to substitution tilings, cellular automata, L-systems and nonlinear operators.
5. Connect the structural engine to measured geometries and dynamical datasets with coordinate provenance, uncertainty and physical falsifiers.
