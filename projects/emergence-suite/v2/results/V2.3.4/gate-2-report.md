# V2.3.4 gate 2

Verdict: **PASS**.

## Metrics

- `identifiable_world_count`: 1500
- `pure_avoidance_world_count`: 1500
- `H_E_accuracy`: 0.992
- `exact_zero_accuracy`: 0.9923664122137404
- `brier`: 0.0070246215160336975
- `ece`: 0.0034947997089640496
- `context_efficacy_classification`: 0.875
- `eta_MAE`: 0.04178098999515974
- `danger_rate_MAE`: 0.010905439248869376
- `parameter_coverage`: 0.9733333333333334
- `pure_false_certainty_rate`: 0.011333333333333334
- `pure_joint_coverage`: 0.9586666666666667
- `pure_median_theta_eta_correlation`: 0.7435119202590341
- `probe_median_absolute_correlation_reduction`: 0.6809363724487543

## Criteria

- `H_E_accuracy_at_least_0_85`: PASS
- `exact_zero_accuracy_at_least_0_85`: PASS
- `brier_at_most_0_15`: PASS
- `ece_at_most_0_08`: PASS
- `context_efficacy_at_least_0_75`: PASS
- `eta_MAE_at_most_0_10`: PASS
- `danger_MAE_at_most_0_05`: PASS
- `coverage_at_least_0_90`: PASS
- `pure_false_certainty_at_most_0_05`: PASS
- `pure_joint_coverage_at_least_0_90`: PASS
- `pure_positive_correlation`: PASS
- `probes_reduce_correlation_at_least_0_15`: PASS
