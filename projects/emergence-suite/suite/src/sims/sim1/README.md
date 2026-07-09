# Sim 1: Freezing Phase Diagram

This module implements T1.2 inside `EmergenceSuite.Sim1`. It is scoped to
`src/sims/sim1/`; the package runner dispatches here only when
`experiment: sim1` is selected.

## Model Contract

- The environment samples aversive/safe outcomes from the configured
  `omega`/`kappa` cell. `omega` changes outcome intensity and observation
  precision; `kappa` changes how much overt actions alter outcome
  probabilities.
- The agent has latent causes with per-cause Dirichlet banks for cue,
  affective outcome, policy-specific outcome, and policy use.
- Policies are selected by an expected-free-energy decomposition over the
  currently dominant cause's learned banks. No policy score reads `omega` or
  `kappa` directly.
- A CRP growth proposal accumulates only when the posterior predictive under
  existing causes is persistently below threshold. The spawned cause is then
  updated by the same arousal-scaled Dirichlet write as any existing cause.
- Arousal is computed from realized precision-weighted surprise. Tier A
  reflexivity is an arousal-linked input and is logged at write time.
- Later revisability is measured by copying the dominant aversive cause,
  running `disconfirming_trials` safe-evidence updates at ordinary arousal, and
  normalizing the KL divergence from the pre-probe affect bank. Pre/post
  aversive posterior means are logged alongside the KL readout.
- Region labels (`frozen`, `revisable`, `shutdown`) are post-run readouts. No
  generative-model factor is named `exile`, `protector`, or `gate`.

## Criteria Amendments

- S1.1a/S1.1b now classify the dominant aversive cause whether it was spawned
  acutely or hardened by accumulation. Reason: the previous spawned-only
  readout made the revisable region empty by construction and excluded the
  slow-kinetics route.
- `later_revision_percent` now means the measured normalized KL change of the
  target cause's affect bank after safe probe trials, with pre/post aversive
  means logged. Reason: the previous readout was a formula over condition
  variables.
- Thresholds in `configs/sim1-criteria.yaml` are unchanged.

## Bundle Artifact Schema

Representative frozen-region causes are exported under each run's `artifacts/`
directory. The schema was bumped because bundles now include measured revision
probe fields, affect banks, policy-specific outcome banks, and route metadata.

Manifest:

```json
{
  "schema_version": "sim1.bundle-manifest.v2",
  "bundle_count": 10,
  "slow_accumulation_bundle_count": 2,
  "bundles": ["bundle_seed1001_omega2p8_kappa0p0.json"],
  "schema": "sim1.bundle.v2"
}
```

Each bundle file has schema version `sim1.bundle.v2`:

```json
{
  "schema_version": "sim1.bundle.v2",
  "seed": 1001,
  "route": "acute_spawn",
  "formation": {
    "omega": 2.8,
    "kappa": 0.0,
    "arousal_at_write": 0.9,
    "reflexivity_at_write": 0.2,
    "spawned": true,
    "spawn_count": 1,
    "posterior_predictive_min": 0.001,
    "crp_threshold_last": 0.064
  },
  "revision_probe": {
    "disconfirming_trials_measured": true,
    "later_revision_percent": 4.2,
    "pre_probe_aversive_mean": 0.91,
    "post_probe_aversive_mean": 0.87,
    "normalized_kl_from_pre_probe": 0.005,
    "structural_precision": 410.0
  },
  "cause_banks": {
    "cue_counts": {"safe": 1.0, "threat": 26.0},
    "affect_counts": {"safe": 3.0, "threat": 380.0},
    "policy_counts": {
      "approach": 1.0,
      "flee": 4.0,
      "appease": 1.0,
      "attenuate": 68.0
    },
    "outcome_counts": {
      "approach": {"safe": 1.0, "threat": 1.0},
      "flee": {"safe": 1.0, "threat": 20.0},
      "appease": {"safe": 1.0, "threat": 1.0},
      "attenuate": {"safe": 2.0, "threat": 360.0}
    }
  }
}
```

T1.3 should treat `formation` and `revision_probe` as metadata and
`cause_banks` as imported sufficient statistics.

## Outputs

- `summary.json`: headline metrics, criteria metrics, phase-boundary readouts,
  three-traits measurements, slow-path result, sensitivity sweep, and bundle
  manifest path.
- `per_seed_metrics.csv`: one row per seed per sweep cell.
- `cell_metrics.csv`: aggregate sweep cell metrics.
- `posterior_traces.csv`: slow-kinetics path for the first configured seed.
- `figures/phase_diagram.svg`: omega-kappa phase diagram with the slow path.
