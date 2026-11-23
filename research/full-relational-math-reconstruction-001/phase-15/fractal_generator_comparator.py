"""Exact affine-IFS and quadratic complex-polynomial structural comparisons."""
from __future__ import annotations
import argparse
import json
import math
from fractions import Fraction
from pathlib import Path
from typing import Any, Mapping

def paired(n: int) -> str:
    if isinstance(n, bool) or not isinstance(n, int): raise TypeError("integer key required")
    if n < 0: return "-" + paired(-n)
    def digits(v: int, base: int) -> str:
        if v == 0: return "0"
        alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"; out = ""
        while v:
            v, r = divmod(v, base); out = alphabet[r] + out
        return out
    return f"<{digits(n,2)}_2|{digits(n,3)}_3>"

def fmt_fraction(v: Fraction) -> str:
    n=paired(v.numerator)
    return n if v.denominator==1 else f"{n}/{paired(v.denominator)}"

def q(a=0,b=0): return (Fraction(a),Fraction(b))
def qparse(v):
    if isinstance(v,dict): return (Fraction(str(v.get("rational",0))),Fraction(str(v.get("radical",0))))
    if isinstance(v,(tuple,list)) and len(v)==2: return (Fraction(v[0]),Fraction(v[1]))
    return (Fraction(str(v)),Fraction(0))
def qadd(x,y): return (x[0]+y[0],x[1]+y[1])
def qmul(x,y,d): return (x[0]*y[0]+d*x[1]*y[1],x[0]*y[1]+x[1]*y[0])
def qiszero(x): return x==(Fraction(0),Fraction(0))
def qfloat(x,d): return float(x[0])+float(x[1])*math.sqrt(d)

def cparse(v):
    if isinstance(v,dict): return (Fraction(str(v.get("real",0))),Fraction(str(v.get("imag",0))))
    return (Fraction(str(v)),Fraction(0))
def cadd(x,y): return (x[0]+y[0],x[1]+y[1])
def csub(x,y): return (x[0]-y[0],x[1]-y[1])
def cmul(x,y): return (x[0]*y[0]-x[1]*y[1],x[0]*y[1]+x[1]*y[0])
def cscale(x,a): return (x[0]*a,x[1]*a)
def cformat(x):
    a,b=x; aa=fmt_fraction(a); bb=fmt_fraction(abs(b))
    if b==0: return aa
    if a==0: return ("-" if b<0 else "") + ("i" if abs(b)==1 else f"{bb}*i")
    return f"{aa} {'-' if b<0 else '+'} {('i' if abs(b)==1 else f'{bb}*i')}"

def _map(dim, ratio, translation, matrix=None):
    ratio=Fraction(ratio)
    m=matrix if matrix is not None else [[q(ratio,0) if i==j else q(0,0) for j in range(dim)] for i in range(dim)]
    return {"matrix":m,"translation":[qparse(v) for v in translation]}

def reference_ifs(name: str):
    if name=="cantor_set":
        return {"dimension":1,"radical":3,"coordinate_system":"euclidean_1d",
                "maps":[_map(1,Fraction(1,3),[0]),_map(1,Fraction(1,3),[Fraction(2,3)])]}
    if name=="sierpinski_gasket":
        return {"dimension":2,"radical":3,"coordinate_system":"barycentric_triangle",
                "maps":[_map(2,Fraction(1,2),[0,0]),_map(2,Fraction(1,2),[Fraction(1,2),0]),_map(2,Fraction(1,2),[0,Fraction(1,2)])]}
    if name=="sierpinski_carpet":
        maps=[_map(2,Fraction(1,3),[Fraction(i,3),Fraction(j,3)])
              for i in range(3) for j in range(3) if (i,j)!=(1,1)]
        return {"dimension":2,"radical":3,"coordinate_system":"euclidean_xy","maps":maps}
    if name=="menger_sponge":
        maps=[_map(3,Fraction(1,3),[Fraction(i,3),Fraction(j,3),Fraction(k,3)])
              for i in range(3) for j in range(3) for k in range(3)
              if sum(v==1 for v in (i,j,k))<2]
        return {"dimension":3,"radical":3,"coordinate_system":"euclidean_xyz","maps":maps}
    if name=="koch_curve":
        r=Fraction(1,3); sixth=Fraction(1,6)
        rot_plus=[[q(sixth,0),q(0,-sixth)],[q(0,sixth),q(sixth,0)]]
        rot_minus=[[q(sixth,0),q(0,sixth)],[q(0,-sixth),q(sixth,0)]]
        return {"dimension":2,"radical":3,"coordinate_system":"euclidean_xy",
                "maps":[_map(2,r,[0,0]),
                        _map(2,r,[Fraction(1,3),0],matrix=rot_plus),
                        _map(2,r,[Fraction(1,2),{"rational":0,"radical":"1/6"}],matrix=rot_minus),
                        _map(2,r,[Fraction(2,3),0])]}
    raise ValueError(f"unknown IFS reference: {name}")

def _parse_ifs(raw: Mapping[str,Any]):
    dim=int(raw["dimension"]); radical=int(raw.get("radical",3))
    if dim<1 or dim>3: raise ValueError("IFS dimension must be one, two or three")
    maps=[]
    for item in raw["maps"]:
        matrix=[[qparse(v) for v in row] for row in item["matrix"]]
        translation=[qparse(v) for v in item["translation"]]
        if len(matrix)!=dim or any(len(row)!=dim for row in matrix) or len(translation)!=dim:
            raise ValueError("affine map matrix and translation dimensions do not match the IFS")
        maps.append({"matrix":matrix,"translation":translation})
    if not maps: raise ValueError("IFS must contain at least one affine map")
    return dim,radical,str(raw.get("coordinate_system","unspecified")),maps

def _map_key(item):
    vals=[]
    for row in item["matrix"]:
        for a,b in row: vals.extend((a,b))
    for a,b in item["translation"]: vals.extend((a,b))
    return tuple(vals)

def _sqrt_fraction(v: Fraction):
    if v<0: return None
    a=math.isqrt(v.numerator); b=math.isqrt(v.denominator)
    return Fraction(a,b) if a*a==v.numerator and b*b==v.denominator else None

def _similarity_ratio(matrix, radical):
    d=len(matrix); gram=[[q(0,0) for _ in range(d)] for _ in range(d)]
    for i in range(d):
        for j in range(d):
            for k in range(d): gram[i][j]=qadd(gram[i][j],qmul(matrix[k][i],matrix[k][j],radical))
    diagonal=gram[0][0]
    if diagonal[1]!=0 or diagonal[0]<0: return None
    if any(not qiszero(gram[i][j]) for i in range(d) for j in range(d) if i!=j): return None
    if any(gram[i][i]!=diagonal for i in range(d)): return None
    return _sqrt_fraction(diagonal[0])

def analyze_ifs(raw: Mapping[str,Any]):
    dim,radical,coords,maps=_parse_ifs(raw)
    contractive=True; ratios=[]
    for affine in maps:
        norm=max(sum(abs(qfloat(v,radical)) for v in row) for row in affine["matrix"])
        if norm>=1: contractive=False
        ratios.append(_similarity_ratio(affine["matrix"],radical))
    common=ratios[0] if ratios and ratios[0] is not None and all(r==ratios[0] for r in ratios) else None
    key=sorted(_map_key(m) for m in maps)
    refs=[]
    for refname in ("cantor_set","sierpinski_gasket","sierpinski_carpet","menger_sponge","koch_curve"):
        ref=reference_ifs(refname); rd,rr,rc,rm=_parse_ifs(ref)
        if (dim,radical,coords,len(maps))==(rd,rr,rc,len(rm)) and key==sorted(_map_key(m) for m in rm):
            refs.append(refname)
    dim_numeric=(math.log(len(maps))/math.log(1/float(common)) if common is not None and 0<float(common)<1 else None)
    return {"name":raw.get("name","unnamed_ifs"),"dimension":paired(dim),"radical_field":f"Q(√{radical})",
        "coordinate_system":coords,"map_count":paired(len(maps)),"contractive_infinity_norm_bound":contractive,
        "common_similarity_ratio":fmt_fraction(common) if common is not None else None,
        "similarity_dimension_expression":f"ln({paired(len(maps))}) / ln(1/{fmt_fraction(common)})"
            if common is not None and 0<float(common)<1 else None,
        "similarity_dimension_numeric_secondary":dim_numeric,"exact_order_independent_generator_signature":True,
        "exact_reference_matches":refs,
        "interpretation":"Similarity dimension equals Hausdorff dimension only under suitable separation conditions such as the open set condition. Exact map equality is checked in the declared coordinates; general affine conjugacy is not yet implemented."}

def analyze_quadratic_dynamics(raw: Mapping[str,Any]):
    coeffs=[cparse(v) for v in raw["coefficients"]]
    if len(coeffs)!=3 or coeffs[2]==(0,0):
        raise ValueError("quadratic polynomial requires exactly three low-to-high coefficients and nonzero z² term")
    mode=raw.get("parameter_mode","fixed")
    if mode not in ("fixed","variable"): raise ValueError("parameter_mode must be fixed or variable")
    a0,b,a=coeffs
    bhalf=cscale(b,Fraction(1,2)); b2quarter=cscale(cmul(b,b),Fraction(1,4))
    c0=cadd(csub(cmul(a,a0),b2quarter),bhalf)
    if mode=="fixed":
        cscale_parameter=(Fraction(0),Fraction(0)); canonical_c=c0
    else:
        param=cparse(raw.get("parameter_coefficient",1)); cscale_parameter=cmul(a,param); canonical_c=None
    is_mandelbrot=(mode=="variable" and a==(Fraction(1),Fraction(0)) and b==(Fraction(0),Fraction(0))
                   and a0==(Fraction(0),Fraction(0)) and cscale_parameter==(Fraction(1),Fraction(0)))
    matches=[]
    if is_mandelbrot: matches.append("mandelbrot_quadratic_parameter_family")
    if mode=="fixed":
        matches.append("quadratic_julia_fixed_parameter_family")
        if canonical_c==(Fraction(0),Fraction(0)): matches.append("julia_map_c0")
        if canonical_c==(Fraction(-1),Fraction(0)): matches.append("julia_map_c_minus1")
    return {"name":raw.get("name","unnamed_quadratic_dynamics"),"parameter_mode":mode,"degree":paired(2),
        "polynomial_coefficients_low_to_high":[{"real":fmt_fraction(x),"imag":fmt_fraction(y)} for x,y in coeffs],
        "affine_conjugacy_normal_form":"w -> w² + C",
        "normalized_C_constant":{"real":fmt_fraction(c0[0]),"imag":fmt_fraction(c0[1])},
        "normalized_C_parameter_coefficient":{"real":fmt_fraction(cscale_parameter[0]),"imag":fmt_fraction(cscale_parameter[1])},
        "normalized_parameter_expression":(f"C = {cformat(c0)} + ({cformat(cscale_parameter)})*c" if mode=="variable" else f"C = {cformat(canonical_c)}"),
        "fixed_normalized_C":None if canonical_c is None else {"real":fmt_fraction(canonical_c[0]),"imag":fmt_fraction(canonical_c[1])},
        "exact_structural_matches":matches,
        "interpretation":"Quadratic complex polynomials with nonzero leading coefficient are affinely conjugate to w -> w² + C. Parameter-space (Mandelbrot-family) mode is distinguished from a fixed-parameter Julia map. This descriptor compares the map family, not rendered fractal images or finite orbit samples."}

def analyze_payload(payload: Mapping[str,Any]):
    ifs_results=[analyze_ifs(item) for item in payload.get("ifs_candidates",[])]
    dynamics_results=[analyze_quadratic_dynamics(item) for item in payload.get("quadratic_dynamics",[])]
    if not ifs_results and not dynamics_results: raise ValueError("at least one IFS or quadratic dynamics candidate is required")
    return {"schema":"universe.fractal-generator-structural-comparison.v1",
        "ifs_candidate_count":paired(len(ifs_results)),"quadratic_dynamics_candidate_count":paired(len(dynamics_results)),
        "ifs_results":ifs_results,"quadratic_dynamics_results":dynamics_results,
        "atlas_scope":"Cantor, Sierpinski gasket/carpet, Menger sponge, Koch IFS descriptors and quadratic Mandelbrot/Julia map families only; other Atlas families remain open.",
        "global_guard":"Generator correspondence is structural evidence only. It does not prove a common physical origin or identify a process that generated a natural object."}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input",type=Path); parser.add_argument("--output",type=Path,default=Path("fractal_comparison.json"))
    args=parser.parse_args(); payload=json.loads(args.input.read_text(encoding="utf-8"))
    result=analyze_payload(payload); args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Wrote {args.output}"); return 0

if __name__=="__main__": raise SystemExit(main())
