# Assay 4 Stage A pilot

Status: **descriptive pilot only**. No criterion statistic was used for calibration, and no operationalization moved after the analysis-plan lock.

- Rows: `36`
- Seeds: all below `700000`; see `per_seed.csv`.
- Analysis plan: frozen before Phase 0 in `analysis-plan.md`.
- Stage A freeze status: confirmatory block had not run and evaluator seed escrow was unopened.

Numeric pilot descriptives are recorded in `summary.json`. They are not confirmatory verdicts.


## Confirmatory results (Stage B)

- Freeze commit: `274f8888f71ac590d7c15d6f9f59777ea919e182`
- Released seeds used: `703086:703165`
- Confirmatory worlds: `80`
- Overall assay verdict: **PASS**

| Frozen criterion | Provenance | Effect estimate | 95% interval | Decision rule | Verdict |
|---|---|---:|---|---|---|
| conditional untreated-cue transfer | Original prediction; 50 prospective primary operationalization | 0.344636 | [0.281471, 0.407801] | conditional mean ≥ 0.1 and rate ≥ 0.80 | **PASS** |
| reversed-graph control | 50 prospective | 0.289622 | [0.238901, 0.340343] | reversed mean transfer < witnessing mean transfer | **PASS** |

Secondary/descriptive: witnessing root revision occurred in `33/80` worlds (`0.4125`). Among those conditional worlds, `27/33` exceeded the transfer margin (rate `0.8182`, Wilson 95% interval `[0.6561, 0.9139]`). Identity-before-threat ordering occurred in `0.3375` of all worlds and retains its **Pilot-amended** provenance.
