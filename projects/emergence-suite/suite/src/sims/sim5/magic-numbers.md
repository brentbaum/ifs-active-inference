# Sim 5 Magic Numbers

All thresholds were preregistered in `configs/sim5-criteria.yaml` before the
first full run.

## Session and evidence budgets

- `n_session_trials = 60`: inherited from Sim 2's melt-phase budget so root BMR
  has the same number of contact opportunities.
- `contact_start_trial = 6`: keeps an activation-only opening before witnessed
  contact can accumulate.
- `bmr_interval = 5`: inherited from Sim 2's BMR cadence.

## Depth grid and priors

- `depth_grid = [0.0, 0.25, 0.50, 0.75, 1.0]`: inherited from Sim 6a's
  accepted categorical depth filter.
- `low/medium/high_baseline_prior`: preregistered self-practice capacity sweep.
  These are explicit baseline-capacity settings, not condition-specific switches.
- `dyad_baseline_prior`: moderate client prior used for all therapist
  conditions.
- `transition_mix = 0.08`: floor on the level-3 transition back toward the
  client's baseline prior. The realized prior pull is
  `max(transition_mix, expected_depth(baseline_prior)^2)`, so low baseline
  capacity gets only the floor while high/owned capacity becomes a stable prior
  across activation trials.

## Likelihood and precision constants

- `activation_drive = 0.86`: bundle-live activation strength. Realized PE is
  scaled by current capture, so higher depth can reduce subsequent volatility
  evidence without a direct depth write.
- `activation_jitter = 0.04`: deterministic seed/trial variation to avoid
  single-trajectory artifacts.
- `volatility_precision = 1.35`: makes activation evidence strong enough to
  collapse low-baseline self-practice.
- `coreg_precision = 2.35`: makes regulated/dysregulated body evidence strong
  enough to test the same-words/different-bodies contrast.
- `regulated_coreg_by_depth = [0.08, 0.16, 0.36, 0.74, 0.93]`: likelihood of
  observing a regulated other at each depth state; the dysregulated likelihood
  is its complement.

## Sim 2 inherited revision constants

- `pi_part = 4.0`, `lambda_ctx = 0.90`, `beta = 1.00`, `gamma = 1.15`: same
  scale as Sim 6a's accepted effective-precision mapping.
- `relational_count_good = 1.0`, `relational_count_old = 0.08`: inherited from
  Sim 2's accessible root statistics.
- `full_prior_met = 2.0`, `full_prior_alone = 12.0`,
  `reduced_prior_met = 7.0`, `reduced_prior_alone = 7.0`,
  `prior_log_odds = -5.0`, `E0 = 1.0`: inherited from Sim 2's D2 BMR
  comparison.

## Borrowed-then-owned prior learning

- `ownership_prior_concentration = 24.0`: converts the low baseline prior into
  slow Dirichlet counts.
- `ownership_learning_rate = 0.72`: adds mean regulated-session depth occupancy
  to the client's prior counts after each borrowed-depth session.
- `ownership_revision_floor = 8.0`: same revision floor as S5.1's contrast
  margin.
- `ownership_max_sessions = 12`: bounded course length for the preregistered
  ownership search.
