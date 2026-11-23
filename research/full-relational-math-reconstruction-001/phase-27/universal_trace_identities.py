"""Universal trace identities for generic matrices of a fixed dimension.

Phase 27 constructs the fundamental trace identity (FTI) for d x d matrices,
substitutes arbitrary noncommutative matrix words, and verifies the resulting
trace polynomial by exact expansion in independent generic matrix entries.

No sampled matrices or finite family data are used. A successful verification
is a polynomial identity over a characteristic-zero commutative coefficient
field and therefore holds for every tuple of d x d matrices over that field.
"""
from __future__ import annotations

from collections import defaultdict
from itertools import permutations, product
from math import factorial
import re


_PAIRED_RE = re.compile(r"(-?)<([0-9A-Z]+)_2\|([0-9A-Z]+)_3>")
_DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def _paired(value: int) -> str:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("paired integer input must be an integer")
    sign = "-" if value < 0 else ""
    magnitude = abs(value)

    def encode(number: int, base: int) -> str:
        if number == 0:
            return "0"
        out = ""
        while number:
            number, digit = divmod(number, base)
            out = _DIGITS[digit] + out
        return out

    return f"{sign}<{encode(magnitude, 2)}_2|{encode(magnitude, 3)}_3>"


def _integer(value, name: str, minimum: int | None = 0, maximum: int | None = None) -> int:
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
    if (minimum is not None and result < minimum) or (maximum is not None and result > maximum):
        lower = f">= {minimum}" if minimum is not None else "unbounded below"
        upper = f" and <= {maximum}" if maximum is not None else ""
        raise ValueError(f"{name} must be {lower}{upper}")
    return result


def _canonical_cyclic_word(word: tuple[int, ...]) -> tuple[int, ...]:
    if not word:
        raise ValueError("trace words must be nonempty")
    return min(word[index:] + word[:index] for index in range(len(word)))


def _permutation_sign(permutation: tuple[int, ...]) -> int:
    inversions = sum(
        permutation[i] > permutation[j]
        for i in range(len(permutation))
        for j in range(i + 1, len(permutation))
    )
    return -1 if inversions % 2 else 1


def _permutation_cycles(permutation: tuple[int, ...]) -> tuple[tuple[int, ...], ...]:
    seen = set()
    cycles = []
    for start in range(len(permutation)):
        if start in seen:
            continue
        cycle = []
        current = start
        while current not in seen:
            seen.add(current)
            cycle.append(current)
            current = permutation[current]
        cycles.append(tuple(cycle))
    return tuple(cycles)


def _normalise_substitutions(dimension: int, substitutions) -> tuple[tuple[int, ...], ...]:
    if not isinstance(substitutions, (list, tuple)):
        raise TypeError("substitutions must be a sequence of matrix words")
    expected = dimension + 1
    if len(substitutions) != expected:
        raise ValueError(f"the fundamental trace identity requires exactly {expected} substitutions")
    normalised = []
    for index, word in enumerate(substitutions):
        if not isinstance(word, (list, tuple)) or not word:
            raise ValueError(f"substitution {index} must be a nonempty matrix word")
        normalised.append(tuple(_integer(item, f"substitution {index} generator", 0) for item in word))
    return tuple(normalised)


def _build_fundamental_terms(dimension: int, substitutions):
    """Return canonical trace-polynomial terms as {factor_tuple: integer}.

    For each permutation sigma, a cycle (i, sigma(i), ...) contributes the
    trace of the concatenation of the substituted matrix words in that cycle.
    Trace cyclicity and commutativity of scalar trace factors are canonicalised.
    Reversal is deliberately not identified.
    """
    words = _normalise_substitutions(dimension, substitutions)
    combined = defaultdict(int)
    for permutation in permutations(range(dimension + 1)):
        factors = []
        for cycle in _permutation_cycles(permutation):
            concatenated = tuple(
                generator
                for substitution_index in cycle
                for generator in words[substitution_index]
            )
            factors.append(_canonical_cyclic_word(concatenated))
        monomial = tuple(sorted(factors))
        combined[monomial] += _permutation_sign(permutation)
    return words, {key: coefficient for key, coefficient in combined.items() if coefficient}


def _encode_trace_terms(raw_terms):
    encoded = []
    for factors, coefficient in sorted(raw_terms.items()):
        encoded.append({
            "coefficient": _paired(coefficient),
            "trace_factors": [[_paired(generator) for generator in word] for word in factors],
            "label": " * ".join(
                "tr(" + " ".join(f"M{generator}" for generator in word) + ")"
                for word in factors
            ),
        })
    return encoded


def generate_fundamental_trace_identity(
    dimension: int,
    substitutions,
    max_identity_permutations: int = 100_000,
):
    """Construct the d-dimensional fundamental trace identity.

    The identity is
      sum_{sigma in S_(d+1)} sign(sigma) * product_{cycles c} tr(W_c) = 0,
    where W_c is the concatenation of the supplied matrix words along c.

    The construction is universal for arbitrary d x d matrices over a
    characteristic-zero commutative field. A permutation cap is reported as
    unresolved, never as absence of an identity.
    """
    dimension = _integer(dimension, "dimension", 1)
    max_identity_permutations = _integer(
        max_identity_permutations, "max_identity_permutations", 1
    )
    substitutions = _normalise_substitutions(dimension, substitutions)
    permutation_count = factorial(dimension + 1)
    base = {
        "theorem": "fundamental_trace_identity",
        "dimension": _paired(dimension),
        "substitutions": [
            [_paired(generator) for generator in word] for word in substitutions
        ],
        "required_permutations": _paired(permutation_count),
        "permutation_cap": _paired(max_identity_permutations),
        "coefficient_field_assumption": "commutative characteristic-zero field",
        "universal_identity": True,
        "scope": "all tuples of square matrices of the declared dimension",
    }
    if permutation_count > max_identity_permutations:
        return {
            **base,
            "status": "unresolved_permutation_cap",
            "terms": [],
            "distinct_trace_monomials": _paired(0),
            "reason": "the complete permutation sum exceeds the configured construction cap",
        }
    _, raw_terms = _build_fundamental_terms(dimension, substitutions)
    return {
        **base,
        "status": "identity_constructed",
        "terms": _encode_trace_terms(raw_terms),
        "distinct_trace_monomials": _paired(len(raw_terms)),
        "formal_identity": (
            "sum_{sigma in S_(d+1)} sign(sigma) * product_{cycles c} tr(W_c) = 0"
        ),
    }


def _normalise_trace_terms(trace_terms, matrix_count: int | None):
    if not isinstance(trace_terms, (list, tuple)):
        raise TypeError("trace_terms must be a sequence")
    if matrix_count is not None:
        matrix_count = _integer(matrix_count, "matrix_count", 1)
    combined = defaultdict(int)
    max_generator = -1
    for term_index, term in enumerate(trace_terms):
        if not isinstance(term, dict):
            raise TypeError(f"trace term {term_index} must be a mapping")
        coefficient = _integer(term.get("coefficient"), f"trace term {term_index} coefficient", minimum=None)
        factors = term.get("trace_factors")
        if not isinstance(factors, (list, tuple)):
            raise TypeError(f"trace term {term_index} trace_factors must be a sequence")
        canonical_factors = []
        for factor_index, word in enumerate(factors):
            if not isinstance(word, (list, tuple)) or not word:
                raise ValueError(f"trace factor {factor_index} in term {term_index} must be nonempty")
            parsed = tuple(
                _integer(item, f"trace term {term_index} generator", 0)
                for item in word
            )
            if matrix_count is not None and any(item >= matrix_count for item in parsed):
                raise ValueError("trace word uses a generator outside matrix_count")
            max_generator = max(max_generator, *parsed)
            canonical_factors.append(_canonical_cyclic_word(parsed))
        monomial = tuple(sorted(canonical_factors))
        combined[monomial] += coefficient
    return {key: value for key, value in combined.items() if value}, max_generator + 1


def _expand_trace_product(dimension: int, factors: tuple[tuple[int, ...], ...]):
    total_degree = sum(len(word) for word in factors)
    for indices in product(range(dimension), repeat=total_degree):
        offset = 0
        entries = []
        for word in factors:
            length = len(word)
            cycle_indices = indices[offset:offset + length]
            offset += length
            for position, generator in enumerate(word):
                row = cycle_indices[position]
                column = cycle_indices[(position + 1) % length]
                entries.append((generator, row, column))
        yield tuple(sorted(entries))


def verify_trace_polynomial_identity(
    dimension: int,
    trace_terms,
    max_expansion_terms: int = 1_000_000,
    matrix_count: int | None = None,
):
    """Verify a trace polynomial by exact generic-matrix-entry expansion.

    Each generator M_i is represented by a matrix of independent commuting
    indeterminates x[i,row,column]. Every trace-product is expanded exactly
    into scalar monomials. A zero residual proves the identity for all d x d
    matrices over a characteristic-zero commutative coefficient field.

    max_expansion_terms counts the deterministic number of index assignments;
    hitting it returns unresolved, never a negative result.
    """
    dimension = _integer(dimension, "dimension", 1)
    max_expansion_terms = _integer(max_expansion_terms, "max_expansion_terms", 1)
    normalised_matrix_count = (
        None if matrix_count is None else _integer(matrix_count, "matrix_count", 1)
    )
    raw_terms, inferred_matrix_count = _normalise_trace_terms(
        trace_terms, normalised_matrix_count
    )
    resolved_matrix_count = (
        normalised_matrix_count
        if normalised_matrix_count is not None
        else max(1, inferred_matrix_count)
    )
    required_expansions = sum(
        dimension ** sum(len(word) for word in factors)
        for factors in raw_terms
    )
    report = {
        "method": "exact_generic_matrix_entry_expansion",
        "dimension": _paired(dimension),
        "matrix_count": _paired(resolved_matrix_count),
        "coefficient_ring": "Z embedded in a commutative characteristic-zero field",
        "required_index_assignments": _paired(required_expansions),
        "expansion_cap": _paired(max_expansion_terms),
        "trace_monomials": _paired(len(raw_terms)),
        "universal_claim": True,
        "scope": "all d x d matrices represented by independent generic entries",
        "work_accounting": (
            "Counts exact generic index assignments; it is a deterministic work "
            "proxy, not a wall-clock or coefficient-bit-complexity bound."
        ),
    }
    if required_expansions > max_expansion_terms:
        return {
            **report,
            "status": "unresolved_expansion_cap",
            "verified": False,
            "universal_identity": None,
            "reason": "exact generic-entry expansion exceeds the configured work cap",
        }

    residual = defaultdict(int)
    expanded_assignments = 0
    for factors, coefficient in raw_terms.items():
        for monomial in _expand_trace_product(dimension, factors):
            residual[monomial] += coefficient
            expanded_assignments += 1
    nonzero = {monomial: coefficient for monomial, coefficient in residual.items() if coefficient}
    if nonzero:
        examples = []
        for monomial, coefficient in sorted(nonzero.items())[:20]:
            examples.append({
                "coefficient": _paired(coefficient),
                "matrix_entry_factors": [
                    [_paired(matrix), _paired(row), _paired(column)]
                    for matrix, row, column in monomial
                ],
            })
        return {
            **report,
            "status": "identity_rejected_nonzero_generic_residual",
            "verified": False,
            "universal_identity": False,
            "expanded_index_assignments": _paired(expanded_assignments),
            "nonzero_residual_monomials": _paired(len(nonzero)),
            "residual_examples": examples,
        }
    return {
        **report,
        "status": "universally_verified_identity",
        "verified": True,
        "universal_identity": True,
        "expanded_index_assignments": _paired(expanded_assignments),
        "nonzero_residual_monomials": _paired(0),
        "exact_residual": "0",
        "certificate": {
            "generic_matrix_entries": "independent commuting indeterminates x[matrix,row,column]",
            "every_trace_product_expanded_exactly": True,
            "all_sparse_polynomial_coefficients_zero": True,
            "proof_scope": (
                "The expanded formal polynomial is identically zero. Therefore "
                "the trace identity holds for every substitution of d x d "
                "matrices over a characteristic-zero commutative coefficient field."
            ),
        },
    }


def prove_fundamental_trace_identity(
    dimension: int,
    substitutions,
    max_identity_permutations: int = 100_000,
    max_expansion_terms: int = 1_000_000,
):
    """Construct and generically verify one substituted FTI instance."""
    identity = generate_fundamental_trace_identity(
        dimension, substitutions, max_identity_permutations
    )
    if identity["status"] != "identity_constructed":
        return {
            "status": identity["status"],
            "identity": identity,
            "verification": None,
            "universal_identity": True,
        }
    verification = verify_trace_polynomial_identity(
        dimension,
        identity["terms"],
        max_expansion_terms=max_expansion_terms,
    )
    if verification["status"] == "universally_verified_identity":
        status = "universally_verified_identity"
    elif verification["status"].startswith("unresolved_"):
        status = verification["status"]
    else:
        status = "generated_identity_verification_failed"
    return {
        "status": status,
        "theorem": "fundamental_trace_identity",
        "universal_identity": True,
        "identity": identity,
        "verification": verification,
    }
