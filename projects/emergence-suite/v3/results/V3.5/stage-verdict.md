# V3.5 final stage closure

Disposition: **CLOSED_PASS_AFTER_AMENDMENT_2**.

The amendment-2 development battery passed Gates 1–5. C-V35B then ran once
on its released block and passed all seven sealed criteria. Its scientific,
semantic, and custody verdict classes all pass. The earlier stage-0 records,
the amendment-1 Gate-3 failure, and the retired unopened C-V35 seal remain in
the ledger; this closure does not rewrite them.

## Bounds

- V3.5 atomic finite-information bound: `3.4760986898352733`.
- Implied binary posterior-change bound: `0.7008782529950642`.
- Exact-identity tolerance: `1e-10`.
- Equivalence ROPE: `[-0.01, 0.01]`.

## Sealed recovery

The 400-world recovery cell obtained active-count accuracy `1.0`, exact-program
accuracy `0.55`, topology accuracy `0.715`, minimum edge accuracy `0.7075`,
partner accuracy `1.0`, coverage `0.9775`, and ECE `0.03666804217262897`.
Maximum normalization error was `5.684341886080802e-14`; the independent
enumeration audit's maximum error was `2.0539125955565396e-15`.

## Custody

All 5,000 escrow seeds in `4055000:4059999` were consumed exactly once,
ascending and gap-free. Paired cells used one seed for both arms. Runtime event
ledgers and per-world statistics were flushed to JSONL during execution. The
raw trace file and every record were hashed before any criterion was evaluated.
The trace SHA-256 is
`6f43f7c9fcfcc923ea8e711c0c2423bcd71dc29ff554946db29e307981d7b899`;
independent rehashing found zero record errors. Frozen identity remained 47/47.
There were no reruns, retries, software errors, or threshold changes. Retired
C-V35 escrow `4050000:4054999` remains untouched.
