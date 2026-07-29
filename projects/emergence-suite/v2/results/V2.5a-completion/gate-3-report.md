# V2.5a completion Gate 3

**Verdict: PASS**

- 1_coupled_support: `PASS`
- 2_independent_false_selection: `PASS`
- 2_independent_log_bf: `PASS`
- 2_marginal_no_unique_coupled: `PASS`
- 3_heldout_prediction: `PASS`
- 4_shuffled_false_selection: `PASS`
- 5_root_effect_resolved: `PASS`
- 5_transfer_effect_resolved: `PASS`
- 6_interaction_lesion: `PASS`
- 7_context_composition: `PASS`
- atomic_budget_identity: `PASS`
- lattice_aware_matching: `PASS`

```json
{
  "context_fixed_G_maximum_transfer": 0.0,
  "context_mediation_maximum_error": 0.0,
  "coupled_support_difference": {
    "lower_95": 0.4871795515894843,
    "mean": 0.49389301824309506,
    "upper_95": 0.5006064848967058
  },
  "heldout_advantage_nats_per_atomic_token": {
    "lower_95": 0.04991536227109486,
    "mean": 0.052929606290173646,
    "upper_95": 0.05594385030925243
  },
  "independent_false_coupled": 0.005,
  "independent_log_bf": {
    "lower_95": 12.951701976286564,
    "mean": 13.318455773836996,
    "upper_95": 13.685209571387428
  },
  "interaction_lesion_maximum_checkpoint_difference": 0.0,
  "interaction_lesion_maximum_scientific_difference": 0.0,
  "marginal_unique_coupled_rate": 0.0,
  "matching_censoring_rate": 0.0,
  "matching_maximum_absolute_error": 0.0,
  "matching_oracle_identity_rate": 1.0,
  "maximum_atomic_budget_error": 0.0,
  "root_format_effect": {
    "lower_95": 0.49389089227946376,
    "mean": 0.49717487970725527,
    "resolution": "positive",
    "rope": [
      -0.01,
      0.01
    ],
    "upper_95": 0.5004588671350468
  },
  "shuffled_false_coupled": 0.0025,
  "transfer_format_effect": {
    "lower_95": 0.39511271382357105,
    "mean": 0.39773990376580426,
    "resolution": "positive",
    "rope": [
      -0.01,
      0.01
    ],
    "upper_95": 0.40036709370803747
  }
}
```
