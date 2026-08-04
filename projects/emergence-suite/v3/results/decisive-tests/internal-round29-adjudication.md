# T-CAP1 Round-29 adjudication (INTERNAL)

**Authority.** Evaluator (Fable) as advisor per Brent's standing
instruction; INTERNAL labeling, open to retroactive external review. All
classifications below are runner/readout-side with direct localization —
the ratified round-24 precedent class. Stage 0 stands; frozen v3.6 and the
T-CAP1 scientific productions are untouched.

## Ruling 29.1 — the census is invalid as a panel, retained as evidence

Block `3824000:3831999` is consumed; its traces (sha `c1cecb32…`) are
retained as descriptive evidence only. Three defects, the first two
disclosed by the implementer, the third found on evaluator review:

1. **Arm-specific world keys.** Control arms drew bundle-stay randomness
   under `bundle-stay:{arm}` keys, so latent bundle paths differ across
   arms — the controls are not counterfactual allocations on one common
   world (the transparency pair alone was proven byte-identical).
2. **Missing fixed-point readout.** The required low/high initial-posterior
   replays were never executed; `fixed_point_count` is a trajectory-end
   heuristic, not the ruled bistability estimand.
3. **Raw-H region classification.** Regions were classified on raw
   transparent hysteresis area. Ruling 5 defines the feedback account as
   passing only where hysteresis EXCEEDS the matched-persistence
   comparator; raw H conflates feedback with state stickiness. The decisive
   evidence is the panel's own cell 0: coupling strength 0.0 — no
   bundle-to-precision feedback exists — yet raw H = 0.325. The uniform
   "all 324 cells clear-hysteresis" classification is therefore a readout
   artifact, not a discovered world property, and the
   PUBLIC_CENSUS_DYNAMIC_RANGE_NOT_SPANNED finding is reclassified as
   apparatus-derived (retained verbatim alongside this reclassification).

## Ruling 29.2 — repairs (runner/readout only)

1. **Arm-common worlds:** all arms of a cell draw world and bundle-path
   randomness under arm-invariant keys; only the allocation process may
   differ by arm.
2. **Explicit bistability estimand:** per world, paired replays from low
   and high initial bundle posteriors; two stable fixed points are counted
   from the pair, not inferred from trajectory ends.
3. **Excess-hysteresis classification:** census regions are defined on
   H_excess = H_transparent − H_matched-persistence, computed per cell on
   paired common worlds. Raw H is still reported descriptively.

## Ruling 29.3 — permanent arm-common world proof

New standing rule, joining the battery beside the candidate-common
schedule-equality proof: before any multi-arm block opens, a zero-seed
proof must show every arm reproduces byte-identical latent world paths on
the enumerable dummy, with only the declared arm-varying process differing.
This is the arm-level instance of the round-22 lesson: proofs transfer,
repairs do not.

## Ruling 29.4 — fresh census

Census-2 on `3840000:3847999`, same frozen 324-cell grid (the grid itself
is not tuned; ruling 13's no-post-hoc-tuning discipline holds), repaired
runner and readouts, full custody. If the EXCESS-hysteresis panel still
fails to span (e.g., no cell with genuine feedback bistability), that is a
real dynamics finding about this organism family and goes to external
review before any prediction seal — it would mean the construct's
bistability claim fails in this family, which is exactly what the census
exists to discover before predictions are committed.
