# V3.2 development failures ledger

## Stage 0 — retained

- Population: pilot `3200000:3201999` (barred).
- Failure: witnessing context-scope gain mean
  `-1.4481277843536589e-11`; a positive floor is unattainable.
- Consequence: parameter slot `witnessing_scope_gain` remains unfrozen; no
  criterion population was opened.
- Localization: the single-regime comparator already identifies
  context-specific scope through its context-0 likelihood.

