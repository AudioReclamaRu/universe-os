# Phase 23 — adaptive directed colour refinement for affine-IFS relational graphs

## Purpose

Phase 22 retains every selected directed pairwise trace label, but begins its
search from per-vertex signatures. Those signatures forget how a vertex's
outgoing and incoming edge labels are distributed over the other vertex
classes. Phase 23 adds exact iterative partition refinement before the
Phase 22 constrained graph-isomorphism search.

This is a stronger necessary filter, not a replacement for graph search and
not a complete invariant for graph isomorphism or simultaneous similarity.

## A. Refinement rule

The initial colour of a map vertex is the exact pair

\[
c_i^{(0)}=(\chi_{A_i}(z),\;\operatorname{profile}_{21}(A_i)),
\]

where the first component is the exact characteristic polynomial and the
second is the Phase 21 sorted multiset of six-word pairwise trace records.

At round \(r+1\), the vertex receives a signature containing its prior colour
and both directed neighbourhood multisets:

\[
c_i^{(r+1)}=\left(
c_i^{(r)},
\left\{\!\left(\!\left(\mathcal L(i,j),c_j^{(r)}\right)\!\right)\!\right\}_{j},
\left\{\!\left(\!\left(\mathcal L(j,i),c_j^{(r)}\right)\!\right)\!\right\}_{j}
\right).
\]

The braces denote multisets: multiplicities are retained. Incoming and outgoing
incidences remain separate, and self-loops participate in both. Source and
target graphs are refined jointly, so equal exact signatures receive the
same colour ID in both graphs.

Refinement terminates when a round creates no new colour class. Since each
round retains the previous colour, classes can split but cannot merge; the
combined source/target partition has at most twice the number of vertices.

## B. Integration with Phase 22

Phase 22 now uses the stable Phase 23 colour classes as its candidate vertex
correspondence. Its existing backtracking still checks every directed edge
against every assigned vertex and applies residual perfect-matching checks.
Only complete relational-graph isomorphisms reach Phase 18's exact affine
equation solver and invertible-determinant witness construction.

The output records:
- candidate edges before and after refinement;
- number of refinement rounds and combined class counts;
- candidate map-index sets after refinement;
- explicit statement that stable colour refinement is necessary, not sufficient.

A colour-class mismatch is a valid negative for the supplied labelled graphs
and selected exact invariants. A search cap remains unresolved, not negative.

## C. Synthetic control

The abstract directed-graph test uses two initial vertex colours, each with
multiplicity two. Every vertex has the same outgoing and incoming multiset of
edge labels in both compared graphs. In one graph, label X joins vertices
within the same initial colour class; in the other, it joins across classes.
A row-profile-only test cannot distinguish the two. Joint directed refinement
does, because it records which neighbour colour receives each labelled edge.

This control validates the refinement rule itself. It is not presented as a
measured extra-pruning benchmark for a naturally occurring affine IFS family.
The IFS integration is separately covered by Phase 22's exact conjugacy,
reordering, negative and cap controls.

## D. Correctness boundary

- Exact initial colours and exact edge labels are compared without floating-point tolerances.
- Directed incoming and outgoing relations are never collapsed.
- Multiplicity and self-loops are retained.
- The source and target are refined jointly; colours are not independently
  numbered and then compared.
- The stable partition is only a necessary isomorphism invariant.
- A non-discrete stable partition may leave many candidate bijections.
- Full graph search and exact affine equations remain mandatory.
- Caps remain explicit unresolved outcomes.
- No physical origin, causal coupling, energy transfer or historical direction
  follows from structural affine equivalence.

## E. Tests and validation

Six standard-library tests cover:
1. neighbour-colour incidence that is invisible to simple row profiles;
2. target relabelling of an isomorphic graph;
3. direction preservation under reversed ordered-pair labels;
4. a regular control where refinement remains correctly inconclusive;
5. self-loops and multiplicity;
6. invalid graph-shape rejection.

The GitHub Actions workflow runs this package on Python 3.12 alongside Phases
16–22. Test success is reported only after the corresponding clean PR run
completes successfully.

## F. Relation to the Canonical Mathematical Pattern Atlas

Phase 23 adds equitable partition refinement / one-dimensional
Weisfeiler–Leman refinement for directed edge-labelled relational structures.
It examines how relations are arranged relative to classes of other
relations, not only the multiset of relation values incident to one object. It
is a relation-of-relations refinement and remains bounded by its exact selected
invariants.
