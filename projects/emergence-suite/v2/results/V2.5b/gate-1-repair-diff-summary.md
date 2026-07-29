# V2.5b Gate-1 software-repair diff

Authorization: `results/V2.5b/gate1-software-repair-authorization.md`.

The independent structural oracle now initializes its working posterior with
`np.array(prior, dtype=float, copy=True)`. It no longer aliases or mutates the
caller's prior. No production likelihood, prior, parameter, threshold, seed
block, or scientific readout changed.

An input-immutability regression test asserts bitwise identity of the oracle's
prior and episode inputs before and after scoring. The runner gained a distinct
`gate1repaired` output path solely so the original Gate-1 FAIL remains intact.

The repaired execution passed all 18 proofs. The structural-odds identity
residual was `2.6645352591003757e-15`; production-versus-oracle error was
exactly `0.0`.
