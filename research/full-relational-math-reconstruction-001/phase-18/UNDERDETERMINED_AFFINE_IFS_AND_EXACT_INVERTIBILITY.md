# Phase 18 — exact invertible witnesses inside underdetermined affine families

## Purpose

Phases 16–17 identified affine coordinate equivalence between finite iterated-function systems (IFS) of affine maps. They also exposed an important class of inputs that cannot be closed by a fixed-point frame alone: every map may have the same fixed point, or the fixed-point cloud may occupy a lower-dimensional affine subspace.

The corresponding equations for an affine coordinate change are still linear in the unknown matrix and translation. A consistent system may have infinitely many solutions. The decisive question is not whether the solution is unique, but whether **at least one solution has a nonzero determinant**.

Phase 18 answers that question exactly for dimensions one through three over a common real quadratic field.

## A. The affine solution family

For a proposed map correspondence \(\pi\), let

\[
F_i(x)=A_i x+b_i,\qquad G_{\pi(i)}(y)=C_{\pi(i)}y+d_{\pi(i)},
\]

and seek an affine coordinate map

\[
H(x)=Px+t.
\]

The conjugacy equations are

\[
PA_i=C_{\pi(i)}P,
\]

\[
Pb_i+t=C_{\pi(i)}t+d_{\pi(i)}.
\]

These are linear equations in the \(n^2+n\) entries of \((P,t)\). Exact reduced-row-echelon elimination returns either an inconsistent system or an affine family

\[
x=x_0+\lambda_1v_1+\cdots+\lambda_kv_k,
\]

where \(x\) contains all entries of \(P\) and \(t\), and the \(\lambda_j\) are free parameters in the declared field.

A unique solution is only the special case \(k=0\). A consistent family must not be discarded merely because \(k>0\).

## B. Determinant polynomial

Substitute the affine family into the matrix entries of \(P\). The determinant becomes an exact multivariate polynomial

\[
D(\lambda_1,\ldots,\lambda_k)
=\det P(\lambda_1,\ldots,\lambda_k).
\]

The algorithm expands this polynomial over the exact coefficient field. No floating-point tolerance or numerical determinant threshold is used.

There are exactly two mathematical cases:

- If \(D\) is the zero polynomial, every solution in that affine family is singular. That map correspondence cannot represent an invertible coordinate change.
- If \(D\) is not the zero polynomial, an invertible member of the family exists over the infinite field. Phase 18 constructs one explicitly.

This is stronger than testing a few arbitrary parameter choices and then guessing that no invertible choice exists.

## C. Deterministic nonzero specialization

Because every entry of \(P(\lambda)\) is affine-linear in the free parameters, its determinant has degree at most \(n\) in each individual parameter.

For any nonzero polynomial of degree at most \(n\) in one variable over a characteristic-zero field, it cannot vanish at \(n+1\) distinct field elements unless it is the zero polynomial. Phase 18 therefore specializes one parameter at a time using the exact finite set

\[
\{0,1,\ldots,n\}.
\]

At each step it chooses the first value for which the remaining polynomial is still nonzero. It then proceeds to the next parameter. After all parameters are fixed, the resulting scalar determinant is exactly nonzero.

The procedure uses at most \(k(n+1)\) polynomial specializations, rather than the full \((n+1)^k\) Cartesian grid. It is deterministic and produces a reproducible witness. The returned matrix is then checked again with the exact determinant routine, and every original affine map equation is independently verified.

## D. Demonstration: a fixed-point cloud with no coordinate frame

The synthetic control uses two maps in two dimensions. Both source maps fix the origin, so the source fixed-point cloud contains only one point and cannot span the plane. The target maps share a translated fixed point. Phase 17's fixed-point-frame method is therefore inapplicable.

The pair is nevertheless related by an invertible affine coordinate change. The linear conjugacy equations leave two free parameters. Phase 18 obtains a nonzero determinant polynomial, selects the exact parameter assignment \((1,1)\), recovers an invertible matrix and translation, and verifies both maps.

This control demonstrates why an underdetermined system is not a failed reconstruction. The missing coordinate frame can be supplied by the full operator relations.

## E. Search and result semantics

Phase 18 still enumerates finite map correspondences, up to a configurable cap (100,000 by default). It reports:

- **affine_conjugacy_verified** — an invertible exact witness was constructed and every map equation was verified.
- **no_affine_conjugacy_found** — every map permutation was examined, and every consistent affine solution family had identically zero determinant polynomial.
- **permutation_search_limit_reached** — the permutation cap stopped the search; the result is unresolved, not negative.
- dimension, coefficient-field and map-count mismatches — the inputs do not describe comparable systems under this implementation.

A negative result is limited to the stated finite affine-map families, common coefficient field, and tested map correspondence class. It does not exclude nonlinear conjugacy, an unmodelled map, a different physical carrier, or another reconstruction family.

## F. Scope and limitations

- Dimensions 1–3.
- Exact rational and quadratic-surd arithmetic in a common real field \(\mathbb Q(\sqrt d)\), with positive squarefree nonsquare integer \(d\).
- Exact symbolic determinant polynomials with degree at most the ambient dimension in each free parameter.
- Deterministic nonzero specialization over \(\{0,\ldots,n\}\).
- Map correspondences are enumerated; large map families remain subject to the permutation cap. Phase 17 remains the preferred route when unique fixed points span the ambient affine space.
- Non-affine conjugacy, mixed coefficient fields, higher-degree number fields, and general nonlinear generator families remain outside scope.

## G. Validation

Six standard-library tests are included. They cover an underdetermined two-dimensional family with coincident fixed points, a one-dimensional free scaling, an identically-zero determinant family, a capped unresolved permutation search, a conjugate affine-map pair, and empty-payload validation.

The synthetic input and exact expected output are stored as example_input.json and example_summary.json. Local prototype checks exercise the algebraic cases, but this phase is not represented as a fresh-checkout validation or repository-wide CI result.

## H. Relation to the Canonical Mathematical Pattern Atlas

Phase 18 separates two properties that must not be confused:

1. the linear space of all transformations satisfying the operator relations;
2. the subset of that space consisting of invertible coordinate transformations.

The determinant polynomial is the exact bridge between them. The result adds a feasibility method to the Atlas's structural-equivalence layer; it does not establish a shared physical origin, source/receiver path, energy transfer, or causal coupling.

## I. Next increments

1. Combine the Phase 17 fixed-point-frame search and Phase 18 determinant-family solver into one adaptive comparator with explicit method selection and provenance.
2. Replace factorial map-permutation enumeration for underdetermined families with invariant-based candidate partitions and exact assignment search.
3. Extend exact arithmetic to compatible higher-degree number fields and composita.
4. Generalize from affine IFS maps to substitution tilings, cellular automata, L-systems and nonlinear operators.
5. Apply the combined structural tests to measured natural-system data, retaining coordinate provenance, uncertainty and physical falsifiers.
