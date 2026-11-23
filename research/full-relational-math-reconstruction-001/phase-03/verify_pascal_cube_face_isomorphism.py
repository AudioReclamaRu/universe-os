"""Exact finite check of the Lucas-support / hypercube-face bijection.

Input dimension is a binary word. All reported counts are emitted as
paired binary/ternary numerals; no decimal count is printed.
"""

from __future__ import annotations

import argparse
from itertools import product
from math import comb
from typing import Iterable

BASE2 = len("01")
BASE3 = len("012")
TERNARY_DIGITS = "012"


def to_base(value: int, base: int) -> str:
    if value < 0:
        raise ValueError("Only non-negative counts are supported.")
    if value == 0:
        return "0"
    digits: list[str] = []
    while value:
        value, remainder = divmod(value, base)
        digits.append(TERNARY_DIGITS[remainder] if base == BASE3 else "01"[remainder])
    return "".join(reversed(digits))


def dual(value: int) -> str:
    return f"<{to_base(value, BASE2)}_2 | {to_base(value, BASE3)}_3>"


def contains_vertex(face: tuple[str, ...], vertex: int) -> bool:
    for position, status in enumerate(face):
        bit = (vertex >> position) & 1
        if status == "-" and bit != 0:
            return False
        if status == "+" and bit != 1:
            return False
    return True


def is_subface(sub: tuple[str, ...], sup: tuple[str, ...]) -> bool:
    return all(sup_status == "0" or sub_status == sup_status
               for sub_status, sup_status in zip(sub, sup))


def face_rank(face: tuple[str, ...]) -> int:
    return face.count("0")


def build_pascal_faces(dimension: int) -> set[tuple[str, ...]]:
    faces: set[tuple[str, ...]] = set()
    limit = pow(BASE2, dimension)

    for n in range(limit):
        for k in range(n + 1):
            # Lucas' theorem in base two: C(n,k) is odd iff k's
            # one-bits are a subset of n's one-bits.
            if comb(n, k) % BASE2 != 1:
                continue
            if k & ~n:
                raise AssertionError("Lucas parity and bit-subset test disagree.")

            statuses: list[str] = []
            for position in range(dimension):
                n_bit = (n >> position) & 1
                k_bit = (k >> position) & 1
                if n_bit == 0:
                    statuses.append("-")
                elif k_bit == 0:
                    statuses.append("0")
                else:
                    statuses.append("+")
            faces.add(tuple(statuses))

    return faces


def count_relations(faces: Iterable[tuple[str, ...]]) -> tuple[int, int]:
    face_list = list(faces)
    comparable = 0
    covers = 0

    for sub in face_list:
        sub_rank = face_rank(sub)
        for sup in face_list:
            if is_subface(sub, sup):
                comparable += 1
                if sub != sup and face_rank(sup) - sub_rank == 1:
                    covers += 1

    return comparable, covers


def verify(dimension: int) -> dict[str, int]:
    if dimension < 1:
        raise ValueError("Dimension must be a non-empty binary word.")

    faces = build_pascal_faces(dimension)
    expected_faces = set(product(("-", "0", "+"), repeat=dimension))
    if faces != expected_faces:
        raise AssertionError("The Pascal-support map is not onto the ternary face set.")

    rank_counts = {
        d: sum(1 for face in faces if face_rank(face) == d)
        for d in range(dimension + 1)
    }
    for d, observed in rank_counts.items():
        expected = comb(dimension, d) * pow(BASE2, dimension - d)
        if observed != expected:
            raise AssertionError(f"Rank count failed at dimension {to_base(d, BASE2)}.")

    incidence_count = sum(
        1
        for face in faces
        for vertex in range(pow(BASE2, dimension))
        if contains_vertex(face, vertex)
    )

    comparable_count, cover_count = count_relations(faces)
    face_count = len(faces)
    vertex_count = pow(BASE2, dimension)
    edge_count = dimension * pow(BASE2, dimension - 1)

    expected = {
        "vertices": vertex_count,
        "edges": edge_count,
        "nonempty_faces": pow(BASE3, dimension),
        "face_vertex_incidences": pow(len("0123"), dimension),
        "inclusion_pairs_including_equality": pow(len("01234"), dimension),
        "strict_inclusions": pow(len("01234"), dimension) - pow(BASE3, dimension),
        "hasse_covers": BASE2 * dimension * pow(BASE3, dimension - 1),
    }

    observed = {
        "vertices": vertex_count,
        "edges": edge_count,
        "nonempty_faces": face_count,
        "face_vertex_incidences": incidence_count,
        "inclusion_pairs_including_equality": comparable_count,
        "strict_inclusions": comparable_count - face_count,
        "hasse_covers": cover_count,
    }

    if observed != expected:
        raise AssertionError("One or more closed-form counts failed.")

    return observed


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify the Pascal-support / cube-face correspondence."
    )
    parser.add_argument(
        "--dimension-binary",
        default="111",
        help="Dimension as a binary word; default is 111.",
    )
    args = parser.parse_args()

    try:
        dimension = int(args.dimension_binary, BASE2)
        results = verify(dimension)
    except (ValueError, AssertionError) as exc:
        parser.error(str(exc))

    print(f"dimension: {dual(dimension)}")
    for name, value in results.items():
        print(f"{name}: {dual(value)}")
    print("status: exact finite checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
