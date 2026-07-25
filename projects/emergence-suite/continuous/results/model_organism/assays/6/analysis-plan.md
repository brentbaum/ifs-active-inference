# Assay 6 analysis plan — Redescription discovered

Status: **frozen before Phase 0**. Evidentiary class: model discrimination.

- Design: structured selectivity and held-out matched-complexity comparison, expanded to a five-family recovery matrix: global down-weight, cue-local, context-split, continuous drift, and change-point generators.
- Primary estimands and unit: diagonal recovery rate by generating family and context-split false-selection rate under the four non-split families. One generated dataset is the unit.
- Aggregation: family-stratified rates, macro-average diagonal rate, full 5×5 confusion matrix, and held-out margin. Tied model scores fail diagonal recovery and are assigned to `tie`; no crossings occur.
- Effect size, threshold, and population: macro diagonal ≥ `assay6_recovery_rate = 0.70`; context-split false-selection ≤ `assay6_false_split_rate = 0.10`; held-out split margin ≥ the inherited `context_heldout_margin = 0.05`. Confirmation uses 80 worlds per family (400 datasets).
- Analysis population and failures: all generated datasets. Missing scores, complexity mismatch, ties, or non-finite evidence are diagonal failures; missing family cells are not ignored.
- Outcomes: primary—confusion matrix, diagonal recovery, split false-selection. Descriptive—score margins and complexity audit.
- Hypothesis provenance: split selectivity and held-out margin are **Original prediction** from Experiment 44b (`results/context_split_redescription/44b/summary.json`); drift/change-point misspecification recovery is **50 prospective**.
