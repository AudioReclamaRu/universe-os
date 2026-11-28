"""Exact rational null-space engine for Buckingham-Pi dimensional groups."""
from __future__ import annotations
import argparse, json, math
from dataclasses import dataclass
from fractions import Fraction
from functools import reduce
from pathlib import Path
from typing import Any, Mapping, Sequence

BASES = ("L", "M", "T", "I", "Theta", "N", "J")

def paired(n: int) -> str:
    if isinstance(n, bool) or not isinstance(n, int): raise TypeError("integer key required")
    if n < 0: return "-" + paired(-n)
    def digits(v: int, base: int) -> str:
        if v == 0: return "0"
        alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"; out = ""
        while v:
            v, r = divmod(v, base); out = alphabet[r] + out
        return out
    return f"<{digits(n, 2)}_2|{digits(n, 3)}_3>"

@dataclass(frozen=True)
class Dimension:
    exponents: tuple[Fraction, ...]
    def __post_init__(self):
        if len(self.exponents) != len(BASES): raise ValueError("exactly seven SI base exponents are required")
        object.__setattr__(self, "exponents", tuple(Fraction(str(x)) if isinstance(x, float) else Fraction(x) for x in self.exponents))
    @classmethod
    def from_mapping(cls, values: Mapping[str, Any]):
        unknown = set(values) - set(BASES)
        if unknown: raise ValueError(f"unknown SI base dimensions: {sorted(unknown)}")
        return cls(tuple(Fraction(str(values.get(k, 0))) for k in BASES))
    def as_dict(self):
        return {k:str(v) for k,v in zip(BASES,self.exponents) if v}

@dataclass(frozen=True)
class Variable:
    name: str
    dimension: Dimension
    value: float | None = None
    unit: str | None = None
    source: str | None = None
    status: str = "unknown"
    def __post_init__(self):
        if not self.name.strip(): raise ValueError("variable name cannot be empty")
        if self.value is not None and (not math.isfinite(float(self.value)) or self.value <= 0):
            raise ValueError("numeric evaluation requires positive finite variable values")

@dataclass(frozen=True)
class PiGroup:
    exponents: tuple[Fraction, ...]
    basis_index: int
    def expression(self, variables: Sequence[Variable]) -> str:
        factors=[]
        for variable, exponent in zip(variables,self.exponents):
            if exponent: factors.append(variable.name if exponent == 1 else f"{variable.name}^{exponent}")
        return " * ".join(factors) if factors else "1"
    def numeric_value(self, variables: Sequence[Variable]):
        if any(v.value is None for v in variables): return None
        return math.prod(float(v.value) ** float(e) for v,e in zip(variables,self.exponents))

@dataclass(frozen=True)
class PiResult:
    rank: int
    nullity: int
    pivot_variables: tuple[str,...]
    free_variables: tuple[str,...]
    matrix: tuple[tuple[Fraction,...],...]
    canonical_basis: tuple[PiGroup,...]
    alternative_bases: tuple[tuple[PiGroup,...],...]

def _primitive(vector: Sequence[Fraction]) -> tuple[Fraction,...]:
    lcm=math.lcm(*(v.denominator for v in vector)) if vector else 1
    ints=[int(v*lcm) for v in vector]
    nz=[abs(v) for v in ints if v]
    divisor=reduce(math.gcd,nz) if nz else 1
    ints=[v//divisor for v in ints]
    if next((v for v in ints if v),0) < 0: ints=[-v for v in ints]
    return tuple(Fraction(v) for v in ints)

def _rref(matrix: list[list[Fraction]]):
    if not matrix: return matrix,[]
    rows,cols=len(matrix),len(matrix[0]); a=[row[:] for row in matrix]
    pivots=[]; pivot_row=0
    for col in range(cols):
        pivot=next((r for r in range(pivot_row,rows) if a[r][col] != 0),None)
        if pivot is None: continue
        a[pivot_row],a[pivot]=a[pivot],a[pivot_row]
        scale=a[pivot_row][col]; a[pivot_row]=[v/scale for v in a[pivot_row]]
        for r in range(rows):
            if r != pivot_row and a[r][col] != 0:
                factor=a[r][col]
                a[r]=[x-factor*y for x,y in zip(a[r],a[pivot_row])]
        pivots.append(col); pivot_row += 1
        if pivot_row == rows: break
    return a,pivots

def _nullspace_basis(matrix: list[list[Fraction]]):
    rref,pivots=_rref(matrix); n=len(matrix[0]) if matrix else 0
    free=[j for j in range(n) if j not in pivots]; basis=[]
    for free_col in free:
        vector=[Fraction(0)]*n; vector[free_col]=Fraction(1)
        for row,pivot_col in enumerate(pivots): vector[pivot_col]=-rref[row][free_col]
        basis.append(_primitive(vector))
    return tuple(basis),tuple(pivots),rref

def _verify_nullspace(matrix, vectors):
    for vector in vectors:
        if any(sum(a*b for a,b in zip(row,vector)) != 0 for row in matrix):
            raise ArithmeticError("null-space verification failed")

def analyze(variables: Sequence[Variable]) -> PiResult:
    names=[v.name for v in variables]
    if len(names) != len(set(names)): raise ValueError("variable names must be unique")
    matrix=[list(row) for row in zip(*(v.dimension.exponents for v in variables))] if variables else [[] for _ in BASES]
    basis,pivots,rref=_nullspace_basis(matrix); _verify_nullspace(matrix,basis)
    free=[i for i in range(len(variables)) if i not in pivots]
    canonical=tuple(PiGroup(vector,i+1) for i,vector in enumerate(basis))
    alternatives=[]
    # Elementary unimodular changes. Each item below is a complete alternative basis.
    for i in range(len(basis)):
        for j in range(len(basis)):
            if i == j: continue
            for sign in (1,-1):
                variant=list(basis)
                variant[i]=_primitive(tuple(basis[i][k]+sign*basis[j][k] for k in range(len(variables))))
                _verify_nullspace(matrix,variant)
                alternatives.append(tuple(PiGroup(vector,k+1) for k,vector in enumerate(variant)))
    return PiResult(len(pivots),len(variables)-len(pivots),tuple(names[i] for i in pivots),
                    tuple(names[i] for i in free),tuple(tuple(x for x in row) for row in matrix),
                    canonical,tuple(alternatives))

def _variable_from_json(item: Mapping[str,Any]) -> Variable:
    return Variable(str(item["name"]),Dimension.from_mapping(item.get("dimension",{})),
                    None if item.get("value") is None else float(item["value"]),
                    item.get("unit"),item.get("source"),item.get("status","unknown"))

def result_to_dict(result: PiResult, variables: Sequence[Variable]):
    def render(groups):
        return [{"basis_id":paired(g.basis_index),"expression":g.expression(variables),
                 "exponents":{v.name:str(e) for v,e in zip(variables,g.exponents) if e},
                 "numeric_value_secondary":g.numeric_value(variables),
                 "status":"dimensionless_group_candidate",
                 "interpretation_guard":"dimensionless_does_not_mean_universal_or_causal"} for g in groups]
    return {
        "schema":"universe.buckingham-pi.v1","rank":paired(result.rank),
        "nullity":paired(result.nullity),"variable_count":paired(len(variables)),
        "dimension_matrix":[[str(v) for v in row] for row in result.matrix],
        "pivot_variables":list(result.pivot_variables),"free_variables":list(result.free_variables),
        "canonical_basis":render(result.canonical_basis),
        "alternative_basis_examples":[{"basis_id":paired(i+1),"groups":render(b)} for i,b in enumerate(result.alternative_bases)],
        "basis_note":"A null-space basis is not unique. Every listed alternative is a complete basis spanning the same dimensionless exponent subspace.",
        "input_provenance":[{"name":v.name,"unit":v.unit,"source":v.source,"status":v.status} for v in variables]
    }

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input",type=Path); parser.add_argument("--output",type=Path,default=Path("pi_groups_report.json"))
    args=parser.parse_args(); payload=json.loads(args.input.read_text(encoding="utf-8"))
    variables=[_variable_from_json(item) for item in payload.get("variables",[])]
    result=result_to_dict(analyze(variables),variables)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Wrote {args.output}"); return 0

if __name__ == "__main__": raise SystemExit(main())
