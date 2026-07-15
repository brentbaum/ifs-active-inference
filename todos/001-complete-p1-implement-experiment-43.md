---
status: complete
priority: p1
issue_id: "001"
tags: [julia, simulation, ifs-paper, experiment-43]
dependencies: []
---

# Implement and run Experiment 43

## Problem Statement

Experiment 43 exists only as a proposed handoff specification. The repository
does not yet contain the four-variable learned bundle model, matched
factorized/replay controls, guidance arms, contact observation, pilot freeze,
or frozen confirmation artifacts required to evaluate the claims.

## Findings

- Experiments 39–42 provide reusable three-level Gaussian inference,
  second-order precision updates, action selection, matched factorization, and
  paired confirmation patterns.
- `UnifiedBeautifulLoop.jl` hard-codes three channels, so the narrowest safe
  extension is a four-channel adapter in the new module while reusing its pure
  Gaussian and hyper-update helpers.
- The current branch contains unrelated manuscript edits that must remain
  untouched, and the Experiment 43 spec explicitly excludes manuscript edits.

## Proposed Solutions

### Option 1: Generalize the existing unified modules

**Approach:** Parameterize all existing three-channel code and migrate prior
experiments to the generic implementation.

**Pros:** One generalized hierarchy.

**Cons:** Broad regression surface and unnecessary changes to frozen results.

**Effort:** High

**Risk:** High

### Option 2: Add a focused four-channel adapter

**Approach:** Implement Experiment 43 in a new module, reuse pure optimizer
helpers, and preserve Experiments 39–42 unchanged.

**Pros:** Auditable, small regression surface, matches the handoff simplicity
rule.

**Cons:** A small amount of adapter code remains experiment-specific.

**Effort:** Medium

**Risk:** Medium

## Recommended Action

Use the focused four-channel adapter. Execute the seven tasks in the handoff in
order, freeze after pilot seeds only, open confirmation seeds once, and record
stage-specific outcomes without editing the manuscript.

## Technical Details

**Affected files:**

- `projects/emergence-suite/continuous/src/IFSBundleInquiry.jl`
- `projects/emergence-suite/continuous/src/ConfirmIFSBundleInquiry.jl`
- `projects/emergence-suite/continuous/scripts/run_ifs_bundle_inquiry_pilot.jl`
- `projects/emergence-suite/continuous/scripts/run_confirm_ifs_bundle_inquiry.jl`
- `projects/emergence-suite/continuous/test/runtests.jl`
- `projects/emergence-suite/continuous/README.md`
- `projects/ifs-paper/experiment-43-ifs-bundle-guided-inquiry.md`

## Resources

- `projects/ifs-paper/experiment-43-ifs-bundle-guided-inquiry-spec.md`
- `projects/emergence-suite/continuous/src/UnifiedRelationalAgent.jl`
- `projects/emergence-suite/continuous/src/ConfirmRelationalActionInteraction.jl`

## Acceptance Criteria

- [x] Task 1 tests and minimal four-node learned target are committed separately.
- [x] Four-channel Gaussian hierarchy and 13-component precision field pass invariants.
- [x] All five guidance arms use one action/budget interface with exact replay.
- [x] Contact is observational, paired identically, and stress-tested.
- [x] Pilot uses only seeds 16901–16910 and freezes config and criteria.
- [x] Confirmation uses untouched seeds 17001–17020 exactly once and writes every required artifact.
- [x] Stage 43A/43B/43C statuses and bounded interpretation are documented without manuscript edits.
- [x] Full Julia test suite passes.

## Work Log

### 2026-07-15 - Execution started

**By:** Codex

**Actions:**

- Read the complete handoff and Experiments 39–42 implementation patterns.
- Selected the focused adapter to preserve frozen prior experiments.
- Confirmed the work is already on a feature branch and isolated unrelated
  dirty manuscript files from the implementation scope.

**Learnings:**

- The spec is sufficiently explicit to proceed without further design choices.
- The existing pure variational helpers can be reused while channel indexing
  and precision forecasting stay local to Experiment 43.

## Notes

- Never stage or edit `draft-v11-theory.md`, `draft-v11-outline.md`, or other
  manuscript files during this work.
- Do not use confirmation seeds before the freeze commit exists.

### 2026-07-15 - Pilot completed

**By:** Codex

**Actions:**

- Committed the red four-node tests and minimal learned target separately.
- Implemented the 13-component precision field, all evidence-selection arms,
  exact replay, contact stress cells, adaptive/rigid/local precision controls,
  and the gated contextual Dirichlet policy learner.
- Ran seven retained pilot attempts using only `16901:16910` and froze the
  successful two-edge configuration, seed ranges, and unchanged criteria.

**Learnings:**

- A 16-cell conditional table needs a separate, non-leaking training stream;
  32 complete scenes were too sparse even though the inference code was valid.
- One coupling edge can create binding and action effects, but cannot transfer
  through a two-packet sample after both endpoints are consumed; two connected
  edges are the minimum retained structure.
- Stage 43C is a separate policy-learning result: it required an explicit
  action table and could not be inferred from the learned precision field.

### 2026-07-15 - Frozen confirmation and handoff completed

**By:** Codex

**Actions:**

- Created freeze commit `84c702a2bd7b83def669c999141674b9fcdccda7`
  before opening confirmation seeds.
- Ran `17001:17020` once through the guarded confirmation runner and committed
  the immutable raw result bundle as
  `a2fceafbc36602eb9644af496d0e1b7b71283539`.
- Recorded `support` for 43A, 43B, 43C, and the stress cell while preserving
  negative and bounded results in the experiment note.
- Reran the complete Julia suite after documentation; every test passed.

**Learnings:**

- The frozen result supports the configural bundle and guide-error calibration
  claims, but the inquiry advantage did not grow in the joint world.
- Post-scaffold root accuracy and first-action retention passed, while the
  narrower unsampled-component transfer estimate remained small.
