# Phase 03 — Exact cross-domain pattern correspondences

## Numeral convention

This phase records integer parameters as paired binary/ternary numerals. The pair notation is

\[
\langle a_2\mid b_3\rangle,
\]

where both strings denote the same integer in bases two and three.

The principal keys used below are

\[
\begin{aligned}
\mathbf 2&=\langle 10_2\mid 2_3\rangle,\\
\mathbf 3&=\langle 11_2\mid 10_3\rangle,\\
\mathbf 4&=\langle 100_2\mid 11_3\rangle,\\
\mathbf 5&=\langle 101_2\mid 12_3\rangle,\\
\mathbf 7&=\langle 111_2\mid 21_3\rangle.
\end{aligned}
\]

No decimal positional expansion is used for the mathematical keys in this phase. Bibliographic identifiers and URLs remain unchanged.

## Finding A — Pascal support, Lucas digit rule and the hypercube face poset

### A.1. The binary support of Pascal's triangle

Let \(m\) be a positive word length. Write \(n\) and \(k\) as \(m\)-bit binary words:

\[
n=\sum_{i=0}^{m-1}n_i\mathbf 2^i,\qquad
k=\sum_{i=0}^{m-1}k_i\mathbf 2^i,\qquad n_i,k_i\in\{0,1\}.
\]

Define the finite support set

\[
P_m=
\left\{(n,k):
0\le k\le n<\mathbf 2^m,\ 
\binom nk\equiv 1\pmod{\mathbf 2}
\right\}.
\]

Lucas' theorem gives

\[
\binom nk\equiv
\prod_{i=0}^{m-1}\binom{n_i}{k_i}
\pmod{\mathbf 2}.
\]

Because each digit is binary, the coefficient is odd exactly when

\[
k_i\le n_i\quad\text{for every }i.
\]

Thus each bit position admits exactly three local pairs:

\[
(0,0),\quad (1,0),\quad (1,1),
\]

while \((0,1)\) is forbidden.

### A.2. An explicit bijection to ternary face states

Map each allowed local pair to a ternary face status:

\[
(0,0)\longleftrightarrow -,\qquad
(1,0)\longleftrightarrow 0,\qquad
(1,1)\longleftrightarrow +.
\]

Interpret these statuses as:

- \( - \): coordinate fixed at the lower endpoint;
- \(0\): coordinate free;
- \(+\): coordinate fixed at the upper endpoint.

Applying this map independently at every bit position gives a bijection

\[
\boxed{
P_m\;\longleftrightarrow\;\{-,0,+\}^{m}
\;\longleftrightarrow\;
\{\text{nonempty faces of }Q_m\}.
}
\]

This is stronger than equality of cardinalities. The inverse map is explicit at every coordinate, so every odd Pascal entry in the binary row block identifies one and only one nonempty face of the \(m\)-cube.

The face dimension is preserved by the rank formula

\[
\boxed{
\dim F(n,k)=
\operatorname{wt}_2(n)-\operatorname{wt}_2(k),
}
\]

because a free coordinate is precisely a bit with \(n_i=1,\ k_i=0\).

### A.3. The face-inclusion order is also preserved

For binary words, write \(a\preceq_{\rm bit}b\) when every one-bit of \(a\) is also a one-bit of \(b\). Define the order on Pascal-support pairs by

\[
(n,k)\preceq(n',k')
\quad\Longleftrightarrow\quad
n\preceq_{\rm bit}n'
\ \text{and}\
k'\preceq_{\rm bit}k.
\]

Under the coordinate map above,

\[
(n,k)\preceq(n',k')
\quad\Longleftrightarrow\quad
F(n,k)\subseteq F(n',k').
\]

Therefore the ordered set of odd Pascal positions is isomorphic to the poset of nonempty cube faces. Adjoining one formal bottom element gives the full abstract face lattice, including the empty face.

### A.4. The complete rank polynomial follows

Every coordinate has two fixed choices, contributing rank zero, and one free choice, contributing rank one. Therefore

\[
\sum_{(n,k)\in P_m}
x^{\operatorname{wt}_2(n)-\operatorname{wt}_2(k)}
=(\mathbf 2+x)^m.
\]

Consequently, the number of \(d\)-dimensional faces is

\[
f_d(Q_m)=\binom md\mathbf 2^{m-d}.
\]

At \(x=1\),

\[
|P_m|=(\mathbf 2+\mathbf 1)^m=\mathbf 3^m.
\]

This recovers the entire cube face vector, not merely its total face count.

### A.5. Further exact counts derived from the same local states

The same coordinate reasoning gives:

\[
\begin{aligned}
V_m&=\mathbf 2^m &&\text{vertices},\\
E_m&=m\mathbf 2^{m-1} &&\text{cube edges},\\
F_m&=\mathbf 3^m &&\text{nonempty faces},\\
I_m&=\mathbf 4^m &&\text{face--vertex incidences},\\
C_m&=\mathbf 5^m &&\text{ordered face-inclusion pairs, equality included},\\
S_m&=\mathbf 5^m-\mathbf 3^m &&\text{strict face-inclusion pairs},\\
H_m&=\mathbf 2m\mathbf 3^{m-1} &&\text{immediate Hasse covers}.
\end{aligned}
\]

Derivations:

- **Incidence:** per coordinate, a fixed-low face permits one vertex bit, a free coordinate permits either bit, and a fixed-high face permits one bit. There are four compatible local face/vertex pairs.
- **Comparable face pairs:** per coordinate, if the containing face is fixed there is one possible contained status; if it is free there are three. Thus there are five local ordered pairs. Equality contributes the \(\mathbf 3^m\) diagonal pairs.
- **Hasse covers:** a face with \(d\) free coordinates has exactly \(2d\) immediate subfaces, obtained by fixing one free coordinate at either endpoint. Summing over the rank polynomial gives \(H_m=\mathbf 2m\mathbf 3^{m-1}\).

### A.6. Exact cross-check for the existing \(Q_7\) reconstruction

For the already studied dimension

\[
m=\mathbf 7=\langle111_2\mid21_3\rangle,
\]

the formulas give the following independently encoded counts:

| Quantity | Binary / ternary pair |
|---|---|
| Vertices | \(\langle10000000_2\mid11202_3\rangle\) |
| Edges | \(\langle111000000_2\mid121121_3\rangle\) |
| Nonempty faces | \(\langle100010001011_2\mid10000000_3\rangle\) |
| Face--vertex incidences | \(\langle100000000000000_2\mid211110211_3\rangle\) |
| Ordered inclusion pairs, equality included | \(\langle10011000100101101_2\mid10222011112_3\rangle\) |
| Strict inclusion pairs | \(\langle10010100010100010_2\mid10212011112_3\rangle\) |
| Immediate Hasse covers | \(\langle10011111011110_2\mid112000000_3\rangle\) |

These closed forms reproduce the corresponding finite-combinatorial counts already stored in Phase 02. The proof is independent of the CSV enumeration method.

### A.7. Why this is a significant correspondence

One structure can now be read in several mathematically equivalent ways:

1. parity support of binomial coefficients;
2. digitwise subset relation between binary words;
3. the additive cellular automaton Rule 90;
4. the Sierpiński pattern in Pascal's triangle;
5. intervals of the Boolean lattice;
6. the ternary status encoding of cube faces;
7. the complete nonempty face-inclusion poset of the hypercube.

The link from Pascal parity to Rule 90 and the Sierpiński sieve is documented in MathWorld. The Lucas digit criterion supplies the exact coordinate rule. The cube-face interpretation then follows from the explicit bijection above.

This is an **exact combinatorial isomorphism**, not a physical law. Its relevance to a binary--ternary foundation is high because binary local constraints generate a ternary state alphabet with no numerical fitting.

## Finding B — The \(\mathbf 2\)-\(\mathbf 3\)-\(\mathbf 5\) scale system of the Sierpiński gasket

For the standard Sierpiński gasket, each stage consists of \(\mathbf 3\) smaller copies, each contracted by a factor \(\mathbf 2^{-1}\). Its Hausdorff dimension is

\[
d_f=\frac{\ln\mathbf 3}{\ln\mathbf 2}.
\]

The complementary Cantor construction has \(\mathbf 2\) copies at contraction factor \(\mathbf 3^{-1}\), so

\[
d_C=\frac{\ln\mathbf 2}{\ln\mathbf 3}=\frac1{d_f}.
\]

The reciprocal relation is exact because the copy-count and scale roles are exchanged.

The standard gasket also has a non-Euclidean diffusion scaling. For its canonical diffusion, the walk dimension and spectral dimension are

\[
d_w=\frac{\ln\mathbf 5}{\ln\mathbf 2},
\qquad
d_s=\frac{\mathbf 2\ln\mathbf 3}{\ln\mathbf 5}.
\]

They satisfy the Einstein relation

\[
\boxed{d_s=\frac{\mathbf 2d_f}{d_w}}.
\]

This creates a meaningful structural triad:

- \(\mathbf 3\): number of self-similar pieces;
- \(\mathbf 2\): linear refinement factor;
- \(\mathbf 5\): canonical diffusion/eigenvalue time-scaling factor.

The same fractal therefore connects geometric dimension, random-walk scaling and Laplacian spectral growth. Discrete scale invariance can additionally produce log-periodic oscillations in random-walk observables.

Scope limit: these exponents belong to the specified gasket and its canonical diffusion/resistance structure. They are not universal constants for every fractal or every physical network.

## Finding C — Fibonacci substitution, the golden ratio and aperiodic order

Consider the two-symbol substitution

\[
L\mapsto LS,\qquad S\mapsto L.
\]

Its incidence matrix is

\[
M=
\begin{pmatrix}
1&1\\
1&0
\end{pmatrix},
\]

with characteristic equation

\[
\lambda^2-\lambda-\mathbf1=0.
\]

Its Perron--Frobenius eigenvalue is

\[
\lambda=\varphi=\frac{\mathbf1+\sqrt{\mathbf5}}{\mathbf2}.
\]

Thus the golden ratio appears as the exact inflation eigenvalue of a finite substitution rule. The same substitution is used to construct Fibonacci aperiodic order; its eigenvectors determine relative tile frequencies and geometric inflation.

Recent mathematical phyllotaxis work also derives the golden-angle feature from a Fibonacci-substitution model of early flower-head development. This supports a specific model mechanism, not a claim that every plant or every spiral in nature must obey the golden ratio.

## Finding D — Feigenbaum scaling is universality within a class

For suitable one-dimensional maps with a single quadratic critical maximum, successive period-doubling intervals approach a common scaling ratio. This is explained through a renormalization fixed point.

The important lesson is methodological: a universal constant can be universal **within a precisely specified class**, rather than across all possible systems. Changing the critical order or moving to a different class of maps changes the scaling constants. Area-preserving maps, for example, have their own universality structure.

This is a strong example of a genuine universality class, but it does not identify a universal constant of the whole Universe.

## Finding E — River-network scaling is conditional, not yet one universal law

A theoretical framework derives river-network scaling relations from structural self-similarity, self-affine channels and approximately uniform drainage density. Under those assumptions, only two scaling exponents are independent, and Horton- and Tokunaga-style descriptions can be related.

However, empirical studies of large river basins report substantial fluctuations, systematic departures from scaling and no single established set of exponents. The same literature explicitly leaves universality unresolved.

This is an important negative control: common power-law appearance does not establish a unique universal generator.

## Evidence register

| Finding | Mathematical status | Physical interpretation |
|---|---|---|
| Pascal parity \(\leftrightarrow\) cube face poset | Exact bijection and order isomorphism | No physical claim yet |
| Sierpiński / Cantor dimension reciprocity | Exact consequence of swapped copy/scale roles | Applies to those constructions |
| Gasket geometric--walk--spectral relation | Established for the canonical gasket model | Model-dependent |
| Fibonacci substitution \(\leftrightarrow\) \(\varphi\) inflation | Exact matrix/eigenvalue result | Applies where the substitution mechanism is relevant |
| Feigenbaum scaling | Renormalization universality class | Conditional on map class |
| River-network exponents | Conditional theory plus empirical scaling | Universality remains unresolved |

## Research references

- Lucas theorem and its nonzero-binomial corollary: https://math.hmc.edu/funfacts/lucas-theorem/
- Rule 90 and Pascal parity / Sierpiński pattern: https://mathworld.wolfram.com/Rule90.html
- Sierpiński gasket construction and Hausdorff dimension: https://encyclopediaofmath.org/wiki/Sierpi%C5%84ski_gasket
- Einstein relation on fractal objects: https://www.aimsciences.org/article/doi/10.3934/dcdsb.2012.17.509
- Exact Laplacian spectrum on a Sierpiński-gasket domain: https://doi.org/10.1016/j.jfa.2018.08.018
- Fibonacci tiling, inflation matrix and golden-ratio eigenvalue: https://journals.iucr.org/a/issues/2020/05/00/ae5086/
- Emergence of the golden angle in flower heads: https://doi.org/10.1080/00029890.2025.2600904
- Feigenbaum universality and changes between classes: https://mathworld.wolfram.com/FeigenbaumConstant.html and https://doi.org/10.1103/PhysRevA.35.1847
- River-network scaling assumptions: https://doi.org/10.1103/PhysRevE.59.4865
- River-network fluctuations and deviations: https://doi.org/10.1103/PhysRevE.63.016115

## Next falsifiable questions

1. Can the Pascal--cube isomorphism be extended to a useful operator correspondence, not merely a state/poset bijection?
2. Which other prime-modulus Pascal supports yield analogous \(p\)-ary face or interval structures, and what makes the binary case special?
3. Can the \(\mathbf 2\)-\(\mathbf 3\)-\(\mathbf 5\) gasket scale relation be reproduced in other self-similar networks under independently specified local rules?
4. Which natural systems possess an independently measured substitution, adjacency or renormalization operator matching one of these exact generators?
5. Which apparent cross-domain coincidences disappear under null models that preserve dimension, sample size and scale range?

No numerical correspondence in this phase is promoted to a physical mechanism without an independently defined mapping, dimensional consistency, data, uncertainty analysis, alternatives and a falsifier.


## Related geometry programme — Phase 04

The Giza geometry study is documented in [../phase-04/GIZA_TRIAD_FIVE_NODE_GEOMETRY.md](../phase-04/GIZA_TRIAD_FIVE_NODE_GEOMETRY.md). It defines eight half-face patches per pyramid as a measurement schema, reports the differing published concavity evidence for Khufu, Khafre and Menkaure, and constructs a five-node spatial comparison using the three pyramid centres, the Great Sphinx head point and the Khentkaus I mapped site point.

The geometric correspondence remains provisional because its target points do not yet share one survey-grade reference frame. No physical network coupling is inferred. The paired binary/ternary numerical report is generated by [analyze_giza_geometric_network.py](../phase-04/analyze_giza_geometric_network.py).
