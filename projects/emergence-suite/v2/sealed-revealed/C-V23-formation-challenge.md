# Sealed stage challenge C-V23 — formation under a novel developmental schedule

**Sealed by evaluator before V2.3 development. Runs on the frozen V2.3 stage with zero new code. The spec publicly names this challenge's family (chronic misattunement + one acute event × avoidance availability); the sealed content is the specific schedule, parameters, cells, and criteria below.**

## Configuration
Single agent (V2.2.1 stack + V2.3 formation machinery). Developmental schedules over 80 slices:
- **Chronic segments:** moderate-intensity misattunement observations at irregular preregistered-by-seed intervals (generator draws; mean rate varies per world across a low band).
- **One acute event:** high-intensity, at a seed-drawn slice in [30, 55], unannounced.
- **Controllability:** the acute event's context has action-dependent world transitions in high-control cells (agent policies genuinely modulate exposure/outcome) and action-independent transitions in low-control cells.
- **Avoidance:** in avoidance-available cells, a policy exists post-event that reduces encounter probability with event-linked contexts; in unavailable cells, exposure follows the same marginal schedule as the agent's realized encounters in a paired available-cell world (matched replay, paired streams).

Cells (2×2): low/high control × avoidance available/unavailable. 60 worlds per cell, escrow block C-V23 (seeds 807203:807502), paired streams across cells within seed.

## Tests
1. **Joint formation boundary:** the persistent-organization structure wins model comparison (cumulative evidence margin ≥ 1 nat) in ≥ 45/60 low-control worlds and in ≤ 12/60 high-control worlds (same schedules; controllability is the only difference). No formation predicate may be consulted anywhere — the win is the formation.
2. **Continuity:** the persistent model's posterior trajectory across the acute event rises without a single-slice jump exceeding the preregistered step-injection bound (no boolean write signature); bound = the 99th percentile single-slice change observed in V2.3's own open development assays, recorded in its freeze before this challenge is revealed.
3. **Active persistence:** among low-control formed worlds, avoidance-available cells show (a) reduced realized encounter rate with disconfirming contexts vs their matched-replay pair, and (b) end-of-run persistent-model evidence margin higher than the pair by a margin bounded away from zero (95% CI) — persistence through realized avoidance, with the mediator computed from actions and transitions only.
4. **Mediation:** across formed worlds, end-state persistence correlates with realized avoidance (computed) and NOT with scheduled dose after conditioning on realized avoidance (partial correlation CI covering 0). Dose must not have a route around action.

Pass = all four. Failures localize by test and are retained as written.
