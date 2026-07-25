# Assay 5 Stage A pilot

Status: **descriptive pilot only**. No criterion statistic was used for calibration, and no operationalization moved after the analysis-plan lock.

- Rows: `48`
- Seeds: all below `700000`; see `per_seed.csv`.
- Analysis plan: frozen before Phase 0 in `analysis-plan.md`.
- Stage A freeze status: confirmatory block had not run and evaluator seed escrow was unopened.

Numeric pilot descriptives are recorded in `summary.json`. They are not confirmatory verdicts.


## Confirmatory results (Stage B)

- Freeze commit: `274f8888f71ac590d7c15d6f9f59777ea919e182`
- Released seeds used: `704172:704251`
- Confirmatory worlds: `80`
- Overall assay verdict: **PASS**

| Frozen criterion | Provenance | Effect estimate | 95% interval | Decision rule | Verdict |
|---|---|---:|---|---|---|
| regulation × evidence interaction | Original prediction; 50 prospective interaction | 0.551300 | [0.482194, 0.620406] | difference-in-differences ≥ 0.1 | **PASS** |
| regulation-only equivalence | Original prediction; 50 prospective margin | 0.000000 | [0.000000, 0.000000] | \|mean root change\| ≤ 0.05 | **PASS** |

Secondary/descriptive: all four cells were present in each of 80 paired 2×2 worlds. No row-level numerical failure occurred.
