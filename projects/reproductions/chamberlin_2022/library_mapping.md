# Library Mapping + Gaps (Chamberlin 2022 / Coherence Therapy)

This file maps simulation requirements to current library capabilities and identifies gaps.

## 1) Core Requirements (from paper concepts)

### Theoretical Claims to Test
1. Symptoms are Bayes-optimal under flawed generative model.
2. Implicit schemas resist updating from contradicting evidence.
3. Making schemas explicit enables reconsolidation (permanent update).
4. Juxtaposition (mismatch experience) is necessary for schema change.

### Simulation Needs
- Agent with "protected" beliefs that don't update normally.
- Mechanism to transition beliefs from protected to updateable.
- Therapist actions that influence agent's belief accessibility.
- Comparison: parametric learning vs. gated/structure learning.

## 2) Mapping to Current Library

### Basic Active Inference (HAVE)
- ✅ Hidden state factors with arbitrary dimensions.
- ✅ A/B/C/D matrix construction.
- ✅ Policy selection via expected free energy.
- ✅ State inference and belief updating.
- ✅ D matrix learning (parameter updates).

### From Smith 2021 Implementation (HAVE)
- ✅ Spider phobia model as base.
- ✅ Exposure therapy simulation.
- ✅ Forced policy mode (therapist-guided actions).
- ✅ P(safe) tracking over trials.

### Coherence Therapy Extensions (NEED)

| Requirement | Status | Notes |
|-------------|--------|-------|
| Gated learning (disable D updates) | 🔶 Partial | Can set η=0, but not state-conditional |
| State-conditional learning rate | ❌ Need | η depends on schema_explicit factor |
| External action on hidden state | 🔶 Partial | B matrix can encode, but "therapist" not modeled |
| Metacognitive observation | ❌ Need | Agent observing own beliefs |
| Multi-model inference | ❌ Need | For Candidate Model B |
| Hierarchical model | ❌ Need | For Candidate Model C |

## 3) Gap Analysis

### Gap 1: State-Conditional Learning
**Requirement:** Learning rate η for D[3] depends on value of factor 4.
**Current:** η is a global scalar in AIFSettings.
**Solution:** Modify `update_pD_final!()` to accept per-factor, state-conditional η.

```julia
# Pseudocode for state-conditional learning
function update_pD_conditional!(agent, factor_idx, condition_factor, condition_state, eta)
    if agent.beliefs[condition_factor] ≈ condition_state
        agent.pD[factor_idx] += eta * posterior_update
    end
end
```

### Gap 2: Therapist Actions on Hidden States
**Requirement:** External agent (therapist) can influence client's hidden states.
**Current:** Actions only affect states via B matrix; no "external input" pathway.
**Solution Options:**
1. Encode therapist actions in client's policy space (client "hears" therapist).
2. Model therapist as separate agent with coupled state space.
3. Script therapist actions as environment interventions.

### Gap 3: Metacognitive Observations
**Requirement:** Agent observes whether own schema is explicit.
**Current:** Observations come from environment, not self-reflection.
**Solution:** Add A matrix modality that maps schema_explicit to observation. This is actually standard—just add the modality.

### Gap 4: Tracking Prediction Error
**Requirement:** Measure mismatch magnitude during juxtaposition.
**Current:** Free energy computed but not decomposed by factor.
**Solution:** Add function to compute per-factor surprise/prediction error.

## 4) Minimal Implementation Path

### Phase 1: Extend Spider Model
1. Add factor 4 (schema_explicit) with 2 states.
2. Add modality 4 (metacognition) - deterministic observation of factor 4.
3. Modify B[4] to allow therapist-controlled transitions.

### Phase 2: Implement Gated Learning
1. Add `condition_mask` parameter to learning functions.
2. Only update D[3] when posterior over factor 4 favors "explicit".

### Phase 3: Simulation Protocol
1. Run N trials with schema implicit (no D[3] learning).
2. Apply "discovery" action (factor 4 → explicit).
3. Run N trials with schema explicit (D[3] learning enabled).
4. Compare to Smith 2021 baseline (always learning).

### Phase 4: Extend to Dyadic Model
1. Add therapist agent with model of client.
2. Therapist policy: minimize uncertainty about client schema.
3. Client receives therapist observations as additional modality.

## 5) Test Specifications

### Test 1: Schema Protection
- Run exposure with schema implicit.
- Assert D[3] unchanged after N trials.
- Assert avoidance policy persists.

### Test 2: Schema Discovery Enables Learning
- Run exposure with schema explicit from start.
- Assert D[3] updates toward safe.
- Assert approach policy emerges.

### Test 3: Full CT Protocol
- Start implicit, switch to explicit mid-simulation.
- Assert no learning before switch, learning after.
- Compare convergence speed to always-explicit baseline.

### Test 4: Mismatch Necessity
- Make schema explicit but provide schema-confirming observations.
- Assert limited D[3] change (no juxtaposition).
- Then provide contradicting observations.
- Assert D[3] change accelerates.

## 6) Reference Mapping

| Paper Concept | Library Primitive | Gap? |
|---------------|-------------------|------|
| Implicit schema | D[3] with protected precision | 🔶 |
| Explicit schema | D[3] with updateable precision | ✅ |
| Discovery | Transition factor 4 | 🔶 |
| Juxtaposition | High prediction error trial | ✅ |
| Reconsolidation | D[3] parameter update | ✅ |
| Symptom | Avoidance policy | ✅ |
| Therapist guidance | External action / forced policy | 🔶 |
