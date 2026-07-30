# V3.2 development failures ledger

## Stage 0 — retained

- Population: pilot `3200000:3201999` (barred).
- Failure: witnessing context-scope gain mean
  `-1.4481277843536589e-11`; a positive floor is unattainable.
- Consequence: parameter slot `witnessing_scope_gain` remains unfrozen; no
  criterion population was opened.
- Localization: the single-regime comparator already identifies
  context-specific scope through its context-0 likelihood.

## Repair pilot — custody disclosure

- Population: repair pilot `3230000:3231999` (barred).
- Scientific result: repaired witnessing gain `0.800036943234541`; positive
  SESOI `0.400` is attainable.
- Process failure: seeds `3230000:3230019` were invoked once in a manual
  preflight without execution-time trace serialization before the fully traced
  formal pilot; seed `3230000` was also regenerated once after the stop for an
  untraced semantic spot check.
- Consequence: progression stopped before Gate 1 for external adjudication.
