"""Exact finite graph and linear-recurrence structural comparators."""
from __future__ import annotations
import argparse
import json
from collections import Counter, deque
from fractions import Fraction
from pathlib import Path
from typing import Any, Mapping, Sequence


def paired(n: int) -> str:
    if isinstance(n, bool) or not isinstance(n, int):
        raise TypeError("integer key required")
    if n < 0:
        return "-" + paired(-n)
    def digits(v: int, base: int) -> str:
        if v == 0:
            return "0"
        alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        out = ""
        while v:
            v, r = divmod(v, base)
            out = alphabet[r] + out
        return out
    return f"<{digits(n, 2)}_2|{digits(n, 3)}_3>"


RECURRENCE_ATLAS = (
    {"name":"fibonacci_operator","coefficients":[1,1],"initial":[0,1]},
    {"name":"lucas_operator","coefficients":[1,1],"initial":[2,1]},
    {"name":"pell_operator","coefficients":[2,1],"initial":[0,1]},
    {"name":"jacobsthal_operator","coefficients":[1,2],"initial":[0,1]},
    {"name":"tribonacci_operator","coefficients":[1,1,1],"initial":[0,0,1]},
    {"name":"padovan_operator","coefficients":[0,1,1],"initial":[1,1,1]},
)


def _fraction(v: Any) -> Fraction:
    return v if isinstance(v, Fraction) else Fraction(str(v))


def _format_fraction(value: Fraction) -> str:
    numerator = paired(value.numerator)
    return numerator if value.denominator == 1 else f"{numerator}/{paired(value.denominator)}"


def _solve_unique(rows: Sequence[Sequence[Fraction]], rhs: Sequence[Fraction], columns: int):
    if len(rows) != len(rhs):
        raise ValueError("linear system row count mismatch")
    matrix=[list(row)+[rhs[i]] for i,row in enumerate(rows)]
    pivot_rows=[]; row_index=0
    for col in range(columns):
        pivot=next((r for r in range(row_index,len(matrix)) if matrix[r][col]),None)
        if pivot is None:
            continue
        matrix[row_index],matrix[pivot]=matrix[pivot],matrix[row_index]
        scale=matrix[row_index][col]
        matrix[row_index]=[x/scale for x in matrix[row_index]]
        for r in range(len(matrix)):
            if r==row_index: continue
            factor=matrix[r][col]
            if factor:
                matrix[r]=[x-factor*y for x,y in zip(matrix[r],matrix[row_index])]
        pivot_rows.append(col); row_index+=1
        if row_index==len(matrix): break
    for row in matrix:
        if all(v==0 for v in row[:columns]) and row[columns]!=0:
            return None
    if len(pivot_rows)!=columns:
        return None
    solution=[Fraction(0)]*columns
    for r,col in enumerate(pivot_rows):
        solution[col]=matrix[r][columns]
    return tuple(solution)


def infer_recurrence(sequence: Sequence[Any], max_order: int = 8):
    values=tuple(_fraction(v) for v in sequence)
    if len(values)<5:
        raise ValueError("at least five sequence terms are required")
    if max_order<1:
        raise ValueError("max_order must be positive")
    upper=min(max_order,len(values)//2)
    for order in range(1,upper+1):
        rows=[]; rhs=[]
        for n in range(order,len(values)):
            rows.append([values[n-j-1] for j in range(order)])
            rhs.append(values[n])
        coeffs=_solve_unique(rows,rhs,order)
        if coeffs is not None:
            return {"order":order,"coefficients":coeffs,"initial":values[:order],"term_count":len(values)}
    return None


def _projective_factor(a: Sequence[Fraction], b: Sequence[Fraction]):
    if len(a)!=len(b): return None
    for x,y in zip(a,b):
        if y:
            factor=x/y
            if all(xx==factor*yy for xx,yy in zip(a,b)):
                return factor
            return None
        if x:
            return None
    return Fraction(1)


def compare_recurrence(sequence: Sequence[Any], max_order: int = 8):
    inferred=infer_recurrence(sequence,max_order=max_order)
    if inferred is None:
        return {"status":"no_unique_linear_recurrence_within_search_order",
                "max_order_searched":paired(min(max_order,len(sequence)//2)),
                "term_count":paired(len(sequence))}
    operator_matches=[]; exact_sequences=[]; projective=[]
    for reference in RECURRENCE_ATLAS:
        coeffs=tuple(_fraction(v) for v in reference["coefficients"])
        initial=tuple(_fraction(v) for v in reference["initial"])
        if inferred["coefficients"]==coeffs:
            operator_matches.append(reference["name"])
            if inferred["initial"]==initial:
                exact_sequences.append(reference["name"])
            factor=_projective_factor(inferred["initial"],initial)
            if factor is not None:
                projective.append({"reference":reference["name"],"initial_state_scale_factor":_format_fraction(factor)})
    return {
        "status":"unique_minimal_order_recurrence_found",
        "order":paired(inferred["order"]),
        "coefficients":[_format_fraction(v) for v in inferred["coefficients"]],
        "characteristic_polynomial_coefficients_descending":[_format_fraction(v) for v in _characteristic_coefficients(inferred["coefficients"])],
        "initial_state":[_format_fraction(v) for v in inferred["initial"]],
        "term_count":paired(inferred["term_count"]),
        "operator_matches":operator_matches,
        "exact_initial_state_matches":exact_sequences,
        "projective_initial_state_matches":projective,
        "interpretation":"An operator match identifies the same declared recurrence coefficients; initial-state agreement is a separate test. A finite observed sequence does not prove the recurrence outside its observed window."
    }


def _characteristic_coefficients(coefficients: Sequence[Fraction]):
    return tuple([Fraction(1)] + [-v for v in coefficients])


def generate_graph(name: str):
    if name.startswith("Q") and name[1:].isdigit():
        dimension=int(name[1:])
        if not 1<=dimension<=6: raise ValueError("reference hypercube dimension must be 1..6")
        nodes=list(range(1<<dimension))
        edges=[]
        for u in nodes:
            for bit in range(dimension):
                v=u^(1<<bit)
                if u<v: edges.append((u,v))
        return nodes,edges
    if name.startswith("C") and name[1:].isdigit():
        n=int(name[1:])
        if n<3: raise ValueError("cycle order must be at least three")
        return list(range(n)),[(i,(i+1)%n) for i in range(n)]
    if name.startswith("P") and name[1:].isdigit():
        n=int(name[1:])
        if n<1: raise ValueError("path order must be positive")
        return list(range(n)),[(i,i+1) for i in range(n-1)]
    if name.startswith("K") and name[1:].isdigit():
        n=int(name[1:])
        if n<1: raise ValueError("complete graph order must be positive")
        return list(range(n)),[(i,j) for i in range(n) for j in range(i+1,n)]
    if name.startswith("S") and name[1:].isdigit():
        leaves=int(name[1:])
        if leaves<1: raise ValueError("star leaf count must be positive")
        return list(range(leaves+1)),[(0,i) for i in range(1,leaves+1)]
    raise ValueError(f"unknown structural graph reference: {name}")


def _parse_graph(raw: Mapping[str,Any]):
    nodes=list(raw["nodes"]); edges=[tuple(edge) for edge in raw["edges"]]
    if not nodes: raise ValueError("graph must contain at least one declared node")
    if len(nodes)!=len(set(nodes)): raise ValueError("graph node labels must be unique")
    index={node:i for i,node in enumerate(nodes)}
    adjacency=[set() for _ in nodes]; seen=set()
    for edge in edges:
        if len(edge)!=2: raise ValueError("every graph edge must have two endpoints")
        a,b=edge
        if a not in index or b not in index: raise ValueError("edge endpoint is not a declared node")
        if a==b: raise ValueError("self-loops are not supported in this simple-graph comparator")
        pair=frozenset((a,b))
        if pair in seen: raise ValueError("duplicate undirected edge")
        seen.add(pair); i,j=index[a],index[b]
        adjacency[i].add(j); adjacency[j].add(i)
    return nodes,adjacency


def _components(adjacency):
    seen=set(); sizes=[]
    for start in range(len(adjacency)):
        if start in seen: continue
        queue=[start]; seen.add(start); size=0
        while queue:
            u=queue.pop(); size+=1
            for v in adjacency[u]:
                if v not in seen: seen.add(v); queue.append(v)
        sizes.append(size)
    return sorted(sizes,reverse=True)


def _bipartite(adjacency):
    colors={}
    for start in range(len(adjacency)):
        if start in colors: continue
        colors[start]=0; queue=deque([start])
        while queue:
            u=queue.popleft()
            for v in adjacency[u]:
                if v not in colors:
                    colors[v]=1-colors[u]; queue.append(v)
                elif colors[v]==colors[u]:
                    return False
    return True


def _diameter(adjacency):
    if not adjacency: return 0
    max_distance=0
    for start in range(len(adjacency)):
        distances={start:0}; queue=deque([start])
        while queue:
            u=queue.popleft()
            for v in adjacency[u]:
                if v not in distances:
                    distances[v]=distances[u]+1; queue.append(v)
        if len(distances)!=len(adjacency): return None
        max_distance=max(max_distance,max(distances.values()))
    return max_distance


def _matmul(a,b):
    n=len(a); out=[[0]*n for _ in range(n)]
    for i in range(n):
        for k,value in enumerate(a[i]):
            if value:
                row_b=b[k]
                for j,bv in enumerate(row_b):
                    if bv: out[i][j]+=value*bv
    return out


def _spectrum_fingerprint(adjacency):
    n=len(adjacency)
    matrix=[[1 if j in adjacency[i] else 0 for j in range(n)] for i in range(n)]
    power=[row[:] for row in matrix]; moments=[]
    for _ in range(n):
        moments.append(sum(power[i][i] for i in range(n)))
        power=_matmul(power,matrix)
    elementary=[Fraction(1)]
    for k in range(1,n+1):
        value=sum(((-1)**(i-1))*elementary[k-i]*moments[i-1] for i in range(1,k+1))/k
        elementary.append(value)
    coefficients=[Fraction(1)]
    for k in range(1,n+1):
        coefficients.append(((-1)**k)*elementary[k])
    return moments,coefficients


def _wl_colors(adjacency_a, adjacency_b=None):
    graphs=[adjacency_a] + ([adjacency_b] if adjacency_b is not None else [])
    sizes=[len(g) for g in graphs]
    nodes=[(gi,i) for gi,g in enumerate(graphs) for i in range(len(g))]
    signatures={node:(len(graphs[node[0]][node[1]]),) for node in nodes}
    def rank_map(values):
        keys=sorted(set(values.values()),key=repr)
        ids={key:i for i,key in enumerate(keys)}
        return {node:ids[value] for node,value in values.items()}
    colors=rank_map(signatures)
    for _ in range(sum(sizes)+1):
        new_signatures={}
        for gi,g in enumerate(graphs):
            for i,neighbors in enumerate(g):
                neighbor_colors=tuple(sorted(colors[(gi,j)] for j in neighbors))
                new_signatures[(gi,i)]=(colors[(gi,i)],neighbor_colors)
        new_colors=rank_map(new_signatures)
        if new_colors==colors: break
        colors=new_colors
    return [[colors[(gi,i)] for i in range(len(g))] for gi,g in enumerate(graphs)]


def _exact_isomorphic(a,b,max_nodes=250000):
    if len(a)!=len(b): return False,"different_vertex_count",0
    n=len(a)
    colors_a,colors_b=_wl_colors(a,b)
    if Counter(colors_a)!=Counter(colors_b):
        return False,"weisfeiler_leman_partition_mismatch",0
    degrees_a=[len(v) for v in a]; degrees_b=[len(v) for v in b]
    candidates={u:[v for v in range(n) if colors_b[v]==colors_a[u] and degrees_b[v]==degrees_a[u]] for u in range(n)}
    if any(not options for options in candidates.values()):
        return False,"no_degree_color_compatible_mapping",0
    mapping={}; used=set(); calls=0; aborted=False
    def recurse():
        nonlocal calls,aborted
        calls+=1
        if calls>max_nodes:
            aborted=True; return False
        if len(mapping)==n: return True
        best_u=None; best_options=None; best_key=None
        for u in range(n):
            if u in mapping: continue
            compatible=[]
            for v in candidates[u]:
                if v in used: continue
                ok=True
                for mapped_u,mapped_v in mapping.items():
                    if ((mapped_u in a[u]) != (mapped_v in b[v])):
                        ok=False; break
                if ok: compatible.append(v)
            key=(len(compatible),-sum(1 for neighbor in a[u] if neighbor in mapping),-degrees_a[u])
            if best_key is None or key<best_key:
                best_u,best_options,best_key=u,compatible,key
            if not compatible: return False
        for v in best_options:
            mapping[best_u]=v; used.add(v)
            if recurse(): return True
            used.remove(v); del mapping[best_u]
            if aborted: return False
        return False
    result=recurse()
    if aborted: return None,"search_node_cap_reached",calls
    return result,("exact_isomorphism" if result else "not_isomorphic"),calls


def graph_summary(nodes,adjacency):
    n=len(nodes); degrees=[len(neighbors) for neighbors in adjacency]
    m=sum(degrees)//2; components=_components(adjacency)
    moments,charpoly=_spectrum_fingerprint(adjacency)
    triangles=sum(sum(1 for v in adjacency[u] if v in adjacency[w])
                  for u in range(n) for w in adjacency[u] if u<w)//3
    return {"vertex_count":paired(n),"edge_count":paired(m),
        "degree_sequence_descending":[paired(v) for v in sorted(degrees,reverse=True)],
        "component_sizes_descending":[paired(v) for v in components],
        "cycle_rank":paired(m-n+len(components)),"bipartite":_bipartite(adjacency),
        "diameter":None if len(components)>1 else paired(_diameter(adjacency)),
        "triangle_count":paired(triangles),
        "adjacency_spectral_moments":[paired(int(v)) for v in moments],
        "adjacency_characteristic_polynomial_coefficients_descending":[_format_fraction(v) for v in charpoly]}


def compare_graph(raw: Mapping[str,Any], max_iso_vertices: int = 24, max_iso_nodes: int = 250000):
    nodes,adjacency=_parse_graph(raw); candidate=graph_summary(nodes,adjacency)
    matches=[]
    for reference_name in ("Q3","Q4","C5","C6","P5","K4","S4"):
        ref_nodes,ref_edges=generate_graph(reference_name)
        _,ref_adj=_parse_graph({"nodes":ref_nodes,"edges":ref_edges})
        reference=graph_summary(ref_nodes,ref_adj)
        spectral_equal=(candidate["adjacency_characteristic_polynomial_coefficients_descending"]==
                        reference["adjacency_characteristic_polynomial_coefficients_descending"])
        if candidate["vertex_count"]!=reference["vertex_count"] or candidate["edge_count"]!=reference["edge_count"]:
            continue
        if not spectral_equal:
            continue
        if len(nodes)<=max_iso_vertices:
            iso,status,calls=_exact_isomorphic(adjacency,ref_adj,max_iso_nodes)
        else:
            iso,status,calls=None,"exact_isomorphism_size_limit",0
        matches.append({"reference":reference_name,"spectral_fingerprint_equal":True,
                        "exact_isomorphic":iso,"isomorphism_status":status,
                        "isomorphism_search_nodes":paired(calls)})
    return {"label":raw.get("name","unnamed_graph"),"graph":candidate,
        "atlas_comparison_scope":"finite reference graphs Q3, Q4, C5, C6, P5, K4 and S4 only",
        "structural_matches":matches,
        "interpretation":"Equal characteristic polynomials indicate adjacency-cospectral candidates, not necessarily graph isomorphism. Exact isomorphism is tested only within declared search limits."}


def analyze_payload(payload: Mapping[str,Any]):
    graph_results=[compare_graph(g) for g in payload.get("graphs",[])]
    recurrence_results=[{"name":item.get("name","unnamed_sequence"),
                         **compare_recurrence(item["terms"],int(item.get("max_order",8)))}
                        for item in payload.get("sequences",[])]
    if not graph_results and not recurrence_results:
        raise ValueError("at least one graph or sequence candidate is required")
    return {"schema":"universe.structural-pattern-comparison.v1",
        "graph_candidate_count":paired(len(graph_results)),
        "sequence_candidate_count":paired(len(recurrence_results)),
        "graph_results":graph_results,"recurrence_results":recurrence_results,
        "global_guard":"Finite graph invariants and finite sequence recurrences are structural candidates; they do not establish common physical origin, causal coupling or universal law."}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input",type=Path)
    parser.add_argument("--output",type=Path,default=Path("structural_comparison.json"))
    args=parser.parse_args(); payload=json.loads(args.input.read_text(encoding="utf-8"))
    result=analyze_payload(payload)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Wrote {args.output}"); return 0

if __name__=="__main__": raise SystemExit(main())
