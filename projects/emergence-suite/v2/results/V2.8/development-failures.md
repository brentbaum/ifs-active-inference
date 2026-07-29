# V2.8 development-failures ledger

No scientific gate failed.

Two pre-criterion development findings are retained:

1. The initial 32-slice redescription pilot had inadequate attainable material
   redescription. The protocol adopted the already-frozen V2.4 96-slice
   primary budget before freeze; no inherited parameter changed.
2. Gate 4's first runner attempt supplied 12 actions to inherited maintenance
   histories shorter than 12 slices. It stopped before criterion evaluation.
   The fixture was corrected to use the history's actual length; no scientific
   computation or threshold changed.

The sandbox rejected `ProcessPoolExecutor` semaphore inspection. The runner
used its deterministic ordered-thread fallback. This was an execution-context
limitation, not a scientific failure.

