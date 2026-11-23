# 10 — Scalar hybrid recurrence: parameter sweep and event locking

The scalar recurrence transcribed from v2 is:
delta_n=theta*dt*[1+a*sin(omega*t_(n+1)+phase0)]
psi_pre=psi_n+delta_n
psi_(n+1)=r*psi_pre if psi_pre>P_threshold, otherwise psi_pre.
The source uses one if, not a while; one reset need not put the state below threshold.

The 315-case sweep combines p perturbations -0.1%, 0, +0.1%; amplitudes a in {0,.15,.3,.6,.9}; dt in {.5,1,1.5}; and reset r in {0,theta,.1,.5,.9,.98,.99}. The 404-case border scan tests 101 reset coefficients from .95 to 1 in .0005 increments at four initial phases.

## Baseline run
At a=.15, dt=1, r=theta and threshold p, a 100,000-step scalar run gives 1,344 reset events. First event times are 75,148,221,295,370,446,522,597,671,743,816,890. Tail gaps are 72–76 steps, mean 74.379 and standard deviation 1.2455. These are numerical properties of the isolated recurrence, not observed physical time.

pi_128 is a finite rational Leibniz sum. Continuous sinusoid period is 85*pi/pi_128≈85.21190138 model time units. At integer steps, omega/(2*pi)=pi_128/(85*pi) is irrational, so sampled phases have no finite exact period; they form an irrational rotation modulo 2*pi.

## Reset-border transition
For constant positive increment delta and 0<=r<1, the one-step event fixed point is psi*=r*delta/(1-r). It remains in the event state when psi*+delta=delta/(1-r)>p, i.e. r>1-delta/p. For delta=theta, the boundary is approximately .98663136. A conservative threshold using the minimum modulated increment theta*(1-.15) is .98863665.

Numerically the event-itinerary transition lies near .9865–.987: one-step tail fraction is about 87% at r=.985, 94% at .986, 97% at .9865 and 100% at .987 for the four sampled phases. At r=.98 it is about 49–50%; at .95 event gaps are 3–5 steps. This is a hybrid border-collision/event-lock transition, not a thermodynamic phase transition.

For bounded input and 0<=r<1 the scalar state is bounded because each reset contracts it; it may nevertheless remain above threshold after reset in a one-step lock. At r=1 the reset no longer reduces the state and positive increments cause unbounded growth; r>1 is expansive. These claims concern the scalar recurrence only, not material stability.

## Sensitivity and telemetry defect
For source formulae 128*p^5, 1-p^-85 and p^125, logarithmic elasticities are 5, 85*p^-85≈26.8647 and 125. Thus relative changes in p are strongly amplified.

The source calculates stress and E_code=M_mu*sum(sigma_i^2) before reset. On collapse it then multiplies stress and psi by theta but does not recompute energy before returning. Returned energy is pre-reset while returned stress/psi are post-reset. For a quadratic functional, post-reset energy would be theta^2 times pre-reset. Stress is rebuilt next step. The source stress and M_mu are dimensionless, so E_code is not in joules. This is a telemetry/state-ordering defect, not a physical energy burst.