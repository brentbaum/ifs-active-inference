# Assay 2 Stage A pilot

Status: **descriptive pilot only**. No criterion statistic was used for calibration, and no operationalization moved after the analysis-plan lock.

- Rows: `36`
- Seeds: all below `700000`; see `per_seed.csv`.
- Analysis plan: frozen before Phase 0 in `analysis-plan.md`.
- Stage A freeze status: confirmatory block had not run and evaluator seed escrow was unopened.

Numeric pilot descriptives are recorded in `summary.json`. They are not confirmatory verdicts.


## Confirmatory results (Stage B)

- Freeze commit: `274f8888f71ac590d7c15d6f9f59777ea919e182`
- Released seeds used: `701198:701277`
- Confirmatory worlds: `80`
- Overall assay verdict: **PASS**

| Frozen criterion | Provenance | Effect estimate | 95% interval | Decision rule | Verdict |
|---|---|---:|---|---|---|
| paired normalized exposure effect | Original prediction; 50 prospective margin | 0.177604 | [0.041667, 0.292708] | mean absolute effect ≥ 0.15 | **PASS** |
| paired root-revision effect | Original prediction; 50 prospective margin | 0.553461 | [0.027816, 0.884644] | mean absolute effect ≥ 0.15 | **PASS** |
| controllability dose response | Original prediction | 0.672092 | [0.603801, 0.740384] | mean within-world slope > 0 | **PASS** |

Secondary/descriptive: the working-avoidance mediator mean was `0.5000` across 80 paired worlds. Non-crossing worlds retained endpoint changes; no row-level numerical failure occurred.
