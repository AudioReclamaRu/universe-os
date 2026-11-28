# Phase 25 — exact algebraic dependency detection for matrix-word traces

## Purpose

Phase 24 adds exact higher-word traces when a map correspondence remains
ambiguous. Phase 25 introduces exact feature-dependency reduction before those
new labels enter the relational graph.

Two logically different reductions are kept separate.

1. **Universal trace identity.** The Phase 21 commutator-square trace is
   exactly dependent on two existing binary-word traces:
   \[
   \operatorname{tr}([A,B]^2)
   =2\operatorname{tr}(ABAB)-2\operatorname{tr}(A^2B^2).
   \]
   Phase 25 checks this identity exactly on every supplied Phase 21 edge and
   removes the redundant sixth coordinate before refinement. This is an
   algebraic identity for square matrices, not a sample-based inference.

2. **Finite-comparison dependency.** On the active ordered-pair rows from
   both the source and target families, Phase 25 tests whether a new trace
   feature is an exact linear combination of already retained trace features.
   The same coefficients must work on every source and target sample row.
   A dependent candidate is not appended to the edge label. The relation is
   reported with exact coefficients.

The second result is deliberately not promoted to a universal identity. It
holds only for this concrete finite comparison and its currently ambiguous
ordered-pair support.

## A. Exact row-space algorithm

Each trace feature is a column vector over the common field \(Q(\sqrt d)\).
The source active-pair rows are concatenated with the target active-pair rows.
An incremental exact row-echelon basis is built using rational/quadratic
field arithmetic inherited from Phase 16.

For each candidate word \(w\), Phase 24 evaluates
\(\operatorname{tr}(w(A_i,A_j))\) on both active supports. Phase 25 reduces
that exact feature vector against the retained basis.

- Zero residual: the candidate is exactly dependent. Phase 25 records an
  equation \(f_w+\sum_k c_k f_k=0\) with exact field coefficients and omits
  the feature from the graph edge label.
- Nonzero residual: the candidate is independent on the current support,
  becomes a retained feature and is appended to the relevant edge labels.

A shared relation over the combined source/target support is safe for the
present comparison: whenever a candidate source/target edge pair matches in
all retained features, it must also match in the omitted dependent feature.
No coefficients are fitted independently to the two systems.

## B. Active-pair support

At a given refinement round, a source or target vertex is active when its
current candidate class is non-singleton. The sample support contains every
ordered pair with at least one active endpoint. Phase 24's active vertex sets
can only shrink after stable colour refinement. Therefore later supports are
subsets of earlier supports, and previously computed trace values remain
available for the exact dependency basis.

If a required prior value is missing, the implementation raises an explicit
error rather than extrapolating or filling an unknown with zero.

## C. Budget semantics

Candidate trace evaluation is still charged at the Phase 24 matrix-product
rate. The dependency test does not pretend that an unknown trace can be
classified without evaluating it. The practical gains are exact feature
compression, fewer retained edge-label coordinates and fewer redundant
constraints in later relational refinements.

The complete candidate tier remains atomic under the matrix-product budget:
if its full exact evaluation cost exceeds the remaining allowance, no word
from the tier is calculated or appended. The report distinguishes evaluated,
retained and dependent words.

## D. Correctness boundary

- All coefficients and equality checks are exact in the declared quadratic field.
- A dependency is tested on both source and target supports with one shared
  coefficient vector.
- Universal identities and finite-comparison relations are reported separately.
- Dependence on the current support is not extrapolated to omitted matrix pairs,
  other IFS families or arbitrary matrices.
- Dependent features are omitted only from the current graph comparison's
  corresponding active edge labels.
- A missing prior value is an error, never zero.
- Word-product and graph-search caps retain distinct unresolved semantics.
- Full directed graph matching and Phase 18's affine equations remain decisive.

## E. Validation

Six standard-library tests cover the universal commutator identity, exact
identity checking, exact field-coefficient recovery, explicitly local
dependency semantics, independent feature retention and field validation.
Phase 24's integration tests additionally verify higher-word pruning and the
atomic evaluation budget.

## F. Phase 26 polynomial extension

Phase 26 extends this exact linear feature-space test with bounded-degree
polynomial monomials of previously retained trace features. Its output is a
separate finite-support relation type with explicit monomial factors, exact
coefficients and row-by-row verification. It does not change the meaning of
the Phase 25 linear relations or the universal commutator identity.

See [EXACT_POLYNOMIAL_TRACE_DEPENDENCIES.md](../phase-26/EXACT_POLYNOMIAL_TRACE_DEPENDENCIES.md).
Only a fully verified polynomial relation on the combined source/target
support is eligible for omission; sample-span saturation and configured caps
remain unresolved.

## G. Relation to the Canonical Mathematical Pattern Atlas

Phase 25 adds an exact relation-space layer: the question is no longer only
whether two operators share a trace value, but whether one relation-feature
column is generated by the others over a specified finite comparison domain.
The domain, coefficient field and exact relation are part of the result.
