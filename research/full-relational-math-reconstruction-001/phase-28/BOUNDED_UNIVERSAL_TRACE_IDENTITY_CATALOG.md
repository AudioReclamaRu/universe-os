# Phase 28 — bounded universal trace-identity catalog

## Objective

Phase 28 turns Phase 27's single-instance proof into a reproducible bounded catalog. It enumerates nonempty noncommutative matrix words over a declared finite generator alphabet, selects every permitted set of d+1 distinct words, constructs the dimension-d fundamental trace identity (FTI) for each set, canonicalises the resulting trace polynomial and exactly verifies every distinct catalog entry.

No sampled matrix values are used. Every entry marked \`universally_verified_identity\` is checked by Phase 27's formal expansion in independent generic matrix entries.

## Search domain

Configuration declares:

- matrix dimension d;
- number of matrix generators;
- maximum nonempty word length;
- maximum word-catalog size;
- maximum number of substitution sets;
- maximum FTI permutation count;
- per-identity and total generic-expansion budgets.

The word vocabulary is exhaustive within its bound:

\[
\mathcal W(g,L)=\bigcup_{\ell=1}^{L}\{0,\ldots,g-1\}^{\ell},
\qquad
|\mathcal W|=\sum_{\ell=1}^{L}g^\ell.
\]

The FTI is alternating and multilinear in its d+1 arguments. Permuting one substitution set changes the generated expression only by an overall sign. Therefore Phase 28 enumerates combinations, not permutations, of d+1 distinct words. Repeated substitutions give the zero alternating expression and are excluded from the nontrivial catalog.

## Canonicalisation and deduplication

Only universally valid transformations are used:

1. cyclic rotations within each trace factor;
2. permutation of scalar trace factors in a product;
3. collection of identical trace-polynomial monomials;
4. division by the common integer coefficient gcd;
5. global sign normalisation.

Thus polynomial expressions that differ only by a nonzero rational scalar share one canonical signature. Matrix-word reversal, commutation of generators, and non-cyclic rearrangement inside a trace are never assumed.

When different substitution sets yield the same canonical trace polynomial, the entry is stored once and all substitution aliases are retained.

## Proof and budget semantics

Every unique nonzero polynomial is passed to Phase 27's exact generic-entry verifier. It expands each trace product into a sparse polynomial in independent entries of generic d × d matrices and checks every integer coefficient.

- \`universally_verified_identity\`: all generic-entry coefficients are exactly zero.
- \`identity_rejected_nonzero_generic_residual\`: a nonzero generic coefficient disproves the proposed universal relation.
- \`unresolved_*\`: a construction or verification cap was reached; no negative conclusion is drawn.

Per-identity and total expansion budgets are distinct. If the total budget is exhausted, already verified catalog entries remain certified, while the current and remaining entries are explicitly unresolved. The catalog is not marked complete.

The reported expansion count is a deterministic index-assignment work proxy, not a wall-clock or coefficient-bit-complexity bound.

## Completeness boundary

When the status is \`complete_catalog_verified\`, the search is complete for:

- the declared matrix dimension;
- the declared generator alphabet;
- all nonempty words up to the declared maximum length;
- all combinations of d+1 distinct words;
- the FTI construction and its trace-polynomial equivalence classes.

It is **not** a complete basis or generating set of all trace identities. It does not yet enumerate substitutions by arbitrary linear combinations of words, all consequences obtained by multiplication/addition of identities, identities from other trace theorems, or identities outside the declared finite word domain.

The current catalog does not feed universal reductions back into the Phase 24–26 adaptive comparison engine; integration requires a separate proof-preserving design.

## Tests

Fourteen standard-library tests cover deterministic word enumeration, noncommutative order, full bounded combination coverage, generic-matrix verification, signature normalisation, caps, paired integer configuration, repeated generators inside words and the explicit incompleteness boundary.
