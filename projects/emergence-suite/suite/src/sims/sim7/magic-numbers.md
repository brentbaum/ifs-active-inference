# Sim 7 Magic Numbers

Sim 7 is a composition run, so most constants are inherited from accepted
component configs. Local constants are preregistered in `configs/sim7.yaml`.

| Constant | Value | Source / debt |
| --- | ---: | --- |
| `therapy_session_cap` | 96 | IOU. Chosen to exceed Sim 4's 64-session descent window and allow BMR checks every 5 sessions without changing component parameters. |
| `adult_baseline_trials` | 8 | IOU. Logging-only count for Act II cue encounters; adult capture is read from the accepted D1 precision balance. |
| `resilient_omega` | 1.40 | Sim 1 high-intensity control-preserved region; paired with high `kappa` as the resilient-world acute event. |
| `resilient_kappa` | 1.00 | Sim 1 high-control setting used to test no frozen stack under preserved control. |
| `capture_threshold` | 0.70 | Borrowed from the accepted capture range in Sims 2/5; used only for readout. |
| `transfer_slope_threshold` | 0.08 | IOU. Minimum post-melt contact-probability slope across the Sim 3 root-coupled continuum. |
| `flat_transfer_slope_threshold` | 0.03 | IOU. H2/resilient control flatness readout on identical transfer axes. |
| `post_melt_original_cue_threshold` | 0.62 | Sim 3-style policy readout threshold for original-cue re-encounter after root revision. |
| `melt_window_fraction_threshold` | 0.10 | Directly from the suite's discreteness convention: >50% structural drop within <=10% of the melt phase. |
| `slow_duration_min` | 20 | IOU. Classifier cutoff separating slow accumulation from one-event formation. |
