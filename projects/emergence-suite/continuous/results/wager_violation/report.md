# Experiment 46: the wager-violation construction

## Design

This construction gives Experiment 45 recruitment-style carriers one transition-relevant parameter: coupling plasticity under corrective evidence. Each seed creates a pair with separately materialized but numerically identical pre-intervention organizations. The paired carriers have identical affect and policy priors and differ only in coupling plasticity (`0.00` versus `0.30`). Both members receive the same twelve-session witnessing-style corrective-evidence stream.

In arm (a), the carrier-inert transition reads the current couplings, their fixed organization precisions, and corrective evidence; plasticity has no input path. In arm (b), the carrier-active transition adds carrier plasticity to the coupling learning rate. The revision-trajectory metric is the RMS paired distance across both coupling coordinates and every post-baseline session. Couplings are organization variables; carrier plasticity is not included in this or any organization measure.

### Register guards

*Organization* is the four-element bundle, its couplings, its precisions, and the field profile, fixed in advance. *Carrier* is independently parameterized substrate. Coupling plasticity is a **carrier** parameter and never enters the organization-matching vector, revision measure, precision profile, or field profile. No measure was renamed after results.

### Design decisions

- One seed is one matched agent pair; arms are paired within seed and replay identical evidence.
- “Witnessing-style” is operationalized as context-held repeated corrective evidence with the complete, fixed organization precision profile available on every update. This is a construction, not a claim that the two-coupling update exhausts witnessing.
- The spec did not define a revision-trajectory metric. After the pilot, RMS distance over both coupling coordinates and all post-baseline sessions was frozen; baseline matching is audited separately.
- The active criterion is applied to the mean paired divergence across worlds; the inert criterion uses the stricter maximum paired divergence.
- The power curve's “carrier effect” is response divergence on the frozen trajectory metric, not a biological parameter estimate. Measurement noise is modeled as independent error of SD `σ` on each member's organization-derived effect measurement.
- Normal-approximation MDE uses two-sided α = `0.05`, power = `0.80`, twenty matched pairs, and the pilot-frozen between-world SD.
- Exact matching means independent reconstruction plus bitwise equality and maximum componentwise absolute error at or below `1e-12`.

## Organization matching procedure

Experiment 45 generates one prepared-world organization. The procedure reconstructs two independent immutable `PartOrganization` values from its bundle, couplings, precisions, and field profile. Only after those copies exist are two new `PreparedCarrier` values attached. Their affect and policy fields are equal; IDs distinguish the substrates; coupling plasticity is the sole parameter difference.

Pilot verification: maximum absolute mismatch `0.000000`; all pairs bitwise equal `true`; all within tolerance `true`.
Confirmation verification: maximum absolute mismatch `0.000000`; all pairs bitwise equal `true`; all within tolerance `true`.

This audit compares all four registered components separately in `per_seed.csv`: bundle, couplings, precisions, and field profile. Carrier plasticity is recorded in separate carrier columns and is never concatenated into the matching vector.

## Machinery audit

The analytic audit distinguishes corrective/revision transitions from formation and residue machinery. The existing IFS inquiry revision loop has no carrier input. Experiment 45's interference shift reads organization targets and fixed model rates but not `coupling_plasticity`; its formation prior, carrier-identity gate, and residue decomposition do read carrier information and are explicitly shown rather than hidden. Thus the narrow claim supported by the audit is: **the pre-Experiment-46 corrective/revision equations have no coupling-plasticity path**. A broader claim that every Experiment 45 equation is organization-only would be false.

| File/lines | Update equation | Inputs | Classification | Carrier read? | Scope |
|---|---|---|---|---:|---|
| `src/IFSBundleInquiry.jl:68-70` | `update_policy!` | policy-count state; context; selected channel | organization + neither | false | policy learning |
| `src/IFSBundleInquiry.jl:168-170` | `update!(JointBundleLearner)` | bundle-count state; identity root; four-element bundle | organization + neither | false | bundle learning |
| `src/IFSBundleInquiry.jl:232-246` | `update_forecaster!` | precision state; context; posterior field; observed channels; fixed config | organization + neither | false | precision-field learning |
| `src/IFSBundleInquiry.jl:332-363` | `bundle_branch_posterior` | observation; candidate cause; field mean/variance; channel; fixed config | organization + neither | false | state inference |
| `src/IFSBundleInquiry.jl:369-435` | `bundle_state_update` | observations; contact; channels; field; bundle table; optional conclusion; fixed config | organization + neither | false | state inference |
| `src/IFSBundleInquiry.jl:438-493` | `infer_bundle_episode` | observations; contact; channels; field prior; bundle table; fixed config | organization + neither | false | revision/inference loop |
| `src/FormationSubstrateTriad.jl:212-217` | `posterior_mean` | formation observations; prior mean; sample count; fixed config | organization + neither (prior may be carrier-authored upstream) | false | formation, not intervention response |
| `src/FormationSubstrateTriad.jl:220-225` | `prior_for_model` | model label; selected carrier id; carrier affect/policy priors | carrier + neither | true | formation, not intervention response |
| `src/FormationSubstrateTriad.jl:366-372` | `shared_carrier_shift` | model label; two organization targets; fixed model-level update rate | organization + neither | false | interference transition |
| `src/FormationSubstrateTriad.jl:375-389` | `interference_measure` | formation estimates; selected-carrier equality; organization targets; fixed config | organization + carrier identity + neither | true | interference gate; no carrier parameter read |
| `src/FormationSubstrateTriad.jl:392-425` | `selective_reduction` | model label; formation fit; carrier affect/policy priors; fixed retention rates | organization + carrier + neither | true | post-formation residue, not corrective revision |

### Ablation

- Experiment 45 formation replay with carrier plasticities changed from all zero to `[-10, 3, 50, 1000]`: maximum estimate difference `0.000000`; exact invariance `true`.
- IFS bundle-count update replay while an external carrier value changes from `0` to `1000`: carrier input port exists `false`; maximum update difference `0.000000`; exact invariance `true`.
- Experiment 46 active transition before ablation: divergence `0.308971`; with the carrier read ablated: `0.000000`; inert comparator: `0.000000`; ablation restores inert behavior `true`.

## Pilot

Ten worlds (`18401:18410`) were run. Carrier-inert mean/maximum divergence was `0.000000` / `0.000000`. Carrier-active mean divergence was `0.249525` (range `0.095893`–`0.403754`; SD `0.087696`).

## Freeze log

The trajectory metric was fixed at pilot and the provisional thresholds were retained. Confirmation remained unopened until the register, metric, thresholds, power formula, and noise sweep were written to `freeze-log.md` and `magic-numbers.md`.

## Confirmatory results

Twenty fresh worlds (`18501:18520`) were run after freeze; the seed block is disjoint from the pilot.

- Arm (a), carrier-inert: mean divergence `0.000000`; maximum `0.000000`; required maximum `≤ 0.02`.
- Arm (b), carrier-active: mean divergence `0.198541`; range `0.018131`–`0.594903`; required mean `≥ 0.1`.
- Organization match: maximum absolute mismatch `0.000000`; every pair bitwise equal and within tolerance `true`.

### Verdicts

1. **PASS — carrier-inert invariance.**
2. **PASS — carrier-moderated divergence with verified organization matching.**
3. **PASS — organization-matching audit.**

Overall frozen conjunction: **PASS**.

## Power curve

The dedicated `power_curve.csv` gives the minimum response-divergence effect detectable with 80% power in twenty matched pairs as organization measurement noise increases. It combines independent measurement error from both members (`2σ²`) with the pilot-frozen between-world effect variance. These values are feasibility calculations for a future measurement design, not confirmatory outcomes.

| Organization measurement noise SD | Minimum detectable carrier effect |
|---:|---:|
| 0.000000 | 0.054937 |
| 0.010000 | 0.055647 |
| 0.020000 | 0.057724 |
| 0.050000 | 0.070572 |
| 0.100000 | 0.104245 |
| 0.150000 | 0.143799 |
| 0.200000 | 0.185509 |
| 0.300000 | 0.271400 |

## Interpretation guard

Arm (b) is not evidence the wager is false of people. It is the pattern the wager stakes itself against, made concrete — and the demonstration that the losing condition is coherent, detectable, and not absorbable once organization is fixed in advance.
