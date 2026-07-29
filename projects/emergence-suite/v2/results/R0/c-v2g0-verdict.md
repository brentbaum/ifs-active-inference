# C-V2G0 sealed apparatus verdict

## Immutable sealed verdict

**`STOP_AS_SEALED_PROSPECTION_FAILURE`**

The sealed run did not start. No escrow seed was consumed, no world was
sampled, no raw scientific trace exists, and none of the four sealed criteria
was evaluated.

The committed release document cannot execute through the frozen public
authorization API. The frozen `ref.world_ir._released_blocks` parser requires
record version 1 and entries containing inclusive `start`/`end`,
`purpose`, `release_id`, and `authorization_commit`. The revealed data commit
contains record version 2 and an entry containing `block`, `challenge`,
`released_by`, `date`, and `basis`.

The pre-execution public-API probe therefore raised, verbatim:

```text
ValueError: invalid V2.G0 released-blocks authorization record
```

Per the sealed instruction, this is reported without an adapter, source-code
change, challenge-specific runner, or attempted escrow sample.

## Localization

| Layer | Frozen declaration | Revealed data | Result |
|---|---|---|---|
| record version | `1` | `2` | incompatible |
| range fields | `start`, `end` | `block: [start, end]` | incompatible |
| authorization class | `purpose="sealed"` | absent | incompatible |
| authorization identity | `release_id`, `authorization_commit` | absent | incompatible |
| descriptive metadata | not a substitute for authorization fields | `challenge`, `released_by`, `date`, `basis` | not accepted |

Challenge plaintext SHA-256:
`c9b2d5c0dd8e1b468fccf99493e0400a43b05672c0ff1f15c3c341e7dbe3b90c`.

Release-record SHA-256:
`64c0da8a9222c05cf7301f4b285558a9bb1df53e761ed5e168983bc4f8b7192f`.

## Sealed criteria

| Criterion | Class | Standing |
|---|---|---|
| 1 — compile/sample/protocol completion for 500 runs | scientific-apparatus | **NOT EVALUATED — prospection precondition failed** |
| 2 — independent log-probability and restriction-normalizer parity | scientific-apparatus | **NOT EVALUATED** |
| 3 — schema constancy and trace custody | semantic | **NOT EVALUATED; no traces exist** |
| 4 — escrow custody | custody | **SEALED STOP CLEAN: 0/500 consumed; no diagnosis seed touched** |

This is not evidence of a scientific-model failure, sampled-world exactness
failure, or schema failure. It is a release-document/frozen-parser
prospection failure at the custody boundary. The pre-seal linter's conclusion
that escrow acceptance required only a compatible data commit is not
satisfied by the revealed record's schema.

## Verdict classes

- **Scientific-apparatus:** `PROSPECTION_FAILURE`; sampling apparatus not
  entered.
- **Semantic:** `NOT_EVALUATED`; no output schema was emitted.
- **Custody:** `PASS_STOP_INTEGRITY`; the complete escrow remains untouched.

## Raw trace seal

There was nothing to seal. The run ledger records a trace count of zero, an
empty trace-file/hash list, and the canonical empty trace-index SHA-256
`4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945`.
This is an explicit no-execution record, not a substitute for the raw-trace
seal required after a successful run.

## Full unit suite

The requested full suite ran:

```text
Ran 131 tests in 445.764s
FAILED (failures=2)
```

The two failures were retained:

```text
test_v2g0_grammar.V2G0GrammarSemanticProofs.test_15_sealed_escrow_is_inaccessible
AssertionError: "escrow" does not match "invalid V2.G0 released-blocks authorization record"

test_v2g0_grammar.V2G0GrammarSemanticProofs.test_16_diagnosis_seeds_are_inaccessible_to_public_sampler
AssertionError: "diagnosis" does not match "invalid V2.G0 released-blocks authorization record"
```

All other 129 tests passed. Both failures localize to the same malformed
release record: the parser stops at the version check before it can reach the
expected escrow- or diagnosis-specific authorization decision.

