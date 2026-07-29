# C-V2G0 pre-seal linter record (evaluator, 2026-07-29)

**Committed BEFORE the challenge plaintext hash, per the four-layer linter. Dry-runs used public development seeds 1000000 and 1000001 via `protocol_ir.dry_run_schema` (construction/support/schema/field-presence only; `scientific_scores_inspected=false` in every audit).**

## Four-layer verdicts
1. **Inference expressibility** — the challenge requests only apparatus fields: compile success, sample success, exact world log probability, `independent_world_log_prob` parity, restriction normalizers via `public_normalizer`, spec/output-schema hashes, RNG component keys. All exist in the frozen public API. PASS.
2. **World expressibility** — four cells, each constructed solely from public process kinds (`ordered_drift`, `static`, `change_point` with `onset_window`, `recurrent_context` with restriction, `shared_latent`, `mixture`, `markov`, `joint_episode`, `masked_observation`, `action_contingent`). PASS.
3. **Protocol expressibility** — observation channels (incl. `path` into shared-latent targets and `masked_by`) and a declared do(action) sequence; no hidden code. PASS.
4. **Composition expressibility** — disjoint product (cell A), `shared_latent` broadcast (cell B), `mixture` + candidate-common mask (cell C), `run_bridge` with declared initial_state on a non-context-split family (cell D). All are actual public operators. PASS.

## Traceability (cells identified by letter; private parameters sealed)
| Cell | Public obligation | Constructors | Composition | Conditioning | Dry-run (2 seeds) |
|---|---|---|---|---|---|
| A | spec §2.1 process primitives + product | ordered_drift (cue subset), static, change_point(onset_window) | disjoint product | exact onset-window renormalization (public) | construction/support/schema PASS; deterministic hash cc9361…df27 |
| B | spec §2.1 shared latent + restriction | recurrent_context(restriction: at_least_one_switch, old_context_recurrence, minimum_visits), shared_latent | shared-latent broadcast to two cue targets | exact path-restriction normalizer (public) | PASS; aa4208…629b |
| C | spec §2.1 mixture + candidate-common nuisance | mixture(markov, ordered_drift), joint_episode, masked_observation | mixture on common scope + product + masked channel | none | PASS; f7f69b…31f6 |
| D | spec §2.2 generic bridge | ordered_drift, action_contingent | run_bridge(initial_state, …) + do(action) | none | PASS; b79f5e…d4c6 |

- Scientific scoring during dry-run: **false** (flag recorded in every audit).
- New code required: **false**.
- Escrow release mechanism: data-commit via `protocols/v2.g0-released-blocks.json` (amendment 75520bd) — no source change at run time.
- Criteria are apparatus-only (spec §2.3 gate 6): compile-after-reveal with zero source change; sample on escrow; independent log-probability parity ≤ 1e-10; schema and custody. The 7-item criterion audit: distinct (1), construct = apparatus executability (2), tolerance 1e-10 is the standing exactness scale (3), attainability demonstrated by dry-run construction (4), no contradiction with viewed data (5), failure interpretations pre-committed in the plaintext (6), classes scientific-apparatus/semantic/custody (7).

## Final blocking question
Could the exact sealed population be generated and scored after reveal with zero source-code change? **YES** (dry-run construction succeeded through public entry points; escrow acceptance is a data commit).
