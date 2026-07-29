# Sealed challenge C-V2G0 — apparatus challenge for the compositional grammar

**Sealed by the evaluator after R0 gates 1-5 and the escrow-authorization amendment (75520bd), with the pre-seal linter record committed first (results/R0/c-v2g0-preseal-linter-record.md). Apparatus only; no scientific model-performance criterion. One run.**

## Cells (125 escrow seeds each, consumed ascending)
Each cell below is the exact world/protocol document pair. Cell D runs through `run_bridge` with the declared initial_state; cells A-C run `compile_world`/`sample_world`/`run_protocol`.

```json
{
 "cell_a": {
  "world": {
   "stage_version": "V2.G0",
   "name": "cva-subset-drift-windowed-cp",
   "processes": [
    {
     "name": "identity-drift",
     "kind": "ordered_drift",
     "scope": [
      "cue:0"
     ],
     "length": 8,
     "states": [
      0,
      1,
      2
     ],
     "initial": [
      0.4,
      0.3,
      0.3
     ],
     "transition": {
      "0": [
       0.7,
       0.3,
       0.0
      ],
      "1": [
       0.15,
       0.7,
       0.15
      ],
      "2": [
       0.0,
       0.3,
       0.7
      ]
     }
    },
    {
     "name": "stable-cues",
     "kind": "static",
     "scope": [
      "cue:1",
      "cue:2"
     ],
     "length": 8,
     "values": [
      "low",
      "high"
     ],
     "probabilities": [
      0.5,
      0.5
     ]
    },
    {
     "name": "regime-shift",
     "kind": "change_point",
     "scope": [
      "latent:regime"
     ],
     "length": 8,
     "before": "old",
     "after": "new",
     "onset_probabilities": {
      "no_change": 0.15,
      "1": 0.1,
      "2": 0.15,
      "3": 0.15,
      "4": 0.15,
      "5": 0.15,
      "6": 0.15
     },
     "onset_window": [
      2,
      5
     ],
     "allow_no_change": false
    }
   ]
  },
  "protocol": {
   "stage_version": "V2.G0",
   "name": "cva-protocol",
   "actions": [],
   "observation_channels": [
    {
     "name": "drift-obs",
     "source_process": "identity-drift"
    },
    {
     "name": "stable-obs",
     "source_process": "stable-cues"
    },
    {
     "name": "regime-obs",
     "source_process": "regime-shift"
    }
   ]
  },
  "escrow": "2000000:2000124"
 },
 "cell_b": {
  "world": {
   "stage_version": "V2.G0",
   "name": "cvb-recurrent-shared",
   "processes": [
    {
     "name": "context-broadcast",
     "kind": "shared_latent",
     "scope": [
      "cue:0",
      "cue:1"
     ],
     "latent": {
      "name": "then-now",
      "kind": "recurrent_context",
      "scope": [
       "latent:context"
      ],
      "length": 12,
      "states": [
       "then",
       "now"
      ],
      "initial": [
       0.8,
       0.2
      ],
      "transition": {
       "then": [
        0.75,
        0.25
       ],
       "now": [
        0.3,
        0.7
       ]
      },
      "restriction": {
       "at_least_one_switch": true,
       "old_context_recurrence": true,
       "minimum_visits": {
        "then": 3,
        "now": 2
       }
      }
     },
     "targets": [
      "cue:0",
      "cue:1"
     ]
    }
   ]
  },
  "protocol": {
   "stage_version": "V2.G0",
   "name": "cvb-protocol",
   "actions": [],
   "observation_channels": [
    {
     "name": "cue0-obs",
     "source_process": "context-broadcast",
     "path": [
      "targets",
      "cue:0"
     ]
    },
    {
     "name": "cue1-obs",
     "source_process": "context-broadcast",
     "path": [
      "targets",
      "cue:1"
     ]
    }
   ]
  },
  "escrow": "2000125:2000249"
 },
 "cell_c": {
  "world": {
   "stage_version": "V2.G0",
   "name": "cvc-mixture-masked-episodes",
   "processes": [
    {
     "name": "regime-mixture",
     "kind": "mixture",
     "scope": [
      "cue:mixed"
     ],
     "length": 6,
     "weights": [
      0.6,
      0.4
     ],
     "components": [
      {
       "name": "steady",
       "kind": "markov",
       "scope": [
        "cue:mixed"
       ],
       "length": 6,
       "states": [
        "calm",
        "tense"
       ],
       "initial": [
        0.5,
        0.5
       ],
       "transition": {
        "calm": [
         0.8,
         0.2
        ],
        "tense": [
         0.2,
         0.8
        ]
       }
      },
      {
       "name": "drifting",
       "kind": "ordered_drift",
       "scope": [
        "cue:mixed"
       ],
       "length": 6,
       "states": [
        0,
        1,
        2
       ],
       "initial": [
        1.0,
        0.0,
        0.0
       ],
       "transition": {
        "0": [
         0.6,
         0.4,
         0.0
        ],
        "1": [
         0.2,
         0.6,
         0.2
        ],
        "2": [
         0.0,
         0.4,
         0.6
        ]
       }
      }
     ]
    },
    {
     "name": "episodes",
     "kind": "joint_episode",
     "scope": [
      "observation:joint"
     ],
     "length": 6,
     "channels": [
      "marker",
      "outcome"
     ],
     "episodes": [
      {
       "marker": "safe",
       "outcome": 1
      },
      {
       "marker": "safe",
       "outcome": 0
      },
      {
       "marker": "danger",
       "outcome": 0
      },
      {
       "marker": "danger",
       "outcome": 1
      }
     ],
     "probabilities": [
      0.4,
      0.2,
      0.3,
      0.1
     ]
    },
    {
     "name": "availability",
     "kind": "masked_observation",
     "scope": [
      "nuisance:mask"
     ],
     "length": 6,
     "availability": 0.75,
     "candidate_common": true
    }
   ]
  },
  "protocol": {
   "stage_version": "V2.G0",
   "name": "cvc-protocol",
   "actions": [],
   "observation_channels": [
    {
     "name": "mixed-obs",
     "source_process": "regime-mixture"
    },
    {
     "name": "episode-obs",
     "source_process": "episodes",
     "masked_by": "availability"
    }
   ]
  },
  "escrow": "2000250:2000374"
 },
 "cell_d": {
  "world": {
   "stage_version": "V2.G0",
   "name": "cvd-drift-bridge",
   "processes": [
    {
     "name": "drift-family",
     "kind": "ordered_drift",
     "scope": [
      "cue:0"
     ],
     "length": 6,
     "states": [
      0,
      1,
      2
     ],
     "initial": [
      0.2,
      0.6,
      0.2
     ],
     "transition": {
      "0": [
       0.7,
       0.3,
       0.0
      ],
      "1": [
       0.15,
       0.7,
       0.15
      ],
      "2": [
       0.0,
       0.3,
       0.7
      ]
     }
    },
    {
     "name": "approach-response",
     "kind": "action_contingent",
     "scope": [
      "latent:response"
     ],
     "length": 6,
     "states": [
      "guarded",
      "open"
     ],
     "initial": [
      0.7,
      0.3
     ],
     "actions": [
      "hold",
      "approach",
      "approach",
      "hold",
      "approach"
     ],
     "transitions_by_action": {
      "hold": {
       "guarded": [
        0.9,
        0.1
       ],
       "open": [
        0.4,
        0.6
       ]
      },
      "approach": {
       "guarded": [
        0.6,
        0.4
       ],
       "open": [
        0.1,
        0.9
       ]
      }
     }
    }
   ]
  },
  "protocol": {
   "stage_version": "V2.G0",
   "name": "cvd-protocol",
   "actions": [
    "hold",
    "approach",
    "approach",
    "hold",
    "approach"
   ],
   "observation_channels": [
    {
     "name": "drift-obs",
     "source_process": "drift-family"
    },
    {
     "name": "response-obs",
     "source_process": "approach-response"
    }
   ]
  },
  "initial_state": {
   "banked": true,
   "root_belief": [
    0.35,
    0.65
   ]
  },
  "bridge": true,
  "escrow": "2000375:2000499"
 }
}
```

## Criteria
1. *(scientific-apparatus)* Every cell compiles after reveal with zero source-code change; every escrow seed samples; `run_protocol`/`run_bridge` complete for all 500 world-runs.
2. *(scientific-apparatus)* Independent log-probability parity: `independent_world_log_prob` agrees with `log_prob_world` within 1e-10 for every sampled truth trace; restriction normalizers published for cells A (onset window) and B (path restriction) agree with the independent oracle within 1e-10.
3. *(semantic)* Output schema hashes are constant per cell across seeds; every trace carries spec hashes, scopes, component RNG keys; `scientific_scores_inspected` fields absent from run traces (dry-run-only flag).
4. *(custody)* Escrow released by data commit only; seeds consumed once, ascending, gap-free ledger; no diagnosis-reserved seed touched; verdict classes reported.

Pass = all four. Failure interpretations, pre-committed: a criterion-1 failure is a grammar executability defect (the R0 exit condition fails; V2.5a master-spec seal blocked); criterion-2 failure is an exactness defect in the compiler or oracle; criterion-3/4 failures are semantic/custody defects. Software errors follow invalidate-and-repeat with byte identity.
