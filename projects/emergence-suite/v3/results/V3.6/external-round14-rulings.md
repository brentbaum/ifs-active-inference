Binding rulings

1. Empty-support lesion semantics: choose (b)

A restricted-prior identity is not vacuously satisfied when the conditioning support is empty. Conditioning on a zero-mass event is undefined:

p(H\mid O,\;H\in S)
=
\frac{p(O\mid H)p(H)\mathbf 1[H\in S]}
{\sum_{H'\in S}p(O\mid H')p(H')}

requires a nonempty licensed set and positive denominator. Defining the error as zero would turn an undefined comparison into a pass and could conceal a malformed lesion.

The grow_mode_slot cell should therefore inherit the V3.1 support-removal semantics:

Support-preserving lesions are tested by restricted-prior identity. Support-destroying lesions are tested by masking/neutralization identity and selective disappearance of the targeted mechanism.

The current stop is apparatus-only. The finite-row guard correctly rejected the nonfinite result before a scientific row or criterion was recorded. The two reported nonfinite fields are aliases of one computation, not two findings.

1.1 Two formally distinct lesion classes

Every Gate-4 lesion must be declared before execution as exactly one of:

SUPPORT_PRESERVING_CONDITIONING
SUPPORT_DESTROYING_MASKING

Support-preserving conditioning

Use restricted-prior identity only when:

licensed candidate count > 0
restricted prior mass > 0
restricted model evidence > 0

Then require:

\max_H
\left|
q_{\mathrm{lesion}}(H)
-
\frac{q_{\mathrm{full}}(H)\mathbf 1[H\in S]}
{\sum_{H'\in S}q_{\mathrm{full}}(H')}
\right|
\le10^{-10}.

Exact-zero posterior entries remain members of the licensed support. “Support” is determined by the frozen grammar restriction, not by whether the realized posterior probability is numerically positive.

Support-destroying masking

When the lesion removes the production needed to define the original candidate family or target variable:

* no restricted-prior posterior is computed;
* restricted_prior_identity_applicable = false;
* the numeric restricted-prior error is serialized as null, never 0, inf, or nan;
* observations belonging only to the removed production are masked and contribute likelihood one;
* the remaining model posterior must be finite and normalized;
* the targeted pathway or readout must disappear under the already-frozen lesion criterion;
* unrelated survivor posteriors must match the candidate-common masked reference within 1e-10.

For grow_mode_slot, use:

semantic_class = SUPPORT_DESTROYING_MASKING

The mode-slot observation channels are masked, the mode-specific structural production is unavailable, and downstream effects are evaluated on the surviving model. Do not condition on an identity-bearing support that the lesion has itself removed.

1.2 Empty support is still diagnostically reported

Each lesion trace must contain:

{
  "semantic_class": "SUPPORT_DESTROYING_MASKING",
  "licensed_support_count": 0,
  "restricted_prior_mass": 0.0,
  "restricted_evidence": null,
  "restricted_prior_identity_applicable": false,
  "restricted_prior_identity_error": null,
  "masked_channel_neutrality_error": 0.0,
  "posterior_normalization_error": 0.0,
  "all_outputs_finite": true
}

If a lesion declared support-preserving unexpectedly produces:

licensed support count = 0
or restricted prior mass = 0
or restricted evidence = 0

that is:

FAIL_APPARATUS_LESION_SEMANTICS_MISMATCH

It may not be dynamically reclassified inside the seeded run.

1.3 Do not alias statistics

masked_channel_neutrality_error may no longer be assigned from restricted_prior_identity_error. They represent different claims and must be computed independently.

The earlier calibration/tuning rules already require apparatus defects to be stated without reference to the desired scientific conclusion, forbid moving criteria, and require bounded published repairs.   This repair satisfies that boundary.

?

2. Seed authorization: approved

Authorize:

Gate-4 second replacement:
3709000:3713999
Population-A third block:
3714000:3715999

Permanently bar and publish:

Gate 4 original:
3630000:3634999
Gate 4 first replacement:
3702000:3706999
Population A original:
3692001:3693999
Population A first replacement:
3707000:3708999

The retained Population-A replacement artifact contains 1,534 serialized rows, but multiprocessing prefetch makes the exact attempted set unknowable; the complete block therefore remains barred and contributes no qualification statistic.

The new blocks must be committed to the seed map before any execution. They may not be pooled with either predecessor.

Suggested ledger entries:

{
  "barred_gate4_original": [3630000, 3634999],
  "barred_gate4_replacement_1": [3702000, 3706999],
  "gate4_replacement_2": [3709000, 3713999],
  "barred_population_a_original": [3692001, 3693999],
  "barred_population_a_replacement_1": [3707000, 3708999],
  "population_a_replacement_2": [3714000, 3715999]
}

The finite-before-serialization guard remains permanent. Its first real use worked correctly: it persisted rejection provenance and an incremental matching hash rather than leaving a zero-byte trace.

?

3. Sequencing and collateral burn: choose (a), de-parallelize

Run no further independent criterion-bearing batteries concurrently.

The remaining order is:

Population A
? Population C
? common-target tournament
? Gate 4
? Gate 5
? compatibility attestations
? C-V36A/B/C

Reasons:

1. The tournament is the critical path for the compression claim.
2. Gate 4 has twice stopped on its first effective row.
3. Parallelism has now burned 4,000 Population-A seeds without producing a Population-A qualification result.
4. The remaining time benefit is small relative to the custody and interpretability cost.
5. Gate 4’s result is independent of the tournament and can safely run afterward even when the valid tournament produces a scientific noninferiority failure.

Revised custody rule for the remaining chain

Only one seeded criterion battery may be open at a time.

When that battery stops:

* its own block is handled under the standing custody rules;
* all later blocks remain unopened;
* already completed prior batteries remain valid;
* no independent in-progress battery exists to become collateral.

This supersedes the prior authorization for Gate-4 parallelism. The earlier authorization and both collateral stops remain visible in the record. The prior sequence had explicitly allowed Gate 4 to run in parallel after Population A opened; that authorization is now retired because its practical cost has been observed twice.

I would also use single-process sequential dispatch for the first seeded cell of each remaining battery. After that cell serializes successfully, ordinary parallel dispatch may resume. This does not eliminate later prefix ambiguity, but it prevents another first-row construct defect from contaminating a prefetched block immediately.

?

4. Mandatory zero-seed lesion pre-run proof: approved and expanded

Before 3709000 may open, every Gate-4 lesion cell must pass a no-RNG enumerable proof under its declared semantic class.

4.1 Required proof table

Persist this table for every lesion:

Field	Requirement
lesion	exact frozen lesion name
semantic_class	support-preserving or support-destroying
licensed_support_count	exact integer
restricted_prior_mass	exact finite value
restricted_evidence	finite value or null when inapplicable
restricted_identity_applicable	exact Boolean
restricted_identity_error	≤1e-10 or null
masked_neutrality_error	≤1e-10 where applicable
independent_oracle_error	≤1e-10
target_pathway_removed	true
unrelated_survivors_preserved	true
posterior_normalization_error	≤1e-10
all_outputs_finite	true

4.2 Proofs for support-preserving lesions

Require:

1. nonempty licensed support;
2. positive prior mass;
3. positive evidence;
4. exact conditioned-full-posterior identity;
5. independent restricted oracle identity;
6. target production removed;
7. unrelated survivor readouts preserved;
8. all statistics finite.

4.3 Proofs for support-destroying lesions

Require:

1. restricted-prior identity explicitly marked inapplicable;
2. target-only channels contribute likelihood one after masking;
3. masked reference and lesioned model agree on shared survivors;
4. target pathway is absent;
5. posterior remains normalized and finite;
6. no clinical or protocol label enters inference;
7. no fallback branch assigns a desired scientific readout.

4.4 Boundary fixtures

The zero-seed battery must include at least:

one exact-zero retained candidate
one empty licensed target subset
all target channels masked
one target channel observed before masking
one unaffected channel observed
one full-support conditioning lesion

This directly exercises the case that defeated the seeded runner.

4.5 Serialization and stop rule

The proof record must be persisted and hashed before its verdict is emitted. It uses no development seed.

Any nonfinite or inapplicable-but-numeric statistic is:

FAIL_PREBLOCK_LESION_PROOF

and returns for external adjudication. No Gate-4 seed opens.

This pre-run proof pattern should become permanent for future lesion batteries. Exact posterior/restricted-prior algebra on one ordinary dummy is insufficient when a lesion can change the very domain on which the identity is defined.

?

5. Remaining chain: confirmed with the revised serial order

After the zero-seed lesion proof and seed-map addendum are committed:

1. Population A
   3714000:3715999
2. Population C
   3694001:3695999
3. Common-target tournament
   3684000:3689999
4. Gate 4
   3709000:3713999
5. Gate 5
   existing untouched block
6. C-V36A/B/C compatibility attestations
7. Reveal and run C-V36A, then B, then C
   immutable verdict first for each
8. V3.6 freeze
9. Final complete V3 profile
10. T-V3-DO1
11. Paper and HTML propagation

Population B’s PASS remains standing. Population C, the tournament, Gate 5, and all three escrows remain untouched according to the current stop record.

A valid scientific failure in the common-target tournament remains non-blocking for Gates 4–5 and the sealed challenges; it changes only whether V3 earns the “no material predictive loss” sentence.

Operative authorization

{
  "round": 14,
  "gate4_current_stop": {
    "verdict_retained": "HONEST_STOP_NONFINITE_WORKER_ROW",
    "scientific_criterion_evaluated": false,
    "classification": "APPARATUS_LESION_SEMANTICS_UNDEFINED_AT_EMPTY_SUPPORT"
  },
  "empty_support_ruling": {
    "vacuous_identity_permitted": false,
    "support_preserving_lesions": "RESTRICTED_PRIOR_IDENTITY",
    "support_destroying_lesions": "MASKING_NEUTRALITY_AND_TARGET_REMOVAL",
    "inapplicable_numeric_value": null
  },
  "new_blocks": {
    "population_a": [3714000, 3715999],
    "gate4": [3709000, 3713999]
  },
  "deparallelized": true,
  "one_seeded_battery_open_at_a_time": true,
  "gate4_zero_seed_per_cell_proof_required": true,
  "population_order": [
    "A",
    "C",
    "TOURNAMENT",
    "GATE4",
    "GATE5",
    "CHALLENGES"
  ],
  "population_b_pass_stands": true,
  "tournament_block_unchanged": [3684000, 3689999],
  "escrows_unchanged": true
}