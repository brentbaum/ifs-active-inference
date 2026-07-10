# Sim 1: De-confounded Freezing Phase Diagram

This is T4.6 Step A. The checked-in configuration is a pilot configuration:
seeds 1001–1010, label `pilot`, output `runs/sim1/pilot/`. No confirmatory
seeds have been run. Step B must audit and commit this code and its frozen
criteria before a separate process supplies fresh confirmatory seeds.

## De-confounded generative design

Each `(seed, omega)` generates one exogenous challenge stream and replays it
unchanged at every kappa. The stream fixes, trial by trial:

- whether challenge evidence is aversive or safe;
- aversive-event severity (1.0); and
- delivered observation precision (1.0).

The challenge outcome updates the cause's cue and affect banks and is the only
input to cause assignment, precision-weighted prediction error, arousal, CRP
pressure, and the arousal-scaled write rate. Kappa is absent from that path.

After the challenge, the selected action produces a separate consequence.
Kappa changes only how much overt flee, appease, and approach reduce the
probability of an aversive action consequence. Those consequences update only
the policy-specific outcome banks. Covert attenuation has no world-outcome
efficacy. Thus control can change learned action forecasts and policy without
changing which aversive challenges the agent was exposed to.

Omega has one evidence coupling: it changes exogenous challenge frequency via
`clamp(0.08 + 0.31*omega, 0.06, 0.97)`. Observation precision is fixed, so
omega is no longer routed through both event probability and precision.
Overwhelm in this implementation means repeated precision-weighted prediction
error from the omega-governed challenge stream, not an omega multiplier on
precision.

A1.4 checks the de-confound directly. For every fixed seed and omega it reports
the maximum across-kappa range of aversive counts, summed aversive severity,
and mean delivered precision. Exact equality (range zero) is stronger than the
registered statistical-equality requirement.

## Posterior-predictive behavioral revision

The safe probe runs on a copied cause for 24 trials. Before and after it, the
module computes:

- predicted aversive probability under approach from the learned
  policy-specific outcome bank; and
- approach probability from a softmax over the learned EFE policy scores.

The revision readout is
`max(pre_aversive - post_aversive, post_approach - pre_approach, 0)`.
KL divergence is neither computed nor used. A target is threat-relevant when
its pre-probe predicted aversive probability is at least 0.40. It is frozen at
behavior change at most 0.15 and revisable at change at least 0.25. Values in
between are deliberately unclassified. A grid cell is classified when at
least 5/10 pilot seeds share the label; a connected region requires at least
two orthogonally adjacent cells.

All classification values, the chronic path (`omega=1.00`, `kappa=0.0`, 600
trials), and arousal learning gain (60.0) are frozen after pilot calibration.
Their full provenance is in `magic-numbers.md`.

## Criteria battery

`configs/sim1-criteria.yaml` retains S1.1a/S1.1b and S1.2–S1.4, rewrites them
against behavioral revision under yoked evidence, retains A1.1–A1.3, and adds
A1.4. Unsupported criteria are reported as unsupported; pilot tuning does not
change their registered 0.80 or other success margins.

## Bundle schema v3

Representative causes produced by the real formation loop are exported under
`runs/sim1/pilot/artifacts/`. The manifest is
`sim1.bundle-manifest.v3`; each bundle is `sim1.bundle.v3`.

V3 preserves the learned sufficient statistics in `cause_banks`, adds the
evidence-yoking key and delivered/action-outcome counts to `formation`, and
replaces the v2 KL fields with behavioral posterior-predictive fields:

```json
{
  "schema_version": "sim1.bundle.v3",
  "seed": 1001,
  "route": "acute_spawn",
  "formation": {
    "omega": 1.8,
    "kappa": 0.0,
    "evidence_yoking_key": "seed=1001;omega=1.8",
    "aversive_evidence_count": 45,
    "aversive_evidence_severity_sum": 45.0,
    "mean_evidence_precision": 1.0,
    "aversive_action_outcome_count": 42
  },
  "revision_probe": {
    "metric": "posterior_predictive_behavior",
    "behavior_change": 0.08,
    "predicted_aversive_reduction": 0.08,
    "approach_probability_increase": 0.03,
    "pre_probe_predicted_aversive": 0.62,
    "post_probe_predicted_aversive": 0.54,
    "pre_probe_approach_probability": 0.12,
    "post_probe_approach_probability": 0.15
  },
  "cause_banks": {
    "cue_counts": {"safe": 1.0, "threat": 26.0},
    "affect_counts": {"safe": 3.0, "threat": 380.0},
    "policy_counts": {},
    "outcome_counts": {}
  }
}
```

The bundle is formation output, not a hand-authored Sim 4 stack. T4.1 may
consume the cause banks and formation provenance; it must still run its own
neutral developmental schedule and may not infer authored taxonomy from route
strings.

## Outputs

- `summary.json`: headline, behavioral-boundary, yoking, sensitivity, chronic,
  and criteria metrics.
- `per_seed_metrics.csv`: one row per seed/cell, including both evidence and
  action-consequence counts and all pre/post behavior values.
- `cell_metrics.csv`: cell aggregates.
- `posterior_traces.csv`: chronic trace for pilot seed 1001.
- `artifacts/`: real formation bundles and v3 manifest.
- `figures/phase_diagram.svg`: behavioral frozen/revisable phase diagram.
