# R0 Gate-3 diagnosis stub

**Status:** blocking stop before Gate 4  
**Observed verdict:** `FAIL`  
**Stage:** V2.G0 apparatus only  
**Escrow accessed:** no  
**Diagnosis-reserved seeds accessed:** no

## Immutable observed result

`run_v2g0_gates.py 3` executed the full public Gate-3 block
`1001000:1002999` once and wrote `gate-3.json`.

The recorded composition results are:

- all 2,000 seeds executed;
- all six required public cells were present;
- every cell executed without an exception;
- exact production trace log probabilities matched the trace records;
- each cell passed two construction/support/schema dry-runs;
- every dry-run recorded `scientific_scores_inspected=false`;
- the execution recorded no cell failure;
- escrow was untouched.

The immutable top-level verdict is nevertheless `FAIL`.

## Failure localization

The runner stores this desired linter outcome in the checks mapping:

```json
"new_code_required": false
```

The generic verdict helper applies `all(checks.values())`. It therefore treats
the correct negative custody fact—no new code was required—as a failed positive
criterion. The declared criterion is satisfied, but its boolean polarity is
incompatible with the generic aggregation convention.

This localizes to the Gate-3 runner/result encoding. It is not a failure of a
world constructor, protocol constructor, composition operator, restriction
normalizer, bridge, support check, schema check, or custody dry-run. No
scientific score or psychological claim exists in R0.

## Provisional taxonomy

**Provisional classification:** pure software error in verdict aggregation.

A prospective repair would rename the positive check to a form such as
`zero_new_code_required: true`, without changing any world, schema, RNG key,
normalizer, dry-run record, or composition result. No repair or rerun is
performed here. Authorization and byte-identity requirements must be handled
before any repaired execution.

## Stop custody

- Gate 2 remains recorded as `PASS`.
- Gate 3 remains recorded as `FAIL` pending adjudication/repair authorization.
- Gate-3 seeds `1001000:1002999` have been consumed by the recorded execution.
- Gate-4 seeds `1003000:1003999` are untouched.
- Gate-5 seeds `1004000:1009999` are untouched.
- Diagnosis block `1010000:1019999` is untouched.
- C-V2G0 escrow `2000000:2000499` is untouched.

