# V3.3 Gate-3 stop

Status: **FAIL — Gates 4–5 unopened**.

Gate 2 passed. Gate 3 then executed its full `3305000:3309999` block once under
serializing trace contexts. Every per-world record was serialized and hashed
before aggregation.

Two blocking checks failed:

1. The timely do-over did not accelerate material reduction. Of 800 same-seed
   pairs, 799 had proportional speedup `0`; one had `-0.25`. The mean was
   `-0.0003125`, with 95% whole-world bootstrap interval
   `[-0.0009375, 0.0]`, below the prospectively frozen `0.00025` floor.
2. Suggestion-only evidence did avoid false structural reduction (`0/700`),
   but its mean historical-minus-current root estimate was
   `-0.007463967250969002`, opposite the preregistered positive direction for
   root revision without pruning.

All other Gate-3 checks passed: configural material reduction `0.9775`,
premature durable reduction `0.00429`, correction-only material reduction
`0.98286`, adaptive-edge survival `0.99802`, mode retention `1.0`, historical
graph reconstruction `0.69355`, and exact neutral-observation identity.

This is the required honest stop. No thresholds, directions, worlds, or
scientific code were changed after seeing Gate 3. Gates 4–5 and escrow
`4030000:4033999` remain unopened.
