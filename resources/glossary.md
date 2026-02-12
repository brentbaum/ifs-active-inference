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

## Active Inference Matrices

The standard notation for discrete active inference models uses lettered matrices to represent different components of the generative model:

| Matrix | Name | What it represents | IFS interpretation |
|--------|------|-------------------|-------------------|
| **A** | Likelihood | P(o \| s) — "Given hidden state *s*, what observations *o* do I expect?" | How a part shapes *perception* — "if dogs are dangerous, I expect to see threat cues." Modular parts have A matrices that don't condition on context. |
| **B** | Transition dynamics | P(s' \| s, u) — "Given state *s* and action *u*, what state comes next?" | The "stickiness" of parts — once a part is active, how likely it stays active. Also captures how actions change internal states. |
| **C** | Preference prior | P(o) preferred — "What observations do I want?" | Pragmatic priors — "I want to not be near dogs." Exiles often have extreme C priors (avoid pain). Valence = prediction error relative to C. |
| **D** | Initial state prior | P(s₀) — "What state am I likely in at the start?" | Baseline activation of parts before any evidence. Trauma can shift D toward hypervigilant states. |
| **E** | Policy prior (habits) | P(π) — "Which policies do I tend to select?" | Manager/firefighter distinction — habitual action tendencies. Managers have high E on avoidance policies; firefighters on escape policies. |

**Additional notation:**

| Symbol | Meaning |
|--------|---------|
| o | Observations (what the agent perceives) |
| s | Hidden states (what the agent infers about the world) |
| u | Actions/controls |
| π | Policy (sequence of actions) |
| F | Variational free energy (to be minimized — roughly: surprise + complexity) |
| G | Expected free energy (to be minimized — drives policy selection) |
| γ | Precision on policies (confidence in action selection) |

**Key relationships:**
- Parts affect **A** (perception) by biasing what observations are expected given states
- Parts affect **B** (stickiness) by influencing state transition probabilities
- Parts affect **C** (preferences) by holding strong outcome preferences
- Parts affect **E** (habits) by biasing policy selection
- Blending = one part's matrices dominating inference
- Unblending = restoring balanced contribution from multiple subgraphs

**See also:**
- `ifs-active-inference-outline-v1.md` Section 2 — Parts in Active Inference Terms
- `paper_reproduction/chamberlin_2022/model_design.md` — Implementation of matrices

---
