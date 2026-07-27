# V2.3.2 — Counterfactual attribution and safety-behavior maintenance: adopted plan

**Status:** Adopted 2026-07-27 (design per GPT-5.6 Pro recommendation, approved by Brent). V2.3 and V2.3.1 remain frozen with their sealed failures standing; this is a new mechanism informed by them, not a confirmatory repair.
**Decision:** proceed with V2.3.2; do not weaken C1 to activation-dependent maintenance. Encode the causal question — *was there no danger, or was danger present and prevented by the action?* — never "avoidance is evidence for threat."

## 0. Pre-mechanism: the no-evidence neutrality audit (on frozen v2.3.1)

Before any new mechanism: verify the model-evidence bookkeeping. On slices carrying no observation that distinguishes transient from persistent candidates, posterior structure odds may change only through the declared structure-transition model. Specifically: a masked outcome has Bayes factor exactly 1 between structures; an equally-predicted outcome likewise; repeated masked outcomes do not decay the persistent model; any decay is traceable to the declared Markov transition or an actual likelihood difference. This separates **informational starvation** (odds plateau; only structural dynamics move them) from **evidence against persistence** (transient predicts the safe observations better). Only the second motivates the attribution mechanism; if the first currently causes decay, that is a bookkeeping defect to correct first (instrument repair, logged).

## 1. Core mechanism

New latents: D_t (would catastrophe occur without protection), A_t (engage vs avoid/protect), P_t (would the action prevent it, Bernoulli(η)), Y_t = D_t·[1 − 1(A_t=avoid)·P_t], M_t (outcome observable/attenuated/censored), H_E (action causally irrelevant vs causal), η (efficacy under H_E=causal). The agent observes A_t, available outcomes, cues, possibly relief — never the counterfactual D_t when prevention succeeds. For safe outcomes under avoidance, p(Y=0 | avoid, θ, η) = 1 − θ(1−η): at η=1 the observation is uninformative about threat; at η=0 it directly disconfirms. That is the formal face of attribution.

- **Spike-and-slab on efficacy existence** (the V2.2.1 representational lesson): exact mass on "this action has exactly no causal effect."
- **Causal structure candidates:** irrelevant; preventive; (open-assay extension: attenuating); masking as an explicit observation mask. 
- **Interventional likelihood** p(Y | do(A), H, η), never p(Y, A | H, η) — a model must not confirm itself by causing the agent to choose its predicted action.
- **Environmental inference separated from policy learning** (relief/negative reinforcement moves policy, never threat) — this is the later hook for the habit–protector boundary.
- **Derived attribution readout** p(K_t=1 | o, A) with K_t = 1(D=1, A=avoid, P=1, Y=0): a pure readout from the joint posterior; no authored K→threat update. The persistent model and the prevented-catastrophe interpretation share D_t; support for the latter naturally un-disconfirms the former.

## 2. The claim structure (C1 split)

- **C1a — Formation.** Overwhelming, poorly controllable experience under collapsed recursive integration can favor a persistent identity-level organization over a transient event model.
- **C1b — Maintenance (conditional).** Effective avoidance can protect a threat organization from disconfirmation by censoring the relevant counterfactual or by attribution of safe outcomes to effective protection; irrelevant or information-preserving safety behavior should not protect it.
- **C1c — Strengthening.** Only with additional diagnostic evidence (near-miss cues, observed action-contingent transitions, demonstrated efficacy); mere non-occurrence under avoidance is insufficient.

Primary maintenance result: **protection from extinction** (ΔH_avoid > ΔH_response-prevention, both possibly negative), not active strengthening. Empirical anchors: avoidance-during-extinction protection of threat beliefs, its dependence on precluding disconfirmatory information, and exposure-with-safety-behavior studies showing substantial belief reduction — hence conditionality, no universal avoidance bonus.

## 3. Scoring: two separately scored subclaims

- **V2.3.2-F (formation calibration):** open balanced population over theory variables (cumulative overwhelm precision, inferred controllability, reflexive integration, real danger, prevalence, structure prior) with schedule dimensions as nuisance; profile scoring (recovery accuracy, Brier/ECE, control contrast, false formation, continuity bound, theory-variable monotonicity) replacing a single absolute floor — as a NEW prospective criterion set; the C-V23b calibration miss stands unreinterpreted.
- **V2.3.2-M (counterfactual maintenance):** factorial over threat base rate × efficacy (exactly-zero/partial/high) × observation mode (full/masked/attenuated) × protocol (closed-loop/forced-engage/yoked-sham/relief-only) × efficacy knowledge × context stability; paired arms share latent D_t and P_t so the evaluator holds exact counterfactual truth the agent never sees.

Gate 1 (ten semantic proofs: masked BF=1; η=0 equivalence; η=1 non-disconfirmation; engagement disconfirms; A cannot directly update threat/structure; relief moves policy only; exact spike mass; threat–efficacy correlation under pure avoidance; forced-engage breaks the confound; enumeration tolerance). Gate 2: recovery where identifiable; in pure-avoidance worlds require calibrated NON-identifiability (coverage, threat–efficacy correlation, entropy floor, no false certainty) rather than point recovery. Gate 3: eight open causal assays (protection-from-extinction, partial-safety, sham no-bonus, censoring-only, relief-only, adaptive avoidance, counterfactual probe, context transfer) with SESOIs fixed from prior-predictive attainable ranges BEFORE sealed challenges are authored. Gate 4: the seven-lesion table separating reduced sampling, causal attribution, and negative reinforcement. Gate 5: cumulative V2.0–V2.3.1 plus the anti-authoring checklist (no avoidance→persistence factor, no K→root update, no outcome-label branch, irrelevant-action safety reduces threat, masked outcomes create no evidence, relief never touches threat, all counterfactual readouts posterior-derived).

## 4. Sealed challenges (two independent bundles, hashes committed before implementation)

- **C-V23c-F:** formation generalization on a novel schedule family (chronic+acute, changing controllability, intermittent restored broadcast, real vs apparent danger, novel ordering); recovery, calibration, false formation, continuity, monotonicity.
- **C-V23c-M:** counterfactual maintenance in a novel world (one effective, one sham, one partially protective action; a context switch changing efficacy; evaluator-scheduled response-prevention probes; high- and low-threat worlds); tests 1–8 per the adopted recommendation, including protection ordering, sham no-bonus, relief-only dissociation, calibrated uncertainty under pure avoidance, probe identification, context-specific efficacy, and no inherited-stage regression.

## 5. Stop rule

V2.3.2 earns exactly one prospective round. After C-V23c: clean pass → V2.4 unblocks; quantitative miss with correct causal ordering → failed prospective result, may narrow effect-size claims; failure to distinguish prevention/masking/irrelevance → C1 is weakened; any need for a direct avoidance bonus, root increment, or challenge-specific branch → architecture failure. No V2.3.3 unless the challenge reveals another missing representational class statable independently of the desired result.

## 6. Execution order

1. Neutrality audit on frozen v2.3.1 (§0) — report before anything else.
2. V2.3.2 public contract + frozen analysis plans for both subclaims (SESOIs from prior-predictive) + dummy bundles. STOP for evaluator sealing.
3. Evaluator seals C-V23c-F and C-V23c-M; hashes committed.
4. Implementation; gates 1–5; freeze; reveal; run; verdicts stand as written.
