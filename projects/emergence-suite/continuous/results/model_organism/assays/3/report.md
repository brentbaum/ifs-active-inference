# Assay 3 Stage A pilot

Status: **descriptive pilot only**. No criterion statistic was used for calibration, and no operationalization moved after the analysis-plan lock.

- Rows: `48`
- Seeds: all below `700000`; see `per_seed.csv`.
- Analysis plan: frozen before Phase 0 in `analysis-plan.md`.
- Stage A freeze status: confirmatory block had not run and evaluator seed escrow was unopened.

Numeric pilot descriptives are recorded in `summary.json`. They are not confirmatory verdicts.


## Confirmatory results (Stage B)

- Freeze commit: `274f8888f71ac590d7c15d6f9f59777ea919e182`
- Released seeds used: `702412:702491`
- Confirmatory worlds: `80`
- Overall assay verdict: **PASS**

| Frozen criterion | Provenance | Effect estimate | 95% interval | Decision rule | Verdict |
|---|---|---:|---|---|---|
| four-regime realization | Original prediction | 1.000000 | [0.988137, 1.000000] | balanced accuracy ≥ 0.9 | **PASS** |
| two-dimensional held-out advantage | 50 prospective | 0.249796 | [0.249769, 0.249823] | loss_1d - loss_2d ≥ 0.02 | **PASS** |

Secondary/descriptive: 320 regime instances formed 80 complete, balanced four-regime world blocks. No row-level numerical failure occurred.
