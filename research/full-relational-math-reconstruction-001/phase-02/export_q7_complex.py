#!/usr/bin/env python3
"""Export the Q7 face poset and exact H3/D4 root tables (Python stdlib only)."""
from __future__ import annotations
import argparse,csv,itertools,json,math
from fractions import Fraction as F
from pathlib import Path

SYMS="-0+"
B=7
VAL={"-":0,"0":None,"+":1}

def wc(path,header,rows):
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f);w.writerow(header);w.writerows(rows)

def export_q7(out):
    states=["".join(s) for s in itertools.product(SYMS,repeat=B)]
    ix={s:i for i,s in enumerate(states)}
    info={};face_rows=[];inc=[];covers=[];adj=[]
    for fid,s in enumerate(states):
        mask=value=0
        for j,ch in enumerate(s):
            bit=1<<(B-1-j)
            if ch!="0":
                mask|=bit
                if ch=="+":value|=bit
        d=s.count("0")
        vs=[]
        for v in range(1<<B):
            if all(ch=="0" or ((v>>(B-1-j))&1)==VAL[ch] for j,ch in enumerate(s)):
                vs.append(v)
        assert len(vs)==1<<d
        info[s]=(fid,d,mask,value,set(vs))
        face_rows.append((fid,s,d,format(mask,"07b"),format(value,"07b"),
          format(((1<<B)-1)^mask,"07b"),len(vs),3**d,7-d if d<7 else 0))
        inc.extend((fid,v) for v in vs)
    for s in states:
        fid,d,mask,value,_=info[s]
        for j,ch in enumerate(s):
            if ch=="0":continue
            sup=s[:j]+"0"+s[j+1:]
            covers.append((fid,ix[sup],d,d+1,B-1-j,VAL[ch]))
    for d in range(1,7):
        group=[(s,info[s]) for s in states if info[s][1]==d]
        for (sa,a),(sb,b) in itertools.combinations(group,2):
            common=a[2]&b[2]
            if (a[3]^b[3])&common:continue
            if (a[2]|b[2]).bit_count()==B-(d-1):
                adj.append((a[0],b[0],d,d-1))
    edges=[(v,v^(1<<k),k) for v in range(1<<B) for k in range(B) if (v^(1<<k))>v]
    fv=[math.comb(7,d)*2**(7-d) for d in range(8)]
    cover_by=[sum(r[2]==d for r in covers) for d in range(7)]
    adj_by=[sum(r[2]==d for r in adj) for d in range(8)]
    assert len(face_rows)==2187 and fv==[128,448,672,560,280,84,14,1]
    assert len(covers)==10206 and len(adj)==20412 and len(inc)==16384 and len(edges)==448
    wc(out/"Q7_FACES.csv",["face_id","state","dimension","fixed_mask","fixed_value_mask","free_mask","vertex_count","subface_count_including_self","immediate_coface_count"],face_rows)
    wc(out/"Q7_FACE_COVERS.csv",["lower_face_id","upper_face_id","lower_dimension","upper_dimension","newly_fixed_coordinate","fixed_value"],covers)
    wc(out/"Q7_FACE_ADJACENCY.csv",["face_a_id","face_b_id","dimension","shared_facet_dimension"],adj)
    wc(out/"Q7_FACE_VERTEX_INCIDENCE.csv",["face_id","vertex_id"],inc)
    wc(out/"Q7_VERTEX_EDGES.csv",["vertex_a","vertex_b","flipped_bit"],edges)
    summary={"bits":7,"vertices":128,"edges":448,"faces_total":2187,"face_vector":fv,
      "abstract_face_lattice_elements_including_empty":2188,"cover_count":len(covers),
      "cover_counts_by_lower_dimension":cover_by,"same_dimension_adjacency_count":len(adj),
      "same_dimension_adjacency_by_dimension":adj_by,"vertex_face_incidences":len(inc),
      "strict_nonempty_inclusions":75938,"assertions":"PASS"}
    (out/"Q7_FACE_LATTICE_SUMMARY.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")

def export_roots(out):
    z=(F(0),F(0)); vals=((F(1,2),F(0)),(F(1,4),F(1,4)),(F(-1,4),F(1,4)))
    roots=set()
    for k in range(3):
        for sg in (-1,1):
            v=[z,z,z];v[k]=(F(sg),F(0));roots.add(tuple(v))
    for perm in ((0,1,2),(1,2,0),(2,0,1)):
        for signs in itertools.product((-1,1),repeat=3):
            roots.add(tuple((vals[perm[j]][0]*signs[j],vals[perm[j]][1]*signs[j]) for j in range(3)))
    def approx(r):return tuple(float(a)+float(b)*math.sqrt(5) for a,b in r)
    roots=sorted(roots,key=approx)
    wc(out/"H3_ROOTS_Q5.csv",["root_id","x_a","x_b","y_a","y_b","z_a","z_b"],
       [[i]+[str(c) for xy in r for c in xy] for i,r in enumerate(roots)])
    wc(out/"H3_ROOTS.csv",["root_id","x","y","z","norm_squared"],
       [[i]+[format(float(a)+float(b)*math.sqrt(5),".15g") for a,b in r]+["1"] for i,r in enumerate(roots)])
    d4=[]
    for i,j in itertools.combinations(range(4),2):
        for a,b in itertools.product((-1,1),repeat=2):
            v=[0]*4;v[i]=a;v[j]=b;d4.append(v)
    wc(out/"D4_ROOTS_SO8.csv",["root_id","e1","e2","e3","e4"],[[i]+v for i,v in enumerate(d4)])
    (out/"H3_D4_EXPORT_SUMMARY.json").write_text(json.dumps({"H3":{"roots":30,"field":"Q(sqrt(5))"},"D4":{"roots":24,"dim_so8":28}},indent=2),encoding="utf-8")

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--out",type=Path,default=Path("data"));a=ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=True);export_q7(a.out);export_roots(a.out)
    print("PASS: Q7 2187 faces / 10206 covers / 20412 adjacencies / 16384 incidences / 448 edges; H3 30; D4 24")
if __name__=="__main__":main()
