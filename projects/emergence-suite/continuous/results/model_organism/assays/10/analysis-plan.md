# Assay 10 analysis plan — Dyad-gate descent

Status: **frozen before Phase 0**. Evidentiary class: causal/mechanism contrast.

- Design: one latent partner disposition (`trustworthy`, `neutral`, `adverse`) generates both regulation signals and trust outcomes. Full disposition × scaffold (`coupled`, `decoupled`) factorial plus positive-evidence-without-scaffolding. Neutral/no-scaffold deadlock is retained as the historical anchor.
- Primary estimand and unit: disposition-by-scaffold interaction in descent, focused on `(trustworthy coupled − trustworthy decoupled) − (adverse coupled − adverse decoupled)`. One paired seeded factorial world is the unit.
- Aggregation: mean interaction, cell-specific descent rates and intervals. Permission-before-root-revision is an audit only. Event-time ties fail that audit. Non-crossings remain failures at the fixed horizon.
- Effect size, threshold, and population: interaction ≥ `assay10_interaction_margin = 0.25`; trustworthy-coupled descent ≥ `assay10_success_rate = 0.80`; trustworthy-decoupled and adverse-coupled descent ≤ `assay10_control_rate = 0.20`. Confirmation uses 80 paired worlds.
- Analysis population and failures: every factorial cell plus positive-evidence-only cell is required per world. Missing cells, numerical failures, or non-finite endpoints count against the relevant rate and interaction.
- Outcomes: primary—factorial interaction and cell descent rates. Audit—permission precedes root revision. Descriptive—positive-evidence-only effect, registered suppressions, field trajectories, and neutral deadlock.
- Hypothesis provenance: coupled/no-dyad descent and historical deadlock are **Original prediction** from Experiment 49 (`results/dyad_gate_descent/report.md`); the shared latent-partner factorial, adverse-partner guard, positive-evidence-only cell, and interaction headline are **50 prospective**.
