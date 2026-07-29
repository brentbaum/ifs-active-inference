# V2.5b Gate-1 diagnosis stub

Gate 1 is retained as `FAIL`. Gate 2 was not opened and no seed in
`1100000:1100999` was consumed.

## Apparatus localization

Proofs 3 and 6 report an odds-identity residual of
`6.160128688350259`, exactly equal to the fixture's published
`log BF_000:111`.

The production identity itself is correct when recomputed without the oracle
side effect:

- posterior log odds `000:111`: `6.160128688350256`;
- prior log odds: `0.0`;
- published log BF: `6.160128688350259`;
- identity residual: `2.6645352591003757e-15`.

The defect is in `ref/v25b_oracle.py`. Its independent scorer initializes
`masses = np.asarray(prior, dtype=float)` without a copy, then performs
in-place multiplication and normalization. Gate 1 passes the production
`v25b.PRIOR` array, so the oracle changes the global prior into the fixture
posterior before proofs 3 and 6 read it. The later audit therefore subtracts
the posterior odds as if they were prior odds.

This is a shared-input mutation/software defect in the independently
authored oracle, not a failure of the declared structural odds identity.
No repair or repeat is performed without evaluator authorization.

All other 16 proofs passed. Maximum normalization error was
`2.220446049250313e-16`, marginal error
`9.992007221626409e-15`, prequential recombination error
`2.6645352591003757e-15`, and production-versus-oracle output error `0.0`
before the mutation was detected.

