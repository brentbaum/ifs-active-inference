# T-CAP1 Census-3: calibration-based metastability

Status: **COMPLETE_PUBLIC_NON_CRITERIAL_CENSUS_3**. The earlier fixed-point result remains negative: 2/8,000 transparent-feedback worlds and 0/8,000 represented/control worlds.

The census serialized 12000 worlds across 486 cells before aggregation. Recovery uses `null`; the coupling-zero q95 area threshold is `34.439763295961285`. Class counts are `{"material_metastability": 0, "null": 268, "pathological_nonqualifying": 12, "weak": 206}`.

## Mechanical panel

- **null**: cell 0, fingerprint rate 0.0000, `{"allocation_persistence": 0.0, "bundle_transition_persistence": 0.85, "coupling_strength": 0.0, "cue_intensity": 0.25, "meta_observation_reliability": 0.6}`
- **weak**: cell 81, fingerprint rate 0.0000, `{"allocation_persistence": 0.0, "bundle_transition_persistence": 0.85, "coupling_strength": 2.0, "cue_intensity": 0.25, "meta_observation_reliability": 0.6}`
- **material_metastability**: no occupied cell
- **pathological_nonqualifying**: cell 16, fingerprint rate 0.0000, `{"allocation_persistence": 0.6, "bundle_transition_persistence": 0.99, "coupling_strength": 0.0, "cue_intensity": 0.25, "meta_observation_reliability": 0.8}`

## Seal-eligibility evaluation (factual; no seal decision)

- `at_least_three_original_grid_cells`: **False**
- `at_least_three_parameter_combinations`: **False**
- `fingerprint_rate_at_least_0_10_per_selected_cell`: **False**
- `coupling_zero_identity_exact`: **True**
- `consistent_transparency_direction`: **False**
- `eventual_recovery_at_least_0_80`: **False**

All conditions factually met: **False**. Coupling-zero identity was exact in 2025 applicable worlds. Trace SHA-256: `6d2ac75417b362b298568c5695b4328eb6c4795e5af0c7a7be6730f2df1b99fb`.

## Recovery and danger-calibration localization

None of the 15 preregistered epsilon/k candidates attained the 0.80 recovery requirement. The largest observed reference recovery rate was `0.6523341523341524`. Therefore no epsilon/k pair was frozen and no world could satisfy the complete fingerprint.

On continuing-danger post-withdrawal slices, the allocation-aware oracle had ECE `0.030402241158490682` and Brier `0.07209627612190457` across `57544` slice forecasts. Continuing-danger worlds were never counted as metastability fingerprints.
