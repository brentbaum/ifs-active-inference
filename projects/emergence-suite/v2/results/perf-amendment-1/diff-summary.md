# Performance amendment 1 — diff summary

The implementation is limited to the six authorized tier-1 items. No R0
enumeration/DP source was touched.

## 1. Oracle audit vectorization

- `ref/oracle.py`
  - retains the original Cartesian implementation as `brute_force_slow`;
  - makes `brute_force` use an independently authored broadcast-joint NumPy
    audit by default;
  - exposes `slow=True` for regression comparison.
- `ExactEngine.infer` remains unchanged and still returns the elimination
  result after the `1e-10` audit.

## 2. World-loop parallelism

- `run_v244_gates.py`
  - moves Gate-2 structural rows, Gate-3 misspecification rows, and Gate-4
    lesion rows onto the existing eight-subprocess pattern;
  - merges strictly by integer position before aggregation;
  - preserves seed-keyed RNG and all row/null values.
- V2.5a's corresponding primary loops were inspected and already use the
  frozen eight-worker `_parallel`/`_parallel_rows` paths; no redundant change
  was made there.

## 3. CRT graph memoization

- `ref/v244.py`
  - caches the exact count lattice by family, history length, and frozen
    transition-parameter tuple;
  - exposes cache clearing/info through the standard `lru_cache` API for
    regression tests.

## 4. CRT edge propagation

- **Dropped after verification.**
- Ordered `np.add.at` was bit-identical but slowed the retained workload from
  `2.044402s` to `2.816013s`.
- The active implementation retains the original scalar edge accumulation.

## 5. CS lattice scalarization

- `ref/v24.py`
  - replaces two-element NumPy allocation/normalization inside
    `_cs_transition` with same-operation-order scalar arithmetic;
  - retains `_cs_transition_numpy_reference` solely for bit-identity tests.

## 6. Test-suite parallelization

- `run_tests_parallel.py`
  - runs unchanged unittest modules in parallel subprocesses;
  - reports modules in deterministic sorted order and propagates any failure.
- `tests/test_performance_amendment_1.py`
  - pins fast/slow oracle audit agreement;
  - pins full CRT null-vector equality on two retained seeds;
  - pins graph-cache reuse;
  - pins scalar/reference CS score equality.

## Generated verification records

Only new files under `results/perf-amendment-1/` were generated. No original
result file was regenerated.

