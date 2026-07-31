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
