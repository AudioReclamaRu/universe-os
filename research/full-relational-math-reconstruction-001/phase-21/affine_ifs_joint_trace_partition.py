"""Joint pairwise trace invariants for exact affine-IFS map partitioning."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
P16 = ROOT / "phase-16"
P20 = ROOT / "phase-20"
for path in (P16, P20):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import affine_ifs_conjugacy as core
from affine_ifs_characteristic_partition import compare_ifs_pair_partitioned


TRACE_WORDS = (
    "tr(A_i A_j)",
    "tr(A_i^2 A_j)",
    "tr(A_i A_j^2)",
    "tr(A_i A_j A_i A_j)",
    "tr(A_i^2 A_j^2)",
    "tr([A_i,A_j]^2)",
)


def _trace(matrix):
    return sum_field([matrix[i][i] for i in range(len(matrix))])


def sum_field(values):
    total = core.Z
    for value in values:
        total = core.add(total, value)
    return total


def _matrix_subtract(left, right):
    return [
        [core.sub(left[i][j], right[i][j]) for j in range(len(left))]
        for i in range(len(left))
    ]


def _pair_relation_record(A, B, radical):
    A2 = core._mm(A, A, radical)
    B2 = core._mm(B, B, radical)
    AB = core._mm(A, B, radical)
    BA = core._mm(B, A, radical)
    A2B = core._mm(A2, B, radical)
    AB2 = core._mm(A, B2, radical)
    ABAB = core._mm(AB, AB, radical)
    A2B2 = core._mm(A2, B2, radical)
    commutator = _matrix_subtract(AB, BA)
    commutator_squared = core._mm(commutator, commutator, radical)
    return (
        _trace(AB),
        _trace(A2B),
        _trace(AB2),
        _trace(ABAB),
        _trace(A2B2),
        _trace(commutator_squared),
    )


def relational_trace_profiles(maps, radical):
    """Permutation-invariant per-map multisets of exact two-generator word traces.

    If one common invertible P simultaneously conjugates the entire map family,
    then for every source map i its multiset of pairwise word traces over all j
    equals the corresponding multiset for the paired target map.
    """
    matrices = [item["matrix"] for item in maps]
    profiles = []
    for A in matrices:
        records = [_pair_relation_record(A, B, radical) for B in matrices]
        profiles.append(tuple(sorted(records)))
    return profiles


def compare_ifs_pair_trace_partitioned(
    source,
    target,
    max_candidate_matchings=100000,
):
    n, d, source_coordinates, source_maps = core._parse(source)
    m, e, target_coordinates, target_maps = core._parse(target)

    if n != m:
        return {
            "status": "dimension_mismatch",
            "source_dimension": core.paired(n),
            "target_dimension": core.paired(m),
        }
    if d != e:
        return {
            "status": "quadratic_field_mismatch",
            "source_field": f"Q(√{d})",
            "target_field": f"Q(√{e})",
        }
    if len(source_maps) != len(target_maps):
        return {
            "status": "map_count_mismatch",
            "source_map_count": core.paired(len(source_maps)),
            "target_map_count": core.paired(len(target_maps)),
        }

    source_profiles = relational_trace_profiles(source_maps, d)
    target_profiles = relational_trace_profiles(target_maps, d)
    candidate_refinement = [
        [j for j, target_profile in enumerate(target_profiles)
         if source_profile == target_profile]
        for source_profile in source_profiles
    ]
    refined_edge_count = sum(len(row) for row in candidate_refinement)

    result = compare_ifs_pair_partitioned(
        source,
        target,
        max_candidate_matchings=max_candidate_matchings,
        candidate_refinement=candidate_refinement,
        refinement_name="exact_joint_pairwise_word-trace_profiles",
    )
    result["joint_relational_trace_filter"] = {
        "word_trace_invariants": list(TRACE_WORDS),
        "candidate_edges_after_relational_filter": core.paired(refined_edge_count),
        "source_profile_class_count": core.paired(len(set(source_profiles))),
        "target_profile_class_count": core.paired(len(set(target_profiles))),
        "profile_definition": (
            "For each map A_i, the sorted multiset over all A_j of the six exact "
            "trace words listed above. The multiset preserves map multiplicity "
            "but is invariant to map-label permutation."
        ),
        "logical_status": (
            "Necessary condition for one common simultaneous affine conjugacy; "
            "not a sufficient proof. Full affine equations and determinant remain decisive."
        ),
    }
    result["schema"] = "universe.ifs-joint-trace-partitioned-conjugacy.v1"
    result["source_coordinate_system"] = source_coordinates
    result["target_coordinate_system"] = target_coordinates
    return result


def analyze_payload(payload):
    pairs = payload.get("pairs", [])
    if not isinstance(pairs, list) or not pairs:
        raise ValueError("at least one source/target IFS pair is required")
    results = [
        {
            "name": item.get("name", "unnamed_pair"),
            **compare_ifs_pair_trace_partitioned(
                item["source"],
                item["target"],
                max_candidate_matchings=int(item.get("max_candidate_matchings", 100000)),
            ),
        }
        for item in pairs
    ]
    return {
        "schema": "universe.ifs-joint-trace-partitioned-batch.v1",
        "pair_count": core.paired(len(results)),
        "results": results,
        "global_guard": (
            "Joint trace profiles are exact necessary invariants under a common "
            "simultaneous conjugacy. They only prune map pairings; every surviving "
            "candidate must still pass the complete affine equations and invertibility check."
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument(
        "--output", type=Path,
        default=Path("affine_ifs_joint_trace_partition.json"),
    )
    args = parser.parse_args()
    result = analyze_payload(json.loads(args.input.read_text(encoding="utf-8")))
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
