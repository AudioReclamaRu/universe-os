# Phase 21 — joint trace profiles for affine IFS map correspondence

## Purpose

Phase 20 compares the characteristic polynomial of each individual linear map. This is a necessary invariant under similarity, but it cannot distinguish different maps that share the same characteristic polynomial.

Phase 21 adds a relational invariant. Instead of looking at a map in isolation, it compares exact traces of products involving pairs of maps from the same family. A single common affine coordinate transformation conjugates every linear part, so traces of all such matrix words are preserved.

## A. Why the pairwise trace profile is invariant

Let source matrices \(A_i\) and target matrices \(C_{\pi(i)}\) be related by one common invertible matrix \(P\):

\[
PA_i=C_{\pi(i)}P.
\]

Then for every word \(W\) formed from selected source matrices,

\[
W(C_{\pi(i_1)},\ldots,C_{\pi(i_r)})
=
P\,W(A_{i_1},\ldots,A_{i_r})\,P^{-1}.
\]

Taking the trace gives an exact invariant:

\[
\operatorname{tr} W(C_{\pi(i_1)},\ldots,C_{\pi(i_r)})
=
\operatorname{tr} W(A_{i_1},\ldots,A_{i_r}).
\]

The same \(\pi\) must work for the whole family. Therefore, for a candidate pairing \(i\to j\), the multiset of pairwise word-trace records involving \(A_i\) and every map in the source family must equal the corresponding multiset for \(C_j\) and every map in the target family.

The multiset is sorted but not deduplicated: repeated maps remain repeated observations. This makes the per-map profile independent of map-list order while preserving multiplicity.

## B. Exact word family

For each ordered pair \((A_i,A_j)\), the implementation records six exact field elements:

\[
\begin{aligned}
&\operatorname{tr}(A_iA_j),\\
&\operatorname{tr}(A_i^2A_j),\\
&\operatorname{tr}(A_iA_j^2),\\
&\operatorname{tr}(A_iA_jA_iA_j),\\
&\operatorname{tr}(A_i^2A_j^2),\\
&\operatorname{tr}([A_i,A_j]^2),
\end{aligned}
\]

where \([A_i,A_j]=A_iA_j-A_jA_i\) is the commutator.

All matrix products and traces are calculated using exact rational/quadratic-surd arithmetic. No numerical eigenvalue, floating-point tolerance or rounded signature is involved.

These six words are a finite necessary-invariant family, not a complete invariant for simultaneous similarity. Matching profiles do not prove conjugacy.

## C. Candidate graph refinement

Phase 21 builds a bipartite graph whose source-to-target edge exists only when the two maps have identical joint pairwise trace profiles.

It then passes those candidate edges to Phase 20, which intersects them with the individual characteristic-polynomial filter. The surviving candidate matchings are tested using Phase 18's complete affine equations and exact determinant-polynomial witness construction.

The resulting chain is:

1. Phase 21 joint pairwise trace-profile filter.
2. Phase 20 individual characteristic-polynomial filter.
3. Phase 18 exact affine-family equations and invertibility witness.
4. Independent exact verification of every map equation.

Any filter may reject an impossible map pairing, but none is permitted to certify physical causation. A final positive result still requires one common invertible affine transformation satisfying every map identity.

## D. Demonstration: same individual characteristic polynomials, different family relations

The synthetic two-dimensional source contains two diagonal matrices:

\[
A_1=\begin{pmatrix}1/2&0\\0&1/3\end{pmatrix},
\qquad
A_2=\begin{pmatrix}1/3&0\\0&1/2\end{pmatrix}.
\]

They have identical individual characteristic polynomials. The target instead repeats \(A_1\) twice. Phase 20 alone therefore leaves all four source-to-target pairings as candidates.

The joint trace profiles distinguish the families: each source map has one self-relation record and one cross-relation record, while each target map has the self-relation record repeated twice. The exact relational filter reduces four characteristic-polynomial edges to zero. No full affine systems need to be solved.

This negative result is exact for the declared finite affine families and the chosen necessary-invariant family. It is not a claim about nonlinear conjugacy, omitted maps, different number fields or other physical models.

## E. Where this filter does not help

If all maps share the same linear part, as in the uniform-contraction Menger IFS, their pairwise trace profiles may all be identical. The filter correctly retains the ambiguity rather than inventing distinctions. Phase 17's fixed-point-frame method remains the efficient route for the Menger control.

More generally, joint trace profiles can be identical for non-conjugate matrix families. In that case the filter will not prune them; the complete affine equations remain decisive.

## F. Search and result semantics

- **affine_conjugacy_verified** — a candidate survived both invariant filters, an invertible affine witness was constructed, and all map equations were verified.
- **no_affine_conjugacy_found** — the refined candidate graph has no perfect matching, or every surviving candidate matching was exhausted without an invertible witness.
- **candidate_matching_search_limit_reached** — the candidate matching cap was reached; the result is unresolved, not negative.
- dimension, coefficient-field and map-count mismatch statuses — the supplied families are not comparable within this implementation.

A zero-edge relational graph is a complete negative result only for the stated finite family and necessary-invariant assumptions. A cap is never a negative result.

## G. Scope and limitations

- Dimensions 1–3.
- Exact rational / common real-quadratic field arithmetic inherited from Phases 16 and 20.
- Six selected pairwise matrix-word traces.
- Per-map multisets preserve multiplicity and remove dependence on map-list order.
- These finite trace profiles are necessary, not sufficient, invariants for simultaneous similarity.
- Candidate matching search remains capped when profiles and characteristic polynomials leave ambiguity.
- Higher-degree fields, longer word families, full trace algebras, nonlinear conjugacy and physical causal identification remain outside scope.

## H. Validation

Seven standard-library tests are included. They cover pruning of equal-characteristic-polynomial but relationally incompatible families, preservation of a valid translated affine family with identical linear parts, map-order invariance, multiplicity preservation, capped ambiguous matching search, complete negative search and payload validation.

All seven Phase 21 tests passed in the clean GitHub Actions pull-request checkout, workflow run [45243433007](https://github.com/AudioReclamaRu/universe-os/actions/runs/45243433007), using Python 3.12. This confirms the Phase 21 test module from a clean checkout; no repository-wide CI pass is claimed.

## I. Relation to the Canonical Mathematical Pattern Atlas

Phase 21 moves from individual operator invariants to relations among operators. The same common transformation must preserve both each map's internal spectrum and its relational trace profile against the rest of the family. This is a concrete relation-of-relations test.

It remains mathematical structural filtering. It does not identify a natural source, carrier, receiver, propagation path, energy transfer, common history or causal coupling.

## J. Next increments

1. Expand the word family adaptively when low-order profiles leave large candidate classes, with an explicit complexity budget and no false-negative claims from truncation.
2. Compare higher-order cyclic trace words and generated matrix-algebra invariants.
3. Integrate relational profiles with fixed-point frames before enumerating any residual matching.
4. Extend exact field arithmetic and apply the structural engine to measured geometries and dynamics with provenance, uncertainty and physical falsifiers.
