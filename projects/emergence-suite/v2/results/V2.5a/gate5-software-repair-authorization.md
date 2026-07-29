# V2.5a gate-5 software-repair authorization (evaluator, 2026-07-29)

## Classification
Pure software error in the V2.5a gate-5 process-custody verifier — the same manifest-chain class repaired in R0 (results/R0/gate5-software-repair-authorization.md): the verifier reads `results/V2.4.4/freeze-manifest.json` without composing the committed `freeze-manifest-addendum.json`; the single mismatch is the addendum-superseded freeze-readiness hash. Every other gate-5 blocking check passed; the full suite passed 129/129.

## Authorized repair, narrowly
- The verifier composes base manifest + committed addenda (reuse or mirror the repaired R0 manifest-chain logic; prefer a single shared helper so this class cannot recur a third time) and records all custody files.
- Nothing else changes. Original FAIL record retained; repaired execution recorded separately with byte identity on every recorded quantity except the manifest-verification fields.
- Regression test for manifest-chain composition in the V2.5a verifier path (or the shared helper).
- On pass: proceed to the format-core stage report and manifest as previously instructed.

## Standing note
Two independent verifiers have now failed identically. The shared-helper requirement above is part of this authorization: manifest-chain verification becomes one public function used by all future gate-5 verifiers.
