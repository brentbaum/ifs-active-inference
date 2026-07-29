# V2.6a Gate-2 repair-cycle stop report

Status: **FAILED_RATCHET_REPAIRED_GATE_2_SWITCH_ONSET**.

The authorized apparatus repair succeeded on its target. Recovery worlds were
drawn from the scorer's frozen uniform initial prior, `0.94/0.02` Markov
transition, and unchanged emission tables. Blocking calibration used all
72,000 per-slice smoothed partner marginals against realized `L_t`, with the
unchanged V2.4.4 ten-bin confidence-ECE convention.

The repaired ECE was `0.0031028041947577687`, down from the category-mismatched
original value `0.20101343381872663`. Multiclass Brier was
`0.14823808079259085`, posterior-set coverage `0.9880555555555556`, macro
majority-family recovery `0.8987705049926129`, and the four diagonals ranged
from `0.8641025641025641` to `0.9426934097421203`. Transition-rate MAE was
`0.017626147746432983` and local-precision calibration error was
`0.0381788763970843`.

One independent retained threshold failed: switch-onset median absolute error
was `5.0` slices against the blocking maximum of `3`. The failure is retained
verbatim in `gate-2-repaired.json` and
`gate-2-repaired-diagnosis-stub.md`. No onset readout, parameter, threshold, or
generator was changed after observing it.

The original Gate-2 FAIL and its traces remain unchanged. The repaired block
`1230000:1231499` was consumed once and is closed. Gate 3 was not executed;
its criterion block was not opened during this repair cycle. Escrow
`2030000:2031999` remains untouched. The full fast suite passed all 22 modules
in 52.665 seconds.
