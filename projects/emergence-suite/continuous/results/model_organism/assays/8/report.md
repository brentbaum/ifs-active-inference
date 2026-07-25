# Assay 8 Stage A pilot

Status: **descriptive pilot only**. No criterion statistic was used for calibration, and no operationalization moved after the analysis-plan lock.

- Rows: `24`
- Seeds: all below `700000`; see `per_seed.csv`.
- Analysis plan: frozen before Phase 0 in `analysis-plan.md`.
- Stage A freeze status: confirmatory block had not run and evaluator seed escrow was unopened.

Numeric pilot descriptives are recorded in `summary.json`. They are not confirmatory verdicts.


## Confirmatory results (Stage B)

- Freeze commit: `274f8888f71ac590d7c15d6f9f59777ea919e182`
- Released seeds used: `707287:707366`
- Confirmatory worlds: `80`
- Software repair status: **AUTHORIZED; COMPLETE**
- Overall assay verdict: **PASS**

| Frozen criterion | Provenance | Effect estimate | 95% interval | Decision rule | Verdict |
|---|---|---:|---|---|---|
| selection tracks learned expected cost | Original prediction; 50 prospective learned-history test | 0.825000 | [0.727423, 0.892795] | tracking rate ≥ 0.8 | **PASS** |
| registration on-minus-off contrast | Original prediction | 0.334404 | [0.334404, 0.334404] | mean paired change ≥ 0.1 | **PASS** |
| registration off and ablation static | Original prediction | 1.000000 | [0.954180, 1.000000] | off and distinct ablation within static tolerance | **PASS** |

Repair verification: the pre-existing on/off block reproduced byte-for-byte (`61953fe9c3cf987145da016a5a8f90ba8f6c93121f05abc54b07026b471c4690`), maximum absolute deviation `0.0`. The distinct ablation arm was static in every paired world.
