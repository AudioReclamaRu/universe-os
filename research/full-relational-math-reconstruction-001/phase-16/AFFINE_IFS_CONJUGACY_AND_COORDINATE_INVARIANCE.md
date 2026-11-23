# Phase 16 — affine conjugacy and coordinate invariance of IFS generators

## Purpose

Phase 15 compared finite affine IFS generators only when their exact map descriptions were written in the same declared coordinate system. That is too restrictive for a relation-first programme: one geometric generator can be expressed in different coordinate charts, with different origins, basis vectors, orientations or affine units.

Phase 16 asks a sharper structural question:

> Are two finite affine map families genuinely different, or are they the same generator written in different affine coordinates?

It adds an exact affine-conjugacy comparator. It is designed to identify a mathematical relation that survives a change of coordinates, not to infer a physical mechanism from a visual resemblance.

## A. Mathematical definition

Let the source IFS contain affine maps

\[
F_i(x)=A_i x+b_i,
\]

and the target IFS contain

\[
G_j(y)=C_j y+d_j.
\]

The comparator searches for an invertible affine coordinate transformation

\[
H(x)=Px+t,\qquad \det P\ne0,
\]

and a permutation \(\pi\) of the finite map list such that

\[
H\circ F_i=G_{\pi(i)}\circ H
\]

for every map in the source family.

For a fixed permutation, this is equivalent to the exact equations

\[
PA_i=C_{\pi(i)}P,
\]

\[
Pb_i+t=C_{\pi(i)}t+d_{\pi(i)}.
\]

These equations are linear in the unknown entries of \(P\) and \(t\). The implementation constructs the complete rational/quadratic-field linear system, solves it by exact Gaussian elimination and then independently verifies every map equation. It accepts a solution only when the determinant of \(P\) is exactly nonzero.

The map list is treated as a finite multiset: source order and target order need not match. The returned permutation is zero-based and uses the paired binary/ternary notation for integer indices.

## B. Exact coefficient domain

The comparator supports dimensions one through three and exact coefficients in a common real quadratic field

\[
\mathbb Q(\sqrt d),
\]

where \(d\) is a positive, squarefree, nonsquare integer. Rational values are the special case with zero radical coefficient. A field element is represented exactly as

\[
a+b\sqrt d,\qquad a,b\in\mathbb Q.
\]

Addition, subtraction, multiplication, division, matrix inversion, determinants and Gaussian elimination remain exact. Decimal floating-point approximations are not used in the conjugacy decision.

Both IFS inputs must use the same declared quadratic field. A comparison across different fields, such as \(\mathbb Q(\sqrt2)\) and \(\mathbb Q(\sqrt3)\), is not silently coerced into a larger compositum; it is reported as a field mismatch and remains future work. General number fields of degree three or higher are also outside this phase.

## C. Search outcomes and epistemic safeguards

The implementation distinguishes the following results:

- `affine_conjugacy_verified`: an exact, invertible transformation and map permutation were found, and every map equation was rechecked.
- `no_affine_conjugacy_found`: every permutation in the finite search was examined and no invertible affine conjugacy was found.
- `affine_solution_underdetermined`: at least one permutation gives a consistent but underdetermined linear system. An invertible member of that solution family may exist; the program does not choose one without an additional criterion.
- `only_singular_affine_solutions_found`: the unique solutions found are singular and therefore cannot be coordinate transformations.
- `permutation_search_limit_reached`: the factorial map-permutation search was capped before exhaustion. This is unresolved, not a negative result.

The default cap is 100,000 permutations. For example, eight maps have 40,320 permutations and fit within the default cap; nine maps have 362,880 permutations and may not. Large systems such as the 20-map Menger generator are therefore not exhaustively searched by the default brute-force permutation strategy. A capped search can still return a positive result if it finds and verifies a conjugacy, but it cannot return a global negative result.

A consistent underdetermined system is not falsely reported as a verified transformation. Conversely, a search limit is not falsely reported as evidence that no transformation exists. These distinctions are part of the result schema, not informal caveats.

## D. Coordinate-change constructor

`apply_affine_coordinate_change(...)` is provided as an exact helper for building controlled test cases and converting a known IFS into another affine coordinate frame. It applies

\[
A'_i=PA_iP^{-1},\qquad
b'_i=Pb_i+t-A'_it.
\]

The constructor rejects a singular \(P\), invalid dimensions and incompatible field coefficients. It does not claim that the chosen coordinate transform is historically or physically meaningful; that must come from external survey or model provenance.

## E. Reproducible synthetic demonstration

The example starts with the three-map Sierpiński-gasket IFS in a two-coordinate barycentric representation and constructs a second description using the exact synthetic transform

\[
P=\begin{pmatrix}2&1\\1&2\end{pmatrix},\qquad
 t=\begin{pmatrix}3\\-1\end{pmatrix},\qquad
\det P=3.
\]

The comparator recovers that transformation exactly and verifies all three map identities. The matrices and translations are exact rational values; the output integers use paired binary/ternary notation. The example is a software control, not an independent empirical discovery and not a claim that any natural object was generated by the Sierpinski IFS.


## F. Interpretation

A verified affine conjugacy means that the two finite affine map families are the same mathematical generator under an invertible affine coordinate change and a relabelling of maps. It prevents a coordinate choice from being mistaken for a structural difference.

When both systems are contractive IFSs, their attractors are carried into one another by the same affine map. This phase does not itself test contractivity, separation conditions, attractor dimensions, Hausdorff measures or physical realizability. It also does not establish a common historical origin, material mechanism, energy transfer, causal coupling or natural implementation.

The result belongs to the **structural-equivalence** layer of the Canonical Mathematical Pattern Atlas. Empirical identification still requires measured source data, coordinate provenance, uncertainty, independent controls, and a test that distinguishes competing models.

## G. Validation

The standard-library implementation is `affine_ifs_conjugacy.py`; its unit tests are `test_affine_ifs_conjugacy.py`.

Seventeen local tests pass. They cover:

- exact recovery of an affine transformation across distinct coordinate-system labels;
- map-order independence;
- exact quadratic-surd arithmetic in \(\mathbb Q(\sqrt3)\);
- underdetermined systems;
- complete negative search versus capped unresolved search;
- dimension, field and map-count mismatches;
- singular and malformed coordinate changes;
- squarefree-field validation and paired binary/ternary input parsing.

The synthetic CLI example also runs and emits `example_summary.json`. This is local verification of the Phase 16 implementation only. It is not a fresh-checkout validation of the whole repository and is not a repository CI claim.

## H. Remaining work

1. Replace factorial permutation enumeration with invariant-based candidate partitioning and a scalable assignment/backtracking strategy, especially for the 20-map Menger generator.
2. Solve underdetermined affine families with exact determinant-nonzero feasibility, rather than stopping at the underdetermined status.
3. Support affine and similarity conjugacy across different but compatible number fields, including composita.
4. Generalize from quadratic fields to exact algebraic number fields of higher degree.
5. Extend generator equivalence beyond affine IFS to substitutions, tilings, cellular automata, L-systems and nonlinear operators in the full Atlas.
6. Connect these exact structural tests to measured natural-system data without collapsing geometric equivalence into physical causation.
