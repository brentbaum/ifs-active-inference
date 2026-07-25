# Assay 4 analysis plan — Identity-first revision and transfer

Status: **frozen before Phase 0**. Evidentiary class: model discrimination and transfer.

- Design: shared identity root with multiple cue-bound meanings; paired witnessing, matched exposure, and reversed-graph arms.
- Primary estimand and unit: untreated-cue transfer in witnessing minus matched exposure, conditional on root revision in the witnessing arm. One paired seeded world is the unit.
- Aggregation: mean paired conditional effect and the rate exceeding `assay4_transfer_margin = 0.10`; report a binomial interval. Identity-before-threat ordering is secondary. Ties in event time fail the ordering outcome. Non-crossing root worlds are excluded only from the explicitly conditional primary denominator and are reported separately.
- Effect size, threshold, and population: mean conditional transfer ≥ `0.10`, success rate ≥ `0.80`; reversed-graph mean transfer must remain below matched witnessing. Confirmation uses 80 worlds from the frozen shared-root/cue generator.
- Analysis population and failures: all successfully generated paired worlds; non-finite endpoints count as failures. A missing crossing is retained as a non-revision and cannot enter the conditional effect.
- Outcomes: primary—conditional untreated-cue transfer. Secondary—identity-before-threat ordering. Descriptive—root revision rates and arm endpoint traces.
- Hypothesis provenance: generalization gradient is **Original prediction** and the two-way ordering was **Pilot-amended** in Experiment 44b (`results/context_split_redescription/report.md`); making transfer primary and adding the reversed-graph causal control are **50 prospective**.
