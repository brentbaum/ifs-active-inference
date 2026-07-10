# Sim 1 Magic Numbers — T4.6 Step A

Pilot provenance means seeds 1001–1010 only. No value below has seen a
confirmatory seed. The orchestrator must freeze this file with the code and
criteria before Step B execution.

## Pilot-tuned and now frozen

| Constant | Frozen value | Pilot provenance |
|---|---:|---|
| `learning_rate_arousal_gain` | 60.0 | Base 15x15 grid compared gains 26, 40, 60, 80. At behavior thresholds 0.15/0.25, 40 left only a one-cell speck; 60 produced a two-cell connected frozen component plus a connected revisable component; 80 did not improve connectivity and increased count mass further. |
| `slow_path_omega` | 1.00 | Chronic sweeps tested 0.70, 0.80, 0.90, 1.00, 1.10. Value 1.00 gave the highest below-acute pilot crossing rate without a spawn (7/10; tied with 1.10, but farther below the acute omega cutoff). Values 0.70–0.90 gave 4–5/10. |
| `slow_path_kappa` | 0.0 | Retained as the no-control chronic path. Kappa affects only action consequences, never challenge exposure. |
| `slow_path_trials` | 600 | Durations 800, 1000, 1200 were checked at omega 0.70, 0.90, 1.00 and did not improve crossing rates; 600 is the shortest tested registered duration. |
| `behavior_frozen_max_change` | 0.15 | Pilot behavior changes were inspected at 0.10, 0.12, 0.15, 0.18. With the 5/10 cell rule, 0.15 was the smallest tested cutoff yielding a connected component (2 cells) at gain 60; 0.10 and 0.12 yielded only isolated cells. This is explicitly outcome-selected on pilots. |
| `behavior_revisable_min_change` | 0.25 | Pilot threat-relevant behavior changes at gain 60 had lower quartile about 0.179 and median about 0.367. A 0.25 cutoff separates the low-change tail from clear >=25 percentage-point prediction/policy movement and leaves a 0.10 unclassified gap above the frozen cutoff. |
| `threat_prediction_threshold` | 0.40 | Compared 0.40, 0.45, 0.50. The untrained approach outcome prior is 1/3; 0.40 is the lowest tested cutoff that requires learned elevation above that prior and avoids excluding most controlled learned cells by definition. |
| `cell_classification_rate` | 0.50 | Compared 0.40, 0.50, 0.60. The majority rule retains a minimal two-cell frozen component; 0.60 erases it and 0.40 expands it to four cells. |
| `connected_region_min_cells` | 2 | Retained after pilot: rejects isolated one-cell specks while making no shape or location requirement. |

The pilot result for the chosen chronic schedule is 7/10 original-order and
7/10 shuffled-order crossings. That misses the frozen 0.80 success margins in
S1.3/A1.3; those margins were not relaxed.

## Fixed design values not tuned in T4.6

| Constant | Value | Basis |
|---|---:|---|
| `crp_concentration` | 0.34 | Existing CRP prior; A1.2 reruns 0.5x, 1x, 1.5x. |
| `crp_threshold_base` | 0.085 | Existing posterior-predictive cutoff; A1.2 challenges boundary sensitivity. |
| `crp_threshold_control_relief` | 0.0 | Legacy compatibility field; unused. |
| `formation_trials` | 72 | Existing formation budget for every grid cell. |
| `disconfirming_trials` | 24 | Fixed safe-probe evidence budget. |
| `post_formation_trials` | 18 | Final target-cause policy-sampling window. |
| `bundle_seed_count` | 8 | Maximum acute bundles before up to two chronic bundles. |
| `spawn_pressure_threshold` | 2.45 | Existing persistent-failure requirement for a CRP spawn. |
| `spawn_pressure_decay` | 0.72 | Existing recent-failure memory. |
| `learning_rate_base` | 0.16 | Nonzero ordinary Dirichlet write. |
| `cue_learning_weight` | 0.55 | Cue bank writes more slowly than affect/outcome banks. |
| `revision_learning_rate` | 2.0 | Fixed per-trial safe-probe write, identical for every condition. |
| `policy_softmax_temperature` | 1.0 | Converts EFE totals, already in common model units, into reported policy probabilities without another rescaling. |
| `arousal_pe_scale` | 5.2 | Existing map from precision-weighted surprise to [0,1] arousal. |
| `reflexivity_arousal_slope` | 0.88 | Existing Tier-A write-time readout. |
| `evidence_precision` | 1.0 | Delivered observation precision is fixed across omega and kappa; this removes omega's former precision coupling. |
| `attenuation_precision_scale` | 0.34 | Attenuation's expected-utility/information model only; it does not alter delivered challenge precision or cause writes. |
| `safe_preference` | 1.35 | Existing EFE preference; sensitivity uses aversive scale 0.85/1/1.15. |
| `aversive_preference` | -2.35 | Existing EFE preference. |
| `ambiguity_weight` | 0.10 | Existing EFE ambiguity term. |
| `epistemic_weight` | 0.28 | Existing information-gain term. |
| `attenuation_info_scale` | 0.18 | Existing expected information reduction for attenuation. |
| `attenuation_cost` | 0.80 | Existing attenuation opportunity cost. |
| `overt_action_cost` | 0.03 | Common approach/flee/appease motor cost. |
| `attenuation_extreme_omega` | 2.65 | S1.4 top-omega corner definition. |
| `attenuation_flat_kappa` | 0.16 | S1.4 near-zero-control corner definition. |
| `acute_region_omega_min` | 1.18 | Defines which behaviorally frozen rows count as acute for S1.3's measured PE comparison. |
| Omega grid | 0.20–3.00, 15 points | Full phase grid. |
| Kappa grid | 0.00–1.40, 15 points | Full phase grid. |

## Priors, environment, and bookkeeping constants

| Constant | Value | Basis |
|---|---:|---|
| Initial base `cue_counts` | `[14,10]` | Existing weak aversive-cue prior. |
| Initial base `affect_counts` | `[15,7]` | Existing mildly safe affect prior. |
| Initial base `outcome_counts` | `[[8,10,9,6]; [4,3,4,6]]` | Existing weak action-outcome priors. |
| Initial base `policy_counts` | `[3,5,4,1]` | Existing policy-use prior. |
| Spawned cue / affect / outcome / policy priors | `[1,2]` / `[1,1]` / all ones / all ones | Uncommitted new cause, weakly keyed to the aversive cue. |
| Challenge probability | `clamp(0.08 + 0.31*omega, 0.06, 0.97)` | Omega's only evidence coupling: exogenous challenge frequency. |
| Aversive/safe challenge action baselines | 0.90 / 0.08 | Post-challenge consequence probability before efficacy relief. They never update cause affect counts. |
| Overt action relief weights | approach 0.10, flee 1.40, appease 0.90 | Kappa changes action efficacy only. Attenuate relief is zero. |
| Control transform | `kappa/(kappa+0.45)` | Existing saturating efficacy map. |
| Evidence severity | 1.0 for each aversive challenge | Fixed and exactly yoked across kappa. |
| Action RNG offset | 1,000,003 | Separates action-consequence draws from the replayed evidence RNG. |
| Shuffle RNG offset | 2,000,003 | Separates A1.3 ordering from both evidence and action RNGs. |
| Revision target | aversive cue plus safe affect and safe approach consequence | The disconfirming probe updates the copied cause through observable sufficient statistics. |
