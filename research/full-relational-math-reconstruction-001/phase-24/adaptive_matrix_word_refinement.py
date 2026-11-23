"""Adaptive exact matrix-word invariants for ambiguous affine-IFS graph classes.

Only vertices that remain ambiguous after the current exact colour partition
trigger higher-word calculations. Whole word tiers are atomic under an explicit
matrix-product budget. The filters are necessary, never sufficient.
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PHASE16 = ROOT / "phase-16"
PHASE21 = ROOT / "phase-21"
PHASE23 = ROOT / "phase-23"
for path in (PHASE16, PHASE21, PHASE23):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import affine_ifs_conjugacy as core
from affine_ifs_adaptive_color_refinement import refine_joint_directed_colours


BASELINE_CYCLIC_WORDS = frozenset({"01", "001", "011", "0101", "0011"})


def canonical_cyclic_word(word: str) -> str:
    if not isinstance(word, str) or not word or any(bit not in "01" for bit in word):
        raise ValueError("matrix word must be a nonempty string over {0,1}")
    return min(word[i:] + word[:i] for i in range(len(word)))


def matrix_word_tiers(max_word_length: int = 8, min_word_length: int = 5):
    """Return deterministic binary-necklace tiers, excluding Phase 21 words."""
    if isinstance(max_word_length, bool) or not isinstance(max_word_length, int):
        raise TypeError("max_word_length must be an integer")
    if isinstance(min_word_length, bool) or not isinstance(min_word_length, int):
        raise TypeError("min_word_length must be an integer")
    if min_word_length < 2 or max_word_length < min_word_length or max_word_length > 12:
        raise ValueError("word lengths must satisfy 2 <= min <= max <= 12")
    tiers = []
    for length in range(min_word_length, max_word_length + 1):
        words = set()
        for bits in itertools.product("01", repeat=length):
            word = "".join(bits)
            if "0" not in word or "1" not in word:
                continue
            canonical = canonical_cyclic_word(word)
            if canonical in BASELINE_CYCLIC_WORDS:
                continue
            words.add(canonical)
        if words:
            tiers.append({"length": length, "words": tuple(sorted(words))})
    return tiers


def trace_matrix_word(A, B, word: str, radical: int):
    """Compute tr(word(A,B)) exactly over the declared quadratic field."""
    canonical_cyclic_word(word)
    n = len(A)
    if n == 0 or len(B) != n or any(len(row) != n for row in A) or any(len(row) != n for row in B):
        raise ValueError("A and B must be nonempty square matrices of equal size")
    product = [[core.O if i == j else core.Z for j in range(n)] for i in range(n)]
    for bit in word:
        product = core._mm(product, A if bit == "0" else B, radical)
    return core.sumq([product[i][i] for i in range(n)])


def _profiles(edges):
    return [tuple(sorted(row)) for row in edges]


def _has_perfect_matching(candidates, target_count):
    owners = {}

    def augment(source, seen):
        for target in candidates[source]:
            if target in seen:
                continue
            seen.add(target)
            previous = owners.get(target)
            if previous is None or augment(previous, seen):
                owners[target] = source
                return True
        return False

    return all(augment(i, set()) for i in range(len(candidates))) and len(owners) == target_count


def _pair_indices(count, active):
    return [
        (i, j)
        for i in range(count)
        for j in range(count)
        if i in active or j in active
    ]


def _extend_edges(edges, matrices, active, words, radical):
    extended = [list(row) for row in edges]
    pairs = _pair_indices(len(matrices), active)
    for i, j in pairs:
        additions = tuple(
            trace_matrix_word(matrices[i], matrices[j], word, radical)
            for word in words
        )
        extended[i][j] = tuple(extended[i][j]) + additions
    return extended, len(pairs)


def _colour_refinement(
    source_characteristics,
    target_characteristics,
    source_edges,
    target_edges,
    prior_source_colours=None,
    prior_target_colours=None,
):
    source_profiles = _profiles(source_edges)
    target_profiles = _profiles(target_edges)
    if prior_source_colours is None:
        source_colours = [
            (source_characteristics[i], source_profiles[i])
            for i in range(len(source_edges))
        ]
        target_colours = [
            (target_characteristics[i], target_profiles[i])
            for i in range(len(target_edges))
        ]
    else:
        source_colours = [
            (source_characteristics[i], source_profiles[i], prior_source_colours[i])
            for i in range(len(source_edges))
        ]
        target_colours = [
            (target_characteristics[i], target_profiles[i], prior_target_colours[i])
            for i in range(len(target_edges))
        ]
    return refine_joint_directed_colours(
        source_colours, target_colours, source_edges, target_edges
    )


def _refinement_summary(result):
    return {
        "rounds": core.paired(result["refinement_rounds"]),
        "combined_colour_class_counts": [
            core.paired(value) for value in result["combined_colour_class_counts"]
        ],
        "candidate_edges_before": core.paired(result["candidate_edges_before_refinement"]),
        "candidate_edges_after": core.paired(result["candidate_edges_after_refinement"]),
        "candidate_edges_before_refinement": core.paired(result["candidate_edges_before_refinement"]),
        "candidate_edges_after_refinement": core.paired(result["candidate_edges_after_refinement"]),
        "stable": result["stable"],
    }


def refine_ambiguous_matrix_word_graph(
    source_matrices,
    target_matrices,
    source_characteristics,
    target_characteristics,
    source_base_edges,
    target_base_edges,
    radical: int,
    max_matrix_products: int = 250000,
    max_word_length: int = 8,
):
    """Adaptively append exact trace words and rerun joint directed refinement.

    The baseline edge labels are the six Phase 21 records. Each additional
    tier is computed only on ordered map pairs incident to currently ambiguous
    source/target vertices. A tier is all-or-nothing under the product budget.
    """
    if isinstance(max_matrix_products, bool) or not isinstance(max_matrix_products, int) or max_matrix_products < 1:
        raise ValueError("max_matrix_products must be a positive integer")
    tiers = matrix_word_tiers(max_word_length=max_word_length)
    n = len(source_matrices)
    if n == 0 or len(target_matrices) != n:
        raise ValueError("source and target matrix families must have the same positive size")
    if len(source_characteristics) != n or len(target_characteristics) != n:
        raise ValueError("characteristic-polynomial lists must match map count")
    if len(source_base_edges) != n or len(target_base_edges) != n:
        raise ValueError("edge-label matrices must match map count")
    if any(len(row) != n for row in source_base_edges + target_base_edges):
        raise ValueError("edge-label matrices must be square")

    source_edges = [list(row) for row in source_base_edges]
    target_edges = [list(row) for row in target_base_edges]
    used_products = 0
    used_evaluations = 0
    tier_reports = []
    refinement = _colour_refinement(
        source_characteristics, target_characteristics,
        source_edges, target_edges,
    )
    initial_candidate_edges = refinement["candidate_edges_before_refinement"]
    if not _has_perfect_matching(refinement["candidate_map_indices"], n):
        return _result(
            "no_compatible_initial_colour_bijection", source_edges, target_edges,
            refinement, tier_reports, used_products, used_evaluations,
            max_matrix_products, max_word_length, initial_candidate_edges,
        )

    initial_refinement = refinement
    source_colours = refinement["source_colours"]
    target_colours = refinement["target_colours"]
    expansion_status = "maximum_word_length_reached"
    if all(len(row) == 1 for row in refinement["candidate_map_indices"]):
        expansion_status = "not_needed_unique_candidate_correspondence"

    for tier in tiers:
        candidates = refinement["candidate_map_indices"]
        if not _has_perfect_matching(candidates, n):
            expansion_status = "no_compatible_colour_bijection"
            break
        ambiguous_source = {i for i, row in enumerate(candidates) if len(row) > 1}
        if not ambiguous_source:
            expansion_status = "not_needed_unique_candidate_correspondence"
            break
        target_degrees = [0] * n
        for row in candidates:
            for j in row:
                target_degrees[j] += 1
        ambiguous_target = {j for j, degree in enumerate(target_degrees) if degree > 1}
        source_pairs = _pair_indices(n, ambiguous_source)
        target_pairs = _pair_indices(n, ambiguous_target)
        words = tier["words"]
        matrix_products = (
            (len(source_pairs) + len(target_pairs))
            * sum(len(word) for word in words)
        )
        trace_evaluations = (len(source_pairs) + len(target_pairs)) * len(words)
        remaining = max_matrix_products - used_products
        if matrix_products > remaining:
            tier_reports.append({
                "length": core.paired(tier["length"]),
                "words": list(words),
                "word_count": core.paired(len(words)),
                "source_ambiguous_vertices": [core.paired(i) for i in sorted(ambiguous_source)],
                "target_ambiguous_vertices": [core.paired(i) for i in sorted(ambiguous_target)],
                "source_ordered_pairs": core.paired(len(source_pairs)),
                "target_ordered_pairs": core.paired(len(target_pairs)),
                "required_matrix_products": core.paired(matrix_products),
                "remaining_matrix_product_budget": core.paired(remaining),
                "applied": False,
                "reason": "whole_tier_exceeds_remaining_matrix_product_budget",
            })
            expansion_status = "matrix_product_budget_exhausted"
            break

        source_edges, source_pair_count = _extend_edges(
            source_edges, source_matrices, ambiguous_source, words, radical
        )
        target_edges, target_pair_count = _extend_edges(
            target_edges, target_matrices, ambiguous_target, words, radical
        )
        if source_pair_count != len(source_pairs) or target_pair_count != len(target_pairs):
            raise ArithmeticError("matrix-word pair accounting mismatch")
        used_products += matrix_products
        used_evaluations += trace_evaluations
        next_refinement = _colour_refinement(
            source_characteristics, target_characteristics,
            source_edges, target_edges,
            source_colours, target_colours,
        )
        if next_refinement["candidate_edges_before_refinement"] != refinement["candidate_edges_after_refinement"]:
            raise ArithmeticError("adding exact words merged a previously distinguished candidate partition")
        tier_reports.append({
            "length": core.paired(tier["length"]),
            "words": list(words),
            "word_count": core.paired(len(words)),
            "source_ambiguous_vertices": [core.paired(i) for i in sorted(ambiguous_source)],
            "target_ambiguous_vertices": [core.paired(i) for i in sorted(ambiguous_target)],
            "source_ordered_pairs": core.paired(source_pair_count),
            "target_ordered_pairs": core.paired(target_pair_count),
            "matrix_products": core.paired(matrix_products),
            "trace_evaluations": core.paired(trace_evaluations),
            "candidate_edges_before": core.paired(refinement["candidate_edges_after_refinement"]),
            "candidate_edges_after": core.paired(next_refinement["candidate_edges_after_refinement"]),
            "applied": True,
        })
        refinement = next_refinement
        source_colours = refinement["source_colours"]
        target_colours = refinement["target_colours"]
        if not _has_perfect_matching(refinement["candidate_map_indices"], n):
            expansion_status = "no_compatible_colour_bijection"
            break
        if all(len(row) == 1 for row in refinement["candidate_map_indices"]):
            expansion_status = "unique_candidate_correspondence_after_word_refinement"
            break

    report = {
        "method": "phase24_adaptive_exact_binary_matrix_word_trace_refinement",
        "expansion_status": expansion_status,
        "baseline_word_trace_invariants": [
            "tr(A_i A_j)",
            "tr(A_i^2 A_j)",
            "tr(A_i A_j^2)",
            "tr(A_i A_j A_i A_j)",
            "tr(A_i^2 A_j^2)",
            "tr([A_i,A_j]^2)",
        ],
        "additional_word_tiers": tier_reports,
        "initial_colour_refinement": _refinement_summary(initial_refinement),
        "final_colour_refinement": _refinement_summary(refinement),
        "matrix_product_budget": {
            "limit": core.paired(max_matrix_products),
            "used": core.paired(used_products),
            "remaining": core.paired(max_matrix_products - used_products),
            "trace_evaluations": core.paired(used_evaluations),
            "accounting": (
                "One exact matrix product is charged for each letter in each "
                "evaluated word. This is a deterministic work proxy, not a "
                "wall-clock or coefficient-bit-complexity guarantee."
            ),
        },
        "max_word_length": core.paired(max_word_length),
        "logical_status": (
            "Every appended trace is invariant under a common simultaneous "
            "similarity. Adaptive word traces and stable colour refinement are "
            "necessary filters only; complete graph matching and exact affine "
            "equations remain decisive. A skipped whole tier is recorded, not "
            "partially applied."
        ),
    }
    return {
        "source_edges": source_edges,
        "target_edges": target_edges,
        "source_profiles": _profiles(source_edges),
        "target_profiles": _profiles(target_edges),
        "candidate_map_indices": refinement["candidate_map_indices"],
        "candidate_edges_before_refinement": initial_candidate_edges,
        "candidate_edges_after_refinement": refinement["candidate_edges_after_refinement"],
        "adaptive_matrix_word_refinement": report,
    }


def _result(status, source_edges, target_edges, refinement, tier_reports,
            used_products, used_evaluations, budget, max_word_length, initial_edges):
    report = {
        "method": "phase24_adaptive_exact_binary_matrix_word_trace_refinement",
        "expansion_status": status,
        "additional_word_tiers": tier_reports,
        "initial_colour_refinement": _refinement_summary(refinement),
        "final_colour_refinement": _refinement_summary(refinement),
        "matrix_product_budget": {
            "limit": core.paired(budget),
            "used": core.paired(used_products),
            "remaining": core.paired(budget - used_products),
            "trace_evaluations": core.paired(used_evaluations),
            "accounting": "One matrix product charged per letter in each exact word trace.",
        },
        "max_word_length": core.paired(max_word_length),
        "logical_status": (
            "No compatible initial colour bijection exists; this is a negative "
            "for the supplied exact vertex and edge labels."
        ),
    }
    return {
        "source_edges": source_edges,
        "target_edges": target_edges,
        "source_profiles": _profiles(source_edges),
        "target_profiles": _profiles(target_edges),
        "candidate_map_indices": refinement["candidate_map_indices"],
        "candidate_edges_before_refinement": initial_edges,
        "candidate_edges_after_refinement": refinement["candidate_edges_after_refinement"],
        "adaptive_matrix_word_refinement": report,
    }
