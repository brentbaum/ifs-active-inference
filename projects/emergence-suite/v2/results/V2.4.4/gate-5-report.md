# V2.4.4 Gate 5 — honest preflight stop

Outcome: **FAIL** before the population run.

The frozen public parameter block declares cue-count support `{2,3,4}`. At `cue_count=4`, global down-weight and continuous drift execute, but cue-local relearning raises `KeyError: 'cue_4'`, while context split and change point raise `IndexError: index 3 is out of bounds for axis 0 with size 3`. The complete per-family preflight is in `gate-5.json`.

This prevents the mandatory all-dimensions robustness sweep. No scientific repair is authorized in this run, so the ratchet stops before the BMA, CRT, remaining robustness, and cumulative populations.

The standing full unit suite nevertheless remains green: `93/93` tests in
`423.448` seconds. That suite does not exercise this declared four-cue
robustness cell, so its PASS does not overwrite the Gate-5 failure.

`B_max_inherited_formation = 3.801426508560692`; `B_max_v24_common_emissions = 6.704414354964107`; `pi1 = 0.92741935483871`.
