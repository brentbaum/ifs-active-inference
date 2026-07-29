# C-V26A sealed verdict

Immutable sealed verdict: **PASS**.

Pass requires all five sealed criteria; no threshold, direction, or non-blocking family was changed.

## Criteria

- `1_stable_reliable`: **PASS** — {'global_precision_difference': {'lower_95': 0.4118739328745117, 'mean': 0.4184651837261833, 'upper_95': 0.4250564345778549}, 'recovery_rate': 1.0, 'regulation_only_root_log_bf_max': 0.0}
- `2_soothing_noncontingent`: **PASS** — {'cell1_minus_cell2_depth': {'lower_95': 0.4197841647216609, 'mean': 0.4283594246027989, 'upper_95': 0.4369346844839369}, 'global_precision_difference': {'lower_95': -0.015692050919415584, 'mean': -0.009894240876615609, 'upper_95': -0.004096430833815631}, 'recovery_rate': 1.0, 'regulation_only_root_log_bf_max': 0.0}
- `3_switching`: **PASS** — {'post_switch_recovery': 0.8835265221700349, 'post_switch_slice_count': 23207, 'pre_switch_history_query_error': 0.0, 'switch_onset_absolute_error_descriptive': {'blocking': False, 'count': 487, 'maximum': 60.0, 'mean': 18.59958932238193, 'median': 15.0, 'p95': 51.69999999999999}, 'switching_world_count': 487}
- `4_factorial`: **PASS** — {'cell_counts': {'reg_0_root_0': 125, 'reg_0_root_1': 125, 'reg_1_root_0': 125, 'reg_1_root_1': 125}, 'no_root_movement_max': 0.0, 'regulation_global_precision_main_effect': {'lower_95': 0.409491604021216, 'mean': 0.41958224989777265, 'upper_95': 0.4296728957743293}, 'root_uptake_interaction': {'lower_95': 0.18163232553728778, 'mean': 0.18779950149220678, 'upper_95': 0.19396667744712578}}
- `5_semantic_custody`: **PASS** — {'ascending_gap_free': True, 'freeze_identity': {'file_count': 35, 'manifest': 'results/V2.6a/freeze-manifest.json', 'manifest_sha256': '713662bbdf729d0ad62b8236c4015ef50d72acbc12f2a9c57f8ffc81d3a555a8', 'mismatches': [], 'passed': True}, 'one_posterior_all_worlds': True, 'permanent_constitution': True, 'raw_hashes_match_seal': True, 'release_ledger': {'file': 'projects/ifs-paper/suite-v2-sealed-hashes.md', 'release_phrase_found': True, 'sha256': '900a9e9ed6013e3344456498d8194a82b526541d928c392b26d0833367b7da5b'}, 'seed_count': 2000}

## Verdict classes

- Scientific: PASS
- Semantic: PASS
- Custody: PASS

The switch-onset errors in cell 3 are descriptive only, exactly as sealed and adjudicated.
