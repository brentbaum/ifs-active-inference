# C-V234-B sealed verdict

Immutable sealed verdict: **PASS**.

Pass requires all seven sealed-B criteria. The sealed pilot-corrected floors
were used exactly: cell-2 no-false attribution `>=0.80` and cell-3 existence
recovery `>=0.45`. No threshold was changed after reveal; all other
directions, reference constructions, and scientific fields remained verbatim.

## Criteria

- `1_effective_action`: **PASS** — `{"danger_vs_low_danger": {"count": 333, "lower_95": 0.15543879611957215, "mean": 0.16130914348521216, "upper_95": 0.16717949085085218}, "efficacy_existence_unique_rate": 1.0, "prevented_outcome_recombination_error_max": 0.0}`
- `2_sham_action`: **PASS** — `{"known_irrelevant_action_free_identity_error_max": 0.0, "no_false_attribution_rate": 0.8738738738738738}`
- `3_partial_efficacy`: **PASS** — `{"cell_1_eta_mean": {"count": 333, "lower_95": 0.7437860079731902, "mean": 0.7534834979982517, "upper_95": 0.7631809880233131}, "cell_2_eta_mean": {"count": 333, "lower_95": 0.13642556354614144, "mean": 0.14554229988729214, "upper_95": 0.15465903622844285}, "cell_3_eta_mean": {"count": 333, "lower_95": 0.26800385603087584, "mean": 0.27934046506664084, "upper_95": 0.29067707410240584}, "efficacy_existence_recovery_rate": 0.5555555555555556, "full_above_partial": {"left_count": 333, "lower_95": 0.45922458739543126, "mean_difference": 0.4741430329316108, "right_count": 333, "upper_95": 0.48906147846779036}, "partial_above_sham": {"left_count": 333, "lower_95": 0.1192505335527283, "mean_difference": 0.1337981651793487, "right_count": 333, "upper_95": 0.1483457968059691}}`
- `4_context_switch`: **PASS** — `{"pre_minus_post_context_efficacy": {"count": 333, "lower_95": 0.7633144134135897, "mean": 0.7743669433036906, "upper_95": 0.7854194731937915}, "pre_switch_attribution_query_error_max": 0.0}`
- `5_forced_probe`: **PASS** — `{"joint_theta_eta_entropy_reduction": {"count": 333, "lower_95": 1.7507660826191662, "mean": 1.7819623340234476, "upper_95": 1.813158585427729}}`
- `6_relief_only`: **PASS** — `{"danger_movement_max": 0.0, "efficacy_existence_movement_max": 1.1102230246251565e-16, "efficacy_magnitude_movement_max": 5.551115123125783e-17, "scientific_posterior_movement_max": 5.204170427930421e-17}`
- `7_semantic_custody`: **PASS** — `{"ascending_gap_free": true, "freeze_identity": {"file_count": 31, "manifest": "results/V2.3.4/freeze-manifest.json", "manifest_sha256": "c4f27d14be5edbcfcf9cbfc3522001544d5daec002cb53c4a34ad71d527ce70a", "mismatches": [], "passed": true}, "one_posterior_all_worlds": true, "permanent_constitution": true, "raw_hashes_match_seal": true, "release_ledger": {"file": "projects/ifs-paper/suite-v2-sealed-hashes.md", "release_phrase_found": true, "sha256": "41cb3bd13dc9a985f9ade43ca40ccdf8649a2aef3a801061e71c1b9c5640cb64"}, "seed_count": 2000}`

## Verdict classes

- Scientific: **PASS**
- Semantic: **PASS**
- Custody: **PASS**

The base stage entered Gate 6 with a clean all-gates-1–5 freeze.
Escrow was consumed once, ascending and gap-free, after evaluator release.
