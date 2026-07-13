# Global precision-field construction check: parameter ledger

This experiment was added after the v11 epistemic-depth definition changed.
It is an internal construction check, not a preregistered confirmatory run. Its
numbers show that the architecture can express the required dissociations; they
are not estimates of psychological or clinical effects.

| Quantity | Value | Role |
|---|---:|---|
| Seeds | `7101:7120` | Twenty independent observation-noise streams, matching the suite's usual sample size. |
| Hyper-prior marginal variance | `0.90` | Leaves each channel revisable from a neutral profile. |
| Cross-channel correlation | `0.35` | Minimal global sharing: an error in one precision forecast can update the rest of the field without making the channels identical. |
| Precise observation variance | `0.025–0.035` | Represents well-calibrated, broadly available evidence in the known-threat and scaffolded-contact constructions. |
| Default observation variance | `0.08` | Neutral inference probe. |
| Narrow-field observation variance | `1.80–2.40` | Represents poor access to errors on the precision forecast. It is paired with explicit channel unavailability rather than used as a synonym for threat. |
| Unavailable-channel variance | `1e6` | Removes a channel's direct error message while allowing indirect global updating through covariance. |
| Profile learning rate | `0.32` | Slow context-profile learning across twelve encounters; swept only by the no-learning ablation in this construction check. |
| Identity-root learning rate | `2.20` | Makes the twelve-session contrast legible. Its output is used only to compare arms, never as an effect-size claim. |
| Sessions / scaffolded sessions | `12 / 6` | Tests whether the learned field persists after dyadic evidence is removed halfway through. |

## Constructed regimes

The four log-precision profiles were chosen to occupy the four cells of the
dominance-by-depth table in §7: blended capture, known urgent threat, quiet
narrowing, and Self-led witnessing. Classification thresholds are deliberately
coarse (`dominance` around `0.4/0.6`, `depth` around `0.4/0.75`) and are tested
only as construction invariants.

## Ablations

- `no_profile_learning`: freezes the context-conditioned hyper-prior.
- `local_only`: removes off-diagonal covariance while retaining all local
  precision inference.
- `inverted_broadcast`: learns the posterior but reverses the sign of every
  predicted log precision before downward broadcast. This deliberately severe
  intervention checks that posterior confidence without broadcast calibration
  does not score as epistemic depth.

The required ablation margins are `0.40` for global sharing and `0.20` for
broadcast calibration. They are coarse construction thresholds, chosen to be
well below the full separation rather than interpreted as empirical effects.
