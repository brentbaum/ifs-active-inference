# Population-A calibration-null decomposition

This analysis is read-only over the retained 2,000-world trace. No world seed was generated or rescored.

## Parametric nulls

| statistic | observed | null mean | q95 | q99 | percentile | beyond q99 |
|---|---:|---:|---:|---:|---:|:---:|
| active_count_top_label_ece | 0.084501 | 0.018032 | 0.029692 | 0.036113 | 1.0000 | True |
| active_count_macro_classwise_ece | 0.097328 | 0.016844 | 0.023585 | 0.027102 | 1.0000 | True |
| JOINT_POLICY_Y_binary_edge_ece | 0.051338 | 0.017544 | 0.024935 | 0.028236 | 1.0000 | True |

The five target ECEs, equivalence-class top-label ECE, and 50/80/90/95% class coverage are reported as passing controls in the JSON record.

## Theorem premise

The pre-block complete-native fixture proof passed: production sum `0.9999999999999999`, oracle sum `0.9999999999999999`, public module-predictive error `0.0`. Its scope is the enumerable factorized dummy, not every complete 64-slice path. The active-count posterior sum error is `1.3766765505351941e-14` and its maximum mismatch from a fresh marginalization of the serialized protect posterior is `0.0`.

## Localization

Observed statistics beyond their null q99: active_count_top_label_ece, active_count_macro_classwise_ece, JOINT_POLICY_Y_binary_edge_ece. Bin-level signed gaps, truth-class decomposition, and the active-count/JOINT_POLICY_Y residual correlation are recorded in the JSON.

The active-count miss is nonmonotone across confidence bins. `JOINT_POLICY_Y` is predominantly overpredicted below posterior 0.7. Their signed residual correlation is `-0.0505`, so the two structural misses are not concentrated in the same worlds.

Passing controls beyond their null q99: identity, coverage_0.95. Identity is mainly underconfident; 95% class coverage is overcoverage.

## Token-mass caveat

Target calibration is world-weighted. Each world has total weight 1/2000, split across its delivered tokens, so large raw token bins do not receive proportional world weight. Full occupancy tables are in the JSON.
