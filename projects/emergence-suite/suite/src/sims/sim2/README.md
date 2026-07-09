# Sim 2: Hysteresis Loop and BMR Melt

This module implements T1.3 inside `EmergenceSuite.Sim2`. It is scoped to
`src/sims/sim2/`; the package runner dispatches here only when
`experiment: sim2` is selected.

## Model Contract

- Sim 2 imports frozen bundle artifacts using schema `sim1.bundle.v2`.
  `formation` and `revision_probe` are metadata; `cause_banks` seed ordinary
  threat and policy sufficient statistics.
- The root structure is a two-state relational coupling:
  `met-in-this` vs. `alone-with-this`. The full prior encodes the frozen
  coupling; the reduced prior is the pruned/no-coupling alternative. Threat and
  policy banks remain separate ordinary Dirichlet banks.
- E_t enters inference only through the D1 log-precision tilt:
  `pi_eff = pi_part * exp(-beta * E_t)`,
  `lambda_eff = lambda_ctx * exp(gamma * E_t)`, with `C_t` logged as the
  normalized bundle-prior precision share.
- The environment emits one observation content per trial. Likelihood routing,
  not a channel switch, determines which sufficient statistics it can update:

  | Observation content | Likelihood target | Root-coupling update |
  | --- | --- | --- |
  | `met-well` | Relational expectation: how shown material is met | Adds weighted evidence for `met-in-this`, plus the registered residual old-coupling count |
  | `met-badly` | Relational expectation: how shown material is met | Adds weighted evidence for `alone-with-this`, plus the registered residual met count |
  | `informational-safe` | Threat/outcome bank | Adds ordinary safe-outcome evidence only; root likelihood is flat, so root-coupling statistics receive zero |
  | `absent` | No observation | Zero root-coupling statistics |

  This is the C3 likelihood claim in code form: informational content can be
  useful evidence about the cue's outcome while still being no evidence about
  the root relational expectation.
- BMR is evaluated every `bmr_interval` trials and in prompted probes. Pruning
  is a structural event: once the reduced model wins, root-coupling structural
  precision drops to the reduced prior while threat and policy banks are
  retained.

## Derived Melt Gate

The melt gate follows D2 directly. The BMR posterior is not the externally
available raw count table. It is the reflexively accessible posterior:

```text
a_E = b_F + rho(E_t) * n
rho(E_t) = E_t / (E_t + E_0)
```

`n` is the weighted root-coupling evidence accumulated from relational
observation content. The module calls the suite's canonical
`BMR.reflexive_prior_swap_delta`, which wraps the Friston-2017 prior-swap
identity. At `E_t = 0`, the data-driven BMR term cancels exactly, so the
comparison is uninformative except for model prior odds. There is no separate
"block prune if E_t is low" rule.

## Relational Accumulation Weight

Relational observations write root-coupling statistics on every trial where the
content is relational. The write weight uses the same D1 effective-precision
balance logged elsewhere:

```text
pi_eff(E_t) = pi_part * exp(-beta * E_t)
lambda_eff(E_t) = lambda_ctx * exp(gamma * E_t)
lambda_share(E_t) = lambda_eff(E_t) / (pi_eff(E_t) + lambda_eff(E_t))
w_rel(E_t) = min(1, lambda_share(E_t) / lambda_share(high_E))
w_obs(E_t) = w_rel(E_t) * attenuation_scale
```

`attenuation_scale` is `attenuation_learning_rate` in dissociative quiet and
`1.0` otherwise. `high_E` therefore defines one registered relational count per
high-depth witnessed trial; low-E capture receives the discounted trickle
implied by the same precision balance. Informational observations have
`w_obs = 0` for root coupling because their root likelihood is flat.

## Imported Bundles

`configs/sim2.yaml` uses the manifest-listed T1.2 artifacts from
`runs/sim1/sim1-t1-2/artifacts/`:

- Acute/frozen-source cohort: `bundle_seed1020_omega1p4_kappa0p0.json`,
  `bundle_seed1001_omega1p4_kappa0p1.json`,
  `bundle_seed1008_omega1p4_kappa0p1.json`,
  `bundle_seed1013_omega1p4_kappa0p1.json`,
  `bundle_seed1004_omega1p6_kappa0p0.json`.
- Slow-accumulation cohort: `bundle_slow_seed1001_trial105.json`,
  `bundle_slow_seed1002_trial95.json`.

The run summary records the resolved bundle files, Sim 1 seeds, routes,
families, and imported structural precision values.

## Outputs

- `summary.json`: config snapshot, imported bundle inventory, D2 melt-gate
  declaration, headline metrics, adversarial probe metrics, E_0 sweep, and
  prior-odds sweep.
- `per_seed_metrics.csv`: one row per seed per four-regime condition.
- `posterior_traces.csv`: trial-level structural/effective precision traces.
- `prompt_probe_metrics.csv`, `real_danger_metrics.csv`,
  `content_swap_metrics.csv`, `et_flip_metrics.csv`,
  `e0_sweep_metrics.csv`, `prior_odds_sweep_metrics.csv`: probe-specific
  readouts.
- `figures/hysteresis.svg`: structural root precision vs. cumulative
  corrective evidence for the four registered regimes, with first-passage
  markers.
- `criteria-results.json`: labels emitted from `configs/sim2-criteria.yaml`.

## E_0 Sweep

`E_0` is treated as a magic number. The preregistered config runs
`E_0 in [0.5, 1.0, 2.0]` and writes the melt rate, mean prune trial, mean root
revision, and drop fraction for each value. The default reported trajectory uses
`E_0 = 1.0`.
