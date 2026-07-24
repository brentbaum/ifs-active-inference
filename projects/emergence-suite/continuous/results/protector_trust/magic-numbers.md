# Experiment 47 magic numbers

Every authored semantic constant in `ProtectorTrustConfig` is listed. Numeric identities (`0`, `1`), array indices, and machine `eps()` are mathematical or language primitives rather than fitted constants.

| Constant | Value | Rationale |
|---|---:|---|
| `pilot_seeds` | `14701:14710` | Ten-world pilot namespace. |
| `confirmation_seeds` | `14751:14770` | Fresh, disjoint twenty-world namespace. |
| `situation_count` | `3` | One tested and at least one untested situation are required. |
| `prior_tolerated` | `0.38` | Skeptical but non-degenerate contact-outcome prior. |
| `prior_competence` | `0.36` | Skeptical co-protection prior. |
| `prior_relational` | `0.5` | Symmetric partner-type prior required for chance discrimination. |
| `outcome_success_likelihood` | `0.82` | Reliability of tolerated-contact evidence. |
| `competence_success_likelihood` | `0.84` | Reliability of shared competence evidence. |
| `refusal_response_reliability` | `0.9` | Noisy mapping from post-refusal behavior to partner type. |
| `refusal_episodes` | `2` | The criterion explicitly specifies two refusal episodes. |
| `outcome_evidence_episodes` | `3` | Small matched evidence budget for transfer. |
| `world_jitter_sd` | `0.025` | Fresh worlds vary priors/effect sizes without changing arm matching. |
| `high_stakes` | `2.2` | High consequence multiplier in permission only. |
| `low_stakes` | `0.55` | Low consequence multiplier in permission only. |
| `outcome_risk_weight` | `0.5` | Half of expected permission cost concerns flooding/collapse. |
| `responsibility_risk_weight` | `0.3` | Co-protection contributes separately to expected cost. |
| `partner_risk_weight` | `0.2` | Partner policy contributes separately to expected cost. |
| `refusal_cost` | `0.78` | Cost of maintaining protection in the policy comparison. |
| `decision_temperature` | `0.2` | Soft policy-selection temperature. |
| `future_stakes_multiplier` | `0.35` | Healing future reduces, but does not erase, contact risk. |
| `hope_value` | `0.42` | Value of a representable healed future. |
| `protector_role_value` | `0.2` | Future value when the protector retains a chosen role. |
| `obsolescence_penalty` | `0.46` | Cost when the same future discards the protector. |
| `transfer_epsilon` | `1.0e-8` | Algorithmic strict-comparison tolerance. |
| `chance_tolerance` | `0.05` | Spec §6.5 chance band. |
| `refusal_accuracy_threshold` | `0.8` | Spec §6.5 post-refusal threshold. |
| `stakes_variance_threshold` | `0.15` | Spec §6.5 stakes-attributable variance threshold. |
| `transfer_world_threshold` | `16` | Spec §6.5 confirmatory world count. |
| `hope_shift_margin` | `0.1` | Pilot-frozen permission-shift margin. |
| `hope_flat_tolerance` | `1.0e-12` | Floating-point audit tolerance for flat posteriors. |
| `high_diagnosticity` | `1.2` | Failure log-evidence under diagnostic attribution. |
| `low_diagnosticity` | `0.2` | Failure log-evidence under non-diagnostic attribution. |
| `smooth_success_log_bayes` | `0.34` | Log-evidence from one explainable smooth success. |
| `repair_log_bayes` | `1.18` | Log-evidence from repair inexplicable under the old model. |
| `repair_smooth_successes_k` | `3` | Pilot-frozen smooth-success comparator. |
| `chance_accuracy` | `0.5` | Posterior mass under the symmetric two-type prior. |
| `probability_floor` | `0.05` | Numerical safeguard on jittered skeptical priors. |
| `probability_ceiling` | `0.95` | Numerical safeguard on jittered skeptical priors. |
| `base_bundle_normalization_tolerance` | `1.0e-12` | Floating-point structural-audit tolerance. |

The hope-shift margin and repair comparator `k` were selected at freeze from the pilot and are justified in `freeze-log.md`. No confirmation result was available at that point.

## Exploratory (d), post-freeze

| Constant | Value | Rationale |
|---|---:|---|
| `exploratory_seeds` | `14801:14840` | Forty fresh worlds, disjoint from all opened blocks. |
| `competence_evidence_episodes` | `4` | Small common evidence budget giving five possible success counts. |
| `true_competence_support` | `[0,1]` | Normalized probability support for the seed-specific generator. |
| `incompetent_system_risk_endpoint` | `1` | Existing normalized maximal-risk endpoint; not a fitted penalty. |

All other exploratory constants reuse the frozen config. No obsolescence-penalty parameter enters the risk-model operationalization.
