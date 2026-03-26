# Three-Move Simulation Specification (v2 — revised after GPT 5.4 critique)
## Full Bundle Cascade with Depth-Gated Self-Observation

**Date:** 2026-03-26
**Purpose:** One simulation that captures all three moves of the paper with the full four-element bundle and the relational depth mechanism.
**Language:** Julia (extends existing codebase in `projects/library/`)
**Base model:** `projects/library/src/active_inference/ifs_model.jl`

---

## Design philosophy

Elegance over exhaustiveness. The simulation proves one thing: witnessing is not a separate process from precision rebalancing — it is the deep case where present relational evidence reaches the organizing prior. Every hidden factor must earn its place. Downstream bundle elements (expected outcome, policy) are shown as consequences of upstream revision, not as separate latent states.

---

## What the paper claims and what the simulation must show

**Move 1:** Parts are identity-level precision bundles with self-state as the organizing prior. Under H1 (self-state upstream), revision cascades down through threat meaning → expected outcome → policy. Under H2 (threat-primary), no cascade.

**Move 2:** Self-energy governs the precision balance. It determines inferential regime: capture vs. context-held activation.

**Move 3:** Move 3 IS Move 2 at sufficient depth. When capture is reduced enough, the system can observe its own present-moment self-state. The part's relational expectation (isolation) meets the system's actual self-state (presence). That identity-level prediction error reaches the organizing prior and triggers the cascade.

**The simulation must show:** Under high Self-energy, self-state revises FIRST, then threat meaning follows, then expected outcome, then policy shifts — a four-element cascade visible in posterior trajectories. Under medium Self-energy, threat meaning moves but self-state barely budges. Under low Self-energy (exposure), all move slowly and uniformly.

---

## Scenario: The Dog Encounter

A person badly frightened by a dog as a child encounters an off-leash dog in a park.

**Part bundle (initial priors, high precision):**
- Self-state: "I am small, helpless, alone with this"
- World-state (threat meaning): "Dogs are dangerous"
- Policy: "I must avoid" (expressed through EFE biases, not a hidden factor)
- Expected outcome: "Avoidance keeps me safe" (optionally a hidden factor; can be derived)

**Present reality:**
- External context: Safe (the dog is friendly, no actual danger)
- The person's actual self-state: Adult, capable, not alone (if Self-energy is sufficient)

---

## Architecture

### Hidden Factors (3 factors, 2 states each)

Minimal model: same factorization as the existing ifs_model.jl but with the witnessed self-state observation channel added. Context is an environmental parameter, not a hidden factor.

| Factor | State 1 (burdened) | State 2 (revised) |
|---|---|---|
| **Self-state** | Helpless_Alone | Capable_Present |
| **Threat meaning** | Dangerous | Safe |
| **Expected outcome** | Avoidance_Saves | Contact_Manageable |

**Self-state** encodes both the identity claim ("I am small/helpless") and the relational expectation ("I am alone with this"). These are the same thing — the relational component lives inside the self-state element.

**Expected outcome** is the one added hidden factor. It earns its place because it is the bridge between threat meaning revision and behavioral change. Without it, the cascade has a missing link — we cannot track the four-element ordering the paper claims. It is dissociable from threat meaning: a person can believe "dogs aren't dangerous" while still believing "avoidance keeps me safe" (residual expected-outcome prior from the original bundle). That dissociability is what makes it worth tracking as a hidden state rather than deriving it.

**Open decision:** If implementation shows expected outcome tracks threat meaning too tightly (no independent variance), demote it to a derived readout and run with 2 hidden factors. Prefer the simpler model unless the data demands the richer one.

**Policy tendency** is NOT a hidden factor. It is a derived readout: the agent's prior/posterior over policies, influenced by expected outcome through EFE. This avoids duplicating what the policy inference engine already does.

**Context** is an environmental parameter. In the dog scenario, it is always Safe. It generates observations (external cues, informational context) but does not need to be inferred.

### Causal Architecture (H1: self-state upstream)

```
Self-state → Threat meaning → Expected outcome → [Policy selection via EFE]
```

B matrices encode:
- Self-state transitions: influenced by witnessed self-state observations (when precision is sufficient)
- Threat meaning transitions: conditioned on self-state (when self-state = Helpless, threat is biased toward Dangerous)
- Expected outcome transitions: conditioned on threat meaning (when threat = Dangerous, outcome is biased toward Avoidance_Saves)

H2 (threat-primary) reverses the upstream ordering: threat meaning drives self-state, not the other way around. This is the structural control for Move 1.

### Observation Channels (5 modalities)

| Channel | Outcomes | Depends on | Role |
|---|---|---|---|
| 1. External cue | Ambiguous / Clear_Safe / Clear_Threat | Threat meaning | World information |
| 2. Interoceptive arousal | Calm / Activated / Panic | Threat meaning + Self-state | Body signals |
| 3. Action outcome | Relief / Neutral / Harm | Expected outcome + Environment | Consequences |
| 4. Informational context | Alone_Overwhelmed / Supported_Here_Now | Environment | Room, body, therapist |
| 5. **Witnessed self-state** | Helpless_Alone / Capable_Present | Self-state (actual) | The system observing its own present-moment self-state in relation |

**Channel 5 ("witnessed self-state") is the key innovation.** It represents the system's ability to observe its own present-moment self-state. Under capture, this channel has near-zero precision. Under context-held activation at relational depth, it gains precision — not because a separate switch was flipped, but because capture has been reduced enough that self-observation becomes possible.

### Self-Energy: One Variable, Progressive Depth

Self-energy (E_t) is a single scalar. It modulates precision continuously. Move 3 emerges from Move 2 — there is no separate gate.

**Implementation:** Channel 5 precision is gated by the *inverse of capture*, not by a separate sigmoid on E_t.

```julia
# Existing: precision modulation
π_part_eff = r_t * π_part * exp(-β_se * E_t)
λ_ctx_eff = λ_ctx * exp(γ_se * E_t)

# Capture index
C_t = π_part_eff / (π_part_eff + λ_ctx_eff)

# NEW: Witnessed self-state precision tracks decapture
# When capture is high (C_t → 1), channel 5 is off
# When capture is low (C_t → 0), channel 5 opens
λ_witness = λ_witness_max * (1 - C_t)^α_witness * floor_term
# where α_witness > 1 makes this superlinear — channel 5 only opens
# substantially when capture is well below threshold
# floor_term = max(0, λ_ctx_eff - λ_floor) ensures that "low capture
# because everything is weak" does not count as witnessing.
# Both precisions must be meaningfully active, not just balanced at zero.
```

**Safeguard (from GPT 5.4 round 2):** Gate channel 5 by inverse capture AND an absolute context precision floor. If both part and context precisions are near zero (e.g., dissociative shutdown), the capture ratio can be low without genuine witnessing. The floor term prevents this artifact.

**Update ordering:** Compute C_t from prior beliefs and channels 1-4 observations first. Then open channel 5 for the current inference step. This avoids circularity where channel 5 affects C_t in the same timestep it depends on.

This means Move 3 is literally "what happens when Move 2 succeeds deeply enough." No second mechanism. The self-observation channel opens as a natural consequence of decapture. The superlinear exponent (α_witness > 1) ensures it only opens substantially at low capture — matching the clinical observation that relational depth requires more than just "not blended."

### Policies (Actions)

Same action space as existing model:
- **Avoid**: move away from the dog
- **Inspect**: approach/investigate
- **Stay**: remain present

Policy selection via Expected Free Energy, biased by expected outcome prior and current beliefs.

---

## Experimental Conditions

### Phase 1: Forced contact (T = 15-20 timesteps)

| Condition | E_t | Policy | Channel 5 | Expected result |
|---|---|---|---|---|
| Exposure | 0.15 | Forced inspect | Off (high capture) | Threat meaning moves slowly. Self-state stuck. No cascade. |
| Informational | 0.50 | Forced inspect | Weak (moderate capture) | Threat meaning moves faster. Expected outcome follows slightly. Self-state barely budges. |
| Relational depth | 0.85 | Forced inspect | Open (low capture) | Self-state crosses threshold FIRST. Cascade: threat → outcome → policy readout shifts. |

### Phase 2: Free-choice probe (T = 1-3 timesteps, learning frozen)

After forced contact, release policy to free choice. **Freeze learning** during probe — this is a behavioral assay, not a second intervention. The agent acts on its revised beliefs without further updating.

- Exposure agent: likely still avoids (self-state unchanged, policy prior intact)
- Informational agent: may approach tentatively (threat revised, self-state partly revised)
- Relational depth agent: approaches (self-state revised, cascade complete, policy readout shifted)

This is where behavioral revision becomes visible.

### Phase 3 (optional): Generalization probe

Present the SAME agent with a novel feared stimulus (different context cue, same bundle). The identity-level revision (Condition 3) should generalize; the threat-level revision (Conditions 1-2) should not.

**Probe stimulus design:** Ambiguous-safe. Same feared class (dog-like), moderate distance, visible affordance for approach, no attack cues, minimal extra reassurance. The stimulus should reveal revised priors, not overwhelm them with obvious evidence in either direction.

### Control conditions

| Condition | Purpose |
|---|---|
| Baseline (E_t = 0.1, free policy) | No contact → no revision. Avoidance. |
| Real danger (E_t = 0.85, context = Dangerous) | High Self-energy should NOT produce false safety. Tests specificity. |
| H2 architecture (all E_t levels) | Cascade should disappear under threat-primary ordering. Confirms Move 1. |

---

## Cascade Metrics (pre-registered)

Define these BEFORE running:

1. **Revision threshold**: posterior P(revised_state) > 0.5 (or a chosen criterion)
2. **First-passage time**: timestep at which each bundle element crosses the revision threshold
3. **Cascade lag**: difference in first-passage time between adjacent elements (self-state → threat → outcome)
4. **Cascade presence**: lag > 0 for all adjacent pairs AND self-state crosses first
5. **No-cascade criterion**: lags ≤ 1 timestep or elements cross in wrong order or don't cross at all
6. **Policy revision readout**: shift in policy posterior from avoid-dominant to approach/stay-dominant during free-choice probe

---

## Figures to Generate

### The One Figure (main paper figure)

**Composite figure.** Left inset: minimal causal-chain diagram (Self-state → Threat → Outcome → Policy) with Self-energy / capture balance as the global gate and the witnessed-self-state channel entering from below. Right main panel: three stacked heatmaps.

Each heatmap: rows = [Self-state, Threat, Expected Outcome, Policy readout], columns = time. Color = posterior probability of revised state.

- **Exposure**: weak, diffuse change. No diagonal.
- **Informational**: threat row changes; self-state row stays dark. Partial.
- **Relational depth**: change starts in self-state row and descends diagonally — visible cascade. Annotate the descending sequence once ("self-state → threat → outcome → policy").

The diagonal IS the paper's argument. All three moves are visible in one image.

**Figure refinements (from GPT 5.4 round 2):**
- Vertical divider between forced-contact and free-choice phases
- First-passage time markers (small dots/ticks) on each row — makes cascade order legible at a glance
- Label policy row concretely as `P(approach/stay)` not "policy readout"
- If space permits: tiny strip above each heatmap showing capture / witness precision over time (makes the diagonal mechanistic, not just descriptive)
- Identical row order and color scale across all three panels
- See `figure-inspiration.md` for Chamberlin 2022 precedent patterns

### Figure 2: "The Relational Depth Gap"

Self-state trajectory only, across three conditions. The gap between Informational and Relational Depth is where Move 3 lives.

### Figure 3: "Self-Energy Sweep"

Sweep E_t from 0 to 1. Plot final self-state revision. Shows that Move 3 is Move 2 at sufficient depth — sigmoid emergence, not a separate switch.

### Figure 4: "H1 vs H2"

Same relational-depth condition, but H2 architecture. Cascade disappears. Confirms Move 1: self-state must be upstream for the cascade to exist.

### Figure 5: "Free-Choice Probe"

Policy selection during Phase 2 across conditions. Relational depth agents approach; others still avoid. Behavioral consequence of the cascade.

### Figure 6 (optional): "Generalization"

Novel stimulus response. Relational depth agents show less fear; others don't.

---

## Implementation Notes

### Extending the existing codebase

Build as `ifs_model_v2.jl`:

1. **Add hidden factor 3 (Expected outcome)**: `num_states = [2, 2, 2]` (same as current, but third factor is now Expected Outcome instead of Context)
2. **Move Context to environment**: generate observations from Context parameter, don't infer it
3. **Add observation channel 5 (Witnessed self-state)**: 2 outcomes, precision gated by inverse capture
4. **Modify B matrices for H1 causal chain**: self-state → threat → outcome
5. **Add free-choice probe phase**: release forced policy after T_forced timesteps
6. **Policy readout**: track posterior over policies at each timestep as the derived "policy tendency"

### File structure
```
projects/library/src/active_inference/ifs_model_v2.jl    # New model
projects/library/scripts/ifs_simulation_v2.jl            # Simulation + figures
projects/ifs-paper/figures/                               # Output
```

### Run parameters
- Phase 1: T = 20 timesteps, forced inspect
- Phase 2: T = 1-3 timesteps, free choice, learning frozen
- N = 50+ trials for error bars
- Dog scenario: Context = Safe, bundle initialized with high-precision burdened priors

---

## Relation to paper sections

- **§3**: First simulation to track full bundle cascade
- **§6**: Depth-gated witnessed self-state is the formal implementation of Self-energy depth
- **§8.3**: Relational depth gap (Cond 2 vs 3) tests relational PE claim
- **§8.4**: Cascade order IS unburdening made visible
- **§8.5**: Three-condition comparison with mechanism specified
- **§12.2**: Limitation note about relational PE can be softened
- **§12.4**: Relational channel prediction now has simulation support

---

## Success criteria

1. Condition 3 shows four-element cascade with self-state leading
2. Gap between Conditions 2 and 3 on self-state is large (Move 3)
3. Gap between Conditions 1 and 2 on threat meaning is clear (Move 2)
4. Cascade disappears under H2 (Move 1)
5. Free-choice probe shows policy revision in Condition 3 only
6. Real-danger control shows no false safety
7. Results robust to ±20% parameter variation
