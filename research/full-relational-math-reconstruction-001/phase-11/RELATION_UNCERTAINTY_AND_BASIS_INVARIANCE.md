# Phase 11 — covariance propagation and basis-invariant relation families

## Purpose

Phase 10 identifies bounded monomial matches in individual dimensionless bases. Phase 11 transports those exponent vectors back to the original Phase 09 variables and propagates their joint measurement uncertainty.

It asks how uncertain a derived relation is when source variables are uncertain and correlated, and whether the same relation in different equivalent Pi bases maps back to the same source-variable exponent vector and uncertainty.

## Mathematical construction

Let the original variable vector be \(q=(q_1,\ldots,q_n)\). A Pi basis is described by an exponent matrix \(A\):

\[
\Pi_j=\prod_i |q_i|^{A_{ij}}.
\]

A candidate relation in that basis has exponent vector \(k\):

\[
R=\prod_j \Pi_j^{k_j}.
\]

Mapping back to the original variables gives

\[
R=\prod_i |q_i|^{u_i},\qquad u=A k.
\]

Let \(C_{\ln q}\) be the supplied covariance matrix of logarithmic absolute magnitudes:

\[
(C_{\ln q})_{ij}=\operatorname{Cov}(\ln|q_i|,\ln|q_j|).
\]

Then

\[
\boxed{\operatorname{Var}(\ln|R|)=u^\mathsf{T}C_{\ln q}u.}
\]

This is covariance propagation for a linear combination in log space. Correlations are included; independence is never silently assumed.

If the log-relation is Gaussian, the relative standard deviation of the corresponding lognormal relation is

\[
\frac{\sigma_R}{|\mathbb E R|}=\sqrt{\exp(v)-1},
\qquad v=\operatorname{Var}(\ln|R|).
\]

The interval \([\exp(-\sqrt v),\exp(\sqrt v)]\) is a one-log-standard-deviation multiplicative interval around the nominal magnitude. It is not a confidence interval unless a suitable distributional assumption is justified. The program reports this limitation explicitly.

## Basis invariance

For every Phase 10 candidate, Phase 11 finds the corresponding Phase 09 Pi groups and reconstructs the original exponent vector \(u=A k\). Relations are grouped only when these exact rational exponent vectors agree.

This is stronger than comparing rounded values. Two formulas written in different Pi coordinates that reduce to the same monomial of the original variables receive the same relation signature and the same propagated log-variance.

A relation and its reciprocal have opposite exponent vectors and are retained as distinct signed relations; they are not collapsed into one entry.

## Covariance input

The input is a JSON package containing phase09_report, phase10_report and log_covariance. The covariance object contains variable_order and a square log_relative_covariance matrix.

The matrix may be supplied in any variable order; names are used to reorder it into Phase 09 order. It must be finite, symmetric and positive semidefinite. Singular positive-semidefinite matrices are valid.

The covariance is an external evidence input. Phase 09 dimensional analysis does not invent measurement errors or correlations. Source, status and method of covariance estimation must be preserved.

## Output

The report contains propagated uncertainty for each candidate in each Pi basis; exact rational original-variable exponent vectors; basis-invariant relation signatures; families grouping representations that map to the same original exponent vector; representation counts and covariance-derived uncertainty.

Counts use paired binary/ternary notation. Floating-point values are secondary numerical evaluations; rational exponent vectors are retained exactly.

## Synthetic demonstration

The example is deliberately artificial. Phase 09 receives two dimensionless variables and Phase 10 supplies five basis representations of the constructed relation \(A B=\varphi\). A synthetic log-covariance matrix is supplied:

\[
C_{\ln q}=
\begin{pmatrix}
0.0001 & 0.00005\\
0.00005 & 0.0004
\end{pmatrix}.
\]

For \(u=(1,1)^\mathsf T\), every representation produces \(v=0.0006\). The report groups the five representations into one relation family and gives the same propagated log-standard uncertainty. Neither the values nor the covariance are real measurements; this is a software and algebra consistency test only.

## Safeguards and limits

- The log-covariance model requires nonzero source-variable magnitudes.
- The covariance matrix must include known correlations; omitted correlations must not be silently set to zero.
- No Gaussian distribution or confidence coverage is assumed by the code.
- The optional lognormal relative-standard-deviation conversion is explicitly conditional.
- Uncertainty is not evidence that a relation is physically meaningful or causal.
- Calibration uncertainty, shared systematic errors, model discrepancy and parameter uncertainty must be included in the supplied covariance if relevant.
- This implementation propagates monomial exponent relations. Nonlinear functions of Pi groups need their own Jacobian or interval propagation.

## Validation

Eleven standard-library tests cover basis-invariant mapping through five representations, correlated covariance propagation, variable-order reindexing, symmetry and positive-semidefinite validation, singular covariance, exact fractional exponents, unknown groups, zero variance and invalid matrix dimensions.

The synthetic Phase 09 → Phase 10 → Phase 11 example ran locally in a repository-shaped directory. This is module-level verification, not a full-repository CI or fresh-checkout claim.

## Next increments

1. Capture covariance directly from survey and sensor ingestion, including common calibration/systematic terms.
2. Add Jacobian propagation for nonlinear functions and uncertainty intervals when the log approximation is unsuitable.
3. Compare structural invariants under basis transformations, not only numerical monomial matches.
4. Add error-in-variables and model-discrepancy treatment for power-law and crossover fits.
5. Add domain-specific data adapters while preserving raw observations, calibration metadata and detection limits.
