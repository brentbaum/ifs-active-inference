# V2.6a gate 2

Verdict: **FAIL**.

## Metrics

- `confusion_matrix`: [[374, 1, 0, 0], [0, 371, 2, 2], [0, 0, 374, 1], [4, 1, 0, 370]]
- `diagonal_recovery`: {'reliable_contingent': 0.9973333333333333, 'soothing_noncontingent': 0.9893333333333333, 'intrusive': 0.9973333333333333, 'unstable': 0.9866666666666667}
- `macro_recovery`: 0.9926666666666667
- `brier`: 0.1293226642643253
- `ece`: 0.20101343381872663
- `posterior_set_coverage`: 1.0
- `transition_switch_parameter_mae`: 0.0186938114207919
- `switch_onset_median_absolute_error`: 0.0
- `local_precision_calibration_error`: 0.01687170887816234
- `world_count`: 1500
- `stable_count`: 752
- `switching_count`: 748

## Criteria

- `each_diagonal_at_least_0_75`: PASS
- `macro_at_least_0_75`: PASS
- `brier_at_most_0_15`: PASS
- `ece_at_most_0_08`: FAIL
- `coverage_at_least_0_90`: PASS
- `switch_mae_at_most_0_10`: PASS
- `onset_median_at_most_3`: PASS
- `local_precision_error_at_most_0_08`: PASS
