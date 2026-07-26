# Sealed stage challenge C-V2.2 — the seam under alternation and anti-correlation

**Sealed by evaluator before V2.2 development against its targets. Runs on the frozen V2.2 stage with zero new code. This is the milestone's composition test: local precision → global depth → root evidence uptake → structural transfer, in a configuration never used in development.**

## Configuration
Six cues over one identity root G:
- Cue pairs constructed so perceptual similarity and root association are ANTI-correlated: cues 1–2 perceptually near-twins with only cue 1 root-associated; cues 3–4 perceptually dissimilar but both root-associated; cues 5–6 neither similar nor associated (floor controls). True structure generated per seed; the agent learns associations from developmental history (V2.2 machinery), never told them.
- Within each corrective episode, the precision regime ALTERNATES in segments: broad-calibrated → narrowed → broad (segment boundaries unannounced; the V2.1 machinery must infer them).
- Treatment delivered on cue 1 (root-associated) and cue 5 (not) in separate arms, corrective information matched by delivered predictive log-likelihood.

## Tests (escrow block C-V22; 60 worlds per arm)
1. **Structure recovery:** the learned association posterior separates root-associated from non-associated cues (AUC ≥ 0.85 across worlds) despite the anti-correlated perceptual similarity.
2. **Segment-gated uptake:** revision of G attributable (by the stage's frozen decomposition) to broad segments exceeds narrowed-segment attribution by a margin bounded away from zero; cue-level meaning revision proceeds in BOTH segment types (equivalence band).
3. **Transfer follows structure, not similarity:** after treating cue 1, untreated cue 3 and 4 (dissimilar, associated) change more than untreated cue 2 (similar, unassociated) in ≥ 48/60 worlds; after treating cue 5, no untreated cue changes beyond the floor band.
4. **Mediation:** worlds where G's posterior did not revise show no transfer (preregistered null band), whatever the segment structure — transfer has no root-free route.

Pass = all four. If the composition holds here, the seam is real; if it fails, the failure localizes (recovery vs gating vs transfer vs mediation) and that localization is the result.
