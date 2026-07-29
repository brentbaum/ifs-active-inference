# C-V2G0-C sealed apparatus verdict

## Immutable sealed verdict

**PASS**

All four sealed criteria passed on the single execution of 500 escrow worlds.
The exact Python literal was parsed with `ast.literal_eval` and no other
transformation. Seeds `2000000:2000499` were consumed once, ascending and
gap-free. No source code changed.

Raw traces were written and sealed before any criterion evaluation. The raw
seal SHA-256 is:

```text
2d046ef8a4c5fa7100c89e7b10546d71cc72168266a4fa6c95104e2a5bcfd6e3
```

## Sealed criteria

| Criterion | Class | Result |
|---|---|---|
| 1 — compile/sample/protocol completion | scientific-apparatus | **PASS** — all four cells compiled; all 500 seeds sampled; A–C completed through `run_protocol`, D through `run_bridge` |
| 2 — exact probability and normalizers | scientific-apparatus | **PASS** — maximum independent log-probability discrepancy `3.552713678800501e-15`; maximum trace-score discrepancy `3.552713678800501e-15`; maximum normalizer discrepancy `1.3322676295501878e-15` |
| 3 — schema and trace custody | semantic | **PASS** — one output-schema hash per cell; all 500 traces carry world/protocol hashes, scopes, and component RNG keys |
| 4 — escrow custody | custody | **PASS** — 500 seeds consumed once in exact ascending order; no gap and no diagnosis seed |

Pass requires all four; therefore the immutable sealed verdict is **PASS**.

## Exactness

Per-cell maximum discrepancies between `independent_world_log_prob` and
`log_prob_world`:

| Cell | Maximum absolute discrepancy |
|---|---:|
| A | `0.0` |
| B | `0.0` |
| C | `3.552713678800501e-15` |
| D | `0.0` |

Restriction-normalizer parity:

| Cell/process | Production | Independent oracle | Absolute discrepancy |
|---|---:|---:|---:|
| A / windowed change point | `0.6` | `0.6` | `0.0` |
| B / restricted recurrent shared latent | `0.7726410158022948` | `0.7726410158022935` | `1.3322676295501878e-15` |

Every discrepancy is below the sealed `1e-10` tolerance.

## Schema and trace custody

| Cell | Schema SHA-256 | RNG keys per trace | Raw file SHA-256 |
|---|---|---:|---|
| A | `6efe8545f7e1750b1770b45864599896dd90e6487c2a5070fe3674b1ea859350` | 3 | `b052957ea6a163d31a6064b8d5e5cc034dae8e0669dba8c07860c18a160fc21a` |
| B | `9cc908a17dc76eb8638a9475329a85b4edd04419b30f48ce39b7b933a7d7125a` | 1 | `c3f610c6d90a6f35eade1548002f5975a88680ec8c090f76ece1eb94801a6b5c` |
| C | `382ce2cd8e52bbddb1755c26ab2f2ea4fd5d38a9651b13ea0946150e7f4d035f` | 9 | `9feb7a5738a302135aa8b46f5b010745615285aafcf155b2c3db51ab124dc9b1` |
| D | `d13af4a88578a3b0faabc7135201b23fe4daa5db142f6f1b0c94c19194c177a0` | 2 | `58c77fa24b10de58a47e810de8cc8dd256545fda31b43ef6e21912344d254508` |

The seal also records the SHA-256 of every individual per-seed record. The
seal and all record hashes were verified before criteria were computed.

## Verdict classes

- **Scientific-apparatus:** **PASS** — construction, sampling, protocol
  execution, exact probability, and restriction normalization passed.
- **Semantic:** **PASS** — schemas were cell-constant and required custody
  fields were present.
- **Custody:** **PASS** — exact literal parsing, data-only release, raw-first
  sealing, single ascending seed use, and no diagnosis access.

## Four-seal history

The prior outcomes remain in force as written:

1. C-V2G0 first sealing — `STOP_AS_SEALED_PROSPECTION_FAILURE`: release-record
   schema incompatible with the frozen parser.
2. C-V2G0 second attempt — `STOP_AS_SEALED_PROSPECTION_FAILURE`: JSON numeric
   onset keys stringified and the exact document did not compile.
3. C-V2G0-B — `STOP_AS_SEALED_PROSPECTION_FAILURE`: fresh escrow lay outside
   the frozen sealed range.
4. C-V2G0-C — **PASS**: exact Python literal, parser-valid contained release,
   raw-first sealed execution, and all four criteria passed.

The first three stops consumed zero seeds. C-V2G0-C is the only executed
sealed population.

## Full unit suite

The full suite ran after the sealed evaluation:

```text
Ran 131 tests in 434.092s
FAILED (failures=1)
```

The sole failure is retained verbatim:

```text
test_v2g0_grammar.V2G0GrammarSemanticProofs.test_15_sealed_escrow_is_inaccessible
AssertionError: ValueError not raised
```

The remaining 130 tests passed. This is a stale pre-release custody assertion:
the test requires the real escrow to remain inaccessible, while the
evaluator's data-only record now intentionally releases that exact range.
It does not alter the sealed criteria or verdict. No source or test was
changed.

## R0 exit

The R0 exit condition is met: the sealed apparatus challenge passed.

