# V3.6 Round-18 adjudication (INTERNAL)

**Authority.** Evaluator (Fable) acting in the advisor role under Brent's
2026-08-03 instruction; INTERNAL labeling, open to retroactive external
review.

## Subject: gate-4 FAIL (two cells), derivative gate-5 FAIL

The immutable gate-4 verdict (FAIL: `split_context_slot`,
`protect_joint_policy`; PASS: `grow_mode_slot`, `prune_M1_G`,
`relate_L_PREC`) stands as written; custody is clean (5,000 worlds,
persisted-before-aggregation). Gate 5's FAIL is purely cumulative-blocking
on gate 4 — its primary effects, stakes checks, and robustness all passed —
so its disposition follows gate 4's. Attestations (6/6) and the 278-file
freeze manifest are recorded but the freeze is NOT declared while gate 4's
classification is open.

## Ruling 18.1 — classification question, diagnosis authorized

The two failures have distinct signatures and must be classified before
either is retained as a scientific finding:

- `protect_joint_policy`: restricted-prior identity exact (4.84e-14),
  independent oracle disagreement 0.8999. A triangulation split of this size
  is either an oracle construct error (apparatus; precedent: round-13
  partner-proof typed-channel misread) or a production defect invisible to
  its own internal identity (scientific). The magnitude (~0.9, near total
  disagreement on some coordinate) suggests a semantic mismatch, not
  numerics.
- `split_context_slot`: all identities exact; the failure is
  `licensed_support_positive_all = false` — the lesion zeroes ALL prior mass
  on some licensed structures in some worlds. Candidate explanation: the
  lesion is CLASS-HETEROGENEOUS — support-preserving where the truth does
  not route through split contexts, support-destroying where it does. The
  round-14 semantics assigned one class per lesion; if heterogeneity is
  real, the correct construct is per-world classification (conditioning
  identity where support is preserved; masking semantics with serialized
  null where the lesion destroys the world's support), mirroring exactly how
  round 14 resolved grow_mode_slot globally.

Authorized: a READ-ONLY + ZERO-SEED diagnosis (no new scientific world
seeds; retained traces plus enumerable dummies only):

- **D1 (protect_joint_policy)**: locate the argmax world/coordinate of the
  oracle disagreement in the retained trace; recompute the lesioned
  posterior for that configuration three ways — production, oracle, and an
  independent hand enumeration written fresh from the frozen production
  rules (the round-13 triangulation pattern); classify ORACLE_CONSTRUCT vs
  PRODUCTION_DEFECT with the disagreeing factor named.
- **D2 (split_context_slot)**: from the retained trace, enumerate exactly
  which licensed structures lose all mass, in which strata/world
  configurations, and verify by enumeration on the dummy whether every such
  loss is forced by the grammar (all derivations of those structures pass
  through the deleted production) — i.e. whether heterogeneity is
  structural fact or an apparatus support-accounting error.
- Both diagnoses write machine-readable records; no gate-4 statistic is
  recomputed, no verdict is amended by the diagnosis itself.

## Ruling 18.2 — disposition rules (pre-declared)

- If D1 = ORACLE_CONSTRUCT and/or D2 = structural class-heterogeneity: the
  affected cell semantics are repaired (oracle fix; per-world two-class
  semantics with serialized nulls), the repair is audited (diff +
  frozen-hash check, GENERATOR/VERIFIER-side only — the organism's
  scientific modules must be untouched), and ONE replacement gate-4 block is
  authorized: `3728000:3732999` (5 × 1,000, per-cell serial first rows).
  Precedent: round-15 GENERATOR_ONLY → repaired A-R1. The original FAIL
  remains in the ledger as a retained apparatus stop.
- If either diagnosis shows a genuine organism defect (a production whose
  lesion is non-selective in the composed grammar): that is a RETAINED
  SCIENTIFIC FINDING; gate 4 stays FAIL, gate 5 stays FAIL-derivative, and
  the profile carries both verbatim. No repair to the organism is
  authorized — the freeze then proceeds over the failing verdicts.
- Mixed outcomes compose cell-wise: only apparatus-classified cells rerun in
  the replacement block; any scientifically-failed cell's verdict is copied
  forward unchanged, not rerun.

## Ruling 18.3 — reveals held

The sealed C-V36A/B/C reveals and escrows remain untouched until gate 4's
classification resolves, since their release conditions were sealed against
a gate-complete freeze. T-V3-DO1 likewise waits.
