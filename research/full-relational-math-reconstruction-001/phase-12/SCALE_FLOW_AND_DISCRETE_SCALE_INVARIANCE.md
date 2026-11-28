# Phase 12 — scale-flow, crossover and discrete-scale-invariance analyzer

## Purpose

Phase 07 made spatial and temporal transformations independent. Phase 12 tests how an observed relation behaves over a finite range: one power law, a change of exponent, or a log-periodic modulation. Each dataset is analysed independently; the code does not silently assume that a length-time relation or a common scaling map exists.

## Models

### Global power law

For positive observations, the model is fitted in log coordinates:

\[
\ln y = a + z\ln x + \epsilon.
\]

The exponent z is the slope in log-log space. If log-standard uncertainties in y are supplied as sigma_log_y, weighted least squares uses inverse-variance weights. Otherwise the fit is unweighted. Reported numerical Atlas matches for z are exploratory screens only.

### Continuous two-regime crossover

The hinge model is

\[
\ln y = a + z_1 u + \Delta z\,\max(0,u-u_c)+\epsilon,
\]

where \(u=\ln x\), \(u_c\) is a candidate breakpoint, the first exponent is \(z_1\), and the second is \(z_1+\Delta z\).

The analyzer searches observed x coordinates as breakpoints, subject to a declared minimum number of points in both regimes. It compares the best hinge fit with the global power law using BIC. A BIC difference is a model-selection diagnostic, not a p-value or proof of a real phase transition. The breakpoint must be validated on independent data and against physically plausible alternatives.

### Discrete scale invariance

A candidate log-periodic modulation is

\[
F(x)=x^\Delta P\!\left(\frac{\ln x}{\ln\lambda_0}\right),
\]

where \(P\) is periodic and \(\lambda_0\) is the preferred discrete scale factor.

As an initial detector, Phase 12 fits a sinusoidal pair in log(x) on top of the best non-periodic trend:

\[
\ln y = \text{trend} + A\cos(\omega\ln x)+B\sin(\omega\ln x)+\epsilon,
\qquad
\lambda_0=\exp(2\pi/\omega).
\]

The non-periodic trend is selected first from the global and hinge fits. This prevents a strong ordinary crossover from being mistaken for a log-periodic oscillation. Two harmonic coefficients and the scanned frequency are counted in the approximate BIC parameter penalty. A frequency-grid scan still introduces multiple-testing and aliasing issues; the BIC screen is not a calibrated significance test.

## Data contract

Each dataset supplies equal-length arrays x and y (at least four pairs). Both must be strictly positive and finite, and x values must be unique. Rows are sorted by x while y and optional sigma_log_y values remain attached. Repeated x observations must be aggregated or handled with a future replicate-aware model.

Optional sigma_log_y supplies positive finite standard uncertainties of ln(y). Uncertainty in x, covariance between points, calibration drift, shared systematic errors and model discrepancy are not yet included. Units and domain labels are retained as metadata; unit conversion is the caller's responsibility.

## Independent spatial and temporal analysis

A dataset can represent any variable domain: spatial extent, time, frequency, mass, energy, temperature, abstract scale parameter or another positive observable. The program fits each declared x/y pair as supplied. It does not rescale space and time together by default.

A dynamic law such as \(\tau_c(\ell)\propto\ell^z\) is tested only when characteristic length and characteristic time observations have been deliberately paired and declared by the input. A numerical correspondence between separate spatial and temporal datasets is not enough to infer a dynamic exponent.

## Atlas comparison and limits

The analyzer compares fitted global and regime exponents, and accepted discrete scale factors, against Phase 08's numeric machine-readable subset of the Canonical Pattern Atlas. The structural Atlas—Mandelbrot and Julia generators, graph spectra, symmetry groups, topology, substitution systems and other mathematical operators—requires its own comparators.

No full-atlas search is claimed by this phase. Numeric matches remain candidates, not exact identities or physical mechanisms.

## Synthetic demonstration

The input includes three synthetic tests:
- a pure quadratic relation with global exponent \(z=2\);
- a continuous crossover from exponent one to exponent two;
- a log-periodic signal constructed with preferred factor \(\lambda_0=1.7\).

The analyzer recovers the quadratic exponent exactly within floating-point precision, recovers the crossover breakpoint and two segment slopes, and estimates the synthetic discrete scale factor near 1.70035. It also rejects the false log-periodic interpretation of the sharp crossover by testing DSI on top of the selected best non-periodic trend.

These are software checks with constructed data, not empirical laws about nature.

## Validation

Eleven standard-library tests pass locally in a repository-shaped directory with Phase 08 available as a sibling. They cover global scaling, crossover detection, crossover-versus-DSI discrimination, log-periodic recovery, weighted fitting, invalid inputs, duplicate x values, minimum regime size, dataset requirements and paired numeral keys.

This is local module-level validation, not a full-repository CI or fresh-checkout claim.

## Next increments

1. Add errors-in-variables and covariance-aware fits for uncertainty in both x and y.
2. Add surrogate/null tests, frequency-grid multiple-comparison corrections and out-of-sample validation.
3. Add multi-crossover, smooth crossover and nonparametric local-exponent spectra.
4. Add a paired space-time dynamic-scaling schema with independent spatial and temporal calibration.
5. Compare crossover exponents, dynamic exponents and log-periodic scale factors against the complete Atlas and against structural recurrence generators.
