# Phase 32 — exact bifiltration operators and mixed predecessor overlap

## Objective

Phase 30 supplies the completed finite two-parameter filtration
\(R_{L,D}\) with its exact predecessor-union quotient dimension \(q_{L,D}\).
Phase 31 supplies canonical rational RREF bases and exact inclusion-coordinate
matrices. Phase 32 studies whether the two growth directions form a commutative
unit square and whether the predecessor overlap is larger than the common
southwest predecessor.

This phase does not regenerate the FTI catalog, does not introduce floating
point arithmetic, and does not extrapolate a finite table into an infinite
Hilbert series or universal recurrence.

## Consumed sources

- Phase 30: `../phase-30/relation_filtration.py` — completed filtration, basis entries, reported dimensions.
- Phase 31: `../phase-31/basis_transitions.py` — canonical RREF, inclusion maps, intersection kernel construction, matrix helpers.
- Phase 29: `../phase-29/trace_ideal_closure.py` — sparse trace-polynomial conventions, exact Fraction parsing, exact insertion and certificate utilities.

`bifiltration_operators.py` consumes a completed Phase 30 result and, optionally,
a completed Phase 31 result. If Phase 31 output is omitted, the same Phase 31
primitives are used to derive the edge maps from the Phase 30 bases. If Phase 31
output is supplied, every reported inclusion matrix is independently recomputed
and must agree entry-by-entry over \(\mathbb Q\).

## Mathematical contract

For an interior cell with \(L\ge 2\), \(D\ge 1\):

\[
C=R_{L-1,D-1},\qquad
A=R_{L-1,D},\qquad
B=R_{L,D-1},\qquad
R=R_{L,D},
\]

with \(C\subseteq A\cap B\). Phase 30 reports

\[
q_{L,D}=\dim R-\dim(A+B).
\]

Phase 32 computes the exact rational space \(A\cap B\), then a deterministic
complement of \(C\) inside it:

\[
\Omega_{L,D}=(A\cap B)/C,\qquad
\omega_{L,D}=\dim(A\cap B)-\dim C\ge 0.
\]

The reported complement vectors carry exact coordinates in the canonical bases
of \(A\), \(B\), and \(A\cap B\). Verification includes:

\[
\dim(A\cap B)=\dim C+\omega_{L,D},
\]

\[
\dim R=\dim A+\dim B-\dim C-\omega_{L,D}+q_{L,D},
\]

\[
\Delta_L\Delta_D r_{L,D}
=\dim R-\dim A-\dim B+\dim C
=q_{L,D}-\omega_{L,D}.
\]

A nonzero \(\omega\) is an explicit local correction. The implementation never
assumes \(A\cap B=C\).

## Sparse representation and matrix orientation

A trace polynomial is a sparse mapping from canonical trace-monomial tuples to
`fractions.Fraction` coefficients. Canonical bases are unique reduced
row-echelon bases for a lexicographic monomial order, inherited from Phase 31.

Matrices follow the existing Phase 31 orientation:

> rows are canonical source-basis vectors; columns are coordinates in the
> canonical target basis.

Thus the two compositions from \(C\) to \(R\) are:

\[
M_{C\to B}M_{B\to R}
\quad\text{and}\quad
M_{C\to A}M_{A\to R}.
\]

They are compared with the direct reconstruction \(M_{C\to R}\) entry-by-entry
over \(\mathbb Q\). Compatible shapes are checked before multiplication.

## Algorithm

1. Validate that Phase 30 is complete and that its cells form a full rectangular
   grid. Duplicate cells are rejected as invalid; missing cells and capped or
   partial sources return explicit unresolved statuses.
2. Canonicalize every cell basis with Phase 31's RREF and reconcile each rank
   with Phase 30.
3. Derive or verify the four edge maps needed by the unit square.
4. Construct \(A\cap B\) exactly by the Phase 31 kernel of \([A\mid -B]\), then
   verify its rank against Phase 30.
5. Insert the canonical \(C\) basis into an exact echelon basis, followed by the
   canonical intersection vectors. Accepted new pivots form the deterministic
   complement of \(C\) in \(A\cap B\). Acceptance order is the canonical
   intersection order, independent of input order.
6. Reconstruct every intersection vector in the canonical span of \(C\) plus the
   complement. Check the rank of the combined coordinates in \(A\cap B\) and the
   rank of the complement coordinates modulo \(C\).
7. Check commutativity, direct-map equality, all rank identities and the exact
   predecessor-union dimension.

## Boundary semantics

The Phase 30 grid starts at \((L,D)=(1,0)\). No missing cell is invented. Cells
with \(L=1\) or \(D=0\) are reported in `boundary_cells` with
`zero_subspace_injected: false`; they do not generate a square. A zero subspace
is not used as a substitute for a computed Phase 30 cell anywhere in this
implementation.

If an interior terminal cell lacks any of its four actual predecessor cells,
the result is unresolved. A non-rectangular cell set is unresolved; duplicate
cells and malformed field types are invalid and raise an exception. Introduced
caps `max_cells` and `max_squares` return explicit unresolved statuses rather
than silently truncating the analysis.

## Finite results on the small completed physical grid

The Phase 31-style small grid used for integration is:

- dimension \(d=2\);
- generator count 2;
- \(L=1,2\);
- \(D=0,1\);
- maximum multiplier trace-word length 1.

It contains one interior unit square with terminal cell \(R_{2,1}\). Exact
computed dimensions are:

| Space | Dimension |
|---|---:|
| \(C=R_{1,0}\) | 4 |
| \(A=R_{1,1}\) | 12 |
| \(B=R_{2,0}\) | 41 |
| \(R=R_{2,1}\) | 120 |
| \(A\cap B\) | 7 |
| \(A+B\) | 46 |
| \(q_{2,1}\) | 74 |
| \(\omega_{2,1}\) | 3 |
| \(\Delta_L\Delta_D r_{2,1}\) | 71 |

The rank difference reconciles exactly: \(71=74-3\). Both compositions from
\(R_{1,0}\) to \(R_{2,1}\) and the direct coordinate reconstruction are identical
over \(\mathbb Q\). The square has nonzero mixed overlap: the predecessor
intersection is three dimensions larger than the southwest predecessor.

These are finite vector-space statements for this declared bounded grid only.

## Synthetic exact-rational controls

The test suite includes homogeneous degree-two synthetic fixtures that use the
same sparse-polynomial conventions:

- **Nonzero overlap:** \(C=\operatorname{span}\{u\}\), \(A\cap B=\operatorname{span}\{m_{00}m_{00},m_{00}m_{01}\}\), with
  \(u=m_{00}m_{00}+\tfrac12 m_{00}m_{01}\). Then \(\dim C=1\),
  \(\dim(A\cap B)=2\), \(\omega=1\), \(\dim R=4\), \(q=0\), and
  \(\Delta_L\Delta_D r=-1=q-\omega\).
- **Zero overlap:** \(A\cap B=C\) exactly, with \(\omega=0\).
- **Non-integer rational coordinates:** the nonzero fixture's southwest basis
  vector has exact coordinates \([1,\tfrac12,0,0]\) in the terminal canonical
  basis; the same \(\tfrac12\) appears in both composed paths.

The synthetic fixtures exist to exercise cases that may not occur in a small
physical sample. They are algebraic controls, not claims about the physical
trace-identity filtration.

## Tests and reproducible commands

From `research/full-relational-math-reconstruction-001/phase-32`:

~~~powershell
$env:OPENBLAS_NUM_THREADS='1'
& C:\Python314\python.exe -m unittest discover -v -p "test_*.py"
~~~

A local run completed with **13 tests passed** for Phase 32. The tests cover:

1. exact commutativity on every unit square of the small completed grid;
2. equality of both composed paths with the direct source-to-terminal map;
3. a synthetic nonzero mixed-overlap fixture;
4. a synthetic zero mixed-overlap fixture;
5. complement independence and spanning in \((A\cap B)/C\);
6. all rank identities, including \(\Delta_L\Delta_D r=q-\omega\);
7. explicit boundary cells with no fabricated square;
8. missing, duplicate, non-rectangular and partial-source cases;
9. deterministic, input-order-independent canonical output;
10. exact non-integer rational coordinate coefficients;
11. malformed input, dimension mismatch and resource caps;
12. independent recomputation of supplied Phase 31 matrices;
13. agreement of the bounded convenience API with the staged API.

The full configured matrix is run with the same standard-library command in
each of `phase-16` through `phase-32`.

## Files

- `bifiltration_operators.py` — public staged and bounded APIs.
- `test_bifiltration_operators.py` — 13 standard-library tests.
- `EXACT_BIFILTRATION_OPERATORS_AND_MIXED_OVERLAP.md` — this report.
- Root `README.md` and `.github/workflows/ifs-exact-comparator-tests.yml` updated additively.

## Epistemic boundary

\(q_{L,D}\) is a finite predecessor-union quotient increment. \(\omega_{L,D}\)
is a local extra overlap inside the declared square. Neither result proves
global distributivity, stabilization beyond the searched grid, a universal
recurrence, a complete infinite Hilbert series, a minimal generating set of the
infinite T-ideal, or any physical mechanism.
