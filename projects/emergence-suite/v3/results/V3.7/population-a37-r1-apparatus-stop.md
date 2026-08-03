# V3.7 Population A37-R1 apparatus stop

Verdict: **FAIL_APPARATUS_THEOREM_PREMISE**. Scientific interpretation is withheld.

All 2,000 replacement worlds were consumed ascending and gap-free. Their trace ledger was persisted before aggregation and has SHA-256 `1e5fed9a3770969e33611427271444129d40974f2ed9de932feb471a76dc1e23`.

The blocking active-count calibration checks failed. Top-label ECE was `0.0924591` and macro classwise ECE was `0.0870070`; both limits are `0.05`. All five target ECEs passed (`0.00347`–`0.00724`), equivalence-class top-label ECE passed at `0.01517`, 95% class-set coverage passed at `0.957`, and the largest edge ECE passed at `0.03600`.

## Apparatus-first localization

`generate_v3_native_world` samples `modes_input[k]` only when `k < structure.active_modes` and forces every higher slot to zero. The observed intervention/query schedule therefore reveals information about the sampled truth structure. The scorer conditions on that schedule and does not score its truth-dependent probability. This contradicts round 20's candidate-common-schedule requirement, so these worlds are not draws from the scorer's complete native prior predictive and calibration-by-theorem does not apply.

No repair is applied without adjudication. Population C37, T37, and registered-prediction scoring remain unopened.
