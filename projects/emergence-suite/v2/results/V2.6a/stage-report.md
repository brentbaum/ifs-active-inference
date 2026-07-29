# V2.6a stage report — gate-2 honest stop

Stage status: **FAILED_RATCHET_GATE_2_CALIBRATION**.

Stage 0 implemented one exact four-state latent partner process for regulation,
remaining/withdrawal, pressure/respect, and trust-relevant observations. Local
partner inference is exact HMM filtering/smoothing; optional broadcast changes
global precision, while partner observations never enter the root likelihood.
`co_regulated` remains a pure readout.

Gate 1 passed all 16 semantic obligations. Production and the independently
authored enumeration oracle agreed within `8.326672684688674e-17`.
Regulation-only root log-BF and root movement were exactly zero; broadcast-off
partner inference was identical. The permanent constitution and V2.5b
manifest chain passed.

Gate 2 stopped the stage. The recovery confusion matrix had macro accuracy
`0.9926666666666667` and family diagonals from `0.9866666666666667` to
`0.9973333333333333`. Brier was `0.1293226642643253`, posterior-set coverage
`1.0`, switch-rate MAE `0.0186938114207919`, switch-onset median absolute
error `0.0`, and local-precision calibration error `0.01687170887816234`.
However, ECE was `0.20101343381872663`, exceeding the blocking `0.08`
ceiling. The failure is retained verbatim in `gate-2.json` and
`gate-2-diagnosis-stub.md`.

Gate 3 was not run. A preflight seed-hygiene error did instantiate public
fixtures at `1202000:1202002`; no criterion was evaluated, but those three
seeds are disclosed as consumed and require adjudication before any future
continuation. Formal fixtures now use `1199900:1199902`. Escrow
`2030000:2031999` was untouched. The full fast suite passed all 22 modules.

Named bounds: inherited formation `3.801426508560692`; V2.4 common emissions
`6.704414354964107`; V2.5a configural `6.084736253211209`; V2.5a marginal
accounting `6.704414354964107`; V2.5b `11.302393144606405`; V2.6a relational
`6.9920964274158885`; V2.6a root `2.9444389791664394`.
