# Phase 13 — paired space-time scaling and dynamic exponents

## Purpose

Phase 12 analysed scale regimes within explicitly supplied x/y datasets. Phase 13 handles the specific case where each observation is a paired characteristic length and characteristic duration from the same process or defined ensemble.

It estimates the dynamic scaling relation

\[
\tau_c(\ell)\propto \ell^z
\]

without pairing unrelated spatial and temporal arrays merely because they have the same number of entries.

## Relation and unit invariance

The fit is performed using geometric reference scales:

\[
\ln\frac{\tau_i}{\tau_{\rm ref}}
=a+z\ln\frac{\ell_i}{\ell_{\rm ref}}+\epsilon_i.
\]

The exponent \(z\) is invariant under independent unit changes \(\ell\mapsto c\ell\) and \(\tau\mapsto d\tau\). The reference scales and intercept change, but the slope does not. No universal value of \(z\) is assumed.

## Measurement uncertainties

The input may provide:
- sigma_log_length: standard uncertainty of \(\ln\ell\);
- sigma_log_time: standard uncertainty of \(\ln\tau\);
- rho_log_length_time: correlation coefficient between the two log-measurement errors for each paired observation.

If only time uncertainty is supplied, the engine uses weighted least squares in log space. If both length and time uncertainty are supplied, it iteratively uses the first-order effective residual variance

\[
\sigma_{\rm eff,i}^2
=\sigma_{\ln\tau,i}^2
+z^2\sigma_{\ln\ell,i}^2
-2z\,\operatorname{Cov}(\ln\ell_i,\ln\tau_i).
\]

The covariance term is constructed from the two standard uncertainties and their supplied correlation. Correlations are not silently assumed zero when a rho array is provided.

This is an iterative effective-variance approximation to errors-in-variables regression, not a full latent-variable maximum-likelihood or Bayesian model. The returned slope uncertainty is conditional on this approximation. When no measurement uncertainties are supplied, the reported OLS slope uncertainty assumes independent homoscedastic log residuals.

## Data contract

Each paired dataset must supply equal-length positive finite arrays length and time, with at least three paired observations. Repeated lengths are allowed, since several observations may share a characteristic length. Sorting is applied to complete observation tuples so uncertainties and correlations remain attached to their measurements.

Values must use consistent units within each dataset. Unit labels and source metadata are preserved as descriptive fields; conversions are the caller's responsibility.

## Atlas comparison

The estimated dynamic exponent is compared to Phase 08's numerical machine-readable subset of the Canonical Pattern Atlas. Exact symbolic identities and structural correspondences are future comparator work. A numerical match is only a candidate and does not prove a universal dynamic law or causal mechanism.

## Synthetic demonstration

The example contains:
- an exact synthetic \(\tau\propto\ell^{3/2}\) control;
- a noisy paired dataset with length and time log-uncertainties and a nonzero within-pair correlation coefficient.

The first recovers \(z\) close to \(3/2\). The second demonstrates the iterative effective-variance fit with correlation. Both datasets are invented for software validation and are not measurements of a natural process.

## Validation

Twelve standard-library tests pass locally in a repository-shaped directory with Phase 08 available as a sibling. They cover exact dynamic-exponent recovery, unit-rescaling invariance, correlated errors-in-variables fitting, time-only weighted fitting, repeated lengths, explicit-pair enforcement, invalid data, covariance requirements, invalid correlations, Atlas screening and paired numeral keys.

This is local module-level validation, not a full-repository CI or fresh-checkout claim.

## Limits and next increments

- The effective-variance fit is an approximation and may need a full orthogonal-distance, latent-variable or hierarchical likelihood model.
- Systematic calibration errors shared across observations need a full cross-observation covariance structure, not only per-pair correlations.
- Between-system heterogeneity and multiple dynamic exponents need hierarchical or mixture models.
- Finite-size crossovers and time-window dependence need to be checked with Phase 12.
- No causal physical bridge is inferred from a fitted exponent alone.
