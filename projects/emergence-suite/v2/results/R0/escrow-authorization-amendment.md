# R0 pre-seal escrow-authorization amendment

**Status:** `PASS_PRESEAL_APPARATUS_AMENDMENT`  
**Stage:** V2.G0 / R0 apparatus only  
**Date:** 2026-07-29  
**Scientific or psychological claim:** none  
**C-V2G0 challenge execution:** not run

## Defect class

The frozen public sampler accepted only development seeds and hard-refused the
C-V2G0 escrow range. That placed challenge release policy inside the sampler:
after reveal, an evaluator could not authorize `2000000:2000499` without a
source change. The permanent four-layer linter would therefore have answered
“no” to:

> Can the exact sealed population be generated and scored after reveal with
> zero source-code change?

This is the same pre-execution seed-guard defect class as the V2.3.3 bank
authorization repair. It is an apparatus/custody defect, not a world,
protocol, inference, criterion, or numerical result.

## Authorized amendment

Release policy moved from a hard-coded refusal to the public committed record:

```text
protocols/v2.g0-released-blocks.json
```

Its initial contents release no block:

```json
{
  "stage": "V2.G0",
  "version": 1,
  "released_blocks": []
}
```

The sampler now applies this authorization order:

1. `1000000:1009999` is always valid development space and returns before the
   release file is read.
2. A diagnosis sub-block inside `1010000:1019999` is accepted only when a
   committed entry declares `purpose="diagnosis"`.
3. A sealed sub-block inside `2000000:2000499` is accepted only when a
   committed entry declares `purpose="sealed"`.
4. Every entry requires inclusive `start`/`end`, `release_id`, and
   `authorization_commit`.
5. The record cannot release a block outside the declared R0 diagnosis or
   escrow ranges.

An evaluator can therefore release C-V2G0 through a data commit after the
public freeze and reveal checks. No source change is required.

## RNG and development byte identity

The authorization check does not enter:

- `component_rng_key`;
- the four-part RNG tuple;
- the RNG digest;
- world or protocol spec hashes;
- process compilation;
- sampling or scoring.

Before and after the amendment, the complete Gate-2–5 development trace corpus
used for the audit had:

```text
trace count: 11000
SHA-256: c5f9ae0cd3e9d9bd3d473612e1dbf541e94a8a51d7e59e785cdb49835612a3a9
```

The fingerprint covers the exact Gate-2 family allocation, all Gate-3
composition-cell traces, both members of every Gate-4 mutation pair, and all
6,000 Gate-5 custody traces. The before/after digests are identical.

## Existing R0 artifact identity

No existing file under `results/R0/` changed. The 18-file committed artifact
set had the same aggregate path-and-content digest before and after:

```text
SHA-256: 6846da18fad5bfa3063abf7c01120b202ad34236bb8a0f1aa1e1c9aca5326bf9
```

This includes every original and repaired gate record, diagnosis,
authorization, byte-identity record, diff summary, stage report, and the
original R0 freeze manifest. This amendment record is a new post-freeze
addendum; it does not rewrite the historical freeze.

## Regression verification

The R0 regression tests establish:

- the committed empty record refuses the real C-V2G0 escrow;
- diagnosis seeds remain refused without a diagnosis release;
- a temporary file authorizes a released block without source modification;
- the acceptance test uses a patched synthetic escrow range, not the real
  C-V2G0 block;
- development sampling is identical with an empty, populated, or unavailable
  release record;
- development RNG keys retain stage, seed, namespace, and event index.

Focused authorization tests: **3 passed**.

Full old-plus-new unit suite:

```text
Ran 129 tests in 436.248s
OK
```

## Diff summary

Exactly these implementation/contract files change:

| File | Change | SHA-256 after amendment |
|---|---|---|
| `ref/world_ir.py` | file-backed authorization validation before non-development sampling | `3769511d9281486a3c49e1bd385396cd5759d726b264623ef982b49978f85bac` |
| `protocols/v2.g0-released-blocks.json` | new committed release record, initially empty | `539c510eb20354be0bd7464d1269a783ee49bb9d8e94f54e6341652a26ac531c` |
| `tests/test_v2g0_grammar.py` | refusal, release, synthetic escrow, and development-identity regressions | `5b427fd6566ef51355f49a9a5cd1d70294c069866a4444d967e3a968da034ad6` |
| `contracts/v2.g0-world-protocol-grammar.md` | public release mechanism and custody semantics | `7e4fad975ce91fae750cce8a041de1affd00856e8bef247a134b6be1ff2c25f1` |

This amendment record is the only new result artifact. No world constructor,
protocol constructor, composition operator, bridge, normalizer, oracle, gate
result, inherited suite file, scientific output, or RNG derivation changed.

## Pre-seal standing

The committed release list is empty. C-V2G0 remains unavailable until the
evaluator commits its exact released block. After such a commit, the frozen
sampler can execute that block without any source modification. The
four-layer linter may now answer its final question from the committed world,
protocol, composition, bridge, schema, and release records.

