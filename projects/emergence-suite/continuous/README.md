# Continuous depth and global precision-field simulations

## v11 global precision field (2026-07-13)

`src/GlobalPrecisionField.jl` implements epistemic depth in the global sense
of Laukkonen, Friston, and Chandaria (2025). It replaces the causal
scalar-depth interpretation with a hyper-model over the channel-specific field

```text
Phi = (part, context, interoception, relational, policy).
```

Each cycle predicts the field, uses it to weight lower-level errors, receives
error on the precision forecast, updates `q(Phi)`, and broadcasts the revised
field. The scalar `depth_index` is computed afterward from posterior
confidence, calibration, and representational breadth. No effective-precision
equation reads that index.

The probes test whether part dominance and depth dissociate, and whether
identity-root revision requires activation plus an open precision field. Run:

```bash
julia --project=projects/emergence-suite/continuous \
  projects/emergence-suite/continuous/scripts/run_global_phi.jl
```

Outputs are written to `results/global_precision_field/`.

## Hierarchical fidelity tranche

`src/HierarchicalEpistemicDepth.jl` moves the construction closer to Table 1
of Beautiful Loop Theory. It adds three explicit latent levels, infers their
states and layer precisions iteratively, derives second-order precision
evidence from lower-level residuals, and compares a shared global hyper-node
against matched independent local meta-inference loops.

Run:

```bash
julia --project=projects/emergence-suite/continuous \
  projects/emergence-suite/continuous/scripts/run_hierarchical_depth.jl
```

Outputs are written to `results/hierarchical_epistemic_depth/`.

## Historical Sim 6a continuous Stage 3

This standalone Julia project implements ticket T2.4: the continuous three-layer Phi bridge and U2 basin map.

This earlier model is retained as an audit artifact. Its scalar `depth` state
directly tilts bundle and evidence precision, so it instantiates local
parametric depth rather than the stronger global definition of epistemic
depth. Its basin and robustness results remain results about that scalar model.

## Model

The build uses the Appendix A.4 empirical-prior resolution. There is no reflexive observation channel in this variant. The depth layer is a top-down precision message over the balance between:

- a bundle-prior stream, pulling content toward the bundle prediction
- a present-evidence stream, weighting current observations

The capture index is the bundle stream's share of effective precision:

```text
bundle_precision / (bundle_precision + evidence_precision)
```

Volatility bursts enter only as observations of volatility. The depth posterior is updated from the volatility prediction error; no code path assigns a burst schedule value to `h`.

## Precision Convention

This continuous implementation realizes a natural-precision Gaussian update for the depth posterior while the stream balance is emitted as an empirical-prior effective-precision message. Per `derivations/d1-tilt-derivation.md`, this means the discrete build's exact affine expected-log-precision tilt does not carry over exactly when the posterior over depth is broad. The expected deviation is the natural-precision moment correction: arithmetic precision averaging can differ from exponentiated expected log precision during collapse.

## Self-Sustaining Loop

The U2 loop is explicit in the expected dynamics. High depth and low capture reduce endogenous volatility; low volatility keeps depth cheap, so the high-depth state sustains itself. Capture pushes the other way: high capture raises endogenous volatility and shifts effective precision toward the bundle stream, making a competing basin possible.

## Running

```bash
julia --project=projects/emergence-suite/continuous projects/emergence-suite/continuous/scripts/run.jl
```

The default output directory is `projects/emergence-suite/continuous/results/sim6a_continuous_stage3/`.

## Run Contract

The runner emits:

- `summary.json`
- `status.json`
- `metadata.json`
- `criteria-results.json`
- `per_seed_metrics.csv`
- `posterior_traces.csv`
- `basin_endpoints.csv`
- `fixed_points.csv`
- `hysteresis_trace.csv`
- `collapse_recovery.svg`
- `basin_map.svg`
- `hysteresis_basin_hopping.svg`

## RxInfer Notes

The runner includes a small RxInfer convergence probe for a three-layer Gaussian `h -> z -> y` message path and records iterations, free-energy endpoints, divergence count, and any obstruction in `summary.json` and `status.json`. The basin map itself is an expected-dynamics integration of the empirical-prior precision-balance equations, because the U2 deliverable is a phase portrait rather than a full time-series inversion.

## T4.8 Step A robustness pilot (2026-07-10)

`scripts/run_t48.jl` is an isolated 10-seed pilot. It leaves the historical
Stage 3 run unchanged, generates observations from an autonomous reflected
latent-depth process, freezes the agent-side theory response for all null
worlds, and never applies the historical phase-specific recovery assistance.
The preregistered complete signature is Self before the first low-depth
crossing, capture during that excursion, and capture in at least 4/5 states
after the latent process autonomously returns to high depth.

The pilot verdict is falsified/mixed. Decoupled capture is `0/10`, including
at zero observation noise, so the theory mapping does not provide the required
reference transition. Flat, reversed, and non-monotone mappings are also
`0/10`; these clean counts cannot support specificity because the theory
reference is absent. Moreover, their driven basin maps are not clean nulls:
mean post-recovery capture fractions across the 81 initial-state cells are
`0.757` (flat), `0.884` (reversed), and `0.607` (non-monotone), versus `0.514`
for theory. The initial condition, rather than the autonomous latent excursion,
determines which existing basin is occupied.

The autonomous bifurcation result does survive. A single 6-neighbor-connected
bistable component occupies `66/125 = 0.528` of the preregistered beta x gamma
x safety-prior grid and contains the historical hysteresis-reference default
`(1.05, 1.25, 0.60)`. It is a slab across safety masses `0.20–0.60`: each of
those slices has `22/25` bistable beta/gamma cells, excluding the same three
low-slope corner cells. No cell is bistable at safety mass `0.80` or `1.00`.
At the default, the converged basin fractions are `0.963` Self and `0.037`
capture.

The noise criterion is already dead at SD `0.0`; counts over the registered
grid `[0, 0.012, 0.035, 0.07, 0.14, 0.28]` are `[0, 0, 0, 0, 2, 4]/10` and
never reach the `8/10` survival gate. No confirmatory seeds were run and no
post-pilot retuning was performed.

Run with:

```bash
~/.juliaup/bin/julia --project=projects/emergence-suite/continuous \
  projects/emergence-suite/continuous/scripts/run_t48.jl
```

Pilot outputs are under
`results/t48_continuous_robustness_pilot/`, including per-mapping SVG basin
maps, `bifurcation_map.svg`, seed-level null/decoupling metrics, and the noise
sweep.

## Higher-fidelity Beautiful Loop hierarchy

The three-level Gaussian fidelity model has explicit hierarchical states and
observations, layer-specific log precisions controlled by $\Phi$, alternating
inference over $q(x^{(1:3)})$ and a Gaussian variational approximation to $q(\Phi)$,
second-order errors computed from expected lower-level residuals, and local and
joint variational-energy traces. Its independent local-loop ablation has the
same marginal prior variance as the global hyper-model.

The context-switch experiment learns precision forecasts from four training
contexts and evaluates them at an out-of-range fifth context before every local
loop receives new residual evidence.

Run with:

```bash
~/.juliaup/bin/julia --project=projects/emergence-suite/continuous \
  projects/emergence-suite/continuous/scripts/run_beautiful_loop_hierarchy.jl
```

Outputs are under `results/beautiful_loop_hierarchy/`.

## Experiment 30: temporal hyper-model

This model learns a context-conditioned precision forecast online and performs
dynamic model selection between globally coupled and independent local
precision changes. Structure switches are not exposed to the agent; expected
lower-level residuals supply the second-order evidence.

```bash
~/.juliaup/bin/julia --project=projects/emergence-suite/continuous \
  projects/emergence-suite/continuous/scripts/run_temporal_hypermodel.jl
```

Outputs are under `results/temporal_hypermodel/`.

## Experiment 31: Bayesian binding

This exact discrete model lets three channel-level causes compete to support
one global cause. Precision controls sensory evidence and each channel's
participation in the coherence prior. Controls use local majority decisions
and an inverted precision field.

```bash
~/.juliaup/bin/julia --project=projects/emergence-suite/continuous \
  projects/emergence-suite/continuous/scripts/run_bayesian_binding.jl
```

Outputs are under `results/bayesian_binding/`.

## Experiment 32: epistemic agency

This experiment uses expected posterior entropy, sampling cost, and uncertainty
about channel reliability to select evidence. An unannounced reliability switch
tests whether second-order surprise redirects sampling without a scripted
policy change.

```bash
~/.juliaup/bin/julia --project=projects/emergence-suite/continuous \
  projects/emergence-suite/continuous/scripts/run_epistemic_agency.jl
```

Outputs are under `results/epistemic_agency/`.

## Experiment 33: one unified Beautiful Loop agent

This construction places three explicit Gaussian levels, a discrete global
cause, the complete precision field `Phi`, and a posterior over epistemic
policies inside one active-inference loop. State and precision posteriors are
updated alternately under one current-state variational objective; expected
free energy supplies the policy factor. The inferred precision field is learned
without cause or reliability labels, broadcast to every transition, and used
to decide which branch is observed next.

The experiment includes matched independent meta-loops, factorized local cause
posteriors pooled by soft probability or summed log odds, matched-budget random
action, fixed sampling, a held-out context forecast, an unannounced structural
break, and an eight-cell parameter perturbation grid. The corrected fair
controls falsify the original binding advantage while preserving the precision
forecasting and adaptive-action results.

```bash
~/.juliaup/bin/julia --project=projects/emergence-suite/continuous \
  projects/emergence-suite/continuous/scripts/run_unified_beautiful_loop.jl
```

Outputs are under `results/unified_beautiful_loop/`.

## Experiment 34: competitive relational binding

This experiment replaces ordinary evidence pooling with a synergy benchmark.
Three locally uninformative causes jointly encode a binary scene through their
parity relation. The full model represents that relation; the control retains
identical local marginals, hierarchy, precision inference, and evidence but no
joint factor. Five percent relation violations expose the prior's failure mode.

```bash
~/.juliaup/bin/julia --project=projects/emergence-suite/continuous \
  projects/emergence-suite/continuous/scripts/run_competitive_binding.jl
```

Outputs are under `results/competitive_binding/`.

## Experiment 35: learned precision structure

This experiment randomizes the channel-loading vector in every seed and hides
it from all agents. A compact global forecaster learns the loadings from
posterior residual evidence. It is compared with independent local regressions
and an evidence-weighted hierarchical local model that can learn the same
cross-layer tying.

```bash
~/.juliaup/bin/julia --project=projects/emergence-suite/continuous \
  projects/emergence-suite/continuous/scripts/run_learned_precision_structure.jl
```

Outputs are under `results/learned_precision_structure/`.

## Experiment 36: frozen confirmation

Fresh seed blocks confirm relational binding and learned global precision,
then stress their load-bearing assumptions. The binding signature survives all
seven cells. The precision comparison passes nine of eleven predictions but
fails the preregistered magnitude of the global-to-local crossover, so the
overall experiment is recorded as failed.

```bash
~/.juliaup/bin/julia --project=projects/emergence-suite/continuous \
  projects/emergence-suite/continuous/scripts/run_confirmatory_beautiful_loop.jl
```

Outputs are under `results/confirmatory_beautiful_loop/`.

## Experiment 37: identifiable global-to-local precision

This construction adds noisy observations at every hierarchical level, making
link-specific residual statistics identifiable without revealing latent states
or true precision. A nested random-effects hypermodel contains the compact
global model as its high-shrinkage limit and releases local deviations when
layer-specific evidence demands them. The exact-sharing margin failed its
frozen threshold, while the nested model won every seed once deviations were
present. Its shrinkage is interpreted as inferred environmental coupling, not
as epistemic depth; depth belongs to the joint residual-update-and-broadcast
loop that can represent either shared or local structure.

```bash
~/.juliaup/bin/julia --project=projects/emergence-suite/continuous \
  projects/emergence-suite/continuous/scripts/run_identifiable_precision_structure.jl
```

Outputs are under `results/identifiable_precision_structure/`.

## Experiment 38: identifiable globality control

This frozen follow-up adds the control missing from Experiment 37: eighteen
independent local meta-loop coefficients, with no parameter sharing, receive
the same noisy layer observations and posterior residual updates as the compact
and nested global hyper-models. A new seed block tests whether joint inference
earns a forecast advantage in the identifiable exact-sharing regime and whether
the nested global model can release tying under genuine local deviations.

On fresh seeds, exact-sharing RMSE was `0.340` compact-global and `0.359`
nested-global versus `0.637` independent-local, with 20/20 paired wins for both
global models. At deviation scale `2.0`, nested-global RMSE was `1.068`, versus
`1.090` independent and `2.716` compact, while shrinkage fell from `8.32` to
`1.88`. All frozen criteria passed; task accuracy remained effectively tied.

```bash
~/.juliaup/bin/julia --project=projects/emergence-suite/continuous \
  projects/emergence-suite/continuous/scripts/run_identifiable_globality.jl
```

Outputs are under `results/identifiable_globality/`.
