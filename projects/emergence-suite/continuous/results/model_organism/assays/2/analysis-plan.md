# Assay 2 analysis plan — Frozen persistence

Status: **frozen before Phase 0**. Evidentiary class: causal/mechanism contrast.

- Design: paired closed action–evidence loop versus matched open-loop replay. Corrective evidence uses the ordinary update path; controllability doses are zero, half, and full. Working avoidance is a measured mediator.
- Primary estimands and unit: within-world closed-minus-open exposure and root-revision effects at full dose, plus the within-world slope of revision over controllability dose. One seeded world is the unit.
- Aggregation: mean paired differences and percentile interval over worlds; dose slope from the three within-world points, then averaged. Exact equality is a zero effect. A root that never crosses is retained with its endpoint change; first-passage is not substituted.
- Effect size, threshold, and population: mean absolute paired exposure and revision effects must each be at least `assay2_effect_margin = 0.15` after normalization; mean dose slope must be positive. Confirmation population is the frozen paired world generator; this continuous paired design uses 80 worlds.
- Analysis population and failures: intention-to-simulate, all generated worlds. Missing events remain non-crossings with endpoint data; missing endpoints or non-finite values count against the criterion.
- Outcomes: primary—paired exposure, paired revision, dose response. Descriptive—avoidance mediation effect size and crossing times.
- Hypothesis provenance: **Original prediction**, inherited from the frozen persistence source result cited in the Experiment 50 spec; the explicit endpoint handling and effect margin are **50 prospective**.
