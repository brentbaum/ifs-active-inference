# Experiment 50-P Stage C apparatus errata

## C-001 — E3 descent ordering

**Apparatus first:** the frozen assay 10 analysis plan defines descent by the root crossing and treats permission-before-root ordering as an audit only. The first E3 runner draft incorrectly required strict permission-episode precedence inside the contact-plus-descent endpoint as well as in the audit.

**Repair:** `scripts/model_organism/run_stage_c.jl` now counts contact plus descent when the conjunctive gate admits contact and the root crosses at the fixed horizon. Strict event ordering remains only in `both_permissions_before_root`. The E3 interpretation record was corrected to quote the frozen distinction. No organism, genome, frozen configuration, frozen analysis, threshold, generator parameter, or seed changed.

**Outcome effect:** the released E3 block was rerun after the correction. Two befriend-both worlds correctly changed from non-descent under the erroneous strict-order endpoint to descent under the frozen endpoint. In seed `710129`, the root was already above the endpoint at episode 1 and the conjunction arrived at episode 24; in seed `710137`, conjunction and root crossing tied at episode 18. Both fail the separate strict-order audit, as required. The befriend-both rate is therefore `2/60` (`0.0333`, 95% Wilson interval `[0.0092, 0.1136]`), while befriend-one and befriend-none remain `0/60`. The E3 compositional verdict remains a scientific **FAIL** against the `0.70` befriend-both threshold.

## C-002 — E4/E5 runner-authored measurements

**Apparatus first:** E4 requires a matched delivered-log-likelihood audit, but the frozen configural/root path and assay-local cue step expose no common likelihood-accounted ordinary-evidence operation. E5 requires the same local forecast to be withheld from or broadcast into q(Φ) and then measured by the frozen depth classifier, but the canonical state exposes neither a part-local forecast coordinate nor an endogenous broadcast/depth readout. The first runner draft substituted bookkeeping likelihood counters for E4 and arm-authored depth values plus an unrelated global error update for E5.

**Disposition:** those substitutions are not valid measurements of the frozen organism. The initial E4 and E5 traces are retained as `invalid-apparatus-per_seed.csv` and explicitly excluded from evidence. Their scientific criteria are not evaluated. Both protocols are recorded as **PROSPECTION FAILURE** under Stage C rule 2; E5 receives its protocol-defined computational-face scope-limit finding. No organism repair was made.
