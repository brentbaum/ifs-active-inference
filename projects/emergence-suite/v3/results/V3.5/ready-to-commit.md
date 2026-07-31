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
are unopened. The next authorized action is evaluator sealing of C-V35; this
implementation stops before Gate 2.
