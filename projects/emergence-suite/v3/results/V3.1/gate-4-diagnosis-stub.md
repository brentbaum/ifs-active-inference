# V3.1 Gate-4 diagnosis stub

Status: **STOPPED — UNDEFINED LESION POSTERIOR**.

The Gate-4 execution opened its planned paired population beginning at seed
3110000. It did not produce a scientific lesion result. The first lesion,
`mode_slot`, restricts the posterior to programs with `active_mode=0`.
`_mode_log_score` assigns such a program log likelihood `-inf` whenever any
observed mode value is one. The repeated-adversity lesion worlds contain such
observations, so every surviving program has log score `-inf`.

The exact failure is therefore:

1. production deletion removes all active-mode programs;
2. typed mode observations remain in the likelihood;
3. the inactive-mode component gives those observations zero probability;
4. all 128 program scores are `-inf`;
5. log-sum-exp evaluates `exp(-inf - -inf)`, producing `NaN`;
6. the JSON custody writer rejects the non-finite result.

This is apparatus-first localization only. No threshold was evaluated, no
scientific consequence was inferred, and no repair was attempted. Whether a
mode-slot deletion must mask the removed channel, retain a normalized
mode-absent observation model, or use another declared lesion semantics
requires adjudication. Gate 5 was not opened.

The recursive-precision runner wiring was corrected before this execution:
it holds the graph and latent trajectory fixed and changes only typed
mode/root observation masks. A five-world barred-pilot preflight showed a
nonzero unlesioned mask effect and exact posterior identity after severing
that pathway. This correction did not alter inference code and is unrelated
to the mode-slot support failure.
