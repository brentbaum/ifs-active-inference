# V2.6a gate 3

Verdict: **PASS**.

## Metrics

- `regulation_only_global_depth_effect`: {'mean': 0.41738937659215797, 'lower_95': 0.412819397304387, 'upper_95': 0.42195935587992894}
- `regulation_only_root_revision`: {'mean': 0.0, 'lower_95': 0.0, 'upper_95': 0.0}
- `regulation_only_transfer`: {'mean': 0.0, 'lower_95': 0.0, 'upper_95': 0.0}
- `regulation_plus_root_uptake_increment`: {'mean': 0.18819028353136144, 'lower_95': 0.1861418407202531, 'upper_95': 0.19023872634246977}
- `regulation_plus_root_transfer_increment`: {'mean': 0.15996174100165722, 'lower_95': 0.15822056461221515, 'upper_95': 0.1617029173910993}
- `broadcast_off_local_partner_max_error`: 0.0
- `broadcast_off_depth_increment`: {'mean': 0.0, 'lower_95': 0.0, 'upper_95': 0.0}
- `broadcast_off_root_uptake_increment`: {'mean': 0.0, 'lower_95': 0.0, 'upper_95': 0.0}
- `soothing_false_reliable_rate`: 0.0
- `soothing_mean_arousal`: 0.9306823323389333
- `intrusive_false_reliable_rate`: 0.0
- `switch_onset_median_absolute_error`: 0.0
- `future_precision_forecast_decrease`: {'mean': 0.7044853743075514, 'lower_95': 0.6990445428801384, 'upper_95': 0.7099262057349645}
- `fixed_G_transfer_max_absolute`: 0.0
- `cell_counts`: {'reg_0_root_0': 1000, 'reg_1_root_0': 1000, 'reg_0_root_1': 1000, 'reg_1_root_1': 1000}

## Criteria

- `1_regulation_only_depth`: PASS
- `2_regulation_only_root_revision`: PASS
- `2_regulation_only_transfer`: PASS
- `3_root_uptake_increment`: PASS
- `3_transfer_increment`: PASS
- `4_broadcast_local_preserved`: PASS
- `4_broadcast_removes_depth`: PASS
- `4_broadcast_removes_uptake`: PASS
- `5_soothing_not_reliable`: PASS
- `6_intrusive_not_reliable`: PASS
- `7_switch_learned`: PASS
- `8_fixed_G_transfer_zero`: PASS
