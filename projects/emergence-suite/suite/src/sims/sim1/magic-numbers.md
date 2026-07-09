# Sim 1 Magic Numbers

Every hand-set constant in `Sim1.jl` and `configs/sim1.yaml` is listed here.

| Constant | Value | Derivation / sweep / IOU |
|---|---:|---|
| `assimilation_capacity` | 1.0 | Derivation: defines omega's unit as precision-weighted PE relative to ordinary assimilation capacity. |
| `crp_concentration` | 0.34 | Sweep: A1.2 reruns the boundary at 0.5x and 1.5x concentration. |
| `crp_threshold_base` | 0.085 | IOU: posterior-predictive cutoff for CRP pressure; A1.2 checks knife-edge dependence. |
| `crp_threshold_control_relief` | 0.0 | Legacy config field retained for compatibility; no longer used in scoring or spawn thresholds. |
| `formation_trials` | 72 | IOU: enough trials for policy learning, CRP pressure, and post-formation measurement while keeping the full 15x15x20 battery tractable. |
| `disconfirming_trials` | 24 | Derivation: ticket minimum for the ordinary safe-evidence revision probe. |
| `post_formation_trials` | 18 | IOU: final target-cause window for measured epistemic sampling rate. |
| `slow_path_trials` | 600 | Derivation: ticket requires a single chronic run of at least 500 trials; 600 leaves room for crossing plus post-cross persistence. |
| `slow_path_omega` | 0.90 | Derivation: below the acute frozen region's per-trial PE after precision weighting, but high enough for chronic aversive accumulation. |
| `slow_path_kappa` | 0.0 | Derivation: uncontrollable chronic condition for the slow-kinetics route; crossing occurs by count accrual without a spawn. |
| `bundle_seed_count` | 8 | IOU: acute frozen bundles exported before adding up to 2 slow-route bundles, enough for T1.3 without bloating artifacts. |
| `frozen_precision_threshold` | 260.0 | IOU: structural precision cutoff separating hardened banks from ordinary learned causes; paired with measured revision <10%. |
| `spawn_pressure_threshold` | 2.45 | IOU: prevents single unlucky prediction errors from spawning while allowing persistent posterior-predictive failure. |
| `spawn_pressure_decay` | 0.72 | IOU: CRP pressure memory over recent failures; A1.2 indirectly checks sensitivity through boundary smoothness. |
| `learning_rate_base` | 0.16 | Derivation: nonzero ordinary Dirichlet learning at low arousal. |
| `learning_rate_arousal_gain` | 26.0 | IOU: maps high precision-weighted PE into high structural write, enabling acute freezing by learned counts. |
| `cue_learning_weight` | 0.55 | IOU: cue banks learn more slowly than affect banks so the revision probe targets affective likelihood rather than cue identity. |
| `revision_learning_rate` | 2.0 | Derivation: ordinary safe evidence has fixed moderate learning strength across all probes; revision is measured, not formulaic. |
| `revision_kl_scale` | 0.025 | IOU: converts measured KL divergence between pre/post affect-bank posteriors into a 0-100 revision percentage for the preregistered thresholds. |
| `aversive_cause_threshold` | 0.42 | IOU: frozen/revisable labels only apply when the measured target cause predicts aversive outcomes above the controlled-cell range; chronic slow-path seeds sit just above this value. |
| `arousal_pe_scale` | 5.2 | IOU: maps realized precision-weighted surprise into the 0-1 arousal scale. |
| `reflexivity_arousal_slope` | 0.88 | Derivation: Tier A reflexivity is the logged arousal-linked input; Sim 6 later makes this inferred. |
| `observation_precision_base` | 0.42 | IOU: nonzero precision for low-omega trials. |
| `observation_precision_gain` | 1.05 | Derivation: omega governs precision-weighted prediction error through observation precision. |
| `attenuation_precision_scale` | 0.34 | Derivation: covert attenuation lowers effective likelihood precision and information gain without changing world outcome probabilities. |
| `safe_preference` | 1.35 | Sensitivity: attenuation-localization sweep reruns at aversive-preference scale 0.85, 1.0, 1.15 around the chosen preference contrast. |
| `aversive_preference` | -2.35 | Sensitivity: same 3-point preference sweep reported in `summary.sensitivity.attenuation_preference_scale`. |
| `ambiguity_weight` | 0.10 | IOU: small expected-ambiguity penalty in the EFE decomposition. |
| `epistemic_weight` | 0.28 | IOU: gives overt policies a sampling opportunity cost relative to attenuation. |
| `attenuation_info_scale` | 0.18 | Derivation: attenuation reduces expected information gain. |
| `attenuation_cost` | 0.80 | Sensitivity: chosen to make attenuation pay a real opportunity cost; 3-point preference sweep reports whether localization survives. |
| `overt_action_cost` | 0.03 | IOU: small motor cost common to approach, flee, and appease. |
| `attenuation_extreme_omega` | 2.65 | Derivation: readout definition of the top-grid omega corner for S1.4. |
| `attenuation_flat_kappa` | 0.16 | Derivation: readout definition of kappa near zero on the 0.0-1.4 grid for S1.4. |
| `acute_region_omega_min` | 1.18 | Legacy fallback only if no acute frozen rows exist; actual slow-path criterion uses measured acute frozen PE when available. |
| Initial base `cue_counts` | `[14, 10]` | IOU: weak prior that aversive cues can occur in the existing cause. |
| Initial base `affect_counts` | `[15, 7]` | IOU: existing cause mildly expects safe outcomes but can assimilate ordinary aversive evidence. |
| Initial base `outcome_counts` | `[[8,10,9,6]; [4,3,4,6]]` | IOU: weak prior that flee/appease may help; failed control must be learned from outcomes. |
| Spawned cause cue prior | `[1, 2]` | Derivation: a new cause is proposed for the currently aversive cue. |
| Spawned cause affect prior | `[1, 1]` | Derivation: uncommitted affect bank before the first arousal-scaled write. |
| Spawned cause outcome prior | all ones | Derivation: uncommitted policy-specific outcome banks before evidence. |
| Environment base aversive probability | `clamp(0.08 + 0.31*omega, 0.06, 0.97)` | Derivation: omega governs the aversive contingency delivered by the world. |
| Environment action relief weights | approach 0.10, flee 1.40, appease 0.90, attenuate 0.0 | Derivation: kappa controls overt action efficacy; attenuate changes precision only, not outcomes. |
| Control transform | `kappa/(kappa+0.45)` | IOU: saturating mapping from grid kappa to action-controllability strength. |
| Revision safe target | aversive cue + safe outcome | Derivation: disconfirming evidence is safe evidence for the target cause at ordinary arousal. |
| Frozen revision threshold | `< 10%` | Preregistered in criteria; unchanged. |
| Revisable revision threshold | `> 80%` | Preregistered in criteria; unchanged. |
| Connected-region minimum | 2 cells | IOU: prevents a one-cell speck from satisfying connected-region criteria. |
| Omega grid | 0.20-3.00, 15 points | Ticket requirement: at least 15 points, spanning ordinary to extreme overwhelm. |
| Kappa grid | 0.00-1.40, 15 points | Ticket requirement: at least 15 points, spanning flat to high control. |
