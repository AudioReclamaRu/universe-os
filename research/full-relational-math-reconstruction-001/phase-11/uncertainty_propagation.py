"""Propagate log-relative measurement covariance through Pi bases and monomial relations."""
from __future__ import annotations
import argparse, json, math
from fractions import Fraction
from pathlib import Path
from typing import Any, Mapping, Sequence

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

def as_fraction(value: Any) -> Fraction:
    return value if isinstance(value, Fraction) else Fraction(str(value))

def _is_psd(matrix: Sequence[Sequence[float]], tolerance: float = 1e-12) -> bool:
    n=len(matrix); scale=max(1.0,max((abs(x) for row in matrix for x in row),default=0.0)); tol=tolerance*scale
    lower=[[0.0]*n for _ in range(n)]; diagonal=[0.0]*n
    for i in range(n):
        lower[i][i]=1.0
        pivot=matrix[i][i]-sum(lower[i][k]**2*diagonal[k] for k in range(i))
        if pivot < -tol: return False
        if pivot <= tol:
            diagonal[i]=0.0
            for j in range(i+1,n):
                residual=matrix[j][i]-sum(lower[j][k]*lower[i][k]*diagonal[k] for k in range(i))
                if abs(residual)>tol: return False
                lower[j][i]=0.0
        else:
            diagonal[i]=pivot
            for j in range(i+1,n):
                residual=matrix[j][i]-sum(lower[j][k]*lower[i][k]*diagonal[k] for k in range(i))
                lower[j][i]=residual/pivot
    return True

def validate_log_covariance(variable_order: Sequence[str], covariance: Sequence[Sequence[Any]],
                            required_order: Sequence[str]) -> tuple[tuple[float,...],...]:
    n=len(variable_order)
    if n!=len(set(variable_order)) or set(variable_order)!=set(required_order) or len(required_order)!=n:
        raise ValueError("covariance variable_order must contain each Phase 09 input variable exactly once")
    if len(covariance)!=n or any(len(row)!=n for row in covariance):
        raise ValueError("log_relative_covariance must be a square matrix matching variable_order")
    matrix=[[float(v) for v in row] for row in covariance]
    if any(not math.isfinite(v) for row in matrix for v in row): raise ValueError("covariance entries must be finite")
    scale=max(1.0,max(abs(v) for row in matrix for v in row))
    for i in range(n):
        for j in range(n):
            if abs(matrix[i][j]-matrix[j][i])>1e-12*scale: raise ValueError("log_relative_covariance must be symmetric")
    if any(matrix[i][i]<-1e-12*scale for i in range(n)): raise ValueError("covariance diagonal cannot be negative")
    if not _is_psd(matrix): raise ValueError("log_relative_covariance must be positive semidefinite")
    indices=[variable_order.index(name) for name in required_order]
    return tuple(tuple(matrix[i][j] for j in indices) for i in indices)

def phase09_bases(report: Mapping[str,Any]):
    variables=[str(item["name"]) for item in report.get("input_provenance",[])]
    if not variables or len(variables)!=len(set(variables)):
        raise ValueError("Phase 09 report must contain unique input_provenance variable names")
    bases={}
    canonical=report.get("canonical_basis",[])
    if canonical: bases[("canonical","canonical")]=canonical
    for alternative in report.get("alternative_basis_examples",[]):
        basis_id=str(alternative.get("basis_id","alternative")); key=("alternative",basis_id)
        if key in bases: raise ValueError(f"duplicate Phase 09 alternative basis id: {basis_id}")
        bases[key]=alternative.get("groups",[])
    return variables,bases

def original_exponents_for_candidate(basis_id: str, phase09_groups: Sequence[Mapping[str,Any]],
                                     candidate_vector: Mapping[str,Any], variable_order: Sequence[str]):
    group_by_name={}
    for group in phase09_groups:
        if "basis_id" not in group or "exponents" not in group:
            raise ValueError("Phase 09 Pi group is missing basis_id or original-variable exponents")
        group_by_name[f"G{group['basis_id']}"]=group["exponents"]
    total={name:Fraction(0) for name in variable_order}
    for group_name,power_raw in candidate_vector.items():
        if group_name not in group_by_name:
            raise ValueError(f"candidate references unknown Pi group {group_name} in basis {basis_id}")
        power=as_fraction(power_raw); source_vector=group_by_name[group_name]
        unknown=set(source_vector)-set(variable_order)
        if unknown: raise ValueError(f"Pi group contains unknown original variables: {sorted(unknown)}")
        for name in variable_order: total[name]+=power*as_fraction(source_vector.get(name,0))
    return tuple(total[name] for name in variable_order)

def uncertainty_from_exponents(exponents: Sequence[Fraction], covariance: Sequence[Sequence[float]]):
    vector=[float(v) for v in exponents]
    variance=sum(vector[i]*covariance[i][j]*vector[j] for i in range(len(vector)) for j in range(len(vector)))
    if variance < -1e-12: raise ArithmeticError("negative propagated log-variance; covariance or exponent map is inconsistent")
    variance=max(0.0,variance); sigma_log=math.sqrt(variance)
    max_log=math.log(float.fromhex("0x1.fffffffffffffp+1023"))
    relative_sd=math.sqrt(math.expm1(variance)) if variance<max_log else None
    lower=math.exp(-sigma_log); upper=math.exp(sigma_log) if sigma_log<max_log else None
    return {"log_variance":variance,"log_standard_uncertainty":sigma_log,
            "relative_standard_deviation_if_lognormal":relative_sd,
            "multiplicative_log_sigma_interval":[lower,upper],
            "uncertainty_model":"Covariance propagation is exact for the linear combination of log absolute values; conversion to relative standard deviation assumes a lognormal model."}

def relation_signature(exponents: Sequence[Fraction], variable_order: Sequence[str]):
    terms=[]
    for name,exponent in zip(variable_order,exponents):
        if exponent: terms.append(name if exponent==1 else f"{name}^{exponent}")
    return " * ".join(terms) if terms else "1"

def propagate(phase09: Mapping[str,Any], phase10: Mapping[str,Any], covariance_payload: Mapping[str,Any]):
    variables,bases=phase09_bases(phase09)
    cov=validate_log_covariance(covariance_payload["variable_order"],
                                covariance_payload["log_relative_covariance"],variables)
    results=[]; family_map={}
    for basis_result in phase10.get("basis_results",[]):
        basis_type=str(basis_result["basis_type"]); basis_id=str(basis_result["basis_id"])
        key=(basis_type,"canonical" if basis_type=="canonical" else basis_id)
        if key not in bases: raise ValueError(f"Phase 10 basis {key} cannot be matched to Phase 09 report")
        groups=bases[key]; candidates_out=[]
        for candidate in basis_result.get("candidates",[]):
            original=original_exponents_for_candidate(basis_id,groups,candidate.get("exponent_vector",{}),variables)
            uncertainty=uncertainty_from_exponents(original,cov)
            candidates_out.append({
                "candidate_id":candidate.get("candidate_id"),
                "formula_in_pi_basis":candidate.get("formula"),
                "original_variable_exponents":{name:str(value) for name,value in zip(variables,original) if value},
                "basis_invariant_relation_signature":relation_signature(original,variables),
                "nominal_value_numeric_secondary":candidate.get("value_numeric_secondary"),
                "numeric_evaluation_status":candidate.get("numeric_evaluation_status"),
                "atlas_matches":candidate.get("matches",[]),**uncertainty})
            family_map.setdefault(original,[]).append({
                "basis_type":basis_type,"basis_id":basis_id,"candidate_id":candidate.get("candidate_id"),
                "formula_in_pi_basis":candidate.get("formula"),
                "atlas_match_symbols":[m.get("symbol") for m in candidate.get("matches",[])]})
        results.append({"basis_type":basis_type,"basis_id":basis_id,
            "basis_completeness":basis_result.get("basis_completeness"),
            "candidate_count":basis_result.get("candidate_count"),"candidates":candidates_out})
    families=[]
    for index,(exponents,representations) in enumerate(
        sorted(family_map.items(),key=lambda item:tuple(str(v) for v in item[0])),1):
        families.append({"relation_family_id":paired(index),
            "original_variable_exponents":{name:str(value) for name,value in zip(variables,exponents) if value},
            "basis_invariant_relation_signature":relation_signature(exponents,variables),
            "representation_count":paired(len(representations)),"representations":representations,
            **uncertainty_from_exponents(exponents,cov)})
    return {"schema":"universe.relation-uncertainty.v1","input_variable_count":paired(len(variables)),
        "basis_count":paired(len(results)),"relation_family_count":paired(len(families)),
        "variable_order":variables,"covariance_source":covariance_payload.get("source"),
        "covariance_status":covariance_payload.get("status","unknown"),
        "covariance_definition":"Cov(ln|q_i|, ln|q_j|); entries are dimensionless and include correlations.",
        "probability_coverage_note":"The multiplicative log-sigma interval is not a confidence interval by itself. It has the usual Gaussian coverage only if the log-relation residual is approximately normal; no distribution is inferred here.",
        "basis_invariance_rule":"Candidates expressed in different Pi bases are grouped only when their exact exponent vectors over the original Phase 09 variables agree.",
        "assumptions_and_limits":[
            "Input log covariance is supplied externally; it is not inferred by dimensional analysis.",
            "The log-covariance approximation requires nonzero original variable magnitudes and locally meaningful relative uncertainties.",
            "All correlations must be represented in the supplied covariance matrix; independence is not assumed.",
            "The same mapped exponent vector has the same propagated log-variance in every equivalent basis.",
            "A propagated uncertainty does not establish the physical validity or causality of a relation."],
        "basis_results":results,"basis_invariant_relation_families":families}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input",type=Path,help="JSON containing Phase 09 report, Phase 10 report and log covariance")
    parser.add_argument("--output",type=Path,default=Path("relation_uncertainty.json"))
    args=parser.parse_args(); payload=json.loads(args.input.read_text(encoding="utf-8"))
    result=propagate(payload["phase09_report"],payload["phase10_report"],payload["log_covariance"])
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Wrote {args.output}"); return 0

if __name__=="__main__": raise SystemExit(main())
