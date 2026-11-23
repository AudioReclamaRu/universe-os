"""Adaptive affine-IFS conjugacy: fixed-point frames, then full relational graph."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PHASE16 = ROOT / "phase-16"
PHASE17 = ROOT / "phase-17"
PHASE22 = ROOT / "phase-22"
for path in (PHASE16, PHASE17, PHASE22):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from affine_ifs_conjugacy import paired
from affine_ifs_scalable_matching import compare_ifs_pair_scalable
from affine_ifs_relational_graph import compare_ifs_pair_relational_graph


FALLBACK_STATUSES = {
    "unique_fixed_point_method_not_applicable",
    "source_fixed_points_do_not_span_ambient_space",
}
TERMINAL_INPUT_STATUSES = {
    "dimension_mismatch",
    "quadratic_field_mismatch",
    "map_count_mismatch",
}
UNRESOLVED_FRAME_STATUS = "target_frame_search_limit_reached"


def compare_ifs_pair_adaptive(
    source,
    target,
    max_target_frames=250000,
    max_graph_nodes=250000,
    max_candidate_isomorphisms=100000,
):
    """Use fixed-point frames first, then exact whole-family relational graph search.

    A capped Phase 17 frame search remains unresolved and is not silently
    reinterpreted as another search. The Phase 22 route is used only when the
    fixed-point-frame assumptions do not hold.
    """
    for value, name in (
        (max_target_frames, "max_target_frames"),
        (max_graph_nodes, "max_graph_nodes"),
        (max_candidate_isomorphisms, "max_candidate_isomorphisms"),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError(f"{name} must be a positive integer")

    frame_result = compare_ifs_pair_scalable(
        source, target, max_target_frames=max_target_frames
    )
    frame_status = frame_result["status"]
    attempts = [{
        "method": "phase17_exact_fixed_point_frames",
        "status": frame_status,
        "result": frame_result,
    }]

    if frame_status in FALLBACK_STATUSES:
        relational_result = compare_ifs_pair_relational_graph(
            source,
            target,
            max_graph_nodes=max_graph_nodes,
            max_candidate_isomorphisms=max_candidate_isomorphisms,
        )
        method = "phase22_edge_labelled_relational_graph_plus_exact_affine_solver"
        attempts.append({
            "method": method,
            "trigger": frame_status,
            "status": relational_result["status"],
            "result": relational_result,
        })
        selected_method = method
        final_result = relational_result
        decision = (
            "Phase 17's fixed-point-frame assumptions did not hold. "
            "Phase 22 matched exact vertex colours and every directed pairwise "
            "trace-word edge under one map bijection, then solved and independently "
            "verified the complete affine equations."
        )
    else:
        selected_method = "phase17_exact_fixed_point_frames"
        final_result = frame_result
        if frame_status in TERMINAL_INPUT_STATUSES:
            decision = "Input mismatch; no fallback was attempted."
        elif frame_status == UNRESOLVED_FRAME_STATUS:
            decision = (
                "The frame search was capped. The outcome remains unresolved; "
                "no fallback was run and no negative conclusion was drawn."
            )
        else:
            decision = (
                "The fixed-point-frame method returned a verified witness "
                "or a complete result under its applicability assumptions."
            )

    return {
        "schema": "universe.affine-ifs-adaptive-conjugacy.v4",
        "selected_method": selected_method,
        "status": final_result["status"],
        "decision": decision,
        "attempt_count": paired(len(attempts)),
        "attempts": attempts,
        "final_result": final_result,
        "method_order": [
            "phase17_exact_fixed_point_frames",
            "phase22_edge_labelled_relational_graph_plus_exact_affine_solver",
        ],
        "global_guard": (
            "A verified affine conjugacy is mathematical structural equivalence only. "
            "It does not establish common physical origin, historical direction, "
            "energy transfer, or causal coupling."
        ),
    }


def analyze_payload(payload):
    pairs = payload.get("pairs", [])
    if not isinstance(pairs, list) or not pairs:
        raise ValueError("at least one source/target IFS pair is required")
    results = []
    for item in pairs:
        results.append({
            "name": item.get("name", "unnamed_pair"),
            **compare_ifs_pair_adaptive(
                item["source"],
                item["target"],
                max_target_frames=int(item.get("max_target_frames", 250000)),
                max_graph_nodes=int(item.get("max_graph_nodes", 250000)),
                max_candidate_isomorphisms=int(
                    item.get("max_candidate_isomorphisms", 100000)
                ),
            ),
        })
    return {
        "schema": "universe.affine-ifs-adaptive-conjugacy.batch.v4",
        "pair_count": paired(len(results)),
        "results": results,
        "method_policy": (
            "Fixed-point frames first. If their explicit applicability assumptions "
            "fail, use exact vertex/edge-labelled relational graph isomorphism "
            "before solving complete affine map equations. Search caps remain unresolved."
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument(
        "--output", type=Path,
        default=Path("adaptive_affine_ifs_conjugacy.json")
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
