# Sim 4: Trust Ledger

This module implements T3.1 inside `EmergenceSuite.Sim4`. It is scoped to
`src/sims/sim4/`; the package runner dispatches here only when
`experiment: sim4` is selected.

## Model Contract

- The developmental stack is grown by neutral latent-cause formation records:
  one early acute-overwhelm cause, one breakthrough-flood spawned cause, and
  one chronic-management slow-accumulation cause.
- Taxonomy words are readout labels only. The fixed readout rules are
  preregistered in `configs/sim4-criteria.yaml` and emitted in
  `summary.json`.
- Access to an earlier cause is computed from the currently active policy
  outputs of later causes. The module logs `access_to_cause*`; it does not
  represent access as a latent state.
- Each later cause carries a relational Dirichlet bank over
  `met-well / met-badly / catastrophic`. Those counts update only when that
  cause is actually contacted.
- E_t enters only through the D1 effective-precision balance used to weight
  relational writes.
- The high-E_t Self-process selects contact targets by expected free energy:
  expected relational outcome, information gain from the relational forecast
  only when the selected contact can update that forecast, and a saturation
  cost for repeating an already-settled forecast. No term reads depth index,
  stack position, or taxonomy label.

## Outputs

- `summary.json`: preregistration record, taxonomy readouts, EFE audit,
  headline metrics, ablation metrics, and contact-choice sequences.
- `per_seed_metrics.csv`: one row per seed with session ordering, permission,
  asymmetry, bank-update, and contact-choice sequence fields.
- `posterior_traces.csv`: session-level contact choices, computed access
  values, trust curves, EFE scores, and deepest-cause revision.
- `formation_events.csv`, `taxonomy_readouts.csv`,
  `forced_direct_access.csv`, `habit_control.csv`: probe-specific readouts.
- `figures/descent.svg`: computed access per layer, protector trust curves,
  deepest-cause revision onset, contact choices, and forced-access panel.
- `criteria-results.json`: labels emitted from `configs/sim4-criteria.yaml`.

## EFE Audit

The objective terms are:

- `expected_outcome`: dot product of the relational forecast with fixed
  utilities for met-well, met-badly, and catastrophic outcomes.
- `information_gain`: entropy of the same relational forecast discounted by
  Dirichlet concentration, credited only when the contact can update the
  forecast being sampled.
- `settled_forecast_cost`: a trust-threshold saturation cost for repeating a
  contact whose forecast is already settled.

No EFE term encodes depth ordering, stack position, taxonomy label, or
"protectors first".
