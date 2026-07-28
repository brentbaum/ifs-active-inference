# V2.4.2 gate-3 adjudication (GPT-5.6 Pro round 3, 2026-07-28)

Consultation round 3 (branch pushed through d0f5212; diagnosis: `gate3-diagnosis.md` and its two CSVs). Decision metric set by the PI: whatever most strengthens the paper.

## Standing of prior verdicts
- The V2.4, V2.4.1, and V2.4.2 honest stops **remain failed as recorded**. The amendments below define a new V2.4.3 claim; they are not repairs converting any prior gate to a pass.
- The formed-state-prior coupling hypothesis is **rejected**: banked posteriors never enter the redescription-family prior; banked vs neutral rescoring of identical streams agree exactly. No claim that formation prior-biases the redescription family may be made.
- All 786000:786359 diagnostic probe seeds remain barred from criterion evaluation.
- No family likelihood, transition, parameter prior, candidate prior, common emission, bridge equation, or root-transfer mechanism changes in V2.4.3.

## Decision A — material context-indexed redescription (adopted)
A context-split (CS) family win is not, by itself, redescription. The CS candidate nests the stationary one-context subcase; single-regime CS wins are predictive wins by that subcase, and shuffled-arm wins ride relative path-complexity geometry. These are genuine family overlap, not tie-breaking artifacts — but "CS was the largest family posterior" is not "the data support a two-context redescription."

Adopted construct (frozen text in `contracts/v2.4.3-structural-existence-addendum.md`): partition the exact CS latent-path support into Z_2C=0 (path occupies only one context) vs Z_2C=1 (path occupies both). A world exhibits **material context-indexed redescription** iff (1) CS is the unique argmax of the pre-held-out five-family posterior, (2) posterior two-context path-class mass q1 ≥ 0.80, and (3) prior-normalized within-CS Bayes factor BF_2C:1C ≥ 4.0. All quantities computed on the frozen pre-held-out prefix. Ties, zero/non-finite masses, or missing paths count as failures. Raw CS argmax is published separately and is not a redescription verdict.

This is the third application of the suite's structural-existence principle (cue association, identity formation, now context splitting): "does this structure exist?" is represented discretely, not inferred from a flexible continuous parameter.

## Decision B — controls retained, endpoint changed (adopted)
The conditional-product shuffled null and the repaired single-regime generator remain unchanged; their raw family label was the wrong endpoint, not the generator. Primary false-redescription estimand in each control population: material-redescription rate ≤ 0.10, separately. Raw CS selection rate becomes a mandatory descriptive family-overlap diagnostic with no pass/fail ceiling. A raw CS win without material two-context support is reported as *nested-family selection without redescription*. No differential-only replacement control; the absolute 0.10 ceiling preserves the selectivity claim. The V2.4.2 diagnostic worlds cannot establish the V2.4.3 result — fresh criterion seeds must.

Exceptions retained at full strength: exact DR and CP generating worlds keep the legacy raw CS ceiling ≤ 0.10 (they are model-recovery controls, not the ambiguous nested construct) **plus** the new material-redescription ceiling ≤ 0.10.

Cue-local control: the 0.55 recovery is fixed by information budget, not threshold — dedicated CL control moves to 96 slices (120 fresh worlds; CL recovery ≥ 0.60; material redescription ≤ 0.10). World-information amendment, not a threshold amendment.

## Decision C — Bayesian model-average regret for nuisance families (option ii adopted)
Per-family attainable-range SESOIs (option i) rejected: bespoke thresholds reflecting the model's own behavior, and overlapping families need not beat every close comparator on a finite sample. Adopted claim: when finite evidence does not identify a unique nuisance family, the calibrated posterior model average should predict approximately as well as the true generating family. Frozen criterion: generator-family regret R_f (generating family's held-out log score minus BMA held-out score, per observed held-out token, exact log-sum-exp over pre-held-out family weights) must have whole-world bootstrap 95% upper bound ≤ 0.01 nats/token in each family's 80 worlds. The 0.01 bound is the already-public smallest meaningful scale — not recalibrated from V2.4.2 or barred probes.

The matched-complexity point-family advantage (≥ 0.01 nats/token, lower CI > 0, ≥ 60/80 matched) is retained **only for CS**, the load-bearing family. GW/CL/DR/CP point margins remain fully reported but are not gate criteria — because the paper's V2.4 claim is context-indexed redescription; the other four families are live alternatives and calibration checks, not four additional psychological claims.

## Revised V2.4 scientific claim (adopted)
> Context-indexed redescription is posterior support for a materially occupied two-context representation — not merely selection of a model family capable of representing two contexts. In genuine then/now worlds, that representation preserves the historical prediction while allowing present-context identity-root revision to transfer to untreated cues. Overlapping alternatives are handled through calibrated model averaging rather than forced point identification.

The formed-P bridge is reframed as a composition test: the redescription mechanism operates cleanly from a previously formed P organization.

## Stop rule
No automatic V2.4.4. A successor requires a new representational absence (CS path cannot represent the sealed mixed schedule; material split indistinguishable from a change point with CP live; a mixture-level latent genuinely required). A numeric miss does not justify adjusting 0.80, 4.0, 0.60, 0.10, or 0.01.

## B_max bookkeeping (reconciled)
Two finite-information bounds coexist on the branch and both are correct for their stages; neither changes. Reports must name them explicitly:
- `B_max_inherited_formation = 3.801426508560692` (V2.3.2 formation support)
- `B_max_v24_common_emissions = 6.704414354964107` (V2.4's larger outcome/marker/root support; used by the V2.4 contract and gate-1 record)

## Post-V2.4 ladder amendment (adopted)
V2.4.3 → **V2.5a** (joint-vs-marginal evidence format) → **V2.5b** (full-vs-reduced structural comparison and do-over) → V2.3.4 (counterfactual action attribution; required before V2.6b, not before V2.6a) → **V2.6a** (latent partner process, co-regulation, relational precision) → **V2.6b** (one protector: trust, joint policy, access, counterfactual future) → V2.7 (multi-protector, exiling, registration, polarization) → V2.8 (whole-therapy trajectory). Rationale: evidence format and Bayesian model reduction are different primitives; co-regulation should be established before protector policy — one compositional seam at a time.

## C-V24 disposition
The sealed challenge (hash 574131ce…, escrow 830001:830600) remains unopened. Evaluator's private compatibility audit: `c-v24-compatibility-attestation.json`. If the sealed criteria use raw-selection endpoints, they are evaluated exactly as sealed; the immutable challenge verdict is reported first, and material-redescription results are reported separately without rewriting the seal.
