# Proof Dependency Scope Ledger

```json
{
  "defenses_learned_from_failures": [
    {
      "failure_class": "truth-dependent schedule",
      "permanent_defense": "candidate-common schedule equality + full-path identity"
    },
    {
      "failure_class": "latent posterior used as forecast",
      "permanent_defense": "typed forecast-semantics manifest"
    },
    {
      "failure_class": "oracle key collapse",
      "permanent_defense": "key-set equality and triangulation"
    },
    {
      "failure_class": "log-evidence underflow",
      "permanent_defense": "log-space support predicates"
    },
    {
      "failure_class": "non-picklable worker row",
      "permanent_defense": "serialization round-trip"
    },
    {
      "failure_class": "order-sensitive implementation",
      "permanent_defense": "metamorphic invariance"
    }
  ],
  "proofs": [
    {
      "dependent_batteries": [
        "all native recovery",
        "external calibration",
        "T-V3-DO2"
      ],
      "files_functions": [
        "ref/v36_round12.py::generate_v3_native_world",
        "ref/v36_round12.py::generate_external_world",
        "ref/v35.py::_slice_likelihood",
        "ref/v32.py::emission_probability"
      ],
      "invalidated_by": [
        "generator",
        "prior",
        "likelihood",
        "mask",
        "intervention schedule"
      ],
      "premise": "worlds and score law share a normalized joint",
      "proof": "full_path_generator_scorer_identity",
      "scope": "full-path staged T=1..4"
    },
    {
      "dependent_batteries": [
        "common-target tournaments"
      ],
      "files_functions": [
        "ref/v36_bridge.py::score_v2",
        "ref/v36_bridge.py::score_v3"
      ],
      "invalidated_by": [
        "adapter",
        "target schema",
        "forecast query"
      ],
      "premise": "adapter predicts requested observable, not latent proxy",
      "proof": "typed_forecast_semantics",
      "scope": "enumerable dummy plus all five targets"
    },
    {
      "dependent_batteries": [
        "Population A/B/C"
      ],
      "files_functions": [
        "ref/v36_fixture_oracle.py",
        "ref/v36_bridge_oracle.py"
      ],
      "invalidated_by": [
        "fixture",
        "channel mapping",
        "CPT"
      ],
      "premise": "production and independent atom enumerator agree",
      "proof": "fixture_identity_and_triangulation",
      "scope": "dummy T=2"
    },
    {
      "dependent_batteries": [
        "native calibration"
      ],
      "files_functions": [
        "ref/v36_round12.py::generate_v3_native_world"
      ],
      "invalidated_by": [
        "schedule constructor",
        "truth-dependent branch"
      ],
      "premise": "interventions do not read candidate truth",
      "proof": "candidate_common_schedule",
      "scope": "all candidate structures"
    },
    {
      "dependent_batteries": [
        "every parallel block"
      ],
      "files_functions": [
        "runner worker rows"
      ],
      "invalidated_by": [
        "row schema",
        "nested type"
      ],
      "premise": "worker row survives IPC without semantic change",
      "proof": "serialization_roundtrip",
      "scope": "exact dummy row type"
    },
    {
      "dependent_batteries": [
        "lesions",
        "manifest verification"
      ],
      "files_functions": [
        "V3.6 verifier helpers"
      ],
      "invalidated_by": [
        "atom key",
        "support predicate"
      ],
      "premise": "oracle coordinates complete; support predicates underflow-safe",
      "proof": "key_set_and_log_space",
      "scope": "full candidate atoms"
    },
    {
      "dependent_batteries": [
        "all V3.6 scoring"
      ],
      "files_functions": [
        "ref/v35.py",
        "ref/v36_bridge.py"
      ],
      "invalidated_by": [
        "slot semantics",
        "candidate aggregation",
        "unordered reduction"
      ],
      "premise": "incidental labels/orders do not change science",
      "proof": "metamorphic_invariance",
      "scope": "enumerable dummy"
    }
  ]
}
```
