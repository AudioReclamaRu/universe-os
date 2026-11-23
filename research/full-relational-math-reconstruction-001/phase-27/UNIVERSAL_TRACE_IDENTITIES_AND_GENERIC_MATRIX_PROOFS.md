# Phase 27 — universal trace identities and exact generic-matrix proofs

## Objective

Phase 27 moves beyond Phase 26's relations on finite source/target samples. It constructs a universal trace identity for an arbitrary fixed matrix dimension, substitutes noncommutative matrix words, and verifies the resulting polynomial identity by exact symbolic expansion in independent matrix entries.

A successful Phase 27 certificate is not an interpolation result: no sampled matrices, measured values, or finite comparison rows are used.

## Fundamental trace identity

For square matrices of size d, the fundamental trace identity (FTI) uses d+1 arbitrary matrices X_0, ..., X_d:

\[
\sum_{\sigma\in S_{d+1}}\operatorname{sgn}(\sigma)
\prod_{c=(i_1\,\ldots\,i_k)\in\operatorname{Cycles}(\sigma)}
\operatorname{tr}(X_{i_1}\cdots X_{i_k})=0.
\]

Each X_i may itself be replaced by a noncommutative word in arbitrary generator matrices M_0, ..., M_(r-1). Phase 27 performs that substitution before canonicalising trace products.

Canonicalisation uses only facts valid for arbitrary square matrices:

- tr(UV) = tr(VU), so cyclic rotations of a trace word are identical;
- scalar trace factors commute, so their order in a product is irrelevant;
- word reversal is **not** assumed, and matrix generators are never commuted.

The coefficient field is assumed commutative and of characteristic zero. Paired binary/ternary integer notation is used in machine-readable report fields.

## Exact generic-entry verification

For a declared dimension d, every generator is represented by a generic matrix

\[
M_a=(x_{aij})_{0\leq i,j<d},
\]

where all x_(aij) are independent commuting indeterminates. Each trace word is expanded using

\[
\operatorname{tr}(M_{a_1}\cdots M_{a_\ell})
=\sum_{i_1,\ldots,i_\ell=0}^{d-1}
x_{a_1 i_1 i_2}\,x_{a_2 i_2 i_3}\cdots x_{a_\ell i_\ell i_1}.
\]

Products of traces are expanded into a sparse commutative polynomial. Terms are represented by sorted tuples of matrix-entry indeterminates; coefficients are exact integers. The verifier combines every contribution and checks every remaining coefficient.

- **universally_verified_identity**: every coefficient of the generic-entry residual is exactly zero. This proves the identity for all substitutions of d × d matrices over a characteristic-zero commutative coefficient field.
- **identity_rejected_nonzero_generic_residual**: at least one exact coefficient is nonzero, so the proposed identity is not universal at that dimension.
- **unresolved_permutation_cap** / **unresolved_expansion_cap**: the construction or verification budget was reached. Neither status is a negative result.

The verifier also accepts an explicitly supplied trace polynomial, so it can reject a proposed relation independently of whether that relation was produced by the FTI generator.

## Complexity controls

The FTI construction has (d+1)! permutation terms before trace-monomial canonicalisation. The generic-entry expansion estimates work as the sum of d^(total word length) over the distinct trace-product monomials. Both stages have separate configurable caps.

The expansion counter is a deterministic index-assignment work proxy. It is not a wall-clock guarantee and does not bound coefficient bit complexity or sparse-dictionary overhead. A cap produces **unresolved**, never **independent** or **false**.

## Scope and limits

Phase 27 currently constructs and proves individual FTI instances for a user-supplied tuple of d+1 matrix words. It does **not** enumerate every possible word substitution, compute a minimal generating set of all trace relations, or integrate universal reductions into the Phase 24–26 adaptive comparator. Those are separate follow-on tasks.

The theorem and its generic-entry certificate concern algebraic matrices. They do not establish that any physical structure, including Giza, implements these matrices or obeys an associated engineering mechanism.

## Tests

Fourteen standard-library tests cover dimensions 1, 2 and 3, noncommutative word substitutions, exact rejection of a false trace identity, trace cyclicity, commutativity of scalar trace factors, paired-integer validation, generator bounds and unresolved budget semantics.

Local run: python -m unittest -v — 14 tests passed. Clean GitHub Actions validation is tracked separately in the repository root index.
