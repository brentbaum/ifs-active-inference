# V3.6 adjudicated traced attainability pilot

Verdict: **FAIL**.

```json
{
  "all_declared_signs_attainable": false,
  "barred_seed": 3600000,
  "compression_counts": {
    "constants_at_least_50_percent": true,
    "factor_templates_at_least_50_percent": true,
    "factor_templates_fraction": 0.5294117647058824,
    "frozen_scientific_constants_fraction": 0.5416666666666666
  },
  "effects": {
    "broadcast_off_monitor": {
      "attainable": true,
      "direction": "positive",
      "interval_95": [
        0.4397653074728647,
        0.47270283082615766
      ],
      "kind": "causal_effect",
      "mean": 0.4570686743820938
    },
    "context_scope_disabled": {
      "attainable": true,
      "direction": "positive",
      "interval_95": [
        0.9542183202726572,
        0.9798223247878355
      ],
      "kind": "causal_effect",
      "mean": 0.9681231933841726
    },
    "cue_only_exposure": {
      "attainable": true,
      "direction": "positive",
      "interval_95": [
        0.3092784932211726,
        0.33226073304707127
      ],
      "kind": "causal_effect",
      "mean": 0.32126658273926645
    },
    "denied_contact_masked": {
      "attainable": true,
      "direction": "positive",
      "interval_95": [
        0.10156493989935741,
        0.16335389303010123
      ],
      "kind": "causal_effect",
      "mean": 0.13284097781844062
    },
    "mode_bypass": {
      "attainable": true,
      "direction": "positive",
      "interval_95": [
        0.06507836417808738,
        0.07142573130367703
      ],
      "kind": "causal_effect",
      "mean": 0.06825895665474503
    },
    "premature_do_over": {
      "attainable": false,
      "direction": "positive",
      "interval_95": [
        -0.03688060730166053,
        0.021721859932301718
      ],
      "kind": "causal_effect",
      "mean": -0.007591287369016907
    },
    "regulation_without_root_evidence": {
      "attainable": true,
      "direction": "positive",
      "interval_95": [
        0.43232551293411164,
        0.4682209109744567
      ],
      "kind": "causal_effect",
      "mean": 0.4507788571271958
    },
    "soothing_noncontingent_partner": {
      "attainable": true,
      "direction": "positive",
      "interval_95": [
        0.9912653727436793,
        0.996353342283854
      ],
      "kind": "causal_effect",
      "mean": 0.9941561951526432
    },
    "structural_pruning_disabled": {
      "attainable": true,
      "direction": "positive",
      "interval_95": [
        0.6099296907530339,
        0.6617263131510611
      ],
      "kind": "causal_effect",
      "mean": 0.6371774205287999
    },
    "unreliable_partner": {
      "attainable": true,
      "direction": "positive",
      "interval_95": [
        0.7000045955922202,
        0.7811749351446462
      ],
      "kind": "causal_effect",
      "mean": 0.7410987106036919
    }
  },
  "pilot_block": [
    3660000,
    3663999
  ],
  "retained_findings": {
    "V3.1_revisability_effect_interval": null,
    "V3.3_do_over_equivalence": {
      "ci95": [
        0.0,
        0.0
      ],
      "frozen_floor": 0.00025,
      "mean": 0.0,
      "passed": false
    },
    "V3.4_information_curve": {
      "32": {
        "classification": "DESCRIPTIVE_ROBUSTNESS",
        "coverage": 0.975,
        "edge_accuracy": {
          "L_PREC": 0.9,
          "L_TRANSITION": 0.975,
          "L_Y": 0.845,
          "PA_RY": 0.969
        },
        "exact_program_accuracy": 0.733,
        "root_accuracy": 0.797,
        "root_ece": 0.01336292120744247,
        "structure_ece": 0.02019370504680673
      },
      "48": {
        "classification": "PRIMARY_BLOCKING",
        "coverage": 0.9903333333333333,
        "edge_accuracy": {
          "L_PREC": 0.9493333333333334,
          "L_TRANSITION": 0.993,
          "L_Y": 0.888,
          "PA_RY": 0.994
        },
        "exact_program_accuracy": 0.837,
        "frozen_exact_program_floor": 0.78,
        "root_accuracy": 0.7823333333333333,
        "root_ece": 0.010738725111008072,
        "structure_ece": 0.015816303036017356
      },
      "96": {
        "classification": "DESCRIPTIVE_ROBUSTNESS",
        "coverage": 0.997,
        "edge_accuracy": {
          "L_PREC": 0.977,
          "L_TRANSITION": 1.0,
          "L_Y": 0.935,
          "PA_RY": 1.0
        },
        "exact_program_accuracy": 0.915,
        "root_accuracy": 0.768,
        "root_ece": 0.021199575930785145,
        "structure_ece": 0.013232751035546705
      }
    },
    "V3.5_failure_records": [
      "original dormant-idleness proof did not prove common observed-channel support",
      "original polarization readout was conditional rather than interventional"
    ]
  },
  "seed_order_gap_free": true,
  "stage": "V3.6",
  "stakes_identity_error_max": 0.0,
  "stakes_policy_low_minus_high": {
    "attainable": true,
    "interval_95": [
      0.10291542939176537,
      0.10598819209407398
    ],
    "mean": 0.1045075410027982
  },
  "structure_code_length": {
    "max": 111.45034976197755,
    "mean": 106.7830170946449,
    "min": 101.45034976197755,
    "quantiles": [
      101.45034976197755,
      107.45034976197755,
      111.45034976197755
    ]
  },
  "verdict": "FAIL",
  "world_count": 4000
}
```
