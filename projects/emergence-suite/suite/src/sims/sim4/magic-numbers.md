# Sim 4 Magic Numbers

Every hand-set constant in `Sim4.jl` and `configs/sim4.yaml` is listed here.

| Constant | Value | Derivation / sweep / IOU |
|---|---:|---|
| `developmental_trials` | 180 | IOU: long enough to place acute, breakthrough, and chronic-management formation events in one biography trace. |
| `therapy_sessions` | 64 | IOU: enough sessions for a rupture setback, trust rebuilding, outside-in descent, and deepest-cause contact across 20+ seeds. |
| `high_E` | 0.90 | Matches the high-depth witnessing scale used by Sim 2. |
| `low_E` | 0.05 | Logged for contract symmetry; Sim 4 therapy uses the high-E_t Self-process. |
| `pi_part`, `beta_se` | 4.0, 1.0 | D1 log-precision tilt parameters, matching Sim 2. |
| `lambda_ctx`, `gamma_se` | 1.0, 1.2 | D1 log-precision tilt parameters, matching Sim 2. |
| `permission_trust_threshold` | 0.56 | IOU: preregistered trust crossing for policy permission readout. |
| `trust_attuned_count` | 8.0 | IOU: relational Dirichlet count for one attuned high-E_t contact. |
| `trust_rupture_count` | 80.0 | IOU: large old-coupling confirmation count used to test rupture asymmetry. |
| `trust_catastrophic_residual` | 0.05 | IOU: small residual catastrophic count during attuned contact to keep forecasts finite. |
| `policy_learning_rate` | 0.45 | IOU: policy-bank feedback rate during actual relational contact. |
| `policy_practice_rate` | 0.80 | Reserved compatibility field; the habit-control trajectory uses `habit_learning_rate`. |
| `mandate_learning_rate` | 0.0 | Derivation: methods-not-mission dissociation requires no mandate/root updates through the protective policy's own operation. |
| `spawn_pressure_decay` | 0.72 | Sim 1 CRP pressure memory reused for forced flood. |
| `spawn_pressure_threshold` | 1.35 | IOU: forced flood must cross spawn pressure in one acute failure. |
| `crp_threshold` | 0.09 | Sim 1-style posterior-predictive failure cutoff for spawn proposal. |
| `flood_predictive` | 0.01 | IOU: posterior predictive assigned to forced direct access while access policies are still blocking. |
| `flood_precision` | 3.2 | IOU: effective precision of breakthrough flood observation. |
| `arousal_pe_scale` | 5.2 | Reuses Sim 1 arousal scaling. |
| `efe_utility_good` | 2.2 | IOU: utility of met-well relational outcome. |
| `efe_utility_bad` | -1.15 | IOU: cost of met-badly relational outcome. |
| `efe_utility_catastrophic` | -4.8 | IOU: cost of catastrophic relational outcome. |
| `efe_information_weight` | 5.0 | IOU: epistemic value of uncertain relational forecasts. |
| `efe_settled_cost` | 1.05 | IOU: saturation cost for repeating already-settled contact, scaled by relational-bank concentration. |
| `habit_trials` | 16 | IOU: brief practiced counter-conditioning block. |
| `habit_initial_avoidance` | 0.86 | IOU: initial policy-only avoidance readout. |
| `habit_learning_rate` | 0.22 | IOU: per-practice decay for the policy-only habit. |
| `protective_practice_learning_rate` | 0.025 | IOU: low non-relational practice effect for protective policy output; practice-only trials are discounted by the low-E_t relational weight. |
| Misattunement session | 8 | IOU: rupture occurs just before the outer relational bank crosses the permission threshold, so setback is measured against an immediately preceding attuned gain. |
| Forced-flood pressure bonus | `(crp_threshold - predictive) / crp_threshold` | Derivation: Sim 1-style one-trial forced access adds posterior-predictive failure magnitude to arousal pressure. |

Any amendment to `configs/sim4-criteria.yaml` must be made before rerunning the
full preregistered suite and logged in the run summary.
