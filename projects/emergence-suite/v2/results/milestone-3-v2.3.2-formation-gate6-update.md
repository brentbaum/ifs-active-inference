# V2.3.2 formation — Gate 6 update

C-V232-F verdict: **FAIL**.

The c67e853 identity check passed for all 33 frozen files. The challenge used
the first 200 released seeds, `813101:813300`.

- No-event neutrality: PASS, 40/40 neutral and 0/40 formation.
- Schedule invariance: PASS, 20/20 triplets within the evidence criterion and
  20/20 with identical selected candidates.
- D/P separation: PASS. D-cell D selection `.96`, P-cell P selection `1.00`,
  D-cell P cross-selection `0`.
- Calibration: PASS. Brier `.012501`, ECE `.050226`, false-P `0`.
- Continuity: FAIL because the second clause is inexpressible. The analytic
  clause passed with zero exceedances (`2.670557` maximum versus the frozen
  `3.801427` bound), but c67e853 contains no frozen empirical p99 rate bound
  for the challenge's `1.75×` comparison. No post-seal threshold was invented.
- Independent constitution audit: PASS, maximum recombination error
  `5.68e-14` over ten seed-drawn worlds.

The numerical formation result is otherwise positive, but Gate 6 requires all
six tests. The missing preregistered continuity quantity therefore stands as
the sealed failure.
