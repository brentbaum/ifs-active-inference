# Experiment 48 magic numbers

Every authored semantic and implementation constant used by `ExilingEmergence` is listed. Numeric identities, collection indices, and machine arithmetic are not fitted constants.

| Constant | Value | Rationale |
|---|---:|---|
| `pilot_seeds` | `14801:14810` | Ten-world pilot namespace. |
| `confirmation_seeds` | `14851:14870` | Fresh, disjoint twenty-world namespace. |
| `episodes` | `64` | Matched observation budget for every registration arm. |
| `contact_attempt_rate` | `0.28` | Base-rate pressure from the vulnerable bundle. |
| `prior_aloneness_alpha` | `3.1` | Prior pseudo-count supporting 'alone with this'. |
| `prior_aloneness_beta` | `1.9` | Counterweight keeping the prior non-degenerate. |
| `rejection_evidence_reliability` | `0.78` | Likelihood that a registered suppressed attempt denotes rejection. |
| `failure_cost` | `1.0` | Common consequence cost for unreliable protection. |
| `favorable_direct_cost` | `0.18` | Low policy burden in a policy's favorable regime. |
| `unfavorable_direct_cost` | `0.64` | Higher burden outside a policy's favorable regime. |
| `favorable_reliability` | `0.91` | Reliable protection in the favorable regime. |
| `unfavorable_reliability` | `0.68` | Imperfect protection outside the favorable regime. |
| `cost_jitter_sd` | `0.025` | Authored between-world variation in direct costs. |
| `reliability_jitter_sd` | `0.02` | Authored between-world variation in reliability. |
| `probability_floor` | `0.02` | Numerical bound on jittered reliability. |
| `probability_ceiling` | `0.98` | Numerical bound on jittered reliability. |
| `static_epsilon` | `1.0e-12` | Pilot-frozen operational tolerance for a static prior. |
| `exclusion_favorable_threshold` | `16` | Spec §7.4 confirmatory lower bound. |
| `competitor_exclusion_ceiling` | `4` | Spec §7.4 confirmatory upper bound. |
| `policy_count` | `4` | The four protective policies named by spec §7.3. |
| `regime_seed_stride` | `1000` | Separates matched policy-regime random streams. |
| `contact_seed_offset` | `9000` | Separates contact attempts from policy parameters. |
| `bundle_normalization_tolerance` | `1.0e-12` | Floating-point structural-audit tolerance. |

The static tolerance was inspected on the pilot and frozen at `1.0e-12` before confirmation. No confirmatory result was available when it was frozen.
