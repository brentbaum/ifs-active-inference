# Key Terms: Active Inference & Consciousness

> **Instructions:** When adding a term, include a brief citation to where examples and definitions can be found elsewhere in this repo (paper name, section). This helps with cross-referencing during review.

---

## Precision

**What is precision applied to?** Precision is (always) applied to prediction error.

```
weighted update = prediction error × precision
```

Precision is inverse variance (1/σ²) — a measure of confidence or reliability. It modulates how much a given prediction error influences belief updating. High precision = this error matters, update strongly. Low precision = this error is unreliable, discount it.

**See also:**
- `papers/limanowski_friston_2018_seeing_the_dark/paper.md` — Precision as the mechanism for attention and transparency/opacity
- `papers/limanowski_blankenburg_2013_minimal_self/paper.md` — Precision weighting in hierarchical self-models

---

## Opacity

The degree to which the generative world model is aware of itself as a construction—when the representational nature of experience becomes introspectively accessible. An opaque representation appears "as being constructed by one's mind" rather than as direct contact with reality.

**Mechanism:** Opacity emerges when precision is deployed to prediction errors about internal states via introspective attention. High meta-level precision × high meta-level prediction error → opacity.

**Examples:** Lucid dreaming, deliberate thought, pseudo-hallucinations, mindfulness meditation, philosophical reflection on perception.

**See also:**
- `papers/limanowski_friston_2018_seeing_the_dark/paper.md` — Full treatment of opacity/transparency in precision terms
- `papers/limanowski_blankenburg_2013_minimal_self/paper.md` — Pathological opacity in depersonalization

---

## Hierarchical Precision

A mechanism in hierarchical generative models where higher-level states parameterize the precision (inverse variance) of lower-level priors. This allows the system to represent beliefs about uncertainty itself—how confident to be in predictions at each level.

**Mechanism:** A higher-level state (e.g., volatility) controls the precision of transitions at lower levels. High volatility → low precision → fast learning from new evidence. Low volatility → high precision → trust existing beliefs.

**Key insight:** This separates "what I believe" from "how confident I am in that belief"—and makes confidence itself learnable.

**Examples:** Volatility estimation in HGF, attention as precision optimization, trauma as aberrant precision (frozen high-confidence priors).

**See also:**
- `docs/concepts/hierarchical_precision.md` — detailed explanation with implementation notes
- `paper_reproduction/chamberlin_2022/model_design.md` — discrete schema_mode as simplified version

---

## Transparency

The default mode of conscious experience where mental representations feel like direct, unmediated contact with mind-independent reality—"like looking through a window onto the world." The construction process remains inaccessible to introspection.

**Mechanism:** Transparency is the default when predictive models successfully suppress prediction errors. The machinery of inference is invisible precisely because it's working.

**Key property:** Beliefs about action cannot become opaque because they generate the very precision expectations that enable opacity elsewhere. The self-as-agent must remain transparent.

**Examples:** Perceiving colors, experiencing body location, sense of agency, flow states.

**See also:**
- `papers/limanowski_friston_2018_seeing_the_dark/paper.md` — "Seeing the Dark" title refers to making uncertainty (darkness) visible
- `papers/laukkonen_friston_chandaria_2025_beautiful_loop/paper.md` — Relates to epistemic depth and luminosity

---

## Effective Free Energy

*(Definition TBD)*

---

## Factored State Space

A decomposition of a large joint state into independent pieces called **factors**. Instead of tracking a single belief distribution over every possible combination of states, you maintain separate, smaller distributions — one per factor.

For example, with factors context (3 states), action (4 states), threat (2 states), and schema_mode (2 states), the full joint has 3×4×2×2 = 48 entries. The factored representation has only 3+4+2+2 = 11 entries — each factor gets its own belief vector.

This makes inference tractable but introduces an approximation: you lose the ability to represent correlations between factors (e.g., "context and threat are linked"). See **Mean-Field Approximation** for how this trade-off is formalized.

**See also:**
- `src/active_inference/inference.jl` — multi-factor VMP implementation
- `PLAN_v2.md` (State Inference section) — mathematical specification

---

## Mean-Field Approximation

The assumption that the joint posterior over all hidden states factorizes into independent marginals:

```
q(s) ≈ ∏_f q(s_f)
```

Each factor f gets its own variational update, derived by taking the expected log-joint while holding all other factors fixed:

```
ln q(s_f) ∝ ln D_f(s_f) + ∑_g 𝔼_{q(s₋f)}[ln A_g(o_g | s)]
```

The term 𝔼_{q(s₋f)}[·] is the marginalization step: summing out all factors except f, weighted by their current beliefs. Because each factor's update depends on the others' current beliefs, you iterate (cycle through all factors, recompute, repeat) until beliefs stabilize. This is the **fixed-point iteration** at the heart of variational message passing.

**Trade-off:** Fast and tractable, but cannot represent correlations between factors. If two factors are strongly coupled (e.g., threat level depends heavily on context), the mean-field approximation may underestimate uncertainty.

**See also:**
- `src/active_inference/inference.jl` — `infer_states!()` implements this loop
- `docs/concepts/hierarchical_precision.md` — how precision interacts with this factorization

---

## Variational Bayesian Methods

A family of techniques for approximating intractable integrals in Bayesian inference. Alternative to Markov Chain Monte Carlo (MCMC) methods. Includes variational message passing.

**Key idea:** Instead of sampling (like MCMC), variational methods optimize an approximate distribution to be as close as possible to the true posterior.

---

## Marginal Likelihood (Evidence)

The likelihood function integrated over the parameter space—i.e., the probability of generating the observed sample given the model (but marginalized over all possible parameter values).

Also called "model evidence" in Bayesian model comparison. This is the denominator in Bayes' theorem.

---

## Bayes' Theorem

The fundamental rule for updating beliefs given new evidence:

```
Posterior = (Likelihood × Prior) / Evidence
```

Or in notation: P(θ|D) = P(D|θ) × P(θ) / P(D)

---

## Prior Parameters

Priors are characterized by two parameters:
- **Mean (μ):** The expected value
- **Sigma (σ):** The standard deviation

**Precision** is calculated as: 1/σ² (inverse of variance)

---
