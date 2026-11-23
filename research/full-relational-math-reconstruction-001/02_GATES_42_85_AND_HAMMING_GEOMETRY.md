# 02 — Gates 42/85, division by three and Hamming geometry

## 1. Exact quotient-and-remainder pair

Start with:

\[
2^7=128.
\]

Division by three gives:

\[
\frac{128}{3}=42+\frac23,
\qquad
128=3\cdot42+2.
\]

Therefore:

\[
\left\lfloor\frac{2^7}{3}\right\rfloor=42,
\qquad
2^7\bmod3=2.
\]

Double the binary space:

\[
2\cdot128=256=2^8.
\]

Then:

\[
\frac{256}{3}=85+\frac13,
\qquad
256=3\cdot85+1.
\]

Therefore:

\[
\left\lfloor\frac{2^8}{3}\right\rfloor=85,
\qquad
2^8\bmod3=1.
\]

The gates have the exact relation:

\[
85=2\cdot42+1.
\]

The remainders complement one another:

\[
2+1=3.
\]

This is exact integer arithmetic.

## 2. Balanced partitions and zero-based boundaries

The 128 integer-indexed vertices split into three consecutive groups whose sizes differ by at most one:

\[
128=42+43+43.
\]

For zero-based vertex indices 0 through 127:
- group 1: 0–41, size 42;
- group 2: 42–84, size 43;
- group 3: 85–127, size 43.

Thus 42 and 85 are the boundaries at which groups 2 and 3 begin. They are also actual vertex indices. A boundary and the size of the preceding group are related but must not be confused.

For the doubled 256-index space:

\[
256=85+85+86.
\]

## 3. Modular explanation

Since:

\[
2\equiv-1\pmod3,
\]

the residues of powers of two alternate:

\[
2^n\bmod3=
\begin{cases}
2,&n\text{ odd},\\
1,&n\text{ even}.
\end{cases}
\]

Therefore:

\[
2^7\bmod3=2,\qquad2^8\bmod3=1.
\]

## 4. Antipodal structure inside Q7

Write the gates as seven-bit binary strings:

\[
42=0101010_2,\qquad85=1010101_2.
\]

They are bitwise complements:

\[
42\oplus85=127=1111111_2.
\]

Their Hamming distance is:

\[
d_H(42,85)=\operatorname{popcount}(42\oplus85)=7.
\]

Seven is the maximum possible Hamming distance in Q7. The gates are antipodal vertices.

Their Hamming weights are 3 and 4, respectively.

## 5. Every vertex has complementary distances to the gates

For any seven-bit vertex i, because 85 is the bitwise complement of 42:

\[
d_H(i,42)+d_H(i,85)=7.
\]

A vertex is therefore at distance at most 3 from its nearer gate.

For distance d=0,1,2,3, the radius-d Hamming shells around the two gates do not overlap, because their centres are seven edges apart and 2d<7. The number of vertices at nearest-gate distance d is:

\[
n_d=2\binom7d.
\]

| Nearest-gate distance | Count |
|---:|---:|
| 0 | 2 |
| 1 | 14 |
| 2 | 42 |
| 3 | 70 |
| **Total** | **128** |

At distance 2, each individual gate has C(7,2)=21 vertices. Together the two disjoint shells contain 42 vertices:

\[
42=2\binom72.
\]

Thus 42 has two exact combinatorial roles in this model: the quotient floor(128/3), and the combined distance-2 shell count around the antipodal gate pair. These definitions are distinct; their correspondence is a research clue, not proof of a physical role.

## 6. Shortest paths between gates

Any shortest path from 42 to 85 must flip each of the seven bits exactly once. The seven flips can occur in any order:

\[
N_{\text{shortest paths}}=7!=5040.
\]

All 5040 paths have length 7. This is a combinatorial path count, not a physical flux count.

## 7. Neighbourhood and index-metric defect in legacy code

Q7-neighbours of 42 are obtained by XOR with one generator. Nodes 43 and 10 are both graph-neighbours:
- 43 = 42 XOR 1;
- 10 = 42 XOR 32.

Both have Hamming distance 1 from 42.

The legacy stress field uses ordinary integer-index distance:

\[
d_{42}(i)=|i-42|/128,\quad
d_{85}(i)=|i-85|/128,
\]

\[
g(i)=\exp[-8\min(d_{42}(i),d_{85}(i))].
\]

At node 43 the exponent is -0.0625, giving weight approximately 0.9394. At node 10 the exponent is -2, giving approximately 0.1353.

Equal Hamming neighbours therefore receive different weights. The current field is not a function of Q7 graph distance alone. Either the numerical-index metric needs its own explicit meaning, or a graph-invariant field must be implemented separately.

## 8. 42 as a gate versus 42 as observer-origin

The legacy integer GATE_42 is a node/index in Q7. The later project convention that 42 is associated with observer-origin or intention-origin is a separate semantic proposal. These must have separate identifiers and separate tests.

No arithmetic identity makes a node index into an observer, force, coordinate, radius or physical constant.

## 9. Exact identities versus interpretation

Exact: both quotient/remainder equations, gate recurrence, complementary residues, antipodality, maximum Hamming distance, nearest-gate shell distribution and 5040 shortest paths.

Open: whether these gates represent physical states; whether 42 has a special observer function; whether the 3:2 relation is implemented by Giza elements; whether gates have any measured natural counterpart.
