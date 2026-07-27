# C-V232-F formation challenge

Verdict: **FAIL**.

The frozen identity check passed for
`33` files at
`c67e853`. The first 200 released seeds
`813101:813300` were used.

## Test outcomes

1. No-event neutrality: **PASS**.
   Neutral worlds `40/40`;
   formation `0/40`;
   maximum prior difference
   `0`.
2. Schedule invariance: **PASS**.
   Relative-evidence criterion
   `20/20`;
   identical selection
   `20/20`.
   Winning evidence is the frozen comparative margin over the runner-up, so
   candidate-common no-event support cancels as required by the constitution.
3. D/P separation: **PASS**.
   D-cell D selection
   `0.960`;
   P-cell P selection
   `1.000`;
   D-cell P cross-selection
   `0.000`.
4. Calibration profile: **PASS**.
   Brier `0.012501`;
   ECE `0.050226`;
   false-P `0.000`.
5. Continuity: **FAIL (inexpressible frozen threshold)**.
   The analytic clause passed with
   `0` exceedances and
   maximum slice log BF
   `2.670557` against
   `3.801427`. The c67e853 freeze contains no empirical p99 rate
   bound to multiply by 1.75; no post-seal value was invented.
6. Independent constitution audit:
   **PASS**.
   Maximum error
   `5.68e-14`
   across ten seed-drawn worlds.

## Failure localization

The sole failing test is Test 5's second clause. The missing frozen definition
was checked in the contract, analysis plan, stage report, sign-table summary,
and manifest. This is a prospective contract omission, not a numerical
continuity exceedance. Per-test seed localization and all intervals are in
`summary.json`; all 200 world outcomes are retained in `per_seed.csv`.
