# V3.6 ready-to-commit ledger

## Composition machinery drafted before the custody stop

- `ref/v36.py`: composition-only orchestration over frozen V3.1–V3.5 public
  APIs; no new likelihood, latent variable, prior, or update equation.
- `ref/v36_oracle.py`: independently authored readout and code-length
  recombination paths with copied inputs.
- `ref/__init__.py`: exposes the two V3.6 modules without removing existing
  exports.

## Honest Stage-0 stop

- `results/V3.6/stage0-custody-stop.json`
- `results/V3.6/stage0-custody-stop.md`

Seed `3600000` was consumed once during a smoke invocation whose trace context
was not persisted to JSONL and hashed at execution. No criterion was evaluated,
no floor was frozen, and no other V3.6 seed was touched. Gates 2–5, diagnosis
blocks, and C-V36A/B/C escrow remain unopened. STOP for evaluator custody
adjudication.

## Custody adjudication and resumed Stage 0

- `stage0-custody-adjudication.md` permanently bars seed `3600000` and
  re-scopes the pilot to `3600001:3603999`.
- The public contract, prospective analysis plan, parameters, dummy bundle,
  compression registry, composition module, independent oracle, tests, and
  runner were written before the re-scoped pilot.
- `gate-1.json` / `gate-1.md`: PASS, 18/18 permanent composition checks; no
  seed consumed.
- `stage-0-attainability-pilot-traces.jsonl` and
  `stage-0-attainability-pilot-trace-hashes.json`: 3,999 persisted, hashed,
  ascending gap-free records. The hash verifies before aggregation.
- `stage-0-attainability-pilot.json` / `.md`: FAIL because the premature
  do-over 95% interval `[-0.01857, 0.04912]` is not contained in the frozen
  `[-0.01, 0.01]` ROPE.
- `stage0-pilot-diagnosis-stub.json` / `.md`: honest stop. No floors frozen;
  no Gate-2/3/4/5, diagnosis, or escrow seed opened.

Current disposition: **STAGE0_PILOT_FAIL_STOP_FOR_EVALUATOR**.

Verification at stop: V3 suite `60/60` green; cumulative V2 suite `180/180`
green. An initial repository-root V2 invocation was invalid because `ref` was
not on that working directory's import path; the canonical invocation from
`projects/emergence-suite/v2/` passed cleanly.

## Premature-do-over adjudication and fresh pilot

- `stage0-adjudication.md` classified the first plan's equivalence declaration
  as a V3.3 claim-fidelity defect. Premature do-over was prospectively amended
  to a positive causal contrast; post-revision do-over remains the equivalence.
- Pre-pilot commits: `e583327` (plan fidelity and Gate-1 addendum), `e20b60f`
  (pruning-disabled comparator retains corrective evidence).
- `gate-1-adjudicated.json` / `.md`: PASS. The moving-boundary schedule fixture
  proves premature and post-revision episodes follow each world's observed
  event, not a fixed slice.
- Fresh pilot `3660000:3663999`: 4,000 persisted, hashed, ascending gap-free
  records. The JSONL hash verifies before aggregation.
- The corrected premature contrast failed: mean `-0.0075913`, 95% interval
  `[-0.0368806, 0.0217219]`, which does not carry the declared positive sign.
  The other nine comparator directions and the stakes identity/path passed.
- `stage0-adjudicated-pilot-diagnosis-stub.json` / `.md`: honest stop as the
  genuine composition finding specified by the adjudication.

Current disposition: **FRESH_PILOT_FAIL_STOP_GENUINE_COMPOSITION_FINDING**.
No floors, freeze-readiness, or stage manifest were issued; all later and
escrow blocks remain unopened.

## Adjudication 2 and pre-seal freeze

- `stage0-adjudication-2.md` retains the premature endpoint contrast as a
  descriptive composition finding, not a criterion. No third pilot ran.
- Both required estimates are frozen into `v3.6-parameters.json`: first pilot
  `0.0151395 [-0.0185675, 0.0491169]`; fresh event-indexed pilot
  `-0.0075913 [-0.0368806, 0.0217219]`.
- The finding has `floor: null` and `gate_criterion: false`. The sealed V3.3
  post-revision equivalence remains unchanged.
- Nine remaining comparator floors and the stakes-policy floor were computed
  mechanically at exactly `0.50 * abs(fresh pilot mean)`. Stakes scientific
  identity remains `1e-10`; the V2-only noninferiority margin remains
  `0.018566762350958` nats/token.
- `v3.6-compression-accounting.json` is finalized, including every V3.5 repair
  factor and the fresh-pilot per-world structure-length distribution (mean
  `106.7830171`, range `101.4503498:111.4503498` bits).
- `stage0-freeze-readiness.json` / `.md`, `stage0-freeze-manifest.json`, and
  `stage0-pre-seal-package.json` are ready. The manifest verifies `21/21`
  hashes.
- V3 full suite: `63/63` green.

Current disposition: **STAGE0_FREEZE_READY_AWAITING_C_V36A_B_C_SEALS**.
Gates 2--5, diagnosis remainder, and all escrows remain untouched.

## Authorized gates 2–3

- C-V36A/B/C were sealed before Gate 2. Escrows remain closed. Evaluator-used
  diagnosis seeds `3664000:3665159` were not touched.
- Gate 2 `3604000:3613999`: **PASS**. Active-count accuracy `0.9996`, minimum
  edge accuracy `0.697`, program accuracy `0.5696`, ECE `0.01183`, coverage
  `0.9796`, candidate-support pass rate `1.0`, registration identity maximum
  `1.46e-13`, and stakes scientific identity `0.0`.
- Gate 3 `3614000:3629999`: formal **FAIL — honest stop**. All nine frozen
  ablations, stakes, stress cells, and ≥50% economy criteria passed. Predictive
  noninferiority alone failed: V3−V2 mean `-0.0338625`, 95% interval
  `[-0.0379879, -0.0296089]`, versus frozen margin `0.018566762350958`.
- The premature endpoint remains descriptive only. Gate-3 mean `0.0067153`,
  95% interval `[-0.0063220, 0.0198961]`; both pilot intervals were also
  published in the Gate-3 record.
- Gate-2 and Gate-3 trace files were persisted and hashed before criteria;
  both ledgers verify. Gates 4 and 5 were not opened.

Current disposition: **GATE3_FAIL_STOP_PREDICTIVE_NONINFERIORITY**.
V3 full suite at stop: `63/63` green. The pre-existing evaluator partial file
`cv36-preseal-pilot-traces-attempt1-partial.jsonl` remains untouched and is not
part of this execution's ready-to-commit set.

## Gate-3 noninferiority diagnosis

- Diagnosis block `3665160:3667159`: 2,000 seeds consumed once, ascending and
  gap-free. Per-world rows and runtime event ledgers were persisted before
  aggregation; trace SHA-256 is
  `646fd20d42b224aa37e7d82e55aa72c7520b3cf60fabe88371ba94e1eb29a9ca`.
- Support equality failed apparatus-first: `0/2000` observation documents are
  byte-identical. V2 scores `(self, outcome, localization)` over 18/30 slices;
  V3 scores `(mode, root, world, policy proposal, outcome)` over 16 separately
  generated slices. Token counts and masking also differ.
- The deficit is not normalization-stable: frozen nominal-token mean
  `-0.0334165`; delivered-token mean `-0.00287369`; equal-weight,
  truth-clamped channel-type mean `+0.0269965`.
- The structure/model-averaging term accounts for `87.7%` of the frozen mean
  deficit. V2's three-candidate structure term averages `-1.36978` nats/world;
  V3's 128-program GROW term averages `-3.76743` nats/world.
- Gate 3 had copied its passing calibration profile from Gate 2; it did not
  calibrate the fixed 16-slice tournament population. On the diagnosis worlds,
  V3 exact-program accuracy is `0.025`, ECE `0.286`, and normalized entropy
  `0.465`. This is separate from the unequal-support likelihood comparison.
- Gates 4–5, escrow, barred blocks, criteria, floors, and scientific modules
  were untouched. The committed Gate-3 FAIL remains unclassified pending
  evaluator adjudication.

Ready-to-commit diagnosis files:

- `scripts/run_v36_noninferiority_diagnosis.py`
- `results/V3.6/gate3-noninferiority-diagnosis-traces.jsonl` (local persisted
  trace bundle, intentionally ignored by the repository's trace rule; pinned
  by the committed hash ledger)
- `results/V3.6/gate3-noninferiority-diagnosis-trace-hashes.json`
- `results/V3.6/gate3-noninferiority-decomposition.json`
- `results/V3.6/gate3-noninferiority-decomposition.md`
- `results/V3.6/ready-to-commit.md`

## Amendment 3 — pre-criterion common-target bridge freeze

- Read and adopted `gate3-adjudication-amendment-3.md` and external round-11
  rulings 1–5 and 10. The invalid original tournament remains unchanged.
- Added the canonical 64-slice R0 document, five deterministic target
  adapters, native-prior V3 model average, exactly one V2 module per target,
  predictive-equivalence classes, and independent arithmetic oracle.
- All fourteen pre-criterion proofs pass on the RNG-free public dummy.
- Frozen `delta = log(1.02) = 0.01980262729617973` per delivered target token.
- The public-dummy event ledger was persisted and hashed before the proof
  aggregate. No seed in `3680000:3689999` was consumed at this freeze point.
- `v3.6-r1-precriterion-freeze-manifest.json` pins ten bridge, plan, oracle,
  test, and proof artifacts before criterion execution.

Pre-criterion bridge package:

- `contracts/v3.6-r1-common-target-bridge.md`
- `protocols/v3.6-r1-analysis-plan.md`
- `protocols/v3.6-r1-bridge-spec.json`
- `ref/v36_bridge.py`
- `ref/v36_bridge_oracle.py`
- `scripts/run_v36_r1.py`
- `tests/test_v36_bridge.py`
- `results/V3.6/v3.6-r1-bridge-proofs.json`
- `results/V3.6/v3.6-r1-bridge-proofs.md`
- `results/V3.6/v3.6-r1-bridge-proofs-trace-hashes.json`
- `results/V3.6/v3.6-r1-bridge-proofs-trace.jsonl` (persisted public-dummy
  proof ledger; pinned by the adjacent hash record)
- `results/V3.6/v3.6-r1-precriterion-freeze-manifest.json`

## Amendment 3 — bridge qualification honest stop

- Consumed `3680000:3683999` exactly once, ascending and gap-free: 2,000
  own-prior common-document fixtures followed by 2,000 fixed-stratum worlds.
- Persisted all 4,000 event ledgers and per-world records before aggregation.
  Trace SHA-256:
  `d749ad565013357f976f45a542ecf83733618dbf40b043fd78e263df5f8a5201`.
- Per-seed world, observation, and held-out-target hashes were identical across
  the V2 and V3 adapter views.
- V2 precision qualification passed for every target. Full 10,000-replicate
  interval widths ranged from `0.00324` to `0.01533`, all below
  `delta=0.01980262729617973`.
- Predictive calibration failed its frozen `ECE <= 0.05` requirement for V2
  identity `0.15170`, outcome `0.05650`, context `0.11897`, and partner
  `0.22798`, and for V3 identity `0.08514`.
- Structural calibration also failed: equivalence-class ECE `0.27892`, 95%
  class-set coverage `0.2405`, and active-count ECE `0.26085`. Every
  load-bearing edge ECE passed (`0.01493`–`0.04583`).
- Verdict: **FAIL_APPARATUS_STOP**. The repaired tournament block
  `3684000:3689999`, diagnosis reserve, Gates 4–5, and all escrow remain
  untouched. No scientific predictive-price result was computed.

Bridge-stop files ready to commit:

- `results/V3.6/v3.6-r1-bridge-qualification.json`
- `results/V3.6/v3.6-r1-bridge-qualification.md`
- `results/V3.6/v3.6-r1-bridge-diagnosis-stub.json`
- `results/V3.6/v3.6-r1-bridge-trace-hashes.json`
- `results/V3.6/v3.6-r1-bridge-traces.jsonl` (local persisted trace bundle,
  ignored by repository policy and pinned by the hash ledger)
- `results/V3.6/ready-to-commit.md`

## Amendment 4 — round-12 precommitments

- The consumed amendment-3 hybrid is retained and demoted to
  `HYBRID_GENERATOR_DIAGNOSIS_ONLY`; it is neither model's native-prior
  calibration population.
- Permanent bridge proof 15 independently enumerates the posterior predictive
  of each observable target for both model adapters. All ten comparisons have
  maximum error `0.0`; no latent posterior is reused as a token forecast.
- The V3 context adapter now conditions only on context emissions present in
  the common document. It no longer manufactures V3.2 root, active-count,
  scope, or dynamics diagnostic tokens. Frozen V2/V3 scientific sources and
  parameters remain byte-identical.
- `shared-target-support-audit.json` freezes binary intersection support and
  the external `.20/.50/.80` public grid without consulting model score
  differences. The external generator uses a declared two-state Markov partner
  process, public V3.2 context path/emission functions, a common intervention
  schedule, and four balanced metadata-only strata.
- Calibration is frozen as world-weighted ten-bin ECE, with repaired
  active-count top-label and macro-classwise definitions and deterministic HPD
  class coverage. The complete factorized structure/class posterior and every
  recomputation field must be serialized before aggregation.
- `v3.6-r1-round12-precommit.json`: **PASS**. Fifteen bridge proofs pass,
  support passes, and scientific-source hash identity passes.
- `v3.6-r1-round12-precommit-manifest.json`: 17/17 hashes verified. No seed was
  consumed.

Phase-1 commit boundary: all files in the round-12 precommit manifest must be
committed before Population B seed `3690000` is opened.

### Phase-1 custody stop

- Phase-1 relevant tests: V3 suite `70/70` green.
- The 17-file precommit manifest verifies with zero mismatches.
- `git add`/commit could not begin because `.git` is read-only in this
  execution environment: creation of `.git/index.lock` returned `Operation not
  permitted`. Nothing was staged.
- Additional custody failure discovered and disclosed: precommit smoke calls
  consumed the first assigned seed of Population B (`3690000`, five target
  fixtures), Population A (`3692000`, native world plus calibration state),
  and Population C (`3694000`, external world). Their trace contexts remained
  in memory; no JSONL event ledger was persisted or hashed. No criterion was
  evaluated.
- No other qualification seed and no tournament, Gate 4, Gate 5, diagnosis,
  barred, or escrow seed was opened.
- Stop records:
  `v3.6-r1-round12-precommit-custody-stop.json` and `.md`.

Current disposition:
**CUSTODY_FAILURE_PRECOMMIT_SMOKE_CONSUMED_ASSIGNED_SEEDS_WITHOUT_PERSISTED_LEDGERS_AND_GIT_METADATA_READ_ONLY**.
Return to the evaluator for custody adjudication before any seeded execution.
