# Sealed stage challenge C-V2.1 — three channels with crossing reliability

**Sealed by evaluator before V2.1 development against its targets. Runs on the frozen V2.1 stage with zero new code.**

## Configuration
Three observation channels over one shared binary latent process:
- Channel A: starts calibrated-reliable, degrades to uninformative at the midpoint (true generating reliability crosses).
- Channel B: starts uninformative, becomes calibrated-reliable at the midpoint (mirror of A).
- Channel C: constant, locally confident but miscalibrated throughout (its own precision state is high while its likelihood is wrong).
Broadcast on in arm 1; broadcast severed (local monitoring only) in arm 2. No regime labels or change-point information is given to the agent.

## Tests (escrow block C-V21; 60 worlds per arm, paired streams)
1. **Tracking:** with broadcast on, the posterior over (λ_A, λ_B) crosses — A's inferred precision falls and B's rises, each side of the midpoint, in ≥ 48/60 worlds (direction, not magnitude, preregistered).
2. **Miscalibration containment:** channel C's contribution to the global state is down-weighted relative to its local confidence — the depth readout must NOT classify arm-1 worlds dominated by C as the calibrated-integrated regime in more than 6/60 worlds.
3. **Broadcast dissociation:** in arm 2, local precision posteriors per channel remain as calibrated as arm 1 (within CI overlap) while the global adjustment disappears — latent-state accuracy in the post-midpoint segment drops relative to arm 1 by a margin bounded away from zero (95% CI), because the reweighting toward B cannot propagate.
4. **No-label check:** an audit confirms nothing in the runner passes midpoint or regime information to inference.

Pass = 1–3 with 4 clean. Distinguishability of local fluency, global calibration, and cross-channel integration is the point; a failure of any single dissociation is reported as that dissociation's absence.
