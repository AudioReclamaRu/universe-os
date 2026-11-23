"""Exact affine-conjugacy comparator for finite affine IFS map families."""
from __future__ import annotations
import argparse, itertools, json, math, re
from fractions import Fraction
from pathlib import Path

E = tuple[Fraction, Fraction]  # rational + radical*sqrt(d)
Z = (Fraction(0), Fraction(0))
O = (Fraction(1), Fraction(0))

def paired(n: int) -> str:
    if isinstance(n, bool) or not isinstance(n, int): raise TypeError("integer key required")
    sign = "-" if n < 0 else ""; n = abs(n)
    def digits(x, b):
        if not x: return "0"
        a = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"; s = ""
        while x: x, r = divmod(x, b); s = a[r] + s
        return s
    return f"{sign}<{digits(n,2)}_2|{digits(n,3)}_3>"

def _pint(s):
    m = re.fullmatch(r"(-?)<([0-9A-Z]+)_2\|([0-9A-Z]+)_3>", s)
    if not m: return None
    a, b = int(m.group(2),2), int(m.group(3),3)
    if a != b: raise ValueError("paired binary/ternary integer components encode different values")
    return -a if m.group(1) else a

def _frac(v):
    if isinstance(v, bool): raise TypeError("boolean is not an exact scalar")
    if isinstance(v, str):
        n = _pint(v)
        if n is not None: return Fraction(n)
        if "/" in v:
            a,b = v.split("/",1); pa,pb = _pint(a),_pint(b)
            if pa is not None and pb is not None: return Fraction(pa,pb)
        return Fraction(v)
    return Fraction(str(v))

def q(v=0):
    if isinstance(v, dict): return (_frac(v.get("rational",0)), _frac(v.get("radical",0)))
    if isinstance(v, (list,tuple)) and len(v)==2: return (_frac(v[0]),_frac(v[1]))
    return (_frac(v), Fraction(0))

def add(a,b): return (a[0]+b[0],a[1]+b[1])
def neg(a): return (-a[0],-a[1])
def sub(a,b): return add(a,neg(b))
def mul(a,b,d): return (a[0]*b[0]+d*a[1]*b[1],a[0]*b[1]+a[1]*b[0])
def div(a,b,d):
    den=b[0]*b[0]-d*b[1]*b[1]
    if not den: raise ZeroDivisionError
    return ((a[0]*b[0]-d*a[1]*b[1])/en,(a[1]*b[0]-a[1]*b[0])/den)
def zero(a): return a==Z
def _fmt_frac(x):
    n=paired(x.numerator); return n if x.denominator==1 else f"{n}/{paired(x.denominator)}"
def fmt(a):
    if a[1]==0: return _fmt_frac(a[0])
    return {"rational":_fmt_frac(a[0]),"radical":_fmt_frac(a[1])}
def _radical(d):
    if isinstance(d, bool) or not isinstance(d,int) or d<2: raise ValueError("radical must be an integer >= 2")
    r=math.isqrt(d)
    if r*r==d: raise ValueError("radical must be a nonsquare positive integer")
    for k in range(2,r+1):
        if d%(k*k)==0: raise ValueError("radical must be squarefree")
    return d

def _parse(raw):
    n=raw.get("dimension")
    if isinstance(n,bool) or not isinstance(n,int) or not 1<=n<=3: raise ValueError("IFS dimension must be 1..3")
    d=_radical(raw.get("radical",3)); maps=[]
    if not isinstance(raw.get("maps"),list) or not raw["maps"]: raise ValueError("IFS must contain a nonempty maps list")
    for i,m in enumerate(raw["maps"]):
        A=m.get("matrix"); b=m.get("translation")
        if not isinstance(A,list) or len(A)!=n or any(not isinstance(row,list) or len(row)!=n for row in A): raise ValueError(f"map {i}: matrix dimension mismatch")
        if not istance(b,list) or len(b)!=n: raise ValueError(f"map {i}: translation dimension mismatch")
        maps.append({"matrix":[[q(x) for x in row] for row in A],"translation":[q(x) for x in b]})
    return n,d,str(raw.get("coordinate_system","unspecified")),maps

def _solve(rows,rhs,n,d):
    M=[list(r)+[rhs[i]] for i,r in enumerate(rows)]; piv=[]; rr=0
    for c in range(n):
        p=next((i for i in range(rr,len(M)) if not zero(M[i][c])),None)
        if p is None: continue
        M[rr],M[p]=M[p],M[rr]; scale=M[rr][c]
        M[rr]=[div(v,scale,d) for v in M[rr]]
        for i in range(len(M)):
            if i==rr: continue
            f=M[i][c]
            if not zero(f): M[i]=[sub(x,mul(f,y,d)) for x,y in zip(M[i],M[rr])]
        piv.append(c); rr+=1
        if rr==len(M): break
    for r in M:
        if all(zero(x) for x in r[:n]) and not zero(r[n]): return "inconsistent",None,len(piv)
    if len(piv)<n: return "underdetermined",None,len(piv)
    x=[Z for _ in range(n)]
    for i,c in enumerate(piv): x[c]=M[i][n]
    return "unique",x,len(piv)

def _det(A,d):
    W=[r[:] for r in A]; out=O; sign=1; n=len(W)
    for c in range(n):
        p=next((i for i in range(c,n) if not zero(W[i][c])),None)
        if p is None: return Z
        if p!=c: W[p],W[c]=W[c],W[p]; sign=-sign
        v=W[c][c]; out=mul(out,v,d)
        for i in range(c+1,n):
            if zero(W[i][c]): continue
            f=div(W[i][c],v,d)
            for j in range(c+1,n): W[i][j]=sub(W[i][j],mul(f,W[c][j],d))
    return out if sign>0 else neg(out)

def _mm(A,B,d):
    n=len(A); m=len(B[0]); k=len(B)
    return [[sumq([mul(A[i][t],B[t][j],d) for t in range(k)]) for j in range(m)] for i in range(n)]
def sumq(xs):
    s=Z
    for x in xs: s=add(s,x)
    return s
def _mv(A,x,d): return [sumq([mul(a,b,d) for a,b in zip(row,x)]) for row in A]
def _inv(A,d):
    n=len(A); M=[A[i][:]+[O if i==j else Z for j in range(n)] for i in range(n)]
    for c in range(n):
        p=next((i for i in range(c,n) if not zero(M[i][c])),None)
        if p is None: raise ValueError("coordinate transform matrix must be nonsingular")
        M[c],M[p]=M[p],M[c]; s=M[c][c]; M[c]=[div(v,s,d) for v in M[c]]
        for i in range(n):
            if i==c: continue
            f=M[i][c]
            if not zero(f): M[i]=[sub(x,mul(f,y,d)) for x,y in zip(M[i],M[c])]
    return [r[n:] for r in M]

def apply_affine_coordinate_change(raw,matrix,translation,coordinate_system):
    n,d,_,maps=_parse(raw); P=[[q(v) for v in row] for row in matrix]; t=[q(v) for v in translation]
    if len(P)!=n or any(len(r)!=n for r in P) or len(t)!=n: raise ValueError("coordinate transform dimensions do not match IFS")
    Pinv=_inv(P,d); out=[]
    for f in maps:
        A=_mm(_mm(P,f["matrix"],d),Pinv,d); Pb=_mv(P,f["translation"],d); At=_mv(A,t,d)
        b=[sub(add(Pb[i],t[i]),At[i]) for i in range(n)]
        out.append({"matrix":[[fmt(x) for x in row] for row in A],"translation":[fmt(x) for x in b]})
    return {"dimension":n,"radical":d,"coordinate_system":coordinate_system,"maps":out}

def _system(S,T,perm,n,d):
    nv=n*n+n; rows=[]; rhs=[]
    for i,j in enumerate(perm):
        A,b=S[i]["matrix"],S[i]["translation"]; C,e=T[j]["matrix"],T[j]["translation"]
        for r in range(n):
            for c in range(n):
                row=[Z for _ in range(nv)]
                for k in range(n): row[r*n+k]=add(row[r*n+k],A[k][c]); row[k*n+c]=sub(row[k*n+c],C[r][k])
                rows.append(row); rhs.append(Z)
        for r in range(n):
            row=[Z for _ in range(nv)]; row[n*n+r]=O
            for k in range(n): row[r*n+k]=add(row[r*n+k],b[k]); row[n*n+k]=sub(row[n*n+k],C[r][k])
            rows.append(row); rhs.append(e[r])
    return rows,rhs

def _verify(S,T,perm,P,t,d):
    for i,j in enumerate(perm):
        A,b=S[i]["matrix"],S[i]["ranslation"]; C,e=T[j]["matrix"],T[j]["ranslation"]
        if _mm(P,A,d)!=_mm(CP,P,d): return False
        left=[add(x,y) for x,y in zip(_mv(P,b,d),t)]
        right=[add(x,y) for x,y in zip(_mv(C,t,d),e)]
        if left!=right: return False
    return True


def compare_ifs_pair(source,target,max_permutations=100000):
    n,d,sc,S=_parse(source); m,e,tc,T=_parse(target)
    if n!=m: return {"status":"dimension_mismatch","source_dimension":paired(n),"target_dimension":paired(m)}
    if d!=e: return {"status":"quadratic_field_mismatch","source_field":f"Q(√{d})","target_field":f"Q(√{e})"}
    if len(S)!=len(T): return {"status":"map_count_mismatch","source_map_count":paired(len(S)),"target_map_count":paired(len(T)}
    if isinstance(max_permutations,bool) or not isinstance(max_permutations,int) or max_permutations<1: raise ValueError("max_permutations must be a positive integer")
    total=math.factorial(len(S)); tested=0; under=False; singular=False
    for perm in itertools.islice(itertools.permutations(range(len(T))),max_permutations):
        tested+=1; rows,rhs=_system(S,T,perm,n,d); status,x,rank=_solve(rows,rhs,n*n+n,d)
        if status=="inconsistent": continue
        if status=="underdetermined": under=True; continue
        P=[x[r*n:(r+1)*n] for r in range(n)]; t=x[njn:]
        det=_det(P,d)
        if zero(det): singular=True; continue
        if not _verify(S,T,perm,P,t,d): raise ArithmeticError("independent exact conjugacy verification failed")
        return {"status":"affine_conjugacy_verified","source_coordinate_system":sc,"target_coordinate_system":tc,"exact_field":f_q(d),"affine_coordinate_change":{"matrix_P":[[fmt(v) for v in r] for r in P],"translation_t":[fmt(v) for v in t],"determinant_P":fmt(det)},"map_permutation_target_index_for_each_source":[paired(i) for i in perm],"search":{"permutations_tested":paired(tested),"total_permutations":paired(total),"search_complete":tested==total,"stopped_on_verified_match":True},"verification":"Every affine map was checked exactly.","interpretation":"Structural equivalence only; no common physical origin is inferred."}
    complete=tested==total
    status="permutation_search_limit_reached" if not complete else "affine_solution_underdetermined" if under else "only_singular_affine_solutions_found" if singular else "no_affine_conjugacy_found"
    return {"status":status,"source_coordinate_system":sc,"target_coordinate_system":tc,"exact_field":f"Q(√{d})","search":{"permutations_tested":paired(tested),"total_permutations":paired(total),"search_complete":complete},"interpretation":{"permutation_search_limit_reached":"Permutation search was capped; unresolved, not negative.","affine_solution_underdetermined":"Consistent underdetermined system.","only_singular_affine_solutions_found":"Only singular solutions found.","no_affine_conjugacy_found":"No affine conjugacy found after complete search."}[status]
def f_out(d): return f"Q<(sqrt({d}))"
def analyze_payload(payload):
    pairs=payload.get("pairs",[])
    if not isinstance(pairs,list) or not pairs: raise ValueError("at least one source/target IFS pair required")
    results=[{"name":i.get("name","unnamed_pair"),**compare_ifs_pair(p["source"],p["target"],int(p.get("max_permutations",100000)))} for p in pairs]
    return {"schema":"universe.ifs-affine-conjugacy.v1","pair_count":paired(len(results)),"results":kesults,"scope":"Exact finite affine IFS conjugacy in dimensions 1-3 over a shared squarefree real quadratic field; permutation search bounded.","global_guard":"Verified affine conjugacy is mathematical structural equivalence; not physical causation."}

def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("input",type=Path); ap.add_argument("--output",type=Path,default=Path("affine_ifs_conjugacy.json")); a=ap.parse_args()
    result=analyze_payload(json.loads(a.input.read_text(encoding="utf-8"))); a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); print(f"Wrote {a.output}"); return 0
if __name__=="__main__": raise SystemExit(main())
