# Sealed stage challenge C-V22b — the seam, second attempt: graded structure and the floor

**Sealed by evaluator after C-V22's FAIL, before any V2.2.1 development. Runs on the frozen V2.2.1 stage with zero new code. C-V22 is burned; this is a different configuration family testing the same seam plus the localized defect (soft-zero leakage).**

## Configuration
Eight cues over one root G. Per seed, true association strengths are GRADED: two strong, two weak, four exactly zero. Perceptual similarity assigned adversarially as in C-V22 (a zero-association cue is the perceptual near-twin of a strong one). Developmental history length varies across worlds over three preregistered tiers (short/medium/long). Two-segment precision structure (broad → narrowed), boundaries unannounced. Treatment arms: one strong-association cue; one exactly-zero cue.

## Tests (escrow block C-V22b, seeds 806117:806416; 60 worlds per arm; paired streams)
1. **Graded transfer:** across worlds, untreated-cue response to strong-cue treatment rank-correlates with the posterior association magnitude (Spearman ≥ 0.6, CI excluding 0); strong > weak > zero ordering in ≥ 45/60 worlds.
2. **Floor with dose-response:** G revision from treating the zero cue shrinks as developmental history lengthens — monotone across the three tiers, and within the floor band in ≥ 48/60 of LONG-tier worlds. This separates "correct Bayesian soft zero under scarce data" (acceptable, must show the dose-response) from "miscalibrated non-association" (defect, flat in history length).
3. **Mediation, unchanged:** no root-free transfer; worlds without G revision show no transfer (null band).
4. **Segment gating, unchanged:** broad-segment attribution exceeds narrowed (margin bounded from zero); cue-level revision proceeds in both.

Pass = all four. Test 2's dose-response clause is the heart: if the leak is real Bayesian humility about finite data, long histories must close it; if it persists at long histories, the calibration defect stands and V2.2.1 has not fixed it.
