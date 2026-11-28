#!/usr/bin/env python3
"""Reproducible exact-math checks for UNIVERSE 2.0 relational reconstruction.

Standard-library only. Checks finite combinatorics and source-derived arithmetic.
Does not run the GUI, alter legacy files or claim new physics.
"""
from __future__ import annotations

import json
import math
from collections import Counter, deque
from itertools import combinations, product
from math import comb, factorial, log, pi, sqrt

BITS = 7
N = 2 ** BITS
GATE_42 = 42
GATE_85 = 85
P = 3 ** 12 / 2 ** 19
THETA = log(P)
PI_128 = 4.0 * sum((-1) ** k / (2 * k + 1) for k in range(128))


def hamming(a: int, b: int) -> int:
    return (a ^ b).bit_count()


def face_vector(n: int = BITS) -> list[int]:
    return [comb(n, d) * 2 ** (n - d) for d in range(n + 1)]


def q7_edges(n: int = BITS) -> set[tuple[int, int]]:
    generators = [1 << bit for bit in range(n)]
    return {
        (i, i ^ g)
        for i in range(2 ** n)
        for g in generators
        if i < (i ^ g)
    }


def ternary_to_binary(state: tuple[int, ...]) -> int:
    """Map NEG/POS to a fixed coordinate (1), CENTER to free (0)."""
    if len(state) != BITS or any(v not in (-1, 0, 1) for v in state):
        raise ValueError("Expected a seven-coordinate state over {-1,0,+1}.")
    return sum((1 << i) for i, value in enumerate(state) if value != 0)


def invert_ternary(state: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(-v for v in state)


def nearest_gate_shells() -> Counter[int]:
    counts: Counter[int] = Counter()
    for node in range(N):
        d = min(hamming(node, GATE_42), hamming(node, GATE_85))
        counts[d] += 1
    return counts


def gate_field_by_index(node: int) -> float:
    d42 = abs(node - GATE_42) / N
    d85 = abs(node - GATE_85) / N
    return math.exp(-min(d42, d85) * 8.0)


def simulate_legacy_reset_steps(count: int = 4, max_steps: int = 1000) -> list[int]:
    t = 0.0
    psi = 0.0
    events: list[int] = []
    for _ in range(max_steps):
        t += 1.0
        psi += THETA * (1.0 + 0.15 * math.sin(t * 2.0 * PI_128 / 85.0))
        if psi > P:
            events.append(int(t))
            psi *= THETA
            if len(events) >= count:
                break
    return events


def main() -> None:
    # Q7 graph
    edges = q7_edges()
    degrees = [0] * N
    adjacency = [[] for _ in range(N)]
    for a, b in edges:
        degrees[a] += 1
        degrees[b] += 1
        adjacency[a].append(b)
        adjacency[b].append(a)
    assert len(edges) == 448
    assert set(degrees) == {7}

    # Connectivity and diameter
    distances = [-1] * N
    distances[0] = 0
    queue = deque([0])
    while queue:
        u = queue.popleft()
        for v in adjacency[u]:
            if distances[v] == -1:
                distances[v] = distances[u] + 1
                queue.append(v)
    assert min(distances) == 0 and max(distances) == 7
    assert all(d >= 0 for d in distances)

    # Complete face lattice
    fv = face_vector()
    assert fv == [128, 448, 672, 560, 280, 84, 14, 1]
    assert sum(fv) == 3 ** 7 == 2187
    assert sum(((-1) ** d) * fv[d] for d in range(8)) == 1
    assert sum(((-1) ** d) * fv[d] for d in range(7)) == 2
    vertex_face_incidence = sum(fv[d] * (2 ** d) for d in range(8))
    edge_face_incidence = sum(fv[d] * d * (2 ** (d - 1)) for d in range(1, 8))
    assert vertex_face_incidence == 4 ** 7 == 16384
    assert edge_face_incidence == 28672

    # Ternary face encoding and comparator fibres
    fibres = Counter()
    ternary_count = 0
    for state in product((-1, 0, 1), repeat=7):
        ternary_count += 1
        mask = ternary_to_binary(state)
        fibres[mask] += 1
        inverted = invert_ternary(state)
        assert invert_ternary(inverted) == state
        assert ternary_to_binary(inverted) == mask
    assert ternary_count == 2187
    assert len(fibres) == 128
    for mask, fibre_size in fibres.items():
        assert fibre_size == 2 ** mask.bit_count()
    assert sum(fibres.values()) == 2187

    # Mixed binary/ternary products
    mixed = [2 ** a * 3 ** (7 - a) for a in range(7, -1, -1)]
    assert mixed == [128, 192, 288, 432, 648, 972, 1458, 2187]
    mixed_union = sum(comb(7, a) * (2 ** a) * (3 ** (7 - a)) for a in range(8))
    assert mixed_union == 5 ** 7 == 78125

    # Gates and integer division by three
    assert 128 == 3 * 42 + 2
    assert 256 == 3 * 85 + 1
    assert 85 == 2 * 42 + 1
    assert 2 ** 7 % 3 == 2
    assert 2 ** 8 % 3 == 1
    assert format(42, "07b") == "0101010"
    assert format(85, "07b") == "1010101"
    assert (42 ^ 85) == 127
    assert hamming(42, 85) == 7
    assert bin(42).count("1") == 3
    assert bin(85).count("1") == 4
    assert factorial(7) == 5040
    shells = nearest_gate_shells()
    assert [shells[d] for d in range(4)] == [2, 14, 42, 70]
    assert sum(shells.values()) == 128
    assert 42 == 2 * comb(7, 2)

    # Index metric is not a graph metric
    neighbours_42 = [42 ^ (1 << b) for b in range(7)]
    assert all(hamming(node, 42) == 1 for node in neighbours_42)
    assert abs(gate_field_by_index(10) - gate_field_by_index(43)) > 0.7

    # H3/SO(8)/Mackay arithmetic and golden ratio
    phi = (1.0 + sqrt(5.0)) / 2.0
    assert abs(phi * phi - phi - 1.0) < 1e-14
    assert 28 == 8 * 7 // 2
    assert [10 * n * n + 2 for n in range(1, 5)] == [12, 42, 92, 162]
    assert 28 + 42 == 70
    assert 28 * 8 == 224 == 448 // 2
    assert 42 * 16 == 672 == fv[2]

    # Legacy source-derived ratios
    assert abs(128 * (THETA / 128) - THETA) < 1e-15
    r_min = 1.0 - 0.28
    r_max = 1.0 + 0.28
    assert abs(r_max / r_min - 16.0 / 9.0) < 1e-14
    pi_period = 85.0 * pi / PI_128
    mass_n = [1, 7, 8, 28, 42, 64, 128]
    mass_coefficients = [n * (2 ** e) for e, n in enumerate(mass_n)]
    assert mass_coefficients == [1, 14, 32, 224, 672, 2048, 8192]
    alpha_model = 128 * P ** 5
    omega_l_model = 1.0 - P ** (-85)
    dm_ob_model_125 = P ** 125
    dm_ob_model_124 = P ** 124
    phase_theta_ratio = 2.0 * PI_128 / (85.0 * THETA)

    # Seven-position interval-pair combinatorics
    pairs = list(combinations(range(7), 2))
    pair_distance_classes = Counter(
        min((b - a) % 7, (a - b) % 7) for a, b in pairs
    )
    assert len(pairs) == 21
    assert dict(pair_distance_classes) == {1: 7, 2: 7, 3: 7}
    assert sum([1, 2, 2, 2, 1, 2, 2]) == 12

    result = {
        "status": "PASS_EXACT_MATH_AND_LEGACY_ARITHMETIC_ONLY",
        "Q7": {
            "vertices": N,
            "edges": len(edges),
            "regular_degree": 7,
            "diameter": 7,
            "face_vector_d0_to_d7": fv,
            "all_faces": sum(fv),
            "vertex_face_incidences": vertex_face_incidence,
            "edge_face_incidences": edge_face_incidence,
            "euler_characteristic_cube": 1,
            "euler_characteristic_boundary": 2,
        },
        "ternary": {
            "states": ternary_count,
            "binary_masks": len(fibres),
            "fibre_rule": "2**popcount(binary_mask)",
            "mixed_alphabet_products": mixed,
            "mixed_alphabet_union_count": mixed_union,
        },
        "gates": {
            "42_binary": format(42, "07b"),
            "85_binary": format(85, "07b"),
            "xor": 127,
            "hamming_distance": 7,
            "nearest_gate_shells_d0_to_d3": [shells[d] for d in range(4)],
            "shortest_paths": factorial(7),
        },
        "natural_keys": {
            "phi": phi,
            "phi_minus_3_over_2": phi - 1.5,
            "mackay_shells_n1_to_n4": [10 * n * n + 2 for n in range(1, 5)],
            "so8_dimension": 28,
            "radial_extrema_ratio": r_max / r_min,
        },
        "legacy_v2": {
            "p": P,
            "theta": THETA,
            "pi_128": PI_128,
            "pi_128_absolute_error": PI_128 - pi,
            "pi_128_relative_error_percent": (PI_128 / pi - 1.0) * 100.0,
            "phase_period_induced_by_pi_128": pi_period,
            "mass_integer_coefficients": mass_coefficients,
            "alpha_inverse_formula": alpha_model,
            "omega_lambda_formula": omega_l_model,
            "dm_to_baryon_p125": dm_ob_model_125,
            "dm_to_baryon_p124_diagnostic_only": dm_ob_model_124,
            "phase_theta_ratio": phase_theta_ratio,
            "relative_difference_phase_ratio_vs_p125_percent": (phase_theta_ratio / dm_ob_model_125 - 1.0) * 100.0,
            "legacy_reset_steps_first_four": simulate_legacy_reset_steps(),
        },
        "heptaphase": {
            "intervals": [1, 2, 2, 2, 1, 2, 2],
            "semitone_sum": 12,
            "two_short_interval_placements": len(pairs),
            "cyclic_distance_class_counts": dict(pair_distance_classes),
        },
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
