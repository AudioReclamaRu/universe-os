import copy
import sys
import unittest
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for sibling in (
    "phase-27",
    "phase-28",
    "phase-29",
    "phase-30",
    "phase-31",
    "phase-32",
    "phase-33",
):
    path = ROOT / sibling
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import basis_transitions as phase31
import relation_filtration as phase30
import trace_ideal_closure as phase29
from bifiltration_operators import analyze_exact_bifiltration_operators

from bifiltration_rank_ledger import (
    DEFAULT_MAX_RECTANGLE_CHECKS,
    analyze_bounded_exact_bifiltration_rank_ledger,
    analyze_exact_bifiltration_rank_ledger,
    check_rectangle,
)


def decode_pair(value):
    sign = -1 if value.startswith("-") else 1
    body = value.lstrip("-")
    return sign * int(body[1:body.index("_2|")], 2)


def paired(value):
    return phase29._paired(value)


def term(coefficient, *words):
    return {
        "coefficient": Fraction(coefficient),
        "trace_factors": [list(word) for word in words],
    }


def basis_entry(degree, terms, label="B00000"):
    return {
        "basis_id": label,
        "candidate_id": label,
        "total_matrix_word_degree": paired(degree),
        "trace_terms": list(terms),
        "pivot_trace_monomial": "tr(M0)",
        "universal_verification": {"status": "universally_verified_identity"},
    }


def profile(values):
    return {decode_pair(k): decode_pair(v) for k, v in values.items()}


def cell_label(length, degree):
    return {
        "substitution_bound": paired(length),
        "multiplier_bound": paired(degree),
    }


def contains_float(value):
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(contains_float(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(contains_float(item) for item in value)
    return False


# Homogeneous degree-1 and degree-2 trace monomials used by the local controls.
MONO_A = term(1, (0,))          # tr(M0), degree 1
MONO_P = term(1, (0,), (0,))    # tr(M0)tr(M0), degree 2
MONO_Q = term(1, (0,), (1,))    # tr(M0)tr(M1), degree 2
MONO_S = term(1, (1,), (1,))    # tr(M1)tr(M1), degree 2
MONO_V = term(1, (0, 1))        # tr(M0 M1), degree 2
VECTOR_U = [MONO_P, term(Fraction(1, 2), (0,), (1,))]


def filtration_cell(length, degree, ranks, quotients, union, basis, directions, intersection):
    return {
        **cell_label(length, degree),
        "status": "complete_bounded_relation_space",
        "relation_space_dimension": paired(sum(ranks.values())),
        "predecessor_union_dimension": paired(sum(union.values())),
        "predecessor_intersection_dimension": paired(intersection),
        "new_quotient_dimension": paired(sum(quotients.values())),
        "rank_by_total_word_degree": {paired(k): paired(v) for k, v in ranks.items()},
        "predecessor_union_rank_by_total_word_degree": {
            paired(k): paired(v) for k, v in union.items()
        },
        "new_quotient_rank_by_total_word_degree": {
            paired(k): paired(v) for k, v in quotients.items()
        },
        "basis_entries": basis,
        "new_directions": directions,
    }


def synthetic_filtration():
    """Two-degree grid with omega=1 at (2,1) and q=0 there."""
    cells = [
        filtration_cell(
            1, 0, {1: 1, 2: 1}, {1: 1, 2: 1}, {},
            [basis_entry(1, [MONO_A], "C10A"), basis_entry(2, VECTOR_U, "C10U")],
            [basis_entry(1, [MONO_A], "Q10A"), basis_entry(2, VECTOR_U, "Q10U")],
            0,
        ),
        filtration_cell(
            1, 1, {1: 1, 2: 3}, {2: 2}, {1: 1, 2: 1},
            [
                basis_entry(1, [MONO_A], "C11A"),
                basis_entry(2, [MONO_P], "C11P"),
                basis_entry(2, [MONO_Q], "C11Q"),
                basis_entry(2, [MONO_S], "C11S"),
            ],
            [basis_entry(2, [MONO_P], "Q11P"), basis_entry(2, [MONO_Q], "Q11Q")],
            0,
        ),
        filtration_cell(
            2, 0, {1: 1, 2: 3}, {2: 2}, {1: 1, 2: 1},
            [
                basis_entry(1, [MONO_A], "C20A"),
                basis_entry(2, [MONO_P], "C20P"),
                basis_entry(2, [MONO_Q], "C20Q"),
                basis_entry(2, [MONO_V], "C20V"),
            ],
            [basis_entry(2, [MONO_Q], "Q20Q"), basis_entry(2, [MONO_V], "Q20V")],
            0,
        ),
        filtration_cell(
            2, 1, {1: 1, 2: 4}, {}, {1: 1, 2: 4},
            [
                basis_entry(1, [MONO_A], "C21A"),
                basis_entry(2, [MONO_P], "C21P"),
                basis_entry(2, [MONO_Q], "C21Q"),
                basis_entry(2, [MONO_S], "C21S"),
                basis_entry(2, [MONO_V], "C21V"),
            ],
            [],
            3,
        ),
    ]
    return {
        "schema": "universe.trace-relation-filtration.v1",
        "status": "complete_bounded_filtration",
        "dimension": paired(2),
        "generator_count": paired(2),
        "max_substitution_word_length": paired(2),
        "max_multiplier_trace_word_length": paired(1),
        "max_multiplier_total_word_degree": paired(1),
        "coefficient_field": "Q",
        "cells": cells,
    }


def synthetic_bifiltration():
    return {
        "schema": "universe.trace-relation-bifiltration-operators.v1",
        "status": "complete_exact_bifiltration_operators",
        "source_filtration_status": "complete_bounded_filtration",
        "coefficient_field": "Q",
        "cell_count": paired(4),
        "square_count": paired(1),
        "boundary_cells": [cell_label(1, 0), cell_label(1, 1), cell_label(2, 0)],
        "squares": [
            {
                "terminal_cell": cell_label(2, 1),
                "source_cell": cell_label(1, 0),
                "left_predecessor": cell_label(1, 1),
                "bottom_predecessor": cell_label(2, 0),
                "dimensions": {
                    "source": paired(2),
                    "left": paired(4),
                    "bottom": paired(4),
                    "terminal": paired(5),
                    "intersection": paired(3),
                    "union": paired(5),
                    "quotient_q": paired(0),
                    "mixed_overlap_omega": paired(1),
                    "rank_difference": paired(-1),
                },
                "mixed_overlap": {
                    "status": "nonzero_mixed_overlap",
                    "omega": paired(1),
                    "complement_ids": ["MO00000"],
                    "complement_basis": [
                        basis_entry(2, [MONO_Q], "MO00000"),
                    ],
                },
            }
        ],
    }


def physical_arguments(**overrides):
    arguments = {
        "dimension": 2,
        "generator_count": 2,
        "max_substitution_word_length": 2,
        "max_multiplier_trace_word_length": 1,
        "max_multiplier_total_word_degree": 1,
        "max_filtration_cells": 4,
        "max_word_catalog_size": 8,
        "max_substitution_sets": 1000,
        "max_multiplier_monomials": 16,
        "max_derived_relations": 5000,
        "max_seed_expansion_terms_per_identity": 100_000,
        "max_seed_expansion_terms_per_cell": 2_000_000,
        "max_relation_expansion_terms_per_relation": 100_000,
        "max_relation_expansion_terms_per_cell": 2_000_000,
        "max_aggregate_seed_expansion_terms": 8_000_000,
        "max_aggregate_relation_expansion_terms": 12_000_000,
    }
    arguments.update(overrides)
    return arguments


class BifiltrationRankLedgerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.physical_filtration = phase30.analyze_bounded_relation_filtration(
            **physical_arguments()
        )
        if cls.physical_filtration["status"] != "complete_bounded_filtration":
            raise AssertionError(cls.physical_filtration)
        cls.physical_transitions = phase31.analyze_exact_basis_transitions(
            cls.physical_filtration
        )
        cls.physical_bifiltration = analyze_exact_bifiltration_operators(
            cls.physical_filtration, cls.physical_transitions
        )
        if cls.physical_bifiltration["status"] != "complete_exact_bifiltration_operators":
            raise AssertionError(cls.physical_bifiltration)
        cls.physical = analyze_exact_bifiltration_rank_ledger(
            cls.physical_filtration, cls.physical_bifiltration
        )
        cls.synthetic = analyze_exact_bifiltration_rank_ledger(
            synthetic_filtration(), synthetic_bifiltration()
        )

    def ledger_by_key(self, analysis):
        return {
            (decode_pair(row["cell"]["substitution_bound"]),
             decode_pair(row["cell"]["multiplier_bound"])): row
            for row in analysis["cell_ledger"]
        }

    def assert_complete(self, analysis):
        self.assertEqual(analysis["status"], "complete_exact_bifiltration_rank_ledger", analysis)

    def test_01_physical_small_grid_recomputed_values(self):
        self.assert_complete(self.physical)
        rows = self.ledger_by_key(self.physical)
        ranks = {key: decode_pair(row["rank"]) for key, row in rows.items()}
        self.assertEqual(ranks, {(1, 0): 4, (1, 1): 12, (2, 0): 41, (2, 1): 120})
        square = self.physical_bifiltration["squares"][0]
        dimensions = square["dimensions"]
        intersection = decode_pair(dimensions["intersection"])
        union = decode_pair(dimensions["union"])
        q = decode_pair(dimensions["quotient_q"])
        omega = decode_pair(dimensions["mixed_overlap_omega"])
        self.assertEqual(intersection, 7)
        self.assertEqual(q, ranks[(2, 1)] - union)
        self.assertEqual(omega, intersection - ranks[(1, 0)])
        self.assertEqual(decode_pair(dimensions["rank_difference"]), 71)
        self.assertEqual(decode_pair(rows[(2, 1)]["q"]), q)
        self.assertEqual(decode_pair(rows[(2, 1)]["omega"]), omega)
        self.assertEqual(decode_pair(rows[(2, 1)]["delta"]), q - omega)

    def test_02_local_delta_equals_q_minus_omega_everywhere(self):
        for analysis in (self.physical, self.synthetic):
            self.assert_complete(analysis)
            for row in analysis["cell_ledger"]:
                q = decode_pair(row["q"])
                omega = decode_pair(row["omega"])
                delta = decode_pair(row["delta"])
                self.assertEqual(delta, q - omega)
                self.assertEqual(delta, decode_pair(row["mixed_rank_difference"]))
                if row["category"] == "interior":
                    self.assertEqual(row["omega_source"], "phase32_mixed_overlap_complement")
                else:
                    self.assertEqual(omega, 0)
                    self.assertEqual(row["omega_source"], "boundary_convention_zero")

    def test_03_all_prefix_identities_small_grid(self):
        for analysis in (self.physical, self.synthetic):
            self.assertEqual(len(analysis["prefix_certificates"]), 4)
            for certificate in analysis["prefix_certificates"]:
                self.assertTrue(certificate["verified"])
                self.assertEqual(
                    decode_pair(certificate["sum_delta"]),
                    decode_pair(certificate["rank"]),
                )
                self.assertEqual(
                    profile(certificate["sum_delta_by_degree"]),
                    profile(certificate["rank_by_degree"]),
                )

    def test_04_all_valid_subrectangle_identities_small_grid(self):
        for analysis in (self.physical, self.synthetic):
            checks = analysis["rectangle_checks"]
            self.assertEqual(checks["status"], "complete_rectangle_checks")
            self.assertEqual(decode_pair(checks["required_checks"]), 9)
            self.assertEqual(len(checks["exhaustive_checks"]), 9)
            for certificate in checks["exhaustive_checks"]:
                self.assertTrue(certificate["verified"])
                self.assertEqual(
                    decode_pair(certificate["sum_delta"]),
                    decode_pair(certificate["rank_difference"]),
                )
                self.assertEqual(
                    profile(certificate["sum_delta_by_degree"]),
                    profile(certificate["rank_difference_by_degree"]),
                )

    def test_05_row_and_column_telescoping(self):
        for analysis in (self.physical, self.synthetic):
            accumulations = analysis["row_column_accumulations"]
            self.assertEqual(len(accumulations["rows"]), 4)
            self.assertEqual(len(accumulations["columns"]), 4)
            for entry in accumulations["rows"] + accumulations["columns"]:
                self.assertTrue(entry["verified"])
                self.assertEqual(
                    decode_pair(entry["cumulative_delta"]),
                    decode_pair(entry["rank_edge_difference"]),
                )
                self.assertEqual(
                    profile(entry["cumulative_delta_by_degree"]),
                    profile(entry["rank_edge_difference_by_degree"]),
                )

    def test_06_degree_resolved_local_identities(self):
        for analysis in (self.physical, self.synthetic):
            for row in analysis["cell_ledger"]:
                q = profile(row["q_by_degree"])
                omega = profile(row["omega_by_degree"])
                delta = profile(row["delta_by_degree"])
                rank_difference = profile(row["mixed_rank_difference_by_degree"])
                expected = {k: q.get(k, 0) - omega.get(k, 0)
                            for k in set(q) | set(omega)}
                expected = {k: v for k, v in expected.items() if v}
                self.assertEqual(delta, expected)
                self.assertEqual(delta, rank_difference)
                self.assertEqual(sum(q.values()), decode_pair(row["q"]))
                self.assertEqual(sum(omega.values()), decode_pair(row["omega"]))

    def test_07_degree_resolved_prefix_and_rectangle_identities(self):
        for analysis in (self.physical, self.synthetic):
            for certificate in analysis["prefix_certificates"]:
                self.assertEqual(
                    profile(certificate["sum_delta_by_degree"]),
                    profile(certificate["rank_by_degree"]),
                )
            for certificate in analysis["rectangle_checks"]["exhaustive_checks"]:
                self.assertEqual(
                    profile(certificate["sum_delta_by_degree"]),
                    profile(certificate["rank_difference_by_degree"]),
                )
        self.assertIn(1, profile(self.synthetic["degree_profiles"]["totals"]["delta_by_degree"]))
        self.assertIn(2, profile(self.synthetic["degree_profiles"]["totals"]["delta_by_degree"]))

    def test_08_degree_totals_reconcile_aggregate(self):
        for analysis in (self.physical, self.synthetic):
            totals = analysis["totals"]
            degree_totals = analysis["degree_profiles"]["totals"]
            self.assertTrue(degree_totals["degree_totals_verified"])
            self.assertEqual(
                profile(degree_totals["delta_by_degree"]),
                profile(degree_totals["terminal_rank_by_degree"]),
            )
            self.assertEqual(
                sum(profile(degree_totals["q_by_degree"]).values()),
                decode_pair(totals["sum_q"]),
            )
            self.assertEqual(
                sum(profile(degree_totals["omega_by_degree"]).values()),
                decode_pair(totals["sum_omega"]),
            )
            self.assertEqual(
                sum(profile(degree_totals["delta_by_degree"]).values()),
                decode_pair(totals["final_rank"]),
            )
            self.assertEqual(
                decode_pair(totals["sum_delta"]),
                decode_pair(totals["final_rank"]),
            )

    def test_09_boundary_axes_formal_zero_and_no_fake_cells(self):
        analysis = self.physical
        rows = self.ledger_by_key(analysis)
        self.assertEqual(set(rows), {(1, 0), (1, 1), (2, 0), (2, 1)})
        self.assertFalse(any(key[0] < 1 or key[1] < 0 for key in rows))
        conventions = analysis["boundary_conventions"]
        self.assertTrue(conventions["no_fabricated_cells"])
        self.assertEqual(len(conventions["formal_zero_values"]), 2)
        self.assertIn("r[0,D] = 0", conventions["formal_zero_values"])
        self.assertIn("r[L,-1] = 0", conventions["formal_zero_values"])
        ranks = {key: decode_pair(row["rank"]) for key, row in rows.items()}
        self.assertEqual(decode_pair(rows[(1, 0)]["q"]), ranks[(1, 0)])
        self.assertEqual(
            decode_pair(rows[(2, 0)]["q"]),
            ranks[(2, 0)] - ranks[(1, 0)],
        )
        self.assertEqual(
            decode_pair(rows[(1, 1)]["q"]),
            ranks[(1, 1)] - ranks[(1, 0)],
        )
        self.assertEqual(len(self.physical_bifiltration["boundary_cells"]), 3)

    def test_10_nonhomogeneous_sources_are_unresolved_with_offending_id(self):
        bifiltration = synthetic_bifiltration()
        bifiltration["squares"][0]["mixed_overlap"]["complement_basis"][0][
            "trace_terms"
        ].append(MONO_A)
        result = analyze_exact_bifiltration_rank_ledger(
            synthetic_filtration(), bifiltration
        )
        self.assertEqual(result["status"], "unresolved_nonhomogeneous_basis_vector")
        self.assertIn("PHASE32", result["offending_basis_id"])

        filtration = synthetic_filtration()
        filtration["cells"][1]["basis_entries"][1]["trace_terms"].append(MONO_A)
        result = analyze_exact_bifiltration_rank_ledger(
            filtration, synthetic_bifiltration()
        )
        self.assertEqual(result["status"], "unresolved_nonhomogeneous_basis_vector")
        self.assertIn("PHASE30", result["offending_basis_id"])

    def test_11_missing_duplicate_and_nonrectangular_sources(self):
        source = synthetic_filtration()
        missing = copy.deepcopy(source)
        missing["cells"] = [
            cell for cell in missing["cells"]
            if decode_pair(cell["substitution_bound"]) != 2
            or decode_pair(cell["multiplier_bound"]) != 1
        ]
        result = analyze_exact_bifiltration_rank_ledger(missing, synthetic_bifiltration())
        self.assertEqual(result["status"], "unresolved_non_rectangular_filtration")

        duplicate = copy.deepcopy(source)
        duplicate["cells"].append(copy.deepcopy(duplicate["cells"][0]))
        result = analyze_exact_bifiltration_rank_ledger(duplicate, synthetic_bifiltration())
        self.assertEqual(result["status"], "unresolved_duplicate_filtration_cell")

        bifiltration = synthetic_bifiltration()
        missing_square = copy.deepcopy(bifiltration)
        missing_square["squares"] = []
        result = analyze_exact_bifiltration_rank_ledger(source, missing_square)
        self.assertEqual(result["status"], "unresolved_empty_source")

        duplicate_square = copy.deepcopy(bifiltration)
        duplicate_square["squares"].append(copy.deepcopy(duplicate_square["squares"][0]))
        result = analyze_exact_bifiltration_rank_ledger(source, duplicate_square)
        self.assertEqual(result["status"], "unresolved_duplicate_square")

    def test_12_mismatched_configurations_are_unresolved(self):
        source = synthetic_filtration()
        bifiltration = synthetic_bifiltration()
        wrong_dimension = copy.deepcopy(bifiltration)
        wrong_dimension["dimension"] = paired(3)
        result = analyze_exact_bifiltration_rank_ledger(source, wrong_dimension)
        self.assertEqual(result["status"], "unresolved_source_config_mismatch")

        wrong_count = copy.deepcopy(bifiltration)
        wrong_count["cell_count"] = paired(7)
        result = analyze_exact_bifiltration_rank_ledger(source, wrong_count)
        self.assertEqual(result["status"], "unresolved_source_config_mismatch")

        wrong_status = copy.deepcopy(bifiltration)
        wrong_status["source_filtration_status"] = "partial_filtration_cell_unresolved"
        result = analyze_exact_bifiltration_rank_ledger(source, wrong_status)
        self.assertEqual(result["status"], "unresolved_source_config_mismatch")

        wrong_dimension_value = copy.deepcopy(bifiltration)
        wrong_dimension_value["squares"][0]["dimensions"]["terminal"] = paired(6)
        result = analyze_exact_bifiltration_rank_ledger(source, wrong_dimension_value)
        self.assertEqual(result["status"], "unresolved_square_dimension_mismatch")

    def test_13_caps_return_explicit_unresolved_status(self):
        source = synthetic_filtration()
        bifiltration = synthetic_bifiltration()
        capped = analyze_exact_bifiltration_rank_ledger(
            source, bifiltration, max_rectangle_checks=8
        )
        self.assertEqual(capped["status"], "unresolved_rectangle_cap")
        self.assertGreater(len(capped["rectangle_checks"]["corner_checks"]), 0)
        self.assertEqual(capped["rectangle_checks"]["exhaustive_checks"], [])

        cell_cap = analyze_exact_bifiltration_rank_ledger(
            source, bifiltration, max_cells=3
        )
        self.assertEqual(cell_cap["status"], "unresolved_cell_cap")

        degree_cap = analyze_exact_bifiltration_rank_ledger(
            source, bifiltration, max_degree_vector_checks=1
        )
        self.assertEqual(degree_cap["status"], "unresolved_degree_vector_cap")

        with self.assertRaises(ValueError):
            analyze_exact_bifiltration_rank_ledger(source, bifiltration, max_squares=0)

        selected_cap = analyze_exact_bifiltration_rank_ledger(
            source,
            bifiltration,
            max_rectangle_checks=4,
            rectangles=[(1, 2, 0, 0), (1, 2, 0, 1), (2, 2, 1, 1)],
        )
        self.assertEqual(selected_cap["status"], "unresolved_rectangle_cap")

    def test_14_exact_integer_and_rational_input_handling(self):
        self.assertEqual(
            self.synthetic["exact_rational_conventions"]["example_one_half"],
            {"numerator": paired(1), "denominator": paired(2)},
        )
        coefficient = phase29._fraction(
            synthetic_filtration()["cells"][0]["basis_entries"][1]["trace_terms"][1][
                "coefficient"
            ],
            "coefficient",
        )
        self.assertEqual(coefficient, Fraction(1, 2))
        self.assertFalse(contains_float(self.physical))
        self.assertFalse(contains_float(self.synthetic))

        paired_cap_result = analyze_exact_bifiltration_rank_ledger(
            synthetic_filtration(),
            synthetic_bifiltration(),
            max_rectangle_checks=paired(DEFAULT_MAX_RECTANGLE_CHECKS),
        )
        self.assertEqual(paired_cap_result, self.synthetic)

        first = check_rectangle(self.synthetic, 1, 2, 0, 1)
        second = check_rectangle(
            self.synthetic, paired(1), paired(2), paired(0), paired(1)
        )
        self.assertEqual(first, second)
        self.assertEqual(decode_pair(first["sum_delta"]), 5)

    def test_15_deterministic_input_order_independent(self):
        source = synthetic_filtration()
        bifiltration = synthetic_bifiltration()
        reversed_source = copy.deepcopy(source)
        reversed_source["cells"].reverse()
        reversed_bifiltration = copy.deepcopy(bifiltration)
        reversed_bifiltration["squares"].reverse()
        reversed_bifiltration["boundary_cells"].reverse()
        self.assertEqual(
            analyze_exact_bifiltration_rank_ledger(source, bifiltration),
            analyze_exact_bifiltration_rank_ledger(
                reversed_source, reversed_bifiltration
            ),
        )
        self.assertEqual(
            analyze_exact_bifiltration_rank_ledger(source, bifiltration),
            analyze_exact_bifiltration_rank_ledger(source, bifiltration),
        )

    def test_16_malformed_empty_and_wrong_dimension_sources(self):
        bifiltration = synthetic_bifiltration()
        with self.assertRaises(TypeError):
            analyze_exact_bifiltration_rank_ledger(None, bifiltration)
        with self.assertRaises(TypeError):
            analyze_exact_bifiltration_rank_ledger(synthetic_filtration(), None)

        partial = copy.deepcopy(synthetic_filtration())
        partial["status"] = "partial_filtration_cell_unresolved"
        result = analyze_exact_bifiltration_rank_ledger(partial, bifiltration)
        self.assertEqual(result["status"], "unresolved_source_filtration")

        empty = copy.deepcopy(synthetic_filtration())
        empty["cells"] = []
        result = analyze_exact_bifiltration_rank_ledger(empty, bifiltration)
        self.assertEqual(result["status"], "unresolved_empty_source")

        malformed = copy.deepcopy(synthetic_filtration())
        malformed["cells"][0]["rank_by_total_word_degree"] = []
        with self.assertRaises(TypeError):
            analyze_exact_bifiltration_rank_ledger(malformed, bifiltration)

        wrong_shape = copy.deepcopy(bifiltration)
        del wrong_shape["squares"][0]["dimensions"]["terminal"]
        with self.assertRaises((KeyError, TypeError, ValueError)):
            analyze_exact_bifiltration_rank_ledger(synthetic_filtration(), wrong_shape)

    def test_17_selected_rectangle_query_api(self):
        certificate = check_rectangle(self.physical, 1, 2, 0, 1)
        self.assertTrue(certificate["verified"])
        self.assertEqual(decode_pair(certificate["rank_difference"]), 120)
        self.assertEqual(
            profile(certificate["sum_delta_by_degree"]),
            profile(certificate["rank_difference_by_degree"]),
        )
        selected = analyze_exact_bifiltration_rank_ledger(
            synthetic_filtration(),
            synthetic_bifiltration(),
            verify_all_rectangles=False,
            rectangles=[(2, 2, 1, 1)],
        )
        self.assertEqual(selected["status"], "complete_exact_bifiltration_rank_ledger")
        self.assertEqual(selected["rectangle_checks"]["status"],
                         "complete_selected_rectangle_checks")
        self.assertEqual(selected["rectangle_checks"]["exhaustive"], False)

    def test_18_bounded_wrapper_matches_staged_analysis(self):
        wrapped = analyze_bounded_exact_bifiltration_rank_ledger(physical_arguments())
        self.assert_complete(wrapped)
        self.assertEqual(wrapped, self.physical)

    def test_19_corner_certificates_survive_rectangle_cap(self):
        capped = analyze_exact_bifiltration_rank_ledger(
            synthetic_filtration(),
            synthetic_bifiltration(),
            max_rectangle_checks=2,
        )
        self.assertEqual(capped["status"], "unresolved_rectangle_cap")
        self.assertTrue(capped["rectangle_checks"]["corner_checks"])
        for certificate in capped["rectangle_checks"]["corner_checks"]:
            self.assertTrue(certificate["verified"])
            self.assertEqual(
                decode_pair(certificate["sum_delta"]),
                decode_pair(certificate["rank_difference"]),
            )
        tiny_cap = analyze_exact_bifiltration_rank_ledger(
            synthetic_filtration(),
            synthetic_bifiltration(),
            max_rectangle_checks=1,
        )
        self.assertEqual(tiny_cap["status"], "unresolved_rectangle_cap")


if __name__ == "__main__":
    unittest.main(verbosity=2)
