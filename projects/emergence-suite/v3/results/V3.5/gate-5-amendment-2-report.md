# V3.5 Gate 5 robustness

Verdict: **PASS**.

All worlds were executed inside serializing trace contexts. The
runtime event ledger is embedded in each persisted JSONL record; the
record-level and whole-file SHA-256 hashes were written before this
criterion report was produced.

Seed block: `[3512000, 3519999]`.

```json
{
  "ascending_gap_free": true,
  "custody": {
    "barred_blocks_touched": false,
    "retired_or_sealed_escrow_touched": false,
    "runtime_events_persisted_in_trace_jsonl": true,
    "trace_hash_ledger": "gate-5-amendment-2-trace-hashes.json"
  },
  "failures": [],
  "manifest_verification": [
    {
      "file_count": 31,
      "mismatches": [],
      "passed": true,
      "stage": "V3.0"
    },
    {
      "file_count": 42,
      "mismatches": [],
      "passed": true,
      "stage": "V3.1"
    },
    {
      "file_count": 42,
      "mismatches": [],
      "passed": true,
      "stage": "V3.2"
    },
    {
      "file_count": 53,
      "mismatches": [],
      "passed": true,
      "stage": "V3.3"
    },
    {
      "file_count": 82,
      "mismatches": [],
      "passed": true,
      "stage": "V3.4"
    }
  ],
  "partition": {
    "primary_assays": 6500,
    "primary_recovery_64": 500,
    "sweeps": {
      "code_length_scale": 200,
      "length_32": 200,
      "length_96": 200,
      "missingness_25pct": 200,
      "policy_schedule": 200
    }
  },
  "primary_assays": {
    "comparisons": {
      "befriend:access": {
        "floor": 0.030808420228944897,
        "metric": {
          "ci95": [
            0.061761922541000804,
            0.06296428062403289
          ],
          "mean": 0.06236368975389198,
          "n": 500
        },
        "passed": true
      },
      "befriend:support_response_3": {
        "floor": 0.25002964669658534,
        "metric": {
          "ci95": [
            0.5000000016897103,
            0.5000000794022231
          ],
          "mean": 0.5000000331355436,
          "n": 500
        },
        "passed": true
      },
      "denied:access": {
        "floor": 0.011022406848183891,
        "metric": {
          "ci95": [
            0.0221614292872218,
            0.022999789905612873
          ],
          "mean": 0.022602452968265255,
          "n": 500
        },
        "passed": true
      },
      "denied:contact_response_3": {
        "floor": 0.23462657827078734,
        "metric": {
          "ci95": [
            0.47033438482373024,
            0.48662352275669074
          ],
          "mean": 0.478917504129658,
          "n": 500
        },
        "passed": true
      },
      "mode_recovery:third_mode_exposure": {
        "floor": 0.49994076283590083,
        "metric": {
          "ci95": [
            0.9998871402539488,
            0.9999877008460133
          ],
          "mean": 0.9999506265321673,
          "n": 500
        },
        "passed": true
      },
      "partner:access": {
        "floor": 0.0575741252904589,
        "metric": {
          "ci95": [
            0.11530825167860552,
            0.1176894218985707
          ],
          "mean": 0.1165129528605204,
          "n": 500
        },
        "passed": true
      },
      "partner:q_remaining": {
        "floor": 0.4999999999999974,
        "metric": {
          "ci95": [
            0.9999999999999984,
            1.0000000000000038
          ],
          "mean": 1.000000000000001,
          "n": 500
        },
        "passed": true
      },
      "policy_engagement:joint_policy_edge_uptake": {
        "floor": 0.2818778047497165,
        "metric": {
          "ci95": [
            0.5447222774471413,
            0.5744841751285067
          ],
          "mean": 0.5603056174189653,
          "n": 500
        },
        "passed": true
      },
      "policy_exclusion:joint_policy_edge_uptake": {
        "floor": 0.22369120540497045,
        "metric": {
          "ci95": [
            0.4595366095464424,
            0.5047317084054731
          ],
          "mean": 0.4823458070754474,
          "n": 500
        },
        "passed": true
      },
      "policy_monitoring:joint_policy_edge_uptake": {
        "floor": 0.028590899494582652,
        "metric": {
          "ci95": [
            0.06600065085338704,
            0.0906553693743745
          ],
          "mean": 0.07830900152381412,
          "n": 500
        },
        "passed": true
      },
      "stakes:access_low_minus_high": {
        "floor": 0.05456176795537784,
        "metric": {
          "ci95": [
            0.1070178380893348,
            0.10941149298827413
          ],
          "mean": 0.10820236403244186,
          "n": 500
        },
        "passed": true
      },
      "support:access": {
        "floor": 0.031786343743120116,
        "metric": {
          "ci95": [
            0.061501045833154876,
            0.06262877101817994
          ],
          "mean": 0.06206161111290689,
          "n": 500
        },
        "passed": true
      },
      "support:support_response_3": {
        "floor": 0.2500000001761959,
        "metric": {
          "ci95": [
            0.500000004593441,
            0.5000016452516887
          ],
          "mean": 0.5000006131769034,
          "n": 500
        },
        "passed": true
      },
      "topology_allied:allied_D_0_1": {
        "floor": 0.004841000047368376,
        "metric": {
          "ci95": [
            0.0051247230277370985,
            0.008684265673291475
          ],
          "mean": 0.006934037741768998,
          "n": 500
        },
        "passed": true
      },
      "topology_allied:allied_D_1_0": {
        "floor": 0.004820009680542292,
        "metric": {
          "ci95": [
            0.005127076366570961,
            0.008672209801204417
          ],
          "mean": 0.00688576273585708,
          "n": 500
        },
        "passed": true
      },
      "topology_allied:allied_recovery": {
        "floor": 0.04582309257999451,
        "metric": {
          "ci95": [
            0.10142027615165598,
            0.12309776224389611
          ],
          "mean": 0.11182201850923479,
          "n": 500
        },
        "passed": true
      },
      "topology_opposed:opposed_D_0_1": {
        "floor": 0.021813188533686426,
        "metric": {
          "ci95": [
            0.03407589112497835,
            0.04016876062490247
          ],
          "mean": 0.03717534637941441,
          "n": 500
        },
        "passed": true
      },
      "topology_opposed:opposed_D_1_0": {
        "floor": 0.02162728537716363,
        "metric": {
          "ci95": [
            0.034045597513489206,
            0.04009484587100583
          ],
          "mean": 0.03707754710782828,
          "n": 500
        },
        "passed": true
      },
      "topology_opposed:opposed_recovery": {
        "floor": 0.19077996532688585,
        "metric": {
          "ci95": [
            0.31074900099145464,
            0.35388417089830626
          ],
          "mean": 0.3321567670258514,
          "n": 500
        },
        "passed": true
      }
    },
    "estimands": {
      "befriend": {
        "access": {
          "ci95": [
            0.061761922541000804,
            0.06296428062403289
          ],
          "mean": 0.06236368975389198,
          "n": 500
        },
        "support_response_3": {
          "ci95": [
            0.5000000016897103,
            0.5000000794022231
          ],
          "mean": 0.5000000331355436,
          "n": 500
        }
      },
      "denied": {
        "access": {
          "ci95": [
            0.0221614292872218,
            0.022999789905612873
          ],
          "mean": 0.022602452968265255,
          "n": 500
        },
        "contact_response_3": {
          "ci95": [
            0.47033438482373024,
            0.48662352275669074
          ],
          "mean": 0.478917504129658,
          "n": 500
        }
      },
      "mode_dormancy": {
        "dormant_influence_error": {
          "ci95": [
            9.348077867343818e-17,
            1.0857981180834031e-16
          ],
          "mean": 1.0103029524088925e-16,
          "n": 500
        }
      },
      "mode_recovery": {
        "third_mode_exposure": {
          "ci95": [
            0.9998871402539488,
            0.9999877008460133
          ],
          "mean": 0.9999506265321673,
          "n": 500
        }
      },
      "partner": {
        "access": {
          "ci95": [
            0.11530825167860552,
            0.1176894218985707
          ],
          "mean": 0.1165129528605204,
          "n": 500
        },
        "q_remaining": {
          "ci95": [
            0.9999999999999984,
            1.0000000000000038
          ],
          "mean": 1.000000000000001,
          "n": 500
        }
      },
      "policy_engagement": {
        "joint_policy_edge_uptake": {
          "ci95": [
            0.5447222774471413,
            0.5744841751285067
          ],
          "mean": 0.5603056174189653,
          "n": 500
        }
      },
      "policy_exclusion": {
        "joint_policy_edge_uptake": {
          "ci95": [
            0.4595366095464424,
            0.5047317084054731
          ],
          "mean": 0.4823458070754474,
          "n": 500
        }
      },
      "policy_monitoring": {
        "joint_policy_edge_uptake": {
          "ci95": [
            0.06600065085338704,
            0.0906553693743745
          ],
          "mean": 0.07830900152381412,
          "n": 500
        }
      },
      "registration": {
        "policy_difference": {
          "ci95": [
            -1.113020786647212e-15,
            1.6520021461907668e-15
          ],
          "mean": 2.606248550307555e-16,
          "n": 500
        },
        "scientific_posterior_max_abs_difference": {
          "ci95": [
            3.138774622157836e-14,
            3.4164895218458113e-14
          ],
          "mean": 3.27879529082864e-14,
          "n": 500
        }
      },
      "stakes": {
        "access_low_minus_high": {
          "ci95": [
            0.1070178380893348,
            0.10941149298827413
          ],
          "mean": 0.10820236403244186,
          "n": 500
        },
        "scientific_posterior_identity_error": {
          "ci95": [
            0.0,
            0.0
          ],
          "mean": 0.0,
          "n": 500
        }
      },
      "support": {
        "access": {
          "ci95": [
            0.061501045833154876,
            0.06262877101817994
          ],
          "mean": 0.06206161111290689,
          "n": 500
        },
        "support_response_3": {
          "ci95": [
            0.500000004593441,
            0.5000016452516887
          ],
          "mean": 0.5000006131769034,
          "n": 500
        }
      },
      "topology_allied": {
        "allied_D_0_1": {
          "ci95": [
            0.0051247230277370985,
            0.008684265673291475
          ],
          "mean": 0.006934037741768998,
          "n": 500
        },
        "allied_D_1_0": {
          "ci95": [
            0.005127076366570961,
            0.008672209801204417
          ],
          "mean": 0.00688576273585708,
          "n": 500
        },
        "allied_recovery": {
          "ci95": [
            0.10142027615165598,
            0.12309776224389611
          ],
          "mean": 0.11182201850923479,
          "n": 500
        }
      },
      "topology_opposed": {
        "opposed_D_0_1": {
          "ci95": [
            0.03407589112497835,
            0.04016876062490247
          ],
          "mean": 0.03717534637941441,
          "n": 500
        },
        "opposed_D_1_0": {
          "ci95": [
            0.034045597513489206,
            0.04009484587100583
          ],
          "mean": 0.03707754710782828,
          "n": 500
        },
        "opposed_recovery": {
          "ci95": [
            0.31074900099145464,
            0.35388417089830626
          ],
          "mean": 0.3321567670258514,
          "n": 500
        }
      }
    },
    "failures": [],
    "identities": {
      "dormant_mode_influence": 4.440892098500626e-16,
      "stakes_scientific_posterior": 0.0
    },
    "registration_pass": true
  },
  "primary_recovery": {
    "active_count_accuracy": 1.0,
    "contact_parameter_accuracy": [
      0.988,
      0.992,
      0.996
    ],
    "coverage": 0.978,
    "ece": 0.0402701217452843,
    "edge_accuracy": {
      "CROSS_MODE_Y": 0.724,
      "JOINT_POLICY_Y": 0.862,
      "M1_G": 0.974,
      "M2_G": 0.992,
      "M3_G": 0.99
    },
    "exact_log_error_max": 0.0,
    "minimum_edge_accuracy": 0.724,
    "normalization_error_max": 5.6621374255882984e-14,
    "partner_accuracy": 1.0,
    "program_accuracy": 0.598,
    "registration_delivered_masked_posterior_error_max": 1.2434497875801753e-13,
    "stakes_policy_difference_mean": 0.013106521529269728,
    "stakes_scientific_posterior_error_max": 0.0,
    "support_parameter_accuracy": [
      0.76,
      0.872,
      0.948
    ],
    "topology_accuracy": 0.718,
    "whole_program_accuracy": 0.598,
    "world_count": 500
  },
  "primary_recovery_comparisons": {
    "active_count_accuracy": [
      1.0,
      0.9,
      ">="
    ],
    "coverage": [
      0.978,
      0.8718750000000001,
      ">="
    ],
    "ece": [
      0.0402701217452843,
      0.06279020976257683,
      "<="
    ],
    "exact_log_error_max": [
      0.0,
      1e-10,
      "<="
    ],
    "minimum_edge_accuracy": [
      0.724,
      0.6165,
      ">="
    ],
    "normalization_error_max": [
      5.6621374255882984e-14,
      1e-10,
      "<="
    ],
    "partner_accuracy": [
      1.0,
      0.9,
      ">="
    ],
    "topology_accuracy": [
      0.718,
      0.61425,
      ">="
    ],
    "whole_program_accuracy": [
      0.598,
      0.49612500000000004,
      ">="
    ]
  },
  "seed_block": [
    3512000,
    3519999
  ],
  "seeds_consumed": 8000,
  "standing_gate_verdicts": {
    "gate-1-amendment-2-rerun.json": "PASS",
    "gate-2-amendment-2.json": "PASS",
    "gate-3-amendment-2.json": "PASS",
    "gate-4-amendment-2.json": "PASS"
  },
  "sweeps_descriptive_no_primary_floor_transplant": {
    "code_length_scale": {
      "active_count_accuracy": 1.0,
      "by_scale": {
        "0.75": {
          "active_count_accuracy": 1.0,
          "edge_accuracy": {
            "CROSS_MODE_Y": 0.71,
            "JOINT_POLICY_Y": 0.83,
            "M1_G": 0.97,
            "M2_G": 1.0,
            "M3_G": 0.99
          },
          "finite_evidence_all": true,
          "minimum_edge_accuracy": 0.71,
          "n": 100,
          "normalization_error_max": 5.595524044110789e-14,
          "whole_program_accuracy": 0.56
        },
        "1.25": {
          "active_count_accuracy": 1.0,
          "edge_accuracy": {
            "CROSS_MODE_Y": 0.68,
            "JOINT_POLICY_Y": 0.8,
            "M1_G": 0.97,
            "M2_G": 0.98,
            "M3_G": 0.98
          },
          "finite_evidence_all": true,
          "minimum_edge_accuracy": 0.68,
          "n": 100,
          "normalization_error_max": 5.639932965095795e-14,
          "whole_program_accuracy": 0.52
        }
      },
      "edge_accuracy": {
        "CROSS_MODE_Y": 0.695,
        "JOINT_POLICY_Y": 0.815,
        "M1_G": 0.97,
        "M2_G": 0.99,
        "M3_G": 0.985
      },
      "finite_evidence_all": true,
      "minimum_edge_accuracy": 0.695,
      "n": 200,
      "normalization_error_max": 5.639932965095795e-14,
      "whole_program_accuracy": 0.54
    },
    "length_32": {
      "active_count_accuracy": 0.99,
      "contact_parameter_accuracy": [
        0.96,
        0.98,
        0.99
      ],
      "coverage": 0.945,
      "ece": 0.06286026665945589,
      "edge_accuracy": {
        "CROSS_MODE_Y": 0.665,
        "JOINT_POLICY_Y": 0.78,
        "M1_G": 0.93,
        "M2_G": 0.95,
        "M3_G": 0.965
      },
      "exact_log_error_max": 0.0,
      "minimum_edge_accuracy": 0.665,
      "normalization_error_max": 2.8310687127941492e-14,
      "partner_accuracy": 1.0,
      "program_accuracy": 0.49,
      "registration_delivered_masked_posterior_error_max": 4.2743586448068527e-14,
      "stakes_policy_difference_mean": 0.013520186475185896,
      "stakes_scientific_posterior_error_max": 0.0,
      "support_parameter_accuracy": [
        0.735,
        0.87,
        0.95
      ],
      "topology_accuracy": 0.67,
      "whole_program_accuracy": 0.49,
      "world_count": 200
    },
    "length_96": {
      "active_count_accuracy": 1.0,
      "contact_parameter_accuracy": [
        1.0,
        1.0,
        0.995
      ],
      "coverage": 0.99,
      "ece": 0.07814965844729728,
      "edge_accuracy": {
        "CROSS_MODE_Y": 0.67,
        "JOINT_POLICY_Y": 0.865,
        "M1_G": 0.995,
        "M2_G": 1.0,
        "M3_G": 1.0
      },
      "exact_log_error_max": 0.0,
      "minimum_edge_accuracy": 0.67,
      "normalization_error_max": 5.684341886080802e-14,
      "partner_accuracy": 1.0,
      "program_accuracy": 0.57,
      "registration_delivered_masked_posterior_error_max": 2.5845992013273644e-13,
      "stakes_policy_difference_mean": 0.01272346260570506,
      "stakes_scientific_posterior_error_max": 0.0,
      "support_parameter_accuracy": [
        0.785,
        0.845,
        0.96
      ],
      "topology_accuracy": 0.67,
      "whole_program_accuracy": 0.57,
      "world_count": 200
    },
    "missingness_25pct": {
      "active_count_accuracy": 1.0,
      "edge_accuracy": {
        "CROSS_MODE_Y": 0.695,
        "JOINT_POLICY_Y": 0.785,
        "M1_G": 0.97,
        "M2_G": 0.98,
        "M3_G": 0.975
      },
      "finite_evidence_all": true,
      "minimum_edge_accuracy": 0.695,
      "n": 200,
      "normalization_error_max": 2.8310687127941492e-14,
      "whole_program_accuracy": 0.505
    },
    "policy_schedule": {
      "policy_engagement": {
        "joint_policy_edge_uptake": {
          "ci95": [
            0.5258320708279307,
            0.5979166195636941
          ],
          "mean": 0.5637674830346749,
          "n": 66
        }
      },
      "policy_exclusion": {
        "joint_policy_edge_uptake": {
          "ci95": [
            0.4058411946335965,
            0.5350917746868284
          ],
          "mean": 0.4732235313401421,
          "n": 67
        }
      },
      "policy_monitoring": {
        "joint_policy_edge_uptake": {
          "ci95": [
            0.02622194271628406,
            0.08758278680871372
          ],
          "mean": 0.05751838774648544,
          "n": 67
        }
      }
    }
  },
  "verdict": "PASS"
}
```
