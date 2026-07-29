# V2.5b freeze readiness

**Stage status:
`FROZEN_ADJUDICATED_MIXED_DO_OVER_SPEEDUP_LIMITATION`**

The stage is ready for evaluator freeze attestation. It is not a clean
all-gates-pass result.

## Gate standing

- Gate 1: original `FAIL` retained; authorized oracle input-copy repair passed
  all 18 proofs.
- Gate 2: `PASS`; eight-way macro recovery `0.999`, edge accuracies
  `1.000/1.000/0.999`, Brier `0.0004443519`, ECE `0.0008029370`.
- Gate 3: formal `FAIL` retained. Do-over speedup was `0.1240`, 95% interval
  `[0.0415, 0.2066]`, below the preregistered `0.20` floor. The committed
  adjudication classifies this effect-size limitation and its Gate-5
  repetitions as non-blocking. Every other Gate-3 criterion passed.
- Gate 4: formal `FAIL` retained. The runner's unaudited per-world minimum
  posterior transplant failed in one `remove_Z_Y` world. The committed
  adjudication makes that statistic descriptive and retains population
  survival accuracy at `0.85` as blocking; retained population accuracy was
  `1.00` in all three edge-lesion cells.
- Gate 5: `PASS`; all blocking cumulative and robustness criteria passed in
  all 16 cells. Two do-over-speedup repetitions missed the floor and are
  retained verbatim under the sole scientific limitation family.

## Robustness and regression

Gate 5 consumed seeds `1106000:1119999` exactly once across eight two-level
dimensions. Material-reduction rates ranged from `0.7486` to `0.9280`;
false full-burden reduction was `0.0` in every cell. Population complete
surviving-edge accuracy ranged from `0.9920` to `1.0`. All held-out margins,
joint-over-marginal directions, historical-retention checks, lesion-target
checks, and stress-return checks passed.

The cumulative fast suite passed all 21 modules with zero failures in
`56.755` seconds.

## Custody

The named bounds remain:

- inherited formation `B_max = 3.801426508560692`;
- V2.4 common emissions `B_max = 6.704414354964107`;
- V2.5a configural `B_max = 6.084736253211209`;
- V2.5a marginal accounting `B_max = 6.704414354964107`;
- V2.5b `B_max = 11.302393144606405`.

Escrow `2020000:2021999` was not accessed. No C-V25B artifact was read,
authored, or executed.
