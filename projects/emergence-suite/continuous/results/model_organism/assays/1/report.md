# Assay 1 Stage A pilot

Status: **descriptive pilot only**. No criterion statistic was used for calibration, and no operationalization moved after the analysis-plan lock.

- Rows: `300`
- Seeds: all below `700000`; see `per_seed.csv`.
- Analysis plan: frozen before Phase 0 in `analysis-plan.md`.
- Stage A freeze status: confirmatory block had not run and evaluator seed escrow was unopened.

Numeric pilot descriptives are recorded in `summary.json`. They are not confirmatory verdicts.


## Confirmatory results (Stage B)

- Freeze commit: `274f8888f71ac590d7c15d6f9f59777ea919e182`
- Released seeds used: `700093:700093`
- Confirmatory worlds: `1`
- Overall assay verdict: **PASS**

| Frozen criterion | Provenance | Effect estimate | 95% interval | Decision rule | Verdict |
|---|---|---:|---|---|---|
| joint-boundary predicate agreement | Original prediction | 1.000000 | [0.866804, 1.000000] | exact agreement = 1.0 | **PASS** |
| no-control edge attenuation | 50 prospective | -3.600000 | [-3.600000, -3.600000] | edge precision < positive-low-control precision | **PASS** |

Secondary/descriptive: all 25 frozen grid points were enumerated and working avoidance was available at every point. No row-level numerical failure occurred.
