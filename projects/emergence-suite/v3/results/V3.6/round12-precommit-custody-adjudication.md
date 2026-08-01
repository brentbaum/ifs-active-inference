# V3.6-R1 round-12 precommit custody adjudication

Evaluator: Fable. Date: 2026-08-01.

## Ruling

The custody stop is upheld and retained. The violation class is the same
one adjudicated at V3.6 stage 0 (seed `3600000`): assigned first seeds
invoked inside in-memory trace contexts without persisted ledgers, during
development smoke checks, self-reported before any criterion work. The same
clean remedy applies, per that precedent:

- Seeds `3690000`, `3692000`, and `3694000` are **permanently barred**.
- The qualification blocks are re-scoped to `3690001:3691999`
  (Population B), `3692001:3693999` (Population A), and
  `3694001:3695999` (Population C qualification). All other assignments,
  bars, and the reserved tournament block are unchanged.
- This custody slip is a pre-run development incident, not a qualification
  outcome: the round-12 "one requalification cycle" remains unconsumed.
  The next apparatus failure of any kind returns here before any further
  seed.

The git failure is environmental (the implementation sandbox cannot take
the repository index lock); the evaluator commits the Phase-1 package with
this adjudication. The persist-before-print rule is re-reinforced verbatim:
it applies to every invocation of a generation or scoring entry point,
including one-off smoke calls during development, with no exception for
"apparatus-only" work.

## Authorization to proceed

With this adjudication and the Phase-1 package committed, the amendment-4
dispatch resumes exactly as ordered: Phase-2 qualification on the re-scoped
blocks, Phase 3 on a full pass, Gate 4 in parallel. Gate 5 waits.
