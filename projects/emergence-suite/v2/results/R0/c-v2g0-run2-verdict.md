# C-V2G0 sealed apparatus run 2 verdict

## Immutable sealed verdict

**`STOP_AS_SEALED_PROSPECTION_FAILURE`**

The evaluator's corrected version-1 release record passes the frozen public
authorization parser and exposes exactly `2000000:2000499` for sealed use.
The sealed run nevertheless did not start: Cell A's exact revealed world
document fails `compile_world` before any seed access.

The compile exception is retained verbatim:

```text
ValueError: change_point onset is outside sequence support
```

No escrow seed was consumed, no world was sampled, no raw trace exists, and
none of the four sealed criteria was evaluated. The first verdict remains
unchanged at `results/R0/c-v2g0-verdict.md`.

## Apparatus-first localization

Cell A declares `regime-shift.onset_probabilities` inside a JSON document:

```json
{
  "no_change": 0.15,
  "1": 0.1,
  "2": 0.15,
  "3": 0.15,
  "4": 0.15,
  "5": 0.15,
  "6": 0.15
}
```

JSON object keys are strings. The frozen compiler's public
`change_point` implementation admits the literal `"no_change"` plus integer
onset indices from `range(1, length)`. It does not coerce numeric strings to
integers. Thus the exact sealed keys `"1"` through `"6"` are outside the
compiler's declared runtime support.

Changing those keys after parsing would be a challenge-specific adapter and
would change the exact sealed document presented to the frozen API. Adding
coercion to the compiler would be a source-code change. Both actions are
forbidden, so execution stopped before `sample_world`.

## Sealed criteria

| Criterion | Class | Standing |
|---|---|---|
| 1 — compile/sample/protocol completion for 500 runs | scientific-apparatus | **NOT EVALUATED — exact Cell A document fails the compile precondition** |
| 2 — independent log-probability and restriction-normalizer parity | scientific-apparatus | **NOT EVALUATED** |
| 3 — schema constancy and trace custody | semantic | **NOT EVALUATED; no traces exist** |
| 4 — escrow custody | custody | **SEALED STOP CLEAN: 0/500 consumed; no diagnosis seed touched** |

The configuration cannot execute through the frozen public vocabulary
exactly as sealed. This is a world-document/compiler expressibility failure,
not a sampled-world probability, schema, or scientific-model result.

## Verdict classes

- **Scientific-apparatus:** `PROSPECTION_FAILURE`; Cell A is not compilable
  as exact revealed JSON.
- **Semantic:** `NOT_EVALUATED`; no output schema was emitted.
- **Custody:** `PASS_STOP_INTEGRITY`; the complete escrow remains untouched
  and the single-run budget remains unspent.

## Custody and hashes

- challenge SHA-256:
  `c9b2d5c0dd8e1b468fccf99493e0400a43b05672c0ff1f15c3c341e7dbe3b90c`;
- corrected release-record SHA-256:
  `ed45e90039858ab42bc453d12f2360558fc64851a72555c46197e2c5983f6e40`;
- retained first-verdict SHA-256:
  `fdcb9bb1950224fcc73a585abe27a5519d16617823d8ed02b3e371ce9869e050`;
- canonical empty trace-index SHA-256:
  `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945`.

There was no raw-trace seal because there was no execution. The ledger's
empty trace index is explicitly a no-execution custody record, not a
replacement for a successful raw-trace seal.

## Full unit suite

The full suite ran against the corrected release data:

```text
Ran 131 tests in 449.744s
FAILED (failures=1)
```

The failure is retained verbatim:

```text
test_v2g0_grammar.V2G0GrammarSemanticProofs.test_15_sealed_escrow_is_inaccessible
AssertionError: ValueError not raised
```

The other 130 tests passed. This failure is a stale pre-release custody
assertion: the test requires the real escrow to remain inaccessible, while
the corrected evaluator data record now legitimately authorizes it. No test
or source file was changed.

