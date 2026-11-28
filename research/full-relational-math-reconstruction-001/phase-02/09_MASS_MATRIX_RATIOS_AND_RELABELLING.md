# 09 — Mass matrix: factorization, units and invariance

The legacy source declares n_E=(1,7,8,28,42,64,128) and M_E=M0*n_E*2^(E-1), E=1..7. The integer coefficients of M0 are (1,14,32,224,672,2048,8192). Adjacent coefficient ratios are 14, 16/7, 7, 3, 64/21, 4.

| E | n_E | 2^(E-1) | coefficient | possible exact key (not derivation) |
|---:|---:|---:|---:|---|
|1|1|1|1|unit|
|2|7|2|14|Q7 degree 7; 2*7|
|3|8|4|32|2^3; dimension of an 8D representation|
|4|28|8|224|dim so(8)=28; 28*8=448/2|
|5|42|16|672|42*16=f2(Q7)|
|6|64|32|2048|2^6*2^5|
|7|128|64|8192|2^7*2^6|

These factorizations do not give a unique decomposition into “topological” and “algebraic” components. Without a declared feature basis and selection rule, infinitely many decompositions are possible.

Source constants: p=3^12/2^19, theta=ln(p), M_mu=theta/128, K_SCALE=6.81e-25, M0=M_mu*K_SCALE. Numerically M0≈7.2095732e-29. It is kg only if K_SCALE has an independently established kg/model-unit calibration; the source supplies no such calibration or uncertainty. The helper multiplies by 10^27 and its docstring describes the return in 10^-27 kg units, so its numeric return is a scaled representation, not a direct kg value.

The source stress values are dimensionless. E_code=M_mu*sum(sigma_i^2) is therefore not joules. “Energy” as a variable name is not a dimensional proof.

Q7 automorphisms preserve degree, graph distance, adjacency spectrum, antipodes, incidence and face vector, but not decimal labels or absolute integer-index differences. The gate field uses |i-42| and |i-85|, not Hamming distance; it depends on the encoding. Atomic-number labels are likewise not Q7 invariants without an explicit, independently justified element-to-vertex mapping.

Exact identities 2:1, 3:2, 224=28*8, 672=42*16 and p=(3/2)^12/2^7 do not calibrate physical masses. Further validation needs pre-registered units, independent measured references, uncertainty budgets and holdout predictions.