# T0.1 framework decision memo

Date: 2026-07-09

## Decision

Use a Julia port of the v10 discrete active-inference core as the substrate for Sims 1-4. Keep the `beautiful-simulation`/RxInfer run-contract and metadata conventions, and write adapters at the suite boundary rather than forcing Sim 1-4 structure learning into RxInfer factor graphs.

Runner-up: discrete-in-RxInfer. Disqualifier: Sim 1/4 need latent-cause growth as a first-class mid-run operation, while the existing RxInfer usage and current RxInfer model API are fixed-graph/fixed-shape per `infer` call; growth can be handled by tearing down and rebuilding a model, but then the hard part of the discrete substrate lives outside RxInfer anyway.

## Spike setup

Both runnable spikes implement the same toy substrate:

- 2 hidden factors, initially 2 states each.
- 2 observation modalities.
- 4 one-step policies: `(1,1)`, `(1,2)`, `(2,1)`, `(2,2)` in Julia and zero-index equivalents in Python.
- Cross-trial Dirichlet counts for A and B.
- Expected-free-energy-like policy scores with preference and ambiguity terms.
- 200 trials.
- Trial 100 prototype: CRP-like spawn adds one state to factor 1, expanding A, B, beliefs, true environment matrices, and count banks from 2x2 to 3x2.
- Analytic Dirichlet evidence/BMR helper implemented directly over counts.

Run evidence:

| Candidate | Command | Result |
|---|---|---|
| v10 Julia port | `PATH="$HOME/.juliaup/bin:$PATH" julia projects/emergence-suite/spikes/v10_port/spike.jl` | `elapsed_sec=1.0190`, true-A concentration `0.5000 -> 0.5701`, final A entropy `0.5122`, growth `true`, post-growth shape `(2, 3, 2)` / `(3, 3, 2)` |
| pymdp | `uv run projects/emergence-suite/spikes/pymdp/spike.py` | `elapsed_sec=2.1421`, true-A concentration `0.5000 -> 0.5725`, final A entropy `0.4934`, growth `True`, post-growth shape `(2, 3, 2)` / `(3, 3, 2)`, `pymdp.Agent` reinit `ok` |

The v10 reference inspected was `/Users/brentbaum/dev/personal/projects/ifs-active-inference/library/src/active_inference/`, especially `core.jl`, `learning.jl`, `efe.jl`, and `agent.jl`. The RxInfer assessment is based on `projects/beautiful-simulation/src/models/sim1_common.jl`, the local `Project.toml` pinned to RxInfer `4.6.6`, and current RxInfer documentation describing `@model`/`infer` as factor-graph construction over model arguments. The pymdp API check used the current `infer-actively/pymdp` repository and package release path (`inferactively-pymdp==1.0.3`).

## Benchmark table

Scores are 1-5, where 5 means the candidate naturally supports the requirement with little framework work.

| Axis | v10 Julia port | pymdp | discrete-in-RxInfer |
|---|---:|---:|---:|
| 1. Cross-trial Dirichlet learning ergonomics | 5 | 3 | 2 |
| 2. Dynamic state-space growth mid-run | 5 | 3 | 2 |
| 3. Analytic BMR over Dirichlet counts | 5 | 5 | 4 |
| 4. 20x20 sweep x 20 seeds wall-clock estimate | 4 | 2 | 2 |
| 5. Interop with RxInfer stack needed by Sim 6 | 4 | 1 | 5 |
| **Total** | **23** | **14** | **15** |

## Axis notes

1. Cross-trial Dirichlet learning ergonomics

The v10 core already uses the exact abstractions this program needs: factored `A`, factored `B`, `pA`, `pB`, explicit learning rates, and pymdp-style EFE terms. The spike mirrors the v10 learning functions directly and stays readable.

pymdp has built-in A/B learning fields (`pA`, `pB`, `learn_A`, `learn_B`), but the modern JAX API is batch/time-shape sensitive and immutable enough that the spike kept count updates explicit. That is workable, but it means the suite would be partly inside and partly outside pymdp abstractions.

RxInfer is excellent for fixed graphical inference, and the existing repo uses it well for fixed joint-categorical HMMs. Cross-trial Dirichlet learning for Sims 1-4 would be external bookkeeping wrapped around repeated inference calls rather than an idiomatic RxInfer model.

2. Dynamic state-space growth

This is the discriminator. In the v10-style port, growth is just expansion of arrays and beliefs. The spike successfully expanded factor 1 at trial 100 and continued learning/scoring policies.

In pymdp, growth worked only by constructing a fresh `Agent` with larger static dimensions. That is acceptable for a toy spike, but a real Sim 1 CRP process would need careful transfer of histories, priors, policies, and compiled JAX state after every spawn.

In RxInfer, the practical path is also model reconstruction. Current local usage flattens a fixed joint state into a fixed HMM graph; a newly spawned factor state means a new transition matrix, new observation matrices, and a new graph/inference call. That loses the main advantage of putting the discrete core inside RxInfer.

3. Analytic BMR

All three can compute Friston-style Dirichlet model evidence externally in fewer than 50 lines because the sufficient statistics are the Dirichlet counts. v10/pymdp are strongest because the counts are the native state of the spike. RxInfer can do it if counts are owned outside the graph.

4. Wall-clock estimate

Raw spike timing gives:

- v10 port: `1.0190s * 8000 = 2.26h` with printing and unoptimized prototype code. Removing checkpoint logging and batching condition loops should plausibly put it under the 2h laptop target.
- pymdp: `2.1421s * 8000 = 4.76h` for the spike. Some of that is JAX/pymdp API overhead; a fully vectorized JAX design could improve it, but dynamic growth works against static compilation.
- RxInfer: likely worst for Sims 1-4 if each dynamic proposal requires graph reconstruction. The existing `beautiful-simulation` code already uses a manual forward filter beside RxInfer smoothing for speed, which is evidence that fixed graph inference is not the right inner loop for large discrete sweeps.

5. RxInfer interop

RxInfer is the native winner for Sim 6. The v10 Julia port is still a good neighbor: same language, same package/depot tooling, and easy reuse of `beautiful-simulation` run contracts (`summary.json`, `status.json`, `metadata.json`, per-seed CSV). pymdp would put Sims 1-4 across a Python/Julia boundary and complicate Sim 7 composition.

## Implementation consequence

Proceed with a small Julia package/module for Sims 1-4 that ports the v10 core concepts but writes outputs in the `beautiful-simulation` contract. Keep BMR and CRP spawn/prune as explicit count-space operations in the discrete core; pass summarized or replayable products into RxInfer/Sim 6 rather than sharing a single inference engine.

## References

- pymdp repository and current install/API notes: https://github.com/infer-actively/pymdp
- RxInfer repository and docs: https://github.com/ReactiveBayes/RxInfer.jl
- Local RxInfer usage: `projects/beautiful-simulation/src/models/sim1_common.jl`
- Local v10 reference: `/Users/brentbaum/dev/personal/projects/ifs-active-inference/library/src/active_inference/`
