# Sim 6b: Spawn in the Inferred-Depth Model

This module implements T2.5 in `EmergenceSuite.Sim6b`. It couples a Sim
1-style CRP formation loop to Sim 6a's categorical inferred-depth posterior.

## Model Contract

- Formation uses latent causes with cue, affect, policy-outcome, and policy-use
  Dirichlet banks. CRP pressure accumulates when the best existing cause has
  low posterior predictive probability.
- Realized precision-weighted PE sets arousal and the structural write learning
  rate, matching Sim 1's `learning_rate_base + learning_rate_arousal_gain *
  arousal` rule.
- Reflexivity at write is the current level-3 inferred depth readout `E_t`.
  Sim 1's arousal-linked reflexivity input is not used.
- Level 3 reuses Sim 6a's categorical filtering:
  `arousal -> volatility_observation -> update_depth_with_evidence ->
  effective_precisions`.
- The clamped arm is an intervention on the posterior: `q(d)` is fixed at the
  high-depth distribution. It is not a model change; downstream writes and
  probes still read `q(d)`.
- The yoked control receives the same PE and arousal stream, but the volatility
  observation is withheld from level 3. Depth remains high by inference.
- Sim 2's accessible-statistics pathway is implemented as root-coupling counts
  that accrue at the D1 depth-discounted relational rate. BMR uses the suite's
  canonical `BMR.reflexive_prior_swap_delta`.

## Registered Arms

- `unclamped`: acute-overwhelm volatility evidence reaches level 3.
- `clamped`: identical PE stream and structural write rates; high `q(d)` is
  held by intervention.
- `yoked-control`: identical PE stream with volatility evidence withheld from
  level 3.

## Revision Threshold

The rescue floor is set to 25% revision. It is anchored to the accepted Sim 1
run `suite/runs/sim1/sim1-t1-2/per_seed_metrics.csv`: non-frozen aversive rows
average 36.765% revision and reach 85.087%, while frozen rows average 5.787%
and remain below 9.993%. The floor is therefore above the frozen range and
below the observed ordinary mean.

## Outputs

- `summary.json`, `status.json`, `metadata.json`
- `per_seed_metrics.csv`
- `posterior_traces.csv`
- `ordinary_revision_probe_metrics.csv`
- `recovery_witnessed_probe_metrics.csv`
- `figures/depth_recovery.svg`
- `criteria-results.json`
