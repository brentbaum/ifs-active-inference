# Milestone update — V2.3.1 Gate 6

C-V23b verdict: **FAIL**.

The challenge ran 120 paired base worlds (240 trajectories) using released seeds
`809301:809420`. Before the run, the runner
verified all 64 files named by the
V2.3.1 freeze manifest against commit `7d5650c`. The frozen p99
single-slice bound was `0.097067115510`.

Test verdicts:

- formation dose-response: **FAIL**
- no-event floor: **PASS**
- continuity: **PASS**
- persistence advantage and realized mediation: **FAIL**


Retained failures:

- Test 1 calibration failure: the level-1 no-control formation rate in one-acute worlds was below 0.60.
- Test 1 calibration failure: the chronic-only bursty no-control formation rate was below 0.25.
- Test 4 localization failure: fewer than 40 matched low-control pairs formed in the replay arm.
- Test 4 failure: the paired 95% interval for the avoidance-available persistence advantage did not exclude zero.
- Test 4 failure: end-state persistence did not track realized avoidance with a positive 95% interval while scheduled dose vanished after conditioning on that mediator.

Full per-seed results, effect intervals, shape/calibration localization, and
continuity accounting are in `results/challenges/C-V23b/`.
