# Simulation Parameter Registry
## Magic numbers, justifications, and sensitivity status

**Last updated:** 2026-03-26
**Model:** ifs_model_v2.jl
**Keep this file evergreen as the simulation evolves.**

---

## Parameter Categories

### Tier 1: Mechanism parameters (the paper's claims depend on these)

| Parameter | Value | Role | Justification | Sensitivity |
|---|---|---|---|---|
| `beta_se` | 2.2 | Part precision decay rate with Self-energy | Controls Move 2: how fast part prior weakens as E_t rises. Originally 2.5 in v1, softened to 2.2 for three-condition gradient. | ±20% passes. Ratio with gamma_se matters more than absolute value. |
| `gamma_se` | 2.0 | Context precision growth rate with Self-energy | Controls Move 2: how fast context gains weight. Originally 2.5 in v1. | ±20% passes. |
| `lambda_witness_max` | 5.5 | Max witness channel precision | Controls Move 3: how strong channel 5 is when fully open. Tuned for relational depth gap. | KEY PARAMETER. Sweep 2.0-10.0 planned. |
| `alpha_witness` | 3.0 | Superlinear exponent for witness opening | Controls Move 3: how sharply channel 5 opens. >1 means it only opens substantially at low capture. | Sweep 1.5-5.0 planned. |
| `lambda_witness_floor` | 2.75 | Context precision floor for witnessing | Prevents false witnessing when both precisions are weak. Safeguard from GPT 5.4 review. | Should be stable — it's a guard, not a tuning lever. |

### Tier 2: Prior strength parameters (bundle initialization)

| Parameter | Value | Role | Justification | Sensitivity |
|---|---|---|---|---|
| `pi_part` | 3.2 | Base part prior precision | How strongly the burdened bundle dominates. Was 8.0 in v1, reduced to 3.2 during tuning. | ±20% passes. |
| `lambda_ctx` | 0.9 | Base context evidence precision | Baseline weight of present-context evidence. Was 2.0 in v1. | ±20% passes. |
| `d_self_helpless` / `d_self_capable` | 18.0 / 2.0 | Initial self-state prior (90% burdened) | Strong prior = consolidated part. 90/10 split is conceptually appropriate. | Moderate. Ratio matters more than absolute values. |
| `d_threat_dangerous` / `d_threat_safe` | 16.0 / 4.0 | Initial threat prior (80% burdened) | Slightly less certain than self-state. Threat can soften faster. | Moderate. |
| `d_outcome_avoidance` / `d_outcome_manageable` | 15.0 / 5.0 | Initial outcome prior (75% burdened) | Weakest of three. Expected outcome is most downstream. | Moderate. |

### Tier 3: Modality weights (observation channel importance)

| Parameter | Value | Role | Justification | Sensitivity |
|---|---|---|---|---|
| `weight_external` | 0.18 | Channel 1 weight | External cues are somewhat informative but not decisive | Arbitrary. Planned: reduce to 2 derived ratios. |
| `weight_intero` | 0.18 | Channel 2 weight | Body signals, similar importance to external | Arbitrary. |
| `weight_outcome` | 0.16 | Channel 3 weight | Action outcomes, slightly less weight | Arbitrary. |
| `weight_info` | 0.24 | Channel 4 weight | Informational context, more weight (scaffolds Move 2) | Arbitrary. |
| `weight_witness` | 1.0 | Channel 5 weight | Witnessed self-state dominates when open. THIS IS THE MECHANISM. | Semi-justified. The asymmetry is the point. |

### Tier 4: Policy and control parameters

| Parameter | Value | Role | Justification | Sensitivity |
|---|---|---|---|---|
| `policy_precision` | 4.0 | Softmax temperature for policy | Controls how deterministic policy is. Inherited from v1. | Sweep 2.0-8.0 planned. |
| `probe_policy_precision` | 4.6 | Softmax temp during probe | Higher than policy_precision by 0.6. Looks tuned. | **TO ELIMINATE** — should equal policy_precision. |
| `r_t` | 1.0 | Part activation strength | Always 1.0. | **TO ELIMINATE** — absorb into pi_part. |

### Tier 5: Structural constants

| Parameter | Value | Role | Justification |
|---|---|---|---|
| `T_forced` | 20 | Forced contact duration | Spec-defined. |
| `T_probe` | 3 | Free-choice probe duration | Spec-defined. |
| `revision_threshold` | 0.50 | P(revised) to count as crossed | Standard decision boundary. |

### Tier 6: A/B matrix entries (~130 probability values)

Not listed individually. Each is a hand-specified likelihood constrained to sum to 1.0 per column. These are inherently model assumptions about the generative process. Not eliminable, but should be documented with their intended interpretation.

### Tier 7: Policy scoring coefficients (~20 values) — TO BE REPLACED

The `compute_ifs_v2_policy_probs` function (lines 628-641) contains ~20 hand-tuned coefficients for a bespoke scoring function. **These should be replaced with proper Expected Free Energy (EFE) computation.** Refactor in progress.

---

## Planned eliminations

1. **`r_t`** → absorb into `pi_part`
2. **`probe_policy_precision`** → use `policy_precision` for both
3. **Five modality weights** → reduce to two ratios: `witness_to_info_ratio`, `info_to_external_ratio`
4. **~20 policy scoring coefficients** → replace with EFE computation using C matrix preferences

## Planned sensitivity sweeps

| Parameter | Range | Status |
|---|---|---|
| `lambda_witness_max` | 2.0 - 10.0 | Pending |
| `alpha_witness` | 1.5 - 5.0 | Pending |
| `beta_se / gamma_se` ratio | 0.5 - 2.0 | Pending |
| `policy_precision` | 2.0 - 8.0 | Pending |

## Context signal coefficients (compute_ifs_v2_capture, line 314-317)

The context_signal computation uses: `0.25, 0.20, 0.30, 0.25`. These weight how much each belief factor contributes to the effective context. **These are arbitrary and should be documented or derived.**

---

## Evergreen notes

- When parameters change, update this file.
- When new parameters are added, add them here with justification.
- When a parameter is eliminated, move it to the "Eliminated" section below.
- After each sensitivity sweep, update the Sensitivity column.

## Eliminated parameters

(None yet)
