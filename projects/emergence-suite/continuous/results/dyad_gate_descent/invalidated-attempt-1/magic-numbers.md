# Experiment 49 magic numbers

Every Experiment 49 semantic, calibration, and implementation constant is listed below. The nested Experiment 47 and 48 configs are reused unchanged and remain enumerated in their own committed magic-number records.

| Constant | Value | Rationale |
|---|---:|---|
| `pilot_seeds` | `14901:14910` | Ten-world pilot namespace following Experiments 47–48. |
| `confirmation_seeds` | `14951:14970` | Fresh, disjoint twenty-world namespace. |
| `episodes` | `12` | Moderate common dyad and witnessing evidence budget. |
| `dyad_alpha_prior` | `2.0` | Symmetric two-success pseudo-count precision prior. |
| `dyad_beta_prior` | `2.0` | Symmetric two-failure pseudo-count precision prior. |
| `dyad_safe_probability` | `0.82` | Moderate co-regulation success generator, fixed before pilot. |
| `dyad_world_jitter_sd` | `0.05` | Between-world variation shared by coupled and decoupled arms. |
| `dyad_probability_floor` | `0.68` | Prevents degenerate always-failing dyad worlds. |
| `dyad_probability_ceiling` | `0.92` | Prevents degenerate always-successful dyad worlds. |
| `evidence_packet_mass` | `1.0` | One posterior-precision unit supports one TrustEvidence packet. |
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
| `dyad_stream_offset` | `98000` | Separates dyad observations from world and witnessing streams. |
| `inferential_arm_count` | `3` | Coupled, no-dyad, and decoupled gate arms. |
| `authored_calibration_count` | `1` | Historical comparator isolated from inferential success. |

The single moderate calibration above was declared before `14901:14910` was opened. It was not strengthened in response to pilot or confirmatory outcomes.
