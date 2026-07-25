# Assay 7 Stage A pilot

Status: **descriptive pilot only**. No criterion statistic was used for calibration, and no operationalization moved after the analysis-plan lock.

- Rows: `1236`
- Seeds: all below `700000`; see `per_seed.csv`.
- Analysis plan: frozen before Phase 0 in `analysis-plan.md`.
- Stage A freeze status: confirmatory block had not run and evaluator seed escrow was unopened.

Numeric pilot descriptives are recorded in `summary.json`. They are not confirmatory verdicts.


## Confirmatory results (Stage B)

- Freeze commit: `274f8888f71ac590d7c15d6f9f59777ea919e182`
- Released seeds used: `706005:706084`
- Confirmatory worlds: `80`
- Overall assay verdict: **PASS**

| Frozen criterion | Provenance | Effect estimate | 95% interval | Decision rule | Verdict |
|---|---|---:|---|---|---|
| imaginal-evidence analytic crossover | 50 prospective | 1.000000 | [0.963358, 1.000000] | exact property agreement = 1.0 | **PASS** |
| post-revision do-over advantage | Original prediction; 50 prospective suggestion-only comparator | 0.145833 | [0.117180, 0.174487] | paired advantage ≥ 0.1 | **PASS** |
| premature reversal rate | Original prediction | 0.937500 | [0.861897, 0.973011] | reversal rate ≥ 0.50 | **PASS** |

Secondary/descriptive: the analytic domain contained 101 unique posterior points; the stochastic comparison used 80 paired worlds. Non-crossings remained non-ready rather than being relabeled.
