# V2.3.4 gate 1

Verdict: **PASS**.

- `01_masked_BF_one`: PASS — {'maximum_error': 1.1102230246251565e-16, 'passed': True}
- `02_eta_zero_equals_irrelevant`: PASS — {'maximum_error': 0.0, 'passed': True}
- `03_full_efficacy_safety_not_danger_evidence`: PASS — {'likelihood_range_over_theta': 0.0, 'passed': True}
- `04_engagement_safety_disconfirms_danger`: PASS — {'before': 0.5, 'after': 0.3464, 'passed': True}
- `05_action_no_direct_update`: PASS — {'maximum_error': 1.1102230246251565e-16, 'action_selection_likelihood': False, 'passed': True}
- `06_relief_policy_only`: PASS — {'scientific_posterior_error': 1.734723475976807e-18, 'policy_probability': 0.6666666666666666, 'passed': True}
- `07_exact_spike`: PASS — {'spike_mass': 0.35, 'eta_value': 0.0, 'passed': True}
- `08_pure_avoidance_confounding`: PASS — {'theta_eta_correlation': [0.0010844320569899006, 0.024565440127948143], 'passed': True}
- `09_forced_probe_reduces_confounding`: PASS — {'absolute_correlation_reduction': 0.0010175302845428485, 'passed': True}
- `10_independent_enumeration`: PASS — {'maximum_error': 0.0, 'prior_input_unchanged': True, 'oracle_evidence': 0.186587969924812, 'passed': True}

## Prospective Gate-2 attainability screen

`{'metrics': {'public_seed_block': [1299000, 1299399], 'identifiable_worlds': 200, 'H_E_accuracy': 0.995, 'context_eta_accuracy': 0.89, 'eta_MAE': 0.03774022175673383, 'danger_MAE': 0.007732976180177327, 'probe_median_absolute_correlation_reduction': 0.6748286924293272}, 'floor_screen': {'H_E_accuracy': True, 'context_eta_accuracy': True, 'eta_MAE': True, 'danger_MAE': True, 'probe_correlation_reduction': True}, 'suspected_unattainable_floor': [], 'criterion_status': 'public-dummy descriptive only'}`
