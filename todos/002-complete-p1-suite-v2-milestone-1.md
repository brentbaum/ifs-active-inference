---
status: complete
priority: p1
issue_id: "002"
tags: [simulation, exact-inference, suite-v2]
dependencies: []
---

# Suite v2 milestone 1

## Problem Statement

Implement the Python exact reference for Suite v2 stages V2.0–V2.2 under
`projects/emergence-suite/v2/`, satisfying gates 1–5 and producing freeze
candidates without reading archived Experiment 51 materials or committing.

## Findings

- The adopted contract is `projects/ifs-paper/suite-v2-spec.md`.
- The implementation must use plain Python and NumPy, with an independently
  authored brute-force checker and a one-posterior audit.
- Stage analysis plans and parameter blocks must exist before protocol runs.

## Proposed Solutions

1. A general finite factor graph with variable elimination plus a separately
   implemented Cartesian-product oracle. This is small, inspectable, and
   supports every milestone primitive.
2. Bespoke enumeration per assay. This is shorter initially but would violate
   the reusable-kernel and independent-checker intent.

## Recommended Action

Use option 1, compiling stage vocabulary to generic categorical factors. Keep
all protocol outputs in posterior, parameter-posterior, or evidence stores and
calculate scientific readouts on demand.

## Acceptance Criteria

- [x] V2.0 gates 1–5 pass and freeze manifest is generated.
- [x] V2.1 gates 1–5 pass and freeze manifest is generated.
- [x] V2.2 gates 1–5 pass and freeze manifest is generated.
- [x] Full test suite passes using only Python, NumPy, and the standard library.
- [x] Milestone report records actual gate and assay numbers, including failures.

## Work Log

### 2026-07-27 - Contract intake

**By:** Codex

**Actions:**
- Read the complete adopted specification and repository instructions.
- Chose a finite factor-graph kernel plus independent brute-force oracle.
- Confirmed the worktree has unrelated changes that must remain untouched.

**Learnings:**
- Broadcast must be a separately removable factor, not the local likelihood.
- V2.2 transfer must be mediated by posterior revision of G.

### 2026-07-27 - Milestone completion

**By:** Codex

**Actions:**
- Implemented the typed factor kernel, elimination engine, independent
  Cartesian-product oracle, conjugate learning, deterministic RNG streams, and
  one-posterior audit.
- Implemented and ran V2.0–V2.2 gates in order with 64-seed stage blocks,
  cumulative regressions, contracts, dummy bundles, decisions, gate reports,
  and freeze manifests.
- Ran 26 unit/integration tests and verified every manifest hash.

**Learnings:**
- A doubly stochastic broadcast CPT provides the required global effect while
  exactly preserving the marginal local calculation.
- Paired developmental histories isolate root association from perceptual
  recognition in the V2.2 2×2.
