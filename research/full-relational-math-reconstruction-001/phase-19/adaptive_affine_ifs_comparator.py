"""Adaptive exact affine-IFS conjugacy: fixed-point frames first, affine-family fallback."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PHASE_ROOT = Path(__file__).resolve().parent.parent
PHASE16 = PHASE_ROOT / "phase-16"
PHASE17 = PHASE_ROOT / "phase-17"
PHASE18 = PHASE_ROOT / "phase-18"
for path in (PHASE16, PHASE17, PHASE18):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from affine_ifs_conjugacy import paired
from affine_ifs_scalable_matching import compare_ifs_pair_scalable
from affine_ifs_underdetermined import compare_ifs_pair


FALLBACK_STATUSES = {
    "unique_fixed_point_method_not_applicable",
    "source_fixed_points_do_not_span_ambient_space",
}

TERMINAL_INPUT_STATUSES = {
    "dimension_mismatch",
    "quadratic_field_mismatch",
    "map_count_mismatch",
}


def compare_ifs_pair_adaptive(
    source,
    target,
    max_target_frames=250000,
    max_permutations=100000,
):
    """Use the frame algorithm where complete; fall back only on inapplicability.

    A capped Phase 17 search remains unresolved. It is not silently reinterpreted
    by another method, and a complete Phase 17 negative result remains terminal.
    """
    if (isinstance(max_target_frames, bool) or
            not isinstance(max_target_frames, int) or max_target_frames < 1):
        raise ValueError("max_target_frames must be a positive integer")
    if (isinstance(max_permutations, bool) or
            not isinstance(max_permutations, int) or max_permutations < 1):
        raise ValueError("max_permutations must be a positive integer")

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
        fallback_result = compare_ifs_pair(
            source, target, max_permutations=max_permutations
        )
        attempts.append({
            "method": "phase18_exact_determinant_family",
            "trigger": frame_status,
            "status": fallback_result["status"],
            "result": fallback_result,
        })
        selected_method = "phase18_exact_determinant_family"
        final_result = fallback_result
        decision = (
            "Phase 17's fixed-point-frame assumptions did not hold; "
            "the full affine solution-family method was used."
        )
    else:
        selected_method = "phase17_exact_fixed_point_frames"
        final_result = frame_result
        if frame_status in TERMINAL_INPUT_STATUSES:
            decision = "Input mismatch; no fallback was attempted."
        elif frame_status == "target_frame_search_limit_reached":
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
        "schema": "universe.affine-ifs-adaptive-conjugacy.v1",
        "selected_method": selected_method,
        "status": final_result["status"],
        "decision": decision,
        "attempt_count": paired(len(attempts)),
        "attempts": attempts,
        "final_result": final_result,
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
                max_permutations=int(item.get("max_permutations", 100000)),
            ),
        })
    return {
        "schema": "universe.affine-ifs-adaptive-conjugacy.batch.v1",
        "pair_count": paired(len(results)),
        "results": results,
        "method_policy": (
            "Fixed-point frames first. Exact determinant-family fallback only when "
            "fixed-point assumptions are inapplicable. Search caps remain unresolved."
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
