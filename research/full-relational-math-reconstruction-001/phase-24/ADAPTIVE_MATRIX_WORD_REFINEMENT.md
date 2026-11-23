# Phase 24 — adaptive exact matrix-word refinement for affine-IFS relational graphs

## Purpose

Phase 23 stabilizes an exact directed colour partition based on six selected
pairwise traces. Some families retain large classes after that refinement.
Phase 24 extends the trace-word signature in controlled tiers, but computes
higher words only on ordered map pairs incident to still-ambiguous vertices.

This is not a complete invariant and does not replace the full graph search
or exact affine equations. The goal is to spend additional exact arithmetic
only where the current candidate correspondence is still ambiguous.

## A. Exact word catalogue

For an ordered pair (A_i,A_j), a binary word over {0,1} means that 0 is
replaced by A_i and 1 by A_j. Its invariant is

\[
\tau_w(A_i,A_j)=\operatorname{tr}(w(A_i,A_j)).
\]

Cyclic rotations are identified because trace is cyclic:
tr(XY)=tr(YX). The two generators are not swapped, and word reversal is not
assumed to preserve trace. Pure powers are omitted because the individual
characteristic polynomial already fixes their traces in the supported
dimensions. Five cyclic word classes already represented in Phase 21 are
excluded from the additional catalogue.

The default tiers contain:
- length 5: 6 new cyclic words;
- length 6: 12 new cyclic words;
- length 7: 18 new cyclic words;
- length 8: 34 new cyclic words.

The hard supported upper bound is length 12. The default stops at length 8
unless the caller explicitly changes the bound.

## B. Adaptive selection

After the current joint directed colour refinement, source vertices whose
candidate target class has size greater than one are marked ambiguous. The
target side is marked by the corresponding candidate indegrees.

For the next word tier, the engine evaluates ordered pairs (i,j) only
when at least one endpoint remains ambiguous. The same rule is applied on
the target graph. This preserves every potentially corresponding edge that
can constrain an ambiguous vertex, while avoiding extra word calculations
for pairs whose endpoints are already fixed.

The new exact trace values are appended to the existing six-word edge labels.
The vertex profiles are rebuilt, and Phase 23 refinement is rerun jointly.
Previous stable colour IDs are retained as part of the new initial colours,
so each successive candidate partition can only split, never merge.

Expansion stops when:
- every source vertex has a unique candidate target;
- no compatible colour-class bijection remains;
- the maximum configured word length is reached; or
- the next complete tier would exceed the explicit budget.

## C. Computation budget

The budget counts exact matrix multiplications. One multiplication is charged
for each letter evaluated in each matrix word. For a tier, the cost is

\[
B_{\mathrm{tier}}=
(N_s+N_t)\sum_{w\in\mathrm{tier}}|w|,
\]

where N_s,N_t are ordered source and target map-pair counts incident to
currently ambiguous vertices. A tier is atomic: it is fully applied or not
applied at all. Partial tier results are never mixed into the graph.

This is a deterministic work proxy, not a wall-clock or coefficient-bit
complexity guarantee. It can be configured through max_matrix_products;
the default is 250,000. The maximum word length defaults to 8 and cannot
exceed 12.

If the next tier does not fit, the report records the required and remaining
budget and proceeds with the last fully applied invariant set. The graph
search cap remains separately unresolved. A complete graph search followed
by exact affine equations can still establish a negative for the supplied
finite map family, regardless of whether the optional word budget was reached.

## D. Synthetic discriminating control

A three-map control uses two copies of one contracting 3×3 operator and one
other contracting operator. Every source and target linear part has the same
characteristic polynomial. The six Phase 21 word traces agree for both
ordered cross-pairs, so the initial exact graph leaves a two-vertex ambiguous
class plus a singleton.

The length-5 tier is also identical. At length 6, the word 001011 gives
-179/4096 for the source ordered pair and -175/4096 for the target.
The adaptive filter separates the class before Phase 18's affine equation
solver is entered.

This is a constructed exact-algebra control, not a claim about a measured
natural IFS, not evidence of physical common origin, and not a completeness
theorem for matrix trace invariants.

## E. Validation and limits

Six standard-library tests cover:
1. cyclic-word canonicalization and deterministic tier counts;
2. exact trace invariance under a common similarity;
3. a higher word that distinguishes a pair invisible to the Phase 21 word set;
4. atomic budget refusal;
5. selective calculation only on ambiguous-vertex incidence;
6. invalid budget and word-length handling.

The Phase 22 integration preserves all prior safeguards: one common map
bijection, both directed edge orientations, self-loops, multiplicity,
Phase 23 stable refinement, Phase 18's exact affine equations, independent
verification, and unresolved search caps.

## F. Relation to the Canonical Mathematical Pattern Atlas

Phase 24 moves from a fixed small collection of trace identities to an
adaptive noncommutative word family. It compares relations of operators at
increasing word depth, with cyclic trace equivalence treated exactly. Word
depth is an explicit analysis parameter, not a hidden constant or a claim
that an infinite trace algebra has been exhausted.
