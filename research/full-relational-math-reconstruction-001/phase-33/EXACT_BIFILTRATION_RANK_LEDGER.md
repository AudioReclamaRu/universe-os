# Phase 33 — exact global bifiltration rank ledger

## Objective

Phase 33 turns a completed Phase 30 rectangular filtration and a completed
Phase 32 bifiltration-square result into one exact, machine-readable rank
ledger. It verifies finite two-dimensional telescoping identities for ranks,
quotient increments `q`, mixed overlaps `omega` and their degree-resolved
profile refinements. It consumes completed upstream results; it does not
rebuild the FTI catalogue, recompute Phase 32 intersections, introduce floating
point arithmetic, or extrapolate a finite table into an infinite series.

## Reused sources

- `../phase-30/relation_filtration.py` — actual cells, `relation_space_dimension`,
  `new_quotient_dimension`, `rank_by_total_word_degree` and
  `new_quotient_rank_by_total_word_degree`.
- `../phase-31/basis_transitions.py` — exact sparse-polynomial and matrix
  conventions reused indirectly through Phase 32 output.
- `../phase-32/bifiltration_operators.py` — unit-square dimensions and
  `mixed_overlap.complement_basis` entries with exact degree metadata.
- `../phase-29/trace_ideal_closure.py` — `_paired`, `_integer`, `_fraction`,
  `_fraction_report` and sparse trace-polynomial parsing conventions.

The bounded convenience wrapper explicitly calls Phase 30, Phase 31 and Phase 32
before invoking the main analyzer. The main analyzer never calls those stages.

## Definitions consumed from upstream

For every actual Phase 30 cell `(L,D)`:

- `r[L,D] = relation_space_dimension`;
- `q[L,D] = new_quotient_dimension` (finite predecessor-union quotient);
- for interior cells `L>=2, D>=1`, `omega[L,D]` is the cardinality of the
  Phase 32 `mixed_overlap.complement_basis`, independently rechecked against
  the reported `mixed_overlap_omega`, intersection, union and rank difference;
- `delta[L,D] = q[L,D] - omega[L,D]`.

The analyzer re-reads exact degree metadata for every supplied Phase 30 basis
vector/direction and every Phase 32 complement vector. A vector whose exact
trace polynomial mixes total matrix-word degrees, or whose declared degree
disagrees with the recomputed degree, returns
`unresolved_nonhomogeneous_basis_vector` or
`unresolved_basis_degree_metadata_mismatch` with the offending basis ID. No
coercion into a degree bucket is performed.

## Boundary conventions

- `r[0,D] = 0` and `r[L,-1] = 0` are **formal zero-boundary conventions only**.
  They are used inside finite-difference formulas and are never emitted as
  computed Phase 30 cells.
- `q[1,0] = r[1,0]`.
- `q[L,0] = r[L,0] - r[L-1,0]` for `L>1`.
- `q[1,D] = r[1,D] - r[1,D-1]` for `D>0`.
- `omega = 0` on `L=1` or `D=0` solely because no Phase 32 unit square exists
  there; the ledger labels this source `boundary_convention_zero`.
- Every emitted ledger row has `actual_phase30_cell: true`; the result reports
  `boundary_conventions.no_fabricated_cells: true`.

The analyzer also rejects a grid whose minimum cell is not `(1,0)`, because the
prefix identity would otherwise require invented cells.

## Exact identities

For every interior cell:

```text
delta[L,D] = r[L,D] - r[L-1,D] - r[L,D-1] + r[L-1,D-1]
           = q[L,D] - omega[L,D].
```

Prefix endpoint `(L,D)`:

```text
r[L,D] = sum_{i=1..L, j=0..D} (q[i,j] - omega[i,j]).
```

Arbitrary subrectangle `[a,b] x [c,d]`:

```text
sum_{i=a..b, j=c..d} (q[i,j] - omega[i,j])
  = r[b,d] - r[a-1,d] - r[b,c-1] + r[a-1,c-1],
```

with formal zero used only when an index falls outside the actual domain.

Row and column accumulations reconcile with rank edge differences:

```text
sum_{j=0..D} delta[L,j] = r[L,D] - r[L-1,D],
sum_{i=1..L} delta[i,D] = r[L,D] - r[L,D-1].
```

Global totals over the supplied grid:

```text
sum q - sum omega = sum delta = r[max_L,max_D].
```

`sum q` is reported strictly as the sum of finite bounded quotient increments.
It is not described as a set of infinite ideal generators.

## Degree-resolved ledger

For every degree `k` appearing in the supplied profiles:

- `delta[L,D,k] = q[L,D,k] - omega[L,D,k]`;
- interior: compare with
  `r[L,D,k] - r[L-1,D,k] - r[L,D-1,k] + r[L-1,D-1,k]`;
- axes: compare the one-sided rank profile difference with `q` and use the
  formal zero omega profile;
- prefix and subrectangle certificates carry both aggregate and by-degree sums;
- degree totals satisfy
  `sum_k q_k = sum q`, `sum_k omega_k = sum omega` and
  `sum_k delta_k = terminal rank profile`;
- Phase 30 predecessor-union degree profiles are additionally reconciled with
  `r_left + r_bottom - r_source - omega` on interior squares.

All rank and profile counts use integers encoded as paired binary/ternary
strings. Exact rational reports use paired numerator/denominator objects; a
canonical `1/2` example is present in the output. No float tolerance is used.

## Algorithms and caps

1. Index and validate the Phase 30 cells, degree profiles and homogeneity
   metadata; duplicates, nonrectangular grids and non-origin grids are
   unresolved.
2. Index and validate Phase 32 squares, dimensions, boundary cells, complement
   cardinality and exact dimension identities; mismatches are unresolved.
3. Build the cell ledger, degree profiles, prefix certificates, row/column
   accumulations and exact totals.
4. Check rectangles. Small grids are enumerated exhaustively. Larger grids use
   the selected-rectangle API plus six deterministic corner rectangles; no
   sampling or randomness is used.

Documented defaults:

- `max_rectangle_checks = 4096`;
- `max_cells = 256`;
- `max_squares = 256`;
- `max_degree_vector_checks = 4096`.

When exhaustive rectangle enumeration exceeds `max_rectangle_checks`, the
overall status is `unresolved_rectangle_cap`, `exhaustive_checks` is empty and
only deterministic corner certificates are reported. That is never presented as
exhaustive completion. Other caps return `unresolved_cell_cap`,
`unresolved_square_cap` or `unresolved_degree_vector_cap`. Invalid cap values
are rejected by exact integer parsing.

## Public API

- `analyze_exact_bifiltration_rank_ledger(filtration_result, bifiltration_result, *, ...)`
  — main staged analyzer.
- `analyze_bounded_exact_bifiltration_rank_ledger(filtration_options, *, ...)`
  — explicit opt-in wrapper that runs Phase 30, Phase 31 and Phase 32 first.
- `check_rectangle(analysis, a, b, c, d)` — validates one selected
  subrectangle against a returned ledger.

## Finite results on the recomputed small physical grid

The Phase 32 small grid (`dimension=2`, `generator_count=2`,
`max_substitution_word_length=2`, `max_multiplier_trace_word_length=1`,
`max_multiplier_total_word_degree=1`) was recomputed in this session. The ledger
recovers:

| Cell | r | q | omega | delta |
|---|---:|---:|---:|---:|
| `(1,0)` | 4 | 4 | 0 | 4 |
| `(1,1)` | 12 | 8 | 0 | 8 |
| `(2,0)` | 41 | 37 | 0 | 37 |
| `(2,1)` | 120 | 74 | 3 | 71 |

The single interior square has predecessor intersection dimension 7, so
`omega = 7 - 4 = 3` and `delta = 74 - 3 = 71`, matching the mixed rank
difference `120 - 12 - 41 + 4`. Exact totals are `sum q = 123`,
`sum omega = 3`, `sum delta = 120 = r[2,1]`.

Degree totals are `q = {3:4, 4:17, 5:32, 6:42, 7:28}`,
`omega = {4:3}`, and
`delta = terminal rank = {3:4, 4:14, 5:32, 6:42, 7:28}`.

A local two-degree synthetic control exercises `omega=1`, `q=0` and
`delta=-1` at `(2,1)` with a non-integer rational coordinate `1/2` in its
southwest basis vector. It verifies that negative degree-resolved rank
differences are allowed and that the degree profiles still telescope exactly.

## Tests and reproducible commands

From `research/full-relational-math-reconstruction-001/phase-33`:

~~~powershell
$env:OPENBLAS_NUM_THREADS='1'
& C:\Python314\python.exe -m unittest discover -v -p "test_*.py"
~~~

A local run after the final source edits completed with **19 tests passed**. The
tests cover the recomputed physical grid, all local/prefix/subrectangle/row/
column identities in aggregate and by degree, exact totals, boundary formalisms,
nonhomogeneous vectors with offending IDs, missing/duplicate/nonrectangular and
mismatched sources, every cap, paired integer and exact rational handling,
determinism, malformed inputs, the rectangle query API, the bounded wrapper,
and corner certificates under a cap.

## Files

- `bifiltration_rank_ledger.py` — staged and bounded APIs plus rectangle query.
- `test_bifiltration_rank_ledger.py` — 19 standard-library tests.
- `EXACT_BIFILTRATION_RANK_LEDGER.md` — this report.

No README, workflow, upstream phase source, legacy file, PR, git index, commit
or push was touched by this phase.

## Epistemic boundary

These are exact finite-dimensional linear-algebra statements for the declared
completed grid. They do not prove an infinite Hilbert series, a universal
recurrence, global distributivity, stabilization beyond the searched window, or
minimal generators of the infinite T-ideal. They also make no physical or
archaeological mechanism claim.
