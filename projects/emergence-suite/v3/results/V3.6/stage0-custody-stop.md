# V3.6 Stage-0 custody stop

Status: **STOPPED_BEFORE_ATTAINABILITY_PILOT_CUSTODY_FAILURE**.

While validating the new composition-only public API, I executed seed
`3600000`, the first seed in the assigned pilot block `3600000:3603999`.
The call was inside a serializing trace context, and the terminal output showed
nine runtime events and the complete immutable composition readout. However,
the sink events and per-world record were printed rather than persisted to a
JSONL ledger and hashed at execution time.

That violates the standing custody rule. In-memory or terminal output is not a
substitute for the required persisted event ledger. The seed cannot be run a
second time without explicit invalidate-and-repeat or reproduction authority.

No criterion was evaluated. No attainable range or floor was computed or
frozen. No other pilot, gate, diagnosis, barred, or escrow seed was touched.
C-V36A/B/C escrow remains untouched.

The stage stops here for evaluator adjudication. The evaluator must decide
whether `3600000` is permanently barred and a fresh pilot block is assigned,
or whether a specifically authorized reproduction-and-custody procedure may
recover the assigned block. This implementation does not self-authorize either
route.

## Apparatus localization

The failure is in the preflight invocation, not in the scientific composition
or trace guard. `v36.run_therapy` correctly required an active serializing
trace context, and the constituent V3.2–V3.5 calls recorded their operations.
The caller failed to persist `sink.events` and the returned readout before
ending the smoke command.
