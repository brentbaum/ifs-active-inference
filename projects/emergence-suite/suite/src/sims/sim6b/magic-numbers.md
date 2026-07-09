# Sim 6b Magic Numbers

All constants are preregistered in `configs/sim6b.yaml`.

- `rescue_revision_floor = 25.0`: Anchored to the accepted Sim 1 run. Frozen
  rows average 5.787% revision and max at 9.993%; non-frozen aversive rows
  average 36.765% and max at 85.087%. The floor is above frozen and below the
  ordinary mean.
- `collapse_E_threshold = 0.35`, `high_E_threshold = 0.70`: Readout thresholds
  over Sim 6a's five-state depth grid, chosen to separate low-depth states
  `[0.0, 0.25]` from high-depth states `[0.75, 1.0]`.
- `clamp_depth_prior = [0.00, 0.01, 0.03, 0.16, 0.80]`: Intervention posterior
  with expected depth above 0.9 while retaining a nonzero categorical support
  except at the zero-depth endpoint.
- `acute_omega = 1.65`, `acute_kappa = 0.05`: Acute-overwhelm schedule near
  Sim 1's accepted frozen boundary, with low control so CRP spawning remains
  possible.
- `ordinary_probe_trials = 24`: Matches Sim 1's disconfirming probe budget.
- `witnessed_contact_trials = 60`: Matches Sim 2's melt-trial budget.
- `accessible_formation_old_count = 0.40`: Formation-time accessible
  root-coupling accrual per structural write at high depth. Low-depth writes
  are discounted by the same D1 precision balance.
- `prior_log_odds = -5.0`, root priors `[2, 12] -> [7, 7]`, `E0 = 1.0`: Reused
  from Sim 2's accepted BMR revision probe.
- `clamp_yoke_tolerance = 12.0`: Allows the intervention and yoked-control
  ordinary revision means to differ by less than one third of the Sim 1
  ordinary non-frozen mean.
