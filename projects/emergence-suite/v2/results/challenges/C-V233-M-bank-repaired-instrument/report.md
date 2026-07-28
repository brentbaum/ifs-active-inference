# C-V233-M-bank (repaired instrument)

Sealed invalidate-and-repeat verdict: **FAIL**.

The repaired instrument consumed all 800 candidate seeds (`815001:815800`)
once in ascending order. No constructor call was repeated after the completed
run. The original frozen-instrument `FAIL_UNEXECUTABLE` remains preserved
under `results/challenges/C-V233-M-bank/`.

## Scientific precondition — FAIL

- moderate: 14/800, rate `0.017500` (95% Wilson `[0.010452, 0.029159]`); did not reach 40 eligible worlds.
- strong: 33/800, rate `0.041250` (95% Wilson `[0.029521, 0.057364]`); did not reach 40 eligible worlds.
- very_strong: 77/800, rate `0.096250` (95% Wilson `[0.077699, 0.118660]`); filled at position `402`, seed `815402`.

Moderate is short by 26 worlds and strong by 7 worlds. Very-strong exceeds
the minimum by 37 and first filled at position 402. Under the precommitted
interpretation, the two shortfalls are formation-yield findings about the
frozen constructor. No regeneration or rule change was attempted.

## Semantic integrity — PASS

All `87` retained states
reconstructed exactly from the declared priors and frozen update equations;
maximum provenance error was
`0`. The one-posterior audit passed
on all ten hash-seeded random retained states, with no failures.

## Process custody — PASS

The ITS ledger contains 800 consecutive released seeds with no gaps. All
`800` candidate states serialized,
reloaded, and rehashed bitwise with zero failures. Released-block
authorization `815001:815800` is logged on every row.

The completed run initially stopped during Markdown rendering because the
formatter assumed every stratum had a non-null fill record. Scientific
outputs had already been persisted. Finalization used those artifacts without
rerunning the constructor. The initial custody classifier also duplicated the
120-state yield requirement; this was corrected analysis-only so criterion 3
reflects its sealed ledger/rehash definition.

## Distributional stress — descriptive only

q0(P) had mean `0.938942`, median `0.999811`, p05
`0.530438`, p95 `1.000000`, minimum
`0.004550`, and maximum `1.000000`. Full values
and fill curves are in `per_seed.csv`. This class is non-criterial.

## Standing

Scientific precondition: **FAIL**. Semantic integrity: **PASS**. Process
custody: **PASS**. Distributional stress: **DESCRIPTIVE ONLY**. The overall
verdict is **FAIL** because criteria 1–3 are conjunctive. The maintenance
bundle and seeds `816001:816900` remain closed and were not accessed.
