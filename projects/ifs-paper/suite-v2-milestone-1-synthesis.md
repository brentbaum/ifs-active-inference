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

---

# Addendum: the V2.3 arc (same night)

V2.3 was built, gated, and failed its sealed challenge twice; the repair loop is deliberately halted with the failure standing. The arc:

- **V2.3 (dee94c5):** gates 1–5 passed with strong open-assay results, including the full policy → transition → observation → persistence → G causal chain. Sealed C-V23: **FAIL on all four tests** — formation collapsed on a novel schedule family (4/60 vs 0.79 in development), false formation under high control, and twelve acute jumps over the frozen step bound. Diagnosis: the formation boundary was fitted to development-schedule surface features, and the acute path behaved near-boolean.
- **V2.3.1 (7d5650c):** parametric recalibration (formation now tracks uncontrollability and overwhelm-precision variables; surface features add 2.5% incremental R²) plus a structural per-slice evidence bound with an analytic guarantee. Sealed C-V23b: continuity **PASSED prospectively** (0/492 exceedances) and the controllability dose-response has the right shape (isotonic p = 0.006), but calibration missed (0.19 vs 0.60 at zero control) and **the persistence effect inverted**: avoidance-available worlds ended with *lower* persistent-model evidence than matched replay (−2.97 [−3.79, −2.15]; realized-avoidance correlation −0.63).

The inversion is the finding of the night. Under honest model comparison, a persistent structure that stops receiving evidence loses ground through its complexity penalty — so in this strain, avoidance starves the frozen model rather than protecting it. The C1 claim requires an asymmetry the current world model does not contain: **avoided catastrophe must count as evidence for the threat model** (the safety-behavior attribution loop — "nothing bad happened *because* I avoided"), so that working avoidance generates the model's own confirmation. Exp 50's strain had this authored in; the ladder has to derive it, and that is a theory-level design decision about the world/attribution structure, not a parameter. Halted here after two burned challenges precisely to avoid tuning-by-exhaustion and to put that decision where it belongs.

**Standing after tonight:** V2.0, V2.1, V2.2.1 — built, gated, prospectively validated (with the V2.2 repair arc). V2.3.1 — frozen, continuity solved, formation dose-response shaped correctly, persistence-under-avoidance open with a sharp statement of the missing mechanism. V2.4+ blocked, correctly, by the ratchet.

**Decision needed (Brent):** whether V2.3.2 adds the counterfactual-attribution structure (avoided-outcome evidence routed to the threat model — the formal face of safety-behavior maintenance, with its own gate-1 semantic proof and a fresh sealed challenge), or whether C1's persistence claim should be weakened to activation-dependent maintenance. The first is the clinically faithful reading; it is also a new mechanism, not a repair.
