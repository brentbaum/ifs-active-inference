# Sim 2 T4.3 Magic Numbers and Pilot Provenance

The values below were written before the T4.3 pilot. Step B must freeze or amend
them after audit; confirmatory seeds may not be used to tune them.

| Constant | Pilot value | Provenance / debt |
| --- | ---: | --- |
| `n_melt_trials` | 60 | Retained matched evidence budget from T1.3 so the de-authored result is directly comparable. |
| `primary_gate` | `write` | Theory choice: R2 locates E_t in D1 effective precision; D2 reading (i) is implemented as registration at write, with raw BMR afterward. |
| `bmr_interval` | 5 | Retained reporting cadence only; no criterion is defined as `interval / melt length`. |
| `bmr_intervals` | `[3,5,10]` | Ticket-mandated arithmetic robustness sweep spanning frequent, original, and sparse checks. |
| `accessibility_functions` | saturating, threshold-linear | Two independently motivated Option B forms: graded effective sample size and addressability threshold. |
| `early_prompt_max_trial` | 10 | Retained T1.3 early probe before substantial corrective evidence. |
| `late_prompt_trial` | 45 | Retained T1.3 late probe after three quarters of the matched budget. |
| `high_E`, `low_E` | 0.90, 0.05 | Retained normalized witnessing/capture anchors used elsewhere in the suite. |
| `flip_trial` | 3 | Early single-observation perturbation. The new audit checks branch-specific one-entry invariants rather than assuming write counts must be identical in Option A. |
| `pi_part`, `beta_se` | 4.0, 1.0 | Retained D1 bundle-prior map from T1.3/Sim 3. Hand-set map parameters; no new tuning. |
| `lambda_ctx`, `gamma_se` | 1.0, 1.2 | Retained D1 contextual-evidence map from T1.3/Sim 3. Hand-set map parameters; no new tuning. |
| `E0` | 1.0 | D2 toy-demo scale for the saturating robustness arm, retained without pilot tuning. |
| `access_threshold`, `access_full` | 0.20, 0.80 | Theoretical bracketing: 0.05 capture lies below addressability; 0.90 witnessing lies above full access. This is a hand-set robustness model, not an estimated psychophysical threshold. |
| `prior_log_odds` | -5.0 nats | Retained T1.3 prior against pruning; swept ±1 nat jointly with all BMR intervals. |
| `relational_count_good`, `relational_count_old` | 1.0, 0.08 | Retained one-count relational observation and finite residual old-coupling evidence. The 0.08 residual remains an IOU inherited from the D2 toy geometry. |
| `informational_root_fraction` | 0.20 | New preregistered weak routing: a fact about the cue carries one fifth the root likelihood strength of being met well. Chosen as a theory-readable 1:5 contrast before pilot; live failure is possible because 60 trials write 12 full-weight root counts in Option A high-E content-swap. |
| v2 root-prior base | `[1,1]` | Canonical unit Dirichlet base measure, not a fitted frozen prior. |
| v2 root-prior mass | `log1p(structural_precision)` | Monotone compression from the formation bundle’s count scale into equivalent root sample size while v2 lacks relational fields. Explicit schema-v2 bridge; schema v3 should remove it. |
| `ordinary_learning_rate` | 1.0 | One ordinary outcome count per unattenuated observation. |
| `attenuation_learning_rate` | 0.18 | Retained T1.3 dissociative-quiet attenuation; independent of E_t and applied in both gate arms. |
| `policy_learning_rate` | 0.25 | Retained slow competence/policy-bank update scale. |
| `policy_precision` | 3.0 | Retained policy readout gain. |
| `root_avoidance_bias` | 0.48 | Retained contribution of an intact relational root to compulsive avoidance. |
| `danger_avoidance_bias` | 0.55 | Retained true-contingency contribution in the real-danger control. |
| `competence_policy_floor` | 0.12 | Retained pseudocount floor keeping competence policies available after root pruning. |

## Pilot tuning log

- Before first T4.3 pilot execution: no constants had been tuned against T4.3
  outcomes. The design changes were made from the ticket, D2, and the adversarial
  review. Any rerun-driven change must be appended here with old value, new
  value, observed failure, and theoretical justification; silent replacement is
  prohibited.
- After the pilot (seeds 1001–1010): **no constants were changed and no second
  pilot was run.** Option A's contact-under-capture and content-swap arms both
  melted in 10/10 seeds. This kills the primary four-regime/C3 contrast at the
  registered values. Raising the BMR penalty or lowering informational routing
  after observing that result could manufacture the desired separation, so this
  Step A deliberately leaves the negative result intact for orchestrator audit.
