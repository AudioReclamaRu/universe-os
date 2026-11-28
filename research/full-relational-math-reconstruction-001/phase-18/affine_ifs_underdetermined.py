"""Exact invertibility search for underdetermined affine IFS conjugacy families."""
from __future__ import annotations

import argparse
import itertools
import json
import math
import sys
from pathlib import Path

PHASE16 = Path(__file__).resolve().parent.parent / "phase-16"
if str(PHASE16) not in sys.path:
    sys.path.insert(0, str(PHASE16))

import affine_ifs_conjugacy as core


def _zero_exp(variable_count):
    return (0,) * variable_count


def _poly_add(a, b, d):
    out = dict(a)
    for exp, coeff in b.items():
        value = core.add(out.get(exp, core.Z), coeff)
        if core.zero(value):
            out.pop(exp, None)
        else:
            out[exp] = value
    return out


def _poly_mul(a, b, d):
    out = {}
    for exp_a, coeff_a in a.items():
        for exp_b, coeff_b in b.items():
            exp = tuple(x + y for x, y in zip(exp_a, exp_b))
            value = core.mul(coeff_a, coeff_b, d)
            out[exp] = core.add(out.get(exp, core.Z), value)
    return {exp: value for exp, value in out.items() if not core.zero(value)}


def _poly_substitute(poly, variable, value, d):
    out = {}
    for exponents, coefficient in poly.items():
        factor = core.O
        for _ in range(exponents[variable]):
            factor = core.mul(factor, value, d)
        reduced_exp = exponents[:variable] + exponents[variable + 1:]
        reduced_coeff = core.mul(coefficient, factor, d)
        out[reduced_exp] = core.add(out.get(reduced_exp, core.Z), reduced_coeff)
    return {exp: coeff for exp, coeff in out.items() if not core.zero(coeff)}


def _determinant_polynomial(matrix, variable_count, d):
    n = len(matrix)
    zero_exp = _zero_exp(variable_count)
    total = {}
    for permutation in itertools.permutations(range(n)):
        inversions = sum(
            permutation[i] > permutation[j]
            for i in range(n) for j in range(i + 1, n)
        )
        sign = -1 if inversions % 2 else 1
        term = {zero_exp: core.O}
        for row, column in enumerate(permutation):
            term = _poly_mul(term, matrix[row][column], d)
        if sign < 0:
            term = {exp: core.neg(coeff) for exp, coeff in term.items()}
        total = _poly_add(total, term, d)
    return total


def _find_nonzero_determinant_assignment(det_poly, variable_count, dimension, d):
    """Construct a witness by exact polynomial specialization over {0,...,n}."""
    current = dict(det_poly)
    assignment = []
    # det(P(lambda)) has degree at most n in each free parameter.
    # A nonzero degree-n univariate polynomial cannot vanish at n+1 distinct points.
    for _ in range(variable_count):
        selected = None
        # Previous substitutions remove one variable, so the next variable is index 0.
        for integer_value in range(dimension + 1):
            value = (integer_value, 0)
            reduced = _poly_substitute(current, 0, value, d)
            if reduced:
                selected = value
                current = reduced
                assignment.append(value)
                break
        if selected is None:
            return None
    if not current or len(current) != 1 or next(iter(current)) != ():
        raise ArithmeticError("determinant specialization did not reduce to one scalar")
    if core.zero(next(iter(current.values()))):
        raise ArithmeticError("constructed determinant witness is zero")
    return assignment


def _rref_affine(rows, rhs, columns, d):
    if len(rows) != len(rhs):
        raise ValueError("linear system row count mismatch")
    matrix = [list(row) + [rhs[i]] for i, row in enumerate(rows)]
    pivot_columns = []
    pivot_row = 0
    for column in range(columns):
        pivot = next(
            (r for r in range(pivot_row, len(matrix))
             if not core.zero(matrix[r][column])),
            None,
        )
        if pivot is None:
            continue
        matrix[pivot_row], matrix[pivot] = matrix[pivot], matrix[pivot_row]
        scale = matrix[pivot_row][column]
        matrix[pivot_row] = [core.div(v, scale, d) for v in matrix[pivot_row]]
        for r in range(len(matrix)):
            if r == pivot_row:
                continue
            factor = matrix[r][column]
            if not core.zero(factor):
                matrix[r] = [
                    core.sub(x, core.mul(factor, y, d))
                    for x, y in zip(matrix[r], matrix[pivot_row])
                ]
        pivot_columns.append(column)
        pivot_row += 1
        if pivot_row == len(matrix):
            break

    for row in matrix:
        if all(core.zero(v) for v in row[:columns]) and not core.zero(row[columns]):
            return "inconsistent", None, None, len(pivot_columns)

    free_columns = [c for c in range(columns) if c not in pivot_columns]
    particular = [core.Z for _ in range(columns)]
    for r, c in enumerate(pivot_columns):
        particular[c] = matrix[r][columns]

    basis = []
    for free in free_columns:
        vector = [core.Z for _ in range(columns)]
        vector[free] = core.O
        for r, pivot in enumerate(pivot_columns):
            vector[pivot] = core.neg(matrix[r][free])
        basis.append(vector)
    return "affine_family", particular, basis, len(pivot_columns)


def _build_system(source_maps, target_maps, permutation, dimension):
    variable_count = dimension * dimension + dimension
    rows, rhs = [], []
    for source_index, target_index in enumerate(permutation):
        source = source_maps[source_index]
        target = target_maps[target_index]
        A, b = source["matrix"], source["translation"]
        C, e = target["matrix"], target["translation"]

        # P A_i - C_j P = 0
        for r in range(dimension):
            for c in range(dimension):
                equation = [core.Z for _ in range(variable_count)]
                for k in range(dimension):
                    p_rk = r * dimension + k
                    p_kc = k * dimension + c
                    equation[p_rk] = core.add(equation[p_rk], A[k][c])
                    equation[p_kc] = core.sub(equation[p_kc], C[r][k])
                rows.append(equation)
                rhs.append(core.Z)

        # P b_i + t - C_j t = e_j
        for r in range(dimension):
            equation = [core.Z for _ in range(variable_count)]
            for k in range(dimension):
                equation[r * dimension + k] = core.add(
                    equation[r * dimension + k], b[k]
                )
            equation[dimension * dimension + r] = core.add(
                equation[dimension * dimension + r], core.O
            )
            for k in range(dimension):
                t_k = dimension * dimension + k
                equation[t_k] = core.sub(equation[t_k], C[r][k])
            rows.append(equation)
            rhs.append(e[r])
    return rows, rhs


def _solution_determinant_polynomial(particular, basis, dimension, d):
    variable_count = len(basis)
    zero_exp = _zero_exp(variable_count)
    polynomial_matrix = []
    for r in range(dimension):
        row = []
        for c in range(dimension):
            index = r * dimension + c
            polynomial = {}
            if not core.zero(particular[index]):
                polynomial[zero_exp] = particular[index]
            for j, vector in enumerate(basis):
                coefficient = vector[index]
                if not core.zero(coefficient):
                    exponent = [0] * variable_count
                    exponent[j] = 1
                    polynomial[tuple(exponent)] = coefficient
            row.append(polynomial)
        polynomial_matrix.append(row)
    return _determinant_polynomial(polynomial_matrix, variable_count, d)


def _instantiate(particular, basis, assignment, d):
    result = list(particular)
    for parameter, vector in zip(assignment, basis):
        for i, coefficient in enumerate(vector):
            result[i] = core.add(result[i], core.mul(parameter, coefficient, d))
    return result


def compare_ifs_pair(source, target, max_permutations=100000):
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
    if isinstance(max_permutations, bool) or not isinstance(max_permutations, int) or max_permutations < 1:
        raise ValueError("max_permutations must be a positive integer")

    total = math.factorial(len(source_maps))
    tested = 0
    maximum_nullity = 0
    for permutation in itertools.islice(
        itertools.permutations(range(len(target_maps))), max_permutations
    ):
        tested += 1
        rows, rhs = _build_system(source_maps, target_maps, permutation, n)
        _status, particular, basis, rank = _rref_affine(
            rows, rhs, n * n + n, d
        )
        if _status == "inconsistent":
            continue

        nullity = len(basis)
        maximum_nullity = max(maximum_nullity, nullity)
        determinant_polynomial = _solution_determinant_polynomial(
            particular, basis, n, d
        )
        if not determinant_polynomial:
            # det(P) is identically zero over this complete affine solution family.
            continue

        assignment = _find_nonzero_determinant_assignment(
            determinant_polynomial, nullity, n, d
        )
        if assignment is None:
            raise ArithmeticError("nonzero determinant polynomial had no exact specialization")
        solution = _instantiate(particular, basis, assignment, d)
        P = [solution[r * n:(r + 1) * n] for r in range(n)]
        t = solution[n * n:]
        determinant = core._det(P, d)
        if core.zero(determinant):
            raise ArithmeticError("determinant polynomial witness failed exact determinant check")
        if not core._verify(source_maps, target_maps, permutation, P, t, d):
            raise ArithmeticError("independent affine conjugacy verification failed")

        return {
            "status": "affine_conjugacy_verified",
            "source_coordinate_system": source_coordinates,
            "target_coordinate_system": target_coordinates,
            "exact_field": f"Q(√{d})",
            "affine_coordinate_change": {
                "convention": "y = P*x + t",
                "matrix_P": [[core.fmt(v) for v in row] for row in P],
                "translation_t": [core.fmt(v) for v in t],
                "determinant_P": core.fmt(determinant),
            },
            "map_permutation_target_index_for_each_source": [
                core.paired(j) for j in permutation
            ],
            "linear_solution_family": {
                "rank": core.paired(rank),
                "free_parameter_count": core.paired(nullity),
                "parameter_assignment": [core.fmt(v) for v in assignment],
                "determinant_polynomial_term_count": core.paired(len(determinant_polynomial)),
                "nonzero_witness_method": (
                    "Exact determinant polynomial; deterministic specialization over {0,1,...,n}."
                ),
            },
            "search": {
                "permutations_tested": core.paired(tested),
                "total_permutations": core.paired(total),
                "search_complete": tested == total,
                "stopped_on_verified_match": True,
            },
            "verification": "Every affine map equation and det(P) ≠ 0 were checked exactly.",
            "interpretation": (
                "An invertible affine conjugacy was recovered from an underdetermined "
                "exact linear solution family. This is mathematical structural "
                "equivalence, not physical causation."
            ),
        }

    complete = tested == total
    return {
        "status": "no_affine_conjugacy_found" if complete else "permutation_search_limit_reached",
        "source_coordinate_system": source_coordinates,
        "target_coordinate_system": target_coordinates,
        "exact_field": f"Q(√{d})",
        "search": {
            "permutations_tested": core.paired(tested),
            "total_permutations": core.paired(total),
            "search_complete": complete,
        },
        "maximum_affine_solution_nullity_seen": core.paired(maximum_nullity),
        "interpretation": (
            "No invertible affine conjugacy exists among all map permutations examined."
            if complete else
            "Permutation search was capped; unresolved, not a negative result."
        ),
    }


def analyze_payload(payload):
    pairs = payload.get("pairs", [])
    if not isinstance(pairs, list) or not pairs:
        raise ValueError("at least one IFS source/target pair is required")
    results = [
        {
            "name": item.get("name", "unnamed_pair"),
            **compare_ifs_pair(
                item["source"], item["target"],
                int(item.get("max_permutations", 100000))
            ),
        }
        for item in pairs
    ]
    return {
        "schema": "universe.ifs-underdetermined-affine-witness.v1",
        "pair_count": core.paired(len(results)),
        "results": results,
        "scope": (
            "Exact affine conjugacy of finite IFS map families in dimensions 1–3 "
            "over a common squarefree real quadratic field; map permutation search remains bounded."
        ),
        "global_guard": (
            "A verified affine conjugacy proves structural equivalence only; it does not "
            "prove common physical origin, energy transfer or causal coupling."
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument(
        "--output", type=Path,
        default=Path("affine_ifs_underdetermined.json")
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
