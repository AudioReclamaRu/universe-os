#!/usr/bin/env python3
"""Scalar recurrence sweeps; does not import or modify legacy application."""
from __future__ import annotations
import argparse,csv,itertools,json,math
from pathlib import Path
P=3**12/2**19;THETA=math.log(P);PI128=4*sum((-1)**k/(2*k+1) for k in range(128));OMEGA=2*PI128/85

def sim(p=P,a=.15,r=None,dt=1.,steps=2000,phase=0.):
 th=math.log(p);r=th if r is None else r
 if p<=1 or dt<=0 or not 0<=a<1:raise ValueError("require p>1, dt>0, 0<=a<1")
 t=psi=0.;events=[];mx=0.
 for _ in range(steps):
  t+=dt;pre=psi+th*dt*(1+a*math.sin(t*OMEGA+phase));psi=pre;mx=max(mx,pre)
  if pre>p:events.append(t);psi=r*pre
 gaps=[events[i]-events[i-1] for i in range(1,len(events))];tail=gaps[-1000:]
 mean=sum(tail)/len(tail) if tail else None
 sd=math.sqrt(sum((x-mean)**2 for x in tail)/len(tail)) if tail else None
 p1=sum(abs(x-dt)<1e-12 for x in tail)/len(tail) if tail else 0.
 regime=("NONCONTRACTING_OR_EXPANSIVE" if r>=1 else "ONE_STEP_EVENT_LOCK" if p1>=.995 and len(tail)>=20 else
  "SINGLE_INTERVAL_LOCK" if tail and max(tail)==min(tail) else "MULTI_INTERVAL_BORDER_OR_QUASIPERIODIC" if tail else "NO_REPEATED_EVENTS")
 return {"p":p,"theta":th,"amplitude":a,"reset_multiplier":r,"threshold":p,"dt":dt,"steps":steps,
  "events":len(events),"first_event_times":events[:12],"mean_gap_tail":mean,"std_gap_tail":sd,
  "min_gap_tail":min(tail) if tail else None,"max_gap_tail":max(tail) if tail else None,
  "period_one_fraction_tail":p1,"event_rate":len(events)/steps,"psi_end":psi,"psi_pre_event_max_observed":mx,
  "regime_diagnostic":regime}
def write(p,rows):
 with p.open("w",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--out",type=Path,default=Path("dynamics_export"));ap.add_argument("--steps",type=int,default=2000);ap.add_argument("--bifurcation-steps",type=int,default=5000);a=ap.parse_args()
 a.out.mkdir(parents=True,exist_ok=True);rows=[]
 for dp,amp,dt,rs in itertools.product((-.001,0,.001),(0,.15,.3,.6,.9),(.5,1.,1.5),("zero","theta",.1,.5,.9,.98,.99)):
  p=P*(1+dp);r=math.log(p) if rs=="theta" else 0. if rs=="zero" else rs
  x=sim(p,amp,r,dt,a.steps);x["p_relative_delta"]=dp;x["reset_spec"]=str(rs);rows.append(x)
 write(a.out/"LEGACY_RESET_PARAMETER_SWEEP.csv",rows)
 border=[]
 for k in range(101):
  r=round(.95+k*.0005,7)
  for ph in (0.,math.pi/2,math.pi,3*math.pi/2):
   x=sim(P,.15,r,1.,a.bifurcation_steps,ph)
   border.append({"reset_multiplier":r,"phase0_radians":ph,"events":x["events"],"mean_gap_tail":x["mean_gap_tail"],
    "std_gap_tail":x["std_gap_tail"],"min_gap_tail":x["min_gap_tail"],"max_gap_tail":x["max_gap_tail"],
    "period_one_fraction_tail":x["period_one_fraction_tail"],"psi_end":x["psi_end"],"regime_diagnostic":x["regime_diagnostic"]})
 write(a.out/"RESET_BORDER_BIFURCATION_SCAN.csv",border)
 sens=[];aa0=128*P**5;w0=1-P**-85;d0=P**125
 for dp in (-.01,-.001,-.0001,0,.0001,.001,.01):
  p=P*(1+dp);aa=128*p**5;ww=1-p**-85;dd=p**125
  sens.append({"p_relative_delta":dp,"p":p,"theta":math.log(p),"alpha_inverse_model":aa,
   "alpha_inverse_relative_change_percent":(aa/aa0-1)*100,"omega_lambda_model":ww,"omega_lambda_absolute_change":ww-w0,
   "dm_to_baryon_p125_model":dd,"dm_to_baryon_relative_change_percent":(dd/d0-1)*100})
 write(a.out/"LEGACY_P_SENSITIVITY.csv",sens)
 baseline=sim(steps=max(a.steps,100000))
 summary={"status":"PARAMETER_SWEEP_COMPLETED","baseline":baseline,"pi_128":PI128,
  "forcing_period_model_time":85*math.pi/PI128,"constant_increment_event_lock_r":1-THETA/P,
  "sufficient_minimum_increment_r":1-THETA*(1-.15)/P,"sweep_rows":len(rows),"border_rows":len(border),
  "sensitivity_rows":len(sens),"log_elasticities":{"alpha_inverse":5,"omega_lambda":85*P**-85,"dm_to_baryon":125},
  "limits":["Scalar recurrence only; GUI not run.","Conditional contraction assumes fixed event itinerary.","Event changes are discontinuous near threshold.","Time/stress/energy lack physical calibration."]}
 (a.out/"NONLINEAR_DYNAMICS_SWEEP_SUMMARY.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
 print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
