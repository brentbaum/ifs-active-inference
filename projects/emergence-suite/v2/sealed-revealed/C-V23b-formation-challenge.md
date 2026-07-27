# Sealed stage challenge C-V23b — formation generalization, second attempt

**Sealed by evaluator after C-V23's four-test FAIL, before any V2.3.1 development. Runs on the frozen V2.3.1 stage with zero new code. C-V23 is burned. This family varies the schedule dimensions C-V23 held fixed, so a repair fitted to C-V23's revealed schedule cannot pass here.**

## Configuration
Single agent (V2.2.1 stack + V2.3.1 formation machinery). Schedule family, per seed:
- Length drawn from {60, 90, 120} slices.
- Acute events: 0, 1, or 2 (cell-assigned), intensities drawn from a band, timings seed-drawn anywhere in the middle 60% of the run.
- Chronic background: three profiles — none, steady-low, bursty-moderate (drawn per world).
- **Controllability as a gradient:** five levels from fully action-independent to strongly action-dependent transitions (cell-assigned), not a binary.
- Avoidance availability crossed as before, with matched-replay pairing.

Cells span (acute count × controllability level × avoidance); 240 worlds total from escrow block C-V23b (seeds 809301:809900), paired streams.

## Tests
1. **Formation dose-response:** probability of persistent-model selection (margin ≥ 1 nat) decreases monotonically across the five controllability levels (isotonic trend test, preregistered), with level-1 (no control) rate ≥ 0.60 in 1-acute worlds and level-5 rate ≤ 0.15. Chronic-only bursty worlds with no control form at a nonzero rate (≥ 0.25) — the gradual route must exist in this family too.
2. **No-event floor:** 0-acute, none-chronic worlds form at ≤ 0.05 at every controllability level.
3. **Continuity under provocation:** across ALL worlds, single-slice persistent-posterior changes exceed the V2.3.1-frozen p99 bound in ≤ 1.5% of slices with acute events and never exceed 1.75× the bound. (The bound is whatever V2.3.1's freeze records; the multiplier and rates are fixed here.)
4. **Persistence and mediation, evaluable by construction:** among formed low-control worlds (expected n ≥ 40 by test 1's rates), avoidance-available vs matched replay shows the persistence advantage (paired CI excluding zero) and end-state persistence tracks realized avoidance, not scheduled dose (partial correlation as in C-V23 test 4).

Pass = all four. If test 1's monotone dose-response holds but rates miss their anchors, report the curve and the miss separately — shape and calibration are different failures.
