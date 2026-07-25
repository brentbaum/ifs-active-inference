# Experiment 50-L apparatus errata

## D-001 — assay-1 unused-secondary empty reduction

**Apparatus first:** the preregistered freeze-to-ordinary-learning lesion emits no high-precision episodic writes. The reused Stage B assay-1 analyzer computes an unused secondary mean over written cases after computing the preregistered S1 property-agreement metric. That empty reduction raised before S1 could be returned.

**Repair:** the Stage D signature adapter now computes S1 directly from the same frozen `property_holds` field and exact-agreement rule, without invoking the unrelated secondary attenuation calculation. No lesion semantics, genome value, threshold, prediction, seed, or other signature changed. The stopped partial execution produced no Stage D result files. The same released block is rerun.

## D-002 — S7 equality lost to floating-point representation

**Apparatus first:** the frozen S7 rule is post-revision advantage `≥ 0.10`, and the Stage D preregistration explicitly says equality passes. In the 20-world neighborhood cohort the exact count-derived advantage is one tenth, represented in binary floating point as `0.09999999999999998`; the reused strict comparison marked it below threshold.

**Repair:** the Stage D S7 adapter applies the already-frozen `static_tolerance` to this comparison only. Metrics and intervals are unchanged; `0.09999999999999998` is classified as the preregistered equality case. The same draws and worlds are rerun. This correction changes S7 survival classifications but does not change any genome, sample, threshold, or the already-observed central neighborhood headline.

## D-003 — completion-critique harness corrections

An independent completion critique identified six validity gaps before final acceptance:

- L1/S6 had disabled context-split classification by rewriting an intact classifier’s row. It now generates the observations normally and evaluates them through a lesion-time classifier whose candidate set excludes `context_split`.
- `rng_history_offset` cannot be perturbed while preserving the preregistered paired histories. It remains in the published sensitivity matrix but is marked paired-noncausal and unresolved, with identical low/reference/high histories. It does not contribute to the architecture classification.
- Perturbed in-memory genomes previously carried the reference SHA string. Harness genomes now receive a deterministic `HARNESS-...` fingerprint that cannot pass the frozen identity guard; the true reference is verified immediately before and after each harness block.
- S4 is compound. The sensitivity matrix now publishes its low/reference/high qualifying rates as well as conditional means, and materiality conservatively uses the component with the larger absolute fractional change. Lesion reporting includes the rate’s Wilson interval.
- L7 previously substituted the outcome forecast only at readout. The lesion now learns a single outcome forecast, uses that scalar for both partner/competence recovery, and uses a lesion-only single-forecast permission route in assay 10.
- The scalar classifier’s apparent `0.25/0.75` cutoffs were an unstated implementation of nearest frozen regime locations. The code now performs that nearest-location calculation directly; the midpoint tie resolves by the frozen regime order.

These are apparatus corrections to implement the preregistered lesions and compound metric faithfully. Predictions, thresholds, samples, magnitudes, and the on-disk reference genome remain unchanged. All Stage D blocks are rerun on the same released seeds.
