# V2.5a Gate-5 authorized repair diff summary

**Classification:** pure software error  
**Original record:** `gate-5.json` — retained FAIL  
**Repaired record:** `gate-5-repaired.json`

## Authorized source change

The V2.5a and repaired R0 Gate-5 verifiers now delegate to the single public `ref.manifest_chain.verify_manifest_chain` helper. The helper reads the base manifest, applies explicitly declared committed addenda in order, verifies the effective file map, and records every custody manifest hash. R0's refactor is preserved by its new freeze-manifest addendum.

## Re-execution identity

The complete V2.5a Gate-5 block `761000:763999` was re-executed. All deterministic scientific, semantic, robustness, and cumulative artifacts were byte-identical. Every field in the repaired gate record outside the authorized manifest-verification and resulting verdict fields is byte-identical to the original. Fresh suite timing and its increased regression-test count are disclosed only in the byte-identity record and repaired-suite log; the repaired gate record retains the original nondeterministic timing fields.

No world, scientific result, likelihood, prior, threshold, parameter, seed, presentation definition, or criterion changed.

The first identity-record emission incorrectly compared the complete
`checks` mapping even though that mapping contains the explicitly permitted
manifest-verification fields. The final audit partitions those two fields
from the non-manifest checks. This bookkeeping correction required no seed
or scientific reexecution; the already-completed rerun had independently
established deterministic identity and a green full suite.
