# Plan: IFS Paper v8 → v9 Rewrite

## Context

The paper's center shifts from "parts as identity-level precision bundles" to **"hierarchical relational gating."** The new one-sentence central move:

> We model IFS as a relational system in which parts are identity-level bundles whose world-models naturally include other parts; protectors are bundles whose policies include access-control over lower-layer states; Self-energy governs whether a broader self-anchor ("Presence") can hold those interactions without capture; and witnessing works by relaxing protective predictions enough for burdened self-states to revise.

This is a major rewrite: new introduction, new central section, new simulation, heavy cuts. ~80% of the prose changes. All figures are new.

## Two Substantive Theory Changes (from adversarial pressure-testing)

### A. Protectors are full parts, not gates

Gate-openness is a *function* of protector policies, not the protector itself. Each protector bundle includes role/self-position, target-part model (beliefs about what lower-layer contact would cause), policy priors, and feared consequences. "Gating" is what their policies produce, not what they are. This resolves the critique that "protector = gate" is too thin.

### B. Other parts are part of the environment → alliances and polarization emerge

A part's world-model already includes beliefs about the environment. Other parts are part of that environment. So beliefs about other parts' strategies are a *subtype* of world-state beliefs — not a special new category. This means:
- **Alliances** = convergent world-models + compatible policy preferences
- **Polarizations** = incompatible policies under limited control bandwidth
- **Effective gate state** = current outcome of this competition

Do not over-emphasize cross-part beliefs as a defining feature — they follow naturally from "world-model includes other agents." Include in theory + one diagram. Do NOT add a separate simulation.

## Four Framing Changes

1. **Therapist = co-regulator / attentional guide / temporary bridge** — not substitute Self. Client Self-leadership is the target.
2. **Self-energy ≠ Presence** — keep distinct. Presence = broad self-anchor. Self-energy = whether it's available under activation.
3. **DELETE "Self meets needs"** — Self *witnesses and relates to* needs. What revises is the prediction that contact with the need is intolerable, not the brute fact it went unmet.
4. **Developmental time-period** folded into self-state in text/diagrams (not a separate hidden factor). Covers age regression, "I am six," why orienting matters.

## Stated Limitations (add to Discussion)

- Witnessing = the window for revision, not the whole IFS arc (retrieval, unburdening, reintegration acknowledged but minimal)
- Model formalizes burdened/extreme roles, not full IFS ontology of parts-as-always-present
- Self-like parts acknowledged as a real unsolved problem
- Foil is narrowed: not strawmanning AEDP, EFT, Coherence Therapy — isolating one variable
- Some protectors operate on accurate current contingencies — do not pathologize realistic protection

## Key Distinctions File

`projects/ifs-paper/v9-key-distinctions.md` — load-bearing sentences and framings from adversarial review. Consult during drafting sessions.

## Strategy: Theory-first, then simulation, then results prose

The v8 experience showed that simulation design follows from theoretical claims. Writing the theory spine first (Sections 1-6) ensures the simulation knows exactly what to prove. Then build the simulation, inspect results, and write Sections 7-8 around real outputs.

## The 10 Sessions

### Session 1: Salvage Inventory + Outline
**Goal:** Identify every passage worth keeping from v8. Write the v9 section outline with word-budget targets.

Tasks:
- [ ] Read v8 end-to-end, tag passages to KEEP / ADAPT / CUT
- [ ] Write `projects/ifs-paper/v9-outline.md` with section structure + word budgets
- [ ] Write `projects/ifs-paper/v9-salvage.md` with salvaged passages and their new homes
- [ ] Update `projects/ifs-paper/next-session.md`

**v9 Target Structure:**
1. Introduction (~600w) — layered unmet-need/protector stack
2. IFS and the Problem (~400w) — parts, exiles, protectors, Self (very short)
3. Formalization: Parts in Hierarchical Relation (~800w) — bundle definition + protectors gate access
4. Layered Protection and Relational Gating (~1000w) — THE new section (4 moves)
5. Self-Energy, Capture, and Gate Traversal (~600w) — precision governs whether stack opens
6. Relational Prediction Error (~800w) — for exiles AND protectors
7. Simulation Evidence (~1200w) — one model, three conditions, ablation, transfer
8. Discussion (~800w) — explains, gaps, next steps

Total: ~6200w main text + 1 appendix (ablation detail + parameter table)

**What gets cut from v8:**
- Object relations aside (§3)
- 8 C's (§6.5), self-like parts (§6.5)
- Most of formation (§4) → 1-2 paragraphs in §3
- Most of persistence (§5) → 1-2 paragraphs in §3
- Polarization (§10.2 + Appendix B) → 1 sentence in Discussion
- Full glossary (Appendix C) → Table 1 only
- Formation simulation (Appendix A) → cut entirely
- Study 1 + Study 2 + adversarial history → replaced
- Dog-fear as conceptual anchor → stays only in simulation if needed

**What gets salvaged from v8:**
- Identity-level precision bundle definition (lines 64-99) → reframed as what exiles carry
- Discriminant validity paragraph (line 77-78) → stays
- Carry-forward sentence (line 80) → adapted
- Capture index formalism (lines 256-280) → adapted for gate
- Relational PE argument (lines 344-366) → upgraded with protector form
- Key clinical quotes from §9 → preserved
- "Same activation, different relationship" → preserved
- Table 1 translation table → updated

---

### Session 2: Introduction + §2 (IFS and the Problem)
**Goal:** Write the new opening. This sets the tone for the whole paper.

Tasks:
- [ ] Write §1: open with layered unmet-need/protector example, state core claim early
- [ ] Write §2: very short IFS primer (parts, exiles, protectors, Self) — no dog, no extended clinical narration
- [ ] Updated Table 1 with new terms (gate, Presence, unburdening as regime change)

**The new opening vignette:**
> A child needs comfort and protests when it is unavailable. That protest is adaptive at first. Later it becomes humiliating, punished, or ignored. A new strategy forms to inhibit protest. Later still, even the wish to ask directly may become shameful, and another protector forms around that. What persists is not just fear, but a layered system in which each strategy is organized around the anticipated cost of allowing the layer beneath it to come forward.

---

### Session 3: §3 (Formalization) + §4 (Layered Protection) — THE CRUX
**Goal:** Write the paper's conceptual core. If this is wrong, everything downstream fails.

Tasks:
- [ ] Write §3: parts as identity-level bundles in hierarchical relation
  - Exile = burdened self-state (including developmental time-position) + unmet need + local world model
  - **Protector = full part** with role/self-position, target-part model, policy priors, feared consequences; gating is a *function* of protector policies, not what protectors *are*
  - Meta-protector = protector inhibiting earlier protector when that strategy becomes costly
  - **Other parts in the world-model:** a part's world-state beliefs naturally include other parts (they are part of the environment) → alliances and polarizations emerge without a separate mechanism
  - **Explicit "Three Levels of Relation" subsection:**
    1. Protector to exile: organized around what it predicts would happen if exile's need/pain became live
    2. Protector to protector: later protectors wrap earlier ones when earlier strategy becomes costly/shaming/ineffective
    3. Self to the stack: witnessing = protector learns contact with exile no longer implies catastrophe
  - Salvage discriminant validity paragraph, carry-forward sentence (adapted)
  - Brief formation story (1-2 paragraphs, not a full section)
  - Brief persistence story (1-2 paragraphs, not a full section)
- [ ] Write §4: Layered Protection and Relational Gating (the 4 moves)
  1. Protector defined relationally: a full part whose policies include gating access, learned because contact predicted costly
  2. Layered protection: new protectors when prior strategies become dangerous/shameful
  3. "Aging up": later layers encode later developmental self-states, burdened layer stays frozen
  4. Witnessing redefined: safe descent through gate hierarchy where protectors update cost predictions
  - Developmental story: wound → first strategy → strategy punished → second protector → stack of gates
  - One diagram: parts with cross-part appraisal arrows showing how alliances/polarizations/gating emerge

**STOP AND EVALUATE after this session.** Read §1-4 end-to-end. The argument must be clear before proceeding.

---

### Session 4: §5 (Self-Energy + Capture) + §6 (Relational PE)
**Goal:** Complete the theory spine.

Tasks:
- [ ] Write §5: Self-energy, capture, and gate traversal
  - Self-energy governs whether the gate stack can be traversed
  - **Self-energy ≠ Presence:** Self-energy = regime variable (is the anchor available?); Presence = the broad self-anchor itself
  - Capture index adapted for gate (Self-energy modulates protector's cost estimate)
  - Presence as broad, low-content self-anchor (not jhana, not metaphysics)
  - Target prose: "The witnessing stance may be scaffolded by a broader, less content-bound self-identification — a present-centered 'I am here' — that parts can encounter as more spacious than their own local identity claims."
  - **Therapist role:** co-regulator, attentional guide, temporary bridge to client Self — not substitute Self. Client Self-leadership is the target.
  - Therapeutic zone: activation × Self-energy → gate closed/traversable
  - Cut: 8 C's, dissociation subsection (mention in 1 sentence)
  - Note: self-like parts acknowledged as unsolved — partial access may support some updating but broader Presence supports deeper work
- [ ] Write §6: Relational prediction error — upgraded
  - **Exile form:** expects isolation, encounters Self's presence → identity-level mismatch
  - **Protector form (NEW):** expects contact = catastrophe, encounters Self remaining present/regulated → gate cost estimate updates
  - Clinical ordering: protectors usually change before exiles
  - Unburdening defined: durable collapse of burdened attractor basin (gate + self-state + policy)
  - **Self witnesses, does not meet needs:** what revises is the prediction that contact with the need is intolerable — not the brute fact the need went unmet
  - **Witnessing = window:** makes later processes possible (retrieval, unburdening, reintegration acknowledged but minimally represented)
  - Clinical probe: "say 'I am presence' — if parts object, the objecting protector is the current gatekeeper"
  - Preserve key clinical quotes from v8 §9

---

### Session 5: Simulation Spec
**Goal:** Write `projects/ifs-paper/simulation-v9-spec.md` — complete design before any code.

Tasks:
- [ ] Specify hidden factors, observation channels, policies
- [ ] Specify A-matrices (likelihood mappings) — especially Presence→Gate coupling
- [ ] Specify B-matrices (transitions) — gate, self-state, meaning
- [ ] Specify D priors (initial beliefs)
- [ ] Specify three conditions: informational-only, relational-only, full witnessing
- [ ] Specify ablation: block Presence→Gate channel
- [ ] Specify transfer probe: cue A (training) → cue B (novel)
- [ ] Specify success criteria and expected results:
  - **Hard temporal ordering:** gate → self → meaning → policy (must be visible in full witnessing condition)
  - **Unburdening threshold:** gate-opening and held-self posteriors remain above 0.50 across later probes AND former symptom policy no longer dominates policy selection
  - **Transfer:** cue B probe shows gate+self transfer in witnessing but not informational-only
  - **Ablation:** blocking Presence→Gate eliminates the witnessing advantage
- [ ] Specify **"Not Simulated (by design)"** list: ceremonial release, developmental aging of all layers, multi-layer protector stacks, polarization, therapist-as-second-agent, 8 C's, formation
- [ ] Include concrete relational cue examples alongside abstract A/B labels (e.g., "cue A: comfort unavailable; cue B: request for help unanswered")
- [ ] Write parameter registry: `simulation-v9-magic-numbers.md`

**Simulation-theory gap (honest):** The theory defines protectors as full parts with role-identities, feared consequences, and cross-part appraisals. The simulation collapses this into one effective gate state — the net result of protector policies. This is a deliberate simplification stated explicitly in §7: "The simulation represents the effective gate state — the net output of protector policies — as a single hidden factor, while the theory allows for richer protector bundles."

**Gate coupling: Multi-cue inference (Option A).** Gate state is inferred from all four observation channels. Presence is one voice among several — interoceptive calm and supportive external response also inform the gate. No single channel forces it. Presence + calm + support → strong opening. Presence + panic + rejection → gate stays closed.

**Future consideration:** Try precision modulation (Option B) as an alternative — Presence doesn't inform gate directly, instead Self-energy increases precision on all channels. Closer to v8's approach. Compare results with Option A to see if the mechanism matters or if both produce the same ordering.

**Presence as control parameter vs hidden state:** Self-energy/Presence should remain a control parameter (not inferred), consistent with v8. It modulates how much the Presence observation channel delivers evidence, and that evidence influences the gate posterior.

---

### Session 6: Build Simulation
**Goal:** Implement `ifs_model_v4.jl` + runner script. Generate figures.

Tasks:
- [ ] New model file: `projects/library/src/active_inference/ifs_model_v4.jl`
  - Follow v2 structural patterns (constants, structs, two-stage inference, configs, aggregation)
  - 3 hidden factors × 2 states each
  - 4 observation channels
  - 4 policies
  - Dirichlet bank pattern from v3 for transfer probe (shared gate + self-state, cue-specific meaning)
- [ ] New runner: `projects/library/scripts/ifs_simulation_v4.jl`
  - Three conditions
  - One ablation
  - Transfer probe
  - Generate Figure 1 (architecture) and Figure 2 (trajectories + transfer)
- [ ] Run, tune, verify success criteria
- [ ] Parameter sensitivity ±20%

**Expected Figure 2 panels:**
- P(gate = permissive) across trials
- P(self = held-capable) across trials
- P(meaning = safe-enough) for cue A
- P(policy = direct ask) across trials
- First probe on cue B: P(contact) across conditions

---

### Session 7: §7 (Simulation Evidence)
**Goal:** Write simulation section around real results.

Tasks:
- [ ] Write §7: one model, three conditions, ablation, transfer
- [ ] Describe architecture concisely (hidden factors, channels, policies)
- [ ] Present three-condition comparison
  - Full witnessing: gate opens first → self-state → meaning → direct ask
  - Relational-only: gate opens, self-state moves, meaning less (no strong correction)
  - Informational-only: meaning moves, gate/self-state barely move, no transfer
- [ ] Present ablation: blocking Presence→Gate eliminates the advantage
- [ ] Present transfer: cue B probe shows shared gate+self vs local meaning
- [ ] Reference Figure 1 and Figure 2

---

### Session 8: §8 (Discussion) + Appendix
**Goal:** Write discussion. Move parameter table + ablation detail to appendix.

Tasks:
- [ ] Write §8 Discussion:
  - What the model explains (layered protection, gate traversal, unburdening, generalization)
  - What remains unmodeled (stacked multiple protector layers, full cross-part dynamics, therapist as agent)
  - **Division-of-labor caution (stated cleanly):** theory sections formalize hierarchical relational gating; simulation tests one consequence — that when the system reaches a witnessing regime, identity-level revision outperforms threat-level updating
  - **Stated limitations** (from adversarial review):
    - Witnessing = window, not whole arc
    - Model formalizes burdened/extreme roles, not full IFS ontology
    - Self-like parts unsolved
    - Foil narrowed — not strawmanning AEDP/EFT/Coherence Therapy
    - Some protectors operate on accurate current contingencies
  - Empirical predictions: gate relaxation ordering, generalization gradient, relational > informational
  - What a stacked-gating simulation would need
- [ ] Write Appendix: ablation detail, parameter table, sensitivity results
- [ ] Updated Table 1 / glossary

---

### Session 9: Full Read-Through + Consistency Pass
**Goal:** Read v9 end-to-end. Fix inconsistencies, forward/back references, terminology.

Tasks:
- [ ] Read §1-8 + appendix in one sitting
- [ ] Check: does the argument flow without needing v8?
- [ ] Check: is Table 1 consistent with prose?
- [ ] Check: are all figure references correct?
- [ ] Check: clinical quotes still grounded?
- [ ] Trim any section that exceeds word budget
- [ ] Write abstract (last, once argument is settled)

---

### Session 10: External Review + Polish
**Goal:** Delegate to Codex for editing review. Final polish.

Tasks:
- [ ] Delegate each section to Codex for editing review (per feedback memory)
- [ ] Incorporate feedback
- [ ] Generate LaTeX
- [ ] Update memory files, roadmap, next-session

---

## Design Decisions (locked)

1. **Simulation domain:** Abstract cues (A/B) with concrete attachment gloss in prose ("e.g., comfort unavailable"). Keeps the model general, lets readers project.
2. **Exposure contrast:** Downplay to discussion only. The three conditions are not framed as "exposure analogue" in the simulation section. Exposure comparison appears in Discussion as an implication of the architecture.
3. **Gate design:** True hidden factor, inferred from observations via A-matrices. Presence + interoceptive + external response cues all contribute to gate posterior. The A-matrix coupling between Presence and gate is the critical design decision — Presence makes gate-opening more likely but does not force it.
4. **Session 1 timing:** Lock plan now, start Session 1 next conversation.
5. **Section count:** 8 sections vs user's proposed 7. The split: user's §3 ("Formalization: parts as identity-level bundles in hierarchical relation") is broken into §3 (formal definitions + three levels of relation) and §4 (layered protection + the 4 moves). The 4 moves earn their own section — they are the paper's new center. If this feels like too much separation, merge back in Session 3.

## Key Risks and Mitigations

| Risk | Mitigation |
|------|-----------|
| Gate-as-hidden-factor feels like labeling, not mechanism | A-matrix design must show *how* gate is inferred from multiple cues, not just flipped by Presence |
| Cutting too much loses what made v8 work | Salvage inventory (Session 1) before any cuts |
| Simulation doesn't show predicted ordering | Theory sections are honest about what simulation does/doesn't prove (same discipline as v8 adversarial disclosure) |
| Paper becomes too broad (all of IFS) | Hard word budgets per section; "hierarchical relational gating" is the one expansion |
| Loss of clinical grounding | Preserve clinical quotes from v8 §9; relational vignette in intro |

## Critical Files

| File | Role |
|------|------|
| `projects/ifs-paper/draft-v8.md` | Source (salvage passages) |
| `projects/ifs-paper/draft-v9.md` | Target (new draft) |
| `projects/ifs-paper/simulation-v9-spec.md` | Simulation design spec |
| `projects/ifs-paper/simulation-v9-magic-numbers.md` | Parameter registry |
| `projects/library/src/active_inference/ifs_model_v4.jl` | New simulation model |
| `projects/library/scripts/ifs_simulation_v4.jl` | New simulation runner |
| `projects/ifs-paper/v9-outline.md` | Section outline + word budgets |
| `projects/ifs-paper/v9-salvage.md` | Salvaged passages with new homes |
| `projects/ifs-paper/figures/v4/` | New figures |

## Verification

After each session, verify:
- Sessions 1-4: Read the theory spine §1-6 end-to-end (no simulation needed)
- Session 5: Spec review — does each success criterion map to a paper claim?
- Session 6: `julia projects/library/scripts/ifs_simulation_v4.jl` — all success criteria pass, figures generated
- Session 7: §7 accurately describes real results
- Sessions 8-9: Full paper read-through, no dangling references
- Session 10: LaTeX compiles, PDF renders
