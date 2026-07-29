# Performance amendment 1 — before/after timing report

**Machine:** Darwin arm64, Python 3.14.3, Homebrew NumPy  
**Authorization:** `protocols/performance-amendment-1-authorization.md`

## Summary

The retained identity fixtures are bit-identical. The largest improvement is
the audit oracle; the serial full suite fell from `434.092s` to `119.161s`
despite adding four regression tests. The new module-parallel wrapper
completed in `51.569s`.

| Workload | Before | After | Speedup |
|---|---:|---:|---:|
| Oracle microfixture, 20 calls | `0.852639s` retained slow path | `0.004845s` vectorized path | `176.0x` |
| Real-model oracle prototype from profiling report | loop baseline | vectorized | `26.2x` |
| CS family score, 96 slices | approximately `0.92s` | `0.428925s` | `2.14x` |
| CRT, 72-slice prehistory, cold graph | `3.8–4.3s` profile range | `2.439402s` | `1.56–1.76x` |
| CRT, same process with warm graph | `3.8–4.3s` profile range | `2.122521s` | `1.79–2.03x` |
| Mandatory complete fixture capture | `18.014219s` | `10.911782s` | `1.65x` |
| Eight Gate-2 structural rows | `20.193995s` serial | `5.099785s`, 8 workers | `3.96x` |
| Serial full unit discovery | `434.092s`, 131 tests | `119.161s`, 135 tests | `3.64x` |
| Module-parallel full suite | approximately `450s` historical | `51.569s` | approximately `8.7x` |

Times are wall-clock observations and include normal run-to-run variation.
The pre-change kernel ranges come from the authorized profiling report; the
fixture and suite baselines were measured in this repository immediately
before the amendment.

## Dropped edge-vectorization item

The authorized `np.add.at` edge propagation was implemented and passed full
bit equality, including both 999-replicate CRT null vectors. It was slower:

```text
cached scalar propagation: 2.044402s
ordered np.add.at:          2.816013s
relative speed:            0.726x
```

It was therefore removed from the active implementation. Graph memoization
remains. No alternative accumulation order was introduced.

## Suite standing

All scientific tests and all new performance tests pass. The mandatory full
suite is not green because `tests.test_v2g0_grammar` contains two custody
failures:

1. the historical assertion that the now-released sealed escrow must remain
   inaccessible;
2. the frozen V2.4.4 manifest correctly reports the three files changed by
   this authorized performance amendment.

Neither failure was edited, bypassed, or reclassified in code. A custody
addendum/test adjudication is required outside this authorization before the
suite can be green.

