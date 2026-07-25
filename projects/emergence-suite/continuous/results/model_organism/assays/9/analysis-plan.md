# Assay 9 analysis plan — Protector trust battery

Status: **frozen before Phase 0**. Evidentiary class: analytic invariants plus learned-history simulation.

- Design: prove/property-test stakes–permission separation and transfer locality; separately replay ambiguous, unreliable, and conflicting histories for trustworthy, neutral, and adverse latent partners before permission. Use risk-model counterfactuals only.
- Primary estimands and unit: exact invariant agreement; joint partner-type/competence recovery rate; competence-dependent obsolescence-shift sign accuracy. One property-domain point or one seeded partner history is the unit.
- Aggregation: exact property results; partner-stratified and macro recovery rates; sign-match rate with interval. Posterior classification ties are neutral and incorrect for trustworthy/adverse recovery. No crossings occur.
- Effect size, threshold, and population: invariants `1.0`; learned recovery ≥ `assay9_recovery_rate = 0.70`; obsolescence sign match ≥ `assay9_crossover_rate = 0.80`. Analytic domain has 101 points across stakes and locality; confirmation uses 80 histories per partner type.
- Analysis population and failures: all property points and histories. Missing history events, direct posterior values, non-finite decisions, or unresolved competence count as failures.
- Outcomes: primary—invariants, learned recovery, obsolescence sign. Descriptive—posterior calibration and permission distributions.
- Hypothesis provenance: stakes separation and transfer locality are **Original prediction** from Experiment 47 (`results/protector_trust/report.md`); the risk-model obsolescence crossover is an **Exploratory finding** from `results/protector_trust/exploratory-summary.json` receiving its first prospective test here; noisy three-type recovery is **50 prospective**.
