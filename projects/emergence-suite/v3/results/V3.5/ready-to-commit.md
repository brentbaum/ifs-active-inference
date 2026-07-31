# V3.5 ready-to-commit list

## Gate 1 and stage machinery

- `contracts/v3.5-protect-contract.md`
- `protocols/v3.5-analysis-plan.md`
- `protocols/v3.5-public-dummy.json`
- `ref/v35.py`
- `ref/v35_oracle.py`
- `scripts/run_v35.py`
- `tests/test_v35_protect.py`
- `results/V3.5/gate-1.json`
- `results/V3.5/gate-1-traces.jsonl`
- `results/V3.5/gate-1-trace-hashes.json`

## Stage-0 pilot and honest stop

- `protocols/v3.5-parameters.json`
- `results/V3.5/stage0-pilot.json`
- `results/V3.5/stage0-pilot-recovery-traces.jsonl`
- `results/V3.5/stage0-pilot-recovery-trace-hashes.json`
- `results/V3.5/stage0-pilot-assays-traces.jsonl`
- `results/V3.5/stage0-pilot-assays-trace-hashes.json`
- `results/V3.5/stage0-diagnosis.md`
- `results/V3.5/stage0-stop.json`
- `results/V3.5/full-fast-suite-stop.json`

No Gate-2–5 result or freeze artifact exists because the stage stopped at the
prospective attainability/calibration pilot.

## Amendment 1 repair cycle — pre-pilot

- `results/V3.5/stage0-adjudication-amendment-1.md` and the external rulings
  are governing evaluator records and remain unchanged.
- `ref/v35.py`, `ref/v35_oracle.py`: common-support dormancy, hierarchical
  support/contact parameters, policy-only stakes, and interventional topology.
- `ref/v35_calibration.py`, `ref/v35_calibration_oracle.py`: expanded item 17.
- `ref/v35_topology.py`, `ref/v35_topology_oracle.py`: exact topology fixture.
- `ref/retro_calibration_audit.py`: additive V3.0–V3.4 audit.
- amended contract, analysis plan, parameters, and public dummy.
- `results/V3.5/stage0-amendment-1-preflight.json`: PASS.
- `results/V3.5/suite-wide-retro-calibration-audit.json`: V3.0–V3.4 PASS.
- each V3.0–V3.4 result tree's
  `amendment-1-retro-calibration-audit.json`.
- `results/V3.5/gate-1-amendment-1-rerun.json`: PASS; the preceding masking
  runner FAIL remains alongside it.
- `results/V3.5/amendment-1-failure-record-addendum.md`.
- `results/V3.5/stage0-amendment-1-smoke.json`: retained FAIL.
- `results/V3.5/stage0-amendment-1-smoke-errata.json`: recovery reconstructed
  from retained traces and the balanced-policy schedule correction recorded.
- all Amendment-1 Gate-1 and smoke trace/hash-ledger files.

## Amendment 1 repaired pilot and custody stop

- `results/V3.5/stage0-amendment-1-pilot.json`: PASS.
- repaired-pilot recovery and assay hash ledgers. Raw `*-traces.jsonl` files
  remain local under the repository's standing trace-ignore rule; their
  complete per-record and file hashes are commit-ready.
- `results/V3.5/stage0-amendment-1-freeze-readiness.json`.
- `results/V3.5/stage0-amendment-1-freeze-readiness.md`.
- `results/V3.5/full-fast-suite-amendment-1.json` (V3 53/53; V2 26/26
  modules).

The numeric floors are frozen in `protocols/v3.5-parameters.json`. Gates 2–5
were unopened at that custody stop. C-V35 was subsequently sealed before
Gate 2 (`f7f560e7...`); escrow remains closed. Gate execution paths now persist
the trace-sink event ledger inside every JSONL world record and seal both
per-record and whole-file hashes before criterion aggregation. Gate 2 is the
only criterion block presently opened by the runner.

## Gate 2 — amendment-1 frozen recovery

- `scripts/run_v35.py`: prospective Gate-2 execution/reporting path only.
- `results/V3.5/gate-2-amendment-1.json`: PASS on all 3,000 ascending seeds.
- `results/V3.5/gate-2-report.md`.
- `results/V3.5/gate-2-amendment-1-trace-hashes.json`: 3,000 records;
  whole-file SHA-256 `ade84592cb755a1463e24b94deef82c3911e4412630969fee12bbeac5a5df496`.
- `results/V3.5/gate-2-amendment-1-traces.jsonl`: local persisted event ledger
  under the standing trace-ignore convention.

Gate 2 passed. Gate 3 is now authorized; Gates 4–5 and escrow remain unopened.

## Gate 3 — honest stop

- `scripts/run_v35.py`: prospective Gate-3 paired execution/reporting path;
  no scientific inference code changed.
- `results/V3.5/gate-3-amendment-1.json`: **FAIL**, retained verbatim.
- `results/V3.5/gate-3-report.md`.
- `results/V3.5/gate-3-diagnosis-stub.md`: apparatus-first localization only;
  no repair proposal or criterion change.
- `results/V3.5/full-fast-suite-gate3-stop.json`: V3 53/53 and cumulative
  V2 180/180 green at the honest stop.
- `results/V3.5/gate-3-amendment-1-trace-hashes.json`: 5,000 records;
  whole-file SHA-256 `f04fdeebf327ceac1a7ddcd4da10b79e86f597e30b56a6c5a92efd6bbfe56c91`.
- `results/V3.5/gate-3-amendment-1-traces.jsonl`: local persisted event ledger
  under the standing trace-ignore convention.

All nineteen nonzero contrasts and both exact identities passed. The blocking
registration-equivalence control failed only for scientific structure weights:
mean maximum absolute movement `0.11144131`, 95% interval
`[0.10178371, 0.12148971]`, versus the frozen `0.01` ROPE. Policy movement was
inside the ROPE. Per the stop rule, Gate 4 (`3510000:3511999`), Gate 5
(`3512000:3519999`), and escrow (`4050000:4054999`) remain unopened. No stage
freeze-readiness record or freeze manifest was produced.

## Amendment 2 — registration construct repair and pre-seal refreeze

- `results/V3.5/gate3-adjudication-amendment-2.md` governs; the earlier Gate-3
  FAIL remains retained and its floors are invalidated.
- `ref/v35.py`: registration alone now uses one candidate-common `M_k=0`
  prior-predictive production in generation and scoring. No other channel was
  changed.
- `ref/v35_oracle.py`: independently authored oracle reflects the same
  declared candidate-common registration model.
- `tests/test_v35_protect.py`: exact cross-candidate evidence and
  delivered-versus-masked posterior identities.
- `results/V3.5/gate-1-amendment-2-rerun.json`: PASS; cross-candidate error
  `0.0`, posterior identity error `7.22e-16`.
- `results/V3.5/stage0-amendment-2-pilot.json`: fresh 2,000-seed traced pilot
  PASS with no failed declared sign; floors mechanically refrozen.
- pilot recovery/assay trace hash ledgers; raw JSONL event ledgers are 800 and
  1,200 records respectively and remain available for custody.
- `results/V3.5/full-fast-suite-amendment-2.json`: V3 55/55 and cumulative V2
  180/180 green.
- `results/V3.5/stage0-amendment-2-freeze-readiness.json` and `.md`: status
  `READY_FOR_C_V35B_SEAL_BEFORE_REPLACEMENT_GATE2`.

Replacement Gates 2–3, original Gates 4–5, retired C-V35 escrow, and new
C-V35B escrow are unopened. STOP for evaluator sealing of C-V35B.

## Post-seal replacement Gate 2

- C-V35B seal `b57339b9...` was verified before opening the replacement
  block; both escrow ranges remain closed.
- `results/V3.5/gate-2-amendment-2.json`: PASS on all 3,000 ascending seeds.
- `results/V3.5/gate-2-amendment-2-report.md`.
- `results/V3.5/gate-2-amendment-2-trace-hashes.json`: whole-file trace hash
  `a89514e2d5ac478e3c4b09d99d80f362c60ad08897341239dd2779a077bee082`.
- Raw JSONL contains the persisted runtime events for every world.

Replacement Gate 3 is now open. Gates 4–5 and escrow remain unopened.

## Replacement Gate 3

- `results/V3.5/gate-3-amendment-2.json`: PASS on all 5,000 ascending seeds;
  all refrozen effects, identities, and registration equivalence passed.
- `results/V3.5/gate-3-amendment-2-report.md`.
- `results/V3.5/gate-3-amendment-2-trace-hashes.json`: whole-file trace hash
  `b6ad9bf1ef0e564a18cb5f4694c92971680949a01d30ce54b4e8a1a3f3f390f5`.
- Opposed/allied results are separate; opposed `D` values retain the
  preregistered negated-raw convention.

Gate 4 is now open. Gate 5 and escrow remain unopened.

## Gate 4 and disconnect custody

- `results/V3.5/gate-4-amendment-2.json`: PASS on all 2,000 ascending seeds.
- `results/V3.5/gate-4-amendment-2-report.md`.
- `results/V3.5/gate-4-amendment-2-trace-hashes.json`: whole-file trace hash
  `a55d003c10e9d0880948321c0df3ff685a7e7e6eff6301dde0be62529c3d00e3`.
- After the stream disconnect, no Gate-5 result, trace, partial JSONL, or hash
  ledger existed. The full Gate-5 block was therefore established as
  unconsumed before execution resumed.
- V3.0–V3.4 freeze manifests preflight with zero mismatches.

Gate 5 is now open. Both escrow ranges remain untouched.

## Gate 5 and amendment-2 freeze candidate

- `results/V3.5/gate-5-amendment-2.json`: **PASS** on all 8,000 seeds in
  `3512000:3519999`, consumed once, ascending and gap-free.
- `results/V3.5/gate-5-amendment-2-report.md`: primary cells block at their
  refrozen floors; shorter-history and robustness sweeps are reported without
  transplanting primary information-budget floors.
- `results/V3.5/gate-5-amendment-2-trace-hashes.json`: 8,000 persisted runtime
  records; whole-file trace hash
  `2ff6c50142f6ba3e2ee5a9c18dce60169070e36afb1a587edbcc5dc8fc263896`.
- Whole-program recovery accuracy is `0.598`; minimum per-edge accuracy is
  `0.724`. Per-edge accuracies and all sweep localizations are retained in the
  Gate-5 record.
- V3.0–V3.4 freeze manifests verify **31/31, 42/42, 42/42, 53/53, and 82/82**.
- `results/V3.5/full-fast-suite-final.json`: V3 **55/55** and cumulative V2
  **180/180** green.
- `results/V3.5/freeze-readiness.json` and `.md`: status
  `FREEZE_READY_AMENDMENT2_ALL_GATES_PASS_AWAITING_C_V35B`.
- `results/V3.5/freeze-manifest.json`: **47/47** hashes independently
  reverified after packaging.
- `results/V3.5/decisions.md` and `development-failures.md`: amendment history,
  retained failures, and custody decisions remain explicit.

Both escrow ranges remain untouched: retired C-V35 `4050000:4054999` and
sealed C-V35B `4055000:4059999`. STOP for evaluator reveal-and-run of C-V35B.
