# External round-12 rulings (verbatim; relayed by Brent 2026-08-01)

# Binding rulings

## 1. Per-population calibration semantics

### 1.1 Retain the stop; reclassify its meaning

The formal V3.6-R1 bridge verdict remains a stop. Classify it as:

```text
STOPPED_AT_BRIDGE_QUALIFICATION_APPARATUS
— NATIVE-POPULATION MISDEFINITION
— FORECAST-SEMANTICS UNRESOLVED
— CALIBRATION-ESTIMAND DEFECT
```

No predictive tournament was run, so this is not evidence for or against V3's noninferiority.
The current 4,000-world calibration results remain in the record, but none should be called "own-prior calibration": the generator was not the complete prior predictive of either model. The earlier common-support diagnosis already established that unequal support and unstable normalization can make apparently precise cross-model numbers uninterpretable.
This remains an apparatus requalification, not a margin or scientific-model change. The earlier calibration boundary—defects stated apparatus-first, criteria not silently moved, and bounded revision—remains the right discipline.

### 1.2 Three populations must now be kept separate

**Population A: V3 native prior predictive.**
Generate complete canonical documents from the frozen V3 prior, grammar, latent processes, and emission models.
Blocking theorem-level criteria:

```text
each target predictive ECE <= 0.05
equivalence-class top-label ECE <= 0.05
95% equivalence-class coverage >= 0.90
active-count top-label ECE <= 0.05
active-count macro classwise ECE <= 0.05
each load-bearing edge ECE <= 0.05
all normalized/proper-score/oracle identities pass
```

**Population B: V2 target-module native prior predictives.**
V2 has no single joint prior predictive over the five canonical target families. Do not invent one and do not exempt V2.
For each target separately, the one frozen V2 module assigned to that target must generate from its own native prior predictive and forecast the same observable token:

```text
identity target  -> native V2 identity/self module
outcome target   -> native V2 formation/outcome module
context target   -> native V2 context/redescription module
partner target   -> native V2 partner module
contact target   -> native V2 protection/contact module
```

Blocking criteria for every target:

```text
predictive ECE <= 0.05
normalized forecast sum error <= 1e-10
adapter-vs-direct-enumeration error <= 1e-10
finite Brier and log scores
```

There is no V2 whole-structure calibration criterion because the five adapters do not share one V2 structure posterior.
If V2 fails a correctly defined native-prior calibration audit, stop and return to the evaluator. Under its own prior predictive, that is not ordinary distribution shift; it indicates a forecast-semantics or probabilistic-coherence problem.

**Population C: external canonical tournament population.**
This population is not generated from either model's prior. Calibration on it is a scientific distribution-shift diagnostic, not a bridge blocker.
Publish, by target and developmental stratum: ECE and reliability tables; Brier and log score; prediction entropy; mean assigned probability; V2–V3 score difference.
Poor external calibration may become a scientific limitation. It does not invalidate proper-score comparison once target semantics and support are correct.

### 1.3 Retain the practical noninferiority margin

Keep delta = log(1.02) = 0.01980262729617973 nats per delivered target token.
It was selected as an interpretable probability-scale margin rather than fitted to the failed bridge. Re-run the V2 precision qualification on the newly specified canonical population. Every target's deterministic bootstrap interval width must remain <= delta.

## 2. Canonical generator

### 2.1 Choose option (b): replace the hybrid generator

The current hybrid must not become the criterial tournament population. It may remain as `HYBRID_GENERATOR_DIAGNOSIS_ONLY` with its complete results retained.
The problem is not simply that neither model "owns" it. A neutral external generator is desirable. The problem is that its partner, context, and possibly identity target processes were not prospectively tied to the forecast semantics of the adapters:

- partner reliability was drawn iid rather than through a declared partner process;
- context used a bespoke emission rule rather than the public temporal/emission grammar;
- the partner discrepancy suggests that the adapter may have compared a latent-state posterior with an observable-token frequency.

The repaired external generator must therefore be an explicit shared-observable-support generator.

### 2.2 Binding generator requirements

The generator must specify ordinary latent processes for all five targets:

```text
identity state       -> identity observation
world + do(action)   -> outcome observation
context state        -> context/localization observation
partner state        -> remaining/pressure observation
partner + policy     -> contact-response observation
```

Requirements:

1. Persistent partner process: declared finite-state Markov partner process; no iid Bernoulli(.5) partner truth.
2. Declared context process: public recurrent/change process and its declared emission function; no standalone bespoke 0.80/0.20 rule.
3. Shared intervention: both models receive the identical do(action) schedule.
4. Intersection support: every target value must have finite, nonzero predictive support under both adapters.
5. No model-owned prior: parameters selected from an external public grid, not sampled from V2 or V3 priors.
6. Balanced scientific population: equal representation of acute one-mode adversity, chronic one-mode adversity, chronic multi-mode adversity, continuing real danger.
7. No clinical labels in inference: stratum labels remain evaluator metadata.
8. One serialized document: both adapters receive byte-identical observations and held-out targets.

### 2.3 Parameter selection rule

Before any qualification or tournament seed, commit `shared-target-support-audit.json`.
For every target: (1) enumerate the public parameter values representable by both adapters; (2) retain their intersection; (3) choose low/medium/high diagnosticity values by the frozen lexicographic rule — nearest to 0.20, nearest to 0.50, nearest to 0.80, ties resolved numerically then by canonical parameter name; (4) balance those values across worlds.
No parameter may be selected using V2–V3 score differences.

### 2.4 Tournament population

6,000 tournament worlds, balanced: 1,500 acute_one; 1,500 chronic_one; 1,500 chronic_multiple; 1,500 real_danger_adaptive.
The five target-specific noninferiority criteria apply to the full balanced population. Report each stratum separately without adding post-hoc stratum thresholds.

## 3. V2 partner and identity resolution

### 3.1 Audit all five adapters, not only partner and identity

Add permanent bridge proof 15 — **forecast-semantics identity**: on an enumerable dummy, each adapter's returned probability vector must equal the frozen module's directly enumerated posterior predictive distribution for the exact observable target token, under the same history, intervention, masks, and query time, within 1e-10.
The target must be an observable, not a latent posterior reused as though it were an observable forecast.

### 3.2 Partner target

The V2 partner adapter must calculate p(r_{t+1} | o_{<=t}) = sum over L_t, L_{t+1} of q(L_t | o_{<=t}) p(L_{t+1} | L_t) p(r_{t+1} | L_{t+1}) — not q(L_t = reliable | o_{<=t}). If the observed target is "remaining after refusal," the adapter must forecast that response token. A latent reliability probability is not the same estimand.

### 3.3 Identity target

Likewise p(i_{t+1} | o_{<=t}) = sum over G of q(G | o_{<=t}) p(i_{t+1} | G), not simply q(G=1). The same rule applies to context, outcome, and contact.

### 3.4 Resolution order

Binding sequence: (1) exact target-definition audit on all five adapters; (2) if mismatch exists, repair the adapter only; (3) verify all scientific V2/V3 source hashes unchanged; (4) rerun exact enumeration; (5) rerun native-prior calibration; (6) only then run external canonical qualification.
If an adapter cannot provide the target through a genuine frozen predictive distribution, stop and return. Do not silently drop or replace the target.
If native calibration passes but external canonical calibration is poor, retain that as a model-specific distribution-shift limitation and proceed to the proper-score tournament.

## 4. Calibration definitions

### 4.1 General weighting

All calibration summaries world-weighted: each world contributes total weight one (w_{w,j} = 1/N_w). Ten frozen equal-width bins [0,.1) ... [.9,1]. Report bin counts and effective world weights.

### 4.2 Binary predictive calibration

confidence = predicted P(target=1); outcome = 1[target observed as 1]. Compute world-weighted ECE, Brier, log score, reliability table.

### 4.3 Active-mode count calibration

Do not mix truth probability with argmax correctness. Two separate valid quantities:
- Top-label ECE: confidence = max_k q(K=k); correct = 1[argmax matches truth].
- Macro classwise ECE: for each k in {1,2,3}, confidence = q(K=k), outcome = 1[K_truth=k]; average equally across classes.
Also report mean q(K_truth), argmax accuracy, multiclass Brier, log score. q(K_truth) may never be paired with argmax correctness inside one ECE.

### 4.4 Equivalence-class calibration

Primary class ECE: confidence = maximum class posterior mass; correct = 1[top class contains truth program]. Also report truth-class posterior mass, class log score, class Brier-style loss, normalized class entropy, exact-program statistics descriptively. No classwise macro ECE across worlds (labels are world-dependent).

### 4.5 Coverage

For 50/80/90/95%: deterministic HPD set (sort classes by mass; ties by canonical minimum program ID; include until cumulative mass reaches level; record truth-class inclusion). Coverage = world-weighted mean.

### 4.6 Edge calibration

confidence = q(edge present); outcome = truth indicator; binary ECE, Brier, log score.

### 4.7 Serialization rule

Every future calibration trace must serialize before aggregation: complete predictive vectors for all five targets; structure posterior; equivalence-class map; class posterior; active-count posterior; edge posteriors; truth program and class; masks; delivered-token counts; confidence/correctness fields; bin assignments.
If a preregistered calibration quantity cannot be recomputed from the persisted trace: `FAIL_UNEXECUTABLE — REQUIRED CALIBRATION STATE NOT SERIALIZED`. Do not rescore a consumed block. The omitted fixed-stratum equivalence posterior is retained as an apparatus failure in the first R1 record.

## 5. Seed authorization

Consumed block stays barred: 3680000:3683999. Tournament block reserved: 3684000:3689999.
Addendum: 3690000:3691999 V2 target-module native calibration (each seed may generate five separately namespaced target-native fixtures); 3692000:3693999 V3 complete native-prior calibration; 3694000:3695999 external shared-support generator qualification + adapter identity repetition + V2 precision qualification + descriptive external calibration; 3696000:3699999 diagnosis reserve only.
Deterministic enumerable adapter fixtures use no random seed.
If 3690000:3695999 passes, run the one and only common-target tournament on 3684000:3689999. There is no second bridge-requalification cycle; another apparatus failure returns to the evaluator before any tournament seed is opened. Add the ranges to epoch-c-seed-map.json.

## 6. Sequencing

6.1 **Gate 4 may run in parallel** once committed: target-semantic audit specification; repaired adapters; canonical-generator specification; calibration definitions; seed-map addendum; scientific-source hash identity. Gate 4 is a V3 internal lesion battery, independent of the tournament.
6.2 **Gate 5 must wait** for R1 qualification and tournament (its required contents are being redefined). Gate 5 may begin only after native calibration passes, external generator qualification passes, and the repaired tournament runs once with its result retained. A valid numeric noninferiority failure remains non-blocking for Gate 5 and the sealed challenges.
6.3 **Challenge sequence unchanged**: after R1 and Gates 4–5 — compatibility attestations; freeze V3.6; reveal; schema-validate without escrow; release block; run once; persist and hash traces before evaluation; publish immutable verdict first. Attestations must confirm no challenge imports the bridge adapters, canonical generator, noninferiority statistic, or calibration definitions.
6.4 **Final statuses**: pass → `V3.6_COMPRESSION_NONINFERIORITY_PASS WITH_RETAINED_R1_BRIDGE_QUALIFICATION_FAILURE`; valid scientific failure → `V3.6_COMPRESSION_PREDICTIVE_COST_RETAINED WITH_RETAINED_R1_BRIDGE_QUALIFICATION_FAILURE`. In either case the ≥50% reductions stand, the nine ablation results stand, Gates 4–5 and C-V36A/B/C proceed, and the failed hybrid qualification remains visible.

## Operative summary

```json
{
  "round": 12,
  "r1_bridge_stop_retained": true,
  "classification": "APPARATUS_NATIVE_POPULATION_FORECAST_SEMANTICS_AND_CALIBRATION_DEFINITION",
  "v2_native_calibration_exempt": false,
  "v2_calibration_form": "PER_TARGET_MODULE_NATIVE_PRIOR_PREDICTIVE",
  "v3_calibration_form": "COMPLETE_NATIVE_PRIOR_PREDICTIVE",
  "external_population_calibration": "DESCRIPTIVE_NONBLOCKING",
  "hybrid_generator_criterial": false,
  "new_external_generator_required": true,
  "adapter_semantics_audit_all_five_targets": true,
  "active_count_ece_definition_repaired": true,
  "equivalence_posterior_serialization_required": true,
  "noninferiority_margin_nats_per_target_token": 0.01980262729617973,
  "gate4_parallel_authorized": true,
  "gate5_parallel_authorized": false,
  "tournament_block_retained": [3684000, 3689999],
  "one_requalification_only": true
}
```
