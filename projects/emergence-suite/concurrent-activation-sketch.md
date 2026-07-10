# Design sketch: concurrent part activation (the v12 architecture question)

*Orchestrator note for collaboration, 2026-07-10. Status: DECIDED by Brent
(2026-07-10): mechanism 2 on substrate 1 — parts observe parts, on soft
responsibility. Built as Sim 8 (exploratory register; Sim 1's frozen record
untouched). Original sketch below for the record. Context: Sim 4's descent claim closed as
unearned after three preregistered cycles (see
reviews/2026-07-10-t41c-sim4-identifying-experiment.md); the identified gap is
that the current architecture allows only ONE active part per trial, so a
protector can never learn "on top of" a live exile — the theory's own
mechanism for sequencing.*

## The three candidate mechanisms

### 1. Soft activation (mixture responsibility)

Replace winner-take-all cause selection with the full posterior split: every
cause receives writes and contributes to policy in proportion to its
responsibility. A spawned protector at 0.7 coexists with the exile at 0.25;
the exile keeps writing underneath; the protector's formative mass accumulates
during the exile's activity by construction, because spawning happens exactly
when the old explanation is failing-but-still-partially-live.

- For: winner-take-all was always the approximation; this is the more
  principled inference. No new machinery.
- Against: parts may smear (individuality loss); spawn/BMR thresholds all
  retune; the coupling is temporal-incidental rather than content-based.

### 2. Parts that observe parts (recommended)

Widen a spawned cause's observation space to include the ACTIVATION LEVELS of
existing causes, not just world events. A protector then literally learns
"exile activation -> catastrophe" in its own banks, and its policies act to
reduce predicted exile activation — avoidance turned inward.

- Direction emerges for a grown reason: at spawn time, the most predictive
  feature of the unassimilable distress IS the older cause's activation, so
  coupling points later-onto-earlier without any ordering rule.
- Protectors-first at therapy falls out: contacting the exile is, in the
  protector's learned model, approaching catastrophe, so its ordinary
  avoidance policies gate access. This is the blocking T4.1b measured for and
  could not find — because nothing in the current architecture ever writes it.
- Unification: this is the same move Sim 6 makes one level up (the system
  observing its own precision). Parts observing parts and reflexive
  self-observation become one mechanism at two scales.
- Likely substrate: mechanism 1's soft responsibility, so that "exile
  activation" is a live quantity while the protector acts.

### 3. Activation as a decaying trace (control, not mechanism)

Parts stay "warm" for several trials after triggering; protectors form during
the warm window. Cheap, but adds a decay dial and makes the coupling an
accident of timing. Useful as a comparison arm to show mechanism 2's coupling
is content-based, not merely temporal.

## The attention-appraisal extension (from the witnessing discussion)

Separately buildable: let the part appraise witnessing attention itself
through the same threat machinery it uses for everything else. Prediction:
attention that is contingent on the part changing (an agenda) re-enacts the
original conditions and closes access; unconditional attention opens it. If
this emerges, IFS's "loving the part is a precondition" becomes a DERIVED
claim — the relational stance is unique not because its evidence is a special
substance (falsified: Sim 2 confirmatory C3) but because it is the only
attention that does not destroy the access it needs. This would replace the
lost C3 with something stronger.

## Preregistration obligations (per the sol re-review)

Whatever is built: label exploratory until reproduced on fresh seeds;
shuffle-history and permutation controls from the start; the ordering claim
must be earnable in BOTH directions; no id comparisons anywhere; magic
numbers with provenance before the first pilot.
