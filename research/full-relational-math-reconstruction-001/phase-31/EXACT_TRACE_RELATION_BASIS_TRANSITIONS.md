# Phase 31 — exact basis transitions and predecessor intersections

## Objective

Phase 30 established the exact finite filtration

\[
R_{L,D}=\operatorname{span}_{\mathbb Q}
\{\text{bounded FTI substitutions and trace-monomial consequences}\}.
\]

Phase 31 exposes how the bases of its neighboring slices relate. It does not fit or extrapolate a numerical sequence. Instead, it constructs canonical rational bases and exact coordinate maps for every completed cell supplied by Phase 30.

## Canonical basis convention

Each trace polynomial is a sparse vector whose coordinates are canonical products of cyclic trace words. Phase 31 fixes the column order to lexicographic order of those trace-monomial tuples and reduces each finite row space to its unique reduced row-echelon form over \(\mathbb Q\).

Every pivot coefficient is exactly one, and every other pivot column is exactly zero in that row. Because reduced row-echelon form is unique for a fixed coordinate order, the reported canonical slice basis is independent of the order in which a spanning family was supplied.

This convention is local to a declared finite slice and its finite trace-monomial support. It is not an ordering of all possible trace identities.

## Inclusion transition maps

The filtration provides two natural inclusions:

\[
R_{L-1,D}\hookrightarrow R_{L,D},\qquad
R_{L,D-1}\hookrightarrow R_{L,D}.
\]

For each available predecessor, Phase 31 reports a rational matrix whose rows are canonical predecessor-basis vectors and whose columns are their coordinates in the canonical target basis. Each coordinate row is reconstructed exactly from the target basis, and the matrix rank must equal the predecessor dimension.

The associated kernel dimension is therefore zero. The cokernel dimension is the target rank minus the predecessor rank. This is an exact finite-dimensional statement for each reported inclusion.

## Exact intersection

When both immediate predecessors exist, Phase 31 solves the coefficient equation

\[
\sum_i a_i A_i=\sum_j b_j B_j
\]

over \(\mathbb Q\), where \(A_i\) and \(B_j\) are the two canonical predecessor bases. The nullspace of the combined coefficient system gives the intersection. Every resulting vector is independently reconstructed from both sides, and its coordinates in both predecessor bases are returned.

The intersection rank is checked against Phase 30's independent dimension identity:

\[
\dim(A\cap B)=\dim A+\dim B-\dim(A+B).
\]

This also tests the Phase 30 predecessor-union calculation by an independent kernel construction.

## Adapted basis and bidirectional change of coordinates

For each cell, Phase 31 forms an adapted basis by concatenating:

1. the canonical basis of the predecessor sum \(R_{L-1,D}+R_{L,D-1}\);
2. the quotient complement already selected by Phase 30.

It then computes the exact coordinate matrix from this adapted basis to the canonical basis of \(R_{L,D}\), and its rational inverse. Both matrix products are recomputed and must equal the identity exactly.

Thus every slice element can be represented in either coordinate system without numerical tolerances. The quotient complement remains a complement relative to the predecessor sum, not a set of minimal generators of the infinite T-ideal.

## Exactness and scope

- Coefficient field: \(\mathbb Q\); no floating-point arithmetic or sampled matrices are used for the transition computations.
- Canonical bases are minimum-cardinality vector-space bases of the finite slices.
- Inclusion maps, intersection coordinates, quotient complements and adapted-basis transition matrices are checked by exact reconstruction and rank identities.
- A partial or capped Phase 30 result is propagated as unresolved; Phase 31 does not silently complete a missing cell.
- The matrices describe only the declared finite \((L,D)\) grid. They do not establish an eventual recurrence, stabilization, an infinite Hilbert series, or a minimal generating set of the full infinite T-ideal.

## Tests

Twelve standard-library tests cover canonical basis ranks, order-independent RREF, injective inclusion maps, predecessor intersections, quotient dimensions, exact inverse transition matrices, boundary cells, unresolved bounds, deterministic output and input validation.
