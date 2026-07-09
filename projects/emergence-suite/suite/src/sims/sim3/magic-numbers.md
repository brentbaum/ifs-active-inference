# Sim 3 Magic Numbers

Every hand-set constant in `src/sims/sim3/` is listed here with its status.

| Constant | Value | Status | Rationale |
|---|---:|---|---|
| `n_training_trials` | 20 | derivation | Carried from v10 Sim 3, enough for stable treated-cue learning while keeping matched protocols short. |
| `n_probe_trials` | 1 | derivation | The first untreated probe is the clean discriminant before repeated probing can itself become exposure. |
| Seeds per condition | 24 | derivation | Exceeds the T1.1 minimum of 20 seeds per condition. |
| `high_E` | 0.85 | derivation | Carried from v10 witnessing condition; high point on the D1 log-precision tilt. |
| `low_E` | 0.15 | derivation | Carried from v10 exposure/capture condition; matched low-depth comparator. |
| Training parity epsilon | 0.05 nats | IOU | Strict enough to catch training-fit confounding; should be narrowed after a formal likelihood-calibration derivation. |
| Root-sharing cue root couplings | `[1.0, 0.8, 0.6, 0.4, 0.2]` | derivation | K=5 structural continuum required by T1.1, evenly spaced coupling to the trained cue's self-state root. |
| Root-sharing cue perceptual similarities | `[1.0, 0.35, 0.2, 0.7, 0.45]` | derivation | Hand-set decorrelated feature-overlap values so perceptual similarity and structural similarity are visibly independent. |
| Structural-confound cue attributes | perceptual similarity `0.9`, root coupling `0.0`, root id `2` | derivation | Perceptually near the trained cue while root-distant for A3.2. |
| Perceptual generalization channel | none | derivation | The T1.1 redesign permits no conventional feature-overlap channel; transfer is tested as root-conditioned structural transfer only. |
| E sweep grid | 0.05:0.10:0.95 | sweep | Covers low, transition, and high depth readout with ten points and no fitted control surface in the model. |
| `pi_part` | 3.6 | derivation | Carried from v10 Sim 3 as the structural-prior log-precision intercept. |
| `beta_se` | 1.0 | derivation | D1 slope from depth to bundle-prior log-precision, matching v10 scale. |
| `lambda_self` | 0.7 | derivation | Carried from v10 Sim 3 as the relational evidence log-precision intercept. |
| `gamma_se` | 1.2 | derivation | D1 slope from depth to relational-evidence log-precision, matching v10 scale. |
| `eta_self` | 1.0 | derivation | Carried from v10 Sim 3 shared-bank learning rate. |
| `eta_threat` | 1.6 | derivation | Carried from v10 Sim 3 cue-local learning rate. |
| `self_to_threat_coupling` | 1.35 | derivation | Carried from v10 Sim 3 root-to-threat within-trial influence. |
| `h2_threat_to_self_coupling` | 1.35 | derivation | Mirrors the H1 coupling magnitude in the reversed-root architecture while reversing the conditioning direction. |
| `outcome_precision` | 1.6 | derivation | Carried from v10 Sim 3 outcome update precision. |
| `policy_precision` | 3.2 | derivation | Carried from v10 Sim 3 policy-selection precision. |
| `threat_policy_weight` | 2.4 | derivation | Carried from v10 Sim 3 threat contribution to policy EFE. |
| `contact_self_bias` | 0.08 | derivation | Carried from v10 Sim 3 small root-state contribution to contact. |
| `avoid_bias` | 0.03 | derivation | Carried from v10 Sim 3 small root-state contribution to avoid. |
| Outcome utilities | `[-2.4, 1.4, -0.15, 0.20]` | derivation | Carried from v10 Sim 3 contact/avoid outcome preferences. |
| Initial `d_self` | `[18.0, 2.0]` | derivation | Carried from v10 Sim 3 helpless-biased self-state prior. |
| Initial `d_threat(c)` | `[17.0, 3.0]` | derivation | Carried from v10 Sim 3 dangerous-biased threat prior. |
| Relational truthfulness | 0.88 | derivation | Relational modality is always on and truthful; value carried from v10 reliability. |
| Outcome reliabilities | `[0.96, 0.08, 0.97, 0.78]` | derivation | Carried from v10 Sim 3 safe/danger contact/avoid outcome model. |
| First-passage threshold | 0.60 | IOU | Chosen as a modest posterior crossing above indifference; should be swept after T1.1. |
| Policy first-passage threshold | 0.60 | IOU | Same crossing convention for contact probability. |
| Shape readout minimum range | 0.20 | IOU | Requires visible transfer-vs-depth change before the emergent threshold shape can receive full support. |
