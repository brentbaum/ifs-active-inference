# C-V33 immutable sealed verdict: PASS

All five sealed criteria passed. This verdict is retained as written.

## Population results

1. **Correction reduces — PASS.** Cell 1 material-reduction rate was `0.977`
   against the `0.89` floor. Mean mode retention was `1.0`, and the maximum
   historical old-graph query error was exactly `0.0`.
2. **Do-over equivalence — PASS.** Cell 2 material rate was `0.975`, a paired
   rate difference of `-0.002` from Cell 1. Mean paired first-material-time
   difference was `-0.008` slices across all 1,000 pairs, within the `0.5`
   bound. Event-index schedule identity was exact in every world. The sealed
   result supports the adjudicated do-over null at evidence ceiling.
3. **Premature imagery is not durable — PASS.** Cell 3 durable material
   reduction was `0.0`, below the `0.09` ceiling.
4. **Adaptive structure survives — PASS.** Cell 4 burden-edge material
   reduction was `0.975`; mean posterior support for adaptive `W_Y` was
   `0.997979`, above the `0.748` floor.
5. **Semantic and custody — PASS.** Maximum neutral-observation posterior error
   was exactly `0.0`. All 4,000 escrow seeds were consumed once, ascending and
   gap-free. All raw traces were serialized and hashed before criterion
   evaluation.

## Verdict classes

- **Scientific: PASS.** Criteria 1–4 all passed. Correction removes current
  burden-edge support without erasing history; timely do-over evidence is
  equivalent at the saturated evidence ceiling; premature imagery does not
  produce durable unburdening; and the adaptive edge survives selective
  pruning.
- **Semantic: PASS.** Candidate-common neutral observations were exactly
  structure-neutral within the declared `1e-10` tolerance.
- **Custody: PASS.** Challenge SHA-256
  `c6ae7f5169be554cbead523f2ffe6ac797033eb63937ccf59bb7c104e21ac3a4`
  matched the committed seal. Frozen identity verified `53/53` files.
  Escrow `4030000:4033999` was used once under release commit `be21368`.
  Per-record and whole-file ledgers verify all four cell trace files.

## Standing limitations

The Gate-3 and Gate-5 do-over-speedup failures remain substantive negative
findings; C-V33 prospectively verified their equivalence interpretation. The
small-negative suggestion-direction anomaly also remains retained. C-V33 did
not contain a suggestion-direction criterion and therefore does not rewrite
that result.

Each raw cell trace file is 34–38 MB, below the 90 MB local-only threshold.
