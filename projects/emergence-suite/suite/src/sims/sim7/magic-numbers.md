# Sim 7 R1 pilot constants

These values were frozen before the only permitted Step-A pilot (seeds
1001–1010). They are pilot-only and carry no confirmatory standing. No constant
was selected from Sim 7 R1 output when this table was written.

| Constant | Value | Provenance / debt |
| --- | ---: | --- |
| `adult_trials` | 48 | Design choice: enough chronic ordinary events to evolve the childhood bank without becoming another lifetime-scale formation epoch. |
| `adult_heldout_trials` | 12 | Sim 3-style frozen model-comparison segment; one quarter of the learned adult segment. |
| `therapy_sessions` | 96 | Inherited upper window from the de-authored Sim 4 pilot. |
| `posttherapy_heldout_trials` | 12 | Paired with the adult held-out segment for equal pre/post coverage. |
| `adult_adversity_probability` | 0.68 | Pilot-only world rate for chronic ordinary adversity. |
| `adult_trigger_every` | 6 | Pilot-only periodic trigger cadence; it changes the world schedule only. |
| `trigger_adversity_probability` | 0.90 | Pilot-only trigger severity contrast. |
| `posttherapy_safe_probability` | 0.82 | Pilot-only held-out post-therapy world rate; never visible to inference. |
| `adult_write_size` | 1.0 | Unit Dirichlet evidence event. |
| `witnessing_write_size` | 18.0 | Pilot-only scale debt. Chosen before running to make 96 graded Sim 4-access contacts commensurate with high-precision Sim 1-grown severity banks. |
| `therapy_safe_probability` | 0.92 | Matches the regulated therapist's coherent-channel reliability scale in Sim 5. |
| `capture_threshold` | 0.30 | Pilot-only behavioral readout for root-share × dangerous-belief capture. |
| `melt_capture_drop_threshold` | 0.08 | Pilot-only minimum absolute change judged substantively visible. |
| `carried_correlation_threshold` | -0.25 | Small-to-moderate negative association required from Sim 1 written reflexivity to adult capture. |
| `adult_capture_rate_threshold` | 0.60 | Majority-plus-one pilot prevalence. |
| `therapy_melt_rate_threshold` | 0.60 | Majority-plus-one pilot prevalence. |
| `h1_loglik_advantage_threshold` | 0.02 | Sim 3-scale nonzero out-of-sample advantage in nats per event. |
| `h1_win_rate_threshold` | 0.70 | Seven of ten paired seeds. |

Inherited Sim 1 probe constants, Sim 4 EFE/access constants, and Sim 5 learned
co-regulation constants are repeated in `configs/sim7.yaml` for auditability.
The two H models have no separate constants.
