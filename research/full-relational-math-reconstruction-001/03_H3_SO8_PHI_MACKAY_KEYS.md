# 03 — H3, SO(8), triality, golden ratio and Mackay-shell keys

This section records mathematical structures that appear in, or are referenced by, the legacy model. It separates exact mathematics from what the source code implements.

## 1. Golden ratio and the 3:2 relation

\[
\varphi=\frac{1+\sqrt5}{2},
\qquad
\varphi^2=\varphi+1,
\qquad
\frac1\varphi=\varphi-1.
\]

Its continued fraction is:

\[
\varphi=[1;1,1,1,\ldots].
\]

Its convergents are ratios of consecutive Fibonacci numbers:

\[
1,\ 2,\ \frac32,\ \frac53,\ \frac85,\ \frac{13}{8},\ldots
\]

Therefore 3/2 is an exact convergent in the continued-fraction sequence for phi, not an exact value of phi.

\[
\varphi-\frac32=\frac{\sqrt5-2}{2}
\approx0.11803398875.
\]

Relative to phi, the shortfall is about 7.2949%. More accurate convergents follow the Fibonacci sequence.

The 3/2 ratio is linked mathematically to the golden ratio through rational approximation. This is not proof that a particular natural structure uses a golden-ratio mechanism.

## 2. H3 and icosahedral symmetry

H3 is a rank-3 non-crystallographic Coxeter group associated with icosahedral symmetry.

Standard mathematical facts:
- the H3 root system has 30 roots;
- the full reflection group has 120 elements;
- the rotational icosahedral subgroup has 60 elements;
- golden-ratio coordinates occur in standard realizations of H3.

The source code labels the environment H3 and uses phi in a coordinate formula. It does not implement H3 generators, the 30-root system, group multiplication or invariance tests. H3 is a design reference in v2, not an implemented symmetry action.

## 3. SO(8) and triality

The dimension of the Lie algebra so(8) is:

\[
\dim so(8)=\frac{8(8-1)}2=28.
\]

Type D4 has the exceptional triality symmetry. For the associated Spin(8) structure, the outer automorphism group is S3, and triality permutes three distinct eight-dimensional representations:
- vector representation 8v;
- one chiral spinor representation 8s;
- the other chiral spinor representation 8c.

The legacy source labels one octave SO(8) Iron Core with n=28. It does not construct the Lie algebra, its generators, the D4 root system or the triality maps. The label is not evidence that the algebra is implemented.

## 4. Mackay icosahedral shells and 42

For an ideal Mackay icosahedral cluster, the number of atoms in shell number n is:

\[
N_{\text{shell}}(n)=10n^2+2.
\]

| Shell n | Atoms in that shell |
|---:|---:|
| 1 | 12 |
| 2 | 42 |
| 3 | 92 |
| 4 | 162 |

Thus:

\[
N_{\text{shell}}(2)=10\cdot2^2+2=42.
\]

Do not confuse shell occupancy with cumulative cluster size. Including the central atom, cumulative closed-shell totals begin:

\[
13,\ 55,\ 147,\ 309,\ldots
\]

The value 42 is the number of atoms in the second added shell, not the total size of the two-shell cluster.

## 5. The exact 28–42–70 correspondence

The dossier contains several exact but independently defined quantities:

\[
28=\dim so(8),
\]

\[
42=10(2^2)+2\quad\text{(second Mackay shell)},
\]

\[
42=2\binom72\quad\text{(combined distance-2 shell around Q7 gates)},
\]

\[
70=2\binom73\quad\text{(combined distance-3 shell around Q7 gates)}.
\]

They satisfy:

\[
\frac{42}{28}=\frac32,\qquad28+42=70.
\]

This is a notable arithmetic and combinatorial correspondence network. The individual definitions are exact; a common physical origin or mechanism is not established.

## 6. A second model-geometry ratio: 16/9

The source projector contains:

\[
r(\alpha)=1+0.28\sin\alpha.
\]

Its extrema are:

\[
r_{\max}=1.28,\qquad r_{\min}=0.72.
\]

Therefore:

\[
\frac{r_{\max}}{r_{\min}}
=\frac{1.28}{0.72}
=\frac{128}{72}
=\frac{16}{9}
=\left(\frac43\right)^2.
\]

The ratio 16/9 is also a Pythagorean-tuning interval commonly called the minor seventh. The identity follows exactly from the source literal 0.28.

The coefficient 0.28 itself is not derived in the code from an independent physical law. This is a source-parameter consequence, not a confirmed natural law.

## 7. Other exact cross-structure arithmetic

The legacy mass coefficient table includes:

\[
c_E=n_E2^{E-1}.
\]

At the SO(8)-labelled octave:

\[
28\cdot2^3=224=448/2.
\]

At the Gate-42-labelled octave:

\[
42\cdot2^4=672=f_2(Q_7).
\]

The adjacent octave mass coefficients have ratio:

\[
\frac{M_5}{M_4}=\frac{672}{224}=3,
\qquad
\frac{n_5}{n_4}=\frac{42}{28}=\frac32.
\]

The relation between the n-value ratio and the mass coefficient ratio follows from the extra octave-doubling factor.

## 8. Natural-key register and caution

| Key | Exact mathematics | Legacy presence | Interpretation status |
|---|---|---|---|
| 3/2 | fifth ratio; Fibonacci convergent to phi | implicit in p | established arithmetic |
| phi | root of x^2-x-1=0 | used in z-coordinate | coordinate parameter; H3 action absent |
| H3 | 30 roots, order 120 | source comment/label | not implemented |
| SO(8) | dimension 28; D4 triality | source label and n=28 | Lie algebra not implemented |
| 42 | Mackay shell 2; Q7 two-gate shell 2; floor(128/3) | gate and octave label | several exact meanings, shared physical cause unknown |
| 16/9 | (4/3)^2, Pythagorean minor seventh | radial max/min consequence of 0.28 | source-parameter consequence |
| 28:42 | 2:3 | n=28 and n=42 | exact ratio; mechanism unknown |

## 9. Further mathematical work

- Implement the H3 root system and test invariance under its generators.
- Implement D4 roots, Dynkin diagram automorphisms and all three triality representations.
- Compare these structures with Q7 through explicit maps, not matching labels.
- Test whether 3/2, phi, 28 and 42 correspondences survive independent representations.
- Run null models to assess how often the same numbers and ratios arise in unconstrained searches.
- Preserve the distinction between shell counts, cumulative cluster counts, group orders, graph layers and code labels.
