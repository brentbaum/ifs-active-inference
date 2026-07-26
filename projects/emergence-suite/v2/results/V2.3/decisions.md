# V2.3 decision log

Frozen design decisions made before protocol execution.

1. The progressive spec does not prescribe a time-horizon representation.
   V2.3 uses exact slice filtering with posterior-to-prior propagation. Every
   slice is a complete finite model checked by the independent enumeration
   oracle; no scientific state is carried except posteriors and conjugate
   parameter posteriors.
2. `H_formation=0/1` is always a finite-model posterior. Terms such as
   “forms,” “persists,” and “wins” are reporting language only; no comparison
   writes a boolean state.
3. Low controllability is represented structurally by action-invariant
   policy-consequence rows. It is not a low scalar multiplied into a result.
4. Reflexive collapse makes the now-context likelihood nondiagnostic. It does
   not suppress event observations, change local event likelihoods, or add a
   persistence bonus.
5. An exact replay shares the full exogenous event, overwhelm, broadcast,
   danger schedule, and component random uniforms with closed loop. It fixes
   engage policy; only the action-dependent world transition and its observed
   consequences may diverge.
6. The avoidance mediator is the within-world product of realized avoidance
   rate and the excess rate of threat-maintaining transitions following
   avoidance versus engagement. It uses no posterior, fitted coefficient, or
   configured transfer constant.
7. Real danger is evaluated against the persistent candidate as ground truth.
   High persistence in that assay is an adaptive recovery success.
8. The single-slice 99th-percentile audit quantity pools absolute adjacent
   changes in the persistent-model posterior across every arm of all six open
   assays. It is recorded but never used as a gate threshold.
9. The sealed C-V23 plaintext remains unavailable. The public challenge-family
   sentence in the adopted spec is sufficient to check contract
   expressibility; no configuration is inferred from its committed hash.

