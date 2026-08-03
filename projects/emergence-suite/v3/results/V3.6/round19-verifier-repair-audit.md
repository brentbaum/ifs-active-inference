# V3.6 Round-19 verifier repair audit

Verdict: **PASS**.

The repair is confined to `scripts/run_v36_gate4.py` and its regression test. Oracle comparisons now use the full `(structure, cross_sign, reliable)` atom coordinate and assert exact key-set equality before comparing values. Licensed-support positivity is decided directly in log space; no log evidence is exponentiated for a predicate.

All 34 frozen `ref/` files match the 278-file freeze manifest byte-for-byte. No likelihood, prior, generator, posterior, threshold, or scientific readout changed. Targeted regressions pass 3/3.
