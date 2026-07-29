# V2.5b development failures

## Gate 1 — FAIL

Retained failed proofs:

- `3_prior_charged_once`
- `6_material_reduction_odds_identity`

The independent oracle mutated the production prior through an aliased NumPy
array. See `gate-1-diagnosis-stub.md`. No Gate-2 or Gate-3 seed was opened.

The evaluator classified this as a pure software error and authorized the
input-copy repair. The original failure remains retained; the repaired Gate 1
passed all 18 proofs.

## Gate 3 — FAIL

The post-redescription do-over speedup was `0.12402008153052833`, with 95%
interval `[0.04146295367760523, 0.20657720938345142]`. Its direction and lower
interval bound were positive, but its mean did not reach the preregistered
`0.20` minimum.

All other Gate-3 criteria passed. No tuning or rerun was performed, and Gate 4
was not opened.
