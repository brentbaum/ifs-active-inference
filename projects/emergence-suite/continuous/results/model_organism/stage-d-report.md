# Experiment 50-L lesions and robustness

The reference organism remained fixed at `274f8888f71ac590d7c15d6f9f59777ea919e182`. The preregistration was hash-locked before Stage D execution. **Ordering deviation:** 50-P had already been inspected; every lesion prediction here targets only the previously known 50-H signatures and no 50-P result.

## Lesion scorecard

| Lesion | Predicted disappear | Observed disappear | Prediction-hit rate | 95% interval |
|---|---|---|---:|---|
| context_split_unavailable | S4;S6 | S4 | 0.9000 | [0.5958, 0.9821] |
| field_scalar | S3;S5 | S3;S4;S5 | 0.9000 | [0.5958, 0.9821] |
| registration_removed | S8 | S4;S8 | 0.9000 | [0.5958, 0.9821] |
| partner_model_collapsed | S10;S9 | S10;S4;S9 | 0.9000 | [0.5958, 0.9821] |
| dyad_protector_severed | S10 | S10;S4 | 0.9000 | [0.5958, 0.9821] |
| freeze_ordinary_learning | S1 | S1;S4 | 0.9000 | [0.5958, 0.9821] |
| trust_single_forecast | S9 | S4 | 0.8000 | [0.4902, 0.9433] |

### Signature-level predictions and misses

| Lesion | Signature | Prediction | Metric | 95% interval | Compound rate (95% interval) | Observed | Hit |
|---|---|---|---:|---|---|---|---|
| context_split_unavailable | S1 | survive | 1.0000 | [0.8668, 1.0000] | NA | survived | **HIT** |
| context_split_unavailable | S2 | survive | 0.4392 | [0.0107, 0.8732] | NA | survived | **HIT** |
| context_split_unavailable | S3 | survive | 1.0000 | [0.9842, 1.0000] | NA | survived | **HIT** |
| context_split_unavailable | S4 | disappear | -0.1996 | [-0.1996, -0.1996] | 0.0000 ([0.0000, 0.7935]) | disappeared | **HIT** |
| context_split_unavailable | S5 | survive | 0.4431 | [0.3632, 0.5230] | NA | survived | **HIT** |
| context_split_unavailable | S6 | disappear | 0.7900 | [0.7404, 0.8323] | NA | survived | **MISS** |
| context_split_unavailable | S7 | survive | 0.1458 | [0.1118, 0.1799] | NA | survived | **HIT** |
| context_split_unavailable | S8 | survive | 0.3344 | [0.3344, 0.3344] | NA | survived | **HIT** |
| context_split_unavailable | S9 | survive | 0.7056 | [0.6352, 0.7673] | NA | survived | **HIT** |
| context_split_unavailable | S10 | survive | 1.0000 | [1.0000, 1.0000] | NA | survived | **HIT** |
| field_scalar | S1 | survive | 1.0000 | [0.8668, 1.0000] | NA | survived | **HIT** |
| field_scalar | S2 | survive | 0.4392 | [0.0107, 0.8732] | NA | survived | **HIT** |
| field_scalar | S3 | disappear | 0.7500 | [0.6916, 0.8006] | NA | disappeared | **HIT** |
| field_scalar | S4 | survive | 0.3166 | [0.2443, 0.3888] | 0.7917 ([0.5953, 0.9076]) | disappeared | **MISS** |
| field_scalar | S5 | disappear | -0.0096 | [-0.0151, -0.0041] | NA | disappeared | **HIT** |
| field_scalar | S6 | survive | 0.9900 | [0.9710, 0.9966] | NA | survived | **HIT** |
| field_scalar | S7 | survive | 0.1458 | [0.1118, 0.1799] | NA | survived | **HIT** |
| field_scalar | S8 | survive | 0.3344 | [0.3344, 0.3344] | NA | survived | **HIT** |
| field_scalar | S9 | survive | 0.7056 | [0.6352, 0.7673] | NA | survived | **HIT** |
| field_scalar | S10 | survive | 1.0000 | [1.0000, 1.0000] | NA | survived | **HIT** |
| registration_removed | S1 | survive | 1.0000 | [0.8668, 1.0000] | NA | survived | **HIT** |
| registration_removed | S2 | survive | 0.4392 | [0.0107, 0.8732] | NA | survived | **HIT** |
| registration_removed | S3 | survive | 1.0000 | [0.9842, 1.0000] | NA | survived | **HIT** |
| registration_removed | S4 | survive | 0.3166 | [0.2443, 0.3888] | 0.7917 ([0.5953, 0.9076]) | disappeared | **MISS** |
| registration_removed | S5 | survive | 0.4431 | [0.3632, 0.5230] | NA | survived | **HIT** |
| registration_removed | S6 | survive | 0.9900 | [0.9710, 0.9966] | NA | survived | **HIT** |
| registration_removed | S7 | survive | 0.1458 | [0.1118, 0.1799] | NA | survived | **HIT** |
| registration_removed | S8 | disappear | 0.0000 | [0.0000, 0.0000] | NA | disappeared | **HIT** |
| registration_removed | S9 | survive | 0.7056 | [0.6352, 0.7673] | NA | survived | **HIT** |
| registration_removed | S10 | survive | 1.0000 | [1.0000, 1.0000] | NA | survived | **HIT** |
| partner_model_collapsed | S1 | survive | 1.0000 | [0.8668, 1.0000] | NA | survived | **HIT** |
| partner_model_collapsed | S2 | survive | 0.4392 | [0.0107, 0.8732] | NA | survived | **HIT** |
| partner_model_collapsed | S3 | survive | 1.0000 | [0.9842, 1.0000] | NA | survived | **HIT** |
| partner_model_collapsed | S4 | survive | 0.3166 | [0.2443, 0.3888] | 0.7917 ([0.5953, 0.9076]) | disappeared | **MISS** |
| partner_model_collapsed | S5 | survive | 0.4431 | [0.3632, 0.5230] | NA | survived | **HIT** |
| partner_model_collapsed | S6 | survive | 0.9900 | [0.9710, 0.9966] | NA | survived | **HIT** |
| partner_model_collapsed | S7 | survive | 0.1458 | [0.1118, 0.1799] | NA | survived | **HIT** |
| partner_model_collapsed | S8 | survive | 0.3344 | [0.3344, 0.3344] | NA | survived | **HIT** |
| partner_model_collapsed | S9 | disappear | 0.1500 | [0.1052, 0.2094] | NA | disappeared | **HIT** |
| partner_model_collapsed | S10 | disappear | -0.0167 | [-0.1676, 0.1342] | NA | disappeared | **HIT** |
| dyad_protector_severed | S1 | survive | 1.0000 | [0.8668, 1.0000] | NA | survived | **HIT** |
| dyad_protector_severed | S2 | survive | 0.4392 | [0.0107, 0.8732] | NA | survived | **HIT** |
| dyad_protector_severed | S3 | survive | 1.0000 | [0.9842, 1.0000] | NA | survived | **HIT** |
| dyad_protector_severed | S4 | survive | 0.3166 | [0.2443, 0.3888] | 0.7917 ([0.5953, 0.9076]) | disappeared | **MISS** |
| dyad_protector_severed | S5 | survive | 0.4431 | [0.3632, 0.5230] | NA | survived | **HIT** |
| dyad_protector_severed | S6 | survive | 0.9900 | [0.9710, 0.9966] | NA | survived | **HIT** |
| dyad_protector_severed | S7 | survive | 0.1458 | [0.1118, 0.1799] | NA | survived | **HIT** |
| dyad_protector_severed | S8 | survive | 0.3344 | [0.3344, 0.3344] | NA | survived | **HIT** |
| dyad_protector_severed | S9 | survive | 0.7056 | [0.6352, 0.7673] | NA | survived | **HIT** |
| dyad_protector_severed | S10 | disappear | 0.0000 | [0.0000, 0.0000] | NA | disappeared | **HIT** |
| freeze_ordinary_learning | S1 | disappear | 0.6400 | [0.4452, 0.7975] | NA | disappeared | **HIT** |
| freeze_ordinary_learning | S2 | survive | 0.4392 | [0.0107, 0.8732] | NA | survived | **HIT** |
| freeze_ordinary_learning | S3 | survive | 1.0000 | [0.9842, 1.0000] | NA | survived | **HIT** |
| freeze_ordinary_learning | S4 | survive | 0.3166 | [0.2443, 0.3888] | 0.7917 ([0.5953, 0.9076]) | disappeared | **MISS** |
| freeze_ordinary_learning | S5 | survive | 0.4431 | [0.3632, 0.5230] | NA | survived | **HIT** |
| freeze_ordinary_learning | S6 | survive | 0.9900 | [0.9710, 0.9966] | NA | survived | **HIT** |
| freeze_ordinary_learning | S7 | survive | 0.1458 | [0.1118, 0.1799] | NA | survived | **HIT** |
| freeze_ordinary_learning | S8 | survive | 0.3344 | [0.3344, 0.3344] | NA | survived | **HIT** |
| freeze_ordinary_learning | S9 | survive | 0.7056 | [0.6352, 0.7673] | NA | survived | **HIT** |
| freeze_ordinary_learning | S10 | survive | 1.0000 | [1.0000, 1.0000] | NA | survived | **HIT** |
| trust_single_forecast | S1 | survive | 1.0000 | [0.8668, 1.0000] | NA | survived | **HIT** |
| trust_single_forecast | S2 | survive | 0.4392 | [0.0107, 0.8732] | NA | survived | **HIT** |
| trust_single_forecast | S3 | survive | 1.0000 | [0.9842, 1.0000] | NA | survived | **HIT** |
| trust_single_forecast | S4 | survive | 0.3166 | [0.2443, 0.3888] | 0.7917 ([0.5953, 0.9076]) | disappeared | **MISS** |
| trust_single_forecast | S5 | survive | 0.4431 | [0.3632, 0.5230] | NA | survived | **HIT** |
| trust_single_forecast | S6 | survive | 0.9900 | [0.9710, 0.9966] | NA | survived | **HIT** |
| trust_single_forecast | S7 | survive | 0.1458 | [0.1118, 0.1799] | NA | survived | **HIT** |
| trust_single_forecast | S8 | survive | 0.3344 | [0.3344, 0.3344] | NA | survived | **HIT** |
| trust_single_forecast | S9 | disappear | 0.7667 | [0.6997, 0.8225] | NA | survived | **MISS** |
| trust_single_forecast | S10 | survive | 1.0000 | [1.0000, 1.0000] | NA | survived | **HIT** |

The unlesioned L-block reference itself did not satisfy compound S4: its mean transfer was `0.3166`, but its qualifying-world rate was `0.7917`, below the frozen `0.80`. Consequently, every predicted-survive S4 cell is retained as a miss; those misses cannot localize a lesion effect.

## Sensitivity matrix

- Classification: **block-diagonal**
- Resolvable shared constants: `41/42`
- Constants materially affecting at least two signatures: `4` (`0.0976`)
- Cross-cluster material constants: `4`
- Paired-noncausal constants reported unresolved: `rng_history_offset`
- For compound S4, materiality uses the larger absolute fractional change across conditional mean and qualifying-world rate; both components are published in the matrix.

Material multi-signature constants:

| Constant | Affected signatures | Crosses clusters |
|---|---|---|
| bayes_reliability | S2;S5 | true |
| history_learning_rate | S2;S5 | true |
| root_evidence_weight | S2;S5 | true |
| training_events | S2;S5 | true |
- Full matrix: `lesions/sensitivity-matrix.csv`.

## Joint neighborhood

- Reference classification: **central**
- Joint survival volume: `1.0000`, 95% interval `[0.9542, 1.0000]`.
- Signatures with survival volume at least `0.60`: `10/10`.

| Signature | Survival volume | 95% interval |
|---|---:|---|
| S1 | 1.0000 | [0.9542, 1.0000] |
| S2 | 1.0000 | [0.9542, 1.0000] |
| S3 | 1.0000 | [0.9542, 1.0000] |
| S4 | 0.9875 | [0.9325, 0.9978] |
| S5 | 1.0000 | [0.9542, 1.0000] |
| S6 | 1.0000 | [0.9542, 1.0000] |
| S7 | 1.0000 | [0.9542, 1.0000] |
| S8 | 1.0000 | [0.9542, 1.0000] |
| S9 | 0.8250 | [0.7274, 0.8928] |
| S10 | 1.0000 | [0.9542, 1.0000] |

All misses, non-finite failures, and narrow survival volumes are retained. No 50-P outcome was used in prediction or scoring.
