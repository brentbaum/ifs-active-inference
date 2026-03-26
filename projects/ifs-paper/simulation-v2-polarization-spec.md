# Two-Part Polarization Simulation: The Dog Encounter
## Two bundles competing for control under varying Self-energy

**Date:** 2026-03-26
**Purpose:** Extend the v2 single-bundle simulation to a two-part system where two bundles with conflicting policies compete for inferential dominance when a dog is present.
**Base:** ifs_model_v2.jl (three-move model with witnessed self-state channel)

---

## Scenario

A person sees a dog being walked by another person in a park. Two parts activate simultaneously with conflicting agendas:

**Part A — The Exile/Protector (avoid the dog):**
- Self-state: "I am small, helpless, alone with this"
- World-state: "Dogs are dangerous"
- Expected outcome: "Avoidance keeps me safe"
- Policy: AVOID (get away from the dog)

**Part B — The Social Manager (approach the human, act normal):**
- Self-state: "I am defective, must not be seen as weak"
- World-state: "People will judge me if I show fear"
- Expected outcome: "Social performance prevents rejection"
- Policy: APPROACH (walk toward the human, maintain composure)

**The conflict:** Part A says flee. Part B says approach. Neither is Self — both are parts with their own identity-level bundles. The person is caught between two captured states, oscillating or frozen.

**What Self-energy does:**
- Low E_t: one part captures and dominates (either flee OR force-approach, depending on which has higher precision). Oscillation possible — anti-phase switching.
- Medium E_t: both parts are partially active but no resolution. The person might approach awkwardly while internally panicking.
- High E_t: Self is present. Neither part dominates. The person can hold both — "a part of me wants to run, another part of me wants to look normal" — and choose from a place that isn't either part. The witnessed self-state channel opens for BOTH parts.

---

## Architecture

### Two Coupled Bundles

Each bundle is a v2-style model (3 hidden factors, 5 observation channels). The coupling occurs through:

1. **Shared observations:** Both parts receive the same external cues (dog present, human present)
2. **Competition for inference:** At each timestep, the system's posterior is a precision-weighted mixture of both bundles' predictions
3. **Self-energy governs the balance:** Low E_t → winner-take-all (one part captures). High E_t → both held in context.

### Implementation options

**Option A: Mixture of experts**
- Two separate generative models (Part A, Part B)
- Each produces predictions and policy preferences
- A mixing weight (governed by precision and Self-energy) determines which bundle dominates the posterior and action selection
- Under capture: mixing weight → 1.0 for dominant part
- Under context-held: mixing weight → balanced, with Self's perspective available

**Option B: Extended state space**
- Add a "dominant bundle" hidden factor: Part_A_dominant / Part_B_dominant / Neither_dominant
- Self-energy shifts precision on this factor
- The three-state factor determines which bundle's B matrices and A matrices are active
- "Neither dominant" = Self regime

**Option C: Extend existing polarization model**
- The existing ifs_polarization_model.jl uses a dynamical systems approach (not standard active inference)
- Could add the v2 observation channels and witness mechanism to this framework
- Simpler but less rigorous

**Recommendation:** Option A (mixture of experts) is cleanest. Two v2 models running in parallel, competing for behavioral control via precision-weighted mixing. Self-energy modulates the competition.

### Competition dynamics

```
At each timestep:
1. Both bundles observe the same stimuli
2. Each bundle computes its posterior and preferred policy
3. Effective precision of each bundle: π_A_eff, π_B_eff (modulated by Self-energy)
4. Mixing weight: w_A = π_A_eff / (π_A_eff + π_B_eff + π_self)
   where π_self increases with Self-energy (the system's own non-captured inference)
5. Policy selection: weighted mixture of Part A's policy, Part B's policy, and Self's policy
6. Under high Self-energy: π_self dominates → neither part controls → free choice from Self
7. Under low Self-energy: π_self ≈ 0 → parts compete → oscillation or capture
```

### Self-energy effects on both parts

When E_t is high enough:
- Channel 5 (witnessed self-state) opens for BOTH parts
- Part A's relational expectation ("I am alone with this terror") encounters Self's presence
- Part B's relational expectation ("I am defective, must perform") encounters Self's presence
- Both parts receive identity-level prediction error simultaneously
- The cascade can begin for both bundles at once

This is clinically accurate: in IFS, when Self is present, the therapist can work with BOTH parts — the scared exile and the social manager — from the same witnessing position.

---

## Experimental Conditions

### Condition 1: Low Self-energy (E_t = 0.15)
- Parts compete. Higher-precision part wins.
- Expected: Part A dominates (avoidance) OR oscillation between A and B
- No witnessed self-state for either part
- Behavioral: erratic — avoid, then approach, then avoid (oscillation) or pure avoidance

### Condition 2: Medium Self-energy (E_t = 0.50)
- Partial decapture. Both parts active but no resolution.
- Expected: awkward compromise — approach the human while internally panicking
- Minimal witnessed self-state
- Behavioral: approach with visible anxiety markers

### Condition 3: High Self-energy (E_t = 0.85)
- Self is present. Neither part captures.
- Witnessed self-state opens for both parts
- Both parts begin revision simultaneously
- Expected: person can hold both perspectives ("I'm scared AND I feel pressure to perform") and choose authentically — maybe approach at own pace, or acknowledge the fear to the human, or decide to cross the street without shame
- Behavioral: flexible, non-captured policy selection

### Condition 4: Anti-phase oscillation (E_t = 0.20)
- Just above baseline — enough for both parts to activate but not enough for resolution
- Expected: classic polarization — Part A activates, triggers Part B, which triggers Part A
- The system oscillates without settling
- This is the IFS "parts war" that therapists see clinically

---

## Predictions

1. **Low E_t:** One part dominates OR anti-phase oscillation. No cascade for either part.
2. **Medium E_t:** Both parts partially active. Threat meaning may revise for both but self-state doesn't. The person "knows" they're safe but still feels trapped between the two parts.
3. **High E_t:** Cascade begins for BOTH parts. Self-state revises first for both. The person is no longer captured by either part's identity claim. Flexible behavior emerges.
4. **The polarization resolves when Self-energy is sufficient for BOTH parts to be witnessed simultaneously.** This is the IFS clinical observation: you don't resolve a parts war by choosing one side. You resolve it by having enough Self-energy that both parts can be held.

---

## Figures

### Figure 1: "Two Parts, Three Regimes"
Three panels (low / medium / high E_t). Each panel shows:
- Part A self-state trajectory
- Part B self-state trajectory
- Policy mixing weight over time
- Behavioral output (avoid / approach / flexible)

### Figure 2: "Oscillation to Resolution"
Time series showing the transition from anti-phase oscillation (low E_t) to stable coexistence (high E_t). Self-energy increases over time (simulating therapy progress).

### Figure 3: "Dual Cascade"
Under high E_t: both parts' four-element cascades shown side by side. Self-state leads for both. Threat meaning follows for both. Different downstream — Part A's expected outcome shifts from "avoidance saves" to "I can handle the dog"; Part B's shifts from "performance prevents rejection" to "I don't need to perform."

---

## Relation to paper

- **§9 (Protectors and Polarization):** This simulation directly extends §9 with the v2 architecture
- **§8.3 (Relational PE):** Shows that the witnessed self-state mechanism works for MULTIPLE parts simultaneously
- **Clinical IFS:** The therapist doesn't take sides in a parts war — they bring Self-energy so both parts can be witnessed. This simulation formalizes that.

---

## Implementation notes

Build as ifs_polarization_v2.jl extending ifs_model_v2.jl:
- Two instances of the v2 model (Part A, Part B) with different initial priors and A/B matrices
- Shared observation generation (same dog, same human)
- Precision-weighted policy mixing
- Self-energy modulates both parts' capture indices and witness channel precision
- Track: both parts' posteriors, mixing weights, policy selection, behavioral output
