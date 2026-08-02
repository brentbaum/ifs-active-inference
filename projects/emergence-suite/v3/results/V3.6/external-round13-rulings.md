# External round-13 rulings (verbatim; relayed by Brent 2026-08-02)

## 1. Population-B adjudication: ratified, with one boundary clarification

Fable's Event-1 adjudication is approved. The first Population-B execution did not instantiate the native-prior population specified in Round 12: the context-split path started deterministically in `then` rather than from the frozen `[0.5, 0.5]` prior; the module's three-valued marker emission was collapsed incorrectly by assigning `none` mass to `then`; the enumerable joint discrepancy was `0.0787`; repairing those two productions in isolation reduced the discrepancy to exactly zero; the context ECE miss was extreme under the parametric calibration null, whereas the four correctly constructed targets remained within their null distributions.

Classify the first attempt as `FAIL_APPARATUS_WRONG_NATIVE_PRIOR_FIXTURE`, not as a V2 calibration failure.

Authorized repair — the only permitted fixture changes: (1) sample the initial context from the frozen module prior; (2) implement the marker bridge using the exact frozen three-category CPT. When the shared target remains binary then/now, both generator and forecast must explicitly condition on the target being in that binary support: p(now | marker in {then, now}, c) = p(now marker | c) / (p(then marker | c) + p(now marker | c)). The `none` marker may not be assigned to either binary category by complementation. If a future target includes `none`, it must remain three-valued. No scorer, scientific module, criterion, ECE ceiling, noninferiority margin, calibration definition, or target population may change.

Seed and verdict treatment: 3690001:3691999 permanently barred, never pooled with the replacement; 3700000:3701999 is the single valid Population-B qualification block; the first block remains visible in the final record; the replacement does not consume an additional scientific requalification cycle because the specified population was never constructed.

Boundary clarification: no open-ended fixture-repair allowance. Once the corrected pre-block proofs pass and 3700000:3701999 opens: a blocking calibration miss on a correctly constructed population is a qualification result; another fixture-semantic defect returns to external adjudication; there is no automatic third Population-B block. The new permanent pre-block fixture-identity proof is ratified.

## 2. Partner proof repair: authorized narrowly

The stop remains HONEST_STOP_PRE_BLOCK_NATIVE_FIXTURE_PROOF_FAILURE with zero seeds consumed. The frozen partner model defines four separate typed Bernoulli channels (regulation, remaining, respect, trust); each matrix entry is that channel's success probability, not one category in a four-category distribution.

Correct enumerable partner joint (two-slice dummy): p(s0, s1, r0, r1) = p(s0) p(s1|s0) Bern(r0; theta_{s0,remaining}) Bern(r1; theta_{s1,remaining}); s over the four partner states, r in {0,1}, theta the frozen remaining-channel success probability; PRIOR and TRANSITION unchanged. Required identity: the joint sums to 1.

Independence: the corrected paths may not share the erroneous positional interpretation. Production path: invoke the fixture's actual partner generation semantics, or relational_likelihood with observation (None, remaining_value, None, None), channel position resolved through the module's declared schema. Oracle path: read the named parameter mapping per state, retrieve `remaining` by NAME, apply a generic Bernoulli enumerator, enumerate directly; do not call relational_likelihood, the fixture helper, or a shared column-index helper. Both may share only the canonical declaration that the target is the observable remaining token.

Mandatory proof preconditions (1e-10): prior sum = 1; every transition row sum = 1; every Bernoulli outcome row sum = 1; production joint sum = 1; oracle joint sum = 1; production/oracle support sets identical; all probabilities finite and nonnegative. Only then evaluate max absolute atom error <= 1e-10. A matching but non-normalized pair is FAIL_INVALID_PROOF.

Scope — authorized: partner proof enumerator; independent partner oracle enumerator; proof-level normalization and support assertions; regression tests and reports. Forbidden: v26a; partner fixture generator; partner adapter; parameters; criteria; seed blocks; target definition. If the corrected proof exposes a nonzero fixture-versus-module discrepancy, stop before any seed and return for adjudication. The failure record remains visible: seven families passed; partner failed because two independent code paths encoded the same semantic misunderstanding.

## 3. Permanent third defense: schema validation AND normalization/support validation

3.1 Every fixture proof needs a committed machine-readable target schema (target name; latent variables with supports; observation name/support/distribution; channel axis names with selection; temporal factorization; missingness semantics). The proof must fail before arithmetic when: array width differs from declared channel count; a named channel cannot be resolved uniquely; a binary channel is treated as categorical; observation support differs between production and oracle; conditioning/missingness semantics differ.

3.2 Positional array access forbidden without an asserted name mapping (CHANNELS.index('remaining') only after asserting EMISSIONS.shape[1] == len(CHANNELS) and CHANNELS[i] == 'remaining'). The independent oracle uses the named parameter source, not the positional index.

3.3 Three-way semantic triangulation, every native-prior fixture proof: (1) schema check; (2) production-vs-oracle joint atoms; (3) module-predictive check — marginalize the enumerable joint to the observable forecast and compare to the public module's direct posterior-predictive query. Agreement between two mistaken enumerators cannot pass if neither reproduces the public forecast.

3.4 Local AND global normalization: each conditional factor normalizes on its declared child support (independent Bernoulli channels tested per channel; categoricals summed on the declared axis), and the complete joint normalizes.

3.5 Exact support equality: production_key_set == oracle_key_set == schema_enumerated_key_set; report support sizes, missing/extra/duplicated atoms, total mass by latent state and by observation value.

3.6 Mutation tests, one per fixture family (partner: changing only the remaining success probability in an in-memory copy changes only the remaining joint; changing regulation/respect/trust changes nothing; permuting columns with names preserved changes nothing; permuting without updating names raises a schema failure). No frozen parameter file altered.

3.7 Permanent rule: a fixture-identity proof is valid only when its declared semantic schema, every local conditional distribution, the complete joint distribution, and the production/oracle support all validate independently; numerical agreement is evaluated last and cannot rescue a semantic or normalization failure. Applies to all five V2 target-native fixtures, the complete V3 native generator, its protect and temporal factors, and future common-support bridges and sealed-challenge constructor proofs.

## 4. Resumption order: confirmed

4.1 Before any seed: commit the partner-proof diagnosis unchanged; commit this adjudication; repair only the partner proof and oracle; add the permanent schema/local-norm/global-norm/support/module-predictive/mutation checks; run all eight pre-block proofs; all eight must pass; persist and hash the proof record before its verdict; verify scientific hashes bitwise unchanged. Another pre-block proof failure returns for external adjudication.

4.2 Seeded order: (1) replacement Population B 3700000:3701999; (2) Population A 3692001:3693999; (3) Population C qualification 3694001:3695999; (4) single repaired tournament 3684000:3689999.

4.3 Transitions: B->A requires all five V2 target-native blocks pass (ECE <= 0.05; forecast normalization <= 1e-10; adapter/direct enumeration <= 1e-10; finite Brier/log) — a correctly constructed blocking failure stops the program. A->C requires the complete V3 native-prior criteria. C->tournament requires external generator qualification, exact bridge identities, support equality, V2 precision width <= log(1.02) per target, all calibration state serialized, no scientific-source change. Tournament: once, 6,000 worlds, lower95[S_V3 - S_V2] >= -log(1.02) separately per target.

4.4 Gate 4 parallel after the corrected proof package commits and all eight zero-seed proofs pass; Gate 4 must not import native-prior fixture code, bridge adapters, the external generator, calibration definitions, or tournament statistics. Gate 5 waits for B, A, C, and the tournament.

4.5 C-V36A/B/C sealed and untouched; reveal after tournament, Gate 4, Gate 5, compatibility attestations, V3.6 freeze.

## Operative authorization

{"round": 13, "population_b_first_attempt": {"verdict_retained": "FAIL_APPARATUS_WRONG_NATIVE_PRIOR_FIXTURE", "block_barred": [3690001, 3691999], "scientific_calibration_result": false}, "population_b_adjudication_ratified": true, "replacement_population_b": [3700000, 3701999], "partner_proof_repair_authorized": true, "scientific_module_changes_authorized": false, "fixture_changes_authorized": false, "proof_changes_authorized": ["typed remaining-channel Bernoulli enumeration", "local normalization checks", "joint normalization checks", "support equality", "module-predictive identity", "schema validation", "semantic mutation tests"], "all_eight_preblock_proofs_required": true, "another_preblock_failure": "RETURN_TO_EXTERNAL_ADJUDICATION", "population_order": ["B", "A", "C", "TOURNAMENT"], "gate4_parallel_after_proofs": true, "gate5_waits_for_tournament": true, "tournament_block_unchanged": [3684000, 3689999]}
