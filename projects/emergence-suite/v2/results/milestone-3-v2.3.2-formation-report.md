# Suite v2 — V2.3.2 formation re-foundation

Stage verdict: **PASS** for Gates 1–5.

The model uses static T/D/P comparison. The retired transition's stationary
persistent mass was `.80`; the replacement has exactly zero no-evidence
drift at 16, 64, 80, and 160 slices.

- Gate 1 normalization/decomposition/independent errors:
  `2.22e-16` /
  `8.88e-16` /
  `0`.
- Gate 2 accuracy/Brier/ECE: `0.9533` /
  `0.0228` /
  `0.0195`.
- Gate 3 matched-statistic maximum difference:
  `7.11e-15`.
- Gate 3 no-event maximum prior difference:
  `0`.
- Gate 4 all five targeted lesion effects are zero with positive survivors.
- Gate 5 preserves V2.0–V2.2.1 and the honest repaired V2.3.1r ledger.

The attribution-first V2.3.2 implementation remains shelved and unchanged.
The superseded sealed bundles were not opened or run.

## Evaluator full-suite verification episode

Evaluator verification of the first freeze candidate found two failures that
the initial report did not disclose:

- retired v2.3.1 recovery ECE `0.10579451215553712 > 0.10`;
- retired v2.3.1 schedule-generalization smoke surface R² `0.6756 > 0.05`
  (the committed full-block ledger value is `0.6173327730910273`).

The apparatus-first diagnosis found no kernel regression. The V2.0 retrofit
only extracted the unchanged nested-comparison model constructor. V2.3.1
computes both metrics before its cumulative `run_v20()` call. Exhaustive
pre-build/current comparison found zero movement across all 22 V2.0, 65
V2.1, and 97 V2.2.1 numeric metric leaves; the v2.3.1r rerun is also
numerically identical to its committed ledger.

The failures were stale assertions for properties explicitly rescinded by
the v2.3.1r errata. They are now ledger-pinning tests: they assert the exact
failing values and require historical Gates 2 and 3 to remain false. This
retains the failure record and prevents accidental resurrection without
weakening any live threshold.
