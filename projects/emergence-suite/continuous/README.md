# Sim 6a Continuous, Stage 3

This standalone Julia project implements ticket T2.4: the continuous three-layer Phi bridge and U2 basin map.

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

