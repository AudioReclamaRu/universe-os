"""Exact joint directed colour refinement for finite edge-labelled graphs.

The refinement is a necessary isomorphism invariant, not a complete graph
isomorphism test. Source and target colours are assigned jointly so equal
signatures always receive the same colour ID across both graphs.
"""
from __future__ import annotations


def _check_square(name, matrix, count):
    if len(matrix) != count or any(len(row) != count for row in matrix):
        raise ValueError(f"{name} must be a square {count}x{count} matrix")


def _joint_colour_ids(source_signatures, target_signatures):
    signatures = source_signatures + target_signatures
    unique = set(signatures)
    ordered = sorted(unique, key=repr)
    ids = {signature: index for index, signature in enumerate(ordered)}
    split = len(source_signatures)
    return (
        [ids[item] for item in source_signatures],
        [ids[item] for item in target_signatures],
        len(unique),
    )


def refine_joint_directed_colours(
    source_vertex_colours,
    target_vertex_colours,
    source_edge_labels,
    target_edge_labels,
):
    """Run exact 1-dimensional refinement on two directed labelled graphs."""
    n = len(source_vertex_colours)
    m = len(target_vertex_colours)
    if n == 0 or n != m:
        raise ValueError("source and target graphs must have the same positive order")
    _check_square("source_edge_labels", source_edge_labels, n)
    _check_square("target_edge_labels", target_edge_labels, m)

    source_signatures = [(item,) for item in source_vertex_colours]
    target_signatures = [(item,) for item in target_vertex_colours]
    source_colours, target_colours, class_count = _joint_colour_ids(
        source_signatures, target_signatures
    )
    class_counts = [class_count]
    stable = False
    rounds = 0

    # Each non-stable round strictly increases the combined class count.
    for _ in range(2 * n + 1):
        source_next = []
        target_next = []
        for i in range(n):
            outgoing = [
                (source_edge_labels[i][j], source_colours[j])
                for j in range(n)
            ]
            incoming = [
                (source_edge_labels[j][i], source_colours[j])
                for j in range(n)
            ]
            source_next.append((
                source_colours[i],
                tuple(sorted(outgoing, key=repr)),
                tuple(sorted(incoming, key=repr)),
            ))
        for i in range(m):
            outgoing = [
                (target_edge_labels[i][j], target_colours[j])
                for j in range(m)
            ]
            incoming = [
                (target_edge_labels[j][i], target_colours[j])
                for j in range(m)
            ]
            target_next.append((
                target_colours[i],
                tuple(sorted(outgoing, key=repr)),
                tuple(sorted(incoming, key=repr)),
            ))

        new_source, new_target, new_class_count = _joint_colour_ids(
            source_next, target_next
        )
        rounds += 1
        source_colours, target_colours = new_source, new_target
        class_counts.append(new_class_count)
        if new_class_count == class_count:
            stable = True
            break
        if new_class_count < class_count:
            raise ArithmeticError("colour refinement unexpectedly merged existing classes")
        class_count = new_class_count

    if not stable:
        raise ArithmeticError("directed colour refinement did not stabilize within its finite bound")

    candidates = [
        [j for j, colour in enumerate(target_colours) if colour == source_colours[i]]
        for i in range(n)
    ]
    before_edges = sum(
        sum(1 for target in target_vertex_colours if target == source)
        for source in source_vertex_colours
    )
    after_edges = sum(len(row) for row in candidates)
    return {
        "source_colours": source_colours,
        "target_colours": target_colours,
        "candidate_map_indices": candidates,
        "refinement_rounds": rounds,
        "combined_colour_class_counts": class_counts,
        "stable": stable,
        "candidate_edges_before_refinement": before_edges,
        "candidate_edges_after_refinement": after_edges,
        "candidate_edges_removed": before_edges - after_edges,
        "method": "exact_joint_1wl_directed_edge_labelled_in_out_multiset_refinement",
        "invariants_preserved": [
            "initial exact vertex colour",
            "directed edge labels",
            "incoming and outgoing incidence",
            "edge-label multiplicity",
            "self-loops",
            "one common source/target vertex-colour correspondence",
        ],
        "logical_status": (
            "Necessary isomorphism invariant only; stable colour refinement is not "
            "a complete graph-isomorphism test. Candidate matches still require "
            "exact relational search and the full affine equations."
        ),
    }
