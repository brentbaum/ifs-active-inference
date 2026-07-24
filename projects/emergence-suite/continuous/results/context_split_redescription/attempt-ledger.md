# Attempt ledger

## 2026-07-24 — preliminary pilot invalidated before confirmation

- Seeds: `174401:174410`.
- No confirmation seed was opened.
- The preliminary implementation produced structured split selection `10/10`,
  no-structure split selection `2/10`, saturated all four root arms, and
  produced no do-over shortening.
- The run was invalidated for contract-level reasons, not because criteria
  failed: the selectivity worlds did not preserve the behavior marginals; the
  split model lacked an explicit shared-root coordinate; and the global
  comparator did not allocate a parameter to learned global precision.
- Repairs preserve the context-effect marginal by shuffling its association
  with the inferred marker, allocate a shared root-signal coefficient in the
  split model, and allocate one of the global model's ten Gaussian coordinates
  to learned global precision. The root and do-over generators and thresholds
  were deliberately left unchanged despite their negative preliminary results.
- The corrected ten-world pilot below is the only run used for freeze.

## 2026-07-24 — first confirmatory block invalidated by held-out scale audit

- Seeds: `174501:174520`; disjoint from the pilot.
- Recorded outcome before invalidation: criterion 1 passed (`20/20` structured,
  `0/20` null); held-out margin was `-0.3264`; criteria 3 and 4 failed.
- The post-run audit found that training design columns were normalized but
  held-out columns were evaluated at raw scale. The held-out log-predictive
  comparison was therefore not in the fitted parameter coordinate system.
- The block is invalidated in full rather than selectively rescuing criterion
  2. No world generator, arm precision, do-over constant, or criterion changed.
- The corrected pilot is rerun and frozen, and the replacement confirmation
  uses never-opened seeds `174601:174620`.

## Experiment 44b — calibrated revision instrument

### Wiring audit

- The 44a field profiles did enter the identity likelihood ratios, but all
  arms received 18 repeats of the same strongly root-positive bundle.
  Regulation-only still accumulated mean bundle/contact log odds of
  `31.094 + 9.294`; the posterior ceiling was therefore inevitable.
- The 44a reversed control changed only the contact sign. It retained mean
  positive bundle log odds `37.300`, overwhelming mean contact log odds
  `-3.873`. It was not a full reversed-graph ablation.
- The complete audit is retained in `44b/wiring-audit.md` and
  `44b/wiring-audit-44a.csv`.

### Pilot calibration attempts — seeds `174701:174710`

1. `44b-cal-01`: 18 sessions, root amplitude `0.55`, observation SD `0.90`.
   Failed the preregistered guard. Fixed-context root was `0.927` and
   witnessing remained `0.999999999`.
2. `44b-cal-02`: 14 sessions, root amplitude `0.35`, observation SD `1.00`.
   Passed the first time: witnessing `0.812`, open `0.777`, regulation
   `0.153`, narrowed `0.389`, fixed-context `0.270`, reversed graph `0.060`.
   Baseline model reduction was measurable in `10/10`.

The first runner invocation aborted after computing the candidates because of
a Julia top-level soft-scope bookkeeping error. It opened no confirmation
seed and wrote no freeze. The runner was corrected, replayed the same
deterministic pilot candidates, logged both attempts, and froze
`44b-cal-02`. No scientific constant changed because of that runner repair.
During diagnosis, a read-only command also evaluated preregistered fallback
`44b-cal-03` on the same pilot seeds after calibration 02 had passed:
witnessing `0.623`, open `0.534`, regulation `0.105`, narrowed `0.224`,
fixed `0.160`, reversed `0.060`; it failed the witnessing lower-band guard.
It is retained as an ineligible diagnostic row in `calibration-ledger.csv`
and played no role in selection or freeze.

### Freeze and confirmation

- All 44a criterion thresholds were retained.
- The saturation guard, calibration, and seed blocks were frozen before
  confirmation.
- Confirmation used never-opened seeds `174801:174820`.
- Confirmatory criteria: 1 PASS, 2 PASS, 3 FAIL, 4 PASS. Overall
  `failed_or_mixed`.

## Exploratory narrowing addendum — seeds `174901:174910`

- Label: post-freeze, non-confirmatory.
- Five matched doses reduced the three off-channel narrowed-contact
  precisions from `0.04` to zero while preserving part precision `0.72`.
- Mean root posterior declined monotonically from `0.442` to `0.397`.
- The regulation floor was `0.182`; maximal narrowing remained `0.214`
  above it, so the sweep supports persistent part-channel root leakage rather
  than convergence to regulation.
- Frozen criteria, status, model source, runner, per-seed block, and freeze
  were not changed. The 44b summary received only the requested exploratory
  addendum object.
