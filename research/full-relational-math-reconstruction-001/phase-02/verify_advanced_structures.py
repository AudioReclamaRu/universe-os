#!/usr/bin/env python3
"""Exact H3 checks in Q(sqrt(5)) and rational D4 triality checks."""
from __future__ import annotations
import itertools,json
from collections import Counter,deque
from fractions import Fraction as F

def z():return (F(0),F(0))
def o():return (F(1),F(0))
def add(x,y):return (x[0]+y[0],x[1]+y[1])
def sub(x,y):return (x[0]-y[0],x[1]-y[1])
def mul(x,y):return (x[0]*y[0]+5*x[1]*y[1],x[0]*y[1]+x[1]*y[0])
def sc(x,c):return (x[0]*c,x[1]*c)
def sm(xs):
 r=z()
 for x in xs:r=add(r,x)
 return r
def dot(x,y):return sm(mul(a,b) for a,b in zip(x,y))
def mid(n):return tuple(tuple(o() if i==j else z() for j in range(n)) for i in range(n))
def mm(a,b):
 n=len(a);return tuple(tuple(sm(mul(a[i][k],b[k][j]) for k in range(n)) for j in range(n)) for i in range(n))
def det3(m):
 a,b,c=m[0];d,e,f=m[1];g,h,i=m[2]
 return add(sub(mul(a,sub(mul(e,i),mul(f,h))),mul(b,sub(mul(d,i),mul(f,g)))),mul(c,sub(mul(d,h),mul(e,g))))
def roots_h3():
 v=((F(1,2),F(0)),(F(1,4),F(1,4)),(F(-1,4),F(1,4)));r=set()
 for k in range(3):
  for s in (-1,1):
   x=[z(),z(),z()];x[k]=(F(s),F(0));r.add(tuple(x))
 for p in ((0,1,2),(1,2,0),(2,0,1)):
  for signs in itertools.product((-1,1),repeat=3):
   r.add(tuple(sc(v[p[j]],F(signs[j])) for j in range(3)))
 return r
def refl(a):
 assert dot(a,a)==o()
 return tuple(tuple(sub(o() if i==j else z(),sc(mul(a[i],a[j]),F(2))) for j in range(3)) for i in range(3))
def sign_q5(x):
 a,b=x
 if a==0:return 0 if b==0 else (1 if b>0 else -1)
 if b==0:return 1 if a>0 else -1
 d=a*a-5*b*b
 if d>0:return 1 if a>0 else -1
 return 1 if b>0 else -1
def cross(a,b):
 return (sub(mul(a[1],b[2]),mul(a[2],b[1])),
         sub(mul(a[2],b[0]),mul(a[0],b[2])),
         sub(mul(a[0],b[1]),mul(a[1],b[0])))
def vsub(a,b):return tuple(sub(x,y) for x,y in zip(a,b))
def h3_facets(R):
 roots=sorted(R,key=lambda r:tuple(float(a)+float(b)*5**.5 for a,b in r));facets=set()
 for i,j,k in itertools.combinations(range(len(roots)),3):
  a,b,c=roots[i],roots[j],roots[k];n=cross(vsub(b,a),vsub(c,a))
  if all(x==z() for x in n):continue
  signs=[];cop=[]
  for t,x in enumerate(roots):
   sg=sign_q5(dot(n,vsub(x,a)))
   if sg:signs.append(sg)
   else:cop.append(t)
  if not(1 in signs and -1 in signs) and len(cop)>=3:facets.add(tuple(cop))
 counts=Counter(len(f) for f in facets)
 assert len(facets)==32 and counts==Counter({3:20,5:12})
 return counts

def check_h3():
 R=roots_h3();assert len(R)==30 and all(dot(x,x)==o() for x in R)
 S=[refl(a) for a in R]
 for a in R:
  for x in R:
   t=sc(dot(x,a),F(2));y=tuple(sub(x[i],mul(t,a[i])) for i in range(3));assert y in R
 I=mid(3);G={I};q=deque([I])
 while q:
  A=q.popleft()
  for s in S:
   B=mm(A,s)
   if B not in G:G.add(B);q.append(B);assert len(G)<=120
 dc=Counter(det3(g) for g in G);assert len(G)==120 and dc==Counter({o():60,sc(o(),F(-1)):60})
 ph=(F(1,4),F(1,4));iph=(F(-1,4),F(1,4))
 E={sc(o(),F(-1)),sc(ph,F(-1)),sc(o(),F(-1,2)),(F(1,4),F(-1,4)),z(),iph,sc(o(),F(1,2)),ph,o()}
 assert {dot(a,b) for a in R for b in R}==E
 edges=sum(dot(a,b)==ph for a,b in itertools.combinations(R,2));assert edges==60
 return {"roots":30,"exact_unit_norms":True,"full_group_order":120,"det_plus":60,"det_minus":60,"inner_products":9,"root_polytope_edges":60}

def ident(n):return tuple(tuple(F(int(i==j)) for j in range(n)) for i in range(n))
def tr(m):return tuple(tuple(m[i][j] for i in range(len(m))) for j in range(len(m[0])))
def apply(m,v):return tuple(sum(m[i][j]*v[j] for j in range(len(v))) for i in range(len(m)))
def matmul(a,b):
 n=len(a);return tuple(tuple(sum(a[i][k]*b[k][j] for k in range(n)) for j in range(n)) for i in range(n))
def d4():
 R=set()
 for i,j in itertools.combinations(range(4),2):
  for a,b in itertools.product((-1,1),repeat=2):
   x=[0]*4;x[i]=a;x[j]=b;R.add(tuple(F(t) for t in x))
 V=set()
 for i in range(4):
  for s in (-1,1):
   x=[F(0)]*4;x[i]=F(s);V.add(tuple(x))
 SP,SM=set(),set()
 for s in itertools.product((-1,1),repeat=4):
  x=tuple(F(t,2) for t in s);(SP if sum(t==-1 for t in s)%2==0 else SM).add(x)
 return R,V,SP,SM
h=F(1,2)
T2=((h,h,h,-h),(h,h,-h,h),(h,-h,h,h),(-h,h,h,h))
T3=((h,h,h,h),(h,h,-h,-h),(h,-h,h,-h),(-h,h,h,-h))
def check_d4():
 R,V,SP,SM=d4();I=ident(4)
 assert (len(R),len(V),len(SP),len(SM))==(24,8,8,8)
 f=lambda T,S:{apply(T,x) for x in S}
 for T in (T2,T3):assert matmul(tr(T),T)==I and f(T,R)==R
 assert matmul(T2,T2)==I and matmul(matmul(T3,T3),T3)==I
 assert f(T3,V)==SM and f(T3,SM)==SP and f(T3,SP)==V
 assert f(T2,V)==SM and f(T2,SM)==V and f(T2,SP)==SP
 G={I};q=[I]
 while q:
  A=q.pop()
  for T in (T2,T3):
   B=matmul(T,A)
   if B not in G:G.add(B);q.append(B);assert len(G)<=6
 assert len(G)==6
 return {"D4_roots":24,"dim_so8":28,"three_8d_rep_sets":True,"T2_order":2,"T3_order":3,"triality_group":"S3","order":6}
def main():
 print(json.dumps({"status":"PASS_EXACT_Q_SQRT5_H3_AND_RATIONAL_D4","H3":check_h3(),"D4_Spin8":check_d4()},indent=2))
if __name__=="__main__":main()
