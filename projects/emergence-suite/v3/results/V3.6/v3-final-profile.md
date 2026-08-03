# Final V3 profile

This is the complete recorded profile. It does not compute an aggregate pass count. Every scientific failure, apparatus stop, replacement result, and adjudication remains visible. Round-17 ruling 17.3 is applied literally: no weighted tournament score, no alternative margin, and no failing family is called a near-miss.

## Stage dispositions

| Stage | Disposition | Gate record |
|---|---|---|
| V3.0 | `PASS` | Gates 1-5 PASS after authorized Gate-5 parity-helper repair; original Gate-5 FAIL retained. |
| V3.1 | `PASS_WITH_ADJUDICATED_REVISABILITY_LIMITATION` | Gate 3 revisability-floor FAIL retained; Gate 4 passed after lesion-semantics and restricted-prior adjudications; Gate 5 PASS. |
| V3.2 | `PASS_WITH_CUSTODY_NOTE_PREFLIGHT_UNSERIALIZED` | Stage-0 design defect and untraced preflight retained; Gates 1-5 PASS after repair. |
| V3.3 | `PASS_WITH_ADJUDICATED_DO_OVER_NULL_AND_SUGGESTION_DIRECTION` | Stage-0 fixed-slice stop retained; Gate-3 do-over-speedup and suggestion-direction FAIL families retained; Gates 4-5 PASS. |
| V3.4 | `PASS_WITH_ADJUDICATED_SHORT_HISTORY_CONJUNCTION_BOUND` | Stage-0 generator/scorer defect retained; original Gate-5 32-slice transplanted-floor FAIL retained; primary 48-slice gate PASS. |
| V3.5 | `CLOSED_PASS_AFTER_AMENDMENT_2` | Earlier Stage-0 and amendment-1 Gate-3 failures retained; amendment-2 Gates 1-5 PASS. |
| V3.6 | `FROZEN_ROUND19_WITH_RETAINED_COMPRESSION_PREDICTIVE_COST` | Original Gate 4 apparatus FAIL retained; replacement Gate 4 PASS; original derivative Gate 5 FAIL retained; amended Gate 5 PASS; tournament scientific FAIL retained. |

## Sealed challenge ledger

| Challenge | Stage | Verdict | Criteria |
|---|---:|---|---:|
| C-V30 | V3.0 | **PASS** | 5/5 |
| C-V31 | V3.1 | **PASS** | 6/6 |
| C-V32 | V3.2 | **PASS** | 5/5 |
| C-V33 | V3.3 | **PASS** | 5/5 |
| C-V34 | V3.4 | **PASS** | 5/5 |
| C-V35 | V3.5 | **RETIRED_UNOPENED** | — |
| C-V35B | V3.5 | **PASS** | 7/7 |
| C-V36A | V3.6 | **PASS** | 5/5 |
| C-V36B | V3.6 | **PASS** | 5/5 |
| C-V36C | V3.6 | **PASS** | 5/5 |

## V3.6 qualification and gates

Populations B, A-R1, and C each passed their final qualification battery:

- **Population B: PASS** — 2,000 worlds, seeds 3700000:3701999. Replacement native-V2 qualification after the wrong context fixture was barred.
- **Population A-R1: PASS** — 2,000 worlds, seeds 3722000:3723999. Final repaired V3 native-prior qualification after GENERATOR_ONLY localization.
- **Population C: PASS** — 2,000 worlds, seeds 3726000:3727999. Final external shared-support qualification after cardinality and native-support stops.

The Gate-4/Gate-5 history is not collapsed:

- `original_gate_4`: **FAIL_APPARATUS_RETAINED** — split_context_slot: {'world_count': 1000, 'semantic_class': 'SUPPORT_PRESERVING_CONDITIONING', 'restricted_prior_identity_applicable': True, 'restricted_prior_identity_error_max': 5.67323965583455e-14, 'masked_channel_neutrality_error_max': 0.0, 'independent_oracle_error_max': 5.67323965583455e-14, 'posterior_normalization_error_max': 7.549516567451064e-14, 'declared_target_error_max': 0.0, 'finite_all': True, 'target_pathway_removed_all': True, 'unrelated_survivors_preserved_all': True, 'licensed_support_positive_all': False, 'unrelated_absolute_movement': {'classification': 'DESCRIPTIVE_RENORMALIZATION_MOVEMENT', 'note': 'Absolute movement in non-target coordinates is not a selectivity criterion after conditioning the structure prior.'}, 'passed': False}; protect_joint_policy: {'world_count': 1000, 'semantic_class': 'SUPPORT_PRESERVING_CONDITIONING', 'restricted_prior_identity_applicable': True, 'restricted_prior_identity_error_max': 4.8405723873656825e-14, 'masked_channel_neutrality_error_max': 1.3344880755994382e-13, 'independent_oracle_error_max': 0.8999336559889483, 'posterior_normalization_error_max': 5.706546346573305e-14, 'declared_target_error_max': 0.0, 'finite_all': True, 'target_pathway_removed_all': True, 'unrelated_survivors_preserved_all': True, 'licensed_support_positive_all': True, 'unrelated_absolute_movement': {'classification': 'DESCRIPTIVE_RENORMALIZATION_MOVEMENT', 'note': 'Absolute movement in non-target coordinates is not a selectivity criterion after conditioning the structure prior.'}, 'passed': False}
- `replacement_gate_4`: **PASS**
- `original_gate_5`: **FAIL_DERIVATIVE_RETAINED** — Gate 4 retained scientific FAIL
- `amended_gate_5`: **PASS**

## Compression tournament — immutable FAIL

Verdict: **V3.6_COMPRESSION_PREDICTIVE_COST_RETAINED WITH_RETAINED_R1_BRIDGE_QUALIFICATION_FAILURE**. The criterion was lower95(S_V3 − S_V2) ≥ −log(1.02) = −0.01980262729617973 nats per delivered target token, separately for every family.

| Target | Mean D | 95% CI | Result |
|---|---:|---:|---|
| identity | -0.180446262097161 | [-0.188972001302923, -0.171758631456126] | **FAIL** |
| outcome | -0.0206460573498925 | [-0.0232030599486949, -0.0180490913006271] | **FAIL** |
| context | 0.269299286580884 | [0.263763506610797, 0.27470809899015] | **PASS** |
| partner | -0.294284604837813 | [-0.302267480323463, -0.286418031994822] | **FAIL** |
| contact | -0.24009197029472 | [-0.247479872403362, -0.232541650569597] | **FAIL** |

Four families fail: identity, outcome, partner, and contact. Context passes. Outcome still fails even though its interval upper bound is close to the fixed margin; the result is not relabeled. The exact per-stratum values and quantiles are preserved verbatim in `v3-final-profile.json`. No weighted aggregate exists.

## Retained stops and adjudications

Earlier-stage logical stops:

- **V3.0 — Gate-5 parity-helper forwarding FAIL**: `PURE_SOFTWARE_ERROR_RETAINED`; adjudication: V3.0 Gate-5 repair authorization.
- **V3.1 — Gate-3 revisability-floor FAIL**: `SCIENTIFIC_LIMITATION_RETAINED`; adjudication: V3.1 Gate-3 mixed-verdict adjudication.
- **V3.1 — Gate-4 lesion-semantics/restricted-prior sequence**: `APPARATUS_AND_SEMANTIC_STOPS_RETAINED`; adjudication: V3.1 Gate-4 lesion-semantics and selectivity adjudications.
- **V3.2 — Stage-0 scope-identifiability defect**: `DESIGN_DEFECT_RETAINED`; adjudication: V3.2 Stage-0 adjudication.
- **V3.2 — Unserialized repair-pilot preflight**: `CUSTODY_STOP_RETAINED`; adjudication: V3.2 Stage-0 custody adjudication.
- **V3.3 — Fixed-position do-over Stage-0 stop**: `PLAN_FIDELITY_DEFECT_RETAINED`; adjudication: V3.3 Stage-0 adjudication.
- **V3.3 — Do-over-speedup and suggestion-direction Gate-3 FAIL**: `SCIENTIFIC_FINDINGS_RETAINED`; adjudication: V3.3 Gate-3 mixed-verdict adjudication.
- **V3.4 — Root-observation generator/scorer mismatch**: `GENERATOR_DEFECT_RETAINED`; adjudication: V3.4 Stage-0 repair authorization.
- **V3.4 — 32-slice four-edge recovery Gate-5 FAIL**: `INFORMATION_BUDGET_TRANSPLANT_RETAINED`; adjudication: V3.4 Gate-5 adjudication.
- **V3.5 — Original Stage-0 support/topology stop**: `MODEL_SUPPORT_AND_CONSTRUCT_DEFECTS_RETAINED`; adjudication: V3.5 Stage-0 adjudication and amendment 1.
- **V3.5 — Amendment-1 Gate-3 registration selectivity FAIL**: `CANDIDATE_COMMONNESS_DEFECT_RETAINED`; adjudication: V3.5 Gate-3 adjudication amendment 2.

V3.6's freeze declaration retains **41 exact stop/failure records**. They are enumerated without omission below; JSON and Markdown companions remain separate records where both were frozen:

- `gate-3-diagnosis-stub.json` — rounds 11-12; SHA-256 `ea44b66f86bdfa9843445b6eb3e15e4b60c4def01c62a88bb78b0bea3068eb2f`.
- `gate-3-diagnosis-stub.md` — rounds 11-12; SHA-256 `74dc2d02f3b13b1491eb113dd05acf68b939c4d114855a4d6a4af2a03e858928`.
- `gate-3.json` — rounds 11-12; SHA-256 `89c681c0397aa62c1b2214a0095ab6eb64adddb3f8663ff00ea42cbad0cff338`.
- `gate-4-custody-stop.json` — round 14 custody adjudication; SHA-256 `dc309f4e0a4f65fff01d04359954333c75d4f8082b703124426bd3bf766b011a`.
- `gate-4-custody-stop.md` — round 14 custody adjudication; SHA-256 `8f8c243947f38d5f1a0d09453c9e16b482feb458b45f22c6031283ec949c003c`.
- `gate-4-diagnosis-stub.json` — INTERNAL rounds 18-19; SHA-256 `2d26e91094b994836e181c0d5b57e22ccd6d201c69feae6c20a4eb23bcd076d0`.
- `gate-4-replacement-custody-stop.json` — round 14 custody adjudication; SHA-256 `78da8f4281c3ad536707bf2128d55a836d161d05666fe8323eb4fc539a8e1e26`.
- `gate-4-replacement-custody-stop.md` — round 14 custody adjudication; SHA-256 `33046e74f2a4e4e0b6eded9aff29fc68d45ff9962fc610ee18f18b0d1eaa4da5`.
- `gate-4-replacement-diagnosis-stub.json` — retained by V3.6 freeze declaration; SHA-256 `c51dbd18f526861d8735f5c2bc89f194a4594f8314971ba93144e550681904cf`.
- `native-fixture-proof-diagnosis-stub.json` — rounds 12-13; SHA-256 `d10ef057897fd506b9ff7135e3941c67166e63c5408194364a5dccda334fd082`.
- `native-fixture-proof-diagnosis-stub.md` — rounds 12-13; SHA-256 `d6ddb1c038404179d127a58b7f21aa3dfacf664c7cc7601a343330942065e3e9`.
- `population-c-native-support-stop.json` — INTERNAL round 16; SHA-256 `81fe4edcf5f1df2c6327f580e228df4073ba372aa0b93ef8ff8be00516680b39`.
- `population-c-native-support-stop.md` — INTERNAL round 16; SHA-256 `cc13a6a46ac1024d5d399bd022a2569d227eefe88e8f72303055d1a56a6d4f56`.
- `population-c-preflight-stop.json` — Population-C cardinality adjudication before INTERNAL round 16; SHA-256 `a5100d03432349401cd2afebfc2cac38d500899263a7fe04ebbb6f3dc549fdeb`.
- `population-c-preflight-stop.md` — Population-C cardinality adjudication before INTERNAL round 16; SHA-256 `2e2e685f8252eefffbff99e3649f09fe860705ac1752c38791d10a91bf6a6a19`.
- `round18-gate4-diagnosis.json` — INTERNAL round 18; SHA-256 `e0ff0eb82324b0a48f611eaeca125d87c1cd6295f15aaf66cc3ade931ed7d01e`.
- `stage0-adjudicated-pilot-diagnosis-stub.json` — stage-0 adjudication 2; SHA-256 `964ca9ed035e33a6a3d80a6461c69f92903f796bf11ff4630fa387344b117302`.
- `stage0-adjudicated-pilot-diagnosis-stub.md` — stage-0 adjudication 2; SHA-256 `ba61db31ab3c565bae1f07ab2ac2495e84850c75c57fa7545e6a1c7cd0c9f48b`.
- `stage0-custody-stop.json` — stage-0 custody adjudication; SHA-256 `15131611958ee1a70e1dd9e155b3b3cac73c54a4ecc37b2eed30eba4d9f37cc2`.
- `stage0-custody-stop.md` — stage-0 custody adjudication; SHA-256 `0b168058975782ac8e176ae5ffda820168d6ae6d32b293f8ec43618cab1f7d28`.
- `stage0-pilot-diagnosis-stub.json` — stage-0 adjudication 1; SHA-256 `620d05763cfa0c681f909efda209e7f0af9ba11d23c1bc1e06596a0cf556d7b2`.
- `stage0-pilot-diagnosis-stub.md` — stage-0 adjudication 1; SHA-256 `5d337ca0c0b7f074cd0f711c75039d8d6843ca0ac84f0b04ce04e1f2f641f51d`.
- `v3.6-r1-bridge-diagnosis-stub.json` — rounds 11-12; SHA-256 `8e0fa58614b245211c8e84a643e68359132079f14ce576891a7b75d43dcd9c80`.
- `v3.6-r1-bridge-qualification.json` — rounds 11-12; SHA-256 `80462821024b75f304c5dddbab19f8e027966084674b029cfbd929fdb4b68e9d`.
- `v3.6-r1-gate4-verdict.json` — INTERNAL rounds 18-19; SHA-256 `6e7f49fc9b5c37d14cd5154d3ba039f799577c43d5de508627d3f6743083ab48`.
- `v3.6-r1-gate5-verdict.json` — INTERNAL rounds 18-19; SHA-256 `7be4b27ab9d2bae056cb1112f1aab33dc08f62d75608d3689353d7dcc379c801`.
- `v3.6-r1-round12-population-b-stop.json` — rounds 12-13; SHA-256 `dee4b9d400f029ceab25b856b750828f41df041af64b11a23fa06fc4bcab3983`.
- `v3.6-r1-round12-population-b-stop.md` — rounds 12-13; SHA-256 `698cebc6381f2a98378c9bdfac5f8d2903bd0c3fc291cc7503787a1712916ff4`.
- `v3.6-r1-round12-precommit-custody-stop.json` — rounds 12-13; SHA-256 `79dc33825d3eca09e31a4810b1b706f28fa2d70577908e1ac9658e900f8b1feb`.
- `v3.6-r1-round12-precommit-custody-stop.md` — rounds 12-13; SHA-256 `227abcc92a19bcfb6db53aaef3ea79319e489fc9ce8d108cca5675ba472b1f27`.
- `v3.6-r1-round12-resumption-custody-stop.json` — rounds 12-13; SHA-256 `391d50c6a5624981fdf6d6dc406a10d905c2ec8101e2901d6f95ad43636497fc`.
- `v3.6-r1-round12-resumption-custody-stop.md` — rounds 12-13; SHA-256 `427c3b4464dd9dbfb8c1ef1232a366ebb8e13322e87842e2859829eb8cf428f1`.
- `v3.6-r1-round12-v2-native-qualification.json` — rounds 12-13; SHA-256 `6680690898ccca0694f9628278f4ac83a48787c2e7a24ba2691357773385d4fe`.
- `v3.6-r1-round13-population-a-interrupted-custody-stop.json` — round 14 custody adjudication; SHA-256 `fa91d4ec8cac70d5038a6ed9e949aa02b239d12e51d0f882007d96e296b2e2be`.
- `v3.6-r1-round13-population-a-interrupted-custody-stop.md` — round 14 custody adjudication; SHA-256 `d0df85ce72a643609f5ce47b39371c4141b453e50352d634f2515cd206a7fe62`.
- `v3.6-r1-round13-population-a-replacement-interrupted-stop.json` — round 14 custody adjudication; SHA-256 `f53d4659300fad2c71377dfa00906ab9a50a3147265a0e328e3dba1c99207924`.
- `v3.6-r1-round13-population-a-replacement-interrupted-stop.md` — round 14 custody adjudication; SHA-256 `083d17f1608abbf66d78e7e42331ab548e7ab8b740d9cf2f9d778e3290d08d01`.
- `v3.6-r1-round14-population-a-diagnosis-stub.json` — INTERNAL round 15; SHA-256 `cd44e78f7f7056939e2e13f665cc54a8758062c2493f47b963b2bd784663006d`.
- `v3.6-r1-round14-population-a-diagnosis-stub.md` — INTERNAL round 15; SHA-256 `581233842acc0eaf7d8ce3980d49216f8257c9d89795daea62ac8c5a2ca25756`.
- `v3.6-r1-round14-v3-native-replacement-2-qualification.json` — INTERNAL round 15; SHA-256 `ffbbb67c73341737f2e64cdb9089d629ada042fb111285d2caecdea72270b5e8`.
- `v3.6-r1-tournament-verdict.json` — INTERNAL round 17; SHA-256 `40011a462bf3bfbda347b6b77dc8b8abe8246ea1b972b627afb7be57244252a0`.

Internal adjudications 16–19 remain binding and retained:

- **Internal round 16:** Population-C native-support constructor defect; one-line constructor repair and coherence proof; final Population C PASS.
- **Internal round 17:** tournament FAIL is scientific and immutable; continuation authorized; prohibition on post-hoc softening.
- **Internal round 18:** original Gate-4 failures localized as apparatus defects: oracle key collapse and exponential-underflow support accounting.
- **Internal round 19:** verifier-only repairs; replacement Gate 4 PASS; Gate 5 recomputed from retained records and PASS; freeze declared.

## Barred and closed seed ledger

Explicit barred blocks:

- V3.0 `3000000:3001999` — attainability pilot.
- V3.1 `3100000:3101999` — attainability pilot.
- V3.2 `3200000:3201999` — original pilot.
- V3.2 `3230000:3231999` — scope-neutrality repair pilot.
- V3.3 `3300000:3301999` — original pilot.
- V3.3 `3330000:3331999` — event-indexed repair pilot.
- V3.4 `3400000:3401999` — defective-generator pilot.
- V3.4 `3430000:3431999` — corrected pilot.
- V3.5 `3500000:3501999` — original pilot.
- V3.5 `3520000:3520999` — amendment-1 smoke.
- V3.5 `3521000:3522999` — amendment-1 repaired pilot.
- V3.5 `3523000:3523960` — diagnosis-reserved and consumed.
- V3.5 `3523961:3525960` — amendment-2 pilot.
- V3.5 `3525961:3526480` — evaluator pre-seal diagnosis.
- V3.5 `3502000:3509999` — consumed amendment-1 Gates 2-3; non-probative after amendment 2.
- V3.6 `3600000:3600000` — stage-0 custody seed.
- V3.6 `3600001:3603999` — first attainability pilot.
- V3.6 `3660000:3663999` — fresh event-indexed pilot.
- V3.6 `3664000:3664389` — evaluator linter attempt 1.
- V3.6 `3664390:3664769` — evaluator linter attempt 2.
- V3.6 `3664770:3665159` — pre-seal attainability diagnostics.
- V3.6 `3665160:3667159` — gate-3 noninferiority diagnosis.
- V3.6 `3680000:3683999` — retained hybrid bridge qualification.
- V3.6 `3690000:3690000` — round-12 Population-B smoke.
- V3.6 `3692000:3692000` — round-12 Population-A smoke.
- V3.6 `3694000:3694000` — round-12 Population-C smoke.
- V3.6 `3690001:3691999` — Population-B wrong native fixture.
- V3.6 `3630000:3634999` — first Gate-4 custody stop.
- V3.6 `3702000:3706999` — first Gate-4 replacement custody stop.
- V3.6 `3692001:3693999` — first Population-A custody stop.
- V3.6 `3707000:3708999` — Population-A replacement custody stop.
- V3.6 `3714000:3715999` — Population-A theorem-premise qualification stop.
- V3.6 `3724000:3725999` — Population-C native-support stop.

Additional V3.6 custody categories:

- Closed diagnosis-only `3696000:3699999` — R1 diagnosis reserve; never opened.
- Closed diagnosis-only `3716000:3720999` — round-15 length ladder; never opened.
- Retired unconsumed `3694001:3695999` — Population-C short block retired by cardinality adjudication.

Valid once-consumed V3.6 blocks:

- `3604000:3613999` — Gate 2.
- `3614000:3629999` — original Gate 3.
- `3700000:3701999` — replacement Population B.
- `3722000:3723999` — Population A-R1.
- `3726000:3727999` — final Population C.
- `3684000:3689999` — one-shot common-target tournament.
- `3709000:3713999` — Gate 4.
- `3635000:3659999` — Gate 5.
- `3728000:3732999` — replacement Gate 4.

Sealed custody notes:

- C-V35 escrow `4050000:4054999` was retired unopened.
- C-V36A/B/C each consumed only the declared 3,000-seed prefix. Their remainders `4103000:4109999`, `4113000:4119999`, and `4123000:4129999` are retired unconsumed.

## Final boundary

C-V36A, C-V36B, and C-V36C all passed 5/5. That does not erase the tournament's four-family FAIL or any retained stop. T-V3-DO1 and V3.7 remain untouched pending evaluator dispatch.
