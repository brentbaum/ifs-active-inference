# Sim 6a: Inferred Depth and Inference-Face Collapse

This module implements T2.1 inside `EmergenceSuite.Sim6a`. It is scoped to
`src/sims/sim6a/`; the package runner dispatches here only when
`experiment: sim6a` is selected.

## Model Contract

- Level 1 imports frozen Sim 1 bundle artifacts using schema `sim1.bundle.v2`.
  The imported affect bank supplies the bundle cue likelihood; present-context
  evidence supplies the context likelihood.
- Level 2 is the effective-precision balance. It is never set directly by a
  parameter during a trial. It is computed from the level-3 depth posterior by
  log-precision message passing:

  ```text
  pi_eff     = exp(E_q[log pi_bundle(d)])
  lambda_eff = exp(E_q[log lambda_context(d)])
  C_t        = pi_eff / (pi_eff + lambda_eff)
  ```

- Level 3 is a discrete posterior over depth coordinate `e(d)`. `E_t` is the
  posterior readout `E_q[e(d)]`; it is not an input.
- The depth-to-log-precision maps are affine and collinear in the registered
  run:

  ```text
  log pi_bundle(d)     = log r_t + log pi_part - beta * e(d)
  log lambda_context(d) = log lambda_ctx + gamma * e(d)
  ```

  `beta` and `gamma` are the map slopes. Under this condition, the closed-form
  D1 tilt is exact.
- `o_self` is process-side. The process emits the actual dominant
  configuration (`bundle` or `context`). The agent reads it through a
  depth-indexed reliability map. Transparency/opacity are readouts from the
  posterior sharpness over this self-observation.
- Collapse is inference-face only. The code path is:

  ```text
  precision_weighted_prediction_error
    -> volatility_observation
    -> update_depth_with_evidence
    -> effective_precisions
    -> E_t readout
  ```

  There is no assignment from arousal to `E_t`, the depth posterior, or the
  precision balance.

## Preregistered Thresholds

`configs/sim6a-criteria.yaml` registers the Stage 1 criteria before the full
run: monotone arousal dose-response across at least four levels, recovery to
80% of baseline within the safety window, transparent and opacified
bundle-active regimes in one run, a one-variable biography figure, D1 exactness
within 1%, a broken-collinearity D1 probe, identifiability correlation at
`r >= 0.8`, and no second-order oscillation inside the verified envelope.

For D3, the preregistered criterion is an S-curve support flag based on
log-odds linearity plus a curvature sign-change check over the inferred-depth
support. If the flag is absent, the criterion is labeled `null`, not tuned.

## Stability Note

The Sandved-Smith stability envelope was derived for a bounded-relaxation
precision update. Sim 6a does not use that update. It uses categorical
filtering over depth states and sends geometric-mean log-precision messages
downward. The shipped run therefore re-verifies stability directly: effective
precisions remain in `[0.9109, 5.3438]`, within the `[0.5, 8.0]` envelope, and
the oscillation detector finds zero oscillating seeds across 24 seeds. There is
no mental-policy horizon in Stage 1.

## D3 Outcome

The registered run labels D3 `null`. `C_t` is monotone decreasing in inferred
depth and log-odds are affine in `E_t` (`R^2 = 1.0`), as expected from the D1
balance. But over the five-state support the curvature does not change sign:
second differences remain negative (`min = -0.0270`, `max = -0.0061`). The
actual form is therefore a monotone concave precision-share curve over this
depth range, not the preregistered S-curve.

The model code contains no logistic or sigmoid function. The audit command used
for the report is:

```sh
rg -n "logistic|sigmoid" projects/emergence-suite/suite/src/sims/sim6a/Sim6a.jl
```

## Stage 2 Result

![Stage 2 EFE decomposition crossover](../../../runs/sim6a/stage2-preregistered/figures/stage2-efe-crossover.svg)

Stage 2 adds two mental actions, `allocate-to-reflexive` and `allocate-to-threat`, selected by expected free energy from the current depth posterior, cause-bank threat belief, learned reflexive-safety contingency, and fixed survival-relevant preferences. In the preregistered run, acute-threat beliefs select `allocate-to-threat`; the ranking is carried by pragmatic value, with epistemic value favoring reflexive allocation until threat belief crosses the figure's zero line. Under activation, `allocate-to-reflexive` is initially EFE-dominated, then becomes optimal after 4 safe/co-regulated evidence observations. With policies enabled, the Stage-1 dose-response collapse and recovery checks still meet their registered tolerances.

## Outputs

- `summary.json`: config snapshot, imported bundle inventory, model contract,
  and aggregate metrics.
- `status.json`: implementation pass flag and criteria-level theory label.
- `metadata.json`: seed/config/git/runtime metadata.
- `per_seed_metrics.csv`: one row per seed for biography-level metrics.
- `posterior_traces.csv`: trial-level `E_t`, `C_t`, arousal, volatility,
  depth-posterior precision, bundle posterior, and `o_self` sharpness.
- `dose_response_metrics.csv`: arousal-level collapse probe.
- `d1_validation.csv`: exact affine and broken-collinearity D1 probe rows.
- `identifiability_metrics.csv`: simulated-inversion recovery correlations.
- `figures/biography.svg`: one-axis biography trace with `E_t`, `C_t`, and
  `o_self` sharpness.
- `criteria-results.json`: labels emitted from
  `configs/sim6a-criteria.yaml`.
