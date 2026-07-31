# V3.5 Replacement Gate 3

Verdict: **PASS**.

All worlds were executed inside serializing trace contexts. The
runtime event ledger is embedded in each persisted JSONL record; the
record-level and whole-file SHA-256 hashes were written before this
criterion report was produced.

Seed block: `[3533000, 3537999]`.

```json
{
  "ascending_gap_free": true,
  "bounds": {
    "B_max_v35_atomic": 3.4760986898352733,
    "implied_binary_change_bound": 0.7008782529950642
  },
  "custody": {
    "barred_blocks_touched": false,
    "retired_or_sealed_escrow_touched": false,
    "runtime_events_persisted_in_trace_jsonl": true,
    "trace_hash_ledger": "gate-3-amendment-2-trace-hashes.json"
  },
  "estimands": {
    "befriend": {
      "access": {
        "ci95": [
          0.061483877854807883,
          0.06319874436846075
        ],
        "mean": 0.06237695987163987,
        "n": 385
      },
      "support_response_3": {
        "ci95": [
          0.49999988160745595,
          0.5013819405254634
        ],
        "mean": 0.5004606185369624,
        "n": 385
      }
    },
    "denied": {
      "access": {
        "ci95": [
          0.020874683411637226,
          0.022380803447172717
        ],
        "mean": 0.02167433527558867,
        "n": 384
      },
      "contact_response_3": {
        "ci95": [
          0.4478646928074532,
          0.476875911681529
        ],
        "mean": 0.4634082601870387,
        "n": 384
      }
    },
    "mode_dormancy": {
      "dormant_influence_error": {
        "ci95": [
          8.795273311965526e-17,
          1.049665405100148e-16
        ],
        "mean": 9.631545200644215e-17,
        "n": 385
      }
    },
    "mode_recovery": {
      "third_mode_exposure": {
        "ci95": [
          0.9999060933277828,
          0.9999966988149432
        ],
        "mean": 0.99996447037901,
        "n": 385
      }
    },
    "partner": {
      "access": {
        "ci95": [
          0.11438241878025508,
          0.11717625673691728
        ],
        "mean": 0.11580577063878753,
        "n": 385
      },
      "q_remaining": {
        "ci95": [
          0.9999999999999992,
          1.0000000000000056
        ],
        "mean": 1.0000000000000024,
        "n": 385
      }
    },
    "policy_engagement": {
      "joint_policy_edge_uptake": {
        "ci95": [
          0.5525065704240059,
          0.5852083116905165
        ],
        "mean": 0.5692902527244634,
        "n": 385
      }
    },
    "policy_exclusion": {
      "joint_policy_edge_uptake": {
        "ci95": [
          0.4528175411863671,
          0.504373252290501
        ],
        "mean": 0.4791824770345091,
        "n": 385
      }
    },
    "policy_monitoring": {
      "joint_policy_edge_uptake": {
        "ci95": [
          0.038839479430869815,
          0.06522174267534553
        ],
        "mean": 0.05187335968908184,
        "n": 385
      }
    },
    "registration": {
      "policy_difference": {
        "ci95": [
          -1.1567154207849557e-15,
          2.145670432417608e-15
        ],
        "mean": 5.015519249917944e-16,
        "n": 384
      },
      "scientific_posterior_max_abs_difference": {
        "ci95": [
          3.077154123053786e-14,
          3.4033296833201976e-14
        ],
        "mean": 3.2388886494691405e-14,
        "n": 384
      }
    },
    "stakes": {
      "access_low_minus_high": {
        "ci95": [
          0.1065893717849499,
          0.10921266696081461
        ],
        "mean": 0.10791827000664571,
        "n": 385
      },
      "scientific_posterior_identity_error": {
        "ci95": [
          0.0,
          0.0
        ],
        "mean": 0.0,
        "n": 385
      }
    },
    "support": {
      "access": {
        "ci95": [
          0.06117751982548655,
          0.06250391499177538
        ],
        "mean": 0.06183444313113278,
        "n": 384
      },
      "support_response_3": {
        "ci95": [
          0.5000000046479293,
          0.5000001796540523
        ],
        "mean": 0.500000073729919,
        "n": 384
      }
    },
    "topology_allied": {
      "allied_D_0_1": {
        "ci95": [
          0.006102479039666373,
          0.009770435718844905
        ],
        "mean": 0.008006341063973015,
        "n": 384
      },
      "allied_D_1_0": {
        "ci95": [
          0.006038811338248788,
          0.00981625543615241
        ],
        "mean": 0.007968084201805581,
        "n": 384
      },
      "allied_recovery": {
        "ci95": [
          0.08711671961288629,
          0.11139399900550359
        ],
        "mean": 0.09893518453164844,
        "n": 384
      }
    },
    "topology_opposed": {
      "opposed_D_0_1": {
        "ci95": [
          0.03435035249805292,
          0.04084201148828317
        ],
        "mean": 0.03750564344888976,
        "n": 384
      },
      "opposed_D_1_0": {
        "ci95": [
          0.03413541425475217,
          0.040655573218455185
        ],
        "mean": 0.037406823742372586,
        "n": 384
      },
      "opposed_recovery": {
        "ci95": [
          0.3128360817880486,
          0.35884168054878673
        ],
        "mean": 0.33554999453931117,
        "n": 384
      }
    }
  },
  "failures": [],
  "frozen_effect_comparisons": {
    "befriend:access": {
      "floor": 0.030808420228944897,
      "lower_ci_must_exceed_zero": true,
      "metric": {
        "ci95": [
          0.061483877854807883,
          0.06319874436846075
        ],
        "mean": 0.06237695987163987,
        "n": 385
      },
      "passed": true
    },
    "befriend:support_response_3": {
      "floor": 0.25002964669658534,
      "lower_ci_must_exceed_zero": true,
      "metric": {
        "ci95": [
          0.49999988160745595,
          0.5013819405254634
        ],
        "mean": 0.5004606185369624,
        "n": 385
      },
      "passed": true
    },
    "denied:access": {
      "floor": 0.011022406848183891,
      "lower_ci_must_exceed_zero": true,
      "metric": {
        "ci95": [
          0.020874683411637226,
          0.022380803447172717
        ],
        "mean": 0.02167433527558867,
        "n": 384
      },
      "passed": true
    },
    "denied:contact_response_3": {
      "floor": 0.23462657827078734,
      "lower_ci_must_exceed_zero": true,
      "metric": {
        "ci95": [
          0.4478646928074532,
          0.476875911681529
        ],
        "mean": 0.4634082601870387,
        "n": 384
      },
      "passed": true
    },
    "mode_recovery:third_mode_exposure": {
      "floor": 0.49994076283590083,
      "lower_ci_must_exceed_zero": true,
      "metric": {
        "ci95": [
          0.9999060933277828,
          0.9999966988149432
        ],
        "mean": 0.99996447037901,
        "n": 385
      },
      "passed": true
    },
    "partner:access": {
      "floor": 0.0575741252904589,
      "lower_ci_must_exceed_zero": true,
      "metric": {
        "ci95": [
          0.11438241878025508,
          0.11717625673691728
        ],
        "mean": 0.11580577063878753,
        "n": 385
      },
      "passed": true
    },
    "partner:q_remaining": {
      "floor": 0.4999999999999974,
      "lower_ci_must_exceed_zero": true,
      "metric": {
        "ci95": [
          0.9999999999999992,
          1.0000000000000056
        ],
        "mean": 1.0000000000000024,
        "n": 385
      },
      "passed": true
    },
    "policy_engagement:joint_policy_edge_uptake": {
      "floor": 0.2818778047497165,
      "lower_ci_must_exceed_zero": true,
      "metric": {
        "ci95": [
          0.5525065704240059,
          0.5852083116905165
        ],
        "mean": 0.5692902527244634,
        "n": 385
      },
      "passed": true
    },
    "policy_exclusion:joint_policy_edge_uptake": {
      "floor": 0.22369120540497045,
      "lower_ci_must_exceed_zero": true,
      "metric": {
        "ci95": [
          0.4528175411863671,
          0.504373252290501
        ],
        "mean": 0.4791824770345091,
        "n": 385
      },
      "passed": true
    },
    "policy_monitoring:joint_policy_edge_uptake": {
      "floor": 0.028590899494582652,
      "lower_ci_must_exceed_zero": true,
      "metric": {
        "ci95": [
          0.038839479430869815,
          0.06522174267534553
        ],
        "mean": 0.05187335968908184,
        "n": 385
      },
      "passed": true
    },
    "stakes:access_low_minus_high": {
      "floor": 0.05456176795537784,
      "lower_ci_must_exceed_zero": true,
      "metric": {
        "ci95": [
          0.1065893717849499,
          0.10921266696081461
        ],
        "mean": 0.10791827000664571,
        "n": 385
      },
      "passed": true
    },
    "support:access": {
      "floor": 0.031786343743120116,
      "lower_ci_must_exceed_zero": true,
      "metric": {
        "ci95": [
          0.06117751982548655,
          0.06250391499177538
        ],
        "mean": 0.06183444313113278,
        "n": 384
      },
      "passed": true
    },
    "support:support_response_3": {
      "floor": 0.2500000001761959,
      "lower_ci_must_exceed_zero": true,
      "metric": {
        "ci95": [
          0.5000000046479293,
          0.5000001796540523
        ],
        "mean": 0.500000073729919,
        "n": 384
      },
      "passed": true
    },
    "topology_allied:allied_D_0_1": {
      "floor": 0.004841000047368376,
      "lower_ci_must_exceed_zero": true,
      "metric": {
        "ci95": [
          0.006102479039666373,
          0.009770435718844905
        ],
        "mean": 0.008006341063973015,
        "n": 384
      },
      "passed": true
    },
    "topology_allied:allied_D_1_0": {
      "floor": 0.004820009680542292,
      "lower_ci_must_exceed_zero": true,
      "metric": {
        "ci95": [
          0.006038811338248788,
          0.00981625543615241
        ],
        "mean": 0.007968084201805581,
        "n": 384
      },
      "passed": true
    },
    "topology_allied:allied_recovery": {
      "floor": 0.04582309257999451,
      "lower_ci_must_exceed_zero": true,
      "metric": {
        "ci95": [
          0.08711671961288629,
          0.11139399900550359
        ],
        "mean": 0.09893518453164844,
        "n": 384
      },
      "passed": true
    },
    "topology_opposed:opposed_D_0_1": {
      "floor": 0.021813188533686426,
      "lower_ci_must_exceed_zero": true,
      "metric": {
        "ci95": [
          0.03435035249805292,
          0.04084201148828317
        ],
        "mean": 0.03750564344888976,
        "n": 384
      },
      "passed": true
    },
    "topology_opposed:opposed_D_1_0": {
      "floor": 0.02162728537716363,
      "lower_ci_must_exceed_zero": true,
      "metric": {
        "ci95": [
          0.03413541425475217,
          0.040655573218455185
        ],
        "mean": 0.037406823742372586,
        "n": 384
      },
      "passed": true
    },
    "topology_opposed:opposed_recovery": {
      "floor": 0.19077996532688585,
      "lower_ci_must_exceed_zero": true,
      "metric": {
        "ci95": [
          0.3128360817880486,
          0.35884168054878673
        ],
        "mean": 0.33554999453931117,
        "n": 384
      },
      "passed": true
    }
  },
  "identity_values": {
    "dormant_mode_influence": 4.440892098500626e-16,
    "stakes_scientific_posterior": 0.0
  },
  "opposed_allied_reported_separately": true,
  "opposed_recording_convention": "opposed_D_* is the negated raw interventional influence; raw opposed D entries are negative",
  "registration_equivalence": {
    "metrics": {
      "policy_difference": {
        "ci95": [
          -1.1567154207849557e-15,
          2.145670432417608e-15
        ],
        "mean": 5.015519249917944e-16,
        "n": 384
      },
      "scientific_posterior_max_abs_difference": {
        "ci95": [
          3.077154123053786e-14,
          3.4033296833201976e-14
        ],
        "mean": 3.2388886494691405e-14,
        "n": 384
      }
    },
    "passed": true,
    "rope": [
      -0.01,
      0.01
    ]
  },
  "seed_block": [
    3533000,
    3537999
  ],
  "seeds_consumed": 5000,
  "verdict": "PASS"
}
```
