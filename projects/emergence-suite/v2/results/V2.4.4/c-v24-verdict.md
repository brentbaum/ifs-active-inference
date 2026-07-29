# C-V24 sealed verdict

**PROSPECTION FAILURE — UNRUN.**

The challenge stopped during frozen-public-API validation, before any escrow seed was accessed. No scientific criterion was evaluated and this outcome is not a numerical PASS or FAIL. The sealed plaintext explicitly classifies an expressibility failure as a prospection failure and requires a sealed stop rather than an improvised extension.

## Expressibility localization

All requested inference-side quantities already exist as pure frozen readouts: five-family posterior selection, tie-conservative false-CS scoring, pre-held-out family weights, held-out scores, matched-complexity margins, path-class occupancy, within-CS split BF, material redescription, CRT statistics, complexity decomposition, constitution identities, and the formed-state bridge estimands.

The world configurations do not all exist in the frozen API:

1. **D:** `generate_world("continuous_drift", ...)` evolves one shared drift state and applies it to every cue. It cannot declare drift on only a subset of cue emissions.
2. **K:** `generate_world("change_point", ...)` samples a hazard. It permits no onset or an onset anywhere in the sequence; it cannot declare exactly one seed-drawn onset restricted to the middle 60%.
3. **S:** `generate_world("context_split", ...)` samples an unconstrained Markov path. It cannot guarantee a switch followed by recurrence of the old context without conditioning/rejection.
4. **X:** no frozen generator composes partial DR on non-identity cues with a recurrent CS process on identity-linked structure.
5. **D-cell bridge:** `_composition_world(seed, bank_state=...)` hard-codes `generate_world("context_split", ...)`. It cannot run the required formed-state D negative control.

Implementing any of these missing constructors, conditioning on generated paths, rejecting seeds, or merging candidate-generated token streams would be new challenge-specific code. The challenge instruction forbids that action. Substituting the nearest existing generator would change the sealed world population and would not be an exact run.

## Five sealed criteria

| Criterion | Standing |
|---|---|
| 1. Diagonal selection and false-CS controls | NOT EVALUATED |
| 2. S/X held-out matched margin | NOT EVALUATED |
| 3. S bridge and D bridge negative control | NOT EVALUATED |
| 4. Constitution spot-audit | NOT EVALUATED ON CHALLENGE TRAJECTORIES |
| 5. Custody | PASS THROUGH THE SEALED STOP |

There are no per-world files or CRT NPZs because zero worlds were generated. Consequently, there is no raw-trace seal commit; sealing an empty or substituted population would misstate custody.

## Verdict classes

- **Scientific:** `NOT_EVALUATED_PROSPECTION_FAILURE`.
- **Semantic:** `PROSPECTION_FAILURE_FROZEN_PROTOCOL_CONSTRUCTORS_INSUFFICIENT`.
- **Distributional stress:** `NOT_EVALUATED`.
- **Process custody:** `PASS_SEALED_STOP`; challenge SHA-256 `574131ce32bf45a72e3163c91df0e924c84478b39c3c07691dfc216dc1b34665`; primary manifest plus addendum `87/87` hashes verified; seeds consumed `0`.

The released block authorization is recorded but unused. Seeds `830001:830600` remain unconsumed by this execution.

`B_max_inherited_formation = 3.801426508560692`; `B_max_v24_common_emissions = 6.704414354964107`; `pi1 = 0.92741935483871`.
