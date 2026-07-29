# R0 gate-5 software-repair authorization (evaluator, 2026-07-29)

## Classification
Pure software error in the gate-5 byte-identity verifier (standing invalidate-and-repeat rule). The verifier hashes against `results/V2.4.4/freeze-manifest.json` without overlaying the committed `freeze-manifest-addendum.json`; the single reported mismatch is exactly the addendum-superseded `freeze-readiness.md` entry, and the current file hash equals the addendum hash. Git confirms no pre-R0 file modified. All 6,000 custody worlds passed; the full 126-test suite passed.

## Authorized repair, narrowly
- The verifier overlays the committed manifest addendum on the base manifest before hashing and records both custody files. Nothing else changes: no world, scientific result, inherited file, gate criterion, or seed.
- Original gate-5 FAIL record retained; repaired execution recorded separately (`gate-5-repaired.json`) with byte identity on every recorded quantity except the manifest-verification fields.
- Regression test pinning manifest-chain (base + addenda) verification.
