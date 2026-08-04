# Full Path Generator Scorer Identity

```json
{
  "external": {
    "family": "external_shared_support_generator",
    "lengths": [
      1,
      2,
      3,
      4
    ],
    "maximum_error": 0.0,
    "passed": true,
    "rows": [
      {
        "length": 1,
        "max_log_joint_error": 0.0,
        "stratum": "acute_one",
        "support_equal": true
      },
      {
        "length": 1,
        "max_log_joint_error": 0.0,
        "stratum": "chronic_one",
        "support_equal": true
      },
      {
        "length": 1,
        "max_log_joint_error": 0.0,
        "stratum": "chronic_multiple",
        "support_equal": true
      },
      {
        "length": 1,
        "max_log_joint_error": 0.0,
        "stratum": "real_danger_adaptive",
        "support_equal": true
      },
      {
        "length": 2,
        "max_log_joint_error": 0.0,
        "stratum": "acute_one",
        "support_equal": true
      },
      {
        "length": 2,
        "max_log_joint_error": 0.0,
        "stratum": "chronic_one",
        "support_equal": true
      },
      {
        "length": 2,
        "max_log_joint_error": 0.0,
        "stratum": "chronic_multiple",
        "support_equal": true
      },
      {
        "length": 2,
        "max_log_joint_error": 0.0,
        "stratum": "real_danger_adaptive",
        "support_equal": true
      },
      {
        "length": 3,
        "max_log_joint_error": 0.0,
        "stratum": "acute_one",
        "support_equal": true
      },
      {
        "length": 3,
        "max_log_joint_error": 0.0,
        "stratum": "chronic_one",
        "support_equal": true
      },
      {
        "length": 3,
        "max_log_joint_error": 0.0,
        "stratum": "chronic_multiple",
        "support_equal": true
      },
      {
        "length": 3,
        "max_log_joint_error": 0.0,
        "stratum": "real_danger_adaptive",
        "support_equal": true
      },
      {
        "length": 4,
        "max_log_joint_error": 0.0,
        "stratum": "acute_one",
        "support_equal": true
      },
      {
        "length": 4,
        "max_log_joint_error": 0.0,
        "stratum": "chronic_one",
        "support_equal": true
      },
      {
        "length": 4,
        "max_log_joint_error": 0.0,
        "stratum": "chronic_multiple",
        "support_equal": true
      },
      {
        "length": 4,
        "max_log_joint_error": 0.0,
        "stratum": "real_danger_adaptive",
        "support_equal": true
      }
    ],
    "support_equal": true
  },
  "native": {
    "family": "frozen_v3.6_native",
    "lengths": [
      1,
      2,
      3,
      4
    ],
    "maximum_error": 0.0,
    "passed": true,
    "rows": [
      {
        "delivered_channels": [
          "contact",
          "identity",
          "outcome",
          "partner"
        ],
        "intervention_probability": 1.0,
        "length": 1,
        "masked_likelihood": 1.0,
        "max_log_joint_error": 0.0,
        "structure": {
          "active_modes": 1,
          "cross_mode_outcome": 0,
          "joint_policy_outcome": 0,
          "mode_root_edges": [
            0,
            0,
            0
          ]
        },
        "support_equal": true,
        "temporal": {
          "active_contexts": 1,
          "dynamics": [
            "static",
            "static"
          ],
          "scopes": [
            "shared_global",
            "shared_global"
          ]
        }
      },
      {
        "delivered_channels": [
          "contact",
          "identity",
          "outcome",
          "partner"
        ],
        "intervention_probability": 1.0,
        "length": 1,
        "masked_likelihood": 1.0,
        "max_log_joint_error": 0.0,
        "structure": {
          "active_modes": 3,
          "cross_mode_outcome": 0,
          "joint_policy_outcome": 0,
          "mode_root_edges": [
            0,
            0,
            1
          ]
        },
        "support_equal": true,
        "temporal": {
          "active_contexts": 2,
          "dynamics": [
            "ordered_random_walk",
            "static"
          ],
          "scopes": [
            "cue_specific",
            "cue_specific"
          ]
        }
      },
      {
        "delivered_channels": [
          "contact",
          "identity",
          "outcome",
          "partner"
        ],
        "intervention_probability": 1.0,
        "length": 1,
        "masked_likelihood": 1.0,
        "max_log_joint_error": 0.0,
        "structure": {
          "active_modes": 3,
          "cross_mode_outcome": 1,
          "joint_policy_outcome": 1,
          "mode_root_edges": [
            1,
            1,
            1
          ]
        },
        "support_equal": true,
        "temporal": {
          "active_contexts": 3,
          "dynamics": [
            "one_way_change",
            "one_way_change"
          ],
          "scopes": [
            "context_specific",
            "context_specific"
          ]
        }
      },
      {
        "delivered_channels": [
          "contact",
          "context",
          "identity",
          "outcome",
          "partner"
        ],
        "intervention_probability": 1.0,
        "length": 2,
        "masked_likelihood": 1.0,
        "max_log_joint_error": 0.0,
        "structure": {
          "active_modes": 1,
          "cross_mode_outcome": 0,
          "joint_policy_outcome": 0,
          "mode_root_edges": [
            0,
            0,
            0
          ]
        },
        "support_equal": true,
        "temporal": {
          "active_contexts": 1,
          "dynamics": [
            "static",
            "static"
          ],
          "scopes": [
            "shared_global",
            "shared_global"
          ]
        }
      },
      {
        "delivered_channels": [
          "contact",
          "context",
          "identity",
          "outcome",
          "partner"
        ],
        "intervention_probability": 1.0,
        "length": 2,
        "masked_likelihood": 1.0,
        "max_log_joint_error": 0.0,
        "structure": {
          "active_modes": 3,
          "cross_mode_outcome": 0,
          "joint_policy_outcome": 0,
          "mode_root_edges": [
            0,
            0,
            1
          ]
        },
        "support_equal": true,
        "temporal": {
          "active_contexts": 2,
          "dynamics": [
            "ordered_random_walk",
            "static"
          ],
          "scopes": [
            "cue_specific",
            "cue_specific"
          ]
        }
      },
      {
        "delivered_channels": [
          "contact",
          "context",
          "identity",
          "outcome",
          "partner"
        ],
        "intervention_probability": 1.0,
        "length": 2,
        "masked_likelihood": 1.0,
        "max_log_joint_error": 0.0,
        "structure": {
          "active_modes": 3,
          "cross_mode_outcome": 1,
          "joint_policy_outcome": 1,
          "mode_root_edges": [
            1,
            1,
            1
          ]
        },
        "support_equal": true,
        "temporal": {
          "active_contexts": 3,
          "dynamics": [
            "one_way_change",
            "one_way_change"
          ],
          "scopes": [
            "context_specific",
            "context_specific"
          ]
        }
      },
      {
        "delivered_channels": [
          "contact",
          "context",
          "identity",
          "outcome",
          "partner"
        ],
        "intervention_probability": 1.0,
        "length": 3,
        "masked_likelihood": 1.0,
        "max_log_joint_error": 0.0,
        "structure": {
          "active_modes": 1,
          "cross_mode_outcome": 0,
          "joint_policy_outcome": 0,
          "mode_root_edges": [
            0,
            0,
            0
          ]
        },
        "support_equal": true,
        "temporal": {
          "active_contexts": 1,
          "dynamics": [
            "static",
            "static"
          ],
          "scopes": [
            "shared_global",
            "shared_global"
          ]
        }
      },
      {
        "delivered_channels": [
          "contact",
          "context",
          "identity",
          "outcome",
          "partner"
        ],
        "intervention_probability": 1.0,
        "length": 3,
        "masked_likelihood": 1.0,
        "max_log_joint_error": 0.0,
        "structure": {
          "active_modes": 3,
          "cross_mode_outcome": 0,
          "joint_policy_outcome": 0,
          "mode_root_edges": [
            0,
            0,
            1
          ]
        },
        "support_equal": true,
        "temporal": {
          "active_contexts": 2,
          "dynamics": [
            "ordered_random_walk",
            "static"
          ],
          "scopes": [
            "cue_specific",
            "cue_specific"
          ]
        }
      },
      {
        "delivered_channels": [
          "contact",
          "context",
          "identity",
          "outcome",
          "partner"
        ],
        "intervention_probability": 1.0,
        "length": 3,
        "masked_likelihood": 1.0,
        "max_log_joint_error": 0.0,
        "structure": {
          "active_modes": 3,
          "cross_mode_outcome": 1,
          "joint_policy_outcome": 1,
          "mode_root_edges": [
            1,
            1,
            1
          ]
        },
        "support_equal": true,
        "temporal": {
          "active_contexts": 3,
          "dynamics": [
            "one_way_change",
            "one_way_change"
          ],
          "scopes": [
            "context_specific",
            "context_specific"
          ]
        }
      },
      {
        "delivered_channels": [
          "contact",
          "context",
          "identity",
          "outcome",
          "partner"
        ],
        "intervention_probability": 1.0,
        "length": 4,
        "masked_likelihood": 1.0,
        "max_log_joint_error": 0.0,
        "structure": {
          "active_modes": 1,
          "cross_mode_outcome": 0,
          "joint_policy_outcome": 0,
          "mode_root_edges": [
            0,
            0,
            0
          ]
        },
        "support_equal": true,
        "temporal": {
          "active_contexts": 1,
          "dynamics": [
            "static",
            "static"
          ],
          "scopes": [
            "shared_global",
            "shared_global"
          ]
        }
      },
      {
        "delivered_channels": [
          "contact",
          "context",
          "identity",
          "outcome",
          "partner"
        ],
        "intervention_probability": 1.0,
        "length": 4,
        "masked_likelihood": 1.0,
        "max_log_joint_error": 0.0,
        "structure": {
          "active_modes": 3,
          "cross_mode_outcome": 0,
          "joint_policy_outcome": 0,
          "mode_root_edges": [
            0,
            0,
            1
          ]
        },
        "support_equal": true,
        "temporal": {
          "active_contexts": 2,
          "dynamics": [
            "ordered_random_walk",
            "static"
          ],
          "scopes": [
            "cue_specific",
            "cue_specific"
          ]
        }
      },
      {
        "delivered_channels": [
          "contact",
          "context",
          "identity",
          "outcome",
          "partner"
        ],
        "intervention_probability": 1.0,
        "length": 4,
        "masked_likelihood": 1.0,
        "max_log_joint_error": 0.0,
        "structure": {
          "active_modes": 3,
          "cross_mode_outcome": 1,
          "joint_policy_outcome": 1,
          "mode_root_edges": [
            1,
            1,
            1
          ]
        },
        "support_equal": true,
        "temporal": {
          "active_contexts": 3,
          "dynamics": [
            "one_way_change",
            "one_way_change"
          ],
          "scopes": [
            "context_specific",
            "context_specific"
          ]
        }
      }
    ],
    "support_equal": true
  },
  "passed": true
}
```
