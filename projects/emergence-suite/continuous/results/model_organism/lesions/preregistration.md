# Experiment 50-L preregistration — lesions and robustness

Status: **locked before any Stage D execution or opening of seed `713204` or above**.

Reference strain: Stage A freeze `274f8888f71ac590d7c15d6f9f59777ea919e182`; Stage B commit `1dcd051`; Stage C commit `effd3e8`.

## Ordering deviation

Specification §9 required this file to be frozen before the 50-P outcomes were inspected. Stage C has already been run and inspected. This is a protocol-ordering deviation and prevents describing the full 50-L preregistration as prospectively independent of 50-P.

The lesion predictions below target only the ten 50-H headline signatures, all of which were already known before either ordering could have been followed. No lesion prediction, sensitivity classification, neighborhood constant, sampling distribution, threshold, or decision rule targets or uses an E3, E4, or E5 outcome. The rationale for proceeding is narrower causal localization of the already-observed 50-H profile, with the ordering deviation carried into every Stage D report.

## Ten headline signatures

One signature per assay is scored to avoid multiplying a lesion’s target merely because an assay has compound secondary criteria. “Survive” means the metric still satisfies the frozen 50-H rule; “disappear” means it fails that rule. Equality follows the frozen plan.

| ID | 50-H signature | Metric | Frozen survival rule |
|---|---|---|---|
| S1 | Freeze formation | joint-boundary predicate agreement | `= 1.00` |
| S2 | Controllability-dependent revision | mean paired root-revision effect | `≥ 0.15` |
| S3 | Dominance–depth dissociation | four-regime realization accuracy | `≥ 0.90` |
| S4 | Identity-first transfer | conditional mean untreated-cue transfer and qualifying-world rate | mean `≥ 0.10` and rate `≥ 0.80` |
| S5 | Co-regulation/access interaction | regulation × evidence difference-in-differences | `≥ 0.10` |
| S6 | Context-family discrimination | five-family macro diagonal recovery | `≥ 0.70` |
| S7 | Timed do-over | mean post-revision do-over advantage | `≥ 0.10` |
| S8 | Registration | mean registration on-minus-off relational change | `≥ 0.10` |
| S9 | Learned protector trust | macro joint partner-type/competence recovery | `≥ 0.70` |
| S10 | Dyad-gate descent | disposition × scaffold interaction | `≥ 0.25` |

The already-failed assay-9 obsolescence crossover is not selected as S9 because a signature that is absent in the reference cannot meaningfully be lesioned away.

## Lesion battery

Each lesion uses `713204:713263` (`N = 60`) with streams paired across the reference and all lesions. Assay 1 uses its complete frozen property domain once; assay 7’s analytic domain is not the selected headline; assay 9 retains its frozen property domain but S9 is scored on the 60 histories per partner family. All other headline metrics use the 60 paired worlds.

Reference execution must call the unchanged canonical assay path and pass the `274f888` identity guard. A lesion may use a configuration/intervention from the frozen grammar. Where no such intervention can change the relevant equation, a lesion-only harness may intercept the named route; it must never be callable on the reference path.

| Lesion | Harness semantics | Predicted to disappear | Predicted to survive |
|---|---|---|---|
| L1 context split unavailable | Disable the shared-root/context-split route: witnessing cannot update the shared root, and `context_split` is unavailable to the family classifier. | S4, S6 | S1, S2, S3, S5, S7, S8, S9, S10 |
| L2 five-channel field → scalar | Replace channel-specific field uptake by one shared scalar; the dominance/depth classifier receives only that scalar and regulation has no relational-channel advantage. | S3, S5 | S1, S2, S4, S6, S7, S8, S9, S10 |
| L3 registration removed | Force the `registration_write` route idle in both nominal registration arms. | S8 | S1, S2, S3, S4, S5, S6, S7, S9, S10 |
| L4 partner model collapsed | Replace trustworthy/neutral/adverse partner-model learning with the neutral partner process before permission and scaffolded descent. | S9, S10 | S1, S2, S3, S4, S5, S6, S7, S8 |
| L5 dyad-to-protector coupling severed | Dyad learning continues, but its packets do not update protector trust, competence, or outcome forecasts. | S10 | S1, S2, S3, S4, S5, S6, S7, S8, S9 |
| L6 freeze write → ordinary learning | Replace the conjunctive one-step high-precision write with an ordinary bounded evidence update lacking the authored overwhelm/control predicate. | S1 | S2, S3, S4, S5, S6, S7, S8, S9, S10 |
| L7 trust posteriors → single outcome forecast | Permission and history recovery expose only `outcome_forecast`; separate partner-type and competence coordinates are unavailable. | S9 | S1, S2, S3, S4, S5, S6, S7, S8, S10 |

### Lesion score

For each lesion, report every signature metric and pass/fail state. A prediction is a hit when a predicted-disappear signature fails or a predicted-survive signature passes. The lesion score is hits divided by 10 with a Wilson 95% interval. Misses remain named; no minimum score retroactively reclassifies them.

## Sensitivity matrix

The one-at-a-time sensitivity matrix covers every constant labeled `shared-equations` in the frozen parameter-use matrix:

`avoidance_cost`, `bayes_reliability`, `competence_risk_weight`, `context_complexity_penalty`, `context_transition_mix`, `dyad_learning_rate`, `dyad_packet_mass`, `dyad_regulated_floor`, `dyad_regulated_span`, `field_broadcast_mix`, `field_context_precision`, `field_learning_rate`, `field_narrowing_strength`, `field_part_precision`, `field_relational_precision`, `freeze_low_control_boundary`, `freeze_no_control_attenuation`, `freeze_overwhelm_boundary`, `freeze_write_precision`, `history_cost_sd`, `history_favorable_cost`, `history_favorable_success`, `history_learning_rate`, `history_root_positive_rate`, `history_unfavorable_cost`, `history_unfavorable_success`, `hope_value`, `imaginal_floor`, `imaginal_span`, `outcome_risk_weight`, `partner_adverse_probability`, `partner_neutral_probability`, `partner_risk_weight`, `partner_trustworthy_probability`, `permission_temperature`, `policy_failure_cost`, `probability_guard`, `refusal_cost`, `registration_increment`, `rng_history_offset`, `root_evidence_weight`, and `training_events`.

Each constant is evaluated at multiplicative factors `0.95` and `1.05`, with probability-like values clamped only if needed to remain in `(probability_guard, 1-probability_guard)` and integer-valued constants rounded to the nearest valid integer with a minimum of one. The reference and both perturbations use `713204:713233` (`N = 30`) with paired streams. Genome copies exist only inside the lesion harness; the on-disk genome never changes.

For metric \(M_s\) and constant \(\theta_j\), the reported sensitivity is the central fractional change

`E[j,s] = (M_s(1.05 θ_j) - M_s(0.95 θ_j)) / max(abs(M_s(reference)), 1e-9)`.

A link is material when `abs(E[j,s]) ≥ 0.10`. Constants with integer rounding that yields identical lower and upper values are reported as unresolved at this perturbation, not as zero sensitivity.

Assay clusters are formation/persistence `{S1,S2}`, field/context `{S3,S4,S5,S6}`, imaginal timing `{S7}`, and protection/dyad `{S8,S9,S10}`. The architecture is classified **constrained** when at least 25% of resolvable constants materially affect two or more signatures and at least one material constant crosses these clusters. It is classified **block-diagonal** otherwise. The full numeric matrix is published regardless.

## Joint genome-neighborhood sweep

The low-dimensional neighborhood uses six constants selected from the frozen matrix because each sits on a canonical route used by more than one configured assay:

| Constant | Role in the joint neighborhood |
|---|---|
| `bayes_reliability` | common developmental and experimental evidence reliability |
| `history_learning_rate` | shared posterior and policy-history learning |
| `root_evidence_weight` | root update and matched-exposure breadth |
| `field_learning_rate` | global field adaptation and uptake |
| `outcome_risk_weight` | protector permission and gate access |
| `dyad_packet_mass` | dyadic evidence delivery into protector/root routes |

There are 80 joint draws, indexed by `713204:713283`. For each draw and each constant independently, a multiplicative factor is sampled from `Uniform(0.90, 1.10)` using the analysis substream keyed by that draw’s escrowed seed. Each sampled genome is evaluated on the paired 20-world cohort `713204:713223`; property domains remain fully enumerated. No draw is rejected or resampled.

Per-signature survival volume is the fraction of 80 draws satisfying that signature’s frozen rule, with a Wilson 95% interval. Joint survival volume is the fraction satisfying at least 8 of 10 signatures. The reference genome is called **central** when at least 8 signatures have survival volume `≥ 0.60` and joint survival volume is `≥ 0.50`; otherwise it is called a **narrow point**. This is a robustness classification, not a tuning target.

## Missingness and integrity

Non-finite metrics and missing required cells fail the affected signature. A harness exception fails that lesion/signature or neighborhood draw and is retained. No seed outside `713204:713403` may be opened. Previously opened 50-H blocks may be read only for committed reference values; Stage D recomputation uses only the L-neighborhood block. No 50-P outcome enters a prediction or metric.
