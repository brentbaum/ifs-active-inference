# C-V23b formation challenge report

Verdict: **FAIL**.

The runner verified every file in the V2.3.1 freeze manifest against commit `7d5650c` before inference. It used seeds `809301:809420`: 120 paired base worlds and 240 arm trajectories. No frozen engine, stage, contract, parameter, or result file was changed.

## Test 1 — formation dose-response

| Control level | Action dependence | Formed / n | Rate | 95% Wilson interval | Isotonic fit |
|---:|---:|---:|---:|---:|---:|
| 1 | 0.00 | 3 / 16 | 0.1875 | [0.0659, 0.4301] | 0.1875 |
| 2 | 0.25 | 0 / 16 | 0.0000 | [0.0000, 0.1936] | 0.0000 |
| 3 | 0.50 | 0 / 16 | 0.0000 | [0.0000, 0.1936] | 0.0000 |
| 4 | 0.75 | 0 / 16 | 0.0000 | [0.0000, 0.1936] | 0.0000 |
| 5 | 1.00 | 0 / 16 | 0.0000 | [0.0000, 0.1936] | 0.0000 |

Shape verdict: **PASS** (isotonic permutation p = 0.0060).

Calibration verdict: **FAIL**. The chronic-only bursty/no-control anchor was 0/6 = 0.0000, 95% Wilson interval [0.0000, 0.3903].

The shape and calibration conclusions above are intentionally separate: a monotone curve does not rescue a missed absolute anchor.

## Test 2 — no-event floor

| Control level | Formed / n | Rate | 95% Wilson interval | Verdict |
|---:|---:|---:|---:|---:|
| 1 | 0 / 4 | 0.0000 | [0.0000, 0.4899] | PASS |
| 2 | 0 / 4 | 0.0000 | [0.0000, 0.4899] | PASS |
| 3 | 0 / 10 | 0.0000 | [-0.0000, 0.2775] | PASS |
| 4 | 0 / 6 | 0.0000 | [0.0000, 0.3903] | PASS |
| 5 | 0 / 6 | 0.0000 | [0.0000, 0.3903] | PASS |

Test 2 verdict: **PASS**.

## Test 3 — continuity

The exact frozen p99 bound was `0.097067115510` (reported freeze value `0.097067`); the challenge hard maximum was `1.75 × p99 = 0.169867452143`. 0/492 acute slices exceeded p99 (0.000000; limit 0.015). The maximum change over all slices was 0.086834165520.

Test 3 verdict: **PASS**.

## Test 4 — persistence and mediation

The replay arm selected 4 formed low-control matched pairs (required at least 40). The available-minus-replay end persistent-evidence-margin effect was -2.967747, 95% paired interval [-3.788013, -2.147480].

End persistence versus the realized action/transition-only mediator: r = -0.6251, 95% interval [-0.9231, 0.1422]. Scheduled dose after conditioning on the mediator: partial r = 0.4268, 95% interval [-0.3974, 0.8699].

Test 4 verdict: **FAIL**.

## Retained failures

- Test 1 calibration failure: the level-1 no-control formation rate in one-acute worlds was below 0.60.
- Test 1 calibration failure: the chronic-only bursty no-control formation rate was below 0.25.
- Test 4 localization failure: fewer than 40 matched low-control pairs formed in the replay arm.
- Test 4 failure: the paired 95% interval for the avoidance-available persistence advantage did not exclude zero.
- Test 4 failure: end-state persistence did not track realized avoidance with a positive 95% interval while scheduled dose vanished after conditioning on that mediator.

## Configuration localization

The five-level gradient was compiled exactly as in V2.3.1's public open-generalization assay: a seed-paired fraction of event positions was assigned the public binary low-controllability state (fractions 1.00, 0.75, 0.50, 0.25, 0.00), and the remaining event positions were assigned high controllability. No continuous latent or interpolated transition table was added. Acute intensity was represented as a seed-drawn 1–3-slice event episode; acute centers were drawn in the middle 60% of each schedule. Steady-low and bursty-moderate chronic profiles were generated without reading run length or schedule shape inside the frozen model. Avoidance could remove chronic encounter evidence with the previously declared 0.82 probability, while acute events were not avoidable. The matched replay arm shared all exogenous random streams and engaged instead of avoiding.
