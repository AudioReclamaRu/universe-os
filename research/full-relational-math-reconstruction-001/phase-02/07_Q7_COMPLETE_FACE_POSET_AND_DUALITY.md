# 07 — Q7: face poset, incidence, duality and symmetry

A geometric 7-cube has 2,187 nonempty geometric faces, including vertices and the whole cube:
\[
f_d=\binom7d2^{7-d},\quad (f_0,\ldots,f_7)=(128,448,672,560,280,84,14,1).
\]
The ordinary abstract face lattice also contains an empty bottom face, so has 2,188 elements. The CSV exports only the 2,187 geometric faces.

Face coordinates use - (fixed 0), 0 (free), + (fixed 1); dimension is the number of free coordinates.

## Inclusion and adjacency
An immediate cover frees one fixed coordinate. Counts by lower dimension are:
\[
(896,2688,3360,2240,840,168,14),\quad \text{total}=10,206.
\]
The formula is \(f_d(7-d)\). Adding the empty face contributes 128 more covers. All nonempty inclusion pairs including equality number \(\sum f_d3^d=5^7=78,125\); strict pairs: 75,938.

Two distinct d-faces are adjacent when they intersect in exactly one shared (d-1)-face. Counts for dimensions 0–7 are (0,2688,6720,6720,3360,840,84,0), total 20,412. Vertex adjacency is recorded separately as the 448 Q7 edges.

Each d-face contains \(2^d\) vertices, giving \(\sum f_d2^d=4^7=16,384\) face/vertex incidences. Every vertex lies in 128 nonempty faces; every edge lies in 64 faces, for 28,672 edge/face incidences.
\[
\chi(Q_7)=1,\qquad \chi(\partial Q_7)=2.
\]

## Polarity and relabelling
The polar dual of Q7 is the 7D cross-polytope, with \(f_d(Q_7)=f_{6-d}(Q_7^*)\) for proper faces. Its proper-face vector is (14,84,280,560,672,448,128).

The graph automorphism group is \(C_2^7\rtimes S_7\), order \(2^7 7!=645,120\). It preserves adjacency, Hamming distance, antipodality, spectra and incidence, but not decimal labels or absolute differences of labels.

42=0101010 and 85=1010101 are antipodes in standard binary order. Their images under any cube automorphism remain antipodal; the two-centre Hamming shell counts (2,14,42,70) remain fixed, while decimal vertex labels can change. The source gate field based on |i-42| and |i-85| is therefore encoding-dependent, not Q7-automorphism invariant.

The ternary sign reversal (- ↔ +, 0 fixed) is central reflection on the cube and preserves face dimensions/incidences. It is not a Möbius strip; that requires non-orientable gluing or an equivalent bundle construction.