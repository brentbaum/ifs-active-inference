# V2.6a gate-2 apparatus-repair authorization (evaluator, 2026-07-29)

Classification: gate apparatus defect, two components, per the committed diagnosis: (1) the recovery generator does not draw from the scorer's generative process (deterministic family cycling; forced single switch at slice 32; deterministic destination — vs the frozen Markov stay-.94 process), voiding the calibration theorem the gate exists to exercise; (2) the calibration statistic treats posterior time-occupancy as confidence in a world-level majority label — a category mismatch that manufactures apparent underconfidence. Recovery accuracy (0.993) and coverage (1.0) are unaffected constructs and stand.

Authorized, narrowly:
1. The repaired gate-2 generator samples worlds FROM the frozen scorer process (initial state from the uniform prior; transitions from the frozen Markov process; emissions unchanged) — the standing recovery-gate convention.
2. Calibration is computed on per-slice smoothed posterior marginals against realized per-slice states (the construct the theorem governs), with ECE under the V2.4.4 binning convention; the occupancy-vs-majority-label comparison is retained descriptively; the label-based recovery diagonal remains the accuracy criterion.
3. Fresh seed block 1230000:1231499 (unassigned inter-stage space, recorded in the seed ledger; the consumed 1200000:1201499 block is closed; the original gate-2 FAIL retained).
4. All thresholds unchanged (diagonal/macro floors, Brier <= .15, ECE <= .08, coverage >= .90). Regression test pinning generator-process identity to the scorer prior on public dummies. Full fast suite green.
On pass, continue to gate 3 as originally instructed.
