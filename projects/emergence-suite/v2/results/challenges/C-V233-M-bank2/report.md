# C-V233-M-bank2

Sealed verdict: **PASS**.

The runner verified the frozen `3e9bad2` identity plus the committed
seed-authorization repair hashes. All 5,504 candidates (`820001:825504`) were
consumed exactly once, ascending, in full. Maintenance escrow remained closed.

## Scientific sampling adequacy — PASS

- moderate: 141/5504, rate `0.025618` (95% Wilson `[0.021763, 0.030134]`); filled at position `1361`, seed `821361`; retained `40`.
- strong: 293/5504, rate `0.053234` (95% Wilson `[0.047608, 0.059483]`); filled at position `696`, seed `820696`; retained `40`.
- very_strong: 517/5504, rate `0.093932` (95% Wilson `[0.086505, 0.101925]`); filled at position `418`, seed `820418`; retained `40`.

The first 40 eligible states in each band were retained without posterior
assignment or trajectory continuation. The 800-seed result remains the
prospective natural-yield finding; this verdict is sampling adequacy only.

## Semantic integrity — PASS

All `120` retained states reconstructed exactly; maximum
provenance error was
`0.0`.
The one-posterior audit ran on all `120` retained states with
zero failures. The constructor source contains no band threshold or
maintenance-trajectory read.

## Process custody — PASS

The ITS ledger contains 5,504 gap-free rows, every row logs released block
`820001:825504`, and all 5,504 states serialize/reload/rehash bitwise. All
quotas first coexisted at position `1361`; processing
continued for
`4143`
additional candidates, proving no early stop.

## Distributional census — descriptive only

q(P) mean/median were `0.939441` /
`0.999660`. m0 mean/median were
`9.560350` /
`8.319950`. Histograms, ECDF coordinates,
history-length/profile strata, saturation, first-selection, post-selection
evidence, cumulative P-vs-runner-up BF, and fill curves are published in
`census.json` and `per_seed.csv`.

Against the committed 800-seed block, the descriptive q(P) mean difference
was `0.000499` (95% interval
`[-0.012460,
0.013458]`). No verdict pools
the blocks. Historical m0 comparison is unavailable because the 800-seed
ledger did not preserve nonbanked candidate evidence, and that block was not
rerun.

## Verdict classes

Scientific sampling adequacy: **PASS**.
Semantic integrity: **PASS**. Process custody:
**PASS**. Distributional census:
**DESCRIPTIVE ONLY**. The maintenance seeds `816001:816900` remain closed and
were not accessed.
