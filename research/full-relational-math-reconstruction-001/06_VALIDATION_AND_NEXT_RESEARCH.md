# 06 — Validation, reproducibility and next research

## 1. Mathematical checks

The standard-library script verify_relations.py checks:
- 128 vertices and 448 edges of Q7;
- degree 7, connectivity and diameter 7;
- face vector and total 2187;
- ternary-to-binary mapping and exact fibre sizes;
- all mixed-alphabet products 2^a*3^(7-a) and sum 5^7;
- 42/85 quotients, remainders, binary words, XOR, Hamming distance and nearest-gate shells;
- shortest-path count 7!;
- SO(8) dimension arithmetic;
- Mackay shell counts;
- golden-ratio convergents;
- legacy p, theta, PI_128, phase period and mass coefficients;
- radial ratio 16/9;
- seven-position cyclic combinatorics.

It checks arithmetic and finite combinatorics only. It does not execute the graphical v2 application or simulate physical spacetime.

## 2. Legacy code audit points that must remain visible

- Q7 is a graph on 128 vertices with 448 undirected edges and degree 7.
- The legacy field is based on absolute integer-index distance, not Hamming distance.
- The projector takes 128 samples of a one-parameter curve; it is not a filled 4D lattice.
- The 4D coordinate norm is not shown to be constant, so the mapping is not verified as a stereographic projection from a fixed S3.
- PI_128 is a truncated approximation.
- The reset frame returns pre-reset energy with post-reset stress.
- SO(8), H3, triality, a ternary state layer and the comparator are not implemented in v2.
- Physical labels in the mass matrix are not supported by dimensional derivations in the source.

## 3. Priority sequence for full reconstruction

### Stage A — Exact combinatorics

1. Preserve Q7 as the binary layer.
2. Enumerate all 2187 ternary states.
3. Implement the face interpretation and comparator projection explicitly.
4. Construct incidence matrices and boundary operators.
5. Verify boundary-of-boundary is zero, face counts, Euler characteristics and Hodge spectra.
6. Keep zero as a valid named state.

### Stage B — Gate and symmetry analysis

1. Preserve gates 42 and 85.
2. Verify all gate shell counts and antipodal paths.
3. Test graph-automorphism invariance.
4. Compare Hamming and legacy integer-index metrics.
5. Investigate how the 42 and 85 roles relate without merging semantics.

### Stage C — H3 / SO(8) / golden geometry

1. Construct the H3 root system and verify invariance under its generators.
2. Construct D4 roots and SO(8)/Spin(8) triality action.
3. Compare these structures with Q7 through explicit maps.
4. Test whether 3/2, phi, 28 and 42 correspondences survive independent representations.
5. Run null models to assess how often the same numbers and ratios arise in unconstrained searches.

### Stage D — Nonlinear dynamics

1. Reproduce the legacy recurrence exactly.
2. Separate pre-event and post-event state variables.
3. Correct the energy ledger only in a new version, never in legacy source.
4. Compare index-metric and graph-invariant gate fields.
5. Run parameter sweeps and sensitivity analysis.
6. Locate bifurcations, stable/unstable regimes and hysteresis.
7. Test dependence on time step and PI approximation.

### Stage E — Physical and cross-domain tests

1. Define dimensionally correct observables.
2. Identify source, path, receiver, transfer function and energy budget.
3. Compare Giza and Rishat properties with uncertainty.
4. Compare against alternative sites and null models.
5. Pre-register test ratios and holdout observations.
6. Reject interpretations without a mechanism or falsifier.

## 4. Nonlinear methods to apply

After defining state variables and units, candidate methods include:
- fixed points and periodic orbits;
- Poincaré maps for thresholded recurrences;
- Floquet multipliers for periodic linearized dynamics;
- bifurcation diagrams versus p, theta, modulation amplitude and threshold;
- Lyapunov exponents where the map is differentiable or piecewise-smooth treatment is justified;
- hysteresis and return-map analysis;
- sensitivity to initial conditions and time step;
- graph Laplacian and Hodge Laplacian mode decomposition;
- entropy and transition statistics with a declared ensemble;
- null models and parameter-identifiability checks.

Do not call a threshold reset a physical collapse until the physical state variable, conserved quantities, units and mechanism are defined.

## 5. Seven-position musical combinatorics from the v3 brief

The existing v3 task brief proposes seven descending intervals:

\[
[1,2,2,2,1,2,2].
\]

Their sum is 12 semitones. The two one-semitone positions can be chosen in:

\[
\binom72=21
\]

ways.

On a 7-position cycle, the minimum cyclic separation between two selected positions has three possible classes, 1, 2 or 3. Since 7 is odd, each class contains exactly seven unordered pairs:

\[
21=7+7+7.
\]

This is exact cyclic combinatorics. It does not demonstrate a galactic period or astronomical mechanism. Keep musical and galactic interpretations separate unless an independently measured relation is supplied.

## 6. Observer, comparator and Möbius extensions

The v3 implementation brief additionally specifies candidate structures:
- sign inversion T(-1)=+1, T(0)=0, T(+1)=-1;
- involution T(T(s))=s;
- projection invariance pi(T(s))=pi(s);
- a comparator that retains binary support while identifying the two signed states;
- a Möbius-type orientation-reversing gluing in which local sign changes but identity is preserved.

These are mathematical model proposals, not current v2 capabilities.

A sign involution alone does not make a Möbius strip. A genuine Möbius construction requires a non-orientable bundle or orientation-reversing identification. The black/white sphere and a Möbius strip are different topological objects.

The number 42 as an observer-origin concept must remain separate from the integer node gate 42 in legacy v2.

## 7. Release discipline

- Keep legacy v2 source immutable.
- Develop new algorithms in a separate namespace/version.
- Preserve test vectors and source hashes.
- Use independent reference values.
- Store every derived relation with status and uncertainty.
- Do not update a mathematical formula because a different exponent gives a closer result.
- Promote no physical conclusion without a measurable prediction and falsifier.

## 8. Completion status

This package is a foundational mathematical dossier and reproducible arithmetic audit. It is not yet the full implementation of the mathematical engine, H3/SO(8) operators, complete nonlinear experiment suite or a physical Rishat–Giza model.
