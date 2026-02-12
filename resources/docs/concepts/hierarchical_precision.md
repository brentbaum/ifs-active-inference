# Hierarchical Precision

**Summary:** In hierarchical generative models, higher-level states can parameterize the precision (inverse variance) of lower-level priors. This creates a mechanism where beliefs about uncertainty control how strongly new evidence updates beliefs.

---

## The Basic Idea

In a hierarchical model, a higher-level state can parameterize the **precision** (inverse variance) of a lower-level prior:

```
Level 2:  s₂ ~ p(s₂)           ← hyperprior
                ↓
          π = f(s₂)            ← precision is a function of higher state
                ↓
Level 1:  s₁ ~ N(μ, π⁻¹)       ← prior with state-dependent precision
                ↓
          x ~ p(x | s₁)        ← observations
```

---

## Concrete Example: Volatility

A common implementation is **volatility estimation**:

| Level | State | Controls |
|-------|-------|----------|
| 3 | Meta-volatility (ω) | How fast volatility changes |
| 2 | Volatility (v) | Precision of level-1 transitions |
| 1 | Hidden state (s) | Observable outcomes |

When volatility is **high** → precision is **low** → agent weights new observations heavily (fast learning).

When volatility is **low** → precision is **high** → agent trusts its prior (slow learning).

---

## Mathematical Form

For Gaussian hierarchical models (like HGF - Hierarchical Gaussian Filter):

```
s₁(t) ~ N(s₁(t-1), exp(κ·s₂(t)))
```

The variance `exp(κ·s₂)` of the level-1 transition depends on the level-2 state. Higher s₂ = more variance = lower precision = faster belief updating.

---

## In Active Inference / Dirichlet Models

Standard active inference implementations (like those in this repo) don't explicitly implement hierarchical precision, but there are analogous mechanisms:

### 1. Implicit via concentration parameters

```julia
# High concentration = high precision prior
pD = [100, 10]  # Very confident P(s=1) ≈ 0.91

# Low concentration = low precision prior
pD = [10, 1]    # Less confident, same expected value
```

### 2. Discrete gating (Chamberlin's schema_mode)

```
schema_mode = implicit  → η = 0 (infinite precision on prior, no learning)
schema_mode = labile    → η = high (low precision, rapid updating)
```

This is a **gating** mechanism rather than continuous precision modulation.

### 3. Action/Policy precision parameters

```julia
# From PMC7250191 model_design.md
alpha = 128  # Action selection precision (high = deterministic)
beta = 1     # Policy precision (gamma = 1/beta)
```

These control how sharply the agent commits to policies, not the priors themselves.

---

## Implementation Sketch

If you wanted hierarchical precision in Julia:

```julia
struct HierarchicalPrior
    μ::Vector{Float64}      # Expected value
    π_base::Float64         # Base precision
    volatility_state::Int   # Higher-level state controlling precision
end

function effective_precision(prior, volatility_beliefs)
    # Precision depends on inferred volatility
    v = expected_value(volatility_beliefs)
    return prior.π_base * exp(-v)  # High volatility → low precision
end
```

---

## Relevance to Therapy Models

In Chamberlin 2022's framing of coherence therapy:

- **Trauma** could be modeled as a frozen high-precision prior (won't update despite evidence)
- **Reconsolidation** temporarily reduces that precision (labile state)
- **Integration** establishes a new prior with context-appropriate precision

The current discrete `schema_mode` factor is a simplified version of what would be a continuous hierarchical precision mechanism.

---

## Key References

- **Hierarchical Gaussian Filter (HGF)**: Mathys et al. (2011, 2014) — canonical model for hierarchical precision
- **Predictive Processing**: Clark (2013), Hohwy (2013) — theoretical framework
- **Active Inference**: Friston et al. — precision as attention mechanism

---

## See Also

- [Precision](../key_terms.md#precision) — base concept
- [Opacity](../key_terms.md#opacity) — precision effects on phenomenology
- `paper_reproduction/chamberlin_2022/model_design.md` — discrete schema_mode gating
