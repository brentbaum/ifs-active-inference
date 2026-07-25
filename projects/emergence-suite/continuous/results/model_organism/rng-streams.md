# Frozen RNG stream definitions

Status: **frozen before the final Stage A package**.

All stochastic components use Julia `Xoshiro` with an integer seed derived from the externally visible world seed plus a genome-authored offset. The component offsets are:

| Component | Genome constant | Pairing rule |
|---|---|---|
| World observations | `rng_world_offset` | Recreated from the same seed in every paired arm. |
| Developmental history | `rng_history_offset` | Shared whenever arms require the same initial state. |
| Latent partner | `rng_partner_offset` | Generated once per seed × disposition and replayed across coupled/decoupled arms. |
| Precision field | `rng_field_offset` | Shared across field interventions. |
| Policy history | `rng_policy_offset` | Reserved for policy-specific history extensions; histories currently use the joint developmental stream. |
| Analysis/resampling | `rng_analysis_offset` | Reserved for interval/resampling code and never read by the agent. |

Generator-family and disposition substreams add `rng_substream_stride × frozen_index`. Indices are explicit tuple positions, never language hash values. Assay pilot blocks begin at `pilot_seed_base + assay × pilot_seed_assay_stride`; their count is `pilot_worlds`. The runner rejects a pilot block whose final seed is at or above `reserved_seed_floor = 700000`.

No confirmatory seed constructor or runner mode exists. Confirmatory seeds remain in evaluator escrow.
