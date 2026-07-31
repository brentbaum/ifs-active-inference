# V3.6 Gate 1 plan-fidelity addendum

Verdict: **PASS**.

```json
{
  "authorization": "results/V3.6/stage0-adjudication.md",
  "gate": "1-adjudicated-plan-fidelity",
  "proofs": {
    "fresh_block_declared": true,
    "post_revision_equivalence_retained": true,
    "post_revision_schedule_follows_observed_boundary": true,
    "premature_declared_positive_causal_effect": true,
    "premature_schedule_follows_moving_boundary": true,
    "retained_gate1_pass": true
  },
  "schedule_fixtures": {
    "post_revision_boundary_11": {
      "event_indexed": true,
      "post_revision_times": [
        12,
        13,
        14
      ],
      "premature_times": [],
      "root_revision_event": 11
    },
    "premature_boundary_19": {
      "event_indexed": true,
      "post_revision_times": [],
      "premature_times": [
        16,
        17,
        18
      ],
      "root_revision_event": 19
    },
    "premature_boundary_7": {
      "event_indexed": true,
      "post_revision_times": [],
      "premature_times": [
        4,
        5,
        6
      ],
      "root_revision_event": 7
    }
  },
  "seed_consumption": [],
  "stage": "V3.6",
  "verdict": "PASS"
}
```
