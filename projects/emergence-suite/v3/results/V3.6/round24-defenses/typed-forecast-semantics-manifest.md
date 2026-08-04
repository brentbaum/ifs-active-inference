# Typed Forecast Semantics Manifest

```json
{
  "adapter_checks": {
    "v2": {
      "contact": {
        "normalization_error": 0.0,
        "observable_suffix_count": 16,
        "target_name_equal": true,
        "vector_count": 16
      },
      "context": {
        "normalization_error": 3.3306690738754696e-16,
        "observable_suffix_count": 16,
        "target_name_equal": true,
        "vector_count": 16
      },
      "identity": {
        "normalization_error": 0.0,
        "observable_suffix_count": 16,
        "target_name_equal": true,
        "vector_count": 16
      },
      "outcome": {
        "normalization_error": 0.0,
        "observable_suffix_count": 16,
        "target_name_equal": true,
        "vector_count": 16
      },
      "partner": {
        "normalization_error": 0.0,
        "observable_suffix_count": 16,
        "target_name_equal": true,
        "vector_count": 16
      }
    },
    "v3": {
      "contact": {
        "normalization_error": 0.0,
        "observable_suffix_count": 16,
        "target_name_equal": true,
        "vector_count": 16
      },
      "context": {
        "normalization_error": 0.0,
        "observable_suffix_count": 16,
        "target_name_equal": true,
        "vector_count": 16
      },
      "identity": {
        "normalization_error": 0.0,
        "observable_suffix_count": 16,
        "target_name_equal": true,
        "vector_count": 16
      },
      "outcome": {
        "normalization_error": 0.0,
        "observable_suffix_count": 16,
        "target_name_equal": true,
        "vector_count": 16
      },
      "partner": {
        "normalization_error": 0.0,
        "observable_suffix_count": 16,
        "target_name_equal": true,
        "vector_count": 16
      }
    }
  },
  "bridge_proof_15": {
    "delivered_counts": {
      "contact": 16,
      "context": 15,
      "identity": 16,
      "outcome": 16,
      "partner": 16
    },
    "forecast_semantics_error_max": 0.0,
    "forecast_semantics_errors": {
      "v2": {
        "contact": 0.0,
        "context": 0.0,
        "identity": 0.0,
        "outcome": 0.0,
        "partner": 0.0
      },
      "v3": {
        "contact": 0.0,
        "context": 0.0,
        "identity": 0.0,
        "outcome": 0.0,
        "partner": 0.0
      }
    },
    "normalization_error_max": 3.3306690738754696e-16,
    "passed": true,
    "proofs": {
      "01_canonical_document_identity": true,
      "02_target_token_identity": true,
      "03_mask_identity": true,
      "04_equal_delivered_target_counts": true,
      "05_no_sentinel_counted": true,
      "06_deterministic_zero_rng_adapters": true,
      "07_normalized_shared_predictions": true,
      "08_target_unavailable_before_prediction": true,
      "09_native_structural_prior_included": true,
      "10_truth_clamped_recombination": true,
      "11_no_exclusive_channel_in_primary": true,
      "12_one_v2_module_per_target": true,
      "13_bridge_input_copying": true,
      "14_scientific_source_bitwise_unchanged": true,
      "15_forecast_semantics_identity_all_five_targets": true
    },
    "recombination_error_max": 0.0,
    "source_hashes": {
      "v2/protocols/v2.3.2-formation-parameters.json": "d1e3b7e329682802c72d8a35e2e53a18ae259e34cfb6800b899a794342d50d91",
      "v2/protocols/v2.3.4-parameters.json": "3dd0851363133a77c0e4433b5b41ba1e2fdaaaaa1f2973f7a579c2a8635c3c68",
      "v2/protocols/v2.4-parameters.json": "94972204bdb406f3d5ff8a8aa2df3f8577f4a71dc0032a79c75990ada6455fde",
      "v2/protocols/v2.6a-parameters.json": "3d4a2c4643d78c5167a8a763037051f940e379787f700a1804cc9d1d8533bb24",
      "v2/protocols/v2.6b-parameters.json": "2403f587f665ef313a1383194a5271e49c67ee9d2cb222a29c85b33b6b61f2ca",
      "v2/ref/v232_formation.py": "499e0688a114ce86ac67878c8d1e986596e2cd3a54fa1ebe3c9d4b7917a03b0e",
      "v2/ref/v234.py": "2110c07ad3c7495e44955486da7695450c9560eadacef4eb1cfddcd034ac1c1d",
      "v2/ref/v24.py": "9efb9654308ca3f558b9b098cea733265ea263819278c36320413d30638633a8",
      "v2/ref/v26a.py": "e7d4284847257353f4bfbfe0122425702449080162bdba7b4c24736e9e62db63",
      "v2/ref/v26b.py": "3752bc019ffa5e460afb40289bd56d53418156dbe0b2f4c04a9aa5f64335a998",
      "v3/ref/v31.py": "0481e51acf72ee8018cb3c9a1c780570b22e05657cc687376f08ca99544149e0",
      "v3/ref/v32.py": "0b990eb4c28f3dd61ec37b57742548c1f63147ec48fe8fac465cf2123dba9833",
      "v3/ref/v33.py": "018ebac662a925a3ed5431197d8c5914049fa5e1b20787fd5b13de3310c977fd",
      "v3/ref/v34.py": "f9a37a36a0393f9fd437776457cc48018db6cfe1d5195d95a9cbf5b2e90744cd",
      "v3/ref/v35.py": "7b71e5a7c8003d27c7f1bcafc8deae2d2eed07dd80942066362a1d9c5da8c264",
      "v3/ref/v36.py": "99fe821485b8112e84ab3fe2ea45f73bf8055be22003982089a135eb07f4dc72"
    }
  },
  "passed": true,
  "targets": {
    "contact": {
      "conditioned": {
        "action": "intervention",
        "contact response parameter": "latent"
      },
      "forecast": "contact-response token",
      "target_type": "observable"
    },
    "context": {
      "conditioned": {
        "None": "mask",
        "context_input": "metadata"
      },
      "forecast": "delivered context marker",
      "target_type": "observable"
    },
    "identity": {
      "conditioned": {
        "action": "intervention",
        "modes_input": "metadata"
      },
      "forecast": "identity token",
      "target_type": "observable"
    },
    "outcome": {
      "conditioned": {
        "action": "intervention",
        "joint_policy": "intervention"
      },
      "forecast": "outcome token under same do(action)",
      "target_type": "observable"
    },
    "partner": {
      "conditioned": {
        "partner state": "latent"
      },
      "forecast": "partner-response token",
      "target_type": "observable"
    }
  },
  "typed_fields": {
    "intervention": [
      "action",
      "joint_policy"
    ],
    "latent": [
      "structure",
      "temporal_path",
      "partner_state",
      "contact_parameter"
    ],
    "mask": [
      "context=None"
    ],
    "metadata": [
      "stratum",
      "cue",
      "time",
      "modes_input",
      "context_input"
    ],
    "observable": [
      "identity",
      "outcome",
      "context",
      "partner",
      "contact"
    ]
  }
}
```
