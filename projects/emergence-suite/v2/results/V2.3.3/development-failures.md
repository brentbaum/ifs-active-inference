# V2.3.3 development failures

No official Gate 1–5 criterion failed.

Pre-official execution/reporting issues are retained:

- A temporary interactive Gate-2 wrapper had a `SyntaxError` before it called
  the bank or any scientific protocol. The fixed protocol itself was unchanged.
- The first Gate-2 reporting wrapper requested nonexistent key
  `retained_counts` and raised `KeyError: 'retained_counts'` after construction.
  The frozen ledger field is `eligible_counts_retained`.
- Gate-3 and the first Gate-4 print wrappers raised
  `TypeError: Object of type bool is not JSON serializable` for NumPy boolean
  report scalars after the calculations completed. Scalars were normalized for
  serialization; no metric changed.
- The first masked-to-safe lesion diagnostic was incorrectly run on the mixed
  85/15 safe/adverse stream. It yielded `M^PT=7.672084348161037` (95% interval
  `[7.2585711930604555, 8.081798735460927]`) and
  `M^PD=13.61799003126592` (`[12.899562254965618,
  14.325087150388851]`). That diagnostic changed hidden adverse content into a
  safe token and therefore did not instantiate the frozen safe-substitution
  lesion. The official lesion uses the declared corrective-safe support in both
  paired arms and yields exact zero contrasts.
