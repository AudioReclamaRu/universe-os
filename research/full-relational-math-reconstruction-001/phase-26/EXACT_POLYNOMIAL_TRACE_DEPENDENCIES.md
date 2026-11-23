# Phase 26 — exact polynomial dependency discovery for trace features

## Purpose

Phase 25 identifies exact **linear** dependencies between trace-feature
columns on the current combined source/target ordered-pair support. Phase 26
extends that comparison by asking whether a candidate trace feature is an
exact polynomial of bounded total degree in previously retained features.

For prior features f_1,...,f_k, the default search includes every
monomial of total degree at most two:

\[
1,\quad f_i,\quad f_i f_j\;(i\leq j).
\]

A candidate g is polynomially dependent at degree bound D only if one exact
coefficient vector satisfies

\[
g + \sum_{|\alpha|\leq D} c_\alpha f^\alpha = 0
\]

on **every row in the combined support**. Coefficients are never fitted
separately to source and target.

## A. Exact construction and certificate

All feature values, monomial products, row reductions and coefficients use
the exact rational/quadratic field arithmetic from Phase 16. The monomial
catalogue is deterministic and includes the constant monomial.

For a detected dependency, the report contains:
- the complete polynomial equation and exact coefficients;
- each monomial's factor list and total degree;
- the exact coefficient-field radicand;
- the number of combined sample rows;
- a row-by-row exact verification count, with every residual checked to zero.

This is a finite-support certificate. It establishes the displayed equation
for those rows only.

## B. Protections against finite-sample interpolation

A polynomial basis can interpolate arbitrary values when it spans the whole
observed sample space. Phase 26 therefore does **not** classify a candidate
as dependent when the exact monomial-column rank equals the number of sample
rows. It returns the unresolved status
unresolved_monomial_span_saturates_samples instead.

Two additional limits are explicit:
- min_sample_rows defaults to four;
- max_polynomial_monomials defaults to 512.

If either limit prevents a meaningful test, the status is unresolved. In the
adaptive graph pipeline, unresolved candidates are retained conservatively;
they are not labelled independent in a universal sense and are not removed.

A finite-support dependency may fail when a new sample row is added. The tests
include such a control deliberately. This is why a detected relation is never
promoted to a universal matrix identity.

## C. Integration with Phases 24–25

The pipeline keeps the reductions in separate logical layers:

1. Phase 25 verifies the universal commutator-square trace identity.
2. Phase 25 removes exact linear dependencies on the current combined support.
3. Phase 26 tests still-linearly-independent candidate words against bounded
   polynomial monomials of the already retained features.
4. Only candidates certified polynomially dependent on the current support
   are omitted. Candidates that are independent or unresolved are retained.

New candidate words within one tier are considered in deterministic order.
A retained candidate may participate in polynomial expressions for later
words in that tier. An omitted candidate does not become a hidden input to
subsequent reductions.

The trace calculations remain subject to Phase 24's matrix-product budget.
Polynomial arithmetic has its own monomial-count cap; the two budgets are
not conflated.

## D. Correctness boundary

- Universal trace identities, finite-support linear dependencies and
  finite-support polynomial dependencies are three different result types.
- One shared exact coefficient vector is required across source and target.
- A certificate is valid only on its exact combined sample support.
- Monomial-span saturation, too few rows and monomial-cap exhaustion are
  unresolved outcomes.
- A polynomial non-detection is limited to the configured degree and monomial
  cap; it does not exclude higher-degree relations.
- The phase does not claim a universal trace-algebra identity or a physical
  interpretation of any relation.

## E. Tests

Seven standard-library tests cover exact quadratic recovery and row-wise
verification, degree-one control, shared source/target coefficients,
monomial-span saturation, monomial-cap exhaustion, finite-support failure
after adding a changed row, and parameter validation.
