"""Bounded catalog of universally verified fundamental trace identities.

Phase 28 enumerates word substitutions from a finite noncommutative alphabet,
canonicalises the alternating substitution set and resulting trace polynomial,
deduplicates identities up to nonzero rational scalar, and verifies every
catalogued identity by Phase 27's exact generic-matrix-entry expansion.

Completeness is only relative to the declared dimension, generator alphabet,
word-length bound and fundamental-identity construction. This is not claimed
to be a complete basis of all trace identities.
"""
from __future__ import annotations

from collections import defaultdict
from itertools import combinations, product
from math import comb, factorial, gcd
import re

import universal_trace_identities as phase27


_PAIRED_RE = re.compile(r"(-?)<([0-9A-Z]+)_2\|([0-9A-Z]+)_3>")
_DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def _paired(value: int) -> str:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("paired integer input must be an integer")
    sign = "-" if value < 0 else ""
    value = abs(value)

    def encode(number: int, base: int) -> str:
        if number == 0:
            return "0"
        out = ""
        while number:
            number, digit = divmod(number, base)
            out = _DIGITS[digit] + out
        return out

    return f"{sign}<{encode(value, 2)}_2|{encode(value, 3)}_3>"


def _integer(value, name: str, minimum: int | None = 0) -> int:
    if isinstance(value, bool):
        raise TypeError(f"{name} must be an integer, not bool")
    if isinstance(value, int):
        result = value
    elif isinstance(value, str):
        match = _PAIRED_RE.fullmatch(value)
        if not match:
            raise ValueError(f"{name} must be an integer or paired binary/ternary integer")
        sign, binary, ternary = match.groups()
        binary_value = int(binary, 2)
        ternary_value = int(ternary, 3)
        if binary_value != ternary_value:
            raise ValueError(f"{name} has inconsistent binary and ternary components")
        result = -binary_value if sign else binary_value
    else:
        raise TypeError(f"{name} must be an integer or paired integer string")
    if minimum is not None and result < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    return result


def _decode_paired(value, name: str = "paired integer") -> int:
    return _integer(value, name, minimum=None)


def _word_catalog(generator_count: int, max_word_length: int) -> tuple[tuple[int, ...], ...]:
    return tuple(
        word
        for length in range(1, max_word_length + 1)
        for word in product(range(generator_count), repeat=length)
    )


def word_catalog(generator_count: int, max_word_length: int) -> list[list[str]]:
    """Return the deterministic nonempty word catalog in length-lexicographic order."""
    generator_count = _integer(generator_count, "generator_count", 1)
    max_word_length = _integer(max_word_length, "max_word_length", 1)
    return [
        [_paired(generator) for generator in word]
        for word in _word_catalog(generator_count, max_word_length)
    ]


def _word_label(word: tuple[int, ...]) -> str:
    return "·".join(f"M{generator}" for generator in word)


def _canonical_cyclic_word(word: tuple[int, ...]) -> tuple[int, ...]:
    if not word:
        raise ValueError("trace words must be nonempty")
    return min(word[index:] + word[:index] for index in range(len(word)))


def _canonical_trace_polynomial_signature(trace_terms):
    """Canonical integer signature up to nonzero rational scalar.

    The key uses only trace cyclicity, commutativity of scalar trace factors,
    exact coefficient collection, common integer gcd reduction and global sign
    normalisation. Matrix word reversal and generator commutation are not used.
    """
    coefficients = defaultdict(int)
    for term_index, term in enumerate(trace_terms):
        if not isinstance(term, dict):
            raise TypeError(f"trace term {term_index} must be a mapping")
        coefficient = _decode_paired(term.get("coefficient"), f"trace term {term_index} coefficient")
        factors = term.get("trace_factors")
        if not isinstance(factors, (list, tuple)):
            raise TypeError(f"trace term {term_index} trace_factors must be a sequence")
        canonical_factors = []
        for factor_index, raw_word in enumerate(factors):
            if not isinstance(raw_word, (list, tuple)) or not raw_word:
                raise ValueError(f"trace factor {factor_index} in term {term_index} must be a nonempty word")
            word = tuple(
                _decode_paired(generator, f"trace factor {factor_index} generator")
                for generator in raw_word
            )
            if any(generator < 0 for generator in word):
                raise ValueError("matrix generator indices must be nonnegative")
            canonical_factors.append(_canonical_cyclic_word(word))
        coefficients[tuple(sorted(canonical_factors))] += coefficient

    coefficients = {
        monomial: coefficient
        for monomial, coefficient in coefficients.items()
        if coefficient
    }
    if not coefficients:
        return tuple()

    divisor = 0
    for coefficient in coefficients.values():
        divisor = gcd(divisor, abs(coefficient))
    first_monomial = min(coefficients)
    orientation = 1 if coefficients[first_monomial] > 0 else -1
    return tuple(
        (monomial, orientation * coefficient // divisor)
        for monomial, coefficient in sorted(coefficients.items())
    )


def _base_report(
    dimension: int,
    generator_count: int,
    max_word_length: int,
    max_word_catalog_size: int,
    max_substitution_sets: int,
    max_identity_permutations: int,
    max_expansion_terms_per_identity: int,
    max_total_expansion_terms: int,
):
    word_count = sum(generator_count ** length for length in range(1, max_word_length + 1))
    permutation_count = factorial(dimension + 1)
    substitution_count = comb(word_count, dimension + 1) if word_count >= dimension + 1 else 0
    return {
        "schema": "universe.universal-trace-identity-catalog.v1",
        "dimension": _paired(dimension),
        "generator_count": _paired(generator_count),
        "maximum_word_length": _paired(max_word_length),
        "word_catalog_count": _paired(word_count),
        "word_catalog_cap": _paired(max_word_catalog_size),
        "fundamental_identity_permutations": _paired(permutation_count),
        "permutation_cap": _paired(max_identity_permutations),
        "candidate_substitution_sets": _paired(substitution_count),
        "substitution_set_cap": _paired(max_substitution_sets),
        "per_identity_expansion_cap": _paired(max_expansion_terms_per_identity),
        "total_expansion_cap": _paired(max_total_expansion_terms),
        "coefficient_field_assumption": "commutative characteristic-zero field",
        "verification_method": "exact generic matrix entry expansion from Phase 27",
        "sampled_matrix_data_used": False,
        "universal_identity_scope": "all square matrices of the declared dimension",
        "catalog_completeness_scope": (
            "all combinations of dimension+1 distinct nonempty words over the "
            "declared generator alphabet with length <= maximum_word_length, "
            "after fundamental-identity permutation symmetry"
        ),
        "not_claimed": (
            "a complete basis or generating set for all trace identities; "
            "substitutions that are linear combinations of words; identities "
            "outside the declared dimension, alphabet or word-length bound"
        ),
    }


def enumerate_universal_trace_identity_catalog(
    dimension: int,
    generator_count: int = 2,
    max_word_length: int = 2,
    max_word_catalog_size: int = 32,
    max_substitution_sets: int = 4096,
    max_identity_permutations: int = 100_000,
    max_expansion_terms_per_identity: int = 1_000_000,
    max_total_expansion_terms: int = 5_000_000,
):
    """Enumerate and exactly verify a bounded FTI substitution catalog.

    The FTI is alternating and multilinear in its d+1 arguments. Therefore
    permutations of one substitution set change only the global sign, which
    is normalised away. Repeated substitutions yield the zero alternating
    expression and are excluded. Distinct generated trace polynomials are
    deduplicated up to a nonzero rational scalar.

    Any configured cap returns an explicit unresolved status. A total
    verification cap may leave a verified prefix; all unverified identities
    remain listed as unresolved and completeness is not claimed.
    """
    dimension = _integer(dimension, "dimension", 1)
    generator_count = _integer(generator_count, "generator_count", 1)
    max_word_length = _integer(max_word_length, "max_word_length", 1)
    max_word_catalog_size = _integer(max_word_catalog_size, "max_word_catalog_size", 1)
    max_substitution_sets = _integer(max_substitution_sets, "max_substitution_sets", 1)
    max_identity_permutations = _integer(max_identity_permutations, "max_identity_permutations", 1)
    max_expansion_terms_per_identity = _integer(
        max_expansion_terms_per_identity, "max_expansion_terms_per_identity", 1
    )
    max_total_expansion_terms = _integer(
        max_total_expansion_terms, "max_total_expansion_terms", 1
    )

    report = _base_report(
        dimension,
        generator_count,
        max_word_length,
        max_word_catalog_size,
        max_substitution_sets,
        max_identity_permutations,
        max_expansion_terms_per_identity,
        max_total_expansion_terms,
    )
    word_count = _decode_paired(report["word_catalog_count"])
    permutation_count = _decode_paired(report["fundamental_identity_permutations"])
    candidate_count = _decode_paired(report["candidate_substitution_sets"])

    if word_count > max_word_catalog_size:
        return {
            **report,
            "status": "unresolved_word_catalog_cap",
            "words": [],
            "identities": [],
            "reason": "the complete bounded word catalog exceeds the configured cap",
        }
    if permutation_count > max_identity_permutations:
        return {
            **report,
            "status": "unresolved_permutation_cap",
            "words": word_catalog(generator_count, max_word_length),
            "identities": [],
            "reason": "the fundamental identity permutation sum exceeds the configured cap",
        }
    if candidate_count > max_substitution_sets:
        return {
            **report,
            "status": "unresolved_substitution_set_cap",
            "words": word_catalog(generator_count, max_word_length),
            "identities": [],
            "reason": "the complete substitution-set catalog exceeds the configured cap",
        }

    words = _word_catalog(generator_count, max_word_length)
    word_report = [
        {
            "word": [_paired(generator) for generator in word],
            "label": _word_label(word),
            "length": _paired(len(word)),
        }
        for word in words
    ]

    unique = {}
    collapsed_zero_sets = 0
    for substitution_set in combinations(words, dimension + 1):
        identity = phase27.generate_fundamental_trace_identity(
            dimension,
            [list(word) for word in substitution_set],
            max_identity_permutations=max_identity_permutations,
        )
        if identity["status"] != "identity_constructed":
            raise ArithmeticError(
                "Phase 27 identity construction returned unresolved after Phase 28 preflight"
            )
        signature = _canonical_trace_polynomial_signature(identity["terms"])
        if not signature:
            collapsed_zero_sets += 1
            continue
        if signature in unique:
            unique[signature]["substitution_aliases"].append(substitution_set)
            continue
        unique[signature] = {
            "substitutions": substitution_set,
            "substitution_aliases": [],
            "terms": identity["terms"],
            "signature": signature,
        }

    catalog = []
    used_expansion_terms = 0
    verified_count = 0
    rejected_count = 0
    unresolved_count = 0
    verification_stopped = False

    for index, item in enumerate(unique.values(), start=1):
        remaining_total = max_total_expansion_terms - used_expansion_terms
        if remaining_total <= 0:
            verification_stopped = True
            break

        identity_expansion_cap = min(
            max_expansion_terms_per_identity,
            remaining_total,
        )
        verification = phase27.verify_trace_polynomial_identity(
            dimension,
            item["terms"],
            max_expansion_terms=identity_expansion_cap,
            matrix_count=generator_count,
        )
        verification_status = verification["status"]

        if verification_status.startswith("unresolved_"):
            unresolved_count += 1
            verification_stopped = True
            catalog.append({
                "identity_id": f"FTI-{index:05d}",
                "substitutions": [
                    [_paired(generator) for generator in word]
                    for word in item["substitutions"]
                ],
                "substitution_aliases": [
                    [
                        [_paired(generator) for generator in word]
                        for word in alias
                    ]
                    for alias in item["substitution_aliases"]
                ],
                "terms": item["terms"],
                "status": verification_status,
                "verification": verification,
            })
            break

        expanded = _decode_paired(
            verification.get("expanded_index_assignments", "<0_2|0_3>"),
            "expanded_index_assignments",
        )
        used_expansion_terms += expanded

        if verification_status == "universally_verified_identity":
            verified_count += 1
        else:
            rejected_count += 1

        catalog.append({
            "identity_id": f"FTI-{index:05d}",
            "substitutions": [
                [_paired(generator) for generator in word]
                for word in item["substitutions"]
            ],
            "substitution_aliases": [
                [
                    [_paired(generator) for generator in word]
                    for word in alias
                ]
                for alias in item["substitution_aliases"]
            ],
            "terms": item["terms"],
            "trace_monomial_count": _paired(len(item["signature"])),
            "status": verification_status,
            "verification": verification,
        })

    if verification_stopped:
        # The current unresolved identity and all later unique identities are
        # intentionally not treated as verified.
        status = "partial_catalog_verification_unresolved"
        remaining_unique = len(unique) - len(catalog)
        unresolved_count += max(0, remaining_unique)
    elif rejected_count:
        status = "verification_rejected_generated_identity"
    elif candidate_count == 0:
        status = "complete_catalog_no_admissible_substitution_sets"
    elif not catalog and collapsed_zero_sets == candidate_count:
        status = "complete_catalog_all_candidates_collapsed_to_zero"
    else:
        status = "complete_catalog_verified"

    return {
        **report,
        "status": status,
        "words": word_report,
        "substitution_sets_processed": _paired(candidate_count),
        "unique_nonzero_trace_identities": _paired(len(unique)),
        "collapsed_zero_substitution_sets": _paired(collapsed_zero_sets),
        "duplicate_identity_substitution_sets": _paired(
            candidate_count - collapsed_zero_sets - len(unique)
        ),
        "verified_identity_count": _paired(verified_count),
        "rejected_identity_count": _paired(rejected_count),
        "unresolved_identity_count": _paired(unresolved_count),
        "identities": catalog,
        "verification_work": {
            "expanded_index_assignments": _paired(used_expansion_terms),
            "total_expansion_cap": _paired(max_total_expansion_terms),
            "remaining_expansion_budget": _paired(
                max_total_expansion_terms - used_expansion_terms
            ),
            "accounting": (
                "Exact generic-index assignments expanded by the Phase 27 "
                "verifier; deterministic work proxy, not wall-clock or "
                "coefficient-bit-complexity."
            ),
        },
        "proof_boundary": (
            "Every identity labelled universally_verified_identity was proved "
            "by exact generic-entry polynomial expansion. Catalog completeness "
            "is bounded to the declared word vocabulary and FTI substitutions; "
            "it is not a complete trace-identity basis."
        ),
    }
