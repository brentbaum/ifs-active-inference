# V3.3 ready-to-commit list

Stage status: **Gate-3 FAIL; Gates 4–5 unopened**.

## Source and public declarations

- `ref/v33.py`
- `scripts/run_v33.py`
- `tests/test_v33_prune.py`
- `contracts/v3.3-prune-contract.md`
- `protocols/v3.3-analysis-plan.md`
- `protocols/v3.3-parameters.json`

## Results and custody

- `results/V3.3/stage0-event-pilot.json`
- `results/V3.3/stage0-event-pilot-report.md`
- `results/V3.3/stage0-event-pilot-*-trace-hashes.json`
- `results/V3.3/gate-2.json`
- `results/V3.3/gate-2-report.md`
- `results/V3.3/gate-2-trace-hashes.json`
- `results/V3.3/gate-2-traces.jsonl`
- `results/V3.3/gate-3.json`
- `results/V3.3/gate-3-report.md`
- `results/V3.3/gate-3-diagnosis-stub.json`
- `results/V3.3/gate-3-stop.md`
- `results/V3.3/gate-3-trace-hashes.json`
- `results/V3.3/gate-3-traces.jsonl`
- `results/V3.3/development-failures.md`
- `results/V3.3/decisions.md`
- `results/V3.3/full-fast-suite-stop.json`

All new trace bundles are below 90 MB, so the V3.2 local-only large-bundle
convention is not triggered. The two pilot JSONL bundles are nevertheless
ignored by the repository's standing non-gate trace policy and remain local;
their complete per-record and file hashes are in the listed ledgers. Gate-2
and Gate-3 JSONL bundles are ready to commit. Existing unrelated working-tree
changes are not part of this list.
