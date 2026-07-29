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

The evaluator authorized mixed-verdict continuation with this as the sole
non-blocking failure family.

## Gate 4 — FAIL

The `remove_Z_Y` lesion removed `Z_Y` exactly (maximum prior deviation
`1.1102230246251565e-16`) but did not preserve every non-target edge above the
inherited `0.85` recovery floor. The minimum surviving-edge posterior was
`0.8154034066846899`.

All other seven lesion fingerprints passed. This is outside the adjudicated
do-over-speedup family and is blocking. Gate 5 was not opened.

The evaluator adjudicated the failed minimum-posterior operationalization as
an unaudited criterion transplant. The formal Gate-4 FAIL remains retained;
population survival accuracy at `0.85` is the blocking construct, and the
per-world minimum is descriptive.

## Gate 5 — adjudicated repetitions

Gate 5 passed every blocking cumulative and robustness criterion. The
do-over-speedup floor repeated below `0.20` in two of 16 cells:

- `episode_interaction:three_episodes`: mean `0.17245223748120153`;
- `precision_regimes:moderate`: mean `0.1954694958462501`.

These are retained verbatim under the committed Gate-3 adjudication's sole
scientific non-blocking limitation family.
