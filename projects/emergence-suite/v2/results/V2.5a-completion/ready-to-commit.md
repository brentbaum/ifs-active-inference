# V2.5a completion ready-to-commit inventory

## Custody succession

- `results/V2.0/freeze-manifest-addendum-perf1.json`
- `results/V2.1/freeze-manifest-addendum-perf1.json`
- `results/V2.2.1/freeze-manifest-addendum-perf1.json`
- `results/V2.3.2-formation/freeze-manifest-addendum-perf1.json`
- `results/V2.3.3/freeze-manifest-addendum-perf1.json`
- `results/V2.4.4/freeze-manifest-addendum-perf1.json`
- `results/V2.5a/freeze-manifest-addendum-perf1.json`
- `results/R0/freeze-manifest-addendum-perf1.json`
- `run_v2g0_gates.py`
- `tests/test_v2g0_grammar.py`

Every base manifest remains unchanged. The addenda record exact successor
hashes and authorizing commits.

## Completion runner and tests

- `run_v25a_completion.py`
- `ref/v25a_completion.py`
- `tests/test_v25a_completion.py`

## Gate records

- Gate-1 authorized repair records and diff summary
- Gate-2 report and 800-world ledger
- Gate-3 report and eight assay/matching ledgers
- Gate-4 report and six lesion ledgers
- Original Gate-5 FAIL and diagnosis, retained unchanged
- `results/V2.5a-completion/gate-5-repaired.json`
- `results/V2.5a-completion/gate-5-repaired-full-fast-suite.log`
- eight retained Gate-5 robustness ledgers

## Freeze candidate

- `results/V2.5a-completion/freeze-readiness.md`
- `results/V2.5a-completion/freeze-manifest.json`
- `results/V2.5a-completion/development-failures.md`
- this inventory

Status:
`FREEZE_READY_ADJUDICATED_MIXED_FORMAT_CORE_PLUS_MASTER_COMPLETION_PASS`.
C-V25A remains evaluator work; its escrow was not accessed.

## Pre-seal escrow-threading amendment

- `ref/v25a_completion.py`
- `tests/test_v25a_completion.py`
- `results/V2.5a-completion/escrow-threading-byte-identity.json`
- `results/V2.5a-completion/escrow-threading-full-suite.json`
- `results/V2.5a-completion/escrow-threading-diff-summary.md`
- `results/V2.5a-completion/freeze-manifest-addendum-escrow-threading.json`

Default development output is byte-identical on both pinned seeds. Escrow
generation remains inaccessible by default and requires the future challenge
runner to pass its evaluator-released block explicitly.
