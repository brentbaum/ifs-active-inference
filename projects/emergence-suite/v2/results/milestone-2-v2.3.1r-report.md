# Milestone 2 update — V2.3.1r instrument repair

The evaluator classified V2.3.1's H-dependent accumulation partition as a
pure software error. V2.3.1r normalizes each candidate likelihood while
retaining the frozen model, parameters, priors, protocols, seeds, and
thresholds.

Neutrality is repaired exactly: masked BF is 1 to `4.44e-16`, and the
artifact term is at most `4.44e-16` per slice across all 900 slices of the
eight audited trajectories.

Invalidate-and-repeat outcomes:

- V2.3.1 Gate 1: PASS
- V2.3.1 Gate 2: **FAIL** (structure ECE `0.105795 > 0.10`)
- V2.3.1 Gate 3: **FAIL** (surface CV R² `0.617333`; control contrast
  `0.072760`)
- V2.3.1 Gates 4–5: PASS
- all cumulative V2.0, V2.1, and V2.2.1 gates: PASS
- C-V23b (repaired instrument): **FAIL** (Tests 1, 2, and 4 fail; continuity
  passes)

The original defective-instrument results remain unchanged. C-V23 is
unaffected by this defect because frozen V2.3 has no accumulation potential;
its masked candidate BF is 1 to `2.18e-14`.

Detailed errata and every moved numeric metric are in
`results/V2.3.1/repair-errata.md` and
`results/V2.3.1r/metric-diff.json`. No V2.3.2 mechanism work was performed.
