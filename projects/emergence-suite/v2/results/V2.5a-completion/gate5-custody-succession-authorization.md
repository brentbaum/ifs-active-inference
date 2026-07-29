# Gate-5 custody-succession authorization (evaluator, 2026-07-29)

Classification: custody-data gap, not a scientific or software failure. The 5,000-world robustness execution passed; the blocking failures are (a) historical stage manifests (V2.0, V2.1, V2.2.1, V2.3.2-formation, V2.3.3, V2.4.4, R0) hashing source files at pre-amendment bytes after the AUTHORIZED performance amendment 1 (56ee77f) and escrow-release data commits, with no succession addenda; (b) two stale test assertions already disclosed at the amendment (R0 escrow-inaccessibility; V2.4.4 base-manifest assertion).

Authorized, narrowly:
1. For each affected historical stage, write a manifest ADDENDUM (results/<stage>/freeze-manifest-addendum-perf1.json) listing exactly the files whose hashes changed, their new sha256, and the authorizing commits (performance amendment 1; release-record commits). Base manifests are never edited. The shared manifest-chain composer already overlays addenda.
2. Update the two stale tests to assert the CURRENT contract (escrow accessible iff released via the committed record; manifest verification through the chain composer).
3. Byte-identity is inherited from the amendment's own verification (196c698... fixture ledger); no re-verification of science is required, but the addenda hashes must be independently confirmed by the evaluator before freeze.
4. Then re-run gate-5 cumulative verification only (no world re-execution — the 5,000-world results stand), write gate-5-repaired.json, and produce the freeze-readiness report and manifest as previously instructed.
