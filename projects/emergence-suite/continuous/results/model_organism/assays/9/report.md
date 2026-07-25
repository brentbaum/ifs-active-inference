# Assay 9 Stage A pilot

Status: **descriptive pilot only**. No criterion statistic was used for calibration, and no operationalization moved after the analysis-plan lock.

- Rows: `48`
- Seeds: all below `700000`; see `per_seed.csv`.
- Analysis plan: frozen before Phase 0 in `analysis-plan.md`.
- Stage A freeze status: confirmatory block had not run and evaluator seed escrow was unopened.

Numeric pilot descriptives are recorded in `summary.json`. They are not confirmatory verdicts.


## Confirmatory results (Stage B)

- Freeze commit: `274f8888f71ac590d7c15d6f9f59777ea919e182`
- Released seeds used: `708300:708379`
- Confirmatory worlds: `80`
- Software repair status: **AUTHORIZED; COMPLETE**
- Overall assay verdict: **FAIL**

| Frozen criterion | Provenance | Effect estimate | 95% interval | Decision rule | Verdict |
|---|---|---:|---|---|---|
| stakes-permission and transfer invariants | Original prediction | 1.000000 | [0.963358, 1.000000] | exact property agreement = 1.0 | **PASS** |
| joint partner-type and competence recovery | 50 prospective | 0.700000 | [0.639244, 0.754454] | macro learned-history recovery ≥ 0.7 | **PASS** |
| risk-model obsolescence crossover | Exploratory finding; first prospective test in 50-H | 0.516667 | [0.453680, 0.579128] | sign-match rate ≥ 0.8 | **FAIL** |

The 101-point property domain passed exactly and used no seeds. The learned-history world block was not rerun and retained SHA-256 `d7f478ac45f33c90fbb178fc5adf74db12af66a778732e1011cf34c9f6d336c7`. Joint recovery remained trustworthy `80/80`, neutral `9/80`, adverse `79/80`. The obsolescence-crossover **FAIL** stands without reinterpretation.
