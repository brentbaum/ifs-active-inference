# Simulation Specification: v11 — The Emergence Suite

**Date:** 2026-07-09
**Status:** Design document. Nothing here is built. Supersedes `simulation-v9-spec.md` (old repo) as the program of record.
**Serves:** `draft-v11-theory.md` §9 (currently stubbed) and §10 (empirical predictions), plus the interactive explainer.
**Prior art:** v10 program at `~/dev/personal/projects/ifs-active-inference/` (Julia, hand-rolled active inference); BLT hyper-model reproductions at `projects/beautiful-simulation/` (RxInfer.jl).

---

## 1. Why a new program

The v10 sims were built for a different paper. v11 became a **derivation paper**: the exile/protector taxonomy, the protectors-first ordering, and the witness-before-unburdening rule are claimed to *fall out* of the architecture. A simulation in which E_t is a dial, the taxonomy is wired into the factor labels, and the A-matrices are tuned until the cascade appears does not under-serve that claim — it contradicts it. Two v10 designs additionally conflict with v11's ontology:

- **v2's Channel 5** (witnessed self-state, precision gated by inverse capture) is the "channel opens" mechanism §7 now explicitly disavows: *"No channel opens; nothing is switched on."* The relational evidence must arrive through the same falling-gain mechanism as everything else.
- **v9/v4's gate as hidden factor** contradicts §5: *"The gate… is not a part at all. Whether access is open, closed, or partial is simply the net output of whichever protector policies are running."* Gate-as-inferred-state is deferred to the sequel; the v11 sims must not smuggle it back in.

What survives from v10:

| Asset | Verdict |
|---|---|
| **v3 transfer design** (shared `d_self`, cue-local `d_threat` Dirichlet banks; matched H1/H2 training fit; transfer as sole discriminant; η_self=0 ablation) | **Keep.** Adversarially hardened; correct epistemology. Becomes the skeleton of Sim 3. |
| v3 adversarial protocol (pre-registered criteria + adversarial tests before running; external-model design review) | **Keep as process.** Applies to every sim below. |
| v2 cascade model, Channel 5 | Retire (mechanism disavowed). |
| v4/v9 gate-as-factor model | Retire (ontology conflict). Presence-as-observation survives as the relational channel concept. |
| Polarization v2 | Park. §10 explicitly defers polarization ("described, not derived"). |
| Chamberlin figure patterns (`figure-inspiration.md`) | Keep for all figures. |
| `beautiful-simulation` RxInfer stack (joint-categorical HMMs, 3-layer GCV/HGF, config/seed/metadata pipeline) | **Keep as substrate.** Sim 6 is built directly on it; its output contracts (summary.json, status.json, per-seed CSV, git-hash metadata) are the engineering standard for the suite. |

---

## 2. Design constitution

These are hard constraints. A sim that violates one is out of the program regardless of how good its figures look.

**R1 — Nothing scripted, everything grown.** Every IFS construct the paper derives must *emerge* from three ingredients: precision dynamics, structure learning (latent-cause spawn / BMR prune), and one depth variable. No factor may be named `exile`, `protector`, or `gate` in the generative model. Taxonomy, ordering, and timing are **readouts**, applied post hoc by fixed classification rules stated before the run.

**R2 — One mechanism.** E_t enters inference in exactly one place: the effective-precision balance (§7's π_eff / λ_eff). No sim may give depth a second entry point (a gate, a channel switch, a bonus term). Everything downstream is consequences.

**R3 — Structural vs. effective precision.** Effective precision (fast, reversible, E_t-modulated) and structural precision (Dirichlet concentration; the spawn/prune axis) are separate quantities in every sim, separately logged. *Witnessing ≠ melting*: E_t opens the regime; the melt is the slow structural follow-on that runs only while held. Any sim where flipping E_t instantly changes structure has a bug by definition.

**R4 — Pre-register, then attack.** Per sim, before any run: success criteria with thresholds, named adversarial tests (including at least one designed to *break* the headline claim, in the spirit of v10's fake-Channel-5 test), and the falsifiable empirical prediction the sim licenses. Outcomes labeled `support / weak_support / null / falsified` in the result bundle.

**R5 — Matched controls.** Every headline contrast ships with the control that could kill it: the reversed-root (H2) architecture, the real-danger environment (witnessing must *preserve* adaptive fear), and the dissociation condition (attenuation reduces disturbance without upstream revision). Controls run on identical seeds and axes.

**R6 — Magic numbers are debts.** Every hand-set constant is listed in a per-sim `magic-numbers.md` with either a derivation, a sensitivity sweep, or an explicit IOU. (Lesson from v10: `rho_bind=0.995` -style tuning choices must be auditable.)

**R7 — Paper register.** Per §1 and §9: the sims are existence proofs and prediction generators, not confirmations. No result may be described as confirming the theory; the confirmatory tests are the §10 studies.

---

## 3. The suite

Seven simulations in three tiers. Tier A discharges the §9 stub. Tier B turns §5/§8 derivations into emergent results. Tier C is the synthesis.

Framework note: Tier A sims 1–3 are discrete POMDPs with Dirichlet cross-trial learning (port of the v10 Julia core or pymdp — decide at build time; the v3 skeleton already exists in Julia). Sims 4–5 extend the same core. Sim 6 is RxInfer (extends `beautiful-simulation`). Sim 7 composes.

---

### Sim 1 — The freezing phase diagram
*"Not every fear becomes a part." (§4)*

**Model.** A latent-cause active inference agent (Gershman/Niv-style CRP structure prior). On each trial the agent either assimilates prediction error into an existing cause (gradient update of that cause's Dirichlet banks) or spawns a new cause when posterior predictive probability falls below the CRP threshold. Learning rate scales with arousal (HGF-style volatility coupling: acute overwhelm ≈ maximal write). The policy space includes overt actions (approach, flee, appease) and one covert action: attenuate (turn down likelihood precision — the mental action of Sandved-Smith et al. 2021).

**Manipulated variables (the sweep).**
- **Overwhelm** ω: magnitude of precision-weighted PE relative to what existing causes can absorb.
- **Control** κ: steepness of the EFE gradient across overt policies (κ→0 = flat landscape, nothing is expected to help).

**Emergent regions (predicted, not wired).** (i) ordinary fear learning — existing cause updates, revisable later by ordinary evidence; (ii) part formation — spawn of a new cause, written at high structural precision, encoded while reflexive precision is collapsed (in Tier A, collapsed reflexivity is an arousal-linked *input*; Sim 6 makes it emergent); (iii) the shutdown corner — ω extreme, κ≈0: attenuation is the EFE-optimal remaining policy.

**The three formation traits as measurements, not assumptions:** spawn event logged (trait 1); reflexivity state at write time logged (trait 2); post-formation epistemic sampling of the spawned cause's cues logged — it should approach zero because avoidance is EFE-optimal (trait 3: write without test).

**Slow kinetics run.** A trajectory of chronic low-ω, low-κ trials (ambient misattunement, no reportable event) crossing the same phase boundary by count accumulation. Plotted as a path on the same diagram as the single-strike trajectory.

**Headline figure.** The (ω, κ) plane with the emergent phase boundary; two life-paths overlaid (one afternoon / one childhood) entering the frozen phase from different directions.

**Pre-registered criteria.**
- S1.1 A connected region of the plane exists where spawning occurs and the spawned cause resists later ordinary corrective evidence (< 10% structural revision after N disconfirming trials), while a distinct region shows ordinary revisable learning (> 80% revision).
- S1.2 The boundary is jointly determined: high ω with high κ does **not** spawn (the chased child who reached the gate).
- S1.3 The slow path crosses the boundary with no single trial exceeding the acute region's per-trial PE.
- S1.4 The shutdown corner selects attenuate without attenuation being preferred anywhere else.

**Adversarial tests.**
- A1.1 Threat-magnitude-only sweep (κ held moderate): if part-like structures form from intensity alone, §4's two-condition claim fails in the model.
- A1.2 CRP concentration sensitivity: the boundary must move smoothly, not exist only at a knife-edge hyperparameter.
- A1.3 Shuffle control: randomize trial order in the slow path; accumulation should still cross (freezing by use is order-insensitive) — if it doesn't, the slow route is an artifact of sequence.

**Licensed empirical predictions.** Controllability moderates part formation independent of threat intensity (joins Maier & Seligman controllability literature). Formation is representationally discontinuous — a new cause, not a drifted parameter — with a hunt-able signature in learning curves (sudden onset of context-specific avoidance) vs. gradual acquisition.

---

### Sim 2 — The hysteresis loop
*"What froze in isolation melts in relationship." (§§7–8) — plus the melt's controls.*

**Model.** One agent, one formed bundle (imported from a Sim 1 spawn, seeds shared): frozen self-state root (relational content: *alone-with-this*) with dependent threat-meaning and policy banks. Cross-trial Dirichlet learning. E_t enters per R2 only. Relational evidence is an observation modality carrying *how the shown material is met* — always available, always truthful, never gated (v3 principle); what varies is only the weight inference gives it, via C_t. Melting is **actual Bayesian model reduction**: at intervals, compare full model (bundle coupling present) against reduced model (coupling pruned, competences retained) by the analytic Friston et al. 2017 free-energy difference over the learned counts. Prune when the reduced model wins.

**The loop.** Drive structural precision up (threat trials), then attempt to bring it down under four regimes on matched evidence budgets:
1. **Informational**: corrective facts about the cue (*safe dogs, endlessly*), low E_t.
2. **Contact under capture**: relational evidence present, E_t low (C_t high).
3. **Dissociative quiet**: attenuation policy active — evidence itself turned down.
4. **Witnessing**: relational evidence under held E_t (C_t low, part active).

**Headline figure.** Structural precision vs. cumulative corrective evidence, four trajectories: three flat lines and one that steps down discontinuously — a literal hysteresis diagram (the path down is not the path up). First-passage markers at the BMR event.

**The unburdening probe.** Trigger the BMR comparison *early* (prompted reduction while the burden still contributes accuracy): the reduced model must lose and the full model persist — *the part takes the burden back*. Trigger after sufficient witnessed contact: the prune runs. The witness-fully-before-unburdening rule as a free-energy comparison, not etiquette.

**Pre-registered criteria.**
- S2.1 Regimes 1–3 produce < 10% of witnessing's root revision on matched evidence counts (three failures of the three conditions, §7).
- S2.2 The melt is discrete: > 50% of the total structural drop occurs within a window ≤ 10% of the melt phase (prepared slowly, completes suddenly).
- S2.3 Prune is selective: competence banks survive at ordinary precision (decoupling, not deletion); post-melt the role re-organizes under Self-led policy (compulsivity drops, competence persists).
- S2.4 Premature-prompt probe: early invited reduction fails; late succeeds; failure tracks remaining evidential work (correlation with residual accuracy contribution), not prompt count.
- S2.5 **Real-danger control:** in an environment where the cue is genuinely dangerous, witnessing preserves adaptive fear (the relational error revises *alone-with-this*, not the true contingency).

**Adversarial tests.**
- A2.1 Content-swap (the v10 killer, re-armed): replace the relational modality's content with matched-precision informational content. If the melt still runs, C3 fails in the model — the mechanism would be "any evidence under depth," not relational error at the root.
- A2.2 E_t-flip test (R3 enforcement): raise E_t for one trial and drop it. Structural precision must be unchanged; only effective precision moves. Witnessing ≠ melting.
- A2.3 BMR threshold sweep: the discreteness of the melt (S2.2) must survive reasonable prior-odds settings, not be an artifact of one threshold.

**Licensed empirical predictions.** Deep change under witnessing is stepwise (sudden-gains literature: gains should cluster, prepared by preceding within-session process markers). Premature unburdening fails in the take-it-back pattern, and failure probability tracks unwitnessed material, not ritual quality (§10 already states this; the sim gives it a quantitative shape).

---

### Sim 3 — The generalization gradient
*v3 rebuilt as the killer experiment. (C1+C3; §9 contrasts 1–3)*

**Model.** The v3 skeleton, upgraded: shared self-state Dirichlet bank `d_self`; cue-local threat banks `d_threat(c)` over a **similarity continuum** of cues c (not one cat — a parametric family graded by feature overlap with the trained cue). H1 architecture: self-state at the root, threat meanings conditioning on it. H2 control: threat at the root, self-state downstream. Matched training fit enforced before any probe (the two architectures must be observationally equivalent on the treated cue — the discriminant is transfer only).

**Contrasts (= the §9 stub, verbatim).**
1. **Cascade:** under witnessing, revision order is root-first — self-state crosses its revision threshold before threat meaning, policy last. Logged as first-passage times per bundle element.
2. **Reversal:** identical protocol on H2 eliminates the cascade and the transfer.
3. **Transfer:** identity-level revision produces a graded generalization curve across the cue continuum; threat-level revision (exposure regime) stays cue-bound. Leakage check: untrained `d_threat(c)` banks unchanged — transfer flows through `d_self` only.

**Headline figure.** Two transfer curves over cue similarity — one traveling, one flat — with the H2 panel showing no gradient at any depth. Identical axes across panels (Chamberlin rules).

**Pre-registered criteria.** Port v3's seven criteria; add: S3.1 the E_t threshold for transfer is sigmoid and **emergent** (no sigmoid anywhere in the parameterization — per the §9 stub); S3.2 the cascade ordering is strict at high E_t and absent under matched exposure; S3.3 η_self=0 ablation kills transfer (necessity), and η_threat=0 does not (non-sufficiency of threat learning for the signature).

**Adversarial tests.** A3.1 v3's full battery re-run. A3.2 Similarity-confound test: transfer must track *structural* similarity through the root, not raw perceptual overlap — include a perceptually similar cue with a different self-state linkage; it should transfer less than a perceptually distant cue sharing the root.

**Licensed empirical predictions.** The paper's signature trial (§10): witnessing vs. matched exposure on one treated fear; measure (a) revision order via instruments separating self-state ("I feel like my younger self around X") from threat meaning ("X is dangerous to me now") from behavioral policy, and (b) the transfer gradient to untreated structurally similar fears. Witnessing: root-first order + gradient. Exposure: uniform movement + cue-bound change.

---

### Sim 4 — The trust ledger
*Protectors-first as an optimal policy, not a rule. (§5, §8)*

**Model.** A stack grown, not built: run Sim 1's formation machinery through a schedule that produces an exile plus 2–3 protector-classified causes (breakthrough-spawned and slow-accumulated — the firefighter/manager kinetics of §5, applied as post-hoc readout labels per R1). Each protector cause carries, among its banks, a **relational prior about Self** — Dirichlet counts over what contact yields (the §8 referent of *trust*). The gate is **computed, not represented**: access to the layer beneath = net output of currently-running protector policies (R1; honors §5's ontology). A Self-process (high-E_t regime) selects whom to contact by expected free energy over the stack.

**What must emerge (not be scripted).**
- **The clinical ordering:** contacting the exile directly is EFE-suboptimal while protector forecasts are unrevised; the optimizer discovers outside-in descent.
- **Thickening:** force the direct route (probe): the flood is itself an overwhelm — Sim 1's spawn condition fires and a *new* layer forms. The stack thickens exactly when the sealing fails (§5).
- **Trust asymmetry:** one misattunement trial (contact met badly) sets the relational bank back super-linearly relative to the per-trial gain of attuned contacts — because it confirms thousands of old counts, each good contact is one count against them.
- **Methods-not-mission:** protector policy banks update continuously from world feedback while the mandate (self-state root) receives nothing through the protector's own operation — the polished manager with the four-year-old mandate, as a logged dissociation between bank update rates.

**Headline figure.** The descent: gate state (computed) per layer over sessions, protector trust curves, exile revision onset — showing permission *preceding* contact preceding root revision, with the forced-direct-route panel showing spawn-and-thicken instead.

**Pre-registered criteria.** S4.1 EFE ranks protector-contact above exile-contact until trust banks cross a threshold, with no ordering term in the objective. S4.2 Forced direct access triggers spawn (thickening), not revision. S4.3 Asymmetry coefficient (setback per rupture / gain per attuned contact) > 5 across seeds. S4.4 Habit control: a policy-only avoidance (no spawned who — sub-boundary in Sim 1 terms) yields to practiced counter-conditioning that leaves the protector unmoved (§10's habit–protector line).

**Adversarial tests.** A4.1 Remove the relational banks: if descent ordering still emerges, it's an artifact of stack topology, not trust. A4.2 Preference-shaping check: verify no C-matrix term encodes "protectors first" implicitly.

**Licensed empirical predictions.** Willingness-to-allow-contact precedes exile-level revision in IFS session data and shows no such ordering under exposure (§10). Rupture events set back measured trust super-linearly. Avoidances that answer the probe with a voice resist skills training; those that answer with nothing yield to it.

---

### Sim 5 — The dyad
*Borrowed depth, actually simulated. (§6, §8) — and the self-like part's first model.*

**Model.** Two coupled active inference agents. **Client:** the Sim 2/3 architecture; its E_t is not free but collapses under activation (arousal-linked, as at formation). **Therapist:** a second agent whose observable behavior carries its regulation state. The coupling: among the client's observation modalities is co-regulation evidence — how the other is holding what the client's system is showing — and the client's *expected available depth* is partly inferred from it. (Formally: the client holds beliefs about its own E_t capacity; therapist-regulation observations are evidence for those beliefs. This is scaffolding in the literal sense — external evidence standing in for a hyper-prior the system cannot yet hold alone.)

**Conditions.** (1) Regulated therapist. (2) Dysregulated therapist (own activation leaking into the co-regulation channel). (3) **Fluent-but-threatened**: parts-language content delivered from a body in threat — the content channel says depth, the regulation channel says none. (4) No-therapist self-practice at varying baseline capacity (the owned-depth endpoint).

**What must emerge.** Client C_t falls (and revision runs) only in (1) and, at sufficient baseline, (4). Condition (3) fails *and is detectably different from (1) inside the client's inference* — the client's system weights the regulation channel over the content channel. That is the **self-like part signature** (§6, §10: depth reported without reflexivity precision under activation), given its first mechanical form — here as a property of the therapist-agent; the full self-like part (the client's own bundle that models being-Self) is flagged as the sequel's problem.

**Headline figure.** Client capture index over a session under the four conditions; the (1)-vs-(3) pair as the money contrast — same words, different bodies, different outcome.

**Pre-registered criteria.** S5.1 Revision in (1) ≫ (2), (3) on matched protocols. S5.2 The (3)-failure is driven by the regulation channel (ablating it makes (3) ≈ (1) — which would be the *wrong* clinical result, so the ablation is the mechanism check). S5.3 Borrowed-then-owned: repeated (1) sessions raise the client's standalone depth capacity (the hyper-prior updates), so later (4) succeeds where early (4) failed.

**Adversarial tests.** A5.1 Content-only therapist (perfect words, zero regulation signal): must fail. A5.2 Regulation-only therapist (no parts-language content): should partially succeed — if it fully matches (1), content does nothing and the sim overclaims against technique; log honestly either way.

**Licensed empirical predictions.** Dyadic physiological synchrony (e.g., HRV coupling) under client activation predicts in-session revision events better than intervention content. Therapist regulation under load predicts outcomes better than technique fluency. Client-side: early-treatment gains depend on therapist presence; late-treatment gains transfer to self-practice.

---

### Sim 6 — E_t made honest: the reflexive hyper-model
*The technical contribution. (§3, §6, §7; Laukkonen, Friston & Chandaria's Φ married to the parts machinery.)*

**Model.** Stop dialing E_t; **infer it**. Extend `beautiful-simulation`'s three-layer stack (hyper-state → precision-state → content) so the top layer is a hyper-model over the precision balance of the parts machinery: its state is precision-on-the-model's-own-precision — reflexivity precision as an inferred quantity, per the BLT Φ construct. Arousal enters as evidence at the middle layer (volatility), and the key dynamic must *emerge*: acute arousal collapses the top layer's posterior precision (collapsed reflexivity), so bundles written under overwhelm are written while the hyper-layer is dark — transparent encoding as a property of the run, not a stipulation. Recovery of hyper-layer precision under safety = opacification. Capture, the C_t index, and the depth threshold are all read off the one inferred variable.

**Why this is Tier B ambitious.** Structure learning inside a hyper-model is not off-the-shelf in RxInfer or pymdp; coupling a CRP spawn process (Sim 1) to a continuous GCV hierarchy is genuine research. Fallback staging: 6a — hyper-model over a *fixed* bundle (no spawning), demonstrating emergent collapse/recovery and the emergent sigmoid; 6b — the coupled version feeding Sim 7.

**Headline figure.** One variable's biography: hyper-layer precision collapsing at the formation event (the write happening in the dark), flat through years of avoidance, scaffolded upward in the dyad, held through witnessing — with capture, opacification, and the revision window all annotated on the same trace. The paper's most elegant circle — *the variable that fails at formation is the one therapy restores* — as a single time series.

**Pre-registered criteria.** S6.1 The E_t↔revision threshold is sigmoid and emergent (v10 found ≈0.6 with a parameterized sigmoid; here no sigmoid may appear anywhere in the spec). S6.2 Collapse under arousal is dose-dependent and recoverable (state, not trait). S6.3 Bundles written during collapse acquire the frozen signature (Sim 1's traits) *because of* the collapse: yoked control with arousal but clamped hyper-precision must produce ordinary revisable learning — the discriminating test that overwhelm freezes *via* reflexivity collapse, not via intensity.

**Adversarial tests.** A6.1 The clamp control above is itself the adversarial test of §3's collapsed-reflexivity claim — if clamping doesn't rescue revisability, the paper's invariant is wrong in the model. A6.2 Identifiability: show hyper-layer precision is recoverable from behavior (simulated inference on simulated data), else the construct is doing no observable work.

**Licensed empirical predictions.** Meta-awareness degrades lawfully with arousal (dose-response within-subject, not a trait difference). Depth-restoration interventions transfer across content domains (the variable is content-general). Peri-traumatic loss of reflexive awareness predicts part-formation (intrusive identity-level sequelae) better than event severity.

**Full design: Appendix A** (core operationalization, substrate decision, collapse mechanisms, the circularity resolution, derivational targets, staging, and the elegance upgrades).

---

### Sim 7 — One simulated life
*The synthesis and the explainer's marquee. Build last.*

**Model.** A single agent = Sim 1's formation machinery + Sim 6's inferred depth + Sim 2's BMR + Sim 4's stack dynamics + Sim 5's dyad, run through a scripted **environment** (the only scripted thing: the world, never the mind): ambient misattunement early; one acute overwhelm event; years of avoidance; a breakthrough flood; chronic management; then therapy — dyadic sessions, trust accumulation, descent, witnessed contact, relational error at the root, prune, and the generalization probe after. Nothing in the model is labeled exile/manager/firefighter; classification rules (formation kinetics + position in the gating graph) are fixed before the run and applied as readouts.

**Controls.** The full life re-run on the H2 (threat-at-root) architecture: same world, no cascade, no descent, no transfer — §9's reversal at biographical scale. And a resilient-world control: same child, one caregiver who comes — the boundary never crossed, the stack never built.

**Headline figure.** The org chart of a psyche growing from three ingredients and melting in reverse order of formation — formation events, stratification, descent, and the post-melt transfer probe on one timeline. If it works, this is the figure the paper is remembered by, and the explainer's central toy: the E_t slider flips the regime instantly; the structural melt integrates only while held.

**Pre-registered criteria.** S7.1 The classification rules recover the IFS taxonomy from the grown structure (blind labeling by a rater given only the rules and the logs). S7.2 Melt order inverts formation order (outside-in). S7.3 The two controls fail in their predicted, distinct ways.

**Adversarial test.** A7.1 Seed robustness: the qualitative biography (spawn → stratify → descend → melt → transfer) must appear in a majority of seeds, not one curated run.

---

## 4. Falsifiable experiments the suite licenses (the Edmundo/Ruben list)

Collected from the per-sim predictions; each names its sim and the §10 claim it sharpens.

1. **Controllability moderation** (Sim 1): part-formation (identity-level sequelae) tracks perceived control at encoding, independent of threat severity.
2. **Formation discontinuity** (Sim 1): part-forming learning shows sudden representational onset, not gradual acquisition.
3. **Sudden gains under witnessing** (Sim 2): deep change is stepwise; gains cluster after within-session process markers (witnessed contact), and are preceded by protector-relaxation markers.
4. **Premature unburdening** (Sim 2, §10): failure probability tracks unwitnessed material, not ritual quality; failure mode is burden return.
5. **Revision order** (Sim 3, §10): self-state instruments move before threat-meaning instruments under witnessing; uniform movement under matched exposure.
6. **Generalization gradient** (Sim 3, §10): transfer to untreated structurally-similar fears under witnessing; cue-bound change under exposure; transfer tracks structural (root-shared) similarity, not perceptual similarity.
7. **Permission-precedes-revision** (Sim 4, §10): willingness-to-allow-contact precedes exile-level change in IFS process data only.
8. **Rupture asymmetry** (Sim 4): trust setbacks from misattunement are super-linear vs. gains from attuned contact.
9. **Habit–protector line** (Sim 4, §10): voice-answering avoidances resist skills training; nothing-answering avoidances yield to it.
10. **Dyadic synchrony** (Sim 5): physiological co-regulation under client activation predicts in-session revision better than intervention content; therapist regulation beats technique fluency.
11. **Arousal–meta-awareness dose-response** (Sim 6): reflexive awareness degrades lawfully with arousal within-subject.
12. **Peri-traumatic reflexivity** (Sim 6): loss of reflexive awareness at encoding predicts part-formation better than event severity.

---

## 5. Priority matrix and R&D plan

### 5.1 Every work item, ranked

Two scores per item. **Strength** = how much the item adds to *draft-v11 itself* (discharging §9, hardening a derivation, upgrading a claim's status) — strength to the sequel or the explainer is noted but doesn't move the rank. **Risk** = probability the item fails or balloons (LOW = recipe exists; MED = new composition of known parts; HIGH = design uncertainty; RESEARCH = no published recipe).

| Rank | Item | Strength to v11 | Risk | Basis |
|---|---|---|---|---|
| 1 | **Sim 3 — generalization gradient** | Critical — discharges §9 contrasts 1–3 and the signature prediction; the paper can cite the program on this alone | LOW | v3 skeleton exists and survived adversarial review; upgrade is a continuum probe + emergent-sigmoid check |
| 2 | **D2/U1 — revision requires representation** (math first) | Critical if it lands — elevates C2 from claim to theorem; would upgrade §7/§8 prose ("a distinction §8 derives") | MED (pencil) | Pure derivation over BMR mechanics; attempt on paper before any code — a week of math, not a quarter of engineering |
| 3 | **D1 — tilt equation as mean-field message** (math first) | High — the paper's only equation becomes a derived limit; β, γ stop being free parameters | MED (pencil) | Expected-log-precision exponentiation is standard; the work is doing it carefully for this factorization |
| 4 | **Sim 1 — freezing phase diagram** | High — §4's two-condition claim and slow-kinetics route as results; feeds Sims 2, 4, 7 | LOW-MED | CRP latent-cause spawning is published machinery; arousal-scaled LR is HGF-standard |
| 5 | **Sim 2 — hysteresis + BMR melt** | High — completes the §9 stub (melt, discreteness, premature-unburden, real-danger + dissociation controls) | MED | Analytic BMR is published; the four-regime matched-budget design needs care; content-swap test is the killer to survive |
| 6 | **Sim 6a-discrete (Stages 0–2) — inferred E_t** | High — makes the paper's central variable honest; collapsed reflexivity emergent; D3 sigmoid; witnessing-as-mental-policy | MED | Sandved-Smith reproduction retires the oscillation risk in Stage 0; semantics relabel is bounded |
| 7 | **U2 — Self as universal attractor** | Med-high — §6's doctrine recoveries become dynamical facts; basin map is a paper-grade figure | LOW-MED | Phase-portrait analysis of a small system; cheap once 6a-continuous exists |
| 8 | **U3 — four-timescales figure** | Medium — organizing frame; one figure + one paragraph, possibly for the paper itself | LOW | Pure synthesis; no new runs |
| 9 | **Sim 4 — trust ledger** | Medium — beyond the stub; §5/§8 orderings emergent; strongest *new* clinical predictions (7–9) | MED | Composition of Sim 1–2 parts; risk is in keeping the gate computed-not-represented under EFE |
| 10 | **Sim 6a-continuous (Stage 3) — Φ-bridge** | Medium — Ruben-legible artifact; carries U2; strengthens the lineage argument, not a §-claim | LOW-MED | Mostly relabeling `beautiful-simulation` Sim 3 + one coupling |
| 11 | **Sim 6b — spawn-in-hyper-model + clamp control** | High *if* it works — the causal test of §3's invariant | RESEARCH | No published recipe for CRP proposals scored inside hyper-model free energy; v12-grade problem |
| 12 | **Sim 5 — dyad** | Medium for v11 (§10 defers the dyad: "described, not derived") — high for the sequel; self-like-part signature is the v11-relevant fragment | MED-HIGH | Two coupled agents is novel composition; the fluent-but-threatened condition is the part worth having early |
| 13 | **Sim 7 — one simulated life** | Medium for v11 (synthesis; §9 doesn't need it) — the explainer's marquee and the paper's memorable figure if it works | HIGH | Pure composition risk; only mature parts compose |

*(U4 — model inversion on session data — and U5 — hyper-prior burden — were cut by author decision 2026-07-09 and do not appear in the plan.)*

Reading the matrix: the top of the list is dominated by two *pencil* items (ranks 2–3). The single highest-leverage week in the program is math, not code — if D1/D2 land, every downstream sim instantiates theorems instead of illustrating claims, and the paper's §7–8 get stronger before a single run.

### 5.2 The R&D plan

**Phase 0 — Foundations (≈2 weeks, partly parallel).**
- **P0.1 Framework decision** (blocks everything): port v3's Julia discrete core vs. pymdp vs. discrete-in-RxInfer. Decision criterion: Sim 7 needs one substrate, and Sim 6 needs RxInfer regardless — so the question is whether the discrete core joins it. Timebox to days, decide, log in the decision log.
- **P0.2 The math sprint (D1 + D2 on paper).** No code. Success = a derivation note per target (`d1-tilt-derivation.md`, `d2-bmr-opacity.md`) with either the result or the precise obstruction. Obstructions are findings.
- **P0.3 Stage-0 reproduction** of Sandved-Smith et al. 2021 (retires the second-order-precision risk).
- *Gate G0:* framework chosen; D1/D2 status known.

**Phase 1 — Minimum viable §9 (the paper's floor).**
- **P1.1 Sim 3 rebuild** (continuum probe, H1/H2, emergent-sigmoid check, v3 adversarial battery + A3.2).
- **P1.2 Sim 1** (phase diagram, slow-kinetics path, three-traits logging).
- **P1.3 Sim 2** (four-regime loop, BMR melt, unburdening probe, controls; content-swap test). If D2 landed in P0.2, implement the melt *as* the derived gate — Sim 2 and Sim 6 begin converging here.
- *Gate G1:* §9 stub is writable. **Write it.** The paper stops depending on the rest of the program at this gate.

**Phase 2 — Make E_t honest (the technical contribution).**
- **P2.1 Sim 6a-discrete Stage 1** (IFS semantics, inference-face collapse, one-variable biography, D3 numerically).
- **P2.2 Stage 2** (mental action; witnessing as learnable policy — one figure, one paragraph, per the scope guard).
- **P2.3 U3 figure** (four timescales — assemble from Phases 1–2 outputs; consider for the paper).
- *Gate G2:* E_t inferred, collapse emergent, sigmoid status known. Candidate standalone methods paper.

**Phase 3 — Beyond the stub (choose by what G2 revealed).**
- **P3.1 Sim 4** (trust ledger — the best new-predictions-per-effort in the suite).
- **P3.2 Sim 6a-continuous + U2 basin map** (the Ruben bridge; send with the derivation notes and the circularity question).
- *Gate G3:* §10's process predictions (7–9) have simulated shape; lineage artifact delivered.

**Phase 4 — Frontier (only mature parts compose).**
- **P4.1 Sim 5** (dyad; the fluent-but-threatened condition first — it's the v11-relevant fragment).
- **P4.2 Sim 6b** (spawn-in-hyper-model; clamp control). Explicitly research — timebox exploration, and a negative result on the clamp is reported, not tuned away.
- **P4.3 Sim 7** (one simulated life; preregister taxonomy readout rules before the run).

**Kill criteria (standing).** Any sim that can't pass its adversarial battery after one redesign cycle gets reported as `falsified`/`null` and the dependent items re-scoped — the v10 lesson (v2's beautiful wrong figures) is the thing this plan exists to not repeat.

## 6. Open technical questions

- **Framework unification:** Tier A discrete core in Julia (port v3) vs. pymdp vs. rebuilding discrete-in-RxInfer to share infra with Sim 6. Decide before Sim 1; Sim 7 needs one substrate.
- **CRP-in-hyper-model coupling** (Sim 6b): no published recipe; candidate approaches — discrete spawn events proposing model expansions scored by the same free-energy comparison BMR uses in reverse (the spawn↔prune symmetry of the frozen-process insert, taken literally as one structure-learning axis). If this works it is a v12-level contribution on its own (flagged in the outline's open theory questions).
- **Trust-bank formalism** (Sim 4): per-layer relational Dirichlet banks are the §10-deferred "per-layer trust variables" — building them here means the sequel's machinery gets prototyped early; keep the paper's §9 silent on them per scope.
- **Classification-rule preregistration** (Sim 7): the taxonomy readout rules must be fixed and published before the flagship run, or R1 is violated at the finish line.

---

## Appendix A — Sim 6 design: the reflexive hyper-model

*(2026-07-09. Worked design for the suite's technical centerpiece. Everything here is subordinate to R1–R7.)*

### A.1 Core operationalization: reflexivity as a channel

The single load-bearing decision: **make reflexivity a modality, and make E_t the precision on it.**

Alongside the exteroceptive modalities, the agent has a reflexive modality `o_self`, generated from the system's own global configuration — which latent cause currently dominates inference, and how strongly. The generative model contains a likelihood mapping from "my current configuration" to this inner observation. Then:

- **E_t = the inferred precision of that mapping.** High: *a part of me is afraid* is available as data (the state is had). Collapsed: the channel is dark; the bundle operates without being represented.
- **Transparency/opacity become mechanical.** Transparent = bundle active while `o_self` precision is collapsed (functioning as the model, invisible in it). Opacified = same bundle registered through a precise reflexive channel (an object in the model). §3's "written while no one was watching" becomes literal: formation is a write that occurs while the channel is dark.
- **C_t becomes a readout, not a formula.** Capture is however much of inference the bundle owns given the precision balance the hyper-layer sets — nothing bespoke remains.

This is Laukkonen & Chandaria's recursive-sharing loop rendered as a modality, with their reflexivity precision as its gain.

### A.2 Substrates: two implementations of one design

| | Discrete (program substrate) | Continuous (Φ-bridge) |
|---|---|---|
| Foothold | Sandved-Smith et al. 2021: 3-level POMDP, level 2 sets level-1 likelihood precision, level 3 sets level-2 precision; **mental action** = policies over precision allocation. Code exists; tiny state spaces. | `beautiful-simulation` Sim 3: 3-layer GCV stack (`h → z → x`) in RxInfer — already an inferred hyper-model lacking only semantics. |
| What changes | Relabel + extend: level 1 = bundle-vs-context inference on cue trials; level 2 = the precision balance; level 3 = depth states. Composes natively with Sims 1–3 (Dirichlet banks, EFE, policies). | Let `h` govern the balance between a bundle-prior stream and a present-evidence stream instead of generic observation noise. Mostly relabeling + one coupling. |
| Role | Feeds Sims 5, 7; carries the clamp control and 6b. | The artifact Ruben can read as a direct extension of the LFC Φ formalism. |

Build both, matched phenomena, report as alternative formalizations of one loop.

### A.3 Making the collapse emergent: two faces, staged

- **Inference face (build first, low risk).** HGF-style: a burst of unmodeled precision-weighted PE raises inferred volatility, which widens posteriors upstream — including the hyper-layer's. Confidence about one's own precision landscape collapses *because the meta-model is being violated*, not because a dial turned. Dose-dependent and recoverable for free.
- **Policy face (the prize).** Precision allocation as **mental action** selected by EFE. Under acute threat, EFE favors throwing precision at first-order survival channels and none at the reflexive channel — introspection has no pragmatic value while the dog is closing. Collapse is *optimal*; the agent does it to itself, rationally, and the freeze follows from the optimality. Corollary: **witnessing is a learnable mental policy** — holding reflexive precision under activation is an action, initially EFE-dominated by threat allocation, made viable by changed evidence. "Borrowed before owned" gets its mechanism: dyadic co-regulation evidence changes which mental policy is optimal until the client's own model supports the witnessing policy unscaffolded. (Ships as one figure and one paragraph until Sims 1–3 are done — scope-creep guard.)

### A.4 The circularity decision

An observation generated from the agent's own posterior is not a standard generative model. Two principled resolutions; we assign one per substrate and flag the divergence for Ruben early:

- **Process-side reflexivity (discrete build):** the generative *process* includes the agent's actual configuration; `o_self` is emitted from that, and the agent holds an ordinary likelihood model of it. The loop is real but crosses the process/model boundary the way proprioception does (the metacognition literature's de facto choice).
- **Empirical-prior reflexivity (continuous build):** no observation — the hyper-layer enters as a top-down precision message (empirical prior on the balance); E_t is that message's confidence. Theoretically cleaner, closer to LFC's Φ; but §7's content-face ("the part registers who is here with it") needs the channel form, so this variant carries the regime-face only.

The two-formalizations-of-one-loop divergence is itself worth a paragraph in any writeup.

### A.5 Derivational targets (pre-registered aims, not hopes)

- **D1 — The paper's equation as a message.** π_eff = r_t·π_part·e^(−βE_t) vs λ_eff = λ_ctx·e^(+γE_t) should *drop out*: under mean-field message passing, the precision a lower level uses is the expected log-precision under the hyper-posterior, and expectations of log-precisions exponentiate into exactly this multiplicative-tilt form. Target: identify β, γ as properties of the likelihood mapping, not free parameters. If it lands, §7's only equation is a derived limit of the hyper-model.
- **D2 — Revision requires representation (the elegance centerpiece; see A.7/U1).** Derive C2's punchline — *only an opacified prior can revise* — from the mechanics of model reduction itself: BMR computes ΔF over a component, and that computation needs a posterior over "this bundle as hypothesis" as its substrate. A transparent bundle — functioning as the reality model, not represented within it — offers BMR nothing to evaluate. Depth doesn't *permit* revision by rule; it *constitutes* the object revision needs. Joint Sim 2/Sim 6 result: the melt machinery and the depth machinery are one machine.
- **D3 — Emergent sigmoid.** C_t against inferred depth must come out sigmoid with no logistic anywhere in the spec (posterior mixing over depth states should produce it). If it doesn't, that is a reportable result about the theory, not a tuning failure.

### A.6 Stages

| Stage | Content | Deliverable | Risk retired |
|---|---|---|---|
| 0 | Reproduce Sandved-Smith et al. 2021 | Working 3-level precision model | Second-order precision oscillation found now, not in Stage 3 |
| 1 | 6a-discrete: IFS semantics, inference-face collapse only | One-variable biography trace; opacification as `o_self` posterior sharpening; D3 check | Core phenomena exist at all |
| 2 | Mental action (policy face) | Collapse-as-optimal figure; witnessing as learnable policy | Feeds Sim 5 |
| 3 | 6a-continuous on RxInfer stack | Continuous phase portrait; the Φ-bridge; U2's basin analysis | Ruben-legible artifact |
| 4 | 6b: couple to Sim 1 spawning | **Clamp control** (S6.3): identical overwhelm, depth posterior clamped high — if frozen bundles still form, §3's invariant is wrong in the model and we report that | The only stage with an unsolved problem (spawn proposals scored inside hyper-model free energy — the spawn↔prune axis; v12 material) |

### A.7 Elegance upgrades

Ranked answers to "more elegant, more ambitious, more direct." U1–U2 are adopted as pre-registered aims; U3 is the suite's organizing frame. (Two further candidates — model inversion on session data, and the hyper-prior burden / "a part about Self" — were considered and **cut by author decision, 2026-07-09**: out of scope for this program, not merely deferred.)

- **U1 — Revision requires representation** (= D2). The deepest available unification: opacification gates BMR *mechanically*, because reduction needs the bundle represented as a hypothesis to compute its ΔF. C2 stops being a claim the sim illustrates and becomes a theorem the sim instantiates. If D1 and D2 both land, the paper's two central moves (the tilt and the melt-gate) are both *derived* from one hyper-model.
- **U2 — Self as a universal attractor.** §6 says Self is a regime: architectural, undamageable, needing access not development. Model it directly as a dynamical fact: compute the phase portrait of the depth–capture system and show a distinguished fixed point — the configuration where no bundle dominates and the reflexive loop is self-sustaining (accurate self-modeling keeps volatility estimates low, which keeps depth cheap: the loop pays for itself). *Everyone has Self* = the attractor exists across the parameter space (architecture, not achievement). *Cannot be damaged* = attractors aren't contents. *Occlusion* = capture as a competing metastable basin, with Sim 2's hysteresis re-read as basin-hopping. Deliverable in Stage 3: the basin map, with the 8 C's region literally a basin of attraction.
- **U3 — Four timescales, one variable.** The suite-level frame: the entire paper is precision moving on one structure at four timescales — effective precision (fast: capture/witnessing, within-moment), mental policy (medium: the witnessing skill, within-treatment), structural precision (slow: freezing/trust/melting, across encounters), structure itself (slowest: spawn/prune, across a life). One organizing figure for the suite and possibly for the paper: the same variable, four clocks. IFS is what precision dynamics looks like when it happens to a self-model.

### A.8 Failure modes, named now

Second-order precision oscillation (Stage 0 catches it); the sigmoid may not emerge (D3 reported honestly per R4); identifiability — E_t must be recoverable from behavior via simulated inference on simulated data (A6.2), else the construct does no observable work; the clamp control may *fail to rescue* revisability, falsifying §3's invariant in-model (that outcome gets reported, not tuned away); and Stage 2 scope creep (guard stated in A.3).
