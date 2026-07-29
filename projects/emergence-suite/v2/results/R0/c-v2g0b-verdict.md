# C-V2G0-B sealed apparatus verdict

## Immutable sealed verdict

**`STOP_AS_SEALED_PROSPECTION_FAILURE`**

The exact single bracketed Python literal parsed successfully using only
`ast.literal_eval`, as required. The run nevertheless stopped before any
cell compilation or escrow sampling because the frozen public authorization
API rejects the fresh escrow block.

The exception is retained verbatim:

```text
ValueError: released block must be contained in the V2.G0 diagnosis or sealed range with the matching purpose
```

No escrow seed was consumed, no world was sampled, no raw trace exists, and
none of the four sealed criteria was evaluated. The two prior stop verdicts
remain unchanged.

## Apparatus-first localization

The re-issued record uses the frozen version-1 entry shape:
`start`, `end`, `purpose`, `release_id`, and `authorization_commit`.
However, schema compatibility is not sufficient for frozen execution.

`ref/world_ir.py` declares:

```text
SEALED_ESCROW = (2000000, 2000499)
```

The parser requires every `purpose="sealed"` entry to be contained within
that range. The new C-V2G0-B entry is `2001000:2001499`, so parsing the
aggregate release record fails before `_validate_seed` can authorize any
seed. Extending the frozen constant or accepting an out-of-range entry would
require a source-code change, which this sealed run forbids.

## Sealed criteria

| Criterion | Class | Standing |
|---|---|---|
| 1 — compile/sample/protocol completion for 500 runs | scientific-apparatus | **NOT EVALUATED — release/API precondition failed** |
| 2 — independent log-probability and restriction-normalizer parity | scientific-apparatus | **NOT EVALUATED** |
| 3 — schema constancy and trace custody | semantic | **NOT EVALUATED; no traces exist** |
| 4 — escrow custody | custody | **SEALED STOP CLEAN: 0/500 consumed; no diagnosis seed touched** |

This is a release-range/frozen-guard prospection failure, not a failure of
the corrected Python-literal documents, sampled-world probabilities, output
schemas, or scientific machinery.

## Verdict classes

- **Scientific-apparatus:** `NOT_EVALUATED`; execution did not reach world
  compilation or sampling.
- **Semantic:** `NOT_EVALUATED`; no output schema was emitted.
- **Custody:** `PROSPECTION_FAILURE_WITH_PASS_STOP_INTEGRITY`; the release
  record is inadmissible to the frozen range guard, while all fresh escrow
  seeds remain untouched.

## Custody and hashes

- challenge SHA-256:
  `cbf0736763f54ac155328145a74fbe17f1401b563c4a05eaf181332634085129`;
- release-record SHA-256:
  `9f3186361df76f308869a034e81d6cd7a1b3bfdf722ca416eebffe64f55a7204`;
- first-stop verdict SHA-256:
  `fdcb9bb1950224fcc73a585abe27a5519d16617823d8ed02b3e371ce9869e050`;
- second-stop verdict SHA-256:
  `f965a5f086737a15b6f56794cd04321d39d87ea95f07ef044e5cd1fd3087669d`;
- canonical empty trace-index SHA-256:
  `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945`.

There was no raw-trace seal because there was no execution. The empty index
is an explicit no-execution custody record, not a replacement for a
successful raw-trace seal.

## R0 stage report

`results/R0/stage-report.md` was not updated. The sealed apparatus challenge
did not pass, so the R0 exit condition remains unmet.

## Full unit suite

The full suite ran:

```text
Ran 131 tests in 430.403s
FAILED (failures=1)
```

The sole failure is retained:

```text
test_v2g0_grammar.V2G0GrammarSemanticProofs.test_15_sealed_escrow_is_inaccessible
AssertionError: "escrow" does not match "released block must be contained in the V2.G0 diagnosis or sealed range with the matching purpose"
```

The remaining 130 tests passed. The failure has the same cause as the
sealed stop: parsing the aggregate release record fails on the out-of-range
C-V2G0-B entry before the test can reach its expected escrow-specific
refusal. No source or test file was changed.

