"""Exact characteristic-polynomial partitioning for affine IFS map correspondence."""
from __future__ import annotations

import argparse
import itertools
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
P16 = ROOT / "phase-16"
P18 = ROOT / "phase-18"
for path in (P16, P18):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import affine_ifs_conjugacy as core
from affine_ifs_underdetermined import (
    _build_system, _find_nonzero_determinant_assignment,
    _instantiate, _rref_affine, _solution_determinant_polynomial,
)


def characteristic_polynomial(matrix, radical):
    """Descending coefficients of det(lambda*I-A), exact for dimensions 1..3."""
    n = len(matrix)
    trace = sum_field([matrix[i][i] for i in range(n)])
    if n == 1:
        return (core.O, core.neg(trace))
    if n == 2:
        return (core.O, core.neg(trace), core._det(matrix, radical))
    if n == 3:
        square = core._mm(matrix, matrix, radical)
        trace_square = sum_field([square[i][i] for i in range(n)])
        second = core.div(
            core.sub(core.mul(trace, trace, radical), trace_square),
            (2, 0), radical,
        )
        return (core.O, core.neg(trace), second, core.neg(core._det(matrix, radical)))
    raise ValueError("dimension must be one, two or three")


def sum_field(values):
    total = core.Z
    for value in values:
        total = core.add(total, value)
    return total


def _candidate_graph(source_maps, target_maps, radical):
    src = [characteristic_polynomial(m["matrix"], radical) for m in source_maps]
    tgt = [characteristic_polynomial(m["matrix"], radical) for m in target_maps]
    candidates = [
        [j for j, signature in enumerate(tgt) if signature == source_sig]
        for source_sig in src
    ]
    return src, tgt, candidates


def _has_perfect_matching(candidates, source_indices, unavailable):
    owner = {}

    def augment(i, visited):
        for j in candidates[i]:
            if j in unavailable or j in visited:
                continue
            visited.add(j)
            old = owner.get(j)
            if old is None or augment(old, visited):
                owner[j] = i
                return True
        return False

    order = sorted(source_indices, key=lambda i: (
        sum(j not in unavailable for j in candidates[i]), i
    ))
    return all(augment(i, set()) for i in order)


def _iter_matchings(candidates):
    n = len(candidates)
    assignment = [-1] * n
    used = set()

    def visit(remaining):
        if not remaining:
            yield tuple(assignment)
            return
        i = min(remaining, key=lambda x: (
            sum(j not in used for j in candidates[x]), x
        ))
        for j in candidates[i]:
            if j in used:
                continue
            assignment[i] = j
            used.add(j)
            rest = [x for x in remaining if x != i]
            if _has_perfect_matching(candidates, rest, used):
                yield from visit(rest)
            used.remove(j)
            assignment[i] = -1

    yield from visit(list(range(n)))


def compare_ifs_pair_partitioned(source, target, max_candidate_matchings=100000):
    n, d, src_coords, src_maps = core._parse(source)
    m, e, tgt_coords, tgt_maps = core._parse(target)
    if n != m:
        return {"status": "dimension_mismatch",
                "source_dimension": core.paired(n), "target_dimension": core.paired(m)}
    if d != e:
        return {"status": "quadratic_field_mismatch",
                "source_field": f"Q(√{d})", "target_field": f"Q(√{e})"}
    if len(src_maps) != len(tgt_maps):
        return {"status": "map_count_mismatch",
                "source_map_count": core.paired(len(src_maps)),
                "target_map_count": core.paired(len(tgt_maps))}
    if (isinstance(max_candidate_matchings, bool) or
            not isinstance(max_candidate_matchings, int) or max_candidate_matchings < 1):
        raise ValueError("max_candidate_matchings must be a positive integer")

    src_sig, tgt_sig, candidates = _candidate_graph(src_maps, tgt_maps, d)
    edge_count = sum(map(len, candidates))
    unrestricted = math.factorial(len(src_maps))
    candidate_indices = [[core.paired(j) for j in row] for row in candidates]

    if any(not row for row in candidates) or not _has_perfect_matching(
        candidates, list(range(len(src_maps))), set()
    ):
        return {
            "status": "no_affine_conjugacy_found",
            "source_coordinate_system": src_coords,
            "target_coordinate_system": tgt_coords,
            "filter": "exact_characteristic_polynomial_of_each_linear_part",
            "candidate_edge_count": core.paired(edge_count),
            "unrestricted_permutation_count": core.paired(unrestricted),
            "candidate_map_indices": candidate_indices,
            "search_complete": True,
            "interpretation": (
                "The exact characteristic-polynomial candidate graph has no perfect "
                "matching. Similarity of each paired linear part is necessary for "
                "affine conjugacy, so no affine map bijection exists."
            ),
        }

    tested = 0
    affine_families = 0
    iterator = _iter_matchings(candidates)
    cap_reached = False
    for permutation in itertools.islice(iterator, max_candidate_matchings + 1):
        if tested == max_candidate_matchings:
            cap_reached = True
            break
        tested += 1
        rows, rhs = _build_system(src_maps, tgt_maps, permutation, n)
        status, particular, basis, rank = _rref_affine(rows, rhs, n*n+n, d)
        if status == "inconsistent":
            continue
        affine_families += 1
        nullity = len(basis)
        det_poly = _solution_determinant_polynomial(particular, basis, n, d)
        if not det_poly:
            continue
        assignment = _find_nonzero_determinant_assignment(det_poly, nullity, n, d)
        if assignment is None:
            raise ArithmeticError("nonzero determinant polynomial had no exact specialization")
        solution = _instantiate(particular, basis, assignment, d)
        P = [solution[r*n:(r+1)*n] for r in range(n)]
        t = solution[n*n:]
        determinant = core._det(P, d)
        if core.zero(determinant):
            raise ArithmeticError("constructed coordinate matrix is singular")
        if not core._verify(src_maps, tgt_maps, permutation, P, t, d):
            raise ArithmeticError("independent affine conjugacy verification failed")
        return {
            "status": "affine_conjugacy_verified",
            "source_coordinate_system": src_coords,
            "target_coordinate_system": tgt_coords,
            "exact_field": f"Q(√{d})",
            "filter": "exact_characteristic_polynomial_of_each_linear_part",
            "candidate_edge_count": core.paired(edge_count),
            "unrestricted_permutation_count": core.paired(unrestricted),
            "candidate_map_indices": candidate_indices,
            "affine_coordinate_change": {
                "convention": "y = P*x + t",
                "matrix_P": [[core.fmt(v) for v in row] for row in P],
                "translation_t": [core.fmt(v) for v in t],
                "determinant_P": core.fmt(determinant),
            },
            "map_permutation_target_index_for_each_source": [core.paired(j) for j in permutation],
            "linear_solution_family": {
                "rank": core.paired(rank),
                "free_parameter_count": core.paired(nullity),
                "parameter_assignment": [core.fmt(v) for v in assignment],
                "determinant_polynomial_term_count": core.paired(len(det_poly)),
            },
            "search": {
                "candidate_matchings_tested": core.paired(tested),
                "affine_families_solved": core.paired(affine_families),
                "search_complete": False,
                "stopped_on_verified_match": True,
                "candidate_matching_cap": core.paired(max_candidate_matchings),
            },
            "verification": "Every affine map equation and det(P) ≠ 0 were checked exactly.",
            "interpretation": (
                "The exact linear-part invariant filter removed impossible pairings; "
                "a remaining candidate produced a verified invertible affine conjugacy."
            ),
        }

    complete = not cap_reached
    return {
        "status": "candidate_matching_search_limit_reached" if cap_reached else "no_affine_conjugacy_found",
        "source_coordinate_system": src_coords,
        "target_coordinate_system": tgt_coords,
        "exact_field": f"Q(√{d})",
        "filter": "exact_characteristic_polynomial_of_each_linear_part",
        "candidate_edge_count": core.paired(edge_count),
        "unrestricted_permutation_count": core.paired(unrestricted),
        "candidate_map_indices": candidate_indices,
        "search": {
            "candidate_matchings_tested": core.paired(tested),
            "affine_families_solved": core.paired(affine_families),
            "search_complete": complete,
            "candidate_matching_cap": core.paired(max_candidate_matchings),
        },
        "interpretation": (
            "Candidate-matching search was capped; unresolved, not negative."
            if cap_reached else
            "All perfect matchings permitted by the exact characteristic-polynomial "
            "filter were examined; no invertible affine conjugacy was found."
        ),
    }


def analyze_payload(payload):
    pairs = payload.get("pairs", [])
    if not isinstance(pairs, list) or not pairs:
        raise ValueError("at least one source/target IFS pair is required")
    results = [
        {"name": item.get("name", "unnamed_pair"),
         **compare_ifs_pair_partitioned(
             item["source"], item["target"],
             int(item.get("max_candidate_matchings", 100000))
         )}
        for item in pairs
    ]
    return {
        "schema": "universe.ifs-characteristic-partitioned-conjugacy.v1",
        "pair_count": core.paired(len(results)),
        "results": results,
        "global_guard": (
            "Characteristic-polynomial equality is necessary, not sufficient, for "
            "similarity of linear parts. Every final affine witness is verified exactly."
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, default=Path("affine_ifs_partitioned_conjugacy.json"))
    args = parser.parse_args()
    result = analyze_payload(json.loads(args.input.read_text(encoding="utf-8")))
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
