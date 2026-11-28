"""Relation-first discovery kernel; standard library only. Matches are leads, not causal evidence."""
import argparse, itertools, json, math
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

BASES = ("L", "M", "T", "I", "Theta", "N", "J")


def paired(n: int) -> str:
    if isinstance(n, bool) or not isinstance(n, int):
        raise TypeError("integer key required")
    if n < 0: return "-" + paired(-n)
    def digits(v, b):
        if not v: return "0"
        out = ""
        while v: v, r = divmod(v, b); out = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"[r] + out
        return out
    return f"<{digits(n, 2)}_2|{digits(n, 3)}_3>"


@dataclass(frozen=True)
class Dim:
    p: tuple = (Fraction(0),) * 7
    def __post_init__(self):
        if len(self.p) != 7: raise ValueError("seven SI exponents required")
        object.__setattr__(self, "p", tuple(Fraction(str(x)) if isinstance(x, float) else Fraction(x) for x in self.p))
    @classmethod
    def of(cls, d=None):
        d = d or {}
        if set(d) - set(BASES): raise ValueError("unknown SI base dimension")
        return cls(tuple(Fraction(str(d.get(k, 0))) for k in BASES))
    def __truediv__(self, b): return Dim(tuple(x-y for x,y in zip(self.p,b.p)))
    def __mul__(self, b): return Dim(tuple(x+y for x,y in zip(self.p,b.p)))
    @property
    def dimensionless(self): return all(x == 0 for x in self.p)
    def dict(self): return {k:str(v) for k,v in zip(BASES,self.p) if v}


ZERO = Dim()

@dataclass(frozen=True)
class Q:
    name: str
    value: float
    dim: Dim
    uncertainty: float | None = None
    source: str | None = None
    status: str = "unknown"
    frame: str | None = None
    def __post_init__(self):
        if not self.name.strip() or not math.isfinite(float(self.value)): raise ValueError("invalid quantity")
        if self.uncertainty is not None and (not math.isfinite(self.uncertainty) or self.uncertainty < 0): raise ValueError("invalid uncertainty")


@dataclass(frozen=True)
class Ref:
    key: str; symbol: str; expression: str; value: float; family: str


REFS = (
    Ref("constant.phi", "φ", "(1 + √5) / 2", (1+math.sqrt(5))/2, "metallic mean"),
    Ref("constant.pi", "π", "circle circumference / diameter", math.pi, "geometry/periodicity"),
    Ref("constant.e", "e", "natural exponential base", math.e, "exponential growth"),
    Ref("constant.sqrt2", "√2", "positive root of x² − 2", math.sqrt(2), "algebraic root"),
    Ref("constant.sqrt3", "√3", "positive root of x² − 3", math.sqrt(3), "algebraic root"),
    Ref("constant.silver", "δ₂", "1 + √2", 1+math.sqrt(2), "metallic mean"),
    Ref("constant.plastic", "ρ", "real root of x³ − x − 1", 1.324717957244746, "recurrence growth"),
    Ref("constant.feigenbaum_delta", "δ_F", "period-doubling renormalization limit", 4.669201609102990, "critical dynamics"),
    Ref("dimension.sierpinski", "d_S", "ln(3) / ln(2)", math.log(3)/math.log(2), "fractal dimension"),
    Ref("dimension.cantor", "d_C", "ln(2) / ln(3)", math.log(2)/math.log(3), "fractal dimension"),
    Ref("dimension.gasket_spectral", "d_s", "2 ln(3) / ln(5)", 2*math.log(3)/math.log(5), "spectral fractal dimension"),
    Ref("integer.one", "1", "unity", 1.0, "identity"),
    Ref("integer.two", "2", "paired integer <10₂|2₃>", 2.0, "integer key"),
    Ref("integer.three", "3", "paired integer <11₂|10₃>", 3.0, "integer key"),
)


@dataclass(frozen=True)
class Candidate:
    formula: str; operation: str; value: float; dim: Dim; inputs: tuple; uncertainty: float | None; matches: tuple


class Finder:
    def __init__(self, refs=REFS, tolerance=1e-4):
        if tolerance <= 0 or not math.isfinite(tolerance): raise ValueError("positive finite tolerance required")
        self.refs, self.tolerance = tuple(refs), tolerance
    def match(self, value):
        out=[]
        for r in self.refs:
            err=abs(value-r.value)/abs(r.value) if r.value else abs(value)
            if err <= self.tolerance: out.append({"key":r.key,"symbol":r.symbol,"expression":r.expression,"family":r.family,"relative_error":err})
        return tuple(sorted(out,key=lambda x:x["relative_error"]))
    def discover(self, qs, cross_ratios=False):
        if len({q.name for q in qs}) != len(qs): raise ValueError("quantity names must be unique")
        out=[]
        for a,b in itertools.permutations(qs,2):
            if a.dim != b.dim or b.value == 0: continue
            v=a.value/b.value
            u=None if a.uncertainty is None or b.uncertainty is None or a.value == 0 else abs(v)*math.hypot(a.uncertainty/a.value,b.uncertainty/b.value)
            out.append(Candidate(f"({a.name}) / ({b.name})","ratio",v,a.dim/b.dim,(a.name,b.name),u,self.match(v)))
        if cross_ratios:
            groups={}
            for q in qs:
                if q.frame: groups.setdefault((q.dim,q.frame),[]).append(q)
            for group in groups.values():
                for a,b,c,d in itertools.permutations(group,4):
                    den=(a.value-d.value)*(b.value-c.value)
                    if den == 0: continue
                    v=((a.value-c.value)*(b.value-d.value))/den
                    out.append(Candidate(f"({a.name},{b.name};{c.name},{d.name})","cross_ratio",v,ZERO,(a.name,b.name,c.name,d.name),None,self.match(v)))
        return sorted(out,key=lambda c:(not bool(c.matches), c.matches[0]["relative_error"] if c.matches else math.inf,c.operation,c.formula))
    def power_law(self,x,y):
        if len(x)!=len(y) or len(x)<3 or any(v<=0 or not math.isfinite(v) for v in (*x,*y)): raise ValueError("positive x/y arrays of equal length (>=3) required")
        a,b=[math.log(v) for v in x],[math.log(v) for v in y]
        ma,mb=sum(a)/len(a),sum(b)/len(b); ssx=sum((v-ma)**2 for v in a)
        if ssx==0: raise ValueError("x values must vary")
        z=sum((u-ma)*(v-mb) for u,v in zip(a,b))/ssx; intercept=mb-z*ma
        residual=tuple(v-(intercept+z*u) for u,v in zip(a,b)); ssr=sum(v*v for v in residual); sst=sum((v-mb)**2 for v in b)
        r2=1.0 if sst==0 and ssr==0 else (0.0 if sst==0 else 1-ssr/sst)
        return {"exponent":z,"amplitude":math.exp(intercept),"r_squared":r2,"count":len(x),"residuals":residual,"atlas_matches":self.match(z),"interpretation":"empirical fit, not universal law"}


def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("input",type=Path); ap.add_argument("--output",type=Path,default=Path("relation_report.json")); a=ap.parse_args()
    data=json.loads(a.input.read_text(encoding="utf-8")); f=Finder(tolerance=float(data.get("relative_tolerance",1e-4)))
    qs=[]
    for item in data.get("quantities",[]):
        value=item["value"]; value=float(Fraction(value)) if isinstance(value,str) else float(value)
        qs.append(Q(item["name"],value,Dim.of(item.get("dimension")),item.get("uncertainty"),item.get("source"),item.get("status","unknown"),item.get("coordinate_frame")))
    candidates=f.discover(qs,bool(data.get("include_cross_ratios",False)))
    result={"schema":"universe.relation-discovery.v1","numeral_convention":"paired binary/ternary integer keys","quantity_count":paired(len(qs)),"candidate_count":paired(len(candidates)),"candidates":[]}
    for i,c in enumerate(candidates,1):
        result["candidates"].append({"id":paired(i),"formula":c.formula,"operation":c.operation,"value_numeric_secondary":c.value,"dimension":c.dim.dict(),"inputs":c.inputs,"uncertainty":c.uncertainty,"matches":c.matches,"status":"derived_candidate","guard":"correspondence_is_not_causation"})
    p=data.get("power_law")
    result["power_law_fit"]=f.power_law(p["x"],p["y"]) if p else None
    if result["power_law_fit"]:
        result["power_law_fit"]["count"]=paired(result["power_law_fit"]["count"])
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Wrote {a.output}")
    return 0

if __name__ == "__main__": raise SystemExit(main())
