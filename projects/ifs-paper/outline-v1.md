# An Active Inference Account of Internal Family Systems
## Draft Outline v1 — January 2026

---

## Working Thesis

**Parts are precision-modulating meta-priors** that boost or suppress clusters of beliefs within a single generative model. They are not separate sub-agents with their own models, but rather *patterns of precision allocation* that, when activated, shape both perception and action.

**The key move**: Parts dominate computation through modularity — isolated subgraphs of the generative model that, lacking edges to context variables, cannot generate context-dependent prediction errors, and therefore cannot update. Blending is what happens when such a subgraph captures policy selection: perception narrows, context is lost, and the system "becomes" the part. IFS therapy works by progressively reconnecting these isolated subgraphs to the full generative model (re-contextualization), at which point standard Bayesian updating operates on previously frozen priors. Unburdening is not a separate mechanism from welcoming — it is the same reconnection process operating at greater depth.

---

## Paper Structure

### 1. Introduction

#### 1.1 The Problem: Why Model IFS Computationally?
- IFS is empirically supported but lacks a formal mechanistic account
- Active inference provides a unified framework for perception, action, and emotion
- Gap: existing active inference models of therapy (Chamberlin's coherence therapy paper) don't address multiplicity or the "parts" architecture
- Contribution: We provide the first computational account of IFS's core constructs

#### 1.2 Brief Review of Active Inference
- Generative model: the brain's hypothesis about causes of sensory data
- Free energy minimization: reduce surprise by updating beliefs OR taking action
- Precision: confidence weighting on predictions (high precision = "trust this signal")
- Key matrices (see Appendix A for full notation):
  - A: likelihood (state → observation mapping)
  - B: transition dynamics (state stickiness)
  - C: preference priors (what outcomes I want)
  - D: initial state priors
  - E: policy/habit priors
- Epistemic vs. pragmatic priors [per your notes with Shamil]:
  - Epistemic: beliefs about the world ("trees are green")
  - Pragmatic: preferences about outcomes ("I want to not be hungry")
  - Prediction error handling differs: epistemic → update beliefs; pragmatic → take action
  - **Valence = prediction error from pragmatic priors** (always ≤ 0)

#### 1.3 IFS Primer (Psychological Terms Only)
*[Goal: A clinician with no computational background can follow this]*

- **Parts**: Distinct aspects of the psyche with their own beliefs, feelings, and motivations
  - Not pathological "splitting" — everyone has parts
  - Developed through experience, especially early attachment and trauma

- **Exiles**: Parts that hold painful emotions, memories, and beliefs from overwhelming experiences
  - Often frozen at the age when trauma occurred
  - System tries to keep them out of awareness

- **Protectors**: Parts that developed to manage or suppress exiles' pain
  - **Managers**: Proactive, planning-oriented. Keep life structured to avoid triggers. "Never let us get close to dogs."
  - **Firefighters**: Reactive, emergency-response. Activated when exiles break through. "Dissociate NOW." "Drink to numb."

- **Blending**: When a part's perspective dominates consciousness
  - You don't just *have* the feeling; you *are* the feeling
  - Perception and action both get filtered through the part's beliefs
  - Often accompanied by age regression (feeling young, small, helpless)

- **Unblending**: Restoring perspective; the part is present but not dominant
  - "I notice I have a part that feels scared" vs. "I AM scared"

- **Self**: The core, undamaged essence that can witness parts with curiosity and compassion
  - Qualities: calm, clarity, curiosity, compassion, confidence, courage, creativity, connectedness
  - Not a part — more like "what's there when no part is blended"

- **Unburdening**: The process of releasing the extreme beliefs and emotions a part carries
  - Part no longer needs to hold the pain
  - Protectors can relax because there's nothing to protect against

- **Polarization**: Two parts in conflict, pulling the system in opposite directions
  - Can oscillate second-by-second or persist for years

---

### 2. The Model: Parts in Active Inference Terms

*[Goal: Mirror the Primer section, translating each concept into computational language]*

#### 2.1 What Is a Part? (Core Definition)

**Claim**: A part is a *cluster of precision-modulating hyperpriors* over a subset of the generative model.

Breaking this down:
- The generative model contains all the organism's priors (beliefs, preferences)
- These priors are *always there*, but with varying precision (confidence weighting)
- A part is characterized by:
  1. A **set of associated priors** (e.g., "dogs are dangerous," "I am helpless," "I must run")
  2. A **meta-prior on precision**: "how much should these beliefs dominate inference?"
  3. A **self-activation prior**: "I am needed" — which boosts the precision of (2)

**Key insight**: Parts don't have separate generative models. They're patterns of *precision allocation* within a single model.

```
Part := {
  associated_priors: [p₁, p₂, ..., pₙ],      // subset of generative model
  precision_hyperprior: π_part,              // how strongly to weight these
  activation_prior: P("I am needed" | context)  // when to activate
}
```

**Phenomenological grounding: parts are not experienced as agents.** When a part is active, it doesn't feel like "an agent inside me is doing something." It feels like *me*. Full identification. "I am scared" — not "a scared agent has taken over." The "agentic" quality of parts (purposes, feelings, age) only becomes visible *after* partial unblending, when Self can observe the part from some distance. IFS's practice of imagining parts as children or figures is a clinical technique — it facilitates unblending by creating representational distance, allowing meta-cognitive access to the modular subgraph. This is an in vitro solution: therapeutically effective, but not a description of the underlying mechanism. The computational model should reflect this: parts are subgraphs, not homunculi.

**Activation**: A part activates when the system's current or predicted world model resembles the conditions under which it formed. In Bayesian terms: P(part_active | s) goes high when the posterior over hidden states falls within the region the subgraph's priors were formed to handle. This includes interoceptive state — the body is part of the world model. A racing heart and tight chest can activate a part just as effectively as seeing a dog, because the physiological signature matches the encoding context.

*[See alternative models analysis: [docs/concepts/alternative-models-comparison.md](docs/concepts/alternative-models-comparison.md)]*

#### 2.2 Blending: Modular Subgraph Captures Policy Selection

**Claim**: Blending occurs when a modular (disconnected) subgraph of the generative model captures policy selection, causing its context-blind beliefs to dominate both perception and action.

This is the same modularity that explains frozenness (2.8), now seen from the other direction: modularity is both why the part *persists unchanged* (no prediction errors reach it) and why it *dominates when activated* (it doesn't condition on context that would moderate its predictions).

Mechanism:
- The part's subgraph lacks edges to context variables — it generates predictions without conditioning on current safety, adult resources, etc.
- Ambiguous stimulus (might be a dog?) → the subgraph's context-blind prior ("dogs are dangerous, full stop") wins because it doesn't have to compete with context-dependent alternatives within its own inference
- Contradictory evidence (floppy ears, wagging tail) is processed by other subgraphs but cannot propagate *into* the modular part — so it doesn't update the driving beliefs
- Result: perception narrows to what the part "sees" (threat), action is constrained to the part's policies, and the system "becomes" the part

**Why blending is hard to break from inside** (stickiness):
- The modular subgraph has no incoming edges that could deliver disconfirming evidence
- Its own predictions are self-consistent within its closed loop
- The part's activation increases precision on its associated priors, which further suppresses competing signals — a positive feedback loop
- Breaking blending requires an *external* intervention (therapist, Self-energy, environmental change) that can bypass the modularity

**Subjective correlates**:
- Feeling younger/smaller (the subgraph preserves the developmental state when it was formed)
- Tunnel vision on threat (context variables are disconnected)
- Loss of access to broader context and resources (those nodes are in the disconnected broader graph)
- "I AM scared" rather than "I notice fear" (the modular subgraph IS the active model — there's no meta-level vantage point connected to it)

#### 2.3 Protectors: Policy Priors Over Different Time Horizons

##### 2.3.1 Managers (Long-Range Avoidance Policies)

**Claim**: Managers are high-level policy priors that plan trajectories to keep the system away from exile-activating states.

- Operate with high *temporal depth* — planning ahead to avoid future triggers
- Modify expected free energy calculations: "paths that might encounter dogs have very high G"
- Shape lifestyle, relationships, career choices — anything to prevent exile activation
- In policy notation: π_manager biases toward trajectories where P(exile_trigger) → 0

##### 2.3.2 Firefighters (Rapid Reactive Policies)

**Claim**: Firefighters are low-level reactive policies that rapidly minimize acute free energy when a trigger slips through.

- Low temporal depth — immediate action, consequences later
- Activated when manager policies fail and exile activation begins
- Examples: dissociation, substance use, bingeing, impulsive behavior
- In policy notation: π_firefighter selected when free energy spike detected, optimizes for immediate F reduction regardless of long-term G

##### 2.3.3 Exiles (Frozen Affective Priors)

**Claim**: Exiles are priors that "freeze" the emotional/somatic/belief state from an overwhelming experience.

- Not just memories — entire *states* of the generative model from that moment
- "I am helpless," "I am unlovable," "I am in danger" — with high precision
- When activated, their predictions dominate (blending occurs)
- Protectors exist specifically to prevent exile priors from being activated

*[OPEN QUESTION: Is "frozen" the right computational metaphor? Alternatives: "encapsulated," "high-precision local minimum," "dissociated subgraph"]*

#### 2.4 Unblending: Restoring Dispersed Precision

**Claim**: Unblending is the shift from a winner-take-all, high-precision micro-model back to a balanced, multi-modal predictive regime.

Mechanism:
- Reduce precision on the active part's associated priors
- Allow other priors (including Self-associated ones) to re-enter competition
- Restore access to broader context, resources, present-moment evidence

Progression observed in therapy:
- Part A active → Part B active → Self-like part → Self
- Each transition = precision rebalancing

**Relation to epistemic depth**: Unblending may increase epistemic depth — considering more hypotheses about the situation rather than collapsing to one.

#### 2.5 Self: The Balanced-Precision State

*[This section is WIP — may go in appendix]*

**Working hypothesis**: Self is not a part but a *regime* of the generative model characterized by:
- No single prior cluster dominating precision allocation
- High epistemic openness (many hypotheses entertained)
- Pragmatic priors oriented toward organism-level thriving (not part-specific survival)

**Self-energy** as a *hyperprior on maximum precision bounds*:
- More Self-energy → lower ceiling on how much any part can dominate
- This is a system-wide parameter, distinct from part-specific reconnection

**Why Self has specific qualities (the 8 C's)**: Self qualities are not a special state you achieve — they are what Bayesian inference naturally produces when modularity is absent. They are the default properties of an unimpeded generative model:

| Self Quality | Computational Property of Unimpeded Inference |
|---|---|
| **Curiosity** | High epistemic drive — the system naturally seeks information gain when no part is forcing avoidance of uncertainty |
| **Calm** | Low baseline threat estimation — without modular threat-priors dominating, the system's prior on danger reflects actual base rates |
| **Clarity** | High signal-to-noise — no modular subgraph injecting context-blind predictions that distort inference |
| **Compassion** | Accurate tracking of others' internal states (social inference) — modular subgraphs distort social perception (projecting threat, assuming rejection); unimpeded inference reads others more accurately, and accurate reading of suffering naturally generates approach/care responses |
| **Courage** | Willingness to approach high-uncertainty states — epistemic drive outweighs avoidance when no part is inflating threat estimates |
| **Creativity** | High policy entropy — many actions considered, not collapsed to one protective strategy |
| **Connectedness** | High precision on social/attachment observations — the system is attending to relational signals rather than suppressing them |
| **Confidence** | Well-calibrated precision on own model — neither the over-confidence of a blended protector nor the under-confidence of a blended exile |

**Testable claim**: These qualities should co-occur (they're all consequences of the same underlying condition: absence of modular domination) and should all increase as modularity decreases. You shouldn't find someone with Self-led curiosity but not Self-led compassion — if one is present, the others should be too.

**Self does not need to be modeled explicitly.** It falls out as "what inference looks like on a fully connected generative model." This is consistent with the IFS phenomenology: Self is not something you build — it's what's revealed when parts step back.

#### 2.6 Unburdening: Restoring Plasticity

**Claim**: Unburdening releases the part's meta-level identification with its beliefs, restoring their plasticity (updateability).

The burden isn't just a belief with high precision—it's a belief that *won't update*. Trauma-formed priors have a **closed learning window**: consolidated under extreme stress, they became fixed points resistant to revision despite contradictory evidence.

Before unburdening:
- Part holds beliefs as essential/unchangeable ("This is who I am")
- Meta-belief: "I must hold this / releasing it would be annihilation"
- First-order beliefs don't update despite new evidence
- Learning window is closed

After unburdening:
- Meta-level grip is released
- First-order beliefs become updatable again
- Part can now learn from experience (e.g., "the world is safe now")
- Part often looks/feels different—frozen structure has dissolved

This is distinct from:
- **Unblending** (momentary precision redistribution)
- **Welcoming** (breaking modularity, context-embedding)

Unburdening is a *structural change* to the belief's updateability, not its precision or accessibility.

*[Note: This aligns with memory reconsolidation—returning consolidated memories to a labile state. See Section 2.8 for how this fits with the other mechanisms.]*

#### 2.7 Polarization: Oscillating Inferential Competition

**Claim**: Polarization occurs when two parts alternate in winning inferential competition, with neither achieving stable dominance.

- Can oscillate rapidly (seconds) or slowly (days/weeks)
- Each part's activation may trigger the other (e.g., inner critic → defeated child → inner critic)
- System gets stuck in limit cycle rather than settling

#### 2.8 Two Mechanisms of Therapeutic Change

*[See prior analysis: [docs/concepts/chamberlin-critique-three-mechanisms.md](docs/concepts/chamberlin-critique-three-mechanisms.md)]*
*[See unification argument: [docs/concepts/recontextualization-as-unfreezing.md](docs/concepts/recontextualization-as-unfreezing.md)]*

The previously proposed three mechanisms (Self-energy increase / Welcoming / Unburdening) reduce to two. Welcoming and unburdening are the same mechanism — re-contextualization — operating at different depths.

| Mechanism | Computational Operation | What Changes |
|-----------|------------------------|--------------|
| **Self-energy increase** | Global precision ceiling | System-wide parameter; enables the work |
| **Re-contextualization** | Progressive reconnection of modular subgraphs (structure learning) | Accessibility, context-embedding, AND updateability — simultaneously |

**Self-energy increase** = global precision gating. More Self-energy means any individual part can dominate less. This is a system-wide parameter that *enables* reconnection (you can't do graph surgery while fully blended) but isn't reconnection itself.

**Re-contextualization** = adding edges between an isolated schema subgraph and the broader network of contextual inference. This is what both "welcoming" and "unburdening" describe. A modular schema is frozen *because* it is disconnected — no new information reaches it, so no prediction errors can drive updating. Reconnecting the subgraph simultaneously makes the schema explicit, embeds it in context, and reopens the learning window. These are not three steps; they are three descriptions of the same graph-topological change.

**Why "frozen" is a consequence of modularity, not a separate property**: A disconnected node in a factor graph cannot receive messages. Its parameters cannot update — not because of a special lock, but because no prediction errors reach it. Re-contextualization (adding edges) IS unfreezing.

**What varies is depth, not kind.** Cases that resolve with Discovery alone (~50%) have shallow modularity — reconnection immediately generates enough prediction error. Cases requiring explicit unburdening have deeper isolation: either strongly consolidated priors (high Dirichlet concentration, needing vivid juxtaposition) or hierarchical identity locks (meta-beliefs like "this IS who I am" requiring reconnection at a higher level of the graph).

**This model explains:**
- Why witnessing must precede unburdening (can't send information to a disconnected node — integration IS prerequisite because integration IS the mechanism)
- Why unburdening is quick but integration takes time (reconnection is discrete; belief updating through the new edges requires subsequent experience)
- Why some parts unburden spontaneously during witnessing (~Chamberlin's >50% — shallow modularity resolves on reconnection alone)
- Why burdens are given to elements, not replaced (the ritual marks release of isolation, not content substitution)
- Why parts look different after unburdening (a reconnected subgraph gets reorganized by information flowing through it)
- Why protectors relax after exile unburdening (the exile's beliefs are now normal updatable priors, no longer dangerous frozen attractors)

---

### 3. Glossary: Computational Definitions of IFS Terms

| IFS Term | Active Inference Translation | Notation |
|----------|------------------------------|----------|
| Part | Cluster of priors + precision hyperprior + activation prior | {P, π_P, P(active)} |
| Blending | High-precision state where part's priors dominate inference | π_P >> π_other |
| Unblending | Precision redistribution restoring balanced inference | π_P ≈ π_other |
| Exile | Modular (disconnected) prior cluster from overwhelming experience; frozen because isolated | Subgraph S, edges(S,C) = 0 |
| Manager | Policy prior with high temporal depth avoiding exile triggers | π_mgr: minimize P(exile_trigger) over trajectory |
| Firefighter | Reactive policy prior minimizing immediate free energy | π_ff: minimize F(t) |
| Self | Balanced-precision regime; no part dominating | ∀P: π_P ≤ π_max |
| Welcoming / Unburdening | Re-contextualization: reconnecting modular subgraph to context network | Add edges(S,C); depth varies by consolidation strength |
| Polarization | Oscillating precision dominance between two parts | π_A ↔ π_B |
| Self-energy | Hyperprior on maximum precision bounds across all parts | π_max |

---

### 4. How IFS Therapy Works: Precision Dynamics in Session

#### 4.1 The Core Operation: Reconnection

IFS therapy involves:
1. **Self-energy** sufficient to prevent full blending (global precision gating)
2. **Attending to a part** — directing precision toward the modular subgraph to make its contents reportable
3. **Witnessing** — connecting the part's isolated beliefs to current context (Self's perspective, present safety, adult resources)
4. This reconnection enables standard Bayesian updating on previously frozen priors — the witnessing IS the change mechanism, not merely its prerequisite

*[This mirrors Chamberlin's Discovery mechanism. For deeply consolidated priors, vivid juxtaposition (high-precision contradictory evidence through the new channel) provides the additional prediction error needed.]*

#### 4.2 Step-by-Step Session Dynamics

**Phase 1: Accessing a Part**
- Therapist guides attention to felt sense (interoceptive precision ↑)
- Part's associated priors become more active
- Controlled partial blending — enough to feel the part, not enough to lose Self

**Phase 2: Witnessing/Unblending**
- Maintain dual awareness: part's experience AND Self's curiosity
- Therapist's regulation co-regulates client's precision dynamics
- "How do you feel toward that part?" — checking for Self-energy

**Phase 3: Learning the Part's Role**
- Part reveals its protective function (what it's trying to prevent)
- System begins to understand part's "I am needed" prior

**Phase 4: Working with Exiles** (if appropriate)
- Protectors give permission to access exile
- Exile's frozen priors become active (controlled blending)
- Witnessing by Self creates context that wasn't present during trauma

**Phase 5: Unburdening**
- Exile releases the extreme beliefs/emotions
- Precision bound on exile's priors decreases
- Protectors can relax — nothing to protect against

#### 4.3 Two Paths to Healing

1. **Increasing Self-energy**: Strengthen the hyperprior on maximum precision bounds
   - All parts become less able to fully blend
   - More natural access to Self qualities

2. **Unburdening specific parts**: Reduce precision bounds on individual parts
   - Target specific trauma-based priors
   - Part-by-part liberation

*[These may interact: unburdening parts may increase global Self-energy, and higher Self-energy may facilitate unburdening]*

---

### 5. Example: The Dog Phobia Scenario

#### 5.1 Before Therapy

**Situation**: Person walks down street, sees shape that might be a dog

**Part activation**:
- Exile prior: "Dogs attack and I am helpless" (frozen from childhood bite)
- Exile precision hyperprior: VERY HIGH when dog-like stimuli detected
- Manager prior: "Avoid all situations where dogs might be" (policy with high temporal depth)
- Firefighter prior: "If dog detected, FREEZE/RUN" (rapid reactive policy)

**Blending cascade**:
1. Ambiguous visual input (might be a dog)
2. Exile's high expected precision for dog-threat → boosts threat interpretation
3. Evidence for "not a dog" (floppy ears, wagging tail) gets low precision → discounted
4. Exile fully blends → person feels small, terrified, helpless
5. Firefighter policy activates → freeze or run
6. Manager updates: "Never walk on this street again"

**Subjective experience**: "I became a terrified child. I couldn't think. I just had to get out of there."

#### 5.2 During Therapy

**Session work**:
1. Therapist helps client access the exile (controlled precision increase)
2. Self witnesses the exile's experience with compassion
3. Exile receives what it needed (attention, validation, updated information: "You survived. You're an adult now. Not all dogs are dangerous.")
4. Prediction error from contradictory evidence + high precision on therapeutic context → belief update
5. Unburdening: exile releases "I am helpless" belief; precision bound decreases

#### 5.3 After Therapy

**Same situation**: Person walks down street, sees shape that might be a dog

**Changed dynamics**:
- Exile's precision hyperprior now has lower ceiling
- Same stimulus doesn't produce winner-take-all dynamics
- Other priors can compete: "I'm an adult," "Most dogs are friendly," "I can assess and choose"
- System doesn't collapse into blended state
- Protectors less activated because exile isn't screaming

**Subjective experience**: "I noticed some nervousness, but I could also see it was just a golden retriever. I kept walking."

---

### 6. Mathematical Formalization

*[To be developed — placeholder for now]*

#### 6.1 Part Activation Dynamics

```
P(part_active | observation) ∝ π_part × P(observation | part_priors)
```

When part is active:
- Precision on part's associated priors increases
- Transition probability to staying active is high (stickiness)

#### 6.2 Blending as Precision Collapse

*[Need to formalize: inferential competition, winner-take-all dynamics, precision as attention]*

#### 6.3 Unburdening as Precision Bound Update

*[How does the structural change happen? Memory reconsolidation? Annealing?]*

#### 6.4 Open Questions for Formalization

- How to model the transition from "part as controller" to "part as content of awareness"?
- What's the right way to represent temporal depth difference between managers/firefighters?
- How does safety modulate precision dynamics? (Is safety itself a hyperprior?)
- Do we need explicit representation of identification ("I am this part")?

---

### 7. Simulation

*[Placeholder — goals outlined]*

#### 7.1 Agent in the World (Without Therapy)
- Simulate blending cascade in response to triggering stimulus
- Show how protector policies shape behavior
- Demonstrate polarization dynamics

#### 7.2 Agent in Therapy Session
- Model therapist as external precision modulator
- Simulate unburdening as precision bound update
- Before/after comparison of stimulus response

---

### 8. Discussion

#### 8.1 Relationship to Chamberlin's Coherence Therapy Model
- Same core mechanism: raise precision → access prior → prediction error → update
- Our extension: multiplicity (parts), precision *bounds* (unburdening), policy architecture (managers/firefighters)

#### 8.2 Neurobiology: State-Dependent Activation and the Body

*[Section to develop — placeholder with key ideas]*

The model's activation mechanism (parts activate when predicted world model resembles encoding context) has a natural neurobiological grounding in state-dependent memory.

Key points to develop:
- **Interoception as part of the world model**: The generative model includes predictions about bodily states (heart rate, muscle tension, breathing, gut feelings). These interoceptive predictions are part of what gets encoded in a modular subgraph. A part formed during terror includes the somatic signature of terror.
- **State-dependent retrieval**: A racing heart can activate a part just as effectively as seeing a dog — because the physiological signature pattern-matches to the encoding context. This is why parts are "felt in the body" — the body IS part of the world model, not separate from it.
- **The catch-22 in neurobiological terms**: The memory network is only fully retrievable when the matching physiological state is entered. But that state overwhelms processing capacity. Therapy = partial physiological activation (window of tolerance) sufficient for retrieval without overwhelm.
- **Reconsolidation as the neurobiological implementation of re-contextualization**: When a consolidated memory is retrieved and the reconsolidation window opens, new encoding occurs. The computational description (adding edges to context variables) maps onto the neurobiology (memory re-encoded with new contextual information during labile state).
- **Why somatic/imaginal ritual matters for unburdening**: Rich multi-sensory experiences during the reconsolidation window provide high-bandwidth encoding material. The ritual (fire, water, light) isn't symbolic — it's providing vivid interoceptive/sensory content that gets encoded alongside the updated context, making the reconsolidation more robust.

*[References to develop: state-dependent memory literature, reconsolidation (Ecker et al.), interoceptive inference (Seth), active inference accounts of PTSD]*

#### 8.3 Relationship to "The Beautiful Loop" / Schema Therapy Models
*[Need to re-read and integrate]*

#### 8.3 Self-Energy, Awakening, and Epistemic Depth
- Self-energy relates to *pragmatic* priors (preferences for how to act)
- Awakening/dereification relates to *epistemic* priors (beliefs about reality)
- IFS increases Self-energy but doesn't directly target epistemic opacity
- Meditation practices may work on epistemic precision bounds
- Could explain why IFS and meditation are complementary

#### 8.4 What IFS Does and Doesn't Do
- IFS: reifies parts in order to disidentify from them
- IFS does NOT teach dereification of the parts framework itself
- Possible extension: after unburdening, parts may "dissolve" into regular preferences/memories

#### 8.5 Clinical Implications
*[What predictions does this model make? What would it look like if it were wrong?]*

---

### Appendix A: Active Inference Notation Reference

| Symbol | Meaning |
|--------|---------|
| o | Observations |
| s | Hidden states |
| π | Policy |
| A | Likelihood matrix: P(o \| s) |
| B | Transition matrix: P(s' \| s, u) |
| C | Preference prior: P(o) preferred |
| D | Initial state prior: P(s₀) |
| E | Policy prior (habits) |
| F | Free energy |
| G | Expected free energy |
| π (overloaded) | Precision (context-dependent) |

---

### Appendix B: Open Questions and Future Directions

1. **Identification**: How to model "I am this part" vs "I have this part"? (See Metzinger on units of identification)

2. **Safety**: Is safety a global hyperprior that modulates all parts' precision bounds? Or do parts have their own safety estimates?

3. **Compatibility of beliefs**: How do we model parts that hold mutually exclusive beliefs? (Inferential competition suggests they literally can't both be active)

4. **Memory reconsolidation**: What's the relationship between our "precision bound reduction" and the biological process of reconsolidation?

5. **Therapist modeling**: Should we explicitly model the therapist as a second agent in dyadic active inference?

6. **[RESOLVED] Three distinct mechanisms → Two**: Welcoming and unburdening are the same mechanism (re-contextualization / reconnection of modular subgraphs) operating at different depths. What varies is consolidation strength and hierarchical depth of isolation. See [docs/concepts/recontextualization-as-unfreezing.md](docs/concepts/recontextualization-as-unfreezing.md).

7. **[RESOLVED] Frozen = disconnected**: Priors are "frozen" because they are modular (disconnected from context), not because of a separate plasticity lock. Re-contextualization IS unfreezing. The learning window was "closed" because no prediction errors could reach the subgraph.

8. **Hierarchical identity locks**: Some schemas have a higher-order wrapping: "this belief IS who I am." This may represent deeper modularity (isolation at a higher level of the graph) rather than a categorically different mechanism. How to model this as nested subgraph isolation?

9. **[PARTIALLY RESOLVED] Spontaneous vs. explicit unburdening**: Shallow modularity resolves on reconnection alone (~50%). Deep consolidation or identity-level wrapping requires vivid juxtaposition or explicit unburdening ritual. Remaining question: can we predict which cases will be shallow vs. deep from observable pre-therapy measures?

10. **[RESOLVED] Chamberlin's modularity critique**: Modularity IS the core mechanism. Precision is one means by which modularity is enforced (extreme precision can silence contradictory messages). But the fundamental operation of change is graph-topological: adding edges, not tuning parameters.

11. **Why is attunement / resonance needed to connect with parts?** Clinically, you can't just *know about* a part — you have to *feel with* it. Intellectual understanding ("I know I have a scared inner child") doesn't produce change; attuned resonance does. In graph terms: why isn't any edge sufficient? What's special about the edges created through attunement vs. cognitive acknowledgment? Hypotheses: (a) Attunement creates edges to *interoceptive/affective* nodes, not just propositional ones — and those are the nodes the modular subgraph is actually connected to internally. You have to meet the part where it lives. (b) Resonance = matching the precision regime of the part's subgraph, which is a prerequisite for message-passing across the new edge. A cognitive "I know about you" has the wrong precision profile to interface with a somatic/affective subgraph. (c) Attunement may be the mechanism by which protectors grant permission — the part's gating nodes detect "is the incoming signal safe/matching?" before allowing information flow.

12. **Partial vs. total witnessing**: IFS often involves degrees of witnessing — a part can be partially seen, partially understood, partially held. What does this look like computationally? Hypotheses: (a) Partial witnessing = partial reconnection. Some edges added but not all. The subgraph is no longer fully modular but not fully integrated either — some prediction errors can propagate but others can't. This would predict partial updating: some beliefs thaw while others remain frozen. (b) Partial witnessing = low-precision edges. The connection exists but the messages flowing through it are weak/uncertain. The part "knows" it's being seen but doesn't fully trust it yet. Updating happens but slowly. (c) Partial witnessing = reconnection at one hierarchical level but not another. You might connect the propositional content ("I understand what happened to you") without connecting the affective content ("I feel what you feel"). This maps to the clinical observation that intellectual insight without emotional contact doesn't heal. What determines whether witnessing deepens from partial to total? Is it a function of Self-energy, therapist attunement, or the part's own readiness (protector permission)?

---

## Status and Next Steps

**What's here**:
- Core conceptual framework
- Translation of major IFS constructs
- Narrative example
- Paper structure

**Planned edits**:
- [ ] Integrate chamberlain into the paper draft properly
- [ ] add a paragraph that explicitly separates: Clinical ontology (as-if agentic): the stance that makes the method work in vivo.  Computational ontology (precision / gating / structure): the stance that makes simulations tractable.
- [ ] distinguish at least two different “quiet” regimes: Quiet-protective (e.g., dissociation, numbing, pleasing): low overt conflict, but still part-led.  Self-led: includes curiosity/compassion + capacity to stay in contact with distress without suppression.
- [ ] split protector's action: policy + expected precision on [all the matrices: information + action] w/ learned trust variable (am I needed?)
- [ ] relational polarizations: polarization includes “each part’s model assigns high risk to the other part’s policy,”
- [ ] process active inference critique
- [ ] strengthen modularity structure (see critique)
- [ ] back off valence?
- [ ] Add a 1-page “precision & gating taxonomy” Define 3–5 precisions you mean (sensory, policy, learning/volatility, coupling/message passing), and then reuse those terms consistently.
- [ ] reframe therapy: relational active inference.

**High level next steps**:
- [ ] Figure out falsifiability loop. Phenomenology list seems most promising. https://claude.ai/code/session_01T4mHVLB1ysogdDZWmBWwpR
- [ ] Mathematical formalization (particularly: what updates during unburdening?)
- [ ] Figures (especially: transition probability visualization, before/after blending)
- [x] Decide on scope: Is Self in the main paper or appendix? it's in the paper.
- [ ] Notation review by someone with active inference expertise
- [ ] **Reach out to Active Inference Discord** to sanity-check the numbers and equations
---

