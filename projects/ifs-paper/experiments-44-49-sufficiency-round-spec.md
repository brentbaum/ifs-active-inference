# Experiments 44–49 specification: the sufficiency-bet round

**Status:** Proposed handoff specification; not yet piloted or preregistered
**Date:** 2026-07-24
**Implementation home:** `projects/emergence-suite/continuous/`
**Paper home:** `projects/ifs-paper/` (`draft-v11-theory.md` as of the 2026-07-23 revision cycle)
**Starting points:** Experiment 43 (`experiment-43-ifs-bundle-guided-inquiry.md` and its implementation), the unified relational agent (Experiments 39–42), the dyad model, and the deadlocked descent rebuild recorded in Appendix B.

## 1. What this round is for

The 2026-07-23 revision cycle left the manuscript making six explicit confessions or promises. Each experiment below is aimed at exactly one of them. The mapping is the round's contract: a result (positive or negative) flips a named Appendix A entry and revises a named manuscript site, and nothing else.

| Exp | Retires or tests | Manuscript site | Appendix A entry |
|---|---|---|---|
| 44 | Identity revision is stipulated, not derived; redescription supplied, not discovered; the unburdening do-over has no computational anchor | §8, §9, §10 Limits | "Identity revision as a posterior consequence"; "Redescription as the change operator"; "Unburdening as Bayesian model reduction" |
| 45 | Assembly, recruitment, and hybrid formation are stated, not compared | §10 orthodoxy | "Formation substrate (§10)" |
| 46 | §1's sufficiency wager has no computational face; its losing condition has no concrete signature | §1, §10 boundary paragraph, Appendix A preamble | (new entry) |
| 47 | The five §8 trust claims are theoretical: refusal discrimination, permission ≠ trust, transfer by inferred variable, the hope-merchant route, conditional rupture asymmetry | §8, §10 secondary predictions | "Protector trust (§8)"; "Trust asymmetry (§8)" |
| 48 | Exiling is derived conditionally in prose only; starvation vs. confirmation is a stated distinction with no realized regimes | §5 | "Derived exiling (§5)" |
| 49 | Protective descent deadlocked; protectors-first ordering is asserted, not derived | §5, §8, §9, §10 Limits | "Derived protective descent (§§5, 8)" |

A clean success anywhere is a construction result: an existence proof or scope condition inside an authored model. Nothing in this round can establish a clinical effect, a biological mechanism, or the ontology of parts. Failures are retained beside their replacements, as before.

## 2. Shared discipline

- **Pilot, freeze, confirm.** Each experiment pilots on ten worlds, freezes its design and criteria, then runs twenty fresh worlds. Every numeric threshold below is **provisional until freeze**; the pilot may move a threshold, but only before the confirmatory block opens, and the change is logged.
- **Matched controls.** Every advantage claim requires a control matched on capacity, evidence budget, and marginals wherever the design permits. The matched-marginal lesson of Experiments 40–42 applies: an ablation that changes the marginals tests the wrong thing.
- **Register guards.** *Configural* is a statistical adjective for within-bundle organization; *relational* is interpersonal only. *Witnessing* names the exile encounter clinically and context-held activation formally; protector encounters are *befriending*. New this round: *organization* means the four-element bundle, its couplings, its precisions, and the field profile, operationalized in advance; *carrier* means independently parameterized substrate. No measure may be renamed across that boundary after results arrive — this is the manuscript's own fix-in-advance constraint applied to its simulations.
- **Record.** All designs, criteria, freezes, and results append to the Appendix B record in program order.

## 3. Experiment 44 — Context-split redescription, with revision derived

### 3.1 The question

Can the system, by its own model comparison, prefer splitting an old belief into past-valid and present-valid hypotheses over globally down-weighting it or relearning it cue by cue — and does identity-root revision then follow as a posterior consequence, with no stipulated update rule anywhere in the loop?

The temporal framing raises the stakes: retrieval is context-split enacted (*that happened then; the part is here now*), so this experiment tests the paper's central clinical mechanism, not a side candidate.

### 3.2 Plain-language thesis

> The frozen inference is not argued down or overwritten. It is re-indexed to the context in which it was true, and the root revises because the re-indexed model explains the present better.

### 3.3 Architecture

Extend the Experiment 43 bundle with a latent context variable

\[
c \in \{\text{then}, \text{now}\}
\]

with a learnable transition prior. Three model classes compete as explanations of change, scored by variational evidence with complexity accounted:

1. **Global down-weight:** one belief, precision reduced everywhere.
2. **Cue-local relearning:** per-cue parameters, no shared structure.
3. **Context-split (redescription):** the old parameters indexed to `then`, fresh parameters indexed to `now`, with the root shared.

Root revision is measured as the posterior over the identity root \(g\), updated **only through inference**. The stipulated update rule of the repeated-contact model appears nowhere. The witnessing arm supplies a context-held evidence stream (part channel active, broad field), reusing the Experiment 43 machinery.

### 3.4 The do-over arm

After root revision has begun (and, in a mismatched sub-arm, before), append an imaginal counterfactual ending to the frozen episode: observations generated under the `then` context but terminating in the non-catastrophic outcome, flagged as internally generated (no new external evidence enters the world).

This arm has a built-in negative control that is also a clinical prediction: applied **before** sufficient root revision, the do-over should fail — the reduced model loses the comparison and the full model is reinstated (the burden returns). If the do-over helps whenever applied, the arm has found a suggestion mechanism, not completion, and should be reported as such.

### 3.5 Controls

- Matched exposure without context inference (single fixed context).
- Reversed-graph control (Experiment 41 style).
- Complexity matching across the three model classes (parameter count and prior entropy).
- **Selectivity control (essential):** worlds with no true context structure. Redescription must *lose* there. A change operator that wins everywhere is a free parameter, not a discovery.

### 3.6 Provisional criteria

1. Context-split selected in ≥ 16/20 worlds with true context structure, and in ≤ 4/20 without.
2. Held-out context-sensitive behavior predicted better by the split model by a margin ≥ 0.05 (scale set at pilot) at comparable complexity.
3. Root revision under witnessing, derived purely by inference, reproduces the qualitative ordering of the stipulated model (witnessing ≈ open-field informational ≫ regulation-only ≈ narrowed contact) without any arm-specific hand assignment.
4. Do-over after revision shortens time-to-reduction by ≥ 20% vs. witnessing-only at matched evidence; do-over before revision fails (reduction reverses) in ≥ 16/20 worlds.

### 3.7 What failure means

If global down-weight wins held-out prediction, redescription loses its candidate-mechanism status and §6/§10 revise accordingly. If revision cannot be derived, the stipulation confession in §9 stands and the tournament result stays interpretive. Either failure is publishable inside the record.

## 4. Experiment 45 — The formation-substrate triad

### 4.1 The question

Are assembly, recruitment, and hybrid formation actually distinguishable, at matched capacity, by the signatures §10 claims — formation efficiency, cross-part interference, and what remains after selective reduction?

### 4.2 Plain-language thesis

> The three stories about what enters the phase disagree about how parts form and what melting leaves behind, even when they agree about everything in between.

### 4.3 Architecture

Three formation models over the same worlds, capacity-matched (parameter count and prior entropy):

1. **Assembly:** uniform latent-cause prior; the bundle is constructed at the freeze.
2. **Recruitment:** a small set of persistent prepared carriers, each an innate prior over affect and policy; the freeze selects the best-fitting carrier and binds the burden to it.
3. **Hybrid:** explicit carrier-plus-coupling factorization; prepared priors supply affect/policy structure, learned couplings supply individuation.

Worlds vary in whether their statistics align with the prepared repertoire (prepared worlds) or not (arbitrary worlds).

### 4.4 Measures

- Formation sample efficiency, prepared vs. arbitrary configurations.
- Interference when one prepared carrier is recruited by two part-formations.
- Taxonomy: cluster structure of resulting bundles across worlds.
- **Post-reduction residue:** after selective reduction, decompose what persists into carrier-attributable (affective/policy priors) and coupling-attributable (biographical) components. The hybrid predicts the dissociation; the pure models predict residue of only one kind.

### 4.5 Controls

- Shuffled-preparation control: prepared modes misaligned with world statistics (recruitment's advantage must vanish).
- Capacity matching audited, not assumed.

### 4.6 Provisional criteria

1. Recruitment beats assembly on formation efficiency in prepared worlds by ≥ 20% sample reduction, and the advantage vanishes (≤ 5%) in arbitrary and shuffled worlds.
2. Interference signature present under recruitment/hybrid (shared-carrier formations degrade each other by a measurable margin), absent under assembly.
3. The residue dissociation appears in the hybrid (both components present, separable by ablation) and not in either pure model, in ≥ 16/20 worlds.

### 4.7 Honesty clause

The carriers are authored. This experiment tests **distinguishability of the models**, not which is true of people. Its result licenses exactly one manuscript sentence: the three formation hypotheses are (or are not) separable in principle by the signatures §10 names.

## 5. Experiment 46 — The wager-violation construction

### 5.1 The question

What does it look like when the sufficiency wager loses? §1 bets that nothing beneath the phase does additional explanatory work for therapeutic change. Appendix A records that this bet has no test. The right construction is not a demonstration of invariance — if the transition law reads only organization variables, invariance is true by fiat. The right construction builds a world where the bet is **false**, and characterizes the signature.

### 5.2 Plain-language thesis

> A bet you cannot lose is not a bet. Here is the loss, in miniature, so the empirical prediction knows what it is looking for.

### 5.3 Architecture

Recruitment-style carriers (from Experiment 45) given one **transition-relevant** parameter: coupling plasticity under corrective evidence. Construct agent pairs whose pre-intervention organization is matched to numerical precision — same bundle contents, couplings, precisions, and field profile — but whose carriers differ in plasticity. The organization-matching procedure is itself a deliverable; if matching is impossible, that is a finding about the partition, not a nuisance.

Arms:

- **(a) Carrier-inert world:** transition law reads organization only. Expected: intervention-response invariance across carriers.
- **(b) Carrier-active world:** plasticity differs by carrier. Expected: matched-organization pairs diverge under identical witnessing-style interventions.
- **(c) Machinery audit:** verify, analytically and by ablation, that the existing suite's update equations read only organization variables — i.e., that the program to date has been organization-only without anyone having checked.

### 5.4 Measures and criteria (provisional)

1. Arm (a): divergence within tolerance (≤ 0.02 on the revision-trajectory metric fixed at pilot) — the null behaves.
2. Arm (b): carrier-moderated divergence ≥ 0.10 with organization matching verified to audit standard — the loss signature exists and is detectable.
3. Power curve: minimum carrier effect detectable as a function of organization measurement noise. This connects the construction to the feasibility of any future clinical test and is the experiment's most useful export.

### 5.5 Interpretation guard

Arm (b) is not evidence the wager is false of people. It is the pattern the wager stakes itself against, made concrete — and the demonstration that the losing condition is coherent, detectable, and not absorbable once organization is fixed in advance. Report it in exactly those terms.

## 6. Experiment 47 — Protector trust

### 6.1 The question

Do the §8 trust claims compute? A protector is modeled with forecasts over three linked questions — what happens if I permit this; who carries responsibility if I relax; what policy is generating the request — plus a representable counterfactual future. Trust is the forecasts; permission is a policy decision under them.

### 6.2 Plain-language thesis

> Trust is what the protector has learned to expect. Permission is what it decides to risk. The two can come apart, and the ways they come apart are the clinical phenomena.

### 6.3 Architecture

A protector bundle (Experiment 43 form) extended with:

- an outcome forecast over contact (flooding/collapse vs. tolerated);
- a co-protection variable (expected system competence if the protector relaxes);
- a **partner model**: a latent over the contact policy's type (instrumental vs. relational), inferred from interaction;
- a **stakes parameter** entering the permission decision but not the posteriors;
- a policy set containing a representable counterfactual future (see 6.4d).

Permission is computed as a decision under the posteriors plus stakes; it is never identified with any posterior.

### 6.4 Arms

**(a) Refusal discrimination.** Two contact policies identical except after refusal: one remains, one pressures or withdraws. The policies are observationally equivalent until a refusal episode occurs, by construction. Test: partner-type discrimination accuracy is at chance in no-refusal worlds and above chance only after refusal episodes. (Refusal with a pressuring response is also discriminating — it reveals the instrumental type; what *trust* requires is refusal met by remaining. Keep discrimination and trust-growth as separate measures.)

**(b) Permission ≠ trust.** Matched posteriors, different stakes → different permission decisions. A regression of permission on posterior alone must leave systematic stakes-attributable variance.

**(c) Transfer by inferred variable.** Identical outcome evidence delivered in two inferential framings: one supporting only a local contact forecast, one supporting a shared cause (*the system can bear this*). Willingness change across untested situations should track the inferred variable, not the evidence label.

**(d) Hope merchant.** Introduce the counterfactual future — exile healed, mandate unnecessary — as an addition to the protector's policy-comparison set, with all evidence streams unchanged. Measure permission shift with posteriors flat. Control: the same future *without room for the protector* (job ends → protector discarded). The obsolescence variant should shift permission less, or negatively.

**(e) Conditional rupture asymmetry (optional, cheap).** A diagnosticity parameter on failure attribution. The one-misattunement-outweighs-one-success asymmetry should appear only when failures are read as diagnostic of partner type; a repair inexplicable under the old model should outweigh smooth successes under the same parameter.

### 6.5 Provisional criteria

1. (a) Discrimination at chance (±0.05) without refusal; ≥ 0.80 after two refusal episodes.
2. (b) Stakes-attributable permission variance ≥ 0.15 at matched posteriors.
3. (c) Transfer tracks inferred variable in ≥ 16/20 worlds; evidence-label regression adds nothing beyond it.
4. (d) Permission shift ≥ margin (pilot-set) with flat posteriors; obsolescence variant ≤ half that shift.
5. (e) Asymmetry present iff diagnosticity high; repair effect exceeds k smooth successes at pilot-set k.

## 7. Experiment 48 — Exiling emergence

### 7.1 The question

Does exclusion from awareness and relationship emerge as the selected protection exactly when attentional/relational policies are the cheapest reliable option — and do the two consequence regimes the manuscript distinguishes (starvation and confirmation) both exist and separate?

### 7.2 Plain-language thesis

> Exile is not assumed and not universal. It is one solution among several, chosen when it is cheapest, and its cost is paid by the excluded part's oldest expectation.

### 7.3 Architecture

A vulnerable bundle with a relational prior (*alone with this*), plus a protective repertoire with per-policy cost and reliability parameters varied across worlds: attentional/relational exclusion, hypervigilant monitoring, internal attack, suppression–flooding oscillation. The vulnerable part presses toward activation (contact attempts at a base rate). A **registration channel**, toggleable, determines whether suppressed contact attempts are represented by the vulnerable bundle as rejection.

### 7.4 Measures and criteria (provisional)

1. Policy selection tracks the cost structure: exclusion emerges in ≥ 16/20 worlds where it is cheapest-reliable and in ≤ 4/20 where a competitor is; each alternative appears in its own favorable regime.
2. Starvation regime: registration off → the aloneness prior is static (no update either direction) during exclusion.
3. Confirmation regime: registration on → the prior strengthens; ablating registration removes the strengthening.
4. Both regimes realized across the confirmatory block, and separable by the registration toggle alone.

## 8. Experiment 49 — Dyad-gate coupling and derived descent

### 8.1 The question

The clean rebuild deadlocked: a gated part was never contacted, so its gate could not relax. The manuscript's diagnosis is that permission cannot be earned from inside the policies that prevent contact — the dyad's learned scaffolding must couple to the gate. Experiment 47 builds the coupling mechanism. Does outside-in descent now emerge with no authored access rules?

### 8.2 Plain-language thesis

> The gate does not open because the system pushes on it. It opens because the protector producing it changes its forecast, and the protector's evidence arrives through a relationship the dyad made available.

### 8.3 Architecture

Minimum two-layer stack: a protector (Experiment 47 form, all routes active) guarding a vulnerable bundle (Experiment 48 form). The gate is the protector's permission decision — no separate gate object. The dyad model's learned precision scaffolding enters the protector's evidence stream: co-regulation shapes the field within which the partner model and outcome forecasts update.

### 8.4 Arms and controls

- **Coupled:** dyadic scaffolding feeds the protector's evidence. Expected: permission earned, contact achieved, descent proceeds.
- **No dyad:** deadlock should reproduce (this is the replication of the recorded failure).
- **Decoupled:** scaffolding present but severed from the protector's evidence stream. Deadlock should persist — this is the arm that shows coupling, not mere dyadic presence, carries the result.
- **Authored-access baseline** for calibration against the historical construction.

### 8.5 Provisional criteria

1. Contact with the vulnerable bundle achieved in ≥ 16/20 coupled worlds; ≤ 2/20 in no-dyad and decoupled worlds.
2. Ordering: protector permission rises before vulnerable-bundle root revision begins, in every world where descent occurs (the §10 secondary prediction, now measured rather than asserted).
3. No arm requires an authored access rule at any point.

### 8.6 What failure means

If descent deadlocks even when coupled, the obstruction is deeper than the coupling hypothesis, and §10's Limits gains a sharper statement of what is missing. That is a better outcome than an authored success.

## 9. Dependencies and order

- 44 is standalone (builds on 43). Run first; its derived-revision machinery is reusable by 49.
- 45 → 46: the wager-violation construction reuses 45's recruitment carriers.
- 47 → 49: descent depends on the trust machinery. 48 is independent of both and can run in parallel.
- Suggested order: 44 ∥ 45 → 46 ∥ 47 → 48 ∥ 49.

## 10. What this round cannot do

No experiment here tests the cross-cultural taxonomy prediction, anything descended from the cut screening-off prediction, loving contact's identification, or legacy burdens — the first three are clinical-empirical, the last is unmodeled by design. If a construction in this round appears to bear on one of them, that is scope creep, and the register guards in §2 exist to catch it.
