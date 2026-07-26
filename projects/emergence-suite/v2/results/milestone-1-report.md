# Suite v2 milestone 1 report

Generated from real Python reference runs. Gate 6 remains evaluator-sealed and unrun.

## V2.0

- gate_1_semantic: PASS
- gate_2_recovery: PASS
- gate_3_comparison: PASS
- gate_4_batch_mutation: PASS
- gate_5_one_posterior: PASS
- Maximum semantic parity error: 0
- State recovery accuracy / Brier / ECE: 0.848 / 0.129 / 0.005
- Parameter MAE / 95% coverage: 0.021 / 1.000
- Freeze candidate: `results/V2.0/freeze-manifest.json`
- Decision log: `results/V2.0/decisions.md`

## V2.1

- gate_1_semantic: PASS
- gate_2_recovery: PASS
- gate_3_composition: PASS
- gate_4_selective_lesion: PASS
- gate_5_cumulative_regression: PASS
- Likelihood sharpening effect: 0.329
- Broadcast depth on/off/effect: 0.730 / 0.333 / 0.397
- Cross-latent delivered log-odds effect: 0.902
- Batch mean depth effect (95% interval): 0.331 (0.282, 0.377)
- Freeze candidate: `results/V2.1/freeze-manifest.json`
- Decision log: `results/V2.1/decisions.md`

## V2.2

- gate_1_structure_recovery: PASS
- gate_2_parameter_recovery: PASS
- gate_3_precision_root_transfer: PASS
- gate_4_selective_lesions: PASS
- gate_5_cumulative_regression: PASS
- Structure recovery accuracy / mean true probability: 0.969 / 0.932
- Association recovery MAE / 95% coverage: 0.023 / 0.953
- Root uptake broad / broadcast-off / narrowed: 0.242 / 0.128 / 0.041
- Transfer broad / broadcast-off / narrowed: 0.194 / 0.102 / 0.033
- 2x2 association / similarity effects: 0.193 / 0.000
- Fixed-G direct transfer: 0
- Freeze candidate: `results/V2.2/freeze-manifest.json`
- Decision log: `results/V2.2/decisions.md`

## Regressions and stop status

All inherited gates survived in the final V2.2 strain. No failed gate blocked the ratchet. No formation, reduction, partner, or protector mechanisms were added. Work stops at the three freeze candidates; evaluator verification, commits, and sealed challenges remain external.
