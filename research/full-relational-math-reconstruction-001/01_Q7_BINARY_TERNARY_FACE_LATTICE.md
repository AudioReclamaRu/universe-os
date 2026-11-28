# 01 — Q7, binary states, ternary states and the complete face lattice

## 1. Binary state space

Define:

\[
V(Q_7)=\{0,1\}^7,\qquad |V(Q_7)|=2^7=128.
\]

Each state is a seven-bit word. The all-zero word is valid, not a missing value.

Two vertices are adjacent exactly when one bit differs:

\[
i\sim j\iff\operatorname{popcount}(i\oplus j)=1.
\]

The Cayley generators are {1,2,4,8,16,32,64}. This is the seven-dimensional Boolean hypercube graph Q7.

Exact graph invariants:
- vertices: 128;
- degree of every vertex: 7;
- undirected edges: 128*7/2=448;
- diameter: 7;
- connected and bipartite;
- graph distance: Hamming distance;
- antipodes: bitwise complements.

The source stores each undirected edge once by retaining only j>i. Therefore the ordinary degree is 7, not 14. A legacy comment mentioning 14 edges per node is not the graph's ordinary degree.

## 2. The key identity: 3^7 counts every face of Q7

A face of a 7-cube is specified coordinate by coordinate. Each coordinate has exactly three possible statuses:
1. fixed at 0;
2. free;
3. fixed at 1.

Thus the full face set is in bijection with a seven-symbol ternary product:

\[
\mathcal F(Q_7)\cong\{-,0,+\}^7,
\qquad |\mathcal F(Q_7)|=3^7=2187.
\]

This is exact combinatorics. The three symbols mean fixed-low, free, fixed-high in this face-lattice interpretation.

## 3. Face vector

For a d-dimensional face, choose d free coordinates. The other 7-d coordinates are fixed, each with two choices:

\[
f_d=\binom7d2^{7-d}.
\]

| Face dimension d | Interpretation | Count |
|---:|---|---:|
| 0 | vertices | 128 |
| 1 | edges | 448 |
| 2 | square faces | 672 |
| 3 | 3-cubes | 560 |
| 4 | 4-faces | 280 |
| 5 | 5-faces | 84 |
| 6 | facets | 14 |
| 7 | whole 7-cube | 1 |
| **Total** | **all faces** | **2187** |

The sum is the binomial identity:

\[
\sum_{d=0}^{7}\binom7d2^{7-d}=(2+1)^7=3^7.
\]

This reconciles the two principal scenarios:
- 2^7: vertices;
- 3^7: all faces, including vertices, higher-dimensional faces and the whole cube.

## 4. Ternary-to-binary comparator as a face map

The project brief proposes:

\[
\pi(-1)=1,\qquad \pi(0)=0,\qquad \pi(+1)=1.
\]

For a seven-coordinate state s in {-1,0,+1}^7:

\[
\pi(s)_i=
\begin{cases}
0,&s_i=0,\\
1,&s_i\in\{-1,+1\}.
\end{cases}
\]

Interpretation:
- CENTER = 0: coordinate remains free;
- NEG = -1: coordinate is fixed at cube coordinate 0;
- POS = +1: coordinate is fixed at cube coordinate 1.

A ternary state therefore identifies one face of Q7.

If the binary mask has Hamming weight k, exactly k coordinates are fixed. Each fixed coordinate has two possible side/sign assignments, hence:

\[
|\pi^{-1}(b)|=2^k.
\]

There are C(7,k) masks of weight k, so:

\[
\sum_{k=0}^{7}\binom7k2^k=(1+2)^7=2187.
\]

This is the exact fibre-count identity behind the 128-to-2187 mapping.

### Fibre distribution

| Fixed coordinates k | Free coordinates | Number of binary masks | Fibre size per mask | Ternary states in stratum |
|---:|---:|---:|---:|---:|
| 0 | 7 | 1 | 1 | 1 |
| 1 | 6 | 7 | 2 | 14 |
| 2 | 5 | 21 | 4 | 84 |
| 3 | 4 | 35 | 8 | 280 |
| 4 | 3 | 35 | 16 | 560 |
| 5 | 2 | 21 | 32 | 672 |
| 6 | 1 | 7 | 64 | 448 |
| 7 | 0 | 1 | 128 | 128 |
| **Total** | — | **128 masks** | — | **2187 states** |

The stratum with k fixed coordinates is the same as face dimension d=7-k. This is the face vector in reverse dimension order.

## 5. Mixed binary/ternary alphabets

For a predetermined choice of a binary positions and 7-a ternary positions:

\[
S_a=2^a3^{7-a}.
\]

From a=7 down to a=0:

\[
128,\ 192,\ 288,\ 432,\ 648,\ 972,\ 1458,\ 2187.
\]

Adjacent terms have exact ratio 3/2.

If the positions assigned to the binary and ternary alphabets may also vary:

\[
\sum_{a=0}^{7}\binom7a2^a3^{7-a}
=(2+3)^7=5^7=78125.
\]

This 5^7 construction is a separate mixed-alphabet product space. Do not conflate it with the 2187 faces of Q7.

## 6. Incidence relations

A d-face contains 2^d vertices. The total number of vertex-face incidences is:

\[
\sum_{d=0}^{7}f_d2^d
=\sum_{d=0}^{7}\binom7d2^{7-d}2^d
=4^7=16384.
\]

Every vertex belongs to exactly 2^7=128 faces: for each coordinate, either leave it free or fix it to that vertex's bit.

Each edge lies in 2^6=64 faces, giving:

\[
448\cdot64=28672
\]

edge-face incidences.

These are incidence counts, not counts of distinct objects.

## 7. Euler characteristics

For the whole cube:

\[
\chi(Q_7)=\sum_{d=0}^{7}(-1)^df_d=1.
\]

For its boundary, omitting the 7-dimensional interior cell:

\[
\chi(\partial Q_7)=\sum_{d=0}^{6}(-1)^df_d=2.
\]

This is consistent with the boundary being a 6-sphere.

## 8. Graph spectrum and dynamical implications

The adjacency eigenvalues of Q7 are:

\[
\lambda_j=7-2j,\qquad
\text{multiplicity }\binom7j,\quad j=0,\ldots,7.
\]

| Eigenvalue | Multiplicity |
|---:|---:|
| 7 | 1 |
| 5 | 7 |
| 3 | 21 |
| 1 | 35 |
| -1 | 35 |
| -3 | 21 |
| -5 | 7 |
| -7 | 1 |

The graph Laplacian eigenvalues are 2j with the same multiplicities. Its algebraic connectivity is 2.

This spectrum supplies exact linear modes for graph diffusion or graph-wave models. Any nonlinear dynamics on Q7 should be compared with these linear modes and tested for graph-automorphism invariance.

## 9. What is and is not established

Established exactly: 128 binary vertices, 448 edges, 2187 faces, the face vector, ternary face encoding, fibre sizes, incidence counts and Euler identities.

Not established: that the cube is a physical model of vacuum, that the ternary mapping is a law of nature, that a natural or archaeological structure physically implements Q7, or that a particular face or vertex has a unique physical interpretation.

The mapping is a mathematically exact model candidate. Its physical meaning remains open.
