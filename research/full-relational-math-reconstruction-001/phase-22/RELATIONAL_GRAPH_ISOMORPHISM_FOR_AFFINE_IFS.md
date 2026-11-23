# Phase 22 — exact relational graph isomorphism for simultaneous IFS conjugacy

## Purpose

Phase 21 builds a per-map relational profile: a sorted multiset of pairwise word traces between one map and every map in its family. This is stronger than a list of isolated matrix spectra, but it forgets which other map produced each record.

Phase 22 retains that incidence information. It treats an affine IFS as a finite directed, edge-labelled relational graph:

- each map is a vertex;
- each vertex has an exact colour formed from its characteristic polynomial and its Phase 21 relational profile;
- each ordered pair of maps carries the exact six-word trace record for that ordered pair.

One simultaneous conjugacy must preserve every vertex colour and every directed edge label under the same map permutation.

## A. The relational graph

For an ordered pair \((A_i,A_j)\), the directed edge label is

\[
\mathcal L(i,j)=
\left(
\begin{array}{c}
\operatorname{tr}(A_iA_j),\
\operatorname{tr}(A_i^2A_j),\
\operatorname{tr}(A_iA_j^2),\\
\operatorname{tr}(A_iA_jA_iA_j),\
\operatorname{tr}(A_i^2A_j^2),\
\operatorname{tr}([A_i,A_j]^2)
\end{array}
\right).
\]

The implementation retains orientation: \(\mathcal L(i,j)\) and \(\mathcal L(j,i)\) are both checked. Self-pairs \(\mathcal L(i,i)\) are checked as loops. Repeated maps remain distinct vertices, so multiplicity is preserved.

For a common simultaneous conjugacy

\[
PA_i=C_{\pi(i)}P,
\]

every matrix word transforms by the same similarity \(PWP^{-1}\). Therefore each exact trace is preserved:

\[
\mathcal L(i,j)=\widetilde{\mathcal L}(\pi(i),\pi(j)).
\]

This is a necessary condition for one map permutation and one common transformation.

## B. Exact constrained graph search

Phase 22 builds a candidate vertex correspondence using the exact characteristic polynomial and Phase 21's per-map trace profile. It then performs deterministic backtracking with relational consistency constraints:

1. Select an unmapped source vertex with the fewest currently compatible target vertices.
2. Test each candidate against every already assigned vertex in both directed orientations and against its self-loop.
3. Run a residual bipartite perfect-matching feasibility check before continuing deeper.
4. At each complete relational graph isomorphism, solve Phase 18's exact affine equations for that one map permutation.
5. Construct a nonzero-determinant witness if the affine solution family contains an invertible member, then independently verify every original affine equation.

This preserves the distinction between three layers: candidate graph correspondence, exact affine feasibility, and final witness verification. A graph isomorphism alone is not reported as affine conjugacy.

## C. Demonstration: retaining which relation belongs to which pair

The two-map source control uses

\[
A_1=\operatorname{diag}(1/2,1/3),\qquad
A_2=\operatorname{diag}(1/3,1/2).
\]

The target repeats \(A_1\) twice. The individual characteristic polynomials of \(A_1\) and \(A_2\) are identical, so Phase 20 alone permits all four vertex pairings. Phase 21's per-map profile filter may already reject this particular pair because the source and target row multisets differ; this example therefore does not claim an additional performance gain over Phase 21.

Phase 22 nevertheless represents the full directed incidence structure explicitly and checks whether any one bijection preserves every ordered pair label. It finds no compatible vertex bijection and rejects the supplied finite families before constructing any affine equation system. The control validates the whole-graph constraint and its negative-result semantics; a separate benchmark would be needed to quantify extra pruning over Phase 21 on families whose vertex profiles already match.

This is an exact negative result within the stated map family and selected relational invariant. It is not a claim about nonlinear conjugacies, omitted maps, different number fields or other physical models.

## D. Positive and negative controls

The test package also includes:
- exact recovery of a common affine transformation for a translated one-dimensional IFS;
- correct map correspondence after target map-list reversal;
- a three-map Sierpiński-gasket coordinate change with exact affine witness verification;
- a complete negative result after all relational graph isomorphisms are examined;
- an explicit graph-search cap that returns unresolved rather than negative.

Uniform-contraction families such as the Menger IFS may have identical vertex and edge labels for many map permutations. Phase 22 does not pretend otherwise. The Phase 17 fixed-point-frame route remains preferable where its full-span assumptions apply.

## E. Search limits and status semantics

- **affine_conjugacy_verified** — an exact relational graph isomorphism yielded an invertible affine witness, and all affine map equations were independently verified.
- **no_affine_conjugacy_found** — the relational graph has no compatible bijection, or all compatible graph isomorphisms were examined and none admits an invertible affine witness.
- **relational_graph_search_limit_reached** — the graph-node or candidate-isomorphism budget was exhausted; the result is unresolved, not negative.
- dimension, coefficient-field and map-count mismatch statuses — inputs are not comparable in the declared implementation.

The caps apply to graph search and candidate isomorphisms. They do not authorize an inference about map structures outside the supplied finite family.

## F. Scope and limitations

- Dimensions 1–3.
- Exact rational / common real-quadratic field arithmetic inherited from Phases 16 and 18.
- Exact characteristic polynomials, the six Phase 21 directed pairwise trace words, Phase 23 directed colour refinement, and Phase 24 adaptive binary matrix-word traces.
- Deterministic constrained backtracking with residual perfect-matching feasibility checks.
- Search is bounded by graph-node and complete-isomorphism caps; optional word expansion has a separate matrix-product budget and maximum word length.
- These selected vertex/edge labels are necessary, not complete invariants for simultaneous similarity.
- Full affine operator equations and determinant feasibility remain decisive.
- Higher-degree number fields, longer word algebras, nonlinear conjugacy and physical causal identification remain outside scope.

## G. Validation

Nine standard-library tests are included. They cover exact common-transform recovery, target map-order reversal, relational rejection when isolated vertex spectra are insufficient, complete negative search, graph-search cap semantics, a three-map gasket control, payload validation, Phase 24 higher-word pruning and atomic word-budget behaviour.

Phase 22 is run together with Phase 24 in the dedicated Python 3.12 workflow matrix. The current implementation's clean-checkout validation is recorded in the root research README after the final nine-phase CI run completes.

## H. Relation to the Canonical Mathematical Pattern Atlas

Phase 22 moves from map-wise relational profiles to a whole-family labelled relational object. It preserves not only which numerical relations exist, but which ordered pair of operators carries each relation. This is a further relation-of-relations representation.

It remains a mathematical structural filter. A verified affine conjugacy does not identify a natural source, propagation carrier, receiver, common history, energy transfer or causal physical bridge.

## I. Phase 23 integration

The Phase 23 directed colour-refinement module is now applied before Phase 22 backtracking. It begins from the exact characteristic-polynomial / Phase 21 profile colours and repeatedly refines them with separate incoming and outgoing multisets of (exact edge label, neighbour colour). Source and target are refined jointly.

The result includes the refinement round count, combined class-count sequence and candidate-edge counts before and after refinement. A stable colour mismatch is a valid negative for these selected graph invariants; a non-discrete stable partition is not a positive result. Phase 22 still performs full directed-edge graph search, and Phase 18 still verifies the complete affine equations.

Six Phase 23 unit tests exercise the refinement engine itself. They do not claim an additional measured pruning gain on an affine-IFS dataset. See [ADAPTIVE_DIRECTED_COLOUR_REFINEMENT.md](../phase-23/ADAPTIVE_DIRECTED_COLOUR_REFINEMENT.md).

## J. Phase 24 adaptive word integration

Before Phase 22 graph backtracking, Phase 24 evaluates additional exact traces of
two-generator matrix words, beginning at length 5 and extending by complete
length tiers. It computes these traces only on ordered pairs incident to
vertices that remain ambiguous after the current joint colour refinement.
Cyclic rotations are deduplicated; generator order is retained.

After each tier, the extended edge labels feed back into a new joint Phase 23
directed refinement. Prior stable colours are retained, so candidate classes
can only split. The tier is atomic under a separate exact matrix-product
budget; no partial tier labels are allowed. The report contains every applied
or budget-skipped tier, its word list, ambiguous vertices, ordered-pair count,
candidate-edge reduction and budget accounting.

A six-test Phase 24 package tests exact trace invariance, a concrete length-six
discriminator, selective ambiguity-driven calculation and atomic budget
handling. The Phase 22 package now also tests the integrated discriminator and
the case where the optional trace budget is exhausted but the exact affine
solver still determines the finite-family result.

## K. Next increments

1. Extend the trace-word search with algebraic dependency detection and exact
   reduction of words before spending further matrix-product budget.
2. Combine fixed-point frame constraints with edge-labelled graph search
   before residual map assignment.
3. Extend exact fields and connect verified structural candidates to measured
   natural-system data with provenance, uncertainty and falsifiable mechanisms.
