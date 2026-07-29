# V2.6b gate 1

Verdict: **PASS**.

- `01_trust_forecasts_separate`: **PASS** — `{"names": ["T_outcome", "T_coprotection", "T_partner"], "posterior_shapes": [[2], [2], [2]]}`
- `02_stakes_policy_only`: **PASS** — `{"permission_difference": 0.5441682413899271, "trust_inputs_identical": true}`
- `03_efficacy_forecast_only`: **PASS** — `{"role_risk_high_efficacy": 0.0, "role_risk_low_efficacy": 0.7}`
- `04_permission_pure_readout`: **PASS** — `{"forbidden_present": [], "scientific_keys": ["G", "T_coprotection", "T_outcome", "T_partner", "attribution_theta_eta", "partner_L", "policy_outcome", "protector_forecasts", "protector_policy"]}`
- `05_no_gate_object`: **PASS** — `{"gate_class_present": false}`
- `06_contact_policy_consequence`: **PASS** — `{"identity_error": 0.0}`
- `07_policy_normalizes`: **PASS** — `{"error": 0.0, "minimum_mass": 0.023300030612753424}`
- `08_expected_cost_softmax_parity`: **PASS** — `{"maximum_error": 0.0}`
- `09_same_trust_different_stakes`: **PASS** — `{"permission_high": 0.00433610148911825, "permission_low": 0.5485043428790454}`
- `10_same_stakes_different_trust`: **PASS** — `{"permission_high_trust": 0.19363065980177396, "permission_low_trust": 0.0021172060795845073}`
- `11_refusal_alone_uninformative`: **PASS** — `{"partner_posterior_error": 0.0}`
- `12_future_hope_equal`: **PASS** — `{"absent": 0.2, "error": 0.0, "preserving": 0.2}`
- `13_independent_oracle`: **PASS** — `{"maximum_error": 0.0}`
- `14_oracle_input_copy`: **PASS** — `{}`
- `15_one_posterior`: **PASS** — `{}`
- `16_model_evidence_constitution`: **PASS** — `{"constitution_passed": true}`
- `17_graded_update_constitution`: **PASS** — `{"constitution_passed": true}`
- `18_bounds_and_custody`: **PASS** — `{"action_selection_likelihood": false, "bounds": {"B_max_v232_formation": 3.801426508560692, "B_max_v234": 11.675460894331877, "B_max_v24_common_emissions": 6.704414354964107, "B_max_v25a_configural": 6.084736253211209, "B_max_v25a_marginal_accounting": 6.704414354964107, "B_max_v25b": 11.302393144606405, "B_max_v26a_relational": 6.9920964274158885, "B_max_v26a_root": 2.9444389791664394, "B_max_v26b_policy_outcome": 1.3862943611198908, "B_max_v26b_trust": 2.1972245773362196, "implied_binary_change_bound_v26b": 0.5}, "released_seed": 1389901}`
