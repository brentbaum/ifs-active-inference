# C-V234 sealed verdict

Immutable sealed verdict: **FAIL**.

Pass requires all seven sealed criteria. No threshold, direction, reference construction, or scientific field was changed.

## Criteria

- `1_effective_action`: **PASS** — `{"danger_vs_low_danger": {"count": 333, "lower_95": 0.15459811722376265, "mean": 0.1603424419718195, "upper_95": 0.16608676671987632}, "efficacy_existence_unique_rate": 1.0, "prevented_outcome_recombination_error_max": 0.0}`
- `2_sham_action`: **FAIL** — `{"known_irrelevant_action_free_identity_error_max": 0.0, "no_false_attribution_rate": 0.8498498498498499}`
- `3_partial_efficacy`: **FAIL** — `{"cell_1_eta_mean": {"count": 333, "lower_95": 0.7377502059041943, "mean": 0.748211546412962, "upper_95": 0.7586728869217296}, "cell_2_eta_mean": {"count": 333, "lower_95": 0.13756981912372035, "mean": 0.14757734695325403, "upper_95": 0.1575848747827877}, "cell_3_eta_mean": {"count": 333, "lower_95": 0.2632272916540757, "mean": 0.27422575043553193, "upper_95": 0.28522420921698816}, "efficacy_existence_recovery_rate": 0.5495495495495496, "full_above_partial": {"left_count": 333, "lower_95": 0.45880667410533954, "mean_difference": 0.47398579597743, "right_count": 333, "upper_95": 0.4891649178495205}, "partial_above_sham": {"left_count": 333, "lower_95": 0.11177840991044732, "mean_difference": 0.1266484034822779, "right_count": 333, "upper_95": 0.14151839705410849}}`
- `4_context_switch`: **PASS** — `{"pre_minus_post_context_efficacy": {"count": 333, "lower_95": 0.7585588362836347, "mean": 0.769598230071003, "upper_95": 0.7806376238583713}, "pre_switch_attribution_query_error_max": 0.0}`
- `5_forced_probe`: **PASS** — `{"joint_theta_eta_entropy_reduction": {"count": 333, "lower_95": 1.7489127186699243, "mean": 1.7806427154256648, "upper_95": 1.8123727121814053}}`
- `6_relief_only`: **PASS** — `{"danger_movement_max": 0.0, "efficacy_existence_movement_max": 1.1102230246251565e-16, "efficacy_magnitude_movement_max": 5.551115123125783e-17, "scientific_posterior_movement_max": 5.204170427930421e-17}`
- `7_semantic_custody`: **PASS** — `{"ascending_gap_free": true, "freeze_identity": {"file_count": 31, "manifest": "results/V2.3.4/freeze-manifest.json", "manifest_sha256": "c4f27d14be5edbcfcf9cbfc3522001544d5daec002cb53c4a34ad71d527ce70a", "mismatches": [], "passed": true}, "one_posterior_all_worlds": true, "permanent_constitution": true, "raw_hashes_match_seal": true, "release_ledger": {"file": "projects/ifs-paper/suite-v2-sealed-hashes.md", "release_phrase_found": true, "sha256": "1b2dbddaa1f72ae467c84097176b6b4c4a46fd5fe1f2ed89abae0825a1bf1a3d"}, "seed_count": 2000}`

## Verdict classes

- Scientific: **FAIL**
- Semantic: **PASS**
- Custody: **PASS**

## Pre-committed failure localization

- Cell 2 missed only the false-attribution ceiling: the no-false-attribution
  rate was `0.8498498498498499` against `>=0.90`. The known-irrelevant
  action-free danger identity remained exact at `0.0`. Per the sealed
  interpretation, this is the protector-relevant false-attribution failure
  class.
- Cell 3 preserved both efficacy-magnitude orderings with strictly positive
  lower 95% bounds (`0.45880667410533954` for full above partial and
  `0.11177840991044732` for partial above sham), but efficacy-existence
  recovery was `0.5495495495495496` against `>=0.60`. This localizes to
  efficacy-existence inference rather than magnitude ordering.
- Context composition, forced-probe epistemics, relief neutrality, semantic
  integrity, and custody all passed. In particular, relief-induced scientific
  posterior movement was at most `5.204170427930421e-17`.

The base stage entered Gate 6 with a clean all-gates-1–5 freeze.
Escrow was consumed once, ascending and gap-free, after evaluator release.
