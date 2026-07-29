# V2.4.4 gate-5 software-repair authorization (evaluator, 2026-07-29)

## Classification
The gate-5 preflight failure is a **pure software error**, not a scientific failure: the frozen public parameter block declares cue-count support {2,3,4}, but the cue_count=4 cell was never exercised by any prior gate (gates 1–4 and all prior stages ran 3-cue worlds), and three families crash there (cue-local `KeyError: 'cue_4'`; context split and change point `IndexError: axis 0 size 3`). No criterion was evaluated; no world was scored; the cell is unexecutable.

Precedent: the C-V233-M-bank seed-authorization defect (FAIL_UNEXECUTABLE → guard repaired at the correct layer → byte-identical science verified → rerun). The same invalidate-and-repeat treatment applies: repairing a crash that prevents execution of a declared cell is an apparatus repair, not a scientific repair, and does not touch the round-6 forbidden-changes list.

## Authorized repair, narrowly
- Fix the cue-indexing defect so all five families execute at cue_count ∈ {2,3,4} as the frozen parameters declare (generalize the hard-coded 3-cue array shapes/keys at the correct layer).
- No frozen definition, likelihood, prior, threshold, randomization procedure, information budget, or seed block may change.
- The gate-5 verdict recorded in `gate-5-report.md` stands as written (honest preflight stop); the repaired rerun is a new execution, not an overwrite.

## Mandatory byte-identity verification before the rerun
1. Re-execute the retained public identity audit (seed 790700 at 32/64/96 slices) and confirm every family weight, log score, BMA score, regret, held-out score, complexity, matched margin, material and selective classification is bitwise identical to the pre-repair values.
2. Re-run the full unit suite (must remain green).
3. Add a regression test that executes all five families at cue_count=2 and cue_count=4 on public development seeds.
4. Record the diff scope in this directory (`gate5-repair-diff-summary.md`): only cue-shape handling may appear.

## Disclosure
This authorization is evaluator-issued under the standing pure-software-error rule; it will be disclosed in the freeze-readiness report and flagged for GPT-5.6 Pro review at the next consultation round before any freeze proceeds.
