# Assay 6 Stage A pilot

Status: **descriptive pilot only**. No criterion statistic was used for calibration, and no operationalization moved after the analysis-plan lock.

- Rows: `60`
- Seeds: all below `700000`; see `per_seed.csv`.
- Analysis plan: frozen before Phase 0 in `analysis-plan.md`.
- Stage A freeze status: confirmatory block had not run and evaluator seed escrow was unopened.

Numeric pilot descriptives are recorded in `summary.json`. They are not confirmatory verdicts.


## Confirmatory results (Stage B)

- Freeze commit: `274f8888f71ac590d7c15d6f9f59777ea919e182`
- Released seeds used: `705013:705092`
- Confirmatory worlds: `80`
- Overall assay verdict: **PASS**

| Frozen criterion | Provenance | Effect estimate | 95% interval | Decision rule | Verdict |
|---|---|---:|---|---|---|
| five-family diagonal recovery | Original prediction (split family); 50 prospective drift/change-point recovery | 0.982500 | [0.964322, 0.991498] | macro diagonal ≥ 0.7 | **PASS** |
| context-split misspecification guard | 50 prospective | 0.000000 | [0.000000, 0.011863] | false split rate ≤ 0.1 | **PASS** |
| context-split held-out margin | Original prediction | 1.749823 | [1.668464, 1.831182] | mean margin ≥ 0.05 | **PASS** |

Secondary/descriptive: 80 released seed blocks generated 400 datasets—80 per family. The complexity audit passed for every dataset. The diagonal interval shown is the pooled Wilson interval; equal family sizes make its point estimate equal to the macro-average rate.
