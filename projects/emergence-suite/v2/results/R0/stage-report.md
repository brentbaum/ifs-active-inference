# R0 / V2.G0 stage report

**Stage type:** apparatus only  
**Status:** `COMPLETE_GATES_1_TO_5_WITH_TWO_AUTHORIZED_SOFTWARE_REPAIRS`  
**Date:** 2026-07-29  
**Clinical or psychological claim:** none  
**Sealed challenge:** not run; C-V2G0 remains evaluator custody

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
| 6 — C-V2G0 | `2000000:2000499` | Not opened or run | **UNRUN — EVALUATOR CUSTODY** |

Both original failures, diagnosis stubs, evaluator authorizations, repaired
records, byte-identity audits, and diff summaries remain in the freeze record.
Neither repair changed a world, scientific result, inherited file, gate
criterion, RNG key, schema, normalizer, bridge, or seed.

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
- C-V2G0 escrow `2000000:2000499` was not accessed.
- Component RNG keys contain stage version, seed, component namespace, and
  time/event index.
- Seed rejection is absent; restricted finite paths are sampled directly from
  their exactly normalized conditional support.

R0 Gates 1–5 are complete. Progression to a future seal remains an evaluator
action under the permanent pre-seal custody procedure.

