# R0 / V2.G0 stage report

**Stage type:** apparatus only  
**Status:** `COMPLETE_GATES_1_TO_6_SEALED_APPARATUS_PASS`
**Date:** 2026-07-29  
**Clinical or psychological claim:** none  
**Sealed challenge:** C-V2G0-C PASS; R0 exit condition met

## Outcome

R0 closes the five protocol-generation expressibility gaps localized after
V2.4.4:

1. process assignment to cue/latent subsets;
2. change-point onset windows with exact conditional mass;
3. recurrence-conditioned context paths with published exact normalizers;
4. product and mixture composition over disjoint scopes;
5. a world-family-parameterized bridge from an arbitrary banked state.

It also supplies the full public primitive set, shared-latent composition,
action-contingent transitions, candidate-common availability, joint episodes,
partner processes, joint-policy outcomes, independent exact probability
recomputation, and custody-complete traces.

No inherited V2.0–V2.4.4 or V2.5a-in-flight file was changed.

## Gate standing

| Gate | Seed block | Immutable execution standing | Final standing |
|---|---:|---|---|
| 1 — semantic proofs | none | 25 tests now present; original Gate-1 record contains the required 24 proofs | **PASS** |
| 2 — generator recovery | `1000000:1000999` | 1,000 worlds; family accuracy 1.0; scope accuracy 1.0; maximum log-probability discrepancy `5.329070518200751e-15`; zero out-of-support worlds | **PASS** |
| 3 — composition battery | `1001000:1002999` | Original `FAIL` retained: satisfied negative custody fact was encoded with negative polarity in an all-positive check mapping | **PASS AFTER AUTHORIZED PURE-SOFTWARE REPAIR**; all recorded non-verdict fields byte-identical |
| 4 — selective mutations | `1003000:1003999` | 500 process mutations and 500 scope mutations; zero failures; unrelated traces/RNG keys and inherited posterior bitwise identical | **PASS** |
| 5 — cumulative regression | `1004000:1009999` | Original `FAIL` retained: verifier omitted the committed V2.4.4 manifest addendum | **PASS AFTER AUTHORIZED PURE-SOFTWARE REPAIR**; all recorded non-manifest fields byte-identical |
| 6 — C-V2G0-C | `2000000:2000499` | 500 worlds, raw traces sealed before criteria; four prior-artifact seal outcomes retained | **PASS — ALL FOUR SEALED CRITERIA; R0 EXIT MET** |

Both original failures, diagnosis stubs, evaluator authorizations, repaired
records, byte-identity audits, and diff summaries remain in the freeze record.
Neither repair changed a world, scientific result, inherited file, gate
criterion, RNG key, schema, normalizer, bridge, or seed.

## Gate-6 four-seal history

The apparatus challenge required four sealing events. Every outcome is
retained:

1. C-V2G0 first sealing stopped before execution because the release record
   used a schema the frozen parser could not read.
2. C-V2G0 second attempt stopped before execution because JSON stringified
   numeric change-point keys and the exact document could not compile.
3. C-V2G0-B stopped before execution because its fresh escrow block lay
   outside the frozen `SEALED_ESCROW` range.
4. C-V2G0-C used the exact sealed Python literal, a parser-valid contained
   release, and the original unconsumed escrow. It passed all four criteria.

The first three verdicts are immutable `STOP_AS_SEALED_PROSPECTION_FAILURE`
records and consumed zero seeds. C-V2G0-C alone consumed the escrow, exactly
once in ascending gap-free order.

Gate-6 results:

- 500/500 world and protocol runs completed;
- maximum independent log-probability discrepancy:
  `3.552713678800501e-15`;
- Cell-A restriction normalizer: production/oracle `0.6 / 0.6`;
- Cell-B restriction normalizer: production/oracle
  `0.7726410158022948 / 0.7726410158022935`;
- one output-schema hash per cell and all required trace custody fields;
- no diagnosis-reserved seed touched.

The raw trace seal was written before criterion evaluation and hashes all four
cell files plus every per-seed record. Its SHA-256 is
`2d046ef8a4c5fa7100c89e7b10546d71cc72168266a4fa6c95104e2a5bcfd6e3`.

The post-run full suite passed 130/131 tests. The sole failure is the
historical pre-release assertion that the real escrow must remain
inaccessible; the evaluator data record now intentionally releases it. No
source or test changed, and the failure does not rewrite the sealed PASS.

## Gate-5 cumulative verification

The repaired V2.4.4 manifest-chain audit:

- read the 86-entry base manifest;
- overlaid the committed addendum;
- verified the effective 87-file chain;
- recorded SHA-256 custody for both manifest files;
- found zero mismatches.

The final old-plus-new suite passed **126 tests**. The repaired execution took
`417.841s` according to unittest (`418.006s` enclosing runtime). The original
non-manifest unit-suite record is retained verbatim for repair byte identity;
the fresh timing is disclosed separately in
`gate-5-repair-byte-identity.json`.

## Mechanized four-layer pre-seal linter

The public entry point for every future sealed cell is:

```python
from ref.protocol_ir import dry_run_schema

audit = dry_run_schema(world_spec, protocol_spec, public_development_seed)
```

`dry_run_schema` mechanizes the four required expressibility layers:

1. `compile_world(world_spec)` — world construction, scope, finite support,
   exact restriction normalizers, and composition validity;
2. `compile_protocol(protocol_spec)` — protocol construction, interventions,
   observation-channel sources, and requested schema;
3. `run_protocol(...)` through the generic family-parameterized bridge path —
   world/protocol composition and output construction;
4. `SchemaAudit` — construction success, support, lengths, requested-field
   presence, schema hash, deterministic hash, and the enforced custody fact
   `scientific_scores_inspected=False`.

Each private challenge row must still map its public obligation, frozen world
constructor, frozen protocol constructor, composition operation, bridge path,
conditioning declaration, and requested readouts to this entry point. It must
dry-run on at least two public development seeds. The public row shape and six
development cells are frozen in
`protocols/v2.g0-public-dummies/cells.json`.

The blocking pre-seal question remains:

> Can the exact sealed population be generated and scored after reveal with
> zero source-code change?

A false answer blocks sealing. The linter does not inspect a posterior,
evidence, margin, transfer, model choice, or other scientific score.

## Custody

- Development blocks `1000000:1009999` were used only by their declared gates.
- Diagnosis block `1010000:1019999` was not accessed.
- C-V2G0-C escrow `2000000:2000499` was consumed exactly once, ascending and
  gap-free, after a data-only release and raw-first trace seal.
- Component RNG keys contain stage version, seed, component namespace, and
  time/event index.
- Seed rejection is absent; restricted finite paths are sampled directly from
  their exactly normalized conditional support.

R0 Gates 1–6 are complete. The sealed apparatus challenge passed and the R0
exit condition is met.
