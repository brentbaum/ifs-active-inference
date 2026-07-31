# V3.5 Amendment 2 — pre-seal freeze readiness

Status: **READY_FOR_C_V35B_SEAL_BEFORE_REPLACEMENT_GATE2**.

The candidate-common registration repair is complete. Registration uses one
shared `M_k=0` prior-predictive production for active and dormant candidates;
masking contributes likelihood one. No other observation channel changed.

The permanent Gate-1 battery passed. Cross-candidate registration evidence
difference was exactly `0.0`; delivered-versus-masked posterior error was
`7.22e-16`. Expanded marginal calibration and the independently reproduced
interventional topology fixture also passed.

The fresh pilot consumed `3523961:3525960` exactly once, ascending and
gap-free. Runtime events were persisted in every JSONL record before
aggregation, and record/file hashes were independently reproduced. Every
declared nonzero estimand carried its preregistered sign. Registration policy
movement averaged `1.24e-15`; maximum scientific-posterior movement averaged
`3.15e-14`, inside the unchanged `±0.01` ROPE. New numeric floors were frozen
mechanically in `protocols/v3.5-parameters.json`.

The Amendment-1 Gate-3 FAIL remains retained. Its floors and consumed Gate-2
and Gate-3 records are non-probative for the repaired construct. C-V35 and
escrow `4050000:4054999` are retired unopened.

Replacement Gates 2–3, original Gates 4–5, and C-V35B escrow
`4055000:4059999` remain unopened. Execution stops here so the evaluator can
seal C-V35B before replacement Gate 2. Full suites are green: V3 `55/55`; V2
`180/180`.
