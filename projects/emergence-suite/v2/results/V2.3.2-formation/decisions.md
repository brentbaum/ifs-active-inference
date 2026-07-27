# V2.3.2 formation decisions

## D1 — candidate family frozen before schedules

Decision: T/D/P.

Persistent external danger is a distinct normalized candidate. Adaptive
threat under real danger should favor D, not count as identity formation.
This prevents the former adaptive-persistent-threat assay from validating
identity recruitment merely because the world is dangerous.

## D2 — static hypothesis

Decision: use static `H_formation`; do not introduce an onset variable.

The claim is finite comparison across a developmental sequence, not inference
of a literal onset time. A static candidate posterior accumulates and reverses
through likelihood evidence. A change point would add unneeded onset
complexity and a new support choice.

## D3 — stationary-drift retirement

The retired transition has formation hazard `a=.02` and recovery hazard
`b=.005`. Its stationary persistent mass is `a/(a+b)=.02/.025=.80`.
Starting at `.30`, no-evidence evolution is
`.80 + (.30-.80)*(.975)^t`, giving approximately `.467` at 16 slices,
`.701` at 64, and `.734` at 80. V2.3.2 has no transition or recovery hazard;
no-evidence posterior odds remain exactly at the once-charged prior.

## D4 — accumulator retirement

`bounded_log_odds_accumulation` is absent. Configural evidence has an
explicit observed child and a normalized predictive distribution. Its
candidate-specific normalizer is published in every BF decomposition.

## D5 — retired v2.3.1 tests

Evaluator verification caught two undisclosed full-suite failures after the
initial freeze candidate: the old v2.3.1 recovery and schedule-generalization
tests still asserted thresholds that the committed v2.3.1r errata explicitly
rescinded.

Decision: retain the test file but convert those two methods into
ledger-pinning tests. They now assert the exact committed failing values
(`ECE=0.10579451215553712`,
`surface incremental CV R²=0.6173327730910273`) and assert that the
corresponding historical gates remain false. This keeps the retired record
executable and prevents accidental resurrection. No live threshold or live
stage test is changed.
