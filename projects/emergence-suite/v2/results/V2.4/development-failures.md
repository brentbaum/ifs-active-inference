# V2.4 development failures

One deterministic Gate-2 seed (`770200`) was evaluated as a performance smoke after Gate 1 passed and before the official full Gate-2 block. Its result caused no code, parameter, threshold, or protocol decision and remains in the preregistered block.

## Official Gate 2 stop

- every_diagonal
- brier

## Gate-2 scoring erratum (analysis only; no rerun)

The original report above is retained verbatim. Its Brier implementation
used `mean(sum((q-y)^2, axis=classes)) = 0.39580583437468875`.
The standing suite definition in `ref/v232_formation.py` is
`mean((q-y)^2)` over worlds and classes. On that inherited scale the same
already-recorded predictions give `0.07916116687493775`, below the frozen
`0.15` ceiling.

No world, parameter, threshold, posterior, or confusion count changed. The
ratchet still stops at Gate 2 because the per-family recovery diagonal failed
for global down-weight (`0.56`), cue-local relearning (`0.49`), and
continuous drift (`0.59`) against the frozen `0.60` minimum.
