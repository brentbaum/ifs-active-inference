# Simulation v11 — Implementation Plan (Phases 0–2)

**Date:** 2026-07-09. Tickets for Codex. Spec of record: `simulation-v11-spec.md` (read §2 design constitution and the relevant sim section before starting any ticket; Appendix A for T2.x).
**Code home:** `projects/emergence-suite/` in this repo (create on T0.5). Old v10 code (read-only reference): `~/dev/personal/projects/ifs-active-inference/library/`.
**Gates:** G0 = T0.1–T0.5 done. G1 = T1.1–T1.3 done → §9 stub writable. G2 = T2.1–T2.3 done.

## Global conventions (all tickets)

- **R1–R7 of the spec are binding.** In particular: no factor named `exile/protector/gate` in any generative model (R1); E_t enters only via the effective-precision balance (R2); structural (Dirichlet counts) and effective (E_t-modulated) precision are separate, separately logged quantities (R3).
- **Preregistration:** each sim ticket writes `criteria.yaml` (thresholds + adversarial tests) and gets it committed **before** the first full run. Results labeled `support | weak_support | null | falsified` per criterion. Null/falsified outcomes are shipped, not tuned away.
- **Run contract** (from T0.5): every run emits `summary.json`, `status.json`, `metadata.json` (seed, git hash, config), per-seed CSV, and figures. Every hand-set constant is listed in the sim's `magic-numbers.md` with derivation, sensitivity sweep, or explicit IOU (R6).
- **Seeds:** ≥ 20 per condition unless stated; report mean + CI bands, never single curves.
- **Definition of done** per ticket = all success criteria checked in the ticket's closing note, including the ones that failed.

---

## Phase 0 — Foundations ✅ COMPLETE (2026-07-09; all five tickets Codex-executed, orchestrator-reviewed, committed)

**Gate G0 outcomes:** framework = Julia v10-core port (memo in `projects/emergence-suite/decisions/`); D1 landed exactly under log-precision messaging (β/γ = map slopes; natural-precision caveat constrains T2.1); D2 landed architecturally + conditionally-inferentially (T1.3 must use reflexively-accessible counts for a derived gate); Sandved-Smith reproduced with stability envelope (A(2) precision [0.5,8.0], LR ≤ 0.8, horizon ≤ 5; provisional if T2.1 changes the update scheme); harness live at `projects/emergence-suite/suite/` (33 tests green; run + criteria-evaluator contract verified). Review fixes applied during acceptance: both T0.1 spikes' BMR helpers corrected (count-averaging → pooled-evidence tying + canonical prior-swap); canonical BMR now lives in the suite's `BMR` module, pinned to D2 demo values.

### T0.1 — Framework decision spike
**Depends:** none. **Timebox: 3 days.**
**Task:** Decide the discrete substrate for Sims 1–4: (a) port of v10 Julia core (`library/src/active_inference/`), (b) pymdp, (c) discrete-in-RxInfer. Build the *same* spike in each viable candidate: 2-factor POMDP (2×2 states, 2 modalities), cross-trial Dirichlet learning on A and B, 4 policies scored by EFE, 200 trials.
**Score on:** (1) cross-trial Dirichlet learning ergonomics; (2) feasibility of dynamic state-space growth (CRP spawn adds a state to a factor mid-run — this is the likely discriminator); (3) analytic BMR over Dirichlet counts (Friston et al. 2017 ΔF formula implementable in <50 lines); (4) wall-clock for a 20×20 condition sweep × 20 seeds (target < 2 h on laptop); (5) interop with the RxInfer stack Sim 6 requires regardless.
**Success criteria:**
- [ ] `decisions/framework-memo.md` with benchmark table on all 5 axes, a decision, and the runner-up's disqualifier.
- [ ] Spike code for ≥ 2 candidates runs and learns (posterior entropy on true A-matrix decreases over trials).
- [ ] Decision logged in `draft-v11-outline.md` decision log.

### T0.2 — D1 derivation: the tilt equation as a mean-field message
**Depends:** none. **Math ticket; deliverable is markdown + one notebook.**
**Task:** In a model where a hyper-layer holds a posterior over depth (discrete depth states d with beliefs q(d), each d implying log-precisions for the bundle-prior stream and present-evidence stream), derive the effective precisions a lower level uses under mean-field VMP. Target result: π_eff = r_t·π_part·e^(−βE_t), λ_eff = λ_ctx·e^(+γE_t) with E_t an expectation under q(d) and β, γ identified as properties of the depth→log-precision mapping (its slope/spacing), **not free parameters**.
**Success criteria:**
- [ ] `derivations/d1-tilt-derivation.md`: assumptions stated, derivation complete **or** the precise obstruction stated (which factorization assumption fails, what the correct message is instead).
- [ ] Numeric check: notebook comparing message-passing effective precision vs. the closed-form tilt across a grid of q(d); agreement < 1% error where the derivation claims exactness.
- [ ] One-paragraph statement of what the result licenses the paper to say (or not say).

### T0.3 — D2 derivation: revision requires representation
**Depends:** none. **Math ticket.**
**Task:** Formalize: BMR computes ΔF for a reduced model relative to a full model *over the posterior of the component being reduced*; show that when a bundle is transparent (its reflexive representation carries no precision — no posterior over "this bundle as hypothesis" is maintained), the reduction comparison lacks its substrate — and derive the quantitative form: ΔF's informativeness (e.g., its magnitude or discriminability) as a function of reflexivity precision on `o_self`. Target: "only an opacified prior can revise" as a property of the ΔF computation, with a threshold or graded form.
**Success criteria:**
- [ ] `derivations/d2-bmr-opacity.md`: formal statement + proof/derivation **or** precise obstruction.
- [ ] Toy numeric demo: a 2-state bundle with Dirichlet counts where BMR ΔF is computed at high vs. collapsed reflexivity precision; the collapsed case shows degenerate/uninformative ΔF as derived.
- [ ] Explicit note on the consequence for Sim 2's design: is the melt gate *derived* (implement in T1.3) or still *imposed* (flag in T1.3's magic-numbers)?

### T0.4 — Reproduce Sandved-Smith et al. (2021)
**Depends:** none.
**Task:** Reproduce the 3-level discrete parametric-depth model (perceptual states; attentional states setting level-1 likelihood precision; metacognitive states setting level-2 precision; mental action as policy over precision allocation). Use their published equations/code as ground truth; reimplement in the T0.1-chosen framework if feasible, else in Python/Julia standalone.
**Success criteria:**
- [ ] Qualitative reproduction: level-2 state inference visibly modulates level-1 precision; mental action switches attentional state; figures matching the paper's key dynamics (attention capture and return).
- [ ] `reproductions/sandved_smith_2021/NOTES.md` documenting: where second-order precision updates oscillate or diverge, parameter ranges that are stable, and any deviation from the paper needed to make it run.
- [ ] Stability envelope stated (the input T2.1 needs).

### T0.5 — Suite harness and run contract
**Depends:** T0.1.
**Task:** Scaffold `projects/emergence-suite/`: config-driven runner (YAML per experiment), seed management, the run contract (summary/status/metadata JSON + per-seed CSV + figures), `criteria.yaml` schema with `support|weak_support|null|falsified` evaluation, and a `magic-numbers.md` template. Port the output-contract patterns from `projects/beautiful-simulation/` rather than inventing new ones.
**Success criteria:**
- [ ] A dummy experiment runs end-to-end producing the full contract.
- [ ] Criteria evaluator: given `criteria.yaml` + `summary.json`, emits per-criterion labels automatically.
- [ ] CI-runnable test (`just test` or equivalent) covering config load, seed reproducibility (same seed → identical summary), and contract completeness.

---

## Phase 1 — Minimum viable §9 ✅ COMPLETE (2026-07-09; Gate G1 passed — §9 written into draft-v11-theory.md)

**Outcomes:** all three sims accepted after one redesign cycle each. Sim 3: 16 support / 1 weak (matched-fit 0.102) / 1 null (A3.2 gap +0.038, correct direction below margin); redesign fixed lobotomized H2 → genuine reversed root, and decoupled perceptual_similarity from root_coupling. Sim 1: 7 support / 2 falsified-with-interpretation (revisable-region threshold arithmetically unreachable at these budgets — criteria lesson; attenuation localizes to a low-control band scaling with ω, a boundary curve not a box); redesign replaced closed-form readouts with real trial loops; slow path crosses without spawning in all seeds. Sim 2: 14/14 support with the D2-derived melt gate (no imposed E_t block) after de-scripting the witnessed_contact flag (observations route by likelihood content; relational weight = channel effective precision under E_t); content-swap does not melt (C3 survives); emergent nuance: capture banks relational evidence (~34% weight) that BMR cannot access until depth rises.

### T1.1 — Sim 3: generalization gradient
**Depends:** T0.5. **Spec: §3 Sim 3.** Reference implementation: v10's `ifs_simulation_v3.jl` + `simulation-v3-spec.md` (port the design, not the code style).
**Task:** Rebuild v3 in the suite framework. Two hidden-factor architecture: shared self-state (Dirichlet bank `d_self`) + cue-local threat banks `d_threat(c)`. **Cue continuum:** K ≥ 5 cues parameterized by feature overlap with the trained cue, plus one **structural-confound cue** (perceptually near, root-distant) for A3.2. H1 (self at root) and H2 (threat at root) variants. E_t enters per R2 only; relational modality always on, always truthful. Conditions: witnessing (high E_t), matched exposure (low E_t), E_t sweep for the sigmoid readout. Log per-element first-passage times (self-state, threat meaning, policy).
**Preregister in `criteria.yaml`, then run. Success criteria:**
- [ ] **Training parity:** H1 vs. H2 log-evidence difference on treated-cue training < preregistered ε (else the transfer discriminant is confounded — stop and fix).
- [ ] **Cascade (S3.2):** under witnessing, first-passage order self→threat→policy in > 90% of seeds; no consistent order under matched exposure.
- [ ] **Transfer:** H1+witnessing shows a monotone transfer gradient over the continuum; exposure and H2 show flat/cue-bound profiles (preregistered effect-size thresholds).
- [ ] **Leakage check:** untrained `d_threat(c)` banks statistically unchanged — transfer flows through `d_self` only.
- [ ] **Ablations (S3.3):** η_self = 0 kills transfer; η_threat = 0 does not kill the signature.
- [ ] **Emergent sigmoid (S3.1):** transfer-vs-E_t is sigmoid by preregistered fit criterion, with **no logistic/sigmoid function anywhere in model code** (assert via code review note in closing).
- [ ] **A3.2:** structural-confound cue transfers less than a perceptually-distant root-sharing cue.
- [ ] v3's original adversarial battery re-run and labeled.

### T1.2 — Sim 1: freezing phase diagram
**Depends:** T0.5. **Spec: §3 Sim 1.**
**Task:** Latent-cause agent: CRP prior over causes; spawn when posterior predictive of all existing causes < CRP threshold; per-cause Dirichlet banks; learning rate scaled by arousal; policy space = {approach, flee, appease, **attenuate** (covert: lowers likelihood precision)}; EFE policy selection. Sweep overwhelm ω × control κ on ≥ 15×15 grid (ω = PE magnitude vs. best-cause assimilation; κ = EFE-gradient steepness across overt policies). Log per cell: spawn events, reflexivity-at-write (arousal-linked input in this tier), post-formation epistemic sampling rate, later-revisability (structural revision % after N disconfirming trials). **Slow-kinetics run:** chronic low-ω/low-κ trial sequence plotted as a path on the same plane.
**Success criteria (S1.1–S1.4 + adversarial):**
- [ ] Connected frozen region exists: spawned causes with < 10% later revision; distinct revisable region with > 80%.
- [ ] Joint determination: high-ω/high-κ cells do **not** spawn.
- [ ] Slow path crosses the boundary with max per-trial PE below the acute region's minimum.
- [ ] Attenuate selected in the ω-extreme/κ≈0 corner and nowhere else (policy-selection heatmap).
- [ ] Three traits logged as measurements: spawn (trait 1), write-time reflexivity (trait 2), near-zero epistemic sampling post-formation (trait 3).
- [ ] **A1.1:** ω-only sweep at moderate κ produces no frozen region (else label falsified).
- [ ] **A1.2:** boundary position moves smoothly under CRP-concentration ±50%.
- [ ] **A1.3:** slow-path trial-order shuffle still crosses.
- [ ] Exports a "formed bundle" artifact (cause + banks + formation metadata) for T1.3.

### T1.3 — Sim 2: hysteresis loop and BMR melt
**Depends:** T1.2 (bundle artifact), T0.3 (gate status). **Spec: §3 Sim 2.**
**Task:** Import a Sim 1 frozen bundle (shared seeds). Cross-trial learning; relational modality (how shown material is met) always on/truthful; E_t per R2. Analytic BMR: at fixed intervals compare full model (coupling present) vs. reduced (coupling pruned, competence banks retained) via Friston-2017 ΔF over counts; prune when reduced wins. **If T0.3 landed:** implement the melt gate as the derived reflexivity-dependence of ΔF; **else:** impose and log as IOU. Four regimes on matched evidence budgets: informational/low-E_t; contact-under-capture; dissociative quiet (attenuation active); witnessing. Probes: premature vs. late prompted reduction; real-danger environment; E_t-flip.
**Success criteria (S2.1–S2.5 + adversarial):**
- [ ] Regimes 1–3 produce < 10% of witnessing's root revision at matched evidence counts.
- [ ] Melt discreteness: > 50% of total structural drop within a window ≤ 10% of melt-phase length; hysteresis figure (structural precision vs. cumulative evidence, 4 trajectories) produced.
- [ ] Selective prune: competence banks survive at ordinary precision; post-melt policy re-organizes (compulsive selection rate drops, competence-dependent success maintained).
- [ ] Premature prompt fails (burden retained), late prompt succeeds; failure probability correlates with residual accuracy contribution, not prompt count.
- [ ] Real-danger control: witnessing preserves adaptive fear (true-contingency avoidance intact; alone-with-this prior revised).
- [ ] **A2.1 content-swap:** matched-precision informational content in the relational slot does **not** melt (this is the C3 test; a failure here is a headline negative result — report it).
- [ ] **A2.2 E_t-flip:** one-trial E_t spike changes effective precision only; structural counts bit-identical.
- [ ] **A2.3:** melt discreteness survives BMR prior-odds sweep (±1 nat).

**→ Gate G1: write the §9 stub from T1.1–T1.3 results.**

---

## Phase 2 — Make E_t honest

### T2.1 — Sim 6a-discrete, Stage 1: inferred depth, inference-face collapse
**Depends:** T0.4 (stability envelope), T1.3 (bundle + melt machinery). **Spec: Appendix A.1–A.4, A.6 Stage 1.**
**Task:** Extend the Sandved-Smith architecture with IFS semantics: level 1 = bundle-vs-context inference on cue trials (T1.2 bundle); level 2 = the precision balance; level 3 = discrete depth states. Reflexive modality `o_self` implemented **process-side** (generative process emits the agent's true dominant-cause configuration; agent holds an ordinary likelihood over it); E_t = inferred precision on that mapping. Collapse via the inference face only: unmodeled PE bursts raise inferred volatility → hyper-posterior widens. No mental action yet.
**Success criteria:**
- [ ] **Emergent collapse (S6.2):** arousal dose-dependently collapses hyper-layer posterior precision and it recovers under safety — with no direct arousal→E_t assignment anywhere in code (collapse must route through volatility inference; assert in closing note).
- [ ] Transparency/opacity readout: `o_self` posterior sharpness tracks depth; bundle-active-while-dark (transparent) and bundle-registered (opacified) regimes both occur in one run.
- [ ] **One-variable biography figure:** collapse at a formation event → dark avoidance phase → recovery, capture index and opacification annotated on one E_t trace.
- [ ] **D3:** C_t vs. inferred depth is sigmoid by preregistered fit criterion with no sigmoid in the spec/code; if not sigmoid, label `null` and characterize the actual form.
- [ ] **D1 numeric validation:** the effective precisions realized by message passing match T0.2's closed form within stated tolerance (or the deviation is characterized).
- [ ] Identifiability (A6.2): simulated-inference-on-simulated-data recovers the depth trajectory (correlation ≥ preregistered threshold) from behavior + observations alone.
- [ ] Stability: no second-order precision oscillation within T0.4's envelope; runs outside it documented.

### T2.2 — Sim 6a-discrete, Stage 2: mental action
**Depends:** T2.1. **Spec: A.3 policy face. Scope guard: one figure, one results paragraph.**
**Task:** Add precision-allocation policies (mental actions) over {reflexive channel, first-order threat channels}; EFE selection with survival-relevant preferences.
**Success criteria:**
- [ ] Under acute threat, EFE ranks threat-allocation above reflexive-allocation — collapse is *selected*, not imposed (policy-EFE decomposition figure showing why).
- [ ] Witnessing = the reflexive-hold policy: initially EFE-dominated under activation; becomes EFE-optimal after preregistered evidence exposure (the borrowed-before-owned precondition, single-agent version).
- [ ] The Stage-1 inference-face results replicate with policies enabled (mental action doesn't break emergent collapse).
- [ ] Deliverable capped: one figure + one results paragraph in the sim README.

### T2.3 — U3: four-timescales figure
**Depends:** T1.1–T1.3, T2.1. **Assembly ticket — no new runs.**
**Task:** One figure from existing logs, four aligned horizontal bands over their native clocks: (1) effective precision within one encounter (capture→witnessing, from T2.1); (2) mental-policy viability across a treatment course (from T2.2 if done, else omit band with note); (3) structural precision across encounters (freeze from T1.2, trust/melt from T1.3); (4) structure events across the life span (spawn/prune markers). Chamberlin rules: identical condition colors across bands, annotated event lines.
**Success criteria:**
- [ ] Single SVG/PDF + caption ≤ 150 words, readable standalone by a colleague who hasn't seen the sims.
- [ ] Every band traces to a named run in a named summary.json (provenance table in the figure's README).
- [ ] A note recommending for/against inclusion in the paper, with the §7 or §9 slot it would occupy.

---

## Phase 2b — Sim 6 Stages 3–4 (added 2026-07-09 by author direction; pulled forward from Phases 3–4)

### T2.4 — Sim 6a-continuous, Stage 3: the Φ-bridge and the basin map (U2)
**Depends:** T0.5 only (independent of T2.1 — may run in parallel). **Spec: Appendix A.2 (continuous column), A.4 (empirical-prior resolution), A.7 U2.**
**Task:** Build a continuous three-layer hyper-model in RxInfer as a NEW Julia project at `projects/emergence-suite/continuous/` (read `projects/beautiful-simulation/` for the GCV/3-layer patterns — read-only, do not modify it). Structure: depth layer `h_t` → precision layer `z_t` → content layer, where `h_t` governs the balance between a bundle-prior stream and a present-evidence stream via the **empirical-prior** resolution (top-down precision message; no reflexive observation channel in this variant — regime-face only, per A.4). Arousal/volatility bursts enter as evidence; collapse and recovery of the depth posterior must be inference-driven (no assignment from burst schedule to `h`).
**Deliverables:** (1) collapse/recovery traces (continuous analogue of T2.1's biography); (2) **U2 basin map**: the (depth, capture) phase portrait — numerically integrate the coupled expected-dynamics over a preregistered parameter grid, mark fixed points and basins; (3) hysteresis-as-basin-hopping figure (drive the system around Sim 2's loop in the continuous model).
**Success criteria (preregister in `continuous/configs/`):**
- [ ] A self-sustaining high-depth fixed point (accurate self-modeling keeps volatility estimates low, keeping depth cheap) exists across the FULL preregistered parameter grid — U2's "everyone has Self" as a dynamical fact; report any grid cells where it vanishes.
- [ ] A competing capture basin exists in part of the grid (occlusion as metastability); basin boundary mapped.
- [ ] Collapse under volatility bursts is dose-dependent and recovers; no direct writes to `h`.
- [ ] The run contract (summary/status/metadata/criteria-results) is emitted; RxInfer inference converges (document iteration counts / divergences).
**Rules:** no commit; no edits outside `projects/emergence-suite/continuous/`; may `Pkg.add` RxInfer + deps INSIDE the new project only.

### T2.5 — Sim 6b, Stage 4: spawn-in-hyper-model + the clamp control
**Depends:** T2.1 (its level-3 machinery) and Sim 1 (spawn machinery). **Spec: Appendix A.6 Stage 4, A.8. RESEARCH-GRADE: a precisely-documented obstruction is a successful outcome; do not fake a result to close the ticket.**
**Task:** Couple Sim 1's CRP formation to Sim 6a's inferred depth in `src/sims/sim6b/`: run formation schedules (acute overwhelm; safe control) where reflexivity-at-write is the INFERRED level-3 posterior (replacing Sim 1's logged arousal-linked input). Then the causal test of §3's invariant:
- **Unclamped:** under acute overwhelm, the depth posterior collapses (via T2.1's volatility pathway) and the spawned cause acquires the frozen signature (Sim 1's trait battery + Sim 2's revision probe).
- **Clamped:** identical overwhelm schedule, with the depth posterior held high by intervention (clamp = fix q(d) at the high state; document as an intervention, not a model change). If the spawned/updated cause is then ORDINARY — revisable by Sim 2's disconfirming protocol — the invariant is supported: overwhelm freezes VIA reflexivity collapse. If it still freezes, §3's invariant is WRONG IN THE MODEL — report as falsified; this is the "stage fails → paper gets a stub" case.
- **Yoked arousal control:** matched arousal stream with volatility evidence withheld from level 3 (so depth stays high by inference, not clamp) — separates the clamp intervention from an evidence artifact.
**Success criteria (preregister):** [ ] unclamped freezes (traits + <10% revision); [ ] clamped rescues (>preregistered revision threshold — state it against Sim 1's measured revisable ceiling, NOT the unreachable 80%); [ ] yoked control patterns with clamp; [ ] no second-order oscillation; [ ] every label shipped.
**Timebox:** if the CRP-inside-hyper-model coupling cannot be made to run after a bounded attempt, deliver the obstruction note (what breaks: message schedule, state-space growth mid-inference, etc.) — that documents the v12 research problem and is a valid completion.
**Rules:** no commit; no Pkg.add; own module + minimal dispatch hook; do not modify sims 1/2/3/6a or shared modules.

## Ticket order

T0.1 → T0.5 → {T0.2, T0.3, T0.4 in parallel with T0.5} → T1.1 → T1.2 → T1.3 → **G1 (§9 stub)** → T2.1 → T2.2 → T2.3 → **G2**.
T1.1 needs only T0.5 and may start while T0.2–T0.4 are in flight.
