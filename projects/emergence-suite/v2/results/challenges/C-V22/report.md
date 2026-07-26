# C-V22 Gate 6 report

Verdict: **FAIL**

Frozen identity: 31 files checked
against `60ba6e0`, zero mismatches.

## Preregistered composition tests

- Structure recovery: PASS;
  mean association AUC `1.000`
  (95% interval `1.000`–
  `1.000`).
- Segment-gated uptake:
  PASS;
  broad-minus-narrowed root attribution
  `0.236`
  (95% interval
  `0.227`–
  `0.244`);
  local broad/narrowed difference
  `5.55e-17`.
- Transfer follows structure:
  FAIL;
  cue-1 structural wins `60/60`,
  cue-5 floor-clean worlds `29/60`.
- Mediation: PASS;
  null-root worlds `11`,
  maximum null-world transfer `0.00822`.

Matched delivered predictive log likelihood differed by
`0`
between treatment arms. Segment identity and boundaries were not passed to
inference.

## Failure localization

Retained localization: transfer did not follow learned root structure.

No frozen engine, stage, contract, tolerance, or manifest file was modified.


## Read-only failure localization

The cue-5 floor failed in `31/60` worlds. Cue 5's learned association
ranged from `0.390` to `0.604` around the
true factorized value 0.5. Mean absolute deviation from 0.5 was
`0.0486` in
failed worlds versus
`0.0161` in
passing worlds. Absolute association deviation correlated `0.970`
with transfer; absolute G revision correlated
`0.998` with transfer.

This localizes the failure to absolute calibration of the learned
non-association: repeated correction of cue 5 revised G when its finite-history
posterior lay away from 0.5. Mediation still passed, so no root-free transfer
route was detected.
