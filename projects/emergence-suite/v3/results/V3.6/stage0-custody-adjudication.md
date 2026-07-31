# V3.6 stage-0 custody adjudication

Evaluator: Fable. Date: 2026-07-31.

## Ruling

The custody stop is upheld and retained. The violation class
(`runtime_trace_not_persisted_at_execution`) is the same one recorded against
the evaluator's own C-V35 pre-seal pilots; the implementation's immediate
self-report after a single seed, before any criterion or floor work, is the
custody discipline working as intended.

Because the printed readout was not preserved verbatim, a
reconstruction-with-byte-comparison route (V3.1 amendment) cannot be
verified for this seed. The clean route is chosen instead:

- **Seed `3600000` is permanently barred.** It may never be consumed again
  in any role.
- **The V3.6 attainability pilot block is re-scoped to `3600001:3603999`**
  (3,999 seeds). All other block assignments are unchanged.
- The mechanical pilot-to-floor rule and every stage requirement from the
  dispatch remain binding and unmodified.

## Reinforced rule (binding, all remaining V3.6 work)

Every serializing trace context must persist `sink.events` and the
associated per-world records to their JSONL ledger, with hash records
written, BEFORE the process prints, aggregates, or exits — including
one-seed smoke checks. Terminal output is never custody.

One custody incident is closed by this record. Any further custody failure
in V3.6 returns to the evaluator before any additional seed is consumed.
