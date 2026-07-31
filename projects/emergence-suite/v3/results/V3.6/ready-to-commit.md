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
