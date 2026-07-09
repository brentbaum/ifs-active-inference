# Sim 2 Magic Numbers

Every hand-set constant in `configs/sim2.yaml` is listed here with its status.

| Constant | Value | Status |
| --- | ---: | --- |
| `n_melt_trials` | 60 | Matched corrective-evidence budget across the four regimes; long enough for interval BMR while keeping the run cheap. |
| `bmr_interval` | 5 | Registered fixed BMR cadence. The discreteness criterion requires the event window to be no wider than 10% of the 60-trial melt phase, so 5/60 = 0.083. |
| `early_prompt_max_trial` | 10 | Premature-prompt probe point before the D2 accessible counts can clear the prior odds. |
| `late_prompt_trial` | 45 | Late-prompt probe after witnessed counts have accumulated substantially beyond the BMR threshold. |
| `high_E` | 0.90 | Held witnessing depth. Uses the same normalized E_t scale as Sim 3. |
| `low_E` | 0.05 | Capture/low-depth condition. With D2 rho and the registered prior odds, low E_t leaves BMR below the prune threshold. |
| `flip_trial` | 3 | A2.2 one-trial E_t perturbation away from the 5-trial BMR cadence, so only effective precision changes. |
| `pi_part`, `beta_se` | 4.0, 1.0 | D1 log-precision tilt parameters, matching Sim 3's implementation pattern. |
| `lambda_ctx`, `gamma_se` | 1.0, 1.2 | D1 log-precision tilt parameters, matching Sim 3's implementation pattern. |
| `E0` | 1.0 | Magic number under D2's saturating accessibility function. Swept at 0.5, 1.0, and 2.0 in the full Sim 2 run. |
| `prior_log_odds` | -5.0 nats | BMR model prior odds against pruning. Swept by +/- 1 nat for A2.3. |
| `relational_count_good` | 1.0 | One self-indexed count for a full-weight high-depth relational observation. Lower-depth relational observations are weighted by the normalized `lambda_eff` share; informational observations route to threat/outcome banks and add zero root counts. |
| `relational_count_old` | 0.08 | Small residual count for the old coupling during a full-weight `met-well` relational observation, reversed for `met-badly`; keeps the D2 comparison finite and close to the toy demo's late-count ratio. |
| `ordinary_learning_rate` | 1.0 | One ordinary Bayesian count per corrective observation. |
| `attenuation_learning_rate` | 0.18 | Sim 1-inspired dissociative quiet condition: ordinary and relational observation precisions are present but written at reduced precision. |
| `policy_learning_rate` | 0.25 | Slow policy-bank learning relative to outcome/threat counts. |
| `policy_precision` | 3.0 | Readout gain for policy probabilities from learned banks and current inferred danger. |
| `root_avoidance_bias` | 0.48 | Frozen-root contribution to compulsive avoidance while the root coupling is present. |
| `danger_avoidance_bias` | 0.55 | Real-danger control contribution preserving adaptive fear when the cue is truly dangerous. |
| `competence_policy_floor` | 0.12 | Pseudocount floor so retained competence policies remain available after pruning. |
| `full_prior_met`, `full_prior_alone` | 2.0, 12.0 | D2 toy-demo full prior: the frozen coupling favors `alone-with-this`. |
| `reduced_prior_met`, `reduced_prior_alone` | 7.0, 7.0 | D2 toy-demo reduced prior: root coupling pruned to no strong relational preference. |

## Sensitivity Sweeps

- `E0_sweep = [0.5, 1.0, 2.0]` is emitted in `summary.json` and
  `e0_sweep_metrics.csv`.
- `prior_odds_offsets = [-1.0, 0.0, 1.0]` is emitted in `summary.json` and
  `prior_odds_sweep_metrics.csv`.

Any future amendment to `configs/sim2-criteria.yaml` must be logged with the
reason and made before rerunning the full preregistered suite.
