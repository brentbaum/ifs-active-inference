# Assay 3 analysis plan — Dominance–depth dissociation

Status: **frozen before Phase 0**. Evidentiary class: conformance plus model comparison.

- Design: one bundle in four input-induced regimes spanning low/high dominance × low/high depth. A capacity-matched one-dimensional arousal/global-confidence scalar is scored on held-out behavior against the two-coordinate field model.
- Primary estimands and unit: four-class regime accuracy and mean held-out squared-loss difference (`loss_1d - loss_2d`). One seeded regime instance is the accuracy unit; one seeded four-regime block is the comparison unit.
- Aggregation: regime-balanced mean accuracy; paired mean loss difference over held-out blocks. Classification ties count incorrect. No crossings occur.
- Effect size, threshold, and population: accuracy ≥ `0.90`; two-dimensional loss improvement ≥ `assay3_comparator_margin = 0.02`. Property domain includes all four cells; 80 paired world blocks are planned for the stochastic held-out comparison.
- Analysis population and failures: all four cells for every world. Any missing cell invalidates that world and counts as an incorrect block; non-finite loss is worst-case failure.
- Outcomes: primary—regime accuracy and held-out comparator margin. Descriptive—dominance/depth coordinate distributions and scalar collisions.
- Hypothesis provenance: four-regime realization is **Original prediction** from `results/global_precision_field/summary.json`; the one-dimensional held-out comparison is **50 prospective**.
