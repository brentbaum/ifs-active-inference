# V2.4.2 decisions

## Provenance

- **Invalidate-and-repeat repair:** the shuffled constructor independently
  randomizes exact per-cue outcome and marker multisets; the fixed/
  single-regime constructor independently randomizes outcomes and supplies
  one fixed marker regime. The prior V2.4.1 transformations are not reused.
- **Invalidate-and-repeat repair:** the formed-bank bridge uses the
  V2.3.3 corrective stream oriented against each frozen bank expectation,
  separate normalized then/now root factors, the exact CS context
  posterior, a signed corrective-direction transfer readout, and an exact
  G-fixed mediation control.
- **Pilot amendment:** the Assay-7 conditional-product null now declares
  preserved marginals and destroyed temporal sufficient statistics
  explicitly; original clauses remain struck in the analysis plan.
- **Pilot amendment:** excluded seeds `781000:781499` derived the Assay-3
  tolerance by the frozen familywise 75th-percentile, maximum, and
  next-0.01-grid rule. The result was `0.13`. Calibration worlds never
  entered a criterion.

## Repair diff

- `_shuffle_marker_association`: marker-only shuffling was replaced by
  independent per-cue outcome and marker permutations.
- `_fixed_context_control`: marker replacement over a recurrent CS outcome
  path was replaced by exchangeable per-cue outcomes plus one marker
  regime.
- `_composition_world`: independently sampled global root truth was
  replaced by bank-relative V2.3.3 corrective evidence; a single global G
  was replaced by context-indexed then/now factors; association reliability
  now comes from the bank's inferred `cue_root_associations`.
- Gate-3 reporting now scores the previously omitted composition/bridge
  held-out margins, matched counts, per-stratum bridge outcomes, historical
  retention, and G-fixed mediation identity.
- Gate 1 gained exact repaired-null and context-indexed-bridge audits.

## Ratchet decision

- Gates 1 and 2 passed. Gate 3 failed Assays 3, 7, and 8.
- The bridge's genuine scientific pathway passed after repair; its two
  control rates failed.
- The amended matcher achieved its power target, exposing adverse/neutral
  held-out results for GW, CL, and DR rather than a yield artifact.
- No model, constructor, parameter, tolerance, threshold, or direction was
  changed after the criterion result. Gates 4–5 were not run.
- C-V24 remained sealed and no escrow seed was accessed.
