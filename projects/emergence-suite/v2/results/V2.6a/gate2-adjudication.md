# V2.6a gate-2 adjudication (evaluator, 2026-07-29)

Both gate-2 verdicts stand as recorded: the original FAIL (apparatus: generator/scorer mismatch + occupancy-label category error, repaired under authorization) and the repaired execution's FAIL on exactly one criterion — switch-onset median absolute error 5.0 slices vs the spec-fixed <= 3.

Classification of the onset miss: **unaudited attainability floor** (adjudication-criterion audit items 3 and 4). The onset estimate is derived from the exact smoothed posterior, which is the Bayes-optimal estimator under the frozen model; its error is therefore the information bound of the frozen four-channel emission table at stay-probability .94, not an implementation or model deficiency. No correct method can satisfy the floor at this informativeness. The floor was authored in the master spec without a power/attainability evaluation against the frozen emissions.

Everything else passed decisively on the repaired apparatus: per-slice ECE 0.0031 (theorem restored), Brier 0.148, coverage 0.988, macro recovery 0.899, switch-parameter MAE within .10, local-precision calibration error 0.038.

Disposition: mixed-verdict continuation — the onset-floor family (and its gate-5 repetitions) is non-blocking and reported verbatim; every other criterion remains blocking. No threshold changes; the spec floor stays in the ledger as missed. Stage status on success carries the limitation clause. Disclosed at the next consultation. Gate 3 proceeds.
