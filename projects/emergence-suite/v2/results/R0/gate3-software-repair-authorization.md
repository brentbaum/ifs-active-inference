# R0 gate-3 software-repair authorization (evaluator, 2026-07-29)

## Classification
Pure software error in verdict aggregation (established invalidate-and-repeat rule; precedents: V2.3.3 seed-guard, V2.4.4 cue-shape). The gate-3 runner stored the custody fact `new_code_required: false` in a checks mapping aggregated by `all(checks.values())`, so a satisfied negative criterion registered as a failed positive one. The diagnosis localizes the defect entirely to result encoding: all 2,000 seeds executed, all six cells passed construction/support/schema dry-runs with `scientific_scores_inspected=false`, exact trace log-probabilities matched, no cell failure, escrow untouched.

## Authorized repair, narrowly
- Rename the check to positive polarity (e.g. `zero_new_code_required: true`) or exempt declared-negative custody facts from the positive aggregation — encoding only.
- No world constructor, protocol constructor, composition operator, restriction normalizer, bridge, schema, RNG key, or dry-run record may change.
- The original gate-3 FAIL record is retained as written; the repaired execution is recorded separately (`gate-3-repaired.json`).

## Mandatory verification
1. Re-execute gate 3 on the same block 1001000:1002999 with the repaired encoding; every recorded per-world/per-cell quantity must be bitwise identical to the original execution — the ONLY permitted difference is the verdict aggregation fields.
2. Regression test pinning the polarity convention (negative custody facts must aggregate correctly).
3. Full unit suite green.
4. Diff summary committed listing exactly what changed.

Disclosed in the R0 freeze record and at the next external consultation.
