# 04 — Legacy v2 formulas, relational structure and nonlinear dynamics

This file records equations as they appear in the pinned source and derives their direct mathematical consequences. It does not certify their physical interpretation.

## 1. Pythagorean comma as the model's base parameter

The source defines:

\[
p=\frac{3^{12}}{2^{19}}
=\frac{531441}{524288}
\approx1.0136432647705078.
\]

This is the Pythagorean comma:

\[
p=\frac{(3/2)^{12}}{2^7}.
\]

It measures the mismatch between twelve pure fifths and seven octaves. The ratio is not unity because powers of 3 cannot equal powers of 2 for positive exponents.

The source then defines:

\[
\theta=\ln p\approx0.0135510333783554,
\qquad
M_\mu=\frac{\theta}{128}.
\]

Therefore:

\[
128M_\mu=\theta.
\]

This distributes the model's logarithmic parameter over 128 equal slots. The code does not supply physical units that would make M_mu an experimentally established inertia quantum.

In musical cents:

\[
1200\log_2(p)\approx23.4600104\text{ cents}.
\]

## 2. Parameter and label map in the source

| Source symbol | Definition | Mathematical status |
|---|---|---|
| N | 128 = 2^7 | exact integer |
| GATE_42 | 42 | node/index |
| GATE_85 | 85 | node/index |
| p | 3^12 / 2^19 | exact rational |
| theta | ln(p) | dimensionless logarithm |
| M_mu | theta / 128 | model-defined scale |
| phi | (1 + sqrt(5))/2 | golden ratio |
| PI_128 | 128-term Leibniz partial sum | approximation to pi |
| K_SCALE | 6.81e-25 | hard-coded calibration; derivation/units need proof |
| radial amplitude | 0.28 | hard-coded geometric parameter |
| phase amplitude | 0.15 | hard-coded modulation parameter |
| w multiplier | 6 | hard-coded projector parameter |
| projection pole | 2.2 with floor 0.2 | hard-coded mapping parameters |

The header describes p as the sole free parameter, but the executable model contains additional constants and scaling choices. A complete derivation must account for each one.

## 3. Legacy cosmological and fine-structure formulas

The source defines:

\[
\alpha^{-1}_{model}=128p^5,
\]

\[
\Omega_{\Lambda,model}=1-p^{-85},
\]

\[
(\Omega_{DM}/\Omega_B)_{model}=p^{125}.
\]

Recalculation from the source equations gives:

| Formula | Recalculated value | Existing comparison value | Status |
|---|---:|---:|---|
| 128*p^5 | 136.9732198005 | CODATA 2022 alpha inverse 137.035999177(21) | discrepancy about -0.045812%; not an exact match |
| 1-p^(-85) | 0.6839446230 | Planck 2018 Omega_Lambda about 0.6847 +/- 0.0073 | close to this benchmark, but exponent 85 lacks an independent physical derivation |
| p^125 | 5.4405446334 | source reference 5.36 | about +1.5027% |
| p^124 | 5.3673169077 | diagnostic comparison only | closer numerically, but choosing exponent 124 after seeing data would be post-hoc fitting |

The exact formula as written must remain unchanged in the legacy record. No exponent should be silently adjusted to improve agreement.

The source-level integer decompositions are:

\[
5=2+3,\qquad85=2\cdot42+1,\qquad125=5^3=128-3.
\]

These are exact arithmetic identities. They do not by themselves derive the physical formulas.

## 4. Mass matrix decomposition

The source octave labels and n-values are:

\[
n_E=[1,7,8,28,42,64,128],\quad E=1,\ldots,7.
\]

The function defines:

\[
M_E=M_0\,n_E\,2^{E-1}.
\]

The integer coefficient multiplying M_0 is:

| E | n_E | 2^(E-1) | c_E |
|---:|---:|---:|---:|
| 1 | 1 | 1 | 1 |
| 2 | 7 | 2 | 14 |
| 3 | 8 | 4 | 32 |
| 4 | 28 | 8 | 224 |
| 5 | 42 | 16 | 672 |
| 6 | 64 | 32 | 2048 |
| 7 | 128 | 64 | 8192 |

Exact correspondences:

\[
224=28\cdot8=448/2,
\]

\[
672=42\cdot16=f_2(Q_7),
\]

\[
\frac{M_5}{M_4}=\frac{672}{224}=3,\qquad
\frac{n_5}{n_4}=\frac{42}{28}=\frac32.
\]

The relation between the n-value ratio and the mass coefficient ratio follows from the extra octave-doubling factor.

The scale M_0=M_mu*K_SCALE still needs a dimensionally complete derivation. Labels such as Planck Vacuum, Quark Matrix, Iron Core, Organic, White Dwarf and Neutron Star are source labels; the table does not demonstrate that the computed values are actual particle or astrophysical masses.

## 5. Legacy projector: exact phase relation and geometric equations

The source sets:

\[
\alpha_i=i\frac{\pi_{128}}{64}+0.009t,
\]

\[
\beta_i=i\frac{\pi_{128}}{32}+0.018t.
\]

Therefore:

\[
\beta_i=2\alpha_i
\]

exactly, for every index i and time t.

Before the 3D mapping, the four coordinates are:

\[
x_i=r_i\cos(2\alpha_i),\quad
y_i=r_i\sin(2\alpha_i),
\]

\[
z_i=\varphi\cos\alpha_i,\quad
w_i=6\Psi\theta\sin\alpha_i,
\]

where:

\[
r_i=1+0.28\sin\alpha_i.
\]

The XY radius is exactly r_i, since cos^2(2alpha)+sin^2(2alpha)=1.

The radial extrema are:

\[
r_{\max}=1.28,\qquad r_{\min}=0.72,
\]

\[
r_{\max}/r_{\min}=16/9.
\]

The four-dimensional norm squared is:

\[
\|q_i\|^2=
(1+0.28\sin\alpha_i)^2+
\varphi^2\cos^2\alpha_i+
(6\Psi\theta)^2\sin^2\alpha_i.
\]

This is not constant for general alpha and Psi. The source does not show that the points lie on one fixed 3-sphere S3. The subsequent denominator mapping is therefore not a verified stereographic projection from S3.

The source coordinates are 128 samples of one parameterized curve, connected by Q7 graph chords. They are not a filled 4D cell complex.

## 6. PI_128 and its induced period drift

The source computes:

\[
\pi_{128}=4\sum_{k=0}^{127}\frac{(-1)^k}{2k+1}
\approx3.1337802727899895.
\]

Compared with mathematical pi:
- absolute error: approximately -0.0078123808;
- relative error: approximately -0.2486758%.

The phase driver uses:

\[
\sin\left(t\frac{2\pi_{128}}{85}\right).
\]

Its actual mathematical period is:

\[
T_d=\frac{85\pi}{\pi_{128}}\approx85.2119013811,
\]

not exactly 85.

For physical resonance claims use exact pi, propagate uncertainty and separately report the legacy approximation.

## 7. Nonlinear threshold recurrence

The source recurrence, for positive time step dt, is:

\[
t_{n+1}=t_n+dt,
\]

\[
\Psi_{n+1}^{pre}=
\Psi_n+\theta dt
\left[
1+0.15\sin\left(\frac{2\pi_{128}t_{n+1}}{85}\right)
\right].
\]

Since the modulation factor lies between 0.85 and 1.15, the pre-reset increment is always positive for dt>0.

When the threshold condition is met:

\[
\Psi_{n+1}=\theta\Psi_{n+1}^{pre},
\qquad
\sigma_i^{post}=\theta\sigma_i^{pre}.
\]

This is a discrete hybrid recurrence with positive accumulation between events, periodic modulation, threshold-triggered switching and multiplicative residual state.

It is not by itself a physical earthquake, vacuum collapse or astrophysical phase transition. The time variable is a model step unless calibrated to physical time.

For the standard initial state, threshold p and dt=1, the existing audit reproduces reset steps near 75, 148, 221 and 295. These are outputs of the source recurrence, not measured natural periods.

## 8. Energy bookkeeping defect

The legacy code calculates:

\[
E^{pre}=M_\mu\sum_i(\sigma_i^{pre})^2
\]

before the threshold branch. It then changes every stress value by theta, but returns the old energy alongside the new stress.

If energy is defined by the same quadratic functional:

\[
E^{post}=M_\mu\sum_i(\theta\sigma_i^{pre})^2
=\theta^2E^{pre}.
\]

Hence:

\[
\frac{E^{pre}}{E^{post}}=\theta^{-2}\approx5445.7183.
\]

This is a state-ordering inconsistency in the code, not evidence of an energy burst. A new engine must either return separate pre- and post-event energies or recompute energy after reset, with a dimensionally defined ledger.

## 9. Graph topology does not currently control the stress field

The graph is Q7, but the gate field uses ordinary integer-index distance:

\[
g(i)=\exp\left[-8\min\left(\frac{|i-42|}{128},
\frac{|i-85|}{128}\right)\right].
\]

This is not Hamming distance. Nodes 10 and 43 are both Q7-neighbours of 42 but receive substantially different index-based weights.

A topology-driven alternative must use graph distance or a defined graph operator, then pass permutation and automorphism invariance tests. It must not be silently substituted into the legacy record.

## 10. Fragile numerical near-match in the phase expression

The code-derived quantity:

\[
\frac{2\pi_{128}}{85\theta}\approx5.4413567113
\]

is close to:

\[
p^{125}\approx5.4405446334
\]

with relative difference approximately 0.01493%.

Replacing PI_128 with exact pi changes the first value to approximately 5.4549217819; its relative difference from p^125 becomes approximately 0.26426%.

This sensitivity to a truncated approximation makes the match fragile. It is an exploratory numerical correspondence, not a robust invariant or physical prediction.

## 11. Chemical anchor positions in Q7

The source places chemical markers at indices equal to atomic numbers for H, Fe, Au, Hg and Og. It does not simulate their electron shells or atomic interactions.

| Marker | Z / Q7 index | 7-bit word | dH(Z,42) | dH(Z,85) | nearest gate |
|---|---:|---|---:|---:|---:|
| H | 1 | 0000001 | 4 | 3 | 3 |
| Fe | 26 | 0011010 | 2 | 5 | 2 |
| Au | 79 | 1001111 | 4 | 3 | 3 |
| Hg | 80 | 1010000 | 5 | 2 | 2 |
| Og | 118 | 1110110 | 4 | 3 | 3 |

This gives a 3:2 split among these five selected markers. Because this is a small, source-selected set, selection bias must be considered.

For Au and Hg:

\[
79\oplus80=31=0011111_2,\qquad d_H(79,80)=5.
\]

They are consecutive atomic numbers but not adjacent vertices in Q7. Any proposed chemical comparison must be stored separately from graph edges.

## 12. Model predictions and scientific status

The three formula outputs and mass matrix are preserved as legacy outputs. They require independent derivations, units, uncertainty propagation and new data before they can be called physical predictions.

No source-level formula may be changed in this reconstruction. A revised equation belongs in a separately versioned model with a derivation explaining why it differs.
