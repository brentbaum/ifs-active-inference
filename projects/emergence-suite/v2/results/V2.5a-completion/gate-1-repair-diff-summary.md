# Gate-1 authorized repair diff summary

Authorization: `gate1-software-repair-authorization.md` (`f599f7c`).

The repair changes only proofs 6 and 8 in `run_v25a_completion.py`:

- before: `numpy.array_equal` required bit-identical neutral posteriors;
- after: maximum absolute posterior deviation must be at most the already
  declared `semantic_tolerance = 1e-10`.

`tests/test_v25a_completion.py` now pins the convention with a marginal
posterior that has a nonzero floating-point deviation but lies inside the
declared tolerance. No likelihood, prior, table, parameter, estimator,
threshold, seed assignment, or scientific readout changed. The original
`gate-1.json` FAIL is retained; `gate-1-repaired.json` is the authorized
re-execution and passes all 16 proofs.

