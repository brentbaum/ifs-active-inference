# An Active Inference Account of Internal Family Systems
## Draft Outline v2 — March 2026

---

## Working Thesis

**Parts are modular subgraphs** of a single generative model that persist and dominate through graph disconnection. IFS therapeutic change is the progressive reconnection of these subgraphs to context — a graph-topological operation, not a parametric one.

**Presence** — the state IFS calls Self — is formally characterized by **maximum-entropy priors**: the least committal distribution across all domains of inference. This is positively distinct from both Part-domination (narrow, high-precision priors) and dissociation (selectively avoidant priors). The distinguishing variable is **prior entropy**, which the precision-balance formulation alone cannot name.

**The key move**: Parts dominate computation through modularity — isolated subgraphs of the generative model that, lacking edges to context variables, cannot generate context-dependent prediction errors, and therefore cannot update. Blending is what happens when such a subgraph captures policy selection: perception narrows, context is lost, and the system "becomes" the part. IFS therapy works by progressively reconnecting these isolated subgraphs to the full generative model (re-contextualization), at which point standard Bayesian updating operates on previously frozen priors.

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
  - A: likelihood (state -> observation mapping)
  - B: transition dynamics (state stickiness)
  - C: preference priors (what outcomes I want)
  - D: initial state priors
  - E: policy/habit priors
- Epistemic vs. pragmatic priors [per your notes with Shamil]:
  - Epistemic: beliefs about the world ("trees are green")
  - Pragmatic: preferences about outcomes ("I want to not be hungry")
  - Prediction error handling differs: epistemic -> update beliefs; pragmatic -> take action

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

- **Self / Presence**: The core, undamaged essence that can witness parts with curiosity and compassion
  - Qualities: calm, clarity, curiosity, compassion, confidence, courage, creativity, connectedness
  - Not a part — more like "what's there when no part is blended"
  - Has positive qualitative content — not merely the absence of Part-domination

- **Unburdening**: The process of releasing the extreme beliefs and emotions a part carries
  - Part no longer needs to hold the pain
  - Protectors can relax because there's nothing to protect against

- **Polarization**: Two parts in conflict, pulling the system in opposite directions
  - Can oscillate second-by-second or persist for years

---

### 2. The Model: Parts in Active Inference Terms

*[Goal: Mirror the Primer section, translating each concept into computational language]*

#### 2.1 What Is a Part? (Core Definition)

**Claim**: A part is a *modular subgraph* of the generative model — a cluster of associated priors that is disconnected (or weakly connected) from context-bearing nodes.

Breaking this down:
- The generative model contains all the organism's priors (beliefs, preferences)
- These priors are *always there*, but with varying precision (confidence weighting)
- A part is characterized by:
  1. A **set of associated priors** (e.g., "dogs are dangerous," "I am helpless," "I must run")
  2. A **precision hyperprior**: "how much should these beliefs dominate inference?"
  3. An **activation prior**: "I am needed" — triggered when the posterior over hidden states resembles the conditions under which the subgraph formed
  4. **Modularity**: weak or absent edges to context variables (current safety, adult resources, present-moment evidence)

**Key insight**: Parts don't have separate generative models. They are subgraphs within a single model whose disconnection from context explains both their persistence (frozenness) and their dominance (blending).

```
Part := {
  associated_priors: [p_1, p_2, ..., p_n],      // subset of generative model
  precision_hyperprior: pi_part,                  // how strongly to weight these
  activation_prior: P("I am needed" | context),   // when to activate
  modularity: edges(subgraph, context) ~ 0        // the structural property
}
```

**Phenomenological grounding: parts are not experienced as agents.** When a part is active, it doesn't feel like "an agent inside me is doing something." It feels like *me*. Full identification. "I am scared" — not "a scared agent has taken over." The "agentic" quality of parts (purposes, feelings, age) only becomes visible *after* partial unblending, when Presence can observe the part from some distance. IFS's practice of imagining parts as children or figures is a clinical technique — it facilitates unblending by creating representational distance, allowing meta-cognitive access to the modular subgraph. This is an in vitro solution: therapeutically effective, but not a description of the underlying mechanism. The computational model should reflect this: parts are subgraphs, not homunculi.

**Activation**: A part activates when the system's current or predicted world model resembles the conditions under which it formed. In Bayesian terms: P(part_active | s) goes high when the posterior over hidden states falls within the region the subgraph's priors were formed to handle. This includes interoceptive state — the body is part of the world model. A racing heart and tight chest can activate a part just as effectively as seeing a dog, because the physiological signature matches the encoding context.

*[See alternative models analysis: [docs/concepts/alternative-models-comparison.md](docs/concepts/alternative-models-comparison.md)]*

#### 2.2 Blending: Modular Subgraph Captures Policy Selection

**Claim**: Blending occurs when a modular (disconnected) subgraph of the generative model captures policy selection, causing its context-blind beliefs to dominate both perception and action.

This is the same modularity that explains frozenness (2.8), now seen from the other direction: modularity is both why the part *persists unchanged* (no prediction errors reach it) and why it *dominates when activated* (it doesn't condition on context that would moderate its predictions).

Mechanism:
- The part's subgraph lacks edges to context variables — it generates predictions without conditioning on current safety, adult resources, etc.
- Ambiguous stimulus (might be a dog?) -> the subgraph's context-blind prior ("dogs are dangerous, full stop") wins because it doesn't have to compete with context-dependent alternatives within its own inference
- Contradictory evidence (floppy ears, wagging tail) is processed by other subgraphs but cannot propagate *into* the modular part — so it doesn't update the driving beliefs
- Result: perception narrows to what the part "sees" (threat), action is constrained to the part's policies, and the system "becomes" the part

**Why blending is hard to break from inside** (stickiness):
- The modular subgraph has no incoming edges that could deliver disconfirming evidence
- Its own predictions are self-consistent within its closed loop
- The part's activation increases precision on its associated priors, which further suppresses competing signals — a positive feedback loop
- Breaking blending requires an *external* intervention (therapist, Presence, environmental change) that can bypass the modularity

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
- In policy notation: pi_manager biases toward trajectories where P(exile_trigger) -> 0

##### 2.3.2 Firefighters (Rapid Reactive Policies)

**Claim**: Firefighters are low-level reactive policies that rapidly minimize acute free energy when a trigger slips through.

- Low temporal depth — immediate action, consequences later
- Activated when manager policies fail and exile activation begins
- Examples: dissociation, substance use, bingeing, impulsive behavior
- In policy notation: pi_firefighter selected when free energy spike detected, optimizes for immediate F reduction regardless of long-term G

##### 2.3.3 Exiles (Frozen Affective Priors)

**Claim**: Exiles are modular (disconnected) prior clusters encoding the emotional, somatic, and belief state from an overwhelming experience. They are frozen because they are isolated.

- Not just memories — entire *states* of the generative model from that moment
- "I am helpless," "I am unlovable," "I am in danger" — with high precision
- When activated, their predictions dominate (blending occurs)
- Protectors exist specifically to prevent exile priors from being activated

#### 2.4 Unblending: Restoring Dispersed Precision

**Claim**: Unblending is the shift from a winner-take-all, high-precision micro-model back to a balanced, multi-modal predictive regime.

Mechanism:
- Reduce precision on the active part's associated priors
- Allow other priors (including Presence-associated ones) to re-enter competition
- Restore access to broader context, resources, present-moment evidence

Progression observed in therapy:
- Part A active -> Part B active -> Presence-like state -> Presence
- Each transition = precision rebalancing

**Relation to epistemic depth**: Unblending may increase epistemic depth — considering more hypotheses about the situation rather than collapsing to one.

#### 2.5 Presence: Maximum-Entropy Inference

**Working hypothesis**: Presence (what IFS calls Self) is not a part but a *regime* of the generative model characterized by **maximum-entropy priors** — the least committal distribution across all domains of inference.

This is not "no prior" (computationally vacuous). It is *maximally open* prior — the distribution that makes the fewest commitments, least screens out what arrives, and therefore encounters what is actually arising rather than what was predicted.

**The crucial formal property**: Maximum-entropy priors and high-precision Part priors are opposites on the same spectrum. Parts inference narrows. Presence inference widens.

**Precision vs. entropy**: Precision is a local parameter — the inverse variance of a specific distribution at a specific node. Entropy is a global property — a measure of how much uncertainty the whole model expresses. For a single Gaussian, they move inversely (higher precision = lower entropy). But Presence isn't just "low precision on one Gaussian" — it's a property of the entire generative model across many domains and distributions. Entropy is the right level of description.

**Solving the dissociation problem**: The previous Self-as-balanced-regime formulation (v1 Section 2.5) risked conflating Presence with dissociation, since both look "quiet." Prior entropy is the distinguishing variable:

| State | Arousal | Part activation | Prior entropy | What's happening |
|---|---|---|---|---|
| **Part-dominated** | High | One part dominant | Low (narrow priors screening) | Modular subgraph captures inference |
| **Dissociation** | Low | Low overt activation | **Low** — selectively avoidant | System predicts with high precision that certain content won't arrive. The prior has a *hole* — organized around absence. Quiet because screening, not because open. |
| **Presence** | Low-moderate | No part dominant | **High** — genuinely flat | Nothing screened. Whatever arises can generate prediction errors and update beliefs. Quiet because *open*. |

**Presence-energy** as a *hyperprior favoring maximum-entropy priors*:
- More Presence-energy -> lower ceiling on how much any part can dominate
- This is a system-wide parameter, distinct from part-specific reconnection

**Why Presence has specific qualities**: Each quality corresponds to maximum-entropy inference in a *specific domain*, which is why they feel different from each other — different shapes of openness — while sharing the common property of non-defensive priors.

| Quality of Presence | Domain of Maximal Openness | Computational Property |
|---|---|---|
| **Curiosity** | Epistemic space | High information-seeking drive; no part forcing avoidance of uncertainty |
| **Calm** | Threat estimation | Prior on danger reflects actual base rates, not inflated by modular threat-priors |
| **Clarity** | Perceptual inference | High signal-to-noise; no modular subgraph injecting context-blind predictions |
| **Compassion** | Affective-interpersonal (with suffering present) | Openness that doesn't recoil; accurate tracking of others' states without protective distortion |
| **Courage** | Uncertainty-approach / action space | Full capacity to approach high-uncertainty states; epistemic drive outweighs avoidance |
| **Creativity** | Policy space | High entropy over possible actions; not collapsed to one protective strategy |
| **Connectedness** | Relational inference | No prior on separation; attending to relational signals rather than suppressing them |
| **Confidence** | Self-model | Well-calibrated precision — neither over-confidence of a blended protector nor under-confidence of a blended exile |

**Testable prediction**: These qualities should co-occur in practice because they share the same underlying condition (maximum-entropy priors across domains). You shouldn't find genuine Courage without some Compassion, genuine Curiosity without some Calm — they're different expressions of the same prior structure, not independent capacities. All should increase as modularity decreases.

**Presence does not need to be modeled explicitly.** It falls out as "what inference looks like on a generative model with maximum-entropy priors and no modular domination." This is consistent with the IFS phenomenology: Presence is not something you build — it's what's revealed when parts step back.

**Honest boundary**: The active inference account captures the *formal structure* of Presence — maximum-entropy priors, domain-specific openness, the dissociation distinction — but cannot capture its *phenomenological character*. Why maximum-entropy in the interpersonal domain feels like the warmth and tenderness of love, rather than simply "more open relational inference," is not a question active inference can answer. The computational account (Marr's level 2) describes the conditions under which Presence arises; the phenomenological account describes what Presence is like from the inside. These are complementary levels of description, not competitors.

#### 2.6 Unburdening: Restoring Plasticity

**Claim**: Unburdening releases the part's meta-level identification with its beliefs, restoring their plasticity (updateability).

The burden isn't just a belief with high precision — it's a belief that *won't update*. Trauma-formed priors have a **closed learning window**: consolidated under extreme stress, they became fixed points resistant to revision despite contradictory evidence.

Before unburdening:
- Part holds beliefs as essential/unchangeable ("This is who I am")
- Meta-belief: "I must hold this / releasing it would be annihilation"
- First-order beliefs don't update despite new evidence
- Learning window is closed

After unburdening:
- Meta-level grip is released
- First-order beliefs become updatable again
- Part can now learn from experience (e.g., "the world is safe now")
- Part often looks/feels different — frozen structure has dissolved

This is distinct from:
- **Unblending** (momentary precision redistribution)
- **Welcoming** (breaking modularity, context-embedding)

Unburdening is a *structural change* to the belief's updateability, not its precision or accessibility.

*[Note: This aligns with memory reconsolidation — returning consolidated memories to a labile state. See Section 2.8 for how this fits with the other mechanisms.]*

#### 2.7 Polarization: Oscillating Inferential Competition

**Claim**: Polarization occurs when two parts alternate in winning inferential competition, with neither achieving stable dominance.

- Can oscillate rapidly (seconds) or slowly (days/weeks)
- Each part's activation may trigger the other (e.g., inner critic -> defeated child -> inner critic)
- System gets stuck in limit cycle rather than settling

#### 2.8 Two Mechanisms of Therapeutic Change

*[See prior analysis: [docs/concepts/chamberlin-critique-three-mechanisms.md](docs/concepts/chamberlin-critique-three-mechanisms.md)]*
*[See unification argument: [docs/concepts/recontextualization-as-unfreezing.md](docs/concepts/recontextualization-as-unfreezing.md)]*

The previously proposed three mechanisms (Self-energy increase / Welcoming / Unburdening) reduce to two. Welcoming and unburdening are the same mechanism — re-contextualization — operating at different depths.

| Mechanism | Computational Operation | What Changes |
|-----------|------------------------|--------------|
| **Presence-energy increase** | Global hyperprior favoring max-entropy priors | System-wide parameter; enables the work |
| **Re-contextualization** | Progressive reconnection of modular subgraphs (structure learning) | Accessibility, context-embedding, AND updateability — simultaneously |

**Presence-energy increase** = global precision gating toward maximum entropy. More Presence-energy means any individual part can dominate less. This is a system-wide parameter that *enables* reconnection (you can't do graph surgery while fully blended) but isn't reconnection itself.

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
| Part | Modular subgraph: cluster of priors + precision hyperprior + activation prior, disconnected from context | Subgraph S, edges(S,C) ~ 0 |
| Blending | Modular subgraph captures policy selection; context-blind priors dominate | pi_P >> pi_other; edges(S,C) = 0 |
| Unblending | Precision redistribution restoring balanced inference | pi_P ~ pi_other |
| Exile | Modular prior cluster from overwhelming experience; frozen because isolated | Subgraph S, edges(S,C) = 0 |
| Manager | Policy prior with high temporal depth avoiding exile triggers | pi_mgr: minimize P(exile_trigger) over trajectory |
| Firefighter | Reactive policy prior minimizing immediate free energy | pi_ff: minimize F(t) |
| Presence / Self | Maximum-entropy inference regime; high prior entropy globally, no domain screened | H(priors) -> max; no part dominant |
| Welcoming / Unburdening | Re-contextualization: reconnecting modular subgraph to context network | Add edges(S,C); depth varies by consolidation strength |
| Polarization | Oscillating precision dominance between two parts | pi_A <-> pi_B |
| Presence-energy | Hyperprior favoring max-entropy priors across all domains | H(priors) -> max system-wide |
| Dissociation | Selective high-precision avoidance; looks quiet but entropy is low | H(priors) low; specific domains screened |

---

### 4. How IFS Therapy Works: Precision Dynamics in Session

#### 4.1 The Core Operation: Reconnection

IFS therapy involves:
1. **Presence-energy** sufficient to prevent full blending (global max-entropy gating)
2. **Attending to a part** — directing precision toward the modular subgraph to make its contents reportable
3. **Witnessing** — connecting the part's isolated beliefs to current context (Presence's perspective, present safety, adult resources)
4. This reconnection enables standard Bayesian updating on previously frozen priors — the witnessing IS the change mechanism, not merely its prerequisite

*[This mirrors Chamberlin's Discovery mechanism. For deeply consolidated priors, vivid juxtaposition (high-precision contradictory evidence through the new channel) provides the additional prediction error needed.]*

#### 4.2 Step-by-Step Session Dynamics

**Phase 1: Accessing a Part**
- Therapist guides attention to felt sense (interoceptive precision up)
- Part's associated priors become more active
- Controlled partial blending — enough to feel the part, not enough to lose Presence

**Phase 2: Witnessing/Unblending**
- Maintain dual awareness: part's experience AND Presence's curiosity
- Therapist's regulation co-regulates client's precision dynamics
- "How do you feel toward that part?" — checking for Presence-energy

**Phase 3: Learning the Part's Role**
- Part reveals its protective function (what it's trying to prevent)
- System begins to understand part's "I am needed" prior

**Phase 4: Working with Exiles** (if appropriate)
- Protectors give permission to access exile
- Exile's frozen priors become active (controlled blending)
- Witnessing by Presence creates context that wasn't present during trauma

**Phase 5: Unburdening**
- Exile releases the extreme beliefs/emotions
- Precision bound on exile's priors decreases
- Protectors can relax — nothing to protect against

#### 4.3 Two Paths to Healing

1. **Increasing Presence-energy**: Strengthen the hyperprior toward maximum-entropy priors
   - All parts become less able to fully blend
   - More natural access to Presence qualities

2. **Unburdening specific parts**: Reconnect individual modular subgraphs
   - Target specific trauma-based priors
   - Part-by-part liberation

*[These interact: unburdening parts may increase global Presence-energy, and higher Presence-energy may facilitate unburdening]*

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
2. Exile's high expected precision for dog-threat -> boosts threat interpretation
3. Evidence for "not a dog" (floppy ears, wagging tail) gets low precision -> discounted
4. Exile fully blends -> person feels small, terrified, helpless
5. Firefighter policy activates -> freeze or run
6. Manager updates: "Never walk on this street again"

**Subjective experience**: "I became a terrified child. I couldn't think. I just had to get out of there."

#### 5.2 During Therapy

**Session work**:
1. Therapist helps client access the exile (controlled precision increase)
2. Presence witnesses the exile's experience with compassion
3. Exile receives what it needed (attention, validation, updated information: "You survived. You're an adult now. Not all dogs are dangerous.")
4. Prediction error from contradictory evidence + high precision on therapeutic context -> belief update
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
P(part_active | observation) ~ pi_part * P(observation | part_priors)
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
- How to formalize prior entropy as a system-level measure across the whole generative model?

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
- Same core mechanism: raise precision -> access prior -> prediction error -> update
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
- **Honest boundary**: The computational account of interoception is at the level of mechanism — "the body is part of the generative model." Phenomenological accounts of somatic experience (Gendlin's felt sense) operate at a different level of description. "The body is the field of intelligence through which Presence is known" is a richer ontological claim than the active inference account makes room for. The paper should name this explicitly rather than let the computational framing quietly colonize the phenomenological.

*[References to develop: state-dependent memory literature, reconsolidation (Ecker et al.), interoceptive inference (Seth), active inference accounts of PTSD, Gendlin (felt sense)]*

#### 8.3 Relationship to "The Beautiful Loop" / Schema Therapy Models
*[Need to re-read and integrate]*

#### 8.4 Integration vs. Transmutation: What Is the Therapeutic Endpoint?

The model accommodates two different accounts of what happens after re-contextualization:

**Integration (reconnection with persistence)**: The part is reconnected and persists with a new role. The subgraph remains in the system, now better connected. Protectors shift to "trusted" functions. Parts remain parts — they are rehabilitated, not eliminated. This is re-contextualization with reification: the Part is now a normal node, but it's still a node.

**Transmutation (reconnection with dissolution)**: The part dissolves back into living process. The frozen structure melts; what was crystallized returns to the flow from which it formed. The goal isn't a healthier parliament of parts — it's fewer parliamentarians, more alive presence. This is re-contextualization with dereification.

In computational terms: reconnection is the shared operation. If subsequent inference thoroughly updates the subgraph's parameters through the new edges — to the point where its predictions become indistinguishable from the surrounding generative model — the "part" may cease to be a distinguishable subgraph at all. Integration and transmutation may be points on a continuum of how much updating occurs after reconnection, not categorically different operations.

This is a genuine choice point with clinical implications. A model that treats the endpoint as "integrated part with a new role" supports one kind of work. A model that treats the endpoint as "dissolved back into living process" supports a different kind — less mapmaking, more willingness to let the structure go entirely. The paper names this as an open question rather than resolving it.

#### 8.5 Where Active Inference Reaches Its Limits: Depths of Description

The paper operates primarily at what we might call the **Depth of Parts** — the domain of beliefs, precision weights, prediction errors, and Bayesian updating. Active inference is a powerful and precise account at this depth. But it is worth being explicit about what lies at and beyond the edges of the framework.

| Depth | What the Paper Formalizes | What the Framework Cannot See |
|---|---|---|
| **Parts** | Modular subgraphs, reconnection, blending, protector dynamics | Fully formalizable |
| **Presence** | Maximum-entropy priors, domain-specific openness, dissociation distinction | Captures formal conditions; cannot capture phenomenological character (why openness in the relational domain *feels like warmth*) |
| **Nondual** | -- | Outside the framework. Presence is still a mode of the generative model — a particular shape of prior held by an agent. The Markov blanket (the statistical boundary constituting the self) is still operative. The recognition that this boundary is a useful local carving, not an ultimate fact, is not something active inference can model from inside itself. |

This is not an incomplete paper. It is a paper that knows what it can formalize, and names where the formalization ends. The computational account and the phenomenological account are complementary levels of description — Marr's level 2 and lived experience, respectively. The active inference model tells you the conditions under which Presence arises; it cannot tell you what Presence is like from the inside. That is an honest boundary, not a failure.

*[Note: Maximum-entropy inference can be understood as a formal model of aletheia — unconcealment. A prior structure that screens nothing out allows what is actually present to disclose itself, rather than organizing experience into the already-expected. The relationship between the computational thesis and this philosophical concept may be worth noting.]*

#### 8.6 Presence-Energy, Awakening, and Epistemic Depth
- Presence-energy relates to the global hyperprior on max-entropy priors (pragmatic: how to be)
- Awakening/dereification relates to *epistemic* priors (beliefs about reality itself)
- IFS increases Presence-energy but doesn't directly target epistemic opacity
- Meditation practices may work on epistemic precision bounds
- Could explain why IFS and meditation are complementary

#### 8.7 Clinical Implications
*[What predictions does this model make? What would it look like if it were wrong?]*

---

### Appendix A: Active Inference Notation Reference

| Symbol | Meaning |
|--------|---------|
| o | Observations |
| s | Hidden states |
| pi | Policy |
| A | Likelihood matrix: P(o \| s) |
| B | Transition matrix: P(s' \| s, u) |
| C | Preference prior: P(o) preferred |
| D | Initial state prior: P(s_0) |
| E | Policy prior (habits) |
| F | Free energy |
| G | Expected free energy |
| pi (overloaded) | Precision (context-dependent) |
| H | Entropy |

---

### Appendix B: Open Questions and Future Directions

1. **Identification**: How to model "I am this part" vs "I have this part"? (See Metzinger on units of identification)

2. **Safety**: Is safety a global hyperprior that modulates all parts' precision bounds? Or do parts have their own safety estimates?

3. **Compatibility of beliefs**: How do we model parts that hold mutually exclusive beliefs? (Inferential competition suggests they literally can't both be active)

4. **Memory reconsolidation**: What's the relationship between our re-contextualization account and the biological process of reconsolidation?

5. **Therapist modeling**: Should we explicitly model the therapist as a second agent in dyadic active inference?

6. **[RESOLVED] Three distinct mechanisms -> Two**: Welcoming and unburdening are the same mechanism (re-contextualization / reconnection of modular subgraphs) operating at different depths.

7. **[RESOLVED] Frozen = disconnected**: Priors are "frozen" because they are modular (disconnected from context), not because of a separate plasticity lock.

8. **Hierarchical identity locks**: Some schemas have a higher-order wrapping: "this belief IS who I am." This may represent deeper modularity (isolation at a higher level of the graph) rather than a categorically different mechanism.

9. **[PARTIALLY RESOLVED] Spontaneous vs. explicit unburdening**: Shallow modularity resolves on reconnection alone (~50%). Remaining question: can we predict which cases will be shallow vs. deep from observable pre-therapy measures?

10. **[RESOLVED] Chamberlin's modularity critique**: Modularity IS the core mechanism. The fundamental operation of change is graph-topological.

11. **[RESOLVED] Dissociation vs. Presence**: Prior entropy is the distinguishing variable. Dissociation = selectively avoidant high-precision priors (low entropy). Presence = genuinely flat priors (high entropy). See Section 2.5.

12. **Why is attunement / resonance needed to connect with parts?** Clinically, you can't just *know about* a part — you have to *feel with* it. Hypotheses: (a) Attunement creates edges to *interoceptive/affective* nodes, not just propositional ones. (b) Resonance = matching the precision regime of the part's subgraph, prerequisite for message-passing. (c) Attunement may be the mechanism by which protectors grant permission.

13. **Partial vs. total witnessing**: IFS often involves degrees of witnessing. Hypotheses: (a) Partial witnessing = partial reconnection — some edges but not all. (b) Low-precision edges — connection exists but messages are weak. (c) Reconnection at one hierarchical level but not another (propositional but not affective).

14. **Formalizing prior entropy as a system-level measure**: How to compute entropy across a heterogeneous factor graph with distributions of different types? This is needed to make the Presence/dissociation distinction formally precise rather than merely conceptual.

---

## Status and Next Steps

**What's here**:
- Core conceptual framework with modularity as primary mechanism
- Presence as maximum-entropy inference (replacing Self-as-balanced-regime)
- Dissociation/Presence distinction via prior entropy
- Integration vs. transmutation as named open question
- Four-depth framework locating the paper's scope
- Translation of major IFS constructs
- Narrative example
- Paper structure

**What changed from v1**:
- Working thesis rewritten: modularity primary, precision secondary
- Self -> Presence throughout; maximum-entropy formulation replaces balanced-precision
- Prior entropy named as the variable distinguishing Presence from dissociation (resolves v1 TODO)
- Integration vs. transmutation discussion added (Section 8.4)
- Depths of description section added (Section 8.5) — honest about what the framework can/cannot formalize
- Honest boundary on interoception/phenomenology added to Section 8.2
- Valence claim (always <= 0) removed — not load-bearing
- Self-energy -> Presence-energy throughout
- Exiles definition simplified (frozen because isolated — no "open question" about the metaphor)

**Planned edits**:
- [ ] Integrate Chamberlin into the paper draft properly
- [ ] Add a paragraph explicitly separating clinical ontology (as-if agentic) from computational ontology (precision / gating / structure)
- [ ] Split protector's action: policy + expected precision w/ learned trust variable (am I needed?)
- [ ] Relational polarizations: each part's model assigns high risk to the other part's policy
- [ ] Strengthen modularity structure (see critique)
- [ ] Add a 1-page "precision & gating taxonomy" — define 3-5 precisions and reuse consistently
- [ ] Reframe therapy: relational active inference
- [ ] Formalize the entropy measure for a heterogeneous factor graph

**High level next steps**:
- [ ] Figure out falsifiability loop. Phenomenology list seems most promising.
- [ ] Mathematical formalization (particularly: what updates during unburdening? how to formalize prior entropy?)
- [ ] Figures (especially: transition probability visualization, before/after blending, entropy landscape)
- [ ] Notation review by someone with active inference expertise
- [ ] Reach out to Active Inference Discord to sanity-check
