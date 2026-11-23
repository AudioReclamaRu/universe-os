"""Scalable exact affine-IFS conjugacy via fixed-point frames and bipartite matching.

This is a Phase 17 extension to Phase 16. It avoids enumerating every map
permutation when each affine map has a unique fixed point and those points
span the ambient affine space.
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
from pathlib import Path

PHASE16 = Path(__file__).resolve().parent.parent / "phase-16"
if str(PHASE16) not in sys.path:
    sys.path.insert(0, str(PHASE16))

import affine_ifs_conjugacy as core  # exact field operations and input validation

Z = core.Z
O = core.O


def _identity_minus(matrix, d):
    n = len(matrix)
    return [[core.sub(O if i == j else Z, matrix[i][j]) for j in range(n)] for i in range(n)]


def _fixed_points(maps, n, d):
    points = []
    for item in maps:
        matrix = _identity_minus(item["matrix"], d)
        status, point, _rank = core._solve(matrix, item["translation"], n, d)
        if status != "unique":
            return None, "map_without_unique_fixed_point"
        points.append(point)
    return points, None


def _difference_frame(points, indices, n, d):
    """Return the d-by-d matrix whose columns are x_i-x_0, i=1..d."""
    anchor = points[indices[0]]
    return [[core.sub(points[indices[j + 1]][r], anchor[r]) for j in range(n)] for r in range(n)]


def _first_affine_frame(points, n, d):
    for indices in itertools.combinations(range(len(points)), n + 1):
        frame = _difference_frame(points, indices, n, d)
        if not core.zero(core._det(frame, d)):
            return indices, frame
    return None, None


def _affine_map_from_frames(source_points, source_indices, target_points, target_indices, n, d):
    X = _difference_frame(source_points, source_indices, n, d)
    Y = _difference_frame(target_points, target_indices, n, d)
    if core.zero(core._det(Y, d)):
        return None
    P = core._mm(Y, core._inv(X, d), d)
    if core.zero(core._det(P, d)):
        return None
    x0 = source_points[source_indices[0]]
    y0 = target_points[target_indices[0]]
    t = [core.sub(y, px) for y, px in zip(y0, core._mv(P, x0, d))]
    return P, t


def _map_compatibility(source_maps, target_maps, source_points, target_points, P, t, n, d):
    """Candidate edge i->j iff fixed point and linear map both transform exactly."""
    candidates = []
    for i, source in enumerate(source_maps):
        transformed_point = [core.add(a, b) for a, b in zip(core._mv(P, source_points[i], d), t)]
        row = []
        for j, target in enumerate(target_maps):
            if transformed_point != target_points[j]:
                continue
            if core._mm(P, source["matrix"], d) != core._mm(target["matrix"], P, d):
                continue
            row.append(j)
        candidates.append(row)
    return candidates


def _perfect_matching(candidates, target_count):
    """Return a deterministic source->target perfect matching, or None."""
    order = sorted(range(len(candidates)), key=lambda i: (len(candidates[i]), i))
    target_to_source = [-1] * target_count

    def augment(source_i, seen):
        for target_j in candidates[source_i]:
            if seen[target_j]:
                continue
            seen[target_j] = True
            previous = target_to_source[target_j]
            if previous == -1 or augment(previous, seen):
                target_to_source[target_j] = source_i
                return True
        return False

    for source_i in order:
        if not candidates[source_i] or not augment(source_i, [False] * target_count):
            return None
    source_to_target = [-1] * len(candidates)
    for target_j, source_i in enumerate(target_to_source):
        if source_i >= 0:
            source_to_target[source_i] = target_j
    return source_to_target if all(j >= 0 for j in source_to_target) else None


def compare_ifs_pair_scalable(source, target, max_target_frames=250000):
    n, d, source_coordinates, source_maps = core._parse(source)
    m, e, target_coordinates, target_maps = core._parse(target)
    if n != m:
        return {"status": "dimension_mismatch", "source_dimension": core.paired(n), "target_dimension": core.paired(m)}
    if d != e:
        return {"status": "quadratic_field_mismatch", "source_field": f"Q(√{d})", "target_field": f"Q(√{e})"}
    if len(source_maps) != len(target_maps):
        return {"status": "map_count_mismatch", "source_map_count": core.paired(len(source_maps)), "target_map_count": core.paired(len(target_maps))}
    if isinstance(max_target_frames, bool) or not isinstance(max_target_frames, int) or max_target_frames < 1:
        raise ValueError("max_target_frames must be a positive integer")

    source_points, source_error = _fixed_points(source_maps, n, d)
    target_points, target_error = _fixed_points(target_maps, n, d)
    if source_error or target_error:
        return {"status": "unique_fixed_point_method_not_applicable", "reason": source_error or target_error,
                "interpretation": "At least one IFS map has no unique fixed point in the declared exact field; this method is inconclusive, not a negative conjugacy result."}

    source_frame_indices, source_frame = _first_affine_frame(source_points, n, d)
    if source_frame_indices is None:
        return {"status": "source_fixed_points_do_not_span_ambient_space",
                "interpretation": "The source fixed-point cloud has affine rank below the ambient dimension. The frame method is inconclusive; no non-conjugacy is inferred."}

    total_frames = 1
    for k in range(n + 1):
        total_frames *= len(target_points) - k
    tested = 0
    frame_iter = itertools.permutations(range(len(target_points)), n + 1)
    for target_frame_indices in itertools.islice(frame_iter, max_target_frames):
        tested += 1
        if core.zero(core._det(_difference_frame(target_points, target_frame_indices, n, d), d)):
            continue
        transform = _affine_map_from_frames(source_points, source_frame_indices,
                                            target_points, target_frame_indices, n, d)
        if transform is None:
            continue
        P, t = transform
        candidates = _map_compatibility(source_maps, target_maps, source_points,
                                        target_points, P, t, n, d)
        permutation = _perfect_matching(candidates, len(target_maps))
        if permutation is None:
            continue
        if not core._verify(source_maps, target_maps, permutation, P, t, d):
            raise ArithmeticError("independent exact conjugacy verification failed")
        det = core._det(P, d)
        return {
            "status": "affine_conjugacy_verified",
            "source_coordinate_system": source_coordinates,
            "target_coordinate_system": target_coordinates,
            "exact_field": f"Q(√{d})",
            "affine_coordinate_change": {
                "convention": "y = P*x + t",
                "matrix_P": [[core.fmt(v) for v in row] for row in P],
                "translation_t": [core.fmt(v) for v in t],
                "determinant_P": core.fmt(det),
            },
            "map_permutation_target_index_for_each_source": [core.paired(j) for j in permutation],
            "fixed_point_frame": {
                "source_anchor_map_indices": [core.paired(i) for i in source_frame_indices],
                "target_anchor_map_indices": [core.paired(i) for i in target_frame_indices],
            },
            "search": {
                "target_frames_tested": core.paired(tested),
                "total_ordered_target_frames": core.paired(total_frames),
                "frame_search_complete": tested == total_frames,
                "stopped_on_verified_match": True,
                "map_permutation_enumeration": False,
            },
            "verification": "The affine map sends the full fixed-point multiset to the target, each source linear part is exactly conjugate to its assigned target linear part, and every original affine map equation was independently verified.",
            "interpretation": "Structural equivalence only. No physical origin, generation history or causal mechanism is inferred.",
        }

    complete = tested == total_frames
    return {
        "status": "no_affine_conjugacy_found" if complete else "target_frame_search_limit_reached",
        "source_coordinate_system": source_coordinates,
        "target_coordinate_system": target_coordinates,
        "exact_field": f"Q(√{d})",
        "search": {
            "target_frames_tested": core.paired(tested),
            "total_ordered_target_frames": core.paired(total_frames),
            "frame_search_complete": complete,
            "map_permutation_enumeration": False,
        },
        "interpretation": "No affine conjugacy exists if and only if the complete target-frame search was exhausted. A capped search is unresolved, not negative.",
    }


def analyze_payload(payload):
    pairs = payload.get("pairs", [])
    if not isinstance(pairs, list) or not pairs:
        raise ValueError("at least one source/target IFS pair is required")
    results = [{"name": p.get("name", "unnamed_pair"),
                **compare_ifs_pair_scalable(p["source"], p["target"],
                                            int(p.get("max_target_frames", 250000)))}
               for p in pairs]
    return {
        "schema": "universe.ifs-affine-conjugacy-scalable.v1",
        "pair_count": core.paired(len(results)),
        "results": results,
        "method": "Exact fixed-point affine-frame enumeration followed by a bipartite perfect-matching test; no factorial map-permutation enumeration.",
        "scope": "Dimensions 1–3 over a common squarefree real quadratic field. Requires one unique fixed point per map and a source fixed-point cloud spanning the ambient affine space.",
        "global_guard": "A verified affine conjugacy is mathematical structural equivalence, not empirical evidence of common physical origin or causal transmission.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, default=Path("affine_ifs_scalable_matching.json"))
    args = parser.parse_args()
    result = analyze_payload(json.loads(args.input.read_text(encoding="utf-8")))
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
