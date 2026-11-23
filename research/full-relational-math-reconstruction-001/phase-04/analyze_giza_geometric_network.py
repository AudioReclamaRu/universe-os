"""GIZA TRIAD — five-node geometry audit.

The script keeps three evidence layers separate:
- GPMP local survey-grid pyramid centres (Khufu, Khafre, Menkaure);
- map-derived Great Sphinx head distances/point;
- a mapped point for the Khentkaus I tomb complex (not a second Sphinx).

All displayed integer quantities are emitted as paired base-2/base-3 numerals.
Floating-point calculations are internal only. No physical coupling law is
inferred from the geometry.
"""
from __future__ import annotations

from math import acos, asin, atan2, cos, gcd, hypot, pi, radians, sin, sqrt

DIGITS = "012"


def base_repr(value: int, base: int) -> str:
    if value < 0:
        return "-" + base_repr(-value, base)
    if value == 0:
        return "0"
    out = ""
    while value:
        value, remainder = divmod(value, base)
        out = DIGITS[remainder] + out
    return out


def dual(value: int) -> str:
    return f"<{base_repr(value, 2)}_2 | {base_repr(value, 3)}_3>"


def dual_fraction(numerator: int, denominator: int = 1) -> str:
    if denominator == 0:
        raise ZeroDivisionError("denominator cannot be zero")
    if denominator < 0:
        numerator, denominator = -numerator, -denominator
    common = gcd(abs(numerator), denominator)
    numerator //= common
    denominator //= common
    return f"{dual(numerator)} / {dual(denominator)}"


def rounded_tenth(value: float) -> str:
    return dual_fraction(round(value * 10), 10)


def rounded_arcseconds(value_degrees: float) -> str:
    return dual_fraction(round(value_degrees * 3600), 3600)


def haversine_m(a: tuple[int, int], b: tuple[int, int]) -> float:
    """Coordinates are latitude/longitude in units of 1e-7 degree."""
    lat1, lon1 = radians(a[0] / 10_000_000), radians(a[1] / 10_000_000)
    lat2, lon2 = radians(b[0] / 10_000_000), radians(b[1] / 10_000_000)
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * 6_371_008.8 * asin(sqrt(h))


def local_en_m(point: tuple[int, int], origin: tuple[int, int]) -> tuple[float, float]:
    lat0 = radians(origin[0] / 10_000_000)
    dlat = (point[0] - origin[0]) / 10_000_000
    dlon = (point[1] - origin[1]) / 10_000_000
    north = dlat * 111_132.92
    east = dlon * (111_412.84 * cos(lat0) - 93.5 * cos(3 * lat0))
    return east, north


def angle_at(a: tuple[float, float], vertex: tuple[float, float], c: tuple[float, float]) -> float:
    u = (a[0] - vertex[0], a[1] - vertex[1])
    v = (c[0] - vertex[0], c[1] - vertex[1])
    dot = u[0] * v[0] + u[1] * v[1]
    return acos(max(-1.0, min(1.0, dot / (hypot(*u) * hypot(*v)))))


# GPMP centres in decimetres; each tuple is (northing, easting).
GPMP_DM = {
    "Khufu": (1_000_000, 5_000_000),
    "Khafre": (996_456, 4_996_660),
    "Menkaure": (992_599, 4_994_265),
}

# Map-derived geodetic reference points, coordinates in 1e-7 degree units.
GEO = {
    "Khufu": (299_791_813, 311_341_960),
    "Khafre": (299_759_865, 311_307_354),
    "Menkaure": (299_725_014, 311_282_569),
    "Great_Sphinx_head": (299_752_751, 311_377_139),
    "Khentkaus_I_site": (299_734_700, 311_354_900),
}

# Published map-derived centre-to-Sphinx-head distances in centimetres.
SPHINX_CM = {
    "Khufu": 55_025,
    "Khafre": 67_810,
    "Menkaure": 96_310,
}

# Nell & Ruggles, Table 5b: difference between two half-wall best-fit azimuths.
MENKAURE_HALF_BEND_ARCMIN = {
    "north course 7 casing": 50,
    "north course 9 casing": 61,
    "east course 6 casing": 21,
    "south course 7 internal": 36,
    "west course 9 internal": 37,
    "west course 11 internal": 0,
}

# Mean deviation from cardinality (arcminutes): Khufu Table 8,
# Khafre Table 3b casing foundation, Menkaure Table 5c.
SIDE_DFC_ARCMIN = {
    "Khufu": {"N": (-30, 10), "E": (-40, 10), "S": (-17, 10), "W": (-40, 10)},
    "Khafre": {"N": (-38, 10), "E": (-40, 10), "S": (-58, 10), "W": (-42, 10)},
    "Menkaure": {"N": (20, 1), "E": (12, 1), "S": (32, 1), "W": (25, 1)},
}


def main() -> None:
    pyramid_names = ("Khufu", "Khafre", "Menkaure")
    xy = {
        name: (GPMP_DM[name][1] / 10, GPMP_DM[name][0] / 10)
        for name in pyramid_names
    }

    print("GIZA TRIAD — GPMP SURVEY-GRID GEOMETRY")
    for i, left in enumerate(pyramid_names):
        for right in pyramid_names[i + 1:]:
            distance = hypot(
                xy[right][0] - xy[left][0],
                xy[right][1] - xy[left][1],
            )
            print(f"{left}--{right}: {rounded_tenth(distance)} m")

    print("TRIAD INTERIOR ANGLES")
    for vertex, first, second in (
        ("Khufu", "Khafre", "Menkaure"),
        ("Khafre", "Khufu", "Menkaure"),
        ("Menkaure", "Khufu", "Khafre"),
    ):
        value_degrees = angle_at(
            xy[first], xy[vertex], xy[second]
        ) * 180 / pi
        print(f"at {vertex}: {rounded_arcseconds(value_degrees)} degrees")

    khufu, khafre, menkaure = xy["Khufu"], xy["Khafre"], xy["Menkaure"]
    vx = menkaure[0] - khufu[0]
    vy = menkaure[1] - khufu[1]
    baseline = hypot(vx, vy)
    ux, uy = vx / baseline, vy / baseline
    wx = khafre[0] - khufu[0]
    wy = khafre[1] - khufu[1]
    along = wx * ux + wy * uy
    cross = (vx * wy - vy * wx) / baseline
    adjacent_sum = hypot(wx, wy) + hypot(
        menkaure[0] - khafre[0], menkaure[1] - khafre[1]
    )
    print("KHAFRE RELATIVE TO KHUfu--MENKAURE AXIS")
    print(f"along-axis projection: {rounded_tenth(along)} m")
    print(f"signed perpendicular offset: {rounded_tenth(cross)} m")
    print(f"baseline minus adjacent-side sum: {rounded_tenth(baseline - adjacent_sum)} m")

    # Matrix intentionally labels the heterogeneous evidence tiers.
    nodes = (
        "Khufu", "Khafre", "Menkaure",
        "Great_Sphinx_head", "Khentkaus_I_site",
    )
    distances: dict[tuple[str, str], str] = {}
    print("FIVE-NODE PAIRWISE DISTANCES")
    for index, first in enumerate(nodes):
        for second in nodes[index + 1:]:
            if first in pyramid_names and second in pyramid_names:
                distance = hypot(
                    xy[second][0] - xy[first][0],
                    xy[second][1] - xy[first][1],
                )
                rendered = rounded_tenth(distance)
                tier = "GPMP centre coordinates"
            elif second == "Great_Sphinx_head" and first in SPHINX_CM:
                rendered = dual_fraction(SPHINX_CM[first], 100)
                tier = "map-derived Sphinx head reference"
            else:
                distance = haversine_m(GEO[first], GEO[second])
                rendered = rounded_tenth(distance)
                tier = "approximate mapped point geodesic"
            distances[(first, second)] = rendered
            print(f"{first}--{second}: {rendered} m [{tier}]")

    print("FIVE-NODE SYMMETRIC MATRIX")
    for first in nodes:
        row = []
        for second in nodes:
            if first == second:
                row.append(dual(0))
            else:
                key = (
                    (first, second)
                    if nodes.index(first) < nodes.index(second)
                    else (second, first)
                )
                row.append(distances[key])
        print(first + ": " + " ; ".join(row))

    # Project selected target points to the GPMP pyramid axis.
    origin = GEO["Khufu"]
    sphinx_en = local_en_m(GEO["Great_Sphinx_head"], origin)
    khentkaus_en = local_en_m(GEO["Khentkaus_I_site"], origin)
    perpendicular = (-uy, ux)

    def project(point: tuple[float, float]) -> tuple[float, float]:
        return (
            point[0] * ux + point[1] * uy,
            point[0] * perpendicular[0] + point[1] * perpendicular[1],
        )

    sphinx_along, sphinx_cross = project(sphinx_en)
    khentkaus_along, khentkaus_cross = project(khentkaus_en)
    target_along = khentkaus_along - sphinx_along
    target_cross = abs(sphinx_cross - khentkaus_cross)
    khafre_cross = abs(cross)
    mismatch = abs(target_cross - khafre_cross)

    print("TARGET PROJECTIONS ON THE KHUfu--MENKAURE AXIS")
    print(
        "Great Sphinx head along/cross: "
        f"{rounded_tenth(sphinx_along)} / {rounded_tenth(sphinx_cross)} m"
    )
    print(
        "Khentkaus mapped point along/cross: "
        f"{rounded_tenth(khentkaus_along)} / {rounded_tenth(khentkaus_cross)} m"
    )
    print(f"Target along-axis separation: {rounded_tenth(target_along)} m")
    print(f"Target cross-axis separation: {rounded_tenth(target_cross)} m")
    print(f"Difference from Khafre cross-axis offset: {rounded_tenth(mismatch)} m")
    print("WARNING: exploratory mixed-frame projection only; map-derived target points are not tied to the GPMP survey grid by a surveyed transformation.")

    print("CARDINAL-SIDE DFC VALUES — ARC MINUTES")
    for pyramid, sides in SIDE_DFC_ARCMIN.items():
        print(pyramid + ":")
        for side, (numerator, denominator) in sides.items():
            print(f"  {side}: {dual_fraction(numerator, denominator)} arcmin")

    print("MENKAURE HALF-WALL DIFFERENCES — ARC MINUTES")
    for description, value in MENKAURE_HALF_BEND_ARCMIN.items():
        print(f"{description}: {dual(value)} arcmin")

    print("status: geometric calculations complete; no physical coupling law inferred")


if __name__ == "__main__":
    main()
