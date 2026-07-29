# V2.5b development failures

## Gate 1 — FAIL

Retained failed proofs:

- `3_prior_charged_once`
- `6_material_reduction_odds_identity`

The independent oracle mutated the production prior through an aliased NumPy
array. See `gate-1-diagnosis-stub.md`. No Gate-2 or Gate-3 seed was opened.

