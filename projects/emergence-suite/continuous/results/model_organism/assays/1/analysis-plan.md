# Assay 1 analysis plan — Freeze formation

Status: **frozen before Phase 0**. Evidentiary class: architecture/conformance.

- Design: one vulnerable bundle, no protector; overwhelm × control grid. The authored one-step write must occur at the joint high-overwhelm/low-control boundary, not in matched controls, with attenuation at the no-control edge. This is a property test plus grid, not a derivation.
- Primary estimand and unit: proportion of frozen grid points whose write indicator exactly equals the prespecified joint-boundary predicate; one grid point is the unit.
- Aggregation: pool the frozen property domain; also report write precision by grid cell. Ties at either inclusive boundary count as boundary cases. No crossing is expected or imputed.
- Effect size, threshold, and population: exact agreement must be `1.0`; no-control precision must be below positive-low-control precision. Population is the 5×5 frozen grid for each of 12 pilot worlds; confirmation repeats the analytic property domain rather than treating seeds as theorem replication.
- Analysis population and failures: all finite grid evaluations. A missing cell, numerical failure, or non-finite precision is a primary failure; no row is dropped.
- Outcomes: primary—predicate agreement and edge attenuation. Descriptive—precision surface and working-avoidance availability.
- Hypothesis provenance: **Original prediction**, inherited as a conformance check from `results/formation_substrate_triad/report.md` and the formation construction; Experiment 50's class/edge wording is **50 prospective**.
