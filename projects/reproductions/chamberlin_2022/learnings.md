# Learnings (Chamberlin 2022 / Coherence Therapy)

Document insights, surprises, and lessons learned during simulation development.

## Implementation Results (2026-01-30)

**ALL 7 TESTS PASSED** - simulation validates Chamberlin's core hypothesis.

### Critical Implementation Insight: D1 Must Match Schema Mode

The most important discovery during implementation: **both A1 (likelihood) AND D1 (prior) must be schema-mode-dependent**.

**Initial Bug:**
- A1 uniform in modular mode (correct)
- D1 set to actual context with 98% confidence (incorrect)

This meant the agent "knew" it was safe even in modular mode - it just couldn't update from observations. Result: weak avoidance (P(avoid) ≈ 0.37).

**The Fix:**
```julia
if schema_mode == CT_SCHEMA_MODULAR
    D1_raw = [0.1, 0.3, 0.6]  # Fearful: bias toward dangerous
else
    D1_raw = fill(0.01, 3)
    D1_raw[context] = 0.98     # Accurate: knows actual context
end
```

**Conceptual Interpretation:**
A trauma-formed schema isn't just about observation processing - it represents a complete cognitive module that includes both:
1. How context cues are processed (A1 - uniform/identity)
2. What the default context belief is (D1 - fearful/accurate)

A trauma-formed schema assumes danger *because it was formed in danger*.

### C3 Preference Balance is Critical

The balance between approach and avoid preferences determines dynamics:
- C3[approach] = +2.0 (strong engagement goal)
- C3[avoid] = +1.0 (fallback avoidance pattern)

This creates the key trade-off:
- High expected harm → avoid dominates (harm aversion > engagement goal)
- Low expected harm → approach dominates (engagement goal wins)

---

## Design Phase Learnings

### On "Implicit" vs "Explicit" Beliefs (REVISED after full paper review)

**Initial design (from Architect review):** 3-state schema_mode (implicit/explicit/labile) focusing on gated learning.

**Revised insight from full paper:** The key distinction is **MODULARITY**, not just learning enablement.

From p6: "it is knowledge in the system, but it is not yet knowledge to the system...the implicit knowledge is 'modular'"

**Modular (implicit) schema:**
- Operates automatically, outside conscious control
- **Context-blind**: fires same policy regardless of current context
- Cannot be accessed by other cognitive processes
- Cannot be verbally reported
- Protected from belief updating

**Integrated (explicit) schema:**
- Consciously accessible, reportable
- **Context-sensitive**: policy selection considers current context
- Available to deliberative cognition
- Can be updated based on evidence

**Critical insight:** Discovery alone resolves symptoms in >50% of cases (p3). This suggests the mechanism isn't primarily about belief updating (which would require Juxtaposition). Instead, **making the schema context-sensitive is often sufficient** - the agent immediately recognizes "I'm not in that dangerous situation anymore."

**Simulation implementation:**
- Implicit = context cues not processed (A1 uniform) + fearful prior (D1 biased)
- Explicit = context cues integrated (A1 identity) + accurate prior (D1 informed)
- Resolution = agent recognizes current context doesn't warrant protective behavior
- No D-matrix update required for many cases (**confirmed by Test 4: CT D3 change = 0.0**)

### On Structure Learning
- Paper emphasizes *structure* learning, not just parameter learning.
- True structure learning (adding/removing factors) is complex.
- Our approach: gated A1 + D1 captures the essential "context-blindness" phenomenon
- Question resolved: Structural gating (not parameter update) is sufficient for resolution

### On Coherence Therapy vs. CBT Exposure
- Smith 2021 models CBT as gradual parameter learning (D matrix).
- Chamberlin proposes CT works via *different mechanism* (reconsolidation).
- **Confirmed:** CT produces step-function dynamics (change magnitude = 0.938 at trial 51)
- CBT produces gradual resolution via D3 learning (Test 2: P(avoid) → 0.027)

---

## Model Architecture Summary

### State Factors (Nf = 4)
1. **Context** (3 states): safe, ambiguous, dangerous
2. **Action** (4 states): wait, approach, avoid, report
3. **Threat** (2 states): threatening, non-threatening (THE SCHEMA)
4. **Schema_mode** (2 states): modular, integrated

### Key Design Choices

**A2 Harm Probabilities:**
| Context | Threat | P(harm\|approach) |
|---------|--------|-------------------|
| Safe | Any | 0.05 |
| Ambiguous | Threatening | 0.30 |
| Ambiguous | Non-threatening | 0.10 |
| Dangerous | Threatening | 0.90 |
| Dangerous | Non-threatening | 0.50 |

---

## Comparison to Smith 2021

| Aspect | Smith 2021 (CBT) | Chamberlin 2022 (CT) | Our Simulation |
|--------|------------------|----------------------|----------------|
| Learning type | Parametric | Structure/gated | Gated A1 + D1 |
| Mechanism | Accumulated evidence | Reconsolidation | Context-awareness |
| Key event | Many safe exposures | Single mismatch | Schema mode change |
| Symptom relief | Gradual | Discrete transition | Step function ✓ |
| Belief change | Required | Optional | Minimal (D3 change = 0) |

---

## Open Questions Resolved

1. **Is gated learning a good proxy for reconsolidation?**
   → Yes - gating A1 + D1 by schema_mode produces predicted dynamics

2. **How large must change be to count as "step function"?**
   → Change magnitude > 0.7 (we achieved 0.938)

3. **Can modularity-breaking alone cause resolution?**
   → Yes - CT shows resolution with D3 change = 0.0

## Discovery Process Model (Extension - 2026-01-30)

### Motivation

The original simulation showed instant behavioral change when schema_mode switched from modular to integrated. However, the paper describes Discovery as:
- "Resembles simulated annealing" - an iterative search process
- "Takes time and often requires scaffolding"
- Even after insight, behavioral change takes "weeks"

We consulted Codex's Architect expert, who recommended modeling Discovery as **gradual schema accessibility** rather than a separate therapist agent.

### Implementation: Three-Level Accessibility

**New state factor:** `schema_access` with 3 levels:
1. **Implicit** (α=0): Fully modular, no conscious access
2. **Partial** (α=0.5): Some access, can sometimes recognize context
3. **Explicit** (α=1): Fully integrated, conscious access

**Interpolation mechanism:**
```julia
A1 = (1-α) * A_modular + α * A_integrated
D1 = (1-α) * D_modular + α * D_integrated
```

**Simulated annealing via precision scheduling:**
- γ_min = 1.0 at implicit (high exploration)
- γ_max = 8.0 at explicit (high exploitation)

This captures the paper's description of Discovery as iterative hypothesis testing.

### Results

| Condition | % Reaching Explicit | Final P(avoid) | Trial to Explicit |
|-----------|---------------------|----------------|-------------------|
| Fast Discovery | 85% | 0.12 | 25 ± 0 |
| Standard Discovery | 65% | 0.16 | 46 ± 10 |
| Slow Discovery | 55% | 0.26 | 75 ± 24 |
| Original CT (instant) | 100% | 0.03 | 51 (fixed) |

### Key Insights

1. **Stochastic scaffolding**: Not all clients reach full explicit access, matching clinical reality
2. **Gradual behavioral change**: P(avoid) decreases progressively as access increases
3. **Exploration → Exploitation**: Low precision initially allows hypothesis testing
4. **Original tests preserved**: All 7 original tests still pass (Discovery configs are separate)

### Discovery Tests (7 additional tests)

| Test | What It Validates | Result |
|------|-------------------|--------|
| 1. Access increases | Mean access > 2.5 at end | ✓ PASS (2.83) |
| 2. Stochastic transitions | 30-95% reach explicit | ✓ PASS (83.3%) |
| 3. Behavior-access correlation | r < -0.3 | ✓ PASS (-0.689) |
| 4. Precision annealing | γ range > 3.0 | ✓ PASS (1.0→8.0) |
| 5. Fast vs Slow timing | Fast reaches explicit sooner | ✓ PASS (25 vs 81) |
| 6. Explicit has lowest avoidance | P(avoid\|explicit) < 0.2 | ✓ PASS (0.001) |
| 7. Access predicts resolution | Higher access → lower final P(avoid) | ✓ PASS |

**Total: 14/14 tests pass** (7 original + 7 Discovery)

### Design Decision: Why Not Separate Therapist Agent?

Codex recommended against hierarchical/nested active inference for therapist-client:
- Simpler: Therapist as exogenous scaffolding schedule is sufficient
- Captures key dynamics: Gradual accessibility with stochastic transitions
- Extensible: Could add therapist agent later if needed for dyadic dynamics

---

## Future Extensions

1. ~~**Gradual integration**: Currently schema_mode is binary; could model gradual accessibility~~ **DONE**
2. **Juxtaposition phase**: Explicit modeling of mismatch between schema and reality
3. **Multi-schema interactions**: Model competing schemas with different contexts
4. **Reconsolidation window**: Time-limited belief updating after integration
5. **Therapist as active inference agent**: Full dyadic model with therapist inference

---

## References Consulted

- Chamberlin (2022) - source paper
- Smith et al. (2021) - CBT active inference model (comparison)
- Ecker et al. (2012) - Coherence Therapy original clinical work (not active inference)
