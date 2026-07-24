# Experiment 49 magic numbers

Every Experiment 49 semantic, calibration, and implementation constant is listed below. Dyad constants reproduce the load-bearing committed Sim 5 mapping→depth→effective-precision path. The nested Experiment 47 and 48 configs are reused unchanged and remain enumerated in their own committed magic-number records.

| Constant | Value | Rationale |
|---|---:|---|
| `pilot_seeds` | `[34901, 34902, 34903, 34904, 34905, 34906, 34907, 34908, 34909, 34910]` | Ten-world pilot namespace following Experiments 47–48. |
| `confirmation_seeds` | `[34951, 34952, 34953, 34954, 34955, 34956, 34957, 34958, 34959, 34960, 34961, 34962, 34963, 34964, 34965, 34966, 34967, 34968, 34969, 34970]` | Fresh, disjoint twenty-world namespace. |
| `episodes` | `18` | Moderate common dyad and witnessing evidence budget. |
| `dyad_depth_grid` | `[0.0, 0.25, 0.5, 0.75, 1.0]` | Committed Sim 5 categorical depth support. |
| `dyad_baseline_prior` | `[0.18, 0.22, 0.24, 0.22, 0.14]` | Committed Sim 5 dyad baseline depth prior. |
| `dyad_transition_mix` | `0.08` | Committed Sim 5 transition floor toward the dyad prior. |
| `dyad_mapping_prior_count` | `1.0` | Committed Sim 5 uniform count for each signal-outcome row. |
| `dyad_mapping_learning_rate` | `1.0` | Committed Sim 5 count increment per observed contingency. |
| `dyad_mapping_settle_probability` | `[0.9, 0.6, 0.64, 0.1]` | Committed Sim 5 signal-to-settling contingencies. |
| `dyad_surface_coherent_probability` | `0.92` | Committed Sim 5 regulated surface emission. |
| `dyad_channel_safe_probability` | `0.9` | Committed Sim 5 regulated relational-channel emission. |
| `dyad_regulated_by_depth` | `[0.08, 0.16, 0.36, 0.74, 0.93]` | Committed Sim 5 co-regulation likelihood over depth. |
| `dyad_activation_drive` | `0.86` | Committed Sim 5 bundle-live activation strength. |
| `dyad_activation_jitter` | `0.04` | Committed Sim 5 deterministic arousal variation. |
| `dyad_volatility_precision` | `1.35` | Committed Sim 5 volatility-likelihood precision. |
| `dyad_coreg_precision` | `2.35` | Committed Sim 5 co-regulation likelihood precision. |
| `dyad_part_precision` | `4.0` | Committed Sim 5 base part precision. |
| `dyad_context_precision` | `0.9` | Committed Sim 5 base context precision. |
| `dyad_part_slope` | `1.0` | Committed Sim 5 depth-to-part precision slope. |
| `dyad_context_slope` | `1.15` | Committed Sim 5 depth-to-context precision slope. |
| `evidence_packet_mass` | `1.0` | One normalized relational-field unit supports one TrustEvidence packet per route. |
| `tolerated_true_probability` | `0.82` | Independent tolerated-outcome evidence generator. |
| `competence_true_probability` | `0.84` | Independent co-protection evidence generator. |
| `remaining_true_probability` | `0.9` | Independent partner-response evidence generator. |
| `permission_threshold` | `0.5` | Predeclared operational definition of protector permission rising. |
| `root_prior_positive` | `0.06` | Experiment 44 frozen-negative identity-root prior. |
| `root_revision_begun_probability` | `0.62` | Experiment 44 operational definition of revision beginning. |
| `root_revision_probability` | `0.8` | Experiment 44 operational definition of completed revision. |
| `witnessing_precision` | `0.38` | Moderate tempering of the committed bundle likelihood ratio. |
| `contact_required` | `16` | Spec §8.5 coupled confirmatory threshold. |
| `control_contact_ceiling` | `2` | Spec §8.5 no-dyad and decoupled ceiling. |
| `protector` | `Experiment 47 frozen config` | Unmodified committed Experiment 47 config. |
| `vulnerable` | `Experiment 48 frozen config` | Unmodified committed Experiment 48 config. |
| `root_stream_offset` | `49000` | Separates witnessing configurations from world jitter. |
| `dyad_regulated_emission_xor` | `20903` | Committed Sim 5 regulated-emission RNG namespace. |
| `dyad_volatility_likelihood` | `[0.06 0.1 0.2 0.42 0.62; 0.18 0.22 0.28 0.3 0.25; 0.3 0.3 0.26 0.17 0.09; 0.28 0.24 0.18 0.08 0.03; 0.18 0.14 0.08 0.03 0.01]` | Committed Sim 5 five-state volatility likelihood. |
| `trust_stream_offset` | `147000` | Separates protector evidence signs from dyad learning and witnessing. |
| `inferential_arm_count` | `3` | Coupled, no-dyad, and decoupled gate arms. |
| `authored_calibration_count` | `1` | Historical comparator isolated from inferential success. |

The final fidelity-corrected calibration above was declared before `34901:34910` was opened. It was not strengthened in response to pilot or confirmatory outcomes. Two architecturally invalid attempts are retained under `invalidated-attempt-1/` and `invalidated-attempt-2/`; neither is evidence for Experiment 49.
