# Research & Technical Specification
## Beautiful Loop Theory simulations in RxInfer

Version: 0.1
Target audience: Codex / implementation engineer
Primary goal: implement three falsifiable simulations of Beautiful Loop Theory (BLT) with RxInfer as the inference backbone.

---

## 1. Scope

This specification is for an **executable formalization** of BLT, not a proof of phenomenal consciousness.
The implementation should test whether a **global recursive precision model** does unique computational work beyond simpler baselines.

A positive result is:
- BLT-style global hyper-models outperform simpler baselines on held-out tasks involving changing reliability, ambiguity, and higher-order precision control.
- The model exhibits **non-encoded emergent properties** under held-out probe conditions.

A negative result is equally publishable:
- If BLT collapses to ordinary local reliability estimation or generic hierarchical smoothing once formalized, that is a substantive result.
- If its proposed state taxonomy (e.g. MPE-like vs dream-like vs noetic/confident-wrong) does not emerge as separable computational regimes, that is also a substantive result.

---

## 2. Short outline of the executable formalization

### 2.1 Abstract BLT formalization

Let:
- `o_t` be observations
- `x_t^(1:L)` be first-order hidden states across layers
- `phi_t` be the global hyper-state controlling precision / reliability expectations
- `pi_t` be optional policies or actions

Use the following abstract factorization:

```math
p(o_{1:T}, x_{1:T}^{1:L}, \phi_{1:T}, \pi_{1:T})
= p(x_1, \phi_1)
  \prod_{t=1}^T
    p(o_t \mid x_t^{(1)}, \phi_t)
    \prod_{\ell=1}^{L-1} p(x_t^{(\ell)} \mid x_t^{(\ell+1)}, \phi_t)
    p(x_t^{(L)} \mid x_{t-1}^{(L)}, \pi_{t-1}, \phi_t)
    p(\phi_t \mid \phi_{t-1}, \epsilon_{t-1}, c_t)
```

where:
- `phi_t` predicts precision structure, not content labels.
- `epsilon_{t-1}` is a summary of recent prediction-error statistics or residual structure.
- `c_t` is optional context.

Operationally, BLT contributes one architectural commitment:

> A **global** latent variable predicts and reweights reliability / precision across the hierarchy, and this global variable is itself inferred from the resulting precision-weighted errors.

### 2.2 Operationalization used in this project

Implement two concrete forms:

#### BLT-Discrete
Used in Simulation 1 and Simulation 2.

- Hidden state is represented by a joint categorical variable.
- The joint variable contains world/scene state plus a hyper-state.
- Multiple modalities or branches receive conditionally independent observations given the joint latent state.
- Precision control is expressed as context-dependent emission matrices.

#### BLT-HGF
Used in Simulation 3.

- Continuous hierarchical Gaussian filter style model.
- Top level `h_t` predicts lower-level log-precision state `z_t`.
- Lower-level content state `x_t` evolves under variance controlled by `z_t`.
- Observations `y_t` are generated from `x_t`.

### 2.3 Derived observables (not encoded in the model)

These quantities are analysis outputs only. They must **not** be supervised or rewarded.

- **Depth score**
  - discrete models: confidence in `phi_t`
  - continuous models: inverse posterior variance of `h_t`
- **Binding index**
  - evidence gap between best and second-best global interpretation
- **Coherence score**
  - compatibility between local branch posteriors and the inferred global hypothesis
- **Confidence-accuracy gap**
  - overconfidence or calibration error

### 2.4 What counts as non-encoded emergence

A property counts as emergent only if all of the following are true:

1. It is not directly supervised.
2. It is not directly optimized or rewarded.
3. It is measured on held-out probes or held-out parameter regimes.
4. It is robust across seeds.
5. It disappears, weakens, or qualitatively changes under relevant ablation.

Target emergent properties:
- Simulation 1: predictive calibration of **future** reliability.
- Simulation 2: coherent global binding and rivalry-like dwell structure without hard-coded winner-take-all logic.
- Simulation 3: separable MPE-like and noetic/confident-wrong regions in phase space.

---

## 3. Common implementation rules

### 3.1 Language and package assumptions

- Julia
- RxInfer.jl as the primary inference engine
- GraphPPL.jl syntax via `@model`
- `infer`, `@constraints`, `@autoupdates`, `@initialization`
- `GCV` node for Simulation 3

Recommended additional packages:
- `Distributions`
- `LinearAlgebra`
- `StatsBase`
- `StableRNGs`
- `Random`
- `DataFrames`
- `CSV`
- `JSON3`
- `ArgParse`
- `Plots` or `Makie` for figures
- `YAML` optionally for configs

### 3.2 Repo layout

```text
blt-rxinfer/
  Project.toml
  README.md
  configs/
    sim1_default.yaml
    sim2_default.yaml
    sim3_default.yaml
  src/
    BLTCore.jl
    utils/
      indexing.jl
      metrics.jl
      io.jl
      plotting.jl
      reproducibility.jl
    envs/
      sensor_fusion.jl
      ambiguous_binding.jl
      phase_diagram.jl
    models/
      sim1_blt_global.jl
      sim1_flat_fixed.jl
      sim1_local_precision.jl
      sim2_blt_global.jl
      sim2_hier_fixed.jl
      sim2_local_branch.jl
      sim3_blt_hgf.jl
      sim3_hgf2.jl
      sim3_kalman_fixed.jl
    runners/
      run_sim1.jl
      run_sim2.jl
      run_sim3.jl
  scripts/
    reproduce_all.jl
    summarize_results.jl
  test/
    runtests.jl
    test_indexing.jl
    test_envs.jl
    test_sim1_correctness.jl
    test_sim2_correctness.jl
    test_sim3_correctness.jl
    test_hypotheses.jl
  results/
    .gitkeep
```

### 3.3 Execution model

The codebase must distinguish between:

1. **Implementation correctness checks**
   - these determine whether the code is working correctly.
2. **Theory evaluation checks**
   - these determine whether BLT is supported, unsupported, or neutral.
   - these must never be treated as software failures.

### 3.4 Reproducibility

Use fixed seeds by default:

```text
[11, 23, 37, 53, 71, 97, 131, 173, 211, 251]
```

Every script must save:
- config snapshot
- git commit hash if available
- Julia version
- RxInfer version
- seed
- runtime
- metrics JSON or CSV

### 3.5 Output contract for every simulation

Each run must produce:
- `summary.json`
- `per_seed_metrics.csv`
- `posterior_traces.csv` or compact binary equivalent
- plots as PNG or PDF
- a machine-readable `status.json` with:
  - `implementation_passed: true/false`
  - `theory_result: support | weak_support | null | falsified | inconclusive`

### 3.6 Do not bake in the answer

Forbidden shortcuts:
- no latent variable named `consciousness`
- no explicit reward for coherence, binding, MPE, or noeticism
- no hard-coded winner-take-all arbitration module for ambiguity probes
- no supervised labels for state taxonomy

Allowed:
- global hyper-state that predicts precision or reliability
- derived analysis metrics computed after inference
- held-out probe tasks

---

## 4. Shared metrics

These metrics should live in `src/utils/metrics.jl` and be reused.

### 4.1 Predictive metrics

- state accuracy
- negative log likelihood (held-out predictive NLL)
- Brier score
- expected calibration error (ECE)
- posterior interval coverage (for continuous models)
- RMSE (continuous latent recovery)

### 4.2 Hyper-model metrics

- hyper-state accuracy if ground truth exists
- future reliability prediction Brier score
- depth score
- confidence-accuracy gap

### 4.3 Binding metrics

- binding index:
  - `top posterior probability - second posterior probability`
- coherence score:
  - probability mass on globally compatible local configurations
- micro-switch rate
- mean dwell time

### 4.4 Regime metrics for Simulation 3

- first-order precision score
- hyper-certainty score
- content complexity
- overconfidence score

Implement these exactly as:

```text
first_order_precision = mean_t(1 / var_q_x_t)
hyper_certainty       = mean_t(1 / var_q_h_t)
content_complexity    = var_t(mean_q_x_t)
overconfidence_90     = max(0, 0.90 - empirical_90pct_interval_coverage)
```

where:
- `var_q_x_t` is posterior variance of `x_t`
- `var_q_h_t` is posterior variance of `h_t`
- `mean_q_x_t` is posterior mean of `x_t`

---

## 5. Simulation 1 — Reliability-switching sensor fusion

## 5.1 Research question

Does a **global** hyper-state that predicts reliability shifts across modalities improve:
- hidden-state inference,
- calibration,
- and future reliability prediction,

relative to fixed-precision or local-only precision models?

## 5.2 Hypothesis

If BLT adds unique value, then a shared hyper-state should outperform simpler baselines when reliability changes are **contextual and globally structured**.

The strongest BLT-specific signature here is not just state accuracy.
It is the ability to infer and predict **future reliability structure**.

## 5.3 Environment

### Hidden variables

- world state `s_t ∈ {1,2,3,4}`
- global reliability context `phi_t ∈ {BG, VG, AG, BP}` where:
  - `BG` = both good
  - `VG` = vision good, audio poor
  - `AG` = audio good, vision poor
  - `BP` = both poor

### State transition matrix

Use a sticky world-state transition matrix:

```text
A_s = 4x4
diag = 0.85
offdiag = 0.05
```

### Hyper-state transition matrix

Use a sticky context matrix:

```text
A_phi = 4x4
diag = 0.94
offdiag = 0.02
```

### Observation spaces

- vision observation `o^v_t ∈ {1,2,3,4}`
- audio observation `o^a_t ∈ {1,2,3,4}`

### Emission matrices

For each modality, define a helper:

```text
make_emission(r): 4x4 matrix
P(obs = true_state) = r
P(obs != true_state) = (1-r)/3
```

Use the following reliability table:

```text
context   r_vision   r_audio
BG        0.90       0.90
VG        0.90       0.40
AG        0.40       0.90
BP        0.40       0.40
```

Thus the environment stores:
- `Bv[phi] = make_emission(r_vision(phi))`
- `Ba[phi] = make_emission(r_audio(phi))`

### Default data generation protocol

Per seed:
- generate 20 episodes
- episode length `T = 240`
- use stochastic transitions from `A_s` and `A_phi`

Also generate a **switch probe** set with deterministic context schedule:
- steps 1–60: `BG`
- steps 61–120: `VG`
- steps 121–180: `AG`
- steps 181–240: `BP`

Use the same world-state dynamics in all probe episodes.

## 5.4 Models

### Model A — FlatFixed baseline

Latent state:
- `s_t` only

Assumptions:
- ignores context entirely
- uses averaged emission matrices:

```text
Bv_bar = mean_phi Bv[phi]
Ba_bar = mean_phi Ba[phi]
```

Use online filtering.

### Model B — LocalPrecision baseline

Latent state:
- `(s_t, phi^v_t, phi^a_t)` where `phi^v_t` and `phi^a_t` are independent modality-specific reliability contexts.

Assumptions:
- no shared global cause of reliability
- each modality explains its own reliability independently

Practical compile-down:
- joint categorical latent with size `4 * 4 * 4 = 64`
- transition factorization:

```text
P(s', phi_v', phi_a' | s, phi_v, phi_a)
= A_s[s', s] * A_phi[phi_v', phi_v] * A_phi[phi_a', phi_a]
```

### Model C — BLTGlobal

Latent state:
- `(s_t, phi_t)`

Assumptions:
- one shared hyper-state controls both modalities

Practical compile-down:
- joint categorical latent with size `4 * 4 = 16`
- transition factorization:

```text
P(s', phi' | s, phi) = A_s[s', s] * A_phi[phi', phi]
```

Emission matrices on joint state:

```text
Bv_joint[obs, (s,phi)] = Bv[phi][obs, s]
Ba_joint[obs, (s,phi)] = Ba[phi][obs, s]
```

### Optional reference model — OracleContext

Not used for hypothesis testing.
Only for an upper bound.

- infer `s_t` with the true `phi_t` clamped

## 5.5 RxInfer implementation details

### Representation

Use one-hot categorical state vectors.

### Online filtering model form

Pseudo-structure:

```julia
@model function sim1_blt(yv, ya, A_joint, Bv_joint, Ba_joint, j_prev_prior)
    j_prev ~ Categorical(j_prev_prior)
    for t in eachindex(yv)
        j[t] ~ Categorical(A_joint * j_prev)
        yv[t] ~ Categorical(Bv_joint * j[t])
        ya[t] ~ Categorical(Ba_joint * j[t])
        j_prev = j[t]
    end
end
```

Notes:
- If RxInfer prefers static batch inference for this discrete model, that is acceptable.
- If online filtering is used, use `@autoupdates` to roll posterior at `j[t]` into the prior for the next step.

### Joint-state utilities

Implement helper functions:
- `joint_index_s_phi(s, phi)`
- `inverse_joint_index_s_phi(idx)`
- analogous helpers for `(s, phi_v, phi_a)`

These must be unit-tested.

## 5.6 Metrics

Primary:
- hidden world-state accuracy
- held-out predictive NLL
- ECE on world-state posterior
- future reliability prediction Brier score

Define future reliability prediction as:

```text
p_hat_v_correct(t+1) = sum_phi q(phi_t)[phi] * r_vision(phi)
p_hat_a_correct(t+1) = sum_phi q(phi_t)[phi] * r_audio(phi)
```

Compare these against actual correctness indicators:

```text
1[o^v_{t+1} == s_{t+1}]
1[o^a_{t+1} == s_{t+1}]
```

Secondary:
- context recovery accuracy
- switch-recovery accuracy in windows after scheduled switches

## 5.7 Implementation correctness checks

These are hard pass/fail software checks.

1. **Emission matrices are valid**
   - all entries nonnegative
   - each column sums to 1 within tolerance `1e-8`

2. **Joint indexing is bijective**
   - for all valid tuples, `inverse(joint_index(...)) == original`

3. **Posterior normalization**
   - every posterior over latent categorical state sums to 1 within tolerance `1e-6`

4. **Degenerate equivalence**
   - if all contexts are forced to `BG`, BLTGlobal must match FlatFixed configured with `BG` emissions within small tolerance on NLL and accuracy

5. **Deterministic reproducibility**
   - same seed and config produce identical summary metrics within tolerance `1e-10` if RNG and inference path are deterministic

## 5.8 Theory evaluation criteria

These do **not** determine software correctness.

### Minimum support target

Across the default seed set:

- BLTGlobal average held-out NLL is at least **5% lower** than FlatFixed
- BLTGlobal future-reliability Brier score is at least **10% lower** than FlatFixed
- BLTGlobal context recovery accuracy is above **0.65** after burn-in

### Stronger support target

- BLTGlobal outperforms LocalPrecision on future-reliability prediction by **at least 3%**
- BLTGlobal switch recovery window accuracy exceeds FlatFixed by **at least 0.05** averaged over probe switches

### Falsification logic

- If BLTGlobal does not beat FlatFixed, then the hyper-model may be unnecessary.
- If BLTGlobal does not beat LocalPrecision, then the global shared hyper-state may add little beyond local reliability trackers.
- If BLTGlobal improves current-state inference but not future reliability prediction, the BLT claim is weakened to ordinary adaptive confidence estimation.

## 5.9 Figures to generate

1. switch-probe accuracy over time with context change markers
2. calibration curves for state confidence
3. future reliability prediction calibration curves
4. posterior heatmap over `phi_t`
5. boxplots of NLL / Brier / ECE across seeds

---

## 6. Simulation 2 — Hierarchical ambiguous perception and Bayesian binding

## 6.1 Research question

Can a global precision hyper-state stabilize coherent global interpretations under ambiguity, yielding binding and rivalry-like dwell structure without a hand-coded arbitration rule?

## 6.2 Hypothesis

If BLT is doing something beyond ordinary hierarchical perception, then a shared hyper-state should:
- increase global coherence,
- reduce micro-jitter under ambiguity,
- and optionally produce coherent-but-wrong interpretations under biased priors and high hyper-certainty.

## 6.3 Environment

### Hidden variables

- global interpretation `g_t ∈ {A, B}`
- global hyper-state `phi_t ∈ {BIND, FRAG}`
- branch latent states:
  - `z1_t ∈ {A, B}`
  - `z2_t ∈ {A, B}`

Interpretation:
- `g_t` is the global scene or percept.
- `z1_t`, `z2_t` are local branch hypotheses.
- `phi_t` determines whether the system expects a coherent single global interpretation or more fragmented local evidence.

### Global-state transition

Use sticky global dynamics:

```text
A_g = 2x2
diag = 0.97
offdiag = 0.03
```

### Hyper-state transition

Use sticky context dynamics:

```text
A_phi = 2x2
diag = 0.95
offdiag = 0.05
```

### Conditional local-state generation

Define branch compatibility with the global scene:

```text
rho_BIND = 0.92
rho_FRAG = 0.65
```

For each branch `b ∈ {1,2}`:

```text
P(zb_t = g_t | phi_t = BIND) = rho_BIND
P(zb_t != g_t | phi_t = BIND) = 1 - rho_BIND

P(zb_t = g_t | phi_t = FRAG) = rho_FRAG
P(zb_t != g_t | phi_t = FRAG) = 1 - rho_FRAG
```

Branches are conditionally independent given `(g_t, phi_t)`.

### Observation model

Each branch emits a categorical observation `ob_t ∈ {A, B}`.

Observation reliability by hyper-state:

```text
r_obs_BIND = 0.75
r_obs_FRAG = 0.90
```

Thus when `FRAG`, local evidence is cleaner but cross-branch coherence is weaker.
This is the condition under which local evidence can remain in conflict.

## 6.4 Data generation protocols

### Natural episodes

Per seed:
- 20 episodes
- `T = 200`
- sample `g_t`, `phi_t`, `z1_t`, `z2_t`, `o1_t`, `o2_t`

### Probe 1 — Unambiguous control

- repeated observations consistent with one global interpretation
- e.g. `o1=A`, `o2=A` with occasional 5% noise flips

### Probe 2 — Balanced ambiguity

- repeated branch conflict
- e.g. `o1=A`, `o2=B` with occasional flips
- length `T = 200`

### Probe 3 — Bias / noetic probe

Same as balanced ambiguity, but set priors:
- `P(g_1 = A) = 0.80`
- strong prior mass on `phi = BIND`

This probe is exploratory and tests whether the model can become coherent-but-wrong.

## 6.5 Models

### Model A — HierFixed baseline

Latent state:
- `(g_t, z1_t, z2_t)`
- no hyper-state

Assumptions:
- fixed branch-global coherence level, e.g. `rho_fixed = 0.78`
- no dynamic precision control

Practical joint-state size:
- `2 * 2 * 2 = 8`

### Model B — LocalBranch baseline

Latent state:
- `(g_t, phi1_t, phi2_t, z1_t, z2_t)`

Assumptions:
- branch-specific reliability states
- no shared global hyper-state controlling both branches

Practical joint-state size:
- `2 * 2 * 2 * 2 * 2 = 32`

### Model C — BLTGlobal

Latent state:
- `(g_t, phi_t, z1_t, z2_t)`

Assumptions:
- one shared hyper-state controls both branch coherence and observation precision

Practical joint-state size:
- `2 * 2 * 2 * 2 = 16`

## 6.6 Practical compile-down

Even though the conceptual model is hierarchical, the initial implementation should compile it into a joint categorical latent HMM for reliability and simplicity.

That is:
- use a single categorical latent variable per time step
- build transition and emission tensors from the factorized generative process
- decode posteriors back into marginals over `g`, `phi`, `z1`, `z2`

This is preferred for the first implementation because it avoids custom nodes.

## 6.7 Metrics

Primary:
- scene accuracy on natural episodes
- coherence score
- binding index
- micro-switch rate on ambiguity probe
- mean dwell time on ambiguity probe

Define coherence score exactly as:

```text
coherence_t = P_q(z1_t = g_t and z2_t = g_t)
coherence = mean_t(coherence_t)
```

Define binding index exactly as:

```text
binding_index_t = p_top_scene_t - p_second_scene_t
binding_index = mean_t(binding_index_t)
```

Since there are only two scenes:

```text
binding_index_t = abs(P_q(g_t = A) - P_q(g_t = B))
```

Define micro-switch rate and dwell:

```text
micro_switch_rate = (# of changes in MAP(g_t)) / (T - 1)
mean_dwell = average run length of consecutive identical MAP(g_t)
```

Secondary:
- confident-wrong rate on bias probe

```text
confident_wrong_t = 1[MAP(g_t) != truth_g_t and max_q_g_t > 0.80]
confident_wrong = mean_t(confident_wrong_t)
```

For the balanced ambiguity probe, where there is no single correct global scene, define truth only if you explicitly construct a hidden `g_t`; otherwise report this metric only for generated natural episodes or bias episodes with known `g_t`.

## 6.8 Implementation correctness checks

1. **Joint tensor validity**
   - transition columns sum to 1
   - emission columns sum to 1

2. **Posterior normalization**
   - categorical posteriors sum to 1 within tolerance

3. **Unambiguous control sanity**
   - all models should achieve scene accuracy > 0.90 on unambiguous control

4. **Hierarchy decoding consistency**
   - marginals recovered from the joint posterior must sum correctly and be consistent across decoding functions

5. **Degenerate equivalence**
   - if `rho_BIND = rho_FRAG` and `r_obs_BIND = r_obs_FRAG`, then BLTGlobal should reduce to a model equivalent to HierFixed within tolerance

## 6.9 Theory evaluation criteria

### Minimum support target

Across seeds:
- BLTGlobal coherence exceeds HierFixed by at least **0.10** on natural stable episodes
- BLTGlobal micro-switch rate is at least **25% lower** than HierFixed on balanced ambiguity probe
- BLTGlobal mean dwell is at least **25% higher** than HierFixed on balanced ambiguity probe

### Stronger support target

- BLTGlobal also exceeds LocalBranch on coherence or dwell metrics
- BLTGlobal shows a non-trivial confident-wrong regime under bias probe while remaining globally coherent

### Falsification logic

- If BLTGlobal fails to improve coherence or dwell relative to HierFixed, Bayesian binding may reduce to ordinary hierarchical smoothing.
- If BLTGlobal fails to outperform LocalBranch, the importance of a shared global hyper-state is weakened.
- If the confident-wrong regime never appears under strong biased priors and high hyper-certainty, the noetic extension is weakened.

## 6.10 Figures to generate

1. posterior trajectories over `P(g_t=A)` under ambiguity
2. coherence and binding index over time
3. dwell-time histograms across models
4. micro-switch rate bar plots
5. bias probe examples showing coherent-but-wrong trajectories if present

---

## 7. Simulation 3 — Phase diagram of precision regimes with BLT-HGF

## 7.1 Research question

Does a continuous BLT-style hyper-model produce separable computational regimes corresponding to:
- ordinary wake-like inference,
- dream-like internally rich but weakly controlled inference,
- MPE-like low-content high-hyper-certainty inference,
- and noetic/confident-wrong inference?

## 7.2 Hypothesis

If BLT has real computational content beyond standard HGF, then a distinct region should emerge where:
- first-order precision is low,
- content complexity is low,
- hyper-certainty is high,

which is the closest computational analogue of the paper's MPE claim.

A second predicted region is:
- hyper-certainty high,
- overconfidence high,

which corresponds to confident-but-wrong or noetic states.

## 7.3 Model family

### Ground-truth generator

Use a 3-level continuous process:

```math
h_t \sim N(h_{t-1}, v_h)
z_t \sim N(h_t, v_z)
x_t \sim N(\rho x_{t-1} + u_t, \exp(\kappa z_t + \omega))
y_t \sim N(x_t, v_y)
```

Where:
- `h_t` is the hyper-state predicting local log-precision
- `z_t` is the local precision state
- `x_t` is the first-order content state
- `u_t` is externally specified endogenous drive

Use `kappa = -1.0` so larger `z_t` implies **smaller** variance and therefore higher first-order precision.

### Default fixed constants

```text
rho      = 0.95
v_z      = 0.20
omega    = 0.00
base_v_h = 0.10
base_v_y = 0.10
T        = 300
```

### Sweep controls

#### Local precision scale

`alpha_local ∈ {0.25, 0.5, 1.0, 2.0, 4.0}`

Implement by setting:
- `mean(h_t)` around `log(alpha_local)` in the generator
- optionally `v_y = base_v_y / alpha_local`

#### Hyper-certainty scale

`alpha_hyper ∈ {0.25, 0.5, 1.0, 2.0, 4.0}`

Implement by setting:
- `v_h = base_v_h / alpha_hyper`

#### Endogenous-drive scale

`input_scale ∈ {0.1, 1.0, 2.0}`

Use:

```text
u_t = input_scale * sin(2π t / 30) + 0.25 * input_scale * ξ_t
ξ_t ~ N(0,1)
```

This drive is only in the generator, not directly in the inference model.

#### Prior-bias condition

For noetic/confident-wrong probes, initialize the inference model with biased priors on `h_0` and/or `x_0`.

Recommended default bias:
- prior mean shifted by `+2` standard deviations from truth
- hyper prior variance divided by `4`

## 7.4 Models

### Model A — KalmanFixed baseline

- constant process variance
- no precision dynamics

### Model B — HGF2 baseline

- two-layer HGF:

```math
z_t \sim N(z_{t-1}, v_z)
x_t \sim N(\rho x_{t-1}, \exp(\kappa z_t + \omega))
y_t \sim N(x_t, v_y)
```

- no extra hyper-state above `z_t`

### Model C — BLT-HGF

- three-layer model with `h_t -> z_t -> x_t -> y_t`

## 7.5 RxInfer implementation details

### Preferred initial model form

Use a single-step streaming model with `@autoupdates`.

Pseudo-structure:

```julia
@model function sim3_blt_hgf(
    y,
    rho,
    kappa,
    omega,
    v_h,
    v_z,
    v_y,
    h_prev_mean,
    h_prev_var,
    z_prev_mean,
    z_prev_var,
    x_prev_mean,
    x_prev_var
)
    h_prev ~ Normal(mean = h_prev_mean, variance = h_prev_var)
    z_prev ~ Normal(mean = z_prev_mean, variance = z_prev_var)
    x_prev ~ Normal(mean = x_prev_mean, variance = x_prev_var)

    h_t ~ Normal(mean = h_prev, variance = v_h)
    z_t ~ Normal(mean = h_t, variance = v_z)
    x_t ~ GCV(rho * x_prev, z_t, kappa, omega)
    y   ~ Normal(mean = x_t, variance = v_y)
end
```

Use `GCVMetadata(GaussHermiteCubature(31))` initially.

Use `@autoupdates`:

```julia
h_prev_mean, h_prev_var = mean_var(q(h_t))
z_prev_mean, z_prev_var = mean_var(q(z_t))
x_prev_mean, x_prev_var = mean_var(q(x_t))
```

### Constraints

Start with mean-field constraints:

```text
q(x_t, x_prev, z_t, h_t) = q(x_t) q(x_prev) q(z_t) q(h_t)
```

If recovery is poor, try structured coupling of `x_prev` and `x_t` only.

## 7.6 Experimental design

### Phase diagram sweep

For each pair `(alpha_local, alpha_hyper)`:
- generate 10 seeds
- `input_scale = 1.0`
- no prior bias
- fit KalmanFixed, HGF2, BLT-HGF
- store summary metrics

### Scenario probes

#### MPE-like candidate

```text
alpha_local = 0.5
alpha_hyper = 4.0
input_scale = 0.1
```

#### Dream-like candidate

```text
alpha_local = 0.5
alpha_hyper = 0.5
input_scale = 2.0
```

#### Wake-like candidate

```text
alpha_local = 2.0
alpha_hyper = 2.0
input_scale = 1.0
```

#### Noetic/confident-wrong candidate

```text
alpha_local = 0.75
alpha_hyper = 4.0
input_scale = 1.0
biased priors enabled
```

## 7.7 Metrics

Primary:
- held-out predictive NLL
- RMSE of `x_t`
- posterior interval coverage of `x_t`
- first-order precision score
- hyper-certainty score
- content complexity
- overconfidence score

Use exact formulas:

```text
first_order_precision = mean_t(1 / var_q_x_t)
hyper_certainty       = mean_t(1 / var_q_h_t)
content_complexity    = var_t(mean_q_x_t)
coverage_90           = mean_t(1[x_true_t in 90pct_CI_q_x_t])
overconfidence_90     = max(0, 0.90 - coverage_90)
```

Secondary:
- posterior mean trajectories for `x_t`, `z_t`, `h_t`
- final Bethe free energy as convergence diagnostic only

## 7.8 Implementation correctness checks

1. **No NaNs / Infs**
   - in means, variances, free energy history

2. **Variance positivity**
   - all inferred variances positive

3. **Generator recovery sanity**
   - on easy setting `alpha_local=4.0`, `alpha_hyper=4.0`, BLT-HGF RMSE on `x_t` must be below a conservative threshold, e.g. `0.35`

4. **Reduction sanity**
   - when `v_h` is extremely small and `h_0` fixed, BLT-HGF should approximate HGF2 with a nearly constant `z_t`

5. **Free-energy sanity**
   - on a small benchmark run, final free energy should be lower than initial free energy for each model

## 7.9 Theory evaluation criteria

### Minimum support target

Across the phase sweep:
- BLT-HGF beats KalmanFixed and HGF2 on held-out NLL for generator settings with nontrivial hyper-dynamics
- a candidate MPE region exists:
  - first-order precision in bottom quartile
  - content complexity in bottom quartile
  - hyper-certainty in top quartile

### Stronger support target

- a candidate dream region also exists and differs from MPE by:
  - lower hyper-certainty
  - higher content complexity
- a noetic/confident-wrong region exists under biased priors with:
  - hyper-certainty in top quartile
  - overconfidence_90 > 0.05

### Falsification logic

- If BLT-HGF does not outperform HGF2 on data generated with hyper-dynamics, the extra hyper-layer may be unnecessary.
- If the MPE-like candidate region does not separate from general collapse or numerical failure, the MPE computational story is weakened.
- If dream-like and MPE-like probes differ only on one generic uncertainty axis, the proposed state taxonomy is weakened.
- If no overconfidence regime appears under biased priors and high hyper-certainty, the noetic extension is weakened.

## 7.10 Figures to generate

1. heatmap of first-order precision over `(alpha_local, alpha_hyper)`
2. heatmap of hyper-certainty over `(alpha_local, alpha_hyper)`
3. heatmap of content complexity over `(alpha_local, alpha_hyper)`
4. heatmap of overconfidence over `(alpha_local, alpha_hyper)`
5. scenario trajectories for wake-like, dream-like, MPE-like, noetic-like probes
6. quadrant or scatter plot of `hyper_certainty` vs `first_order_precision` with labels by scenario

---

## 8. Cross-simulation ablation logic

For publication, the strongest comparison set is:

- **NoHyper** / fixed precision
- **LocalHyper** / local-only precision tracking
- **BLTGlobal** / shared global hyper-state

Interpretation:
- `NoHyper -> LocalHyper` tests whether dynamic reliability matters at all.
- `LocalHyper -> BLTGlobal` tests whether a shared global hyper-state adds something beyond local reliability tracking.

Optional additional ablation:
- **GlobalObserver**
  - infer a global hyper-state, but do not allow it to modulate lower-level inference.
  - this isolates whether the descending precision broadcast matters.

If implemented, this is a very strong test.

---

## 9. Software test plan

## 9.1 Required distinction

`test/` must separate:
- correctness tests
- hypothesis tests

Suggested files:

```text
test_indexing.jl
test_envs.jl
test_sim1_correctness.jl
test_sim2_correctness.jl
test_sim3_correctness.jl
test_hypotheses.jl
```

## 9.2 Correctness tests

### Generic

- stochastic matrices valid
- decoding helpers valid
- posterior normalization
- no NaNs / Infs
- reproducibility under fixed seeds

### Simulation-specific

#### Sim1
- degenerate equivalence under single context
- switch probe generation exactness

#### Sim2
- ambiguity probes generated exactly as specified
- unambiguous control solved by all models

#### Sim3
- generator produces finite trajectories
- easy recovery setting passes RMSE threshold
- free-energy decreases on benchmark case

## 9.3 Hypothesis tests

These should output support labels, not raise hard failures.

Recommended structure:

```julia
struct TheoryResult
    label::Symbol   # :support, :weak_support, :null, :falsified, :inconclusive
    metrics::Dict
    notes::Vector{String}
end
```

---

## 10. Publication framing

## 10.1 Strong positive paper

Title pattern:

> An executable formalization of Beautiful Loop Theory: testing global recursive precision control in active inference

Core claims:
- BLTGlobal predicts future reliability better than baselines
- BLTGlobal binds globally coherent interpretations under ambiguity without a hard-coded WTA module
- BLT-HGF exhibits a distinct low-content / high-hyper-certainty regime and a separate confident-wrong regime

## 10.2 Strong negative paper

Title pattern:

> Beautiful Loop Theory as executable active inference: where the theory adds predictive value and where it collapses to standard reliability estimation

Core claims:
- global hyper-model adds little beyond local reliability tracking
- MPE/noetic regimes do not separate computationally once formalized
- binding effects are explained by generic temporal smoothing rather than recursive global precision control

Both outcomes are acceptable.

---

## 11. Suggested implementation order

### Phase 1
- build common utilities
- implement Simulation 1 with fixed known matrices
- pass all correctness tests

### Phase 2
- implement Simulation 2 using joint-state compile-down
- verify coherence and dwell metrics

### Phase 3
- implement Simulation 3 with BLT-HGF and HGF2 baseline
- verify phase sweep and scenario probes

### Phase 4
- add optional learned-parameter variants
- add GlobalObserver ablation if time permits
- produce publication-ready figures

---

## 12. Minimal commands Codex should support

```bash
julia --project=. scripts/run_sim1.jl --config configs/sim1_default.yaml --output results/sim1
julia --project=. scripts/run_sim2.jl --config configs/sim2_default.yaml --output results/sim2
julia --project=. scripts/run_sim3.jl --config configs/sim3_default.yaml --output results/sim3
julia --project=. scripts/reproduce_all.jl --output results/full
julia --project=. test/runtests.jl
```

Each run script should print a compact summary table and write `status.json`.

---

## 13. Deliverables checklist

- [ ] repo scaffold exists
- [ ] configs exist for all three simulations
- [ ] correctness tests pass
- [ ] per-seed results saved
- [ ] summary report saved
- [ ] plots generated
- [ ] final `status.json` labels hypothesis outcome per simulation
- [ ] README explains how to reproduce

---

## 14. Final instruction to implementation agent

Optimize for:
1. falsifiability,
2. simple first-pass models that can actually run,
3. clean ablations,
4. machine-verifiable outputs.

Avoid sophistication that obscures the core comparison.
The first implementation should prefer **joint-state categorical compile-down** and the existing **RxInfer HGF / GCV** pattern over custom nodes.
Only add custom RxInfer nodes if a later iteration shows that the simpler factorization cannot express the required structure cleanly.
