# Assay 10 Stage A pilot

Status: **descriptive pilot only**. No criterion statistic was used for calibration, and no operationalization moved after the analysis-plan lock.

- Rows: `84`
- Seeds: all below `700000`; see `per_seed.csv`.
- Analysis plan: frozen before Phase 0 in `analysis-plan.md`.
- Stage A freeze status: confirmatory block had not run and evaluator seed escrow was unopened.

Numeric pilot descriptives are recorded in `summary.json`. They are not confirmatory verdicts.


## Confirmatory results (Stage B)

- Freeze commit: `274f8888f71ac590d7c15d6f9f59777ea919e182`
- Released seeds used: `709439:709518`
- Confirmatory worlds: `80`
- Overall assay verdict: **PASS**

| Frozen criterion | Provenance | Effect estimate | 95% interval | Decision rule | Verdict |
|---|---|---:|---|---|---|
| disposition × scaffold interaction | 50 prospective | 1.000000 | [1.000000, 1.000000] | mean interaction ≥ 0.25 | **PASS** |
| trustworthy-coupled descent | 50 prospective | 1.000000 | [0.954180, 1.000000] | rate ≥ 0.8 | **PASS** |
| decoupled/adverse safeguards | 50 prospective | 0.000000 | [0.000000, 0.045820] | trustworthy-decoupled and adverse-coupled ≤ 0.2 | **PASS** |

Secondary/descriptive: trustworthy-coupled descent was `1.0000`, neutral-coupled `0.4500`, and every decoupled/adverse safeguard cell was `0.0000`. Positive evidence without scaffolding produced no descent; the neutral-decoupled historical anchor remained deadlocked; permission preceded root revision in every descent world.
