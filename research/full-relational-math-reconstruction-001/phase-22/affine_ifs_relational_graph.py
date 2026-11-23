"""Exact relational graph isomorphism for simultaneous affine-IFS conjugacy."""
from __future__ import annotations

import argparse
import itertools
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PHASE16 = ROOT / "phase-16"
PHASE18 = ROOT / "phase-18"
PHASE20 = ROOT / "phase-20"
PHASE21 = ROOT / "phase-21"
PHASE23 = ROOT / "phase-23"
PHASE24 = ROOT / "phase-24"
for path in (PHASE16, PHASE18, PHASE20, PHASE21, PHASE23, PHASE24):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import affine_ifs_conjugacy as core
from affine_ifs_underdetermined import (
    _build_system,
    _find_nonzero_determinant_assignment,
    _instantiate,
    _rref_affine,
    _solution_determinant_polynomial,
)
from affine_ifs_characteristic_partition import characteristic_polynomial
from affine_ifs_joint_trace_partition import _pair_relation_record, TRACE_WORDS
from adaptive_matrix_word_refinement import refine_ambiguous_matrix_word_graph


def _has_perfect_matching(candidates, source_indices, unavailable_targets, target_count):
    target_owner = {}

    def augment(source_index, visited):
        for target_index in candidates[source_index]:
            if target_index in unavailable_targets or target_index in visited:
                continue
            visited.add(target_index)
            previous = target_owner.get(target_index)
            if previous is None or augment(previous, visited):
                target_owner[target_index] = source_index
                return True
        return False

    order = sorted(
        source_indices,
        key=lambda i: (
            sum(j not in unavailable_targets for j in candidates[i]),
            i,
        ),
    )
    return all(augment(i, set()) for i in order)


def _relational_graphs(source_maps, target_maps, radical):
    source_chars = [
        characteristic_polynomial(item["matrix"], radical)
        for item in source_maps
    ]
    target_chars = [
        characteristic_polynomial(item["matrix"], radical)
        for item in target_maps
    ]
    source_edges = [
        [_pair_relation_record(a["matrix"], b["matrix"], radical) for b in source_maps]
        for a in source_maps
    ]
    target_edges = [
        [_pair_relation_record(a["matrix"], b["matrix"], radical) for b in target_maps]
        for a in target_maps
    ]
    source_profiles = [tuple(sorted(row)) for row in source_edges]
    target_profiles = [tuple(sorted(row)) for row in target_edges]
    candidates = [
        [
            j for j in range(len(target_maps))
            if source_chars[i] == target_chars[j]
            and source_profiles[i] == target_profiles[j]
        ]
        for i in range(len(source_maps))
    ]
    return {
        "source_characteristics": source_chars,
        "target_characteristics": target_chars,
        "source_edges": source_edges,
        "target_edges": target_edges,
        "source_profiles": source_profiles,
        "target_profiles": target_profiles,
        "candidates": candidates,
    }


def _edge_compatible(graphs, source_index, target_index, mapping):
    """Require all directed pair labels to agree with already assigned vertices."""
    if graphs["source_edges"][source_index][source_index] != graphs["target_edges"][target_index][target_index]:
        return False
    for other_source, other_target in enumerate(mapping):
        if other_target < 0:
            continue
        if graphs["source_edges"][source_index][other_source] != graphs["target_edges"][target_index][other_target]:
            return False
        if graphs["source_edges"][other_source][source_index] != graphs["target_edges"][other_target][target_index]:
            return False
    return True


def _candidate_options(graphs, source_index, mapping, used_targets):
    return [
        target_index
        for target_index in graphs["candidates"][source_index]
        if target_index not in used_targets
        and _edge_compatible(graphs, source_index, target_index, mapping)
    ]


def compare_ifs_pair_relational_graph(
    source,
    target,
    max_graph_nodes=250000,
    max_candidate_isomorphisms=100000,
    max_matrix_products=250000,
    max_word_length=8,
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
    for value, name in (
        (max_graph_nodes, "max_graph_nodes"),
        (max_candidate_isomorphisms, "max_candidate_isomorphisms"),
        (max_matrix_products, "max_matrix_products"),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError(f"{name} must be a positive integer")

    graphs = _relational_graphs(source_maps, target_maps, d)
    initial_candidates = graphs["candidates"]
    initial_candidate_edges = sum(len(row) for row in initial_candidates)
    unrestricted = math.factorial(len(source_maps))
    vertex_profile_classes = len(set(graphs["source_profiles"]))

    refinement = refine_ambiguous_matrix_word_graph(
        [item["matrix"] for item in source_maps],
        [item["matrix"] for item in target_maps],
        graphs["source_characteristics"],
        graphs["target_characteristics"],
        graphs["source_edges"],
        graphs["target_edges"],
        d,
        max_matrix_products=max_matrix_products,
        max_word_length=max_word_length,
    )
    if refinement["candidate_edges_before_refinement"] != initial_candidate_edges:
        raise ArithmeticError(
            "Phase 24 initial colour classes disagree with the Phase 22 vertex filter"
        )
    candidates = refinement["candidate_map_indices"]
    candidate_edges = sum(len(row) for row in candidates)
    graphs["source_edges"] = refinement["source_edges"]
    graphs["target_edges"] = refinement["target_edges"]
    graphs["source_profiles"] = refinement["source_profiles"]
    graphs["target_profiles"] = refinement["target_profiles"]
    graphs["candidates"] = candidates
    adaptive_word_report = refinement["adaptive_matrix_word_refinement"]
    colour_refinement_report = adaptive_word_report["final_colour_refinement"]

    if any(not row for row in candidates) or not _has_perfect_matching(
        candidates, list(range(len(source_maps))), set(), len(target_maps)
    ):
        return {
            "status": "no_affine_conjugacy_found",
            "source_coordinate_system": source_coordinates,
            "target_coordinate_system": target_coordinates,
            "exact_field": f"Q(√{d})",
            "candidate_filter": "phase24_adaptive_exact_matrix_word_trace_refinement",
            "candidate_edge_count": core.paired(candidate_edges),
            "unrestricted_permutation_count": core.paired(unrestricted),
            "candidate_map_indices": [[core.paired(j) for j in row] for row in candidates],
            "adaptive_matrix_word_refinement": adaptive_word_report,
            "adaptive_colour_refinement": colour_refinement_report,
            "search": {
                "graph_search_complete": True,
                "candidate_isomorphisms_tested": core.paired(0),
                "search_nodes": core.paired(0),
                "affine_families_solved": core.paired(0),
            },
            "interpretation": (
                "The stable exact directed colour partition has no compatible "
                "source/target bijection. No simultaneous affine conjugacy exists "
                "for the supplied finite map families under the selected necessary invariants."
            ),
        }

    count = len(source_maps)
    mapping = [-1] * count
    used_targets = set()
    search_nodes = 0
    tested_isomorphisms = 0
    affine_families_solved = 0
    capped = False
    witness = None

    def visit(remaining):
        nonlocal search_nodes, tested_isomorphisms, affine_families_solved, capped, witness
        if capped or witness is not None:
            return
        search_nodes += 1
        if search_nodes > max_graph_nodes:
            capped = True
            return
        if not remaining:
            if tested_isomorphisms >= max_candidate_isomorphisms:
                capped = True
                return
            tested_isomorphisms += 1
            permutation = tuple(mapping)
            rows, rhs = _build_system(source_maps, target_maps, permutation, n)
            status, particular, basis, rank = _rref_affine(rows, rhs, n*n+n, d)
            if status == "inconsistent":
                return
            affine_families_solved += 1
            nullity = len(basis)
            determinant_polynomial = _solution_determinant_polynomial(
                particular, basis, n, d
            )
            if not determinant_polynomial:
                return
            assignment = _find_nonzero_determinant_assignment(
                determinant_polynomial, nullity, n, d
            )
            if assignment is None:
                raise ArithmeticError("nonzero determinant polynomial had no exact specialization")
            solution = _instantiate(particular, basis, assignment, d)
            P = [solution[r*n:(r+1)*n] for r in range(n)]
            t = solution[n*n:]
            determinant = core._det(P, d)
            if core.zero(determinant):
                raise ArithmeticError("constructed coordinate matrix is singular")
            if not core._verify(source_maps, target_maps, permutation, P, t, d):
                raise ArithmeticError("independent exact affine verification failed")
            witness = {
                "permutation": permutation,
                "P": P,
                "t": t,
                "determinant": determinant,
                "rank": rank,
                "nullity": nullity,
                "parameter_assignment": assignment,
                "determinant_polynomial_term_count": len(determinant_polynomial),
            }
            return

        option_rows = {
            i: _candidate_options(graphs, i, mapping, used_targets)
            for i in remaining
        }
        source_index = min(
            remaining,
            key=lambda i: (len(option_rows[i]), -sum(
                1 for other in remaining
                if other != i and graphs["source_edges"][i][other] != graphs["source_edges"][i][i]
            ), i),
        )
        options = option_rows[source_index]
        for target_index in options:
            if capped or witness is not None:
                break
            mapping[source_index] = target_index
            used_targets.add(target_index)
            next_remaining = [i for i in remaining if i != source_index]
            feasible = True
            if next_remaining:
                residual = {
                    i: _candidate_options(graphs, i, mapping, used_targets)
                    for i in next_remaining
                }
                if any(not row for row in residual.values()):
                    feasible = False
                elif not _has_perfect_matching(
                    residual, next_remaining, used_targets, len(target_maps)
                ):
                    feasible = False
            if feasible:
                visit(next_remaining)
            used_targets.remove(target_index)
            mapping[source_index] = -1

    visit(list(range(count)))

    search_complete = not capped and witness is None
    search_report = {
        "graph_search_complete": search_complete,
        "candidate_isomorphisms_tested": core.paired(tested_isomorphisms),
        "search_nodes": core.paired(search_nodes),
        "affine_families_solved": core.paired(affine_families_solved),
        "max_graph_nodes": core.paired(max_graph_nodes),
        "max_candidate_isomorphisms": core.paired(max_candidate_isomorphisms),
    }
    base = {
        "source_coordinate_system": source_coordinates,
        "target_coordinate_system": target_coordinates,
        "exact_field": f"Q(√{d})",
        "candidate_filter": "phase24_adaptive_exact_matrix_word_trace_refinement",
        "candidate_edge_count": core.paired(candidate_edges),
        "unrestricted_permutation_count": core.paired(unrestricted),
        "candidate_map_indices": [[core.paired(j) for j in row] for row in candidates],
        "adaptive_matrix_word_refinement": adaptive_word_report,
        "adaptive_colour_refinement": colour_refinement_report,
        "joint_relational_trace_filter": {
            "word_trace_invariants": list(TRACE_WORDS),
            "adaptive_additional_words": [
                {
                    "length": tier["length"],
                    "words": tier["words"],
                    "applied": tier["applied"],
                }
                for tier in adaptive_word_report["additional_word_tiers"]
            ],
            "source_profile_class_count": core.paired(vertex_profile_classes),
            "profile_definition": (
                "Each map vertex is colored by its exact characteristic polynomial "
                "and sorted multiset of current pairwise edge labels. Each directed "
                "edge includes the six Phase 21 baseline values and every Phase 24 "
                "higher-word trace applied to its ambiguity class."
            ),
            "edge_constraint": (
                "One bijection must preserve every ordered pair label, including "
                "self-loops, under a single common map permutation."
            ),
            "logical_status": (
                "Necessary, not sufficient, invariant for simultaneous similarity. "
                "Every final witness still passes the complete affine equations."
            ),
        },
        "search": search_report,
    }

    if witness is None:
        base["status"] = "relational_graph_search_limit_reached" if capped else "no_affine_conjugacy_found"
        base["interpretation"] = (
            "Relational graph search reached a configured cap; unresolved, not negative."
            if capped else
            "All relational-graph isomorphisms were examined; none admitted an invertible "
            "affine conjugacy under the complete equations."
        )
        return base

    P, t = witness["P"], witness["t"]
    base.update({
        "status": "affine_conjugacy_verified",
        "affine_coordinate_change": {
            "convention": "y = P*x + t",
            "matrix_P": [[core.fmt(v) for v in row] for row in P],
            "translation_t": [core.fmt(v) for v in t],
            "determinant_P": core.fmt(witness["determinant"]),
        },
        "map_permutation_target_index_for_each_source": [
            core.paired(j) for j in witness["permutation"]
        ],
        "linear_solution_family": {
            "rank": core.paired(witness["rank"]),
            "free_parameter_count": core.paired(witness["nullity"]),
            "parameter_assignment": [core.fmt(v) for v in witness["parameter_assignment"]],
            "determinant_polynomial_term_count": core.paired(witness["determinant_polynomial_term_count"]),
        },
        "verification": "Every affine map equation and det(P) ≠ 0 were independently checked exactly.",
        "interpretation": (
            "A relationally consistent map bijection yielded one exact invertible affine "
            "conjugacy. This is structural equivalence, not physical causation."
        ),
    })
    return base


def analyze_payload(payload):
    pairs = payload.get("pairs", [])
    if not isinstance(pairs, list) or not pairs:
        raise ValueError("at least one source/target IFS pair is required")
    results = [
        {
            "name": item.get("name", "unnamed_pair"),
            **compare_ifs_pair_relational_graph(
                item["source"],
                item["target"],
                max_graph_nodes=int(item.get("max_graph_nodes", 250000)),
                max_candidate_isomorphisms=int(item.get("max_candidate_isomorphisms", 100000)),
                max_matrix_products=int(item.get("max_matrix_products", 250000)),
                max_word_length=int(item.get("max_word_length", 8)),
            ),
        }
        for item in pairs
    ]
    return {
        "schema": "universe.ifs-relational-graph-conjugacy.v2",
        "pair_count": core.paired(len(results)),
        "results": results,
        "global_guard": (
            "Adaptive exact matrix-word traces and directed colour refinement are "
            "necessary invariants only. Every final witness is verified against "
            "every original affine map equation; work budgets and search caps are explicit."
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, default=Path("affine_ifs_relational_graph.json"))
    args = parser.parse_args()
    result = analyze_payload(json.loads(args.input.read_text(encoding="utf-8")))
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
