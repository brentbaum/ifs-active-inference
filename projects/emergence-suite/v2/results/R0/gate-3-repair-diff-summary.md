# R0 Gate-3 authorized repair diff summary

**Classification:** pure software error  
**Original record:** `gate-3.json` — retained `FAIL`  
**Repaired record:** `gate-3-repaired.json` — `PASS`

## Authorized source change

The Gate-3 positive-check mapping changed only:

```text
new_code_required: false
```

to:

```text
zero_new_code_required: true
```

The generic all-positive verdict aggregation is unchanged.

## Re-execution identity

The same block `1001000:1002999` was re-executed. Canonical byte
representations and SHA-256 hashes match for every recorded non-verdict field:
cell counts, per-cell dry-run quantities and deterministic hashes, failure
records, escrow custody, gate number, seed block, and stage. The only record
differences are the authorized polarity key/value and the resulting top-level
verdict.

No world constructor, protocol constructor, composition operator, restriction
normalizer, bridge, schema, RNG key, or dry-run calculation changed.
