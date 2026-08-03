# V3.7 Round-22 adjudication (INTERNAL)

**Authority.** Evaluator (Fable) as advisor per Brent's 2026-08-03
instruction; INTERNAL labeling, open to retroactive external review.

## Subject: A37-R1 FAIL_APPARATUS_THEOREM_PREMISE

## Ruling 22.1 — classification without a five-layer ladder

Classified GENERATOR_ONLY by direct code localization, verified by the
evaluator in `ref/v37.py::generate_v3_native_world` (mode inputs sampled
only for `index < structure.active_modes`): the schedule is truth-dependent,
so the worlds are not draws from the scorer's complete native prior
predictive and the calibration theorem's premise fails. The full five-layer
ladder is NOT required this time: the failing/passing statistic split
(active-count ECEs fail; all five target ECEs, equivalence-class ECE,
coverage, and edge ECEs pass) is the third occurrence of an
already-adjudicated signature (round 15), and the defect is explicit in the
code. Precedent discipline: a signature earns a diagnostic shortcut only
after its class has been fully diagnosed once and the new localization is
verified in source by the evaluator — both hold here.

## Ruling 22.2 — repair

Authorized, generator-only: make the v3.7 native mode-emission schedule
candidate-common, mirroring the round-15 repaired pattern in
`v36_round12.py` (all coordinates emitted on a schedule identical across
candidate truths; inactive-slot structure enters through the scorer's
likelihood, never through the generator's schedule). Differential audit;
round-15 replacement preconditions apply scaled to v3.7: staged
schedule-ladder check across all truth structures, complete-data identity,
schedule-only diff, frozen-hash verification.

## Ruling 22.3 — permanent candidate-common-schedule proof

New standing rule: before any native-population block opens, a zero-seed
proof enumerates the generator's emission/query schedule under EVERY
candidate truth structure on the enumerable dummy and asserts exact
schedule equality. This converts the round-15/round-22 class from
block-burning to pre-block. (Root cause of recurrence: the round-15 repair
lived in the v3.6 generator and the fresh v3.7 generator did not inherit
it; a proof, unlike a repair, transfers automatically to new modules.)

## Ruling 22.4 — seeds

A37-R1 block `3746000:3747999` consumed by the retained apparatus stop
(trace sha `1e5fed9a…`, evidence only). FINAL replacement A37-R2:
`3748000:3749999`, one-shot boundary as A-R1 (a blocking failure on a
correctly generated population stands scientifically; only a new apparatus
class returns here). Chain unchanged: A37-R2 → C37 → T37 → prediction
scoring.
