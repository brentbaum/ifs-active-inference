# Suite v2 — V2.3 formation and active persistence

Stage verdict: **PASS** for gates 1–5.

## Formation semantics

- Event-precision log-odds increase: `1.733675`.
- Low/high-control action evidence contrasts:
  `0.000000` /
  `1.558145`.
- Action-dependent transition effect:
  `0.700000`.
- Reflexive-collapse context effect:
  `0.126921`.
- Independent finite-comparison error:
  `1.11e-16`.

## Recovery

- Structure accuracy / mean true probability:
  `1.000` / `0.915`.
- Structure Brier / ECE:
  `0.0169` / `0.0853`.
- Controllability / broadcast accuracy:
  `0.906` / `1.000`.
- Policy-consequence parameter MAE / coverage:
  `0.0292` /
  `0.945`.

## Open assays

- Acute final persistent posterior:
  `0.793`
  (95% interval `0.719`–
  `0.866`).
- Gradual final posterior / accumulated change:
  `0.890` /
  `0.670`.
- Acute-minus-controlled effect:
  `0.368`.
- Low-minus-high controllability effect without overwhelm:
  `0.196`.
- Adaptive real-danger persistence:
  `0.998`;
  this is correct structure recovery, not an error.

The realized closed-loop chain was:

`policy 0.441 -> world 0.290
-> observation 0.222
-> persistent model 0.108
-> G 0.282`.

Every paired 95% interval excludes zero. The mediator computed only from
realized actions and transitions was `0.254`
(`0.203`–`0.309`).

## Freeze audit and regressions

The empirical 99th-percentile single-slice absolute change in persistent-model
posterior across all open assay arms was
`0.294529387` over
`10944` slice changes.

All isolated V2.3 lesions passed. All V2.0, V2.1, and V2.2.1 gates passed
unchanged. The full 32-point neighborhood profile, joint reliability
perturbations, prior sensitivity, and byte-identical full-seed determinism
check are retained in the stage artifacts.

## Status

V2.3 is a freeze candidate. C-V23 remains sealed, unrevealed, and unrun.
No evaluator seed was used and no commit was created.
