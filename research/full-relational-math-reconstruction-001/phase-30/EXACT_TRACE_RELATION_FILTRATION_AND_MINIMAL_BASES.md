# Phase 30 — exact filtration, quotient increments and bounded minimal bases

## Objective

Phase 30 studies how the finite exact relation spaces from Phase 29 grow as two independent bounds increase:

- L: maximum length of each matrix word substituted into the fundamental trace identity;
- D: maximum total matrix-letter degree of a trace-monomial multiplier.

The maximum length of an individual trace word used in multipliers is fixed across a run. This produces a nested two-parameter family:

\[
R_{L,D}\subseteq R_{L+1,D},\qquad
R_{L,D}\subseteq R_{L,D+1}.
\]

For every grid cell, Phase 30 computes the exact Q-dimension, a homogeneous total-word-degree profile, the union of the immediate predecessor spaces, and a basis for the quotient:

\[
Q_{L,D}
=
R_{L,D}\big/
\left(R_{L-1,D}+R_{L,D-1}\right).
\]

The complement directions are selected from Phase 29's exact basis, then tested against an exact echelon basis of the predecessor union. Every dependency certificate is recomputed over Q and must leave a zero sparse trace-polynomial residual.

## What "minimal" means in this phase

There are three distinct notions and they must not be conflated:

1. **Minimal cardinality basis of one finite vector space.** If the exact rank of \(R_{L,D}\) is r, every Q-basis has exactly r elements. Phase 29 supplies such a basis, and Phase 30 checks its size against the reported rank.
2. **Minimal quotient complement at one filtration cell.** The number of new directions is exactly \(\dim R_{L,D}-\dim(R_{L-1,D}+R_{L,D-1})\). The selected complement vectors are independent modulo the predecessor sum and span the quotient.
3. **Minimal generators of the infinite T-ideal.** This is **not** established. Finite vector-space elimination does not prove ideal-module or T-ideal generator minimality.

The predecessor intersection dimension is computed from

\[
\dim(A\cap B)=\dim A+\dim B-\dim(A+B),
\]

where \(A=R_{L-1,D}\) and \(B=R_{L,D-1}\).

## Graded structure

Each FTI substitution on fixed words is homogeneous in total matrix-letter degree. Multiplication by a trace monomial adds its total word degree. The Phase 30 basis therefore carries an exact profile by total trace-word degree.

The output reports, per cell:

- \(\dim R_{L,D}\);
- \(\dim(R_{L-1,D}+R_{L,D-1})\);
- the quotient dimension;
- the exact intersection dimension of the predecessor spaces;
- current, predecessor-union and quotient ranks by total word degree;
- a complete minimal Q-basis for the cell;
- exact rational certificates for predecessor overlaps and for current basis vectors already in the predecessor union.

The profile is a finite Hilbert-like table for this bounded construction, not an infinite Hilbert series.

## Growth across bounds and structural caution

The grid makes word-length and multiplier-degree effects separable. It can show which new independent trace relations first appear when L or D is increased and how much the two predecessor subspaces overlap.

The final word-length rank increment is reported as an observation over the last searched step only. Repeated increments over a short finite range are not a proof of eventual stabilization, a polynomial Hilbert function, a recurrence, or a presentation of the infinite ideal.

## Budgets and conservative semantics

Distinct limits control:
- number of filtration cells;
- Phase 28 seed expansion work, both per cell and in aggregate;
- Phase 29 derived-relation expansion work, per relation, per cell and in aggregate;
- word catalogs, substitution multisets, multiplier monomials and derived relations;
- emitted exact dependency-certificate count.

If any cell cannot be completed, the overall status is partial/unresolved. Previously completed cells remain available, but no complete filtration claim is made. A cap is never interpreted as a negative mathematical result.

Work counters are deterministic generic-index-assignment proxies, not wall-clock or coefficient-bit complexity.

## Scope

Phase 30 proves finite-dimensional linear-algebra statements for the explicitly declared R[L,D] construction over Q, whose members have already been independently verified as universal matrix trace identities by Phase 27.

It does not:
- prove a minimal generating set for the infinite T-ideal;
- prove stabilization beyond the searched grid;
- claim a complete infinite Hilbert series or graded presentation;
- infer a physical matrix algebra or mechanism from any archaeological object.

## Tests

Thirteen standard-library tests cover nested ranks, quotient dimension identities, degree-profile accounting, minimal basis cardinality, exact dependency certificates, both filtration directions, conservative final-step diagnostics, budget caps, deterministic output and input validation.
