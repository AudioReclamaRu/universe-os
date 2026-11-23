"""Adaptive exact matrix-word invariants for ambiguous affine-IFS graph classes.

Only vertices that remain ambiguous after the current exact colour partition
trigger higher-word calculations. Whole word tiers are atomic under an explicit
matrix-product budget. The filters are necessary, never sufficient.
"""
from __future__ import annotations

import itertools
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PHASE16 = ROOT / "phase-16"
PHASE21 = ROOT / "phase-21"
PHASE23 = ROOT / "phase-23"
PHASE25 = ROOT / "phase-25"
for path in (PHASE16, PHASE21, PHASE23, PHASE25):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import affine_ifs_conjugacy as core
from affine_ifs_adaptive_color_refinement import refine_joint_directed_colours
from trace_feature_dependencies import (
    BASELINE_WORDS,
    COMMUTATOR_IDENTITY,
    compress_phase21_edges,
    dependency_basis_from_edges,
    insert_feature,
)


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


def _append_retained_edge_features(edges, pair_values):
    extended = [list(row) for row in edges]
    for (i, j), values in pair_values.items():
        extended[i][j] = tuple(extended[i][j]) + tuple(values)
    return extended


def _initial_candidate_map(
    source_characteristics, target_characteristics, source_edges, target_edges
):
    source_profiles = _profiles(source_edges)
    target_profiles = _profiles(target_edges)
    return [
        [
            j for j in range(len(target_edges))
            if source_characteristics[i] == target_characteristics[j]
            and source_profiles[i] == target_profiles[j]
        ]
        for i in range(len(source_edges))
    ]


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

    source_edges = compress_phase21_edges(source_base_edges, radical)
    target_edges = compress_phase21_edges(target_base_edges, radical)
    initial_candidate_map_indices = _initial_candidate_map(
        source_characteristics, target_characteristics, source_edges, target_edges
    )
    applied_words = []
    used_products = 0
    used_evaluations = 0
    tier_reports = []
    refinement = _colour_refinement(
        source_characteristics, target_characteristics,
        source_edges, target_edges,
    )
    initial_candidate_edges = refinement["candidate_edges_before_refinement"]
    if sum(len(row) for row in initial_candidate_map_indices) != initial_candidate_edges:
        raise ArithmeticError("initial Phase 25 compression changed the Phase 22 candidate-edge count")
    if not _has_perfect_matching(refinement["candidate_map_indices"], n):
        return _result(
            "no_compatible_initial_colour_bijection", source_edges, target_edges,
            refinement, tier_reports, used_products, used_evaluations,
            max_matrix_products, max_word_length, initial_candidate_edges,
            initial_candidate_map_indices,
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

        basis, prior_dependencies = dependency_basis_from_edges(
            source_edges, target_edges,
            source_pairs, target_pairs,
            applied_words, radical,
        )
        candidate_values = {}
        source_values_by_word = {}
        target_values_by_word = {}
        for word in words:
            source_values = [
                trace_matrix_word(source_matrices[i], source_matrices[j], word, radical)
                for i, j in source_pairs
            ]
            target_values = [
                trace_matrix_word(target_matrices[i], target_matrices[j], word, radical)
                for i, j in target_pairs
            ]
            candidate_values[word] = source_values + target_values
            source_values_by_word[word] = dict(zip(source_pairs, source_values))
            target_values_by_word[word] = dict(zip(target_pairs, target_values))

        retained_words = []
        dependent_words = []
        for word in words:
            independent, relation = insert_feature(
                basis, f"trace:{word}", candidate_values[word], radical
            )
            if independent:
                retained_words.append(word)
            else:
                dependent_words.append(relation)

        source_append = {}
        target_append = {}
        for pair in source_pairs:
            values = tuple(source_values_by_word[word][pair] for word in retained_words)
            if values:
                source_append[pair] = values
        for pair in target_pairs:
            values = tuple(target_values_by_word[word][pair] for word in retained_words)
            if values:
                target_append[pair] = values
        source_edges = _append_retained_edge_features(source_edges, source_append)
        target_edges = _append_retained_edge_features(target_edges, target_append)
        source_pair_count = len(source_pairs)
        target_pair_count = len(target_pairs)
        used_products += matrix_products
        used_evaluations += trace_evaluations
        applied_words.extend(retained_words)
        next_refinement = _colour_refinement(
            source_characteristics, target_characteristics,
            source_edges, target_edges,
            source_colours, target_colours,
        )
        if next_refinement["candidate_edges_before_refinement"] > refinement["candidate_edges_after_refinement"]:
            raise ArithmeticError(
                "adding exact independent words merged a previously distinguished candidate partition"
            )

        tier_reports.append({
            "length": core.paired(tier["length"]),
            "words": list(words),
            "word_count": core.paired(len(words)),
            "tested_words": list(words),
            "retained_words": list(retained_words),
            "dependent_words": dependent_words,
            "prior_feature_dependencies": prior_dependencies,
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
        "method": "phase25_exact_dependency_reduced_adaptive_matrix_word_refinement",
        "expansion_status": expansion_status,
        "universal_trace_reductions": [
            {
                "identity": COMMUTATOR_IDENTITY["equation"],
                "removed_feature": COMMUTATOR_IDENTITY["left"],
                "status": "exact_universal_identity_checked_on_all_input_edges",
            }
        ],
        "retained_additional_words": list(applied_words),
        "baseline_word_trace_invariants": [
            "tr(A_i A_j)",
            "tr(A_i^2 A_j)",
            "tr(A_i A_j^2)",
            "tr(A_i A_j A_i A_j)",
            "tr(A_i^2 A_j^2)",
            "tr([A_i,A_j]^2) = 2*tr(A_i A_j A_i A_j) - 2*tr(A_i^2 A_j^2) [exactly reduced]",
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
            "Universal trace identities are removed exactly. Finite-comparison "
            "dependencies are detected with one shared exact coefficient vector "
            "over all active source and target ordered-pair rows; those dependent "
            "features are omitted only on that support. Candidate word evaluation "
            "is still charged to the matrix-product budget. Complete graph matching "
            "and exact affine equations remain decisive."
        ),
    }
    return {
        "source_edges": source_edges,
        "target_edges": target_edges,
        "source_profiles": _profiles(source_edges),
        "target_profiles": _profiles(target_edges),
        "candidate_map_indices": refinement["candidate_map_indices"],
        "initial_candidate_map_indices": initial_candidate_map_indices,
        "candidate_edges_before_refinement": initial_candidate_edges,
        "candidate_edges_after_refinement": refinement["candidate_edges_after_refinement"],
        "adaptive_matrix_word_refinement": report,
    }


def _result(status, source_edges, target_edges, refinement, tier_reports,
            used_products, used_evaluations, budget, max_word_length, initial_edges,
            initial_candidate_map_indices):
    report = {
        "method": "phase25_exact_dependency_reduced_adaptive_matrix_word_refinement",
        "expansion_status": status,
        "universal_trace_reductions": [
            {
                "identity": COMMUTATOR_IDENTITY["equation"],
                "removed_feature": COMMUTATOR_IDENTITY["left"],
                "status": "exact_universal_identity_checked_on_all_input_edges",
            }
        ],
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
        "initial_candidate_map_indices": initial_candidate_map_indices,
        "candidate_edges_before_refinement": initial_edges,
        "candidate_edges_after_refinement": refinement["candidate_edges_after_refinement"],
        "adaptive_matrix_word_refinement": report,
    }
