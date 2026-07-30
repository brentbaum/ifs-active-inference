# C-V34 immutable sealed verdict: PASS

All five sealed criteria passed. The bundle was executed once on escrow
`4040000:4043999`; all 4,000 seeds were consumed ascending and gap-free.
Raw per-world traces and per-record hashes were sealed before any criterion
was evaluated.

## Scientific class

1. **Reliable, regulated, root evidence — PASS.** Mean root movement was
   `0.452563` with 95% interval `[0.443633, 0.461493]`. Mean global precision
   was `0.898858`. Partner-state argmax accuracy was `1.0`.
2. **Co-regulation without root writing — PASS.** In every no-root-evidence
   world, root movement and root log BF were exactly `0.0`. The paired uptake
   effect was `0.452563 [0.443633, 0.461493]`, above the sealed lower-bound
   requirement `0.25`.
3. **Regulation increases uptake of the same evidence — PASS.** Mean global
   precision without regulation was `0.499195`. The paired regulated-minus-
   unregulated root-movement difference was
   `0.067335 [0.055461, 0.079210]`, above the sealed `0.02` lower-bound
   requirement.
4. **Partner switching and historical retention — PASS.** Post-switch
   partner-state recovery was `0.99165625`. The pre-switch posterior segment
   remained queryable with maximum error exactly `0.0`.

Switch-onset error was descriptive as sealed: mean `0.189`, 95th percentile
`1`, maximum `31`.

## Semantic class

- Regulation-only root log BF: exactly `0.0`.
- Maximum structure-posterior normalization error:
  `1.432187701766452e-14`, below `1e-10`.
- No private partner label entered inference.
- All scoring used the frozen public `score_world` path.

## Custody class

- Challenge SHA-256:
  `6b09fd32e32e7b79e1ef5e99a136bf90f32695b10369eb04f902f4275f3a4c16`.
- Frozen manifest: `82/82` files verified before execution.
- Released escrow: `4040000:4043999`.
- Seeds: `4,000`, once, ascending, gap-free.
- Cells 2 and 3 were paired with Cell 1 by seed index.
- Four trace bundles were hashed before evaluation. Their sizes were
  approximately `25–33 MB`, so none required the over-90-MB local-only
  convention.

The complete immutable calculations are in `c-v34/summary.json`; execution
custody is in `c-v34/run-ledger.json`.
