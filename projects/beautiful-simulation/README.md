# BLT RxInfer Simulations

Executable Julia research package for the Beautiful Loop Theory simulations built on `RxInfer.jl`.

## Status

All three simulations are implemented and runnable:
- `sim1`: reliability-switching sensor fusion
- `sim2`: ambiguous perception / Bayesian binding
- `sim3`: BLT-HGF phase diagram

The package now reports discrete-state results in two modes:
- `filtered`: forward-only posteriors used for time-local theory metrics and headline support labels
- `smoothed`: full-sequence retrospective posteriors kept for latent recovery and comparison

Simulation 2's default causal regime now uses a phi-dependent global scene persistence (`g_diag_bind`, `g_diag_frag`) plus a fragment-side alternation control (`ambiguity_frag_flip_len`) so the ambiguity probe can test causal binding rather than benefit from a fixed side-channel.

Each result bundle writes:
- `summary.json`
- `status.json`
- `metadata.json`
- `per_seed_metrics.csv`
- mode-specific metric CSVs when applicable
- `posterior_traces.csv`
- image artifacts

`metadata.json` captures the config snapshot, git commit hash, Julia version, RxInfer version, and runtime.

## Reproduce

Run the default result bundle:

```bash
julia --project=projects/beautiful-simulation projects/beautiful-simulation/scripts/reproduce_all.jl
```

Run one simulation directly:

```bash
julia --project=projects/beautiful-simulation projects/beautiful-simulation/scripts/run_sim1.jl --config projects/beautiful-simulation/configs/sim1_default.yaml --output projects/beautiful-simulation/results/sim1_default
julia --project=projects/beautiful-simulation projects/beautiful-simulation/scripts/run_sim2.jl --config projects/beautiful-simulation/configs/sim2_default.yaml --output projects/beautiful-simulation/results/sim2_default
julia --project=projects/beautiful-simulation projects/beautiful-simulation/scripts/run_sim3.jl --config projects/beautiful-simulation/configs/sim3_default.yaml --output projects/beautiful-simulation/results/sim3_default
```

Run tests:

```bash
julia --project=projects/beautiful-simulation projects/beautiful-simulation/test/runtests.jl
```

## Notes

Simulation 3 now reports both:
- `implied_local_precision`: phase metric derived from inferred `z_t`
- `posterior_content_precision`: `mean(1 / var_q(x_t))` comparator

That deviation from the original draft reading is recorded explicitly in the result bundle so the phase-diagram interpretation is auditable.
