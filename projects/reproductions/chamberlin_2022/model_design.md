# Model Design (Chamberlin 2022 / Coherence Therapy)

**Status:** Design phase - no canonical model exists in the paper.

This document explores candidate generative model structures for simulating Coherence Therapy.

## Key Insights from Full Paper

### Discovery is often sufficient (p3)
> "successful Discovery of the precise symptom necessitating schema results in immediate and enduring cessation of the symptom in more than half of clients"

This suggests making the schema explicit may be more central than the Juxtaposition phase.

### Implicit = Modular (p6)
> "it is knowledge in the system, but it is not yet knowledge to the system...the implicit knowledge is 'modular'"

The schema operates automatically but can't be accessed by other cognitive processes (no context sensitivity, no verbal report, no deliberate control).

### Structure Learning, not Parameter Learning (p5)
> "Structure Learning...refers to learning the repertoire or narratives that constitute our prior beliefs"

CT involves creating NEW representations, not just updating existing belief parameters. This is fundamentally different from Smith 2021's gradual D-matrix learning.

### Memory Suppression Blocks Redescription (p10)
> "Suppression of the retrieval process...renders the related information unavailable for further processing e.g., representational redescription and inference"

### Stress Creates Context-Free Policies (p12)
> "a policy is selected...that requires minimal exploration and has minimal parameters e.g., no consideration of context"

The schema lacks episodic/contextual detail because it was formed under stress.

### Resolution = Context Embedding, Not Erasure (p14)
> "Rather than 'unlearning' or 'erasing' anything, she has learned a model...that contains an appreciation of its former utility and current irrelevance"

The new explicit schema IS context-sensitive: "necessary in some contexts but not others."

---

## Design Goal
Operationalize the key claim: Coherence Therapy works by making implicit (modular, context-free) schemas explicit (integrated, context-sensitive), which often immediately resolves symptoms by enabling context-appropriate policy selection.

---

## Candidate Model A: Modularity-Breaking Model

Based on the paper's emphasis on "modularity" as the key property of implicit schemas.

### Core Insight
The implicit schema is **context-blind**: it fires the same protective policy regardless of whether the current context warrants it. Making it explicit means making it **context-sensitive**.

### 1) Dimensions
- **Hidden state factors (Nf = 4)**
  - Factor 1: `behavior` (Ns1 = 5): start, approach, avoid, freeze, interact
  - Factor 2: `context_type` (Ns2 = 3): safe, ambiguous, dangerous
  - Factor 3: `threat_belief` (Ns3 = 2): threatening, non-threatening
  - Factor 4: `schema_mode` (Ns4 = 2): modular (implicit), integrated (explicit)

- **Outcome modalities (Ng = 4)**
  - Modality 1: proprioception (behavior observation)
  - Modality 2: context_cues (environmental signals about context type)
  - Modality 3: interoception (harm/neutral outcome)
  - Modality 4: metacognition (schema reportability)

### 2) Key Mechanism: Context-Sensitivity Gating

**When schema_mode = modular (implicit):**
- Policy selection IGNORES factor 2 (context_type)
- Agent always selects protective policy (avoid) regardless of context
- This is the "context-free" policy formed under stress
- D[3] does NOT update (schema is protected from revision)

**When schema_mode = integrated (explicit):**
- Policy selection CONDITIONS ON factor 2 (context_type)
- Agent selects avoid in dangerous context, approach in safe context
- D[3] CAN update based on context-specific observations
- This is "context embedding" - the schema is now integrated with broader cognition

### 3) Implementation

**A matrix for context_cues (A[2]):**
- When modular: uniform distribution (context cues not processed)
- When integrated: deterministic mapping from context_type

**Policy evaluation:**
```julia
function evaluate_policy(agent, policy)
    if agent.beliefs[:schema_mode] == :modular
        # Ignore context - always weight protective policy highly
        return evaluate_without_context(policy)
    else
        # Full EFE evaluation including context
        return evaluate_with_context(policy, agent.beliefs[:context_type])
    end
end
```

### 4) Coherence Therapy Mapping

| CT Phase | Model Operation | Effect |
|----------|-----------------|--------|
| Discovery | Transition schema_mode: modular → integrated | Context cues now processed |
| (Immediate resolution) | Agent recognizes current context is safe | Policy shifts to approach |
| Juxtaposition (if needed) | Present vivid safe-context + safe-outcome | D[3] updates rapidly |
| Verification | Reintroduce trigger in safe context | Agent maintains approach |

### 5) Predicted Behavior

**Modular (implicit) schema:**
- Agent in safe context still avoids (context-blind)
- No learning occurs despite safe outcomes
- "It is happening to me" - no sense of agency

**After Discovery (integrated/explicit):**
- Agent immediately recognizes "I'm not in the dangerous context anymore"
- Policy shifts to context-appropriate behavior
- "I don't need to do this anymore" - agency emerges
- Learning now possible (but may not be needed if context shift is sufficient)

### 6) Key Testable Prediction
**Resolution can occur WITHOUT belief updating** - just by enabling context-sensitivity.
This matches the paper's claim that Discovery alone resolves symptoms in >50% of cases.

---

## Candidate Model B: Dual Generative Models

Agent maintains two competing models, therapy shifts balance.

### 1) Structure
- **Model α (schema-based):** High precision priors, encodes protective belief.
- **Model β (evidence-based):** Lower precision priors, more responsive to data.

### 2) Inference
- Posterior = weighted average of model predictions.
- Weight determined by model evidence (free energy).

### 3) Therapy Mechanism
- Default: Model α dominates (schema-consistent behavior).
- Discovery: Agent becomes aware Model α exists (metacognition).
- Juxtaposition: Model α prediction error spikes.
- Reconsolidation: Model α precision drops; Model β dominates.

### 4) Implementation Challenge
Requires multi-model active inference (Bayesian model averaging or selection).
May need library extensions.

---

## Candidate Model C: Hierarchical Beliefs

Schema encoded at higher level of hierarchical model.

### 1) Structure
- Level 1: Immediate context inference (spider present, danger).
- Level 2: Schema inference ("world is dangerous", "I am vulnerable").
- Level 2 constrains Level 1 priors.

### 2) Therapy Mechanism
- Standard exposure updates Level 1 only (symptom suppression).
- Coherence Therapy targets Level 2 (schema change).
- Making schema "explicit" = attending to Level 2 beliefs.

### 3) Implementation Challenge
Requires hierarchical active inference (deep temporal models).
Significant library extension needed.

---

## Recommended Model: Enhanced Model A (Architect Review)

Based on architectural review, extend Model A with a **3-state schema_mode** factor that separates metacognitive access from learning enablement.

### Final Design (4 Factors)

| Factor | States | Role |
|--------|--------|------|
| f1: context | absent, present | Exogenous threat context |
| f2: action | start, approach, avoid, freeze, interact | Agent-controlled (same as Smith) |
| f3: outcome | reject/harm, accept/safe | Schema-bearing belief to update |
| f4: schema_mode | implicit, explicit, labile | Therapist-controlled, gates learning |

### Schema Mode States (Key Innovation)

| State | Metacognitive Access | Learning (η) | Meaning |
|-------|---------------------|--------------|---------|
| implicit | None (A_m4 uniform) | 0 | Can't report or update schema |
| explicit | Yes (A_m4 deterministic) | 0 | Can report schema, but frozen |
| labile | Yes | High | Reconsolidation window - brief, high learning |

**Critical insight:** "Making explicit" ≠ "learning enabled". Explicitness alone doesn't cause change; you need explicit + mismatch → labile → reconsolidation.

### Observation Modalities (4 Modalities)

| Modality | Maps From | Notes |
|----------|-----------|-------|
| m1: context_obs | f1 | Deterministic observation of threat presence |
| m2: outcome_obs | f3 (+ f1) | Actual outcome; mismatch trials deliver safe despite prior |
| m3: proprioception | f2 | Agent observes own action |
| m4: metacog_report | f3 gated by f4 | Uniform when implicit, deterministic when explicit/labile |

### Key Matrices

**A_m4 (Metacognition - Gated):**
```
if f4 = implicit:  A_m4 = uniform (no info about f3)
if f4 = explicit:  A_m4 = identity (reports f3)
if f4 = labile:    A_m4 = identity (reports f3)
```

**B_f4 (Therapist-Controlled Transitions):**
```
Discovery:      implicit → explicit
Juxtaposition:  explicit → labile (triggered by high prediction error)
Post-recon:     labile → explicit (after update completes)
```

**Learning Rule:**
```julia
function update_pD_reconsolidation!(agent, factor_idx)
    if agent.beliefs[:schema_mode] == :labile
        # High learning rate during reconsolidation window
        agent.pD[factor_idx] += η_high * posterior_update
    else
        # No learning outside labile state
        # Schema is protected
    end
end
```

### Coherence Therapy Simulation Protocol

1. **Baseline** (trials 1-N): schema_mode = implicit, expose to threat
   - No D_f3 update despite safe outcomes
   - Agent continues avoidance (symptom persists)

2. **Discovery** (trial N+1): therapist transitions implicit → explicit
   - Agent can now report schema ("I believe X is dangerous")
   - Still no D_f3 update

3. **Juxtaposition** (trial N+2): explicit + high mismatch → labile
   - Therapist ensures vivid contradicting experience
   - High prediction error triggers labile state
   - D_f3 updates rapidly toward safe

4. **Verification** (trials N+3 onward): schema_mode = explicit
   - Learning frozen again at new belief state
   - Agent now approaches (symptom resolved)
   - Test durability by reintroducing trigger context

### Testable Predictions

| Prediction | CT Model | CBT Baseline |
|------------|----------|--------------|
| Learning curve shape | Abrupt step at labile event | Gradual sigmoid |
| Explicit without mismatch | No change | N/A |
| Mismatch without explicit | No change | Gradual change |
| Durability (retest after delay) | Stable | Partial relapse |

### Implementation Steps

1. Add schema_mode factor (3 states) to spider model.
2. Add metacog_report modality with gated A matrix.
3. Implement state-conditional learning (η=0 outside labile).
4. Script therapist protocol as external state interventions.
5. Create mismatch trial generator (safe outcome despite dangerous prior).
6. Add tests comparing CT protocol to CBT baseline.

### Effort Estimate
**Medium (1-2 days)** - builds on existing spider model infrastructure.

---

## Open Questions (Resolved)

| Question | Resolution |
|----------|------------|
| Irreversibility | Labile → explicit after reconsolidation (not back to implicit) |
| Learning rate | η=0 for implicit/explicit, η_high for labile only |
| Mismatch magnitude | Prediction error threshold triggers explicit → labile |
| Therapist model | Scripted actions initially; can add agent later |
| Verification test | Approach policy selected, durability under context reintroduction |
