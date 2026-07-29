# V2.5b gate-1 software-repair authorization (evaluator, 2026-07-29)

Classification: pure software error — the independent oracle's `masses = np.asarray(prior)` aliases the production `v25b.PRIOR` and mutates it in place, so proofs 3 and 6 subtract posterior odds as prior odds. The declared identity is correct (residual 2.7e-15 when recomputed without the side effect); all other 16 proofs passed.

Authorized, narrowly: copy the prior in the oracle (`np.array(prior, dtype=float, copy=True)`); add a regression test asserting the oracle leaves its inputs bitwise unchanged (and consider an immutability guard on module-level priors if it is a pure readonly flag with zero behavior change). Re-execute gate 1 (gate-1-repaired.json; original FAIL retained), then continue to gates 2 and 3 as previously instructed. Full fast suite green.
