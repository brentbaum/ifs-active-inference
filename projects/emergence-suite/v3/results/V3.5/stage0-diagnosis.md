# V3.5 Stage-0 stop — planned effects unattainable and recovery uncalibrated

## Verdict

`STOPPED_AT_STAGE0_UNATTAINABLE`

The complete pilot block `3500000:3501999` was consumed under serializing
trace contexts and is barred. No Gate-2–5 seed was opened. C-V35 escrow
`4050000:4054999` remains untouched.

## Primary finding

The exact planned cells did not expose the V3.5 scientific claims. Mean
paired-effect magnitudes were:

| Effect family | Pilot value |
|---|---:|
| befriend none vs all | `9.63e-16` |
| denied-contact masked vs delivered | `5.63e-16` |
| two vs three modes | `-1.96e-32` |
| remaining vs pressure trust | `1.0` |
| exclusion vs engagement | `1.24e-15` |
| low vs high stakes | `4.33e-17` |
| support one vs all | `0.0` |
| opposed/allied topology score | `-0.6667` |

Thus six required policy/readout contrasts were numerically null, support
targeting was exactly null, and the topology contrast had the wrong sign.
Only the partner remaining-versus-pressure query was exposed.

## Apparatus localization

The joint-policy posterior is computed from model-averaged shared outcome
forecasts, but the planned manipulations do not reach it materially:

- partner observations saturate the global partner posterior, so mode-specific
  befriending/support observations add no usable policy distinction;
- low/high stakes rescale a nearly symmetric 27-policy score and leave the
  vulnerable-mode marginal effectively unchanged;
- observed exclusion/engagement histories do not materially identify a
  different future joint-policy marginal;
- the active-mode candidate silently ignores typed channels beyond its
  declared active count. Consequently a smaller-mode candidate is not charged
  for non-missing higher-slot observations, and active-count recovery is only
  `0.4275`;
- the cross-mode outcome production does not recover sign/topology on the
  planned policy schedules.

These are representational/exposure defects, not floors that can be repaired
by threshold selection.

## Calibration-by-theorem failure

The 800 recovery worlds were intended to be sampled from the scorer's own
prior and likelihood, yet reported:

| Metric | Result |
|---|---:|
| 95% structure-set coverage | `0.4225` |
| structure ECE | `0.329671` |
| exact-program accuracy | `0.26125` |
| active-mode-count accuracy | `0.4275` |
| minimum edge accuracy | `0.64875` |
| exact complete-log-probability error | `0.0` |
| normalization error | `2.86e-14` |

Exact complete-path log-probability parity and normalization therefore do not
establish marginal calibration here. Either the generated distribution and
the marginalized scorer differ, or posterior aggregation/coverage is wrong.
That discrepancy must be independently localized before any recovery gate.

Gate 1's enumerable channel normalization and small oracle fixture remain
valid, but they were insufficient to detect this population-level
calibration failure. No repair is attempted in this run.

## Custody

- Pilot: consumed and traced, `3500000:3501999`.
- Gates 2–5: unopened.
- C-V35: unopened.
- Frozen V3.5 atomic bound: `3.4760986898352733`.
