# Sealed challenge C-V24 — redescription under mixed drift and abrupt transition

**Sealed by evaluator after the V2.4 phase-1 public artifacts, before any implementation. Runs on the frozen V2.4 stage with zero new engine code. The public family (spec §4/V2.4): a mixed schedule containing partial drift plus an abrupt contextual transition. Everything below is the private instantiation.**

**Pre-seal linter record:** every referenced quantity is a frozen public-plan field (the five family names; the ≥ .01 nats-per-held-out-token margin with lower 95% bound > 0 at matched complexity ≤ .05 nats/observation; the tie-conservative false-split scoring; the frozen train/validation/held-out partition and pre-held-out-posterior scoring rule; the bridging-assay estimands; Wilson intervals; verdict classes); reference population = evaluation population for every rate (all cells scored within this challenge's own worlds); no external baseline quantity; criteria classified; failure interpretations pre-committed; expressibility failure = prospection failure, stop as sealed.

## Configuration
160 worlds from escrow block 830001:830600 (first 160), 40 per cell, generator truth per cell:
- **Cell D (drift-only):** continuous slow drift on a subset of cue emissions; no context recurrence, no abrupt structural change.
- **Cell K (change-point-only):** one abrupt transition in emission structure at a seed-drawn slice in the middle 60%; no recurrence of the old regime, no drift.
- **Cell S (genuine split):** two recurring contexts (then/now) with a learnable transition process; the old context RECURS after the switch — the structure a split family exists to capture — plus mild observation noise, no drift.
- **Cell X (mixed):** partial drift on non-identity cues AND one abrupt contextual transition on identity-linked structure, with old-context recurrence — the schedule the public family names. Ground truth for family scoring in X is split-plus-nuisance-drift; the frozen misspecification machinery (assay 5) provides the scoring convention.

## Criteria
1. *(scientific — recovery)* Diagonal family selection: D-cell selects drift and K-cell selects change-point, each ≥ 30/40; S-cell selects context-split ≥ 30/40; false context-split (tie-conservative) ≤ 4/40 in D and ≤ 4/40 in K.
2. *(scientific — prediction)* In S and X cells, the selected family beats its best matched-complexity comparator on the held-out suffix by ≥ .01 nats per observed token, lower 95% bound > 0, under the frozen pre-held-out-posterior scoring rule.
3. *(scientific — composition, the seam)* In S-cell worlds run through the frozen bridging assay (banked formed state + witnessing-style corrective evidence with genuine then/now structure): the split family is favored over global down-weight; root revision proceeds; transfer follows the shared root within the inferred PRESENT context (frozen estimand); old-context predictions remain retrievable under the old-context index without remaining globally current (frozen estimand). In D-cell bridging runs, the split family must NOT be favored (down-weight or drift wins) — re-indexing must lose where there is no then/now structure.
4. *(semantic)* Constitution spot-audit on challenge trajectories (independent summation; masked/no-event neutrality; prequential recombination across the frozen partition).
5. *(custody)* Frozen identity hashes; seeds within block; gap-free ledger; verdict-class reporting.

Pass = all five. Failure interpretations, pre-committed: a criterion-1 D/K false-split failure revives the free-parameter concern (redescription winning where it should lose) and blocks V2.5; a criterion-3 bridging failure localizes (favoring / revision / transfer-indexing / retrievability) and is the result; criterion-2 misses at intact criterion 1 are effect-size findings, reported with intervals.
