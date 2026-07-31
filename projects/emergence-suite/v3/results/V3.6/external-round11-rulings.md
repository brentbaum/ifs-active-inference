# Binding rulings

## 1. A1 — Classify the V3.6 noninferiority stop as an invalid-comparison apparatus failure

The formal Gate-3 verdict remains **FAIL**, but its predictive-noninferiority component is reclassified:

```text
FAIL_INVALID_COMMON_SUPPORT_APPARATUS
```

It is **not** evidence that V3 is predictively inferior to V2.

The executed comparison violated the minimum requirement for predictive comparison:

- the two models received independently generated observations;
- they scored different variables;
- they used different history lengths;
- they used different token denominators;
- zero of 2,000 observation documents were identical;
- the sign changed under plausible alternative normalizations. 

The observed structural/model-averaging cost is therefore not yet interpretable. A flexible 128-program grammar genuinely should pay more posterior-predictive complexity than a concentrated three-state menu, and that cost **must remain in the repaired test**. But it becomes scientifically meaningful only when both models predict the same held-out targets from the same history.

Binding implications:

- Retain the original `?0.0339 [?0.0380, ?0.0296]` result verbatim.
- Do not call it scientific predictive loss.
- Do not truth-clamp, flatten, or otherwise equalize the structural priors in the repaired primary statistic.
- Continue reporting a truth/equivalence-class-clamped decomposition as a diagnostic.
- The full posterior predictive—including each model’s actual structural prior and model averaging—is the repaired primary quantity.

The fact that the truth-clamped component was only about `?0.0041` while the mixture residual contributed about `?0.0293` is useful localization, but not a valid estimate of compression cost under unequal support. 

---

## 2. A2 — Replace the scalar pseudo-joint tournament with a common-target predictive panel

Do **not** construct one synthetic “joint V2 likelihood” by multiplying its independent stage modules. Suite v2 does not define one coherent joint distribution over the whole V3 observation document. Multiplying its modules would create another authored accounting choice and could double-count evidence.

The repaired tournament is a panel of matched conditional-prediction tasks.

### 2.1 One canonical document per seed

Generate one canonical R0 world and one immutable observation document per seed.

Primary length:

```text
64 slices total
48-slice inference prefix
16-slice untouched held-out suffix
```

Also publish 16-, 32-, and 48-prefix information curves descriptively.

For every seed:

```text
canonical_world_sha256_V2 == canonical_world_sha256_V3
canonical_observation_sha256_V2 == canonical_observation_sha256_V3
heldout_target_sha256_V2 == heldout_target_sha256_V3
```

No model-specific RNG call may generate or modify observations.

### 2.2 Five required shared targets

For every held-out slice, both models must return a normalized predictive distribution for the same target token:

1. **Identity evidence**
   - canonical self/root observation;
   - V2 adapter: self-state channel;
   - V3 adapter: root/identity observation.

2. **Outcome evidence**
   - canonical harm/safety outcome conditional on the same `do(action)`;
   - action selection itself is never scored as evidence.

3. **Context evidence**
   - canonical present/historical/localization observation;
   - deterministic sentinels and masked values do not count as delivered tokens.

4. **Partner-response evidence**
   - canonical remaining/pressure/contingency response.

5. **Contact-response evidence**
   - canonical contact, denial, or relational-availability outcome after the same intervention.

Each V2 target is scored by exactly one frozen V2 module. V2 stage likelihoods may not be multiplied into a pseudo-joint score.

If either model cannot return a normalized predictive distribution for one of these targets through an analysis-only deterministic adapter, the bridge fails before criterion seeds. That target may not be silently omitted after results.

### 2.3 Model-exclusive channels

The following may be published as scope-extension results but are outside the noninferiority criterion unless both models can predict exactly the same target:

- V3 mode signals;
- V3 world-state signals not represented in V2;
- policy-proposal channels;
- support-targeting signals;
- any V2-only configural object with no V3 observable counterpart.

An exclusive channel must never be assigned a neutral pseudo-score to force commensurability.

### 2.4 Scoring

For target family \(\tau\), world \(w\), and held-out target tokens \(j\):

\[
S_{m,w,\tau}
=
\frac{1}{N_{w,\tau}}
\sum_j
\log p_m(y_{w,\tau,j}\mid x_{w,\tau,j}),
\]

where both models receive the same \(x\) and predict the same \(y\).

The paired effect is:

\[
D_{w,\tau}=S_{V3,w,\tau}-S_{V2,w,\tau}.
\]

There is **no criterial weighted aggregate** across target families. Report the five differences as a Pareto vector. An equal-target-weight macro mean may be descriptive only.

This preserves the design principle already stated in the V3.6 plan—that the compression result is a profile rather than a single scalar—while correcting the implementation, which used `3 ? V2 slices` versus `5 ? V3 slices`. 

### 2.5 Required bridge proofs

Before any repaired criterion seed:

1. canonical document identity;
2. target-token identity;
3. mask identity;
4. equal delivered-target counts;
5. no sentinel counted as an observation;
6. deterministic adapters with zero RNG;
7. normalized prediction on every shared target;
8. target unavailable before prediction;
9. full posterior predictive includes the native structural prior;
10. truth-clamped decomposition recombines exactly;
11. no model-exclusive channel enters the primary score;
12. no V2 module contributes twice to one target;
13. bridge input copying;
14. model source and scientific parameters bitwise unchanged.

---

## 3. A2 — Retire the old noninferiority margin and freeze a new interpretable margin

The existing margin:

```text
0.018566762350958 nats/token
```

does not transfer. It was derived from a V2.4.4 BMA interval on a different target, population, and denominator. The plan records that provenance explicitly. 

Use one prospective practical margin for each shared target:

\[
\delta=\log(1.02)=0.01980262729617973
\]

nats per delivered target token.

Interpretation:

> V3’s geometric-mean probability assigned to the observed target may be at most approximately 2% lower than V2’s.

For each of the five targets, require:

\[
\operatorname{lower}_{95\%}
\left[
E(D_\tau)
\right]
\ge -\delta.
\]

No family-specific exception is permitted.

### V2 precision qualification

Before V3 is scored on criterion worlds, the V2-only public calibration block must show that the full width of its deterministic whole-world bootstrap interval is at most \(\delta\) for every target family.

If a target’s V2 interval remains wider than \(\delta\), the target is insufficiently measured and the apparatus stops. Do not enlarge the noninferiority margin.

Use 10,000 deterministic whole-world bootstrap replicates.

### Seed authorization

Add these blocks to Epoch C:

```text
common-target bridge and V2 precision qualification:
3680000:3683999

fresh repaired tournament:
3684000:3689999

repair diagnosis reserve:
3690000:3699999
```

The existing diagnosis block through `3679999` remains barred according to its prior uses. The V3 development namespace remains open through `3899999`; the three challenge escrows remain separate at `4100000:4129999`. 

The original Gate-3 tournament is not rerun or overwritten. The repaired result is named:

```text
V3.6-R1 COMMON-TARGET COMPRESSION TOURNAMENT
```

---

## 4. A3 — Use predictive-equivalence-class calibration, with exact-program recovery descriptive

Exact-program accuracy is not the primary calibration target on the tournament population.

The V3 diagnosis found exact-program accuracy `0.025`, ECE `0.286`, and normalized entropy `0.465` on the 16-slice fixed formation population, while the cited Gate-2 calibration came from a distinct 64-slice prior-sampled population. 

Two issues are mixed there:

- insufficient information to distinguish graph programs with identical predictions;
- population-prior shift between prior-sampled Gate 2 and fixed-stratum Gate 3.

### 4.1 Primary calibration: observable prediction

For every shared target, require on the actual tournament population:

- predictive ECE `≤ 0.05`;
- reliability diagram;
- Brier score;
- mean log score;
- calibration by developmental stratum;
- calibration by active-mode count.

This is the calibration most directly relevant to predictive noninferiority.

### 4.2 Structural calibration: equivalence classes

After the 48-slice prefix, construct for each V3 program \(H\) the exact predictive-signature vector over:

- all five shared target families;
- all possible values of each target;
- the frozen held-out intervention and context query schedule.

For world \(w\):

\[
H\sim_w H'
\iff
\max_q
\left\|
p_H(Y_q\mid X_q,o_{1:48})
-
p_{H'}(Y_q\mid X_q,o_{1:48})
\right\|_\infty
\le10^{-10}.
\]

Sum posterior mass over each class.

Primary structural reporting:

- truth-equivalence-class posterior mass;
- class argmax accuracy;
- class ECE;
- 50%, 80%, 90%, and 95% class-set coverage;
- normalized class entropy.

Blocking requirements:

```text
equivalence-class ECE <= 0.05
95% class-set coverage >= 0.90
active-count ECE <= 0.05
load-bearing edge ECE <= 0.05
```

Exact-program accuracy, exact-program ECE, and exact-program entropy remain mandatory but descriptive.

### 4.3 Prior-matched calibration fixture

Use half of `3680000:3683999` for an own-prior common-document calibration fixture. This tests the theorem-level calibration of the native code-length posterior.

Use the other half for the fixed-stratum bridge population. On that population, also publish a diagnostic posterior reweighted to the known evaluation mixture, but do not use the reweighted posterior for predictive scoring or scientific inference.

The native code-length prior remains the primary posterior and continues to pay its genuine complexity cost.

---

## 5. A4 — Existing V3.6 results and sealed challenges stand

The following Gate-3 findings are independent of the invalid cross-model tournament and remain valid:

- both structural-economy reductions above 50%;
- all nine floor-bearing ablation contrasts;
- stakes scientific-posterior identity;
- stakes policy effect;
- all required V3.5-derived stress categories. 

Do not rerun them as part of the tournament repair.

C?V36A, C?V36B, and C?V36C survive unchanged because, as represented in the request, none uses the tournament statistic or margin. Their escrow blocks remain intact and separate. Before reveal, the evaluator must commit a compatibility attestation confirming:

```json
{
  "tournament_bridge_not_imported_by_challenge_runner": true,
  "challenge_criteria_do_not_reference_noninferiority": true,
  "challenge_floors_unchanged": true,
  "scientific_model_unchanged": true,
  "challenge_hashes_unchanged": true,
  "escrow_unchanged": true
}
```

### Continuation after the repaired tournament

The result of the valid repaired tournament is scientific:

- If all five targets pass, V3 earns predictive noninferiority on shared scope.
- If any target fails, that failure stands as a real predictive price of compression.

A valid numeric failure does **not** block Gates 4–5 or the three already-sealed whole-system challenges. It blocks only the sentence “V3 incurred no material predictive loss.”

This continuation is authorized now, before the repaired result is known.

Suggested statuses:

```text
if repaired tournament passes:
V3.6_COMPRESSION_NONINFERIORITY_PASS_WITH_RETAINED_INVALID_INITIAL_TOURNAMENT

if repaired tournament fails scientifically:
V3.6_COMPRESSION_PREDICTIVE_COST_RETAINED_WITH_MECHANISM_PROFILE_CONTINUED
```

---

## 6. B1 — The V3.3 do-over speed null is valid only at an evidence ceiling

The V3.3 result must remain exactly as sealed:

- the post-revision do-over was equivalent to correction-only;
- premature imagery alone was not durable under return evidence;
- same-edge reduction and adaptive-edge survival passed. 

But the broad interpretation must be narrowed.

The corrective stream crossed the material boundary very early relative to the available 48-slice trajectory. The Gate-3 speedup was essentially zero, and 799/800 eligible pairs reportedly had no meaningful difference. The formal speedup criterion failed while the correction-only material-reduction rate was approximately `0.978`. 

Therefore C?V33 establishes:

> Under a strong, rapidly saturating corrective stream, adding a post-revision do-over does not improve the measured reduction speed or endpoint.

It does **not yet establish**:

> Do-overs cannot accelerate reduction under a nonsaturated evidential regime.

A paced extension is required to distinguish genuine equivalence from an evidence-ceiling artifact.

---

## 7. B2 — Present the three findings as one claim family with separate scopes

Use the family-level claim:

> **A do-over has no privileged structural operation. It is an ordinary source of evidence whose effects depend on its information, timing, and the later evidence path.**

Then retain three distinct instances.

### Instance 1 — V3.3 post-revision strong-stream equivalence

Scope:

- strong corrective stream;
- early material crossing;
- no detectable added speed or endpoint effect.

Status:

- prospective sealed result;
- possible ceiling limitation.

### Instance 2 — V3.3 premature imagery alone

Scope:

- premature imagery without adequate ordinary correction;
- burden-return probe.

Result:

- no durable reduction.

This supports readiness/evidential-landscape dependence.

### Instance 3 — V3.6 whole-trajectory endpoint path independence

The fresh event-indexed V3.6 pilot and Gate 3 both produced intervals crossing zero. Subsequent ordinary corrective evidence made the final edge-absence posterior nearly independent of whether the premature packet had appeared.  

This strengthens the no-privileged-operation and endpoint-path-independence claims. It does **not** validate the V3.3 speed null; endpoint equality can coexist with transient timing differences.

The paper should not pool these into one effect estimate.

---

## 8. B3 — Include the suggestion-direction anomaly, but first determine its exact semantic status

Do not leave the `?0.0075` root-direction result unexplained. V3.3 retained it as a small negative result. 

Before sealing the timing extension, exactly enumerate the suggestion-only packet’s likelihood.

For every relevant root and structure state, calculate:

\[
\log BF_G(o_{\mathrm{suggestion}})
=
\log
\frac{
p(o_{\mathrm{suggestion}}\mid G=1)
}{
p(o_{\mathrm{suggestion}}\mid G=0)
}
\]

and the corresponding burden-edge Bayes factors.

Two possible outcomes:

### Candidate-common suggestion

If the packet is intended to contain no root information:

```text
root BF = 0 exactly
burden-edge BF = 0 exactly
```

Any nonzero simulated direction is then an apparatus defect and must stop the extension before challenge seeds.

### Indirectly informative suggestion

If the learned graph makes a positive outcome token more likely under one root or edge state, freeze the analytically predicted sign before simulation. The prior “positive direction” expectation is then retired; the observed negative result becomes a model implication rather than an anomaly.

The suggestion arm is secondary. It cannot determine the primary do-over-timing verdict.

---

## 9. B4 — Binding specification for the sealed do-over timing extension

Name the study:

```text
T-V3-DO1 — do-over timing under nonsaturated corrective evidence
```

It is post-ladder work, not V3.3 repair and not required for V3.6 closure.

### 9.1 Frozen model

- exact final V3.6 scientific model;
- no new latent, edge, likelihood, prior, or parameter;
- protocol scheduling and observation timing only;
- imaginal/ordinary source label remains likelihood-neutral.

### 9.2 Seed namespace

```text
public pacing qualification:
5000000:5001999

open timing and semantic assays:
5002000:5007999

robustness:
5008000:5013999

diagnosis reserve:
5014000:5019999

sealed extension escrow:
5100000:5105999
```

### 9.3 Apparatus-only pacing qualification

Use correction-only worlds. Do not inspect any imagery or do-over contrast.

Search a frozen lexicographic grid of:

- corrective-packet cadence;
- candidate-common masking cadence;
- already-licensed precision support;
- total correction length.

Select the first schedule satisfying:

```text
trajectory length = 48 correction slices
median first-material time in [24, 32]
20th percentile first-material time >= 12
80th percentile first-material time <= 44
material rate at slice 8 <= 0.15
material rate at slice 48 in [0.60, 0.90]
root-revision event available in >= 0.80 of worlds
```

If no schedule satisfies these conditions, stop as an apparatus failure. Do not relax them after inspecting do-over results.

Retain:

- a fast V3.3-like ceiling schedule;
- the selected paced schedule;
- a weak-evidence stress schedule.

Only the paced schedule carries the primary timing criteria.

### 9.4 Baseline-derived event anchor

For each seed, run the correction-only baseline first and define:

\[
t_R^0
=
\text{first frozen root-revision crossing in the baseline arm}.
\]

The paired intervention schedules are:

```text
premature:       t_R^0 - 4
immediate-post:  t_R^0 + 1
delayed-post:    t_R^0 + 8
```

Primary timing analysis includes the prospectively defined event-available population. Report the complete intention-to-simulate population and the qualification yield.

This baseline counterfactual anchor avoids using an intervention arm’s future crossing to schedule its own treatment.

### 9.5 Evidence-matched arms

Every packet-timing arm receives the same diagnostic configural packet. Only its position changes.

Primary arms:

1. correction only + neutral packet;
2. premature configural imagery;
3. immediate-post configural imagery;
4. delayed-post configural imagery;
5. immediate-post ordinary configural packet with exactly the same content;
6. immediate-post suggestion-only packet.

All arms have equal slice counts.

For arms 2–5, publish:

- exact packet log BF;
- cumulative structural BF by slice;
- total delivered structural BF;
- root BF;
- edge BF.

The ordinary-versus-imaginal identical-content pair must be bitwise identical. Any difference is an apparatus failure.

### 9.6 Primary estimands

Let:

\[
T^*=\min(T_{\mathrm{material}},48).
\]

Report:

1. paired restricted-mean time to material reduction;
2. first-material-time distribution;
3. material reduction at slice 48;
4. material reduction after a 24-slice return/stress phase;
5. final current-context edge-absence posterior;
6. first root-revision time;
7. total delivered structural log BF.

Frozen practical thresholds:

```text
meaningful timing difference: > 1.0 slice
time-equivalence ROPE: [-1.0, +1.0] slices
final edge-posterior ROPE: [-0.01, +0.01]
durable material-rate ROPE: [-0.02, +0.02]
semantic identity tolerance: 1e-10
```

### 9.7 Key contrasts

#### Evidence-ceiling interaction

\[
I_{\mathrm{ceiling}}
=
S_{\mathrm{paced,post}}
-
S_{\mathrm{fast,post}},
\]

where:

\[
S_{\mathrm{pace,post}}
=
E[T^*_{\mathrm{neutral}}-T^*_{\mathrm{post}}].
\]

Evidence-ceiling interpretation is supported when:

```text
paced post speedup > 1 slice with lower CI > 0
and
paced-minus-fast speedup interaction > 1 slice with lower CI > 0
```

It is falsified when the paced post effect’s full interval lies inside the ±1-slice ROPE.

#### Readiness/timing effect

\[
I_{\mathrm{timing}}
=
E[T^*_{\mathrm{premature}}-T^*_{\mathrm{post}}].
\]

A genuine timing effect requires:

```text
mean > 1 slice
lower CI > 0
```

#### Privileged-operation test

Imaginal versus ordinary identical-content packets must be bitwise identical.

A difference above `1e-10` is an apparatus failure, not a scientific result.

#### Endpoint path independence

After sufficient later evidence:

```text
post vs premature final q(edge absent) interval inside [-0.01, +0.01]
post vs premature durable-rate interval inside [-0.02, +0.02]
```

Crossing-time differences may coexist with endpoint equivalence.

#### Premature durability

If premature imagery speeds transient crossing but fails after return while post-revision imagery survives, readiness dependence is supported.

If both survive equally under the paced stream, the original V3.3 premature failure was schedule-specific.

### 9.8 Interpretation patterns

| Pattern | Interpretation |
|---|---|
| Fast null, paced post speedup | V3.3 post-revision null was ceiling-limited |
| Fast and paced null | Genuine no-speedup result under both regimes |
| Post beats premature with same packet | Timing/readiness matters |
| Post equals premature, endpoints equal | Evidence content matters; timing does not |
| Imaginal equals ordinary exactly | No privileged do-over operation |
| Timing changes crossing but not endpoint | V3.6 endpoint path independence plus transient timing effect |
| Suggestion packet has exact zero root BF | Suggestion direction must be zero |
| Suggestion packet has analytically signed root BF | Report that sign; retire the earlier verbal expectation |

The sealed extension should publish this profile whole rather than require one preferred pattern.

---

## 10. C — Closure sequencing

Adopt the following order.

### Step 1 — Commit this adjudication

Record:

```text
original Gate-3 noninferiority verdict:
FAIL retained

classification:
INVALID_COMMON_SUPPORT_APPARATUS

one tournament-apparatus repair:
authorized
```

### Step 2 — Build and freeze the common-target bridge

Before repaired criterion seeds:

- canonical document specification;
- five target adapters;
- bridge proofs;
- equivalence-class definition;
- 2% noninferiority margin;
- V2 precision qualification;
- seed-map addendum;
- repair analysis plan.

### Step 3 — Run V3.6-R1 once

Use:

```text
3680000:3683999  bridge/margin/calibration
3684000:3689999  repaired tournament
```

If the bridge or calibration apparatus fails, stop and return to the evaluator.

If the apparatus passes, retain the scientific noninferiority result whether it passes or fails.

### Step 4 — Gates 4–5

Proceed regardless of a valid numeric noninferiority pass or failure.

A numeric failure affects the compression claim, not the already-independent mechanism, lesion, robustness, or challenge questions.

Gates 4–5 must additionally rerun:

- common-target bridge identities;
- shared-target predictive calibration;
- equivalence-class profile;
- structure-prior decomposition;
- support equality;
- 16/32/48/64 information curves.

### Step 5 — Challenge compatibility and execution

Have the evaluator attest that C?V36A/B/C do not reference or import the tournament repair.

Then:

1. freeze V3.6;
2. reveal each challenge;
3. validate schema without escrow;
4. release its existing block;
5. run once;
6. seal traces before scoring;
7. publish immutable verdicts first.

### Step 6 — Publish the final V3 profile

Include:

- every V3.0–V3.5 verdict;
- both V3.6 stage-0 stops;
- the invalid original tournament;
- the valid repaired tournament;
- all Gate-3 mechanisms;
- structural-economy results;
- Gates 4–5;
- C?V36A/B/C;
- V3.1 revisability limitation;
- V3.3 do-over equivalence and suggestion result;
- V3.4 short-history conjunction limitation;
- V3.5 support and registration repair arcs.

### Step 7 — Run T?V3?DO1

This is the first post-ladder study. It does not alter V3.6 or any earlier verdict.

### Step 8 — Paper and HTML propagation

Only after the final V3 profile and timing extension are complete should the main paper make strong do-over timing claims.

The paper may already state from the closed ladder:

> V3 compressed the expanded mechanism suite into one sparse structural grammar and reproduced the full mechanism profile.

The predictive sentence depends on V3.6-R1:

- pass: “without material predictive loss on five shared observable targets”;
- fail: “with a localized predictive cost on [named target(s)].”

The do-over sentence should remain:

> Do-over imagery had no privileged structural operator; its effects were consistent with ordinary evidence, with its timing under nonsaturated conditions tested separately.