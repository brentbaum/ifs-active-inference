# V3.7 Round-20 adjudication (INTERNAL)

**Authority.** Evaluator (Fable) as advisor per Brent's 2026-08-03
instructions ("play the part of the advisor"; "ok let's try 3.7. predict.
then go."). INTERNAL labeling, open to retroactive external review.

## Ruling 20.1 — sequencing

The V3.6 chain completes first: replacement gate 4 → gate-5 recompute →
freeze declaration → evaluator reveals C-V36A/B/C → final v3.6 profile.
V3.7 work begins only after the freeze is declared, so the two arcs never
share an open block. T-V3-DO1 runs after the v3.7 tournament (it probes
do-over timing and is more informative on whichever organism is current).

## Ruling 20.2 — V3.7 registration discipline

The registered prediction (registered-prediction.md, committed with this
file) is sealed by its commit hash BEFORE implementation. Order of work:

1. **Design freeze**: exact A1/A2 specification (persistence grid, danger
   prior odds, factor placement) written and committed before any pilot
   seed. The design may consult v3.6 code but NO seed may be spent tuning
   the grid: the persistence prior spans {0.80, 0.90, 0.97} and danger prior
   odds are fixed at the v3.6 stratum-agnostic uniform convention unless the
   design freeze documents a construct-level (not performance-level) reason.
2. **Zero-seed proofs** under the full standing battery: fixture-identity
   proofs for the v3.7 adapter, generator-coherence proof, key-set equality
   assertions, log-space predicates, mutation tests, forecast-semantics
   proof 15 extended to the new latents (marginalization audited).
3. **Populations**: A37 (v3.7 complete native prior predictive, blocking)
   block `3734000:3735999`; B is NOT rerun (v2 untouched; its round-13 PASS
   carries); C37 (external population, descriptive) block `3736000:3737999`.
4. **Tournament T37**: block `3740000:3745999`, 6,000 worlds, same five
   families, same delta, same Pareto-vector no-aggregate rule, per-stratum
   serial first worlds, one-shot. The v3.6 tournament verdict is never
   rescored or amended; T37 is a NEW result against the standing prediction.
5. **Scoring the prediction**: a post-run record maps every numbered
   prediction and falsifier to outcome, with no softening language either
   direction.

## Ruling 20.3 — custody

All standing rules apply unchanged (honest stops, bar-and-reallocate,
incremental hash ledgers, finite guards, serial first worlds, evaluator
commits). Dev-namespace allocations above are recorded in the seed map with
this round's note. V3.6's sealed challenges and escrows are untouched by the
V3.7 arc; C-V36A/B/C test the v3.6 organism and are revealed under the
v3.6 freeze per round 19.
