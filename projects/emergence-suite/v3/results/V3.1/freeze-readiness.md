# V3.1 freeze readiness

Status:
**FROZEN_ADJUDICATED_MIXED_REVISABILITY_LIMITATION**.

V3.1 is ready for evaluator verification and C-V31 sealing custody. This is
not an all-gates-pass claim:

- Gates 1 and 2 passed.
- Gate 3 remains formally **FAIL**. Seven of eight open results passed. The
  high-control minus low-control safe-evidence revisability difference was
  `0.005241709145309157`, 95% interval
  `[-0.00039953177232204037, 0.011316189191591242]`, below the frozen
  `0.0071` floor. `gate3-adjudication.md` makes this one effect-size family
  non-blocking and preserves it verbatim.
- The original Gate-4 software stop and repaired Gate-4 selectivity FAIL both
  remain in the ledger.
- The amended Gate-4 rescore passed. Deterministic reconstruction reproduced
  the complete repaired aggregate object exactly before corrected scoring.
  All six declared consequences passed. Every per-world restricted-prior
  identity and independent-oracle check was within `1e-10`; observed maxima
  were below `1e-14`.
- Gate 5 passed all blocking V3.1 cells and the inherited V3.0 robustness
  regression.

Custody:

- Gate-4 reconstructed worlds: 2,000 records, file SHA-256
  `908fc36a15b5f8e1ef818c5605afc9650a3d7ac4158e5ca2f11252bfe29fde0b`.
- Gate-4 corrected per-world readouts: 2,000 records, file SHA-256
  `87703c22b81ec376c395d3841b306f3fda68c577b54bc9c85cf203d59c87344e`.
- Gate-5 traces: 800 records, file SHA-256
  `ef12009dba20e677c3c67d65e7ef6c7ff3df3bed336163ef4c638ccfbb39bd17`.
- Per-record SHA-256 ledgers accompany all three files.
- C-V31 escrow 4010000–4013999 was not accessed.

Regression status: V3 23/23 and frozen V2 180/180 passed. The freeze manifest
hashes source, independent oracle, tests, public artifacts, adjudications,
gate reports, and trace custody files.
