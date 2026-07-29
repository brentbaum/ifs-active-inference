# R0 Gate-5 authorized repair diff summary

**Classification:** pure software error  
**Original record:** `gate-5.json` — retained `FAIL`  
**Repaired record:** `gate-5-repaired.json`

## Authorized source change

The V2.4.4 verifier now reads the base `freeze-manifest.json`, overlays the
committed `freeze-manifest-addendum.json`, hashes the resulting effective
87-file chain, and records the SHA-256 of both custody files.

## Re-execution identity

The same R0 block `1004000:1009999` was re-executed. Every recorded
non-manifest field is byte-identical to the original execution. The full suite
was independently rerun; its fresh status and test count matched the original.
Fresh wall-clock timing is disclosed in the byte-identity record, while the
repaired gate record retains the original nondeterministic timing block
verbatim for the required non-manifest byte comparison.

Permitted record differences are limited to the manifest-chain fields, their
positive verification check, the explicit repaired-execution suite check, and
the resulting verdict.

No world, scientific result, inherited file, gate criterion, or seed changed.
