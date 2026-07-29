# V2.5a completion development failures

## Gate 1 — FAIL

Retained verbatim from `gate-1.json`:

- `6_missing_tokens_neutral: false`
- `8_no_direct_format_to_H_cfg: false`

The execution stopped before Gate 2. See `gate-1-diagnosis-stub.md`.

The evaluator classified this as a pure verdict-encoding software error and
authorized the declared-tolerance repair. The repaired execution passes in
`gate-1-repaired.json`; this original failure remains part of the record.

## Gate 5 — FAIL

All completion-stage primary gates and all 5,000 robustness-world exact
identities passed. Cumulative custody failed:

- the full fast suite retained the two failures already disclosed by
  performance amendment 1: the stale pre-release R0 escrow-inaccessibility
  assertion and the V2.4.4 manifest assertion that does not include the
  authorized performance changes;
- effective manifest verification also found historical base manifests
  without addenda for authorized later changes, including the performance
  amendment and post-seal R0 release/stage-report updates.

The formal Gate-5 verdict is retained as `FAIL`. No freeze-readiness report
or completion freeze manifest was produced. See `gate-5-diagnosis-stub.md`
and `gate-5-full-fast-suite.log`.
