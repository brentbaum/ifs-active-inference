# V2.6a gate 2 — repaired apparatus

Verdict: **FAIL**.

The original Gate-2 FAIL remains immutable. Calibration here is per-slice; occupancy-label calibration is descriptive.

## Metrics

- `confusion_matrix`: [[360, 11, 8, 13], [16, 337, 10, 27], [7, 6, 329, 7], [10, 23, 15, 321]]
- `diagonal_recovery`: {'reliable_contingent': 0.9183673469387755, 'soothing_noncontingent': 0.8641025641025641, 'intrusive': 0.9426934097421203, 'unstable': 0.8699186991869918}
- `macro_recovery`: 0.8987705049926129
- `brier`: 0.14823808079259085
- `ece`: 0.0031028041947577687
- `posterior_set_coverage`: 0.9880555555555556
- `occupancy_label_brier_descriptive`: 0.29383972585284995
- `occupancy_label_ece_descriptive`: 0.27949769284206827
- `occupancy_label_coverage_descriptive`: 0.9993333333333333
- `transition_switch_parameter_mae`: 0.017626147746432983
- `switch_onset_median_absolute_error`: 5.0
- `local_precision_calibration_error`: 0.0381788763970843
- `world_count`: 1500
- `calibrated_slice_count`: 72000
- `stable_count`: 78
- `switching_count`: 1422

## Criteria

- `each_diagonal_at_least_0_75`: PASS
- `macro_at_least_0_75`: PASS
- `brier_at_most_0_15`: PASS
- `ece_at_most_0_08`: PASS
- `coverage_at_least_0_90`: PASS
- `switch_mae_at_most_0_10`: PASS
- `onset_median_at_most_3`: FAIL
- `local_precision_error_at_most_0_08`: PASS
