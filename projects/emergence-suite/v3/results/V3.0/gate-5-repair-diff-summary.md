# V3.0 Gate-5 software-repair diff

Authorization: `gate5-software-repair-authorization.md`.

The repair is limited to the Gate-5 parity verification path:

1. `recovery_rows` reads the already-supplied `hyperparameters` value from its
   world keyword arguments, defaulting to the unchanged V3.0 defaults.
2. It passes that value to `local_log_scores` when recombining the exact world
   probability.
3. The regression test runs the parity helper across every Gate-5 robustness
   configuration, including code-length scale 1.25, and requires error at most
   1e-10.

No generator, posterior scorer, likelihood, prior, threshold, seed, scientific
readout, or criterion changed. The original `gate-5.json` FAIL remains intact.
The repaired run is `gate-5-repaired.json`.

The spurious `shorter_code_penalty` parity error changed from
`1.2473394093880898` to `1.2789769243681803e-13`. Every non-parity quantity is
byte-identical, as recorded in `gate-5-repair-byte-identity.json`.
