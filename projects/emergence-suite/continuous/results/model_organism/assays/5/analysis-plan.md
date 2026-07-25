# Assay 5 analysis plan — Co-regulation and access

Status: **frozen before Phase 0**. Evidentiary class: architecture/conformance with interaction.

- Design: complete 2×2, regulation present/absent × root-relevant witnessing evidence present/absent. Regulation and evidence streams are paired within world.
- Primary estimand and unit: difference-in-differences in root change: `(regulation+evidence − regulation-only) − (evidence-only − neither)`. One paired seeded 2×2 world is the unit.
- Aggregation: mean within-world interaction and interval. Regulation-only root change is tested for equivalence. Exact boundary equality passes equivalence; ties in the interaction are zero effects. No first-passage replacement is used.
- Effect size, threshold, and population: interaction ≥ `assay5_interaction_margin = 0.10`; absolute mean regulation-only change ≤ `assay5_equivalence_margin = 0.05`. Confirmation uses 80 frozen partner/field worlds.
- Analysis population and failures: all four cells required. A missing cell or non-finite root endpoint makes that world a primary failure; no available-case interaction.
- Outcomes: primary—interaction and regulation-only equivalence. Descriptive—field breadth, uptake, root endpoints, and crossing times.
- Hypothesis provenance: matched evidence uptake is **Original prediction** from Experiment 44b/global-field results (`results/context_split_redescription/report.md`, `results/global_precision_field/summary.json`); the 2×2 interaction and equivalence margin are **50 prospective**.
