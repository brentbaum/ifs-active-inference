# Sim 4 magic numbers — T4.1 Step A

The classifier and success thresholds were frozen before any T4.1 pilot run.
Only the per-event contact write size may be selected from the preregistered
pilot sweep. This file must be amended with the observed sweep and selection;
the falsified 80:8 implementation remains recorded below.

## Frozen before pilot

| Constant | Value | Provenance |
|---|---:|---|
| Pilot seeds | 1001-1010 | Protocol; the runner rejects all other seeds and labels. |
| Initial development episodes `(omega, kappa; acute, consolidation)` | `(1.4,.9;64,32)`, `(2.6,.5;64,48)`, `(4.0,.2;96,64)`, `(2.0,.7;64,64)` | Neutral severity/control schedule chosen before outputs; contained no cause targets, labels, counts, or positions. It produced only the Sim 1 initial cause in 10/10 seeds and is retained as a failed pilot. |
| `therapy_sessions` | 96 | Pre-pilot capacity for variable-size grown populations; not tuned after output. |
| `high_E`, `low_E` | 0.90, 0.05 | Existing suite D1 scales; only `high_E` is used for therapy writes. |
| `pi_part`, `beta_se` | 4.0, 1.0 | Existing D1 effective-precision parameters. |
| `lambda_ctx`, `gamma_se` | 1.0, 1.2 | Existing D1 effective-precision parameters. |
| `permission_trust_threshold` | 0.72 | Pre-pilot policy readout threshold; above every bounded randomized initial forecast share. |
| `relational_prior_count` | 1.0 | Symmetric pseudo-count scale, applied identically across positions. |
| `relational_prior_jitter` | 0.25 | IID bounded jitter; each count is in `[0.75,1.25]`, independent of formation order. |
| `breach_probability` | 0.08 | Pre-pilot seed-specific environment rate; not targeted to a cause or session. |
| `policy_learning_rate` | 0.45 | Existing Sim 4 feedback scale; every actual write is audited. |
| EFE utilities `(well,bad,catastrophic)` | `2.2,-1.15,-4.8` | Retained outcome preferences; no ordering or label term. |
| `efe_information_weight` | 5.0 | Retained epistemic scale. |
| `efe_settled_cost` | 1.05 | Retained repetition/saturation scale. |
| Classifier `written_reflexivity_max_exile` | 0.35 | Preregistered in `sim4-criteria.yaml` before classifier output. |
| Classifier `catastrophic_belief_min_exile` | 0.25 | Preregistered before classifier output. |
| Classifier `manager_structural_precision_min` | 120.0 | Preregistered before classifier output. |
| Classifier firefighter dominant policies | `flee`, `attenuate` | Preregistered before classifier output. |
| `S4.descent`, `A4.perm` | >= 8/10 | User protocol, frozen before pilot. |
| `A4.grown` | exactly 1.0 complete/zero-authored audit | User protocol, frozen before pilot. |
| `S4.rupture` | ratio > 1 in >= 8/10 | Operationalized before pilot; actual per-seed breach required. |

## T4.1b repaired-access preregistration (frozen before repaired pilot)

| Constant | Value | Pilot provenance |
|---|---:|---|
| Pairwise policy mass | `flee + appease + attenuate` posterior mass | The complement of Sim 1's learned approach/allow policy; fixed by the semantic access mapping, with no taxonomy or position input. |
| Pairwise history weight | blocker's cue-plus-affect write mass under target-active trials / all cue-plus-affect write mass to blocker | Dimensionless grown coupling; exactly zero when the blocker never learned while the target was active. |
| Cue write contribution | Sim 1 `cue_learning_weight * learning_rate` | Exact mass written by `Sim1.update_cause!`; no new fitted scale. |
| Affect write contribution | Sim 1 `learning_rate` | Exact mass written by `Sim1.update_cause!`; no new fitted scale. |
| A4.shuffle-history RNG offset | `9_000_031` | Fixed before repaired pilot; separate from development, forecast, therapy-choice, and outcome streams. |
| A4.shuffle-history permutation domain | all off-diagonal directed cause pairs within seed | Makes either direction reachable while preserving the multiset of grown strengths. |
| A4.shuffle-history degradation | baseline minus shuffled ordering rate `>= 0.20` | Preregistered material degradation of at least 2/10 pilot seeds; `0.10` is weak support and `<=0` falsifies the carrier claim. |

No blocking-strength cutoff is introduced. Every grown strength enters access
continuously; an uncoupled pair contributes exactly zero.

### T4.1b repaired pilot observations (not confirmatory)

| Criterion/readout | Pilot value | Frozen target | Result |
|---|---:|---:|---|
| S4.descent baseline ordering | 1/10 | >= 8/10 | Falsified |
| A4.perm forecast-permuted ordering | 1/10 | >= 8/10 | Falsified (same seed-level outcomes as baseline) |
| A4.shuffle-history ordering | 0/10 | degradation >= 2/10 | Degradation 1/10; weak support only, carrier not accepted |
| A4.grown provenance | 20/20 causes; 0 authored | 100% complete, 0 authored | Support |
| S4.rupture asymmetry | 4/10 | >= 8/10 | Null; breach-after-repair observed in 5/10 |
| Structural precision/order correlation | mean `r=-0.981` in 8 evaluable seeds | Audit only | Strong proxy correlation disclosed; not used by access/EFE |
| Later-to-earlier share of grown blocking mass | mean `0.465` in 8 evaluable seeds | No fitted target | Direction was not reliably outside-in |

The equal-write sweep after the access repair produced ordering `1/10` for all
five candidates. At the retained `0.25` write size, rupture asymmetry was
`4/10` with mean grown ratio `1.3380`; changing write size is therefore neither
an ordering rescue nor authorized after this pilot.

## T4.1c graded-contact identifying preregistration (frozen before pilot)

This experiment changes only the therapy contact/write rule. All three arms
reuse T4.1b's grown stacks, pair strengths, IID forecasts, EFE choice stream,
outcome stream, retained write size, sessions, and pilot seeds.

| Constant | Value | Pilot provenance |
|---|---:|---|
| Contact arms | `G=gate`, `W=weighted`, `P=probabilistic` | User protocol, frozen before the T4.1c pilot. |
| Arm G contact | `access >= 1.0 - 1e-9` | Exact T4.1b rule, retained solely as the reproduction baseline. |
| Arm W contact/write | contact always; every write scaled by continuous `access` | User protocol; no access threshold is applied in this arm. |
| Arm P contact/write | Bernoulli(`access`); full write on contact | User protocol. |
| Arm P contact RNG offset | `3_000_037` | Fixed before pilot; separate from development (`seed`), formation policy (`+1_000_003`), outcome (`+2_000_033`), forecast (`+4_000_009`), forecast permutation (`+8_000_021`), and history shuffle (`+9_000_031`) streams. |
| A4c.baseline | G ordering exactly `1/10`; G zero-contact exactly `5/8` multi-cause seeds | T4.1b reproduction values supplied by protocol. |
| S4c.unlock | W and P each contact in `>=7/10` seeds | User protocol. |
| S4c.descent revival | either W or P complete outside-in ordering `>=8/10` | Gate-authored negative; only a fresh-seed cycle may test the revived claim. |
| S4c.descent no-direction | both W and P ordering `<=3/10`, conditional on unlock | Confirms T4.1b's no-direction conclusion; missing concurrent activation remains a candidate, not a uniquely identified fact. |
| A4.shuffle-history trigger | report the control for any arm with ordering `>=8/10` | The existing within-seed off-diagonal pair-strength permutation and RNG offset are unchanged. |

No arm changes `access_fraction`, `score_contact`, EFE choice, relational
forecast initialization, blocking-strength construction, or cause identity.
Arm W's scale is the raw continuous access value; no cutoff, floor, or fitted
transform is introduced.

### T4.1c pilot observations (not confirmatory)

| Criterion/readout | G gate | W weighted | P probabilistic | Frozen interpretation |
|---|---:|---:|---:|---|
| Seeds with >=1 contact | 5/10 | 10/10 | 10/10 | S4c.unlock supports; the exact-access deadlock disappears in both graded arms. |
| Zero-contact multi-cause seeds | 5/8 | 0/8 | 0/8 | G exactly reproduces T4.1b. |
| Complete outside-in ordering | 1/10 | 1/10 | 1/10 | Both graded arms are <=3/10, so the no-direction conclusion is confirmed. |
| Total contact events | 322 | 960 | 942 | Audit only; W contacts every session by definition, while P realizes Bernoulli access. |
| History-shuffled ordering | 0/10 | 2/10 | 2/10 | No arm reached the >=8/10 trigger. Controls were nevertheless run for all arms; shuffle did not reveal a hidden directional carrier. |

Seed 1003 is the sole outside-in pass in all three unshuffled arms. Unlocking
contact therefore does not revive descent. The gate authored the zero-contact
deadlock, but the grown coupling still has no reliable outside-in directional
bias. Missing concurrent activation remains a candidate mechanism; this pilot
does not uniquely establish it.

## Preregistered pilot-only write-size sweep

Candidate repair and breach write sizes are identical within each arm:
`0.25, 0.50, 1.00, 2.00, 4.00`. Initial configured candidate: `1.00`.

First-pilot results:

| Equal repair/breach write | Ordering rate | Breach observed | Asymmetry rate | Mean grown ratio |
|---:|---:|---:|---:|---:|
| 0.25 | 0/10 | 10/10 | 10/10 | 3.9521 |
| 0.50 | 0/10 | 10/10 | 10/10 | 5.8735 |
| 1.00 | 0/10 | 10/10 | 10/10 | 8.3080 |
| 2.00 | 0/10 | 10/10 | 10/10 | 11.3383 |
| 4.00 | 0/10 | 10/10 | 10/10 | 15.4759 |

Selected: **0.25**, the smallest candidate. It already produced asymmetry in
10/10 seeds, so larger writes would add intervention without earning a new
qualitative result. Repair and breach remain exactly equal per event.

## Pilot schedule amendment after the one-cause falsification

The first neutral schedule exposed low/moderate episodes before the acute
episode. Sim 1 assimilated the later severe observations into its initial cause
and spawned zero causes in every pilot seed. No ordering model can earn a
descent criterion with a one-element population.

On the same pilot seeds only, the final schedule was amended to begin with Sim
1's established two-epoch acute cell `(omega=3.0, kappa=0.0; 72 acute, 128
consolidation)`, followed by neutral episodes `(2.6,.2;64,64)`,
`(1.4,.9;64,32)`, and `(2.0,.7;64,64)`. This changes only environment order;
it does not change Sim 1 parameters, set a cause count, target a cause, or add a
spawn gate. The amended schedule is pilot-tuned and not confirmatory evidence.

Final amended-pilot results:

| Equal repair/breach write | Ordering rate | Breach observed | Asymmetry rate | Mean grown ratio |
|---:|---:|---:|---:|---:|
| **0.25 (selected)** | 8/10 | 10/10 | 10/10 | 2.5613 |
| 0.50 | 8/10 | 10/10 | 10/10 | 4.2696 |
| 1.00 | 8/10 | 10/10 | 10/10 | 6.0870 |
| 2.00 | 8/10 | 10/10 | 10/10 | 8.6324 |
| 4.00 | 8/10 | 10/10 | 10/10 | 12.5149 |

The amended schedule grew 20 causes total: one cause in seeds 1002/1006, two
causes in six seeds, and three causes in seeds 1005/1009. The two one-cause
seeds are scored as descent failures, not treated as trivially ordered. The
8/10 headline therefore has zero margin above the criterion and must be treated
as fragile pilot support.

## Permanently retired authored constants

| Constant | Old value | Verdict |
|---|---:|---|
| `trust_attuned_count` | 8.0 | FALSIFIED mechanism; direct event-size authorship. Removed. |
| `trust_rupture_count` | 80.0 | FALSIFIED mechanism; direct event-size authorship. Removed. |
| `mandate_learning_rate` | 0.0 | FALSIFIED measurement; assumed the answer. Removed. |
| Authored formation trials/routes/positions | `8/72/150` and taxonomy-like strings | FALSIFIED mechanism. Removed. |
| Forecast inheritance | blocker-count sum | FALSIFIED ordering carrier. Removed. |
