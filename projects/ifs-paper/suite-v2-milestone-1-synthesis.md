# Suite v2, milestone 1: synthesis

**Status:** Complete, 2026-07-27. Spec: `suite-v2-spec.md`. Record: `projects/emergence-suite/v2/`. Commits: spec bd095e1 → seals 2756aea/108f34b → stage freezes 60ba6e0 → gate 6 44fb872 → v2.2.1 347482f → C-V22b a1e4154.

## What stands

The first three rungs of the ladder are built, gated, and prospectively validated in the Python exact reference:

- **V2.0 kernel.** Typed factor graphs, exact elimination, conjugate learning, finite model comparison — every reported posterior automatically checked against an independent brute-force oracle (max deviation 3.2e-17). Sealed challenge C-V2.0 (novel collider/action-controlled graph, fresh in-runner oracle): PASS.
- **V2.1 recursive precision.** Per-channel precision that provably controls the likelihood entering inference (sharpening 0.33); a global hyper-state whose broadcast is a severable factor — a doubly stochastic CPT gives the global effect while exactly preserving the local marginal, which is the dissociation Experiment 51 never achieved. Cross-latent log-odds effect 0.93. Sealed challenge C-V2.1 (three channels with crossing reliability): PASS — inferred precisions cross with the true reliabilities, a confident-but-miscalibrated channel is contained, and severing broadcast preserves local calibration while the global adjustment disappears.
- **V2.2 identity root and structural transfer.** Cue-root structure learned from developmental history (recovery 96.9%); the seam — local precision → global depth → root uptake → transfer — shows the required three-way pattern (transfer 0.196 broad / 0.102 broadcast-off / 0.030 narrowed) with mediation enforced by construction check, not assumption (fixed-G transfer exactly zero).

## The instructive failure

Sealed challenge C-V22 failed its floor control: treating a *non*-associated cue moved the root in 31/60 worlds. Localization showed mediation intact — the leak ran through the association posterior itself. Diagnosis (before any repair): the continuous Beta learner **cannot represent exact non-association** — no sample size concentrates it on zero (bias −0.002 and coverage 0.97 at n=180, i.e., calibrated; exact-zero mass 0 even at n=1600, i.e., representationally incapable). The repair was structural and prior-side only: a spike-and-slab existence comparison with posterior model averaging — no clamps, no transfer patches. Under the fresh sealed challenge C-V22b (authored and hash-committed before repair work began), the fix passed everything, including the clause designed to catch a fake: zero-cue leakage now *shrinks monotonically with developmental evidence* (0.0052 → 0.0004 → 0.00004), which is what a real resolution of "Bayesian humility vs. defect" looks like.

The theoretical content of the episode: **whether a cue belongs to an identity's organization must be a discrete structural question inside model comparison, not a graded parameter** — a small formal echo of the paper's redescription claim, discovered by a sealed test.

## Discipline notes

Every gate, freeze, seal, reveal, and failure is committed in order with hashes; the C-V22 FAIL stands unedited beside its repair; the burned challenge was replaced, never reused; all verification (tests, manifest rehashes) was re-run independently by the evaluator before each freeze commit.

## Next

V2.3 (formation and persistence) is the next rung, per spec §4 — it may begin now that the seam holds. The milestone's six exit conditions (spec §8) are all met.
