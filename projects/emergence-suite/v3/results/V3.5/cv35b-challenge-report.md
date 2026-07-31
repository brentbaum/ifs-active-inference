# C-V35B sealed challenge report

## Immutable sealed verdict

Overall: **PASS**.

- Criterion 1 — befriending_and_targeted_support: **PASS**.
- Criterion 2 — partner_and_stakes: **PASS**.
- Criterion 3 — outcome_bearing_policy_histories: **PASS**.
- Criterion 4 — denied_contact: **PASS**.
- Criterion 5 — interventional_topology_and_exact_dormancy: **PASS**.
- Criterion 6 — registration_candidate_common_null: **PASS**.
- Criterion 7 — recovery_semantics_and_custody: **PASS**.

The verdict above was written only after the per-seed trace and
statistics JSONL had been closed, hashed record-by-record, and sealed
in `cv35b-challenge-raw-seal.json`. It is retained as written.

## Verdict classes

- Scientific: **PASS**.
- Semantic: **PASS**.
- Custody: **PASS**.

## Complete sealed statistics

```json
{
  "criteria": [
    {
      "criterion": 1,
      "metrics": {
        "cell1_access": {
          "bootstrap_replicates": 5000,
          "ci95": [
            0.061507947339860786,
            0.06271877291463682
          ],
          "ci_carries_positive_sign": true,
          "floor": 0.030808420228944897,
          "mean": 0.06210523229131487,
          "mean_meets_floor": true,
          "n": 500,
          "passed": true
        },
        "cell1_support_response_3": {
          "bootstrap_replicates": 5000,
          "ci95": [
            0.5000000000864259,
            0.5000000196760273
          ],
          "ci_carries_positive_sign": true,
          "floor": 0.25002964669658534,
          "mean": 0.5000000066765437,
          "mean_meets_floor": true,
          "n": 500,
          "passed": true
        },
        "cell4_access": {
          "bootstrap_replicates": 5000,
          "ci95": [
            0.06134084655855657,
            0.06257225302531619
          ],
          "ci_carries_positive_sign": true,
          "floor": 0.031786343743120116,
          "mean": 0.0619641503900494,
          "mean_meets_floor": true,
          "n": 400,
          "passed": true
        },
        "cell4_support_response_3": {
          "bootstrap_replicates": 5000,
          "ci95": [
            0.5000000045944101,
            0.5000001806167893
          ],
          "ci_carries_positive_sign": true,
          "floor": 0.2500000001761959,
          "mean": 0.5000000725959193,
          "mean_meets_floor": true,
          "n": 400,
          "passed": true
        }
      },
      "name": "befriending_and_targeted_support",
      "passed": true
    },
    {
      "criterion": 2,
      "metrics": {
        "cell2_access": {
          "bootstrap_replicates": 5000,
          "ci95": [
            0.11483187852615984,
            0.11735404922658574
          ],
          "ci_carries_positive_sign": true,
          "floor": 0.0575741252904589,
          "mean": 0.11608728935193695,
          "mean_meets_floor": true,
          "n": 500,
          "passed": true
        },
        "cell2_trust_remaining": {
          "bootstrap_replicates": 5000,
          "ci95": [
            0.9999999999999934,
            0.9999999999999992
          ],
          "ci_carries_positive_sign": true,
          "floor": 0.4999999999999974,
          "mean": 0.9999999999999962,
          "mean_meets_floor": true,
          "n": 500,
          "passed": true
        },
        "cell3_access_low_minus_high": {
          "bootstrap_replicates": 5000,
          "ci95": [
            0.10677838405383702,
            0.10902124488160798
          ],
          "ci_carries_positive_sign": true,
          "floor": 0.05456176795537784,
          "mean": 0.10789374075749018,
          "mean_meets_floor": true,
          "n": 500,
          "passed": true
        },
        "cell3_scientific_posterior_identity_error_max": {
          "passed": true,
          "tolerance": 1e-10,
          "value": 0.0
        }
      },
      "name": "partner_and_stakes",
      "passed": true
    },
    {
      "criterion": 3,
      "metrics": {
        "cell6_exclusion": {
          "bootstrap_replicates": 5000,
          "ci95": [
            0.42235680480007215,
            0.4999733303642649
          ],
          "ci_carries_positive_sign": true,
          "floor": 0.22369120540497045,
          "mean": 0.46251075170042555,
          "mean_meets_floor": true,
          "n": 200,
          "passed": true
        },
        "cell7_monitoring": {
          "bootstrap_replicates": 5000,
          "ci95": [
            0.04328451708957188,
            0.06754686248493422
          ],
          "ci_carries_positive_sign": true,
          "floor": 0.028590899494582652,
          "mean": 0.05534417413919042,
          "mean_meets_floor": true,
          "n": 500,
          "passed": true
        },
        "cell8_engagement": {
          "bootstrap_replicates": 5000,
          "ci95": [
            0.5447721279492176,
            0.5889486452678624
          ],
          "ci_carries_positive_sign": true,
          "floor": 0.2818778047497165,
          "mean": 0.5675686994212118,
          "mean_meets_floor": true,
          "n": 200,
          "passed": true
        }
      },
      "name": "outcome_bearing_policy_histories",
      "passed": true
    },
    {
      "criterion": 4,
      "metrics": {
        "cell5_access": {
          "bootstrap_replicates": 5000,
          "ci95": [
            0.02110865711089148,
            0.022411094629507414
          ],
          "ci_carries_positive_sign": true,
          "floor": 0.011022406848183891,
          "mean": 0.021799265675044817,
          "mean_meets_floor": true,
          "n": 400,
          "passed": true
        },
        "cell5_contact_response_3": {
          "bootstrap_replicates": 5000,
          "ci95": [
            0.4521327021286752,
            0.47823991634830015
          ],
          "ci_carries_positive_sign": true,
          "floor": 0.23462657827078734,
          "mean": 0.46593362825285595,
          "mean_meets_floor": true,
          "n": 400,
          "passed": true
        }
      },
      "name": "denied_contact",
      "passed": true
    },
    {
      "criterion": 5,
      "metrics": {
        "cell10_allied_D_0_1": {
          "bootstrap_replicates": 5000,
          "ci95": [
            0.006517020519016007,
            0.010131940942683377
          ],
          "ci_carries_positive_sign": true,
          "floor": 0.004841000047368376,
          "mean": 0.008339919491799751,
          "mean_meets_floor": true,
          "n": 400,
          "passed": true
        },
        "cell10_allied_D_1_0": {
          "bootstrap_replicates": 5000,
          "ci95": [
            0.006478408239635695,
            0.010067364255476649
          ],
          "ci_carries_positive_sign": true,
          "floor": 0.004820009680542292,
          "mean": 0.008315807404492425,
          "mean_meets_floor": true,
          "n": 400,
          "passed": true
        },
        "cell10_allied_recovery": {
          "bootstrap_replicates": 5000,
          "ci95": [
            0.08902266432063652,
            0.1138360085386508
          ],
          "ci_carries_positive_sign": true,
          "floor": 0.04582309257999451,
          "mean": 0.10129730281404806,
          "mean_meets_floor": true,
          "n": 400,
          "passed": true
        },
        "cell11_dormant_effect_max": {
          "all_worlds_pass": true,
          "passed": true,
          "tolerance": 1e-10,
          "value": 3.3306690738754696e-16
        },
        "cell9_opposed_D_0_1_negated_raw": {
          "bootstrap_replicates": 5000,
          "ci95": [
            0.03349758295137815,
            0.040327273702800835
          ],
          "ci_carries_positive_sign": true,
          "floor": 0.021813188533686426,
          "mean": 0.03687381669524063,
          "mean_meets_floor": true,
          "n": 400,
          "passed": true
        },
        "cell9_opposed_D_1_0_negated_raw": {
          "bootstrap_replicates": 5000,
          "ci95": [
            0.03370696378334548,
            0.040226483295544166
          ],
          "ci_carries_positive_sign": true,
          "floor": 0.02162728537716363,
          "mean": 0.03693169570011725,
          "mean_meets_floor": true,
          "n": 400,
          "passed": true
        },
        "cell9_opposed_recovery": {
          "bootstrap_replicates": 5000,
          "ci95": [
            0.3065686980846311,
            0.3527734877726441
          ],
          "ci_carries_positive_sign": true,
          "floor": 0.19077996532688585,
          "mean": 0.3295214293557085,
          "mean_meets_floor": true,
          "n": 400,
          "passed": true
        }
      },
      "name": "interventional_topology_and_exact_dormancy",
      "passed": true
    },
    {
      "criterion": 6,
      "metrics": {
        "cell12_policy_difference_equivalence": {
          "bootstrap_replicates": 5000,
          "ci95": [
            -2.1685893821417792e-16,
            3.592538303879658e-15
          ],
          "mean": 1.6820804008924975e-15,
          "n": 300,
          "passed": true,
          "rope": [
            -0.01,
            0.01
          ]
        },
        "cell12_scientific_posterior_identity_error_max": {
          "all_pairs_pass": true,
          "passed": true,
          "tolerance": 1e-10,
          "value": 1.031952301389083e-13
        }
      },
      "name": "registration_candidate_common_null",
      "passed": true
    },
    {
      "criterion": 7,
      "custody_checks": {
        "all_5000_seeds_once": true,
        "ascending_gap_free": true,
        "escrow_release_record_verified": true,
        "raw_sealed_before_criteria": true,
        "runtime_event_ledgers_persisted": true,
        "trace_hash_matches": true
      },
      "metrics": {
        "active_count_accuracy": 1.0,
        "coverage": 0.9775,
        "ece": 0.03666804217262897,
        "edge_accuracy": {
          "CROSS_MODE_Y": 0.7075,
          "JOINT_POLICY_Y": 0.8175,
          "M1_G": 0.9625,
          "M2_G": 0.9825,
          "M3_G": 0.9825
        },
        "exact_program_accuracy": 0.55,
        "independent_oracle_audited_worlds": 20,
        "independent_oracle_error_max": 2.0539125955565396e-15,
        "independent_oracle_prefix_slices": 4,
        "minimum_edge_accuracy": 0.7075,
        "normalization_error_max": 5.684341886080802e-14,
        "partner_accuracy": 1.0,
        "topology_accuracy": 0.715
      },
      "name": "recovery_semantics_and_custody",
      "passed": true,
      "recovery_checks": {
        "active_count_accuracy": true,
        "coverage": true,
        "ece": true,
        "exact_program_accuracy": true,
        "independent_oracle_error_max": true,
        "minimum_edge_accuracy": true,
        "normalization_error_max": true,
        "partner_accuracy": true,
        "topology_accuracy": true
      }
    }
  ],
  "overall": "PASS"
}
```
