# V3.0 Gate 5 stop — diagnosis stub

Gate 5 verdict: **FAIL**. The stage stopped before freeze.

The only failed cell was `shorter_code_penalty`. Its recovery, calibration,
and coverage criteria passed:

- macro field accuracy: 0.998929;
- ten-bin ECE: 0.000650;
- 95% posterior-set coverage: 1.000000.

The exact-log-probability parity check failed with maximum absolute error
1.2473394093880898, above the declared 1e-10 tolerance.

Apparatus localization: the robustness world generator and posterior scorer
both received `code_length_scale = 1.25`. The retained parity helper
`recovery_rows` called `local_log_scores` without forwarding that robustness
hyperparameter, so the decomposition side used the default scale 1.0. The
failure therefore localizes to the Gate-5 verification path rather than to a
numeric recovery miss. No scientific parameter, likelihood, prior, threshold,
seed, or result has been changed after observing the failure.

Repair is not attempted in this run. An invalidate-and-repeat decision belongs
to evaluator adjudication under the suite's software-error rule.
